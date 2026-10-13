import tempfile
import unittest
from pathlib import Path

from app.database.connection import Database
from app.database.migrations import run_migrations
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.user_repository import UserRepository
from app.services.catalog_service import CatalogService


class CatalogServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        database = Database(Path(self.temp.name) / "test.db")
        run_migrations(database)
        self.user = UserRepository(database).create_admin("Admin", "admin", "hash")
        self.service = CatalogService(CatalogRepository(database))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_creates_and_searches_sapiens_user(self) -> None:
        self.service.create_sapiens("Maria", "maria.s", "123", "Financeiro")
        self.assertEqual("maria.s", self.service.search_sapiens("Financeiro")[0].login)

    def test_modules_keep_categories_and_search_separate(self) -> None:
        self.service.create_category("relatorio", "Financeiro")
        self.service.create("relatorio", "Fluxo de caixa", "Resumo", "Conferência", "",
                            "Financeiro", self.user.id)
        self.assertEqual(1, len(self.service.search("relatorio", "caixa")))
        self.assertEqual([], self.service.search("regra", "caixa"))

    def test_adds_fields_to_database_record(self) -> None:
        self.service.create("banco", "usuarios", "Tabela principal", "Armazena usuários",
                            "", "Sem categoria", self.user.id)
        record = self.service.search("banco", "usuarios")[0]
        self.service.add_database_field(record.id, "id", "Chave primária")
        self.assertEqual([("id", "Chave primária")], self.service.database_fields(record.id))

        field_id, _name, _description = self.service.database_field_entries(record.id)[0]
        self.service.update_database_field(field_id, "codigo", "Identificador da tabela")
        self.assertEqual(
            [("codigo", "Identificador da tabela")],
            self.service.database_fields(record.id),
        )

    def test_updates_and_deletes_sapiens_user(self) -> None:
        self.service.create_sapiens("Maria", "maria", "1", "TI")
        item = self.service.search_sapiens("maria")[0]
        self.service.update_sapiens(item.id, "Maria Souza", "maria.s", "2", "RH")
        self.assertEqual("RH", self.service.search_sapiens("maria.s")[0].sector)
        self.service.delete_sapiens(item.id)
        self.assertEqual([], self.service.search_sapiens("maria.s"))

    def test_updates_and_deletes_catalog_record(self) -> None:
        self.service.create("regra", "Regra antiga", "", "", "", "Sem categoria", self.user.id)
        item = self.service.search("regra", "antiga")[0]
        self.service.update(item.id, "regra", "Regra nova", "Descrição", "Validação", "Obs", "Sem categoria")
        self.assertEqual("Regra nova", self.service.search("regra", "nova")[0].title)
        self.service.delete(item.id)
        self.assertEqual([], self.service.search("regra", "nova"))


if __name__ == "__main__":
    unittest.main()
