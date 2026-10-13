"""Amplia o catálogo preservando IDs e relacionamentos existentes."""

from contextlib import closing
from datetime import datetime
import sqlite3

from app.database.connection import Database


def migrate_catalog(database: Database) -> None:
    with closing(database.connect()) as connection:
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='registros_modulo'"
        ).fetchone()[0]
        if "'tela_senior'" in schema:
            return

        backup_dir = database.path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"{database.path.stem}_antes_catalogo_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
        with closing(sqlite3.connect(backup_path)) as backup:
            connection.backup(backup)

        # SQLite exige recriar a tabela para mudar um CHECK. Desligamos as FKs
        # apenas nesta conexão; a integridade é conferida antes do commit.
        connection.execute("PRAGMA foreign_keys=OFF")
        try:
            connection.execute("BEGIN IMMEDIATE")
            for table in ("categorias_modulo", "registros_modulo"):
                definition = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()[0]
                definition = definition.replace(table, f"{table}_novo", 1).replace(
                    "'relatorio','banco','regra'", "'relatorio','banco','regra','tela_senior'")
                # Recriar índices/triggers explícitos evita perder extensões locais.
                extras = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE tbl_name=? AND type IN ('index','trigger') AND sql IS NOT NULL",
                    (table,)).fetchall()
                sequence = connection.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name=?", (table,)).fetchone()
                connection.execute(definition)
                connection.execute(f"INSERT INTO {table}_novo SELECT * FROM {table}")
                connection.execute(f"DROP TABLE {table}")
                connection.execute(f"ALTER TABLE {table}_novo RENAME TO {table}")
                if sequence:
                    connection.execute("UPDATE sqlite_sequence SET seq=MAX(seq,?) WHERE name=?",
                                       (sequence[0], table))
                for extra in extras:
                    connection.execute(extra[0])

            connection.execute("""
                CREATE TABLE registro_categorias (
                    registro_id INTEGER NOT NULL REFERENCES registros_modulo(id) ON DELETE CASCADE,
                    categoria_id INTEGER NOT NULL REFERENCES categorias_modulo(id) ON DELETE CASCADE,
                    PRIMARY KEY (registro_id, categoria_id)
                )
            """)
            connection.execute("""
                INSERT INTO registro_categorias(registro_id,categoria_id)
                SELECT id,categoria_id FROM registros_modulo WHERE categoria_id IS NOT NULL
            """)
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise sqlite3.IntegrityError("A migração encontrou relacionamentos inválidos.")
            connection.commit()
        except Exception:
            # O rollback desfaz inclusive a troca de tabelas caso uma etapa falhe.
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys=ON")
