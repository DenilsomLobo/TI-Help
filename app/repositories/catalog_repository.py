from contextlib import closing

from app.database.connection import Database
from app.models.catalog_record import CatalogRecord, SapiensUser


class CatalogRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def search_records(self, module: str, term: str = "") -> list[CatalogRecord]:
        pattern = f"%{term.strip()}%"
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                """SELECT r.id,r.modulo,r.titulo,r.descricao,r.finalidade,r.observacao,
                          COALESCE(c.nome,'Sem categoria') categoria
                   FROM registros_modulo r LEFT JOIN categorias_modulo c ON c.id=r.categoria_id
                   WHERE r.modulo=? AND (r.titulo LIKE ? COLLATE NOCASE
                     OR r.descricao LIKE ? COLLATE NOCASE OR r.finalidade LIKE ? COLLATE NOCASE
                     OR r.observacao LIKE ? COLLATE NOCASE OR EXISTS (
                         SELECT 1 FROM registro_categorias rc
                         JOIN categorias_modulo mc ON mc.id=rc.categoria_id
                         WHERE rc.registro_id=r.id AND mc.nome LIKE ? COLLATE NOCASE))
                   ORDER BY r.atualizado_em DESC,r.id DESC""",
                (module, pattern, pattern, pattern, pattern, pattern)).fetchall()
            category_rows = connection.execute(
                """SELECT rc.registro_id,c.nome FROM registro_categorias rc
                   JOIN categorias_modulo c ON c.id=rc.categoria_id
                   JOIN registros_modulo r ON r.id=rc.registro_id
                   WHERE r.modulo=? ORDER BY c.nome COLLATE NOCASE""", (module,)).fetchall()
        categories: dict[int, list[str]] = {}
        for row in category_rows:
            categories.setdefault(row["registro_id"], []).append(row["nome"])
        return [CatalogRecord(row["id"], row["modulo"], row["titulo"], row["descricao"],
                              row["finalidade"], row["observacao"], row["categoria"],
                              tuple(categories.get(row["id"], [])))
                for row in rows]

    def create_record(self, module: str, title: str, description: str, purpose: str,
                      observation: str, category_ids: list[int], user_id: int) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """INSERT INTO registros_modulo
                       (modulo,titulo,descricao,finalidade,observacao,categoria_id,criado_por)
                       VALUES(?,?,?,?,?,?,?)""",
                    (module, title, description, purpose, observation,
                     next(iter(category_ids), None), user_id))
                self._set_categories(connection, cursor.lastrowid, category_ids)

    @staticmethod
    def _set_categories(connection, record_id: int, category_ids: list[int]) -> None:
        # Registro e vínculos são gravados na mesma transação: tudo ou nada.
        connection.execute("DELETE FROM registro_categorias WHERE registro_id=?", (record_id,))
        connection.executemany(
            "INSERT INTO registro_categorias(registro_id,categoria_id) VALUES(?,?)",
            [(record_id, category_id) for category_id in category_ids])

    def categories(self, module: str) -> list[tuple[int, str]]:
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                "SELECT id,nome FROM categorias_modulo WHERE modulo=? ORDER BY nome COLLATE NOCASE",
                (module,)).fetchall()
        return [(row["id"], row["nome"]) for row in rows]

    def create_category(self, module: str, name: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute("INSERT INTO categorias_modulo(modulo,nome) VALUES(?,?)",
                                   (module, name))

    def add_database_field(self, record_id: int, name: str, description: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    "INSERT INTO campos_banco(registro_id,nome,descricao) VALUES(?,?,?)",
                    (record_id, name, description))

    def database_fields(self, record_id: int) -> list[tuple[str, str]]:
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                "SELECT nome,descricao FROM campos_banco WHERE registro_id=? ORDER BY id",
                (record_id,)).fetchall()
        return [(row["nome"], row["descricao"]) for row in rows]

    def database_field_entries(self, record_id: int) -> list[tuple[int, str, str]]:
        """Retorna também o ID usado para selecionar um campo para edição."""
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                "SELECT id,nome,descricao FROM campos_banco WHERE registro_id=? ORDER BY id",
                (record_id,)).fetchall()
        return [(row["id"], row["nome"], row["descricao"]) for row in rows]

    def update_database_field(self, field_id: int, name: str, description: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    "UPDATE campos_banco SET nome=?,descricao=? WHERE id=?",
                    (name, description, field_id))

    def search_sapiens(self, term: str = "") -> list[SapiensUser]:
        pattern = f"%{term.strip()}%"
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                """SELECT id,nome,login,numero,setor FROM usuarios_sapiens
                   WHERE nome LIKE ? COLLATE NOCASE OR login LIKE ? COLLATE NOCASE
                      OR numero LIKE ? COLLATE NOCASE OR setor LIKE ? COLLATE NOCASE
                   ORDER BY nome COLLATE NOCASE""", (pattern,) * 4).fetchall()
        return [SapiensUser(row["id"], row["nome"], row["login"], row["numero"], row["setor"])
                for row in rows]

    def create_sapiens(self, name: str, login: str, number: str, sector: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    "INSERT INTO usuarios_sapiens(nome,login,numero,setor) VALUES(?,?,?,?)",
                    (name, login, number, sector))

    def update_sapiens(self, item_id: int, name: str, login: str,
                       number: str, sector: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    """UPDATE usuarios_sapiens SET nome=?,login=?,numero=?,setor=?,
                       atualizado_em=CURRENT_TIMESTAMP WHERE id=?""",
                    (name, login, number, sector, item_id))

    def delete_sapiens(self, item_id: int) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute("DELETE FROM usuarios_sapiens WHERE id=?", (item_id,))

    def update_record(self, record_id: int, title: str, description: str,
                      purpose: str, observation: str, category_ids: list[int]) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    """UPDATE registros_modulo SET titulo=?,descricao=?,finalidade=?,
                       observacao=?,categoria_id=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?""",
                    (title, description, purpose, observation,
                     next(iter(category_ids), None), record_id))
                self._set_categories(connection, record_id, category_ids)

    def delete_record(self, record_id: int) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute("DELETE FROM registros_modulo WHERE id=?", (record_id,))
