from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.database.connection import Database
from app.database.migrations import run_migrations
from app.database.catalog_migration import migrate_catalog
from app.repositories.catalog_repository import CatalogRepository
from app.services.catalog_service import CatalogService, CatalogValidationError


class CatalogMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Database(Path(self.temp.name) / "legacy.db")
        # Simula a versão anterior, antes da ampliação do catálogo.
        with patch("app.database.migrations.migrate_catalog"):
            run_migrations(self.database)
        with closing(self.database.connect()) as connection, connection:
            connection.execute("INSERT INTO usuarios(id,nome,usuario,senha,tipo) VALUES(1,'Teste','teste','hash','admin')")
            connection.execute("INSERT INTO categorias_modulo(id,modulo,nome) VALUES(7,'banco','ERP')")
            connection.execute("""INSERT INTO registros_modulo
                (id,modulo,titulo,descricao,finalidade,observacao,categoria_id,criado_por)
                VALUES(9,'banco','Tabela antiga','Descrição','Finalidade','Observação',7,1)""")
            connection.execute("INSERT INTO campos_banco(id,registro_id,nome,descricao) VALUES(4,9,'codigo','Chave')")
        self.service = CatalogService(CatalogRepository(self.database))

    def snapshot(self):
        with closing(self.database.connect()) as connection:
            return {table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
                    for table in ("usuarios", "categorias_modulo", "registros_modulo", "campos_banco")}

    def test_preserves_old_rows_relationships_and_backup_and_is_repeatable(self):
        before = self.snapshot()
        run_migrations(self.database)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(("ERP",), self.service.search("banco")[0].categories)
        run_migrations(self.database)
        self.assertEqual(before, self.snapshot())
        backups = list((self.database.path.parent / "backups").glob("*.db"))
        self.assertEqual(1, len(backups))
        with closing(sqlite3.connect(backups[0])) as backup:
            self.assertEqual(before["registros_modulo"], backup.execute("SELECT * FROM registros_modulo").fetchall())
        with closing(self.database.connect()) as connection:
            self.assertEqual([], connection.execute("PRAGMA foreign_key_check").fetchall())
            self.assertEqual("ok", connection.execute("PRAGMA integrity_check").fetchone()[0])
        self.service.delete(9)
        self.assertEqual([], self.service.database_fields(9))

    def test_all_modules_support_multiple_categories_and_search(self):
        run_migrations(self.database)
        for module in sorted(self.service.MODULES):
            with self.subTest(module=module):
                self.service.create_category(module, "Financeiro")
                self.service.create_category(module, "Operação")
                self.service.create(module, "Novo registro", "Descrição", "Finalidade", "Nota",
                                    ["Financeiro", "Operação", "Financeiro"], 1)
                record = self.service.search(module, "Operação")[0]
                self.assertEqual(("Financeiro", "Operação"), record.categories)
                self.service.update(record.id, module, record.title, "Alterado", "", "", ["Operação"])
                self.assertEqual([], self.service.search(module, "Financeiro"))
                run_migrations(self.database)
                self.assertEqual(("Operação",), self.service.search(module, "Novo")[0].categories)
                self.service.update(record.id, module, record.title, "", "", "", [])
                self.assertEqual((), self.service.search(module, "Novo")[0].categories)
                self.service.delete(record.id)
                self.assertEqual([], self.service.search(module, "Novo"))

    def test_invalid_category_does_not_change_record(self):
        run_migrations(self.database)
        with self.assertRaises(CatalogValidationError):
            self.service.update(9, "banco", "Mudado", "", "", "", ["Inexistente"])
        self.assertEqual("Tabela antiga", self.service.search("banco")[0].title)

    def test_failure_rolls_back_table_rebuild(self):
        with closing(self.database.connect()) as connection:
            connection.execute("PRAGMA foreign_keys=OFF")
            with connection:
                connection.execute("UPDATE registros_modulo SET criado_por=999 WHERE id=9")
        before = self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):
            migrate_catalog(self.database)
        self.assertEqual(before, self.snapshot())
        with closing(self.database.connect()) as connection:
            definition = connection.execute("SELECT sql FROM sqlite_master WHERE name='registros_modulo'").fetchone()[0]
            self.assertNotIn("tela_senior", definition)
