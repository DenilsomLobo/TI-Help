from contextlib import closing

from app.database.connection import Database
from app.models.knowledge_article import KnowledgeArticle


class KnowledgeRepository:
    """Centraliza todo o SQL relacionado à Base de Conhecimento."""

    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _to_article(row) -> KnowledgeArticle:
        return KnowledgeArticle(
            id=row["id"],
            title=row["titulo"],
            problem=row["problema"],
            solution=row["solucao"],
            category=row["categoria"],
            created_by=row["criado_por"],
            created_at=row["criado_em"],
            updated_at=row["atualizado_em"],
            observation=row["observacao"],
            categories=tuple(filter(None, (row["categorias"] or "").split("|"))),
        )

    def search(self, term: str = "") -> list[KnowledgeArticle]:
        pattern = f"%{term.strip()}%"
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                """
                SELECT a.id,a.titulo,a.problema,a.solucao,a.categoria,a.criado_por,
                       a.criado_em,a.atualizado_em,a.observacao,
                       GROUP_CONCAT(c.nome, '|') categorias
                FROM artigos_conhecimento a
                LEFT JOIN artigo_categorias ac ON ac.artigo_id=a.id
                LEFT JOIN categorias c ON c.id=ac.categoria_id
                WHERE a.titulo LIKE ? COLLATE NOCASE
                   OR a.problema LIKE ? COLLATE NOCASE
                   OR a.solucao LIKE ? COLLATE NOCASE
                   OR a.categoria LIKE ? COLLATE NOCASE
                   OR c.nome LIKE ? COLLATE NOCASE
                GROUP BY a.id
                ORDER BY a.atualizado_em DESC, a.id DESC
                """,
                (pattern, pattern, pattern, pattern, pattern),
            ).fetchall()
        return [self._to_article(row) for row in rows]

    def create(self, title: str, problem: str, solution: str,
               categories: list[str], observation: str, created_by: int) -> KnowledgeArticle:
        primary_category = categories[0]
        with closing(self.database.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO artigos_conhecimento
                        (titulo,problema,solucao,categoria,observacao,criado_por)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (title, problem, solution, primary_category, observation, created_by),
                )
                article_id = int(cursor.lastrowid)
                self._replace_categories(connection, article_id, categories)
        return self.find_by_id(article_id)

    def update(self, article_id: int, title: str, problem: str,
               solution: str, categories: list[str], observation: str) -> bool:
        with closing(self.database.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE artigos_conhecimento
                    SET titulo=?, problema=?, solucao=?, categoria=?, observacao=?,
                        atualizado_em=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (title, problem, solution, categories[0], observation, article_id),
                )
                if cursor.rowcount:
                    self._replace_categories(connection, article_id, categories)
        return cursor.rowcount > 0

    def find_by_id(self, article_id: int) -> KnowledgeArticle | None:
        with closing(self.database.connect()) as connection:
            row = connection.execute(
                """SELECT a.id,a.titulo,a.problema,a.solucao,a.categoria,a.criado_por,
                          a.criado_em,a.atualizado_em,a.observacao,
                          GROUP_CONCAT(c.nome, '|') categorias
                   FROM artigos_conhecimento a
                   LEFT JOIN artigo_categorias ac ON ac.artigo_id=a.id
                   LEFT JOIN categorias c ON c.id=ac.categoria_id
                   WHERE a.id=? GROUP BY a.id""", (article_id,)
            ).fetchone()
        return self._to_article(row) if row else None

    @staticmethod
    def _replace_categories(connection, article_id: int, categories: list[str]) -> None:
        connection.execute("DELETE FROM artigo_categorias WHERE artigo_id=?", (article_id,))
        for name in categories:
            connection.execute("INSERT OR IGNORE INTO categorias(nome) VALUES(?)", (name,))
            category = connection.execute(
                "SELECT id FROM categorias WHERE nome=? COLLATE NOCASE", (name,)
            ).fetchone()
            connection.execute(
                "INSERT OR IGNORE INTO artigo_categorias(artigo_id,categoria_id) VALUES(?,?)",
                (article_id, category["id"]),
            )

    def delete(self, article_id: int) -> bool:
        with closing(self.database.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM artigos_conhecimento WHERE id=?", (article_id,)
                )
        return cursor.rowcount > 0

    def list_categories(self) -> list[str]:
        with closing(self.database.connect()) as connection:
            rows = connection.execute("SELECT nome FROM categorias ORDER BY nome COLLATE NOCASE").fetchall()
        return [row["nome"] for row in rows]

    def create_category(self, name: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute("INSERT INTO categorias(nome) VALUES(?)", (name,))

    def rename_category(self, old_name: str, new_name: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "UPDATE categorias SET nome=? WHERE nome=? COLLATE NOCASE",
                    (new_name, old_name))
                if not cursor.rowcount:
                    raise ValueError("A categoria não foi encontrada.")
                # Os vínculos usam ID, mas registros antigos também guardam o nome.
                connection.execute(
                    "UPDATE artigos_conhecimento SET categoria=? WHERE categoria=? COLLATE NOCASE",
                    (new_name, old_name))

    def delete_category(self, name: str) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                used = connection.execute(
                    """SELECT 1 FROM artigos_conhecimento a
                       WHERE a.categoria=? COLLATE NOCASE OR EXISTS (
                           SELECT 1 FROM artigo_categorias ac JOIN categorias c
                           ON c.id=ac.categoria_id
                           WHERE ac.artigo_id=a.id AND c.nome=? COLLATE NOCASE)
                       LIMIT 1""", (name, name)).fetchone()
                if used:
                    raise ValueError("Categoria em uso. Altere as categorias dos registros antes de excluí-la.")
                cursor = connection.execute(
                    "DELETE FROM categorias WHERE nome=? COLLATE NOCASE", (name,))
                if not cursor.rowcount:
                    raise ValueError("A categoria não foi encontrada.")

    def search_problems(self, term: str = "", category: str = "") -> list[KnowledgeArticle]:
        with closing(self.database.connect()) as connection:
            # Marcas de qualquer usuário impedem que contatos/acessos apareçam como problemas.
            excluded = {row[0] for row in connection.execute(
                "SELECT artigo_id FROM artigo_marcacoes WHERE tipo IN ('contato','cofre')")}
        return [article for article in self.search(term)
                if article.id not in excluded
                and (not category or category in article.categories or category == article.category)]

    def set_mark(self, article_id: int, user_id: int, mark_type: str, marked: bool) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                if marked:
                    connection.execute(
                        "INSERT OR IGNORE INTO artigo_marcacoes(artigo_id,usuario_id,tipo) VALUES(?,?,?)",
                        (article_id, user_id, mark_type),
                    )
                else:
                    connection.execute(
                        "DELETE FROM artigo_marcacoes WHERE artigo_id=? AND usuario_id=? AND tipo=?",
                        (article_id, user_id, mark_type),
                    )

    def marks_for(self, article_id: int, user_id: int) -> set[str]:
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                "SELECT tipo FROM artigo_marcacoes WHERE artigo_id=? AND usuario_id=?",
                (article_id, user_id),
            ).fetchall()
        return {row["tipo"] for row in rows}

    def search_marked(self, user_id: int, mark_type: str, term: str = "",
                      category: str = "") -> list[KnowledgeArticle]:
        return [article for article in self.search(term)
                if mark_type in self.marks_for(article.id, user_id)
                and (not category or category in article.categories)]

    def record_recent(self, article_id: int, user_id: int) -> None:
        with closing(self.database.connect()) as connection:
            with connection:
                connection.execute(
                    """INSERT INTO artigos_recentes(artigo_id,usuario_id,acessado_em)
                       VALUES(?,?,CURRENT_TIMESTAMP)
                       ON CONFLICT(artigo_id,usuario_id) DO UPDATE SET
                           acessado_em=CURRENT_TIMESTAMP""",
                    (article_id, user_id))

    def recent(self, user_id: int, limit: int = 30) -> list[KnowledgeArticle]:
        with closing(self.database.connect()) as connection:
            ids = [row["artigo_id"] for row in connection.execute(
                """SELECT artigo_id FROM artigos_recentes WHERE usuario_id=?
                   ORDER BY acessado_em DESC LIMIT ?""", (user_id, limit)).fetchall()]
        return [article for article_id in ids
                if (article := self.find_by_id(article_id)) is not None]
