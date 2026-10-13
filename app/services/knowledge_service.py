from app.models.knowledge_article import KnowledgeArticle
import sqlite3

from app.repositories.knowledge_repository import KnowledgeRepository


class KnowledgeValidationError(ValueError):
    pass


class KnowledgeService:
    """Aplica as regras antes de permitir alterações no banco."""

    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def search(self, term: str = "") -> list[KnowledgeArticle]:
        return self.repository.search(term)

    def get(self, article_id: int) -> KnowledgeArticle | None:
        return self.repository.find_by_id(article_id)

    def create(self, title: str, problem: str, solution: str,
               category: str | list[str], created_by: int,
               observation: str = "") -> KnowledgeArticle:
        title, problem, solution, categories = self._validate(
            title, problem, solution, category
        )
        return self.repository.create(
            title, problem, solution, categories, observation.strip(), created_by
        )

    def update(self, article_id: int, title: str, problem: str,
               solution: str, category: str | list[str], observation: str = "") -> None:
        title, problem, solution, categories = self._validate(
            title, problem, solution, category
        )
        if not self.repository.update(
            article_id, title, problem, solution, categories, observation.strip()
        ):
            raise KnowledgeValidationError("O registro não foi encontrado.")

    def delete(self, article_id: int) -> None:
        if not self.repository.delete(article_id):
            raise KnowledgeValidationError("O registro não foi encontrado.")

    def list_categories(self) -> list[str]:
        return self.repository.list_categories()

    def create_category(self, name: str) -> None:
        name = name.strip()
        if len(name) < 2:
            raise KnowledgeValidationError("A categoria deve ter pelo menos 2 caracteres.")
        try:
            self.repository.create_category(name)
        except sqlite3.IntegrityError as error:
            raise KnowledgeValidationError("Essa categoria já existe.") from error

    def marks_for(self, article_id: int, user_id: int) -> set[str]:
        return self.repository.marks_for(article_id, user_id)

    def rename_category(self, old_name: str, new_name: str) -> None:
        new_name = new_name.strip()
        if len(new_name) < 2 or "|" in new_name:
            raise KnowledgeValidationError("Use pelo menos 2 caracteres e não use | no nome.")
        try:
            self.repository.rename_category(old_name, new_name)
        except sqlite3.IntegrityError as error:
            raise KnowledgeValidationError("Essa categoria já existe.") from error
        except ValueError as error:
            raise KnowledgeValidationError(str(error)) from error

    def delete_category(self, name: str) -> None:
        try:
            self.repository.delete_category(name)
        except ValueError as error:
            raise KnowledgeValidationError(str(error)) from error

    def search_problems(self, term: str = "", category: str = "") -> list[KnowledgeArticle]:
        return self.repository.search_problems(term, category)

    def toggle_mark(self, article_id: int, user_id: int, mark_type: str) -> bool:
        if mark_type not in {"favorito", "contato", "cofre"}:
            raise KnowledgeValidationError("Tipo de marcação inválido.")
        marked = mark_type not in self.repository.marks_for(article_id, user_id)
        self.repository.set_mark(article_id, user_id, mark_type, marked)
        return marked

    def search_marked(self, user_id: int, mark_type: str, term: str = "",
                      category: str = "") -> list[KnowledgeArticle]:
        return self.repository.search_marked(user_id, mark_type, term, category)

    def record_recent(self, article_id: int, user_id: int) -> None:
        self.repository.record_recent(article_id, user_id)

    def recent(self, user_id: int) -> list[KnowledgeArticle]:
        return self.repository.recent(user_id)

    @staticmethod
    def _validate(title: str, problem: str, solution: str,
                  category: str | list[str]) -> tuple[str, str, str, list[str]]:
        category_values = [category] if isinstance(category, str) else category
        categories = list(dict.fromkeys(value.strip() for value in category_values if value.strip()))
        values = title.strip(), problem.strip(), solution.strip()
        if len(values[0]) < 3:
            raise KnowledgeValidationError("O título deve ter pelo menos 3 caracteres.")
        if not categories:
            categories = ["Geral"]
        return values + (categories,)
