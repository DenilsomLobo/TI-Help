import sqlite3

from app.models.catalog_record import CatalogRecord, SapiensUser
from app.repositories.catalog_repository import CatalogRepository


class CatalogValidationError(ValueError):
    pass


class CatalogService:
    MODULES = {"relatorio", "banco", "regra", "tela_senior"}

    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    def search(self, module: str, term: str = "") -> list[CatalogRecord]:
        return self.repository.search_records(module, term)

    def create(self, module: str, title: str, description: str, purpose: str,
               observation: str, category_name: str | list[str], user_id: int) -> None:
        if module not in self.MODULES:
            raise CatalogValidationError("Módulo inválido.")
        if not title.strip():
            raise CatalogValidationError("Informe o título.")
        category_ids = self._category_ids(module, category_name)
        self.repository.create_record(module, title.strip(), description.strip(), purpose.strip(),
                                      observation.strip(), category_ids, user_id)

    def _category_ids(self, module: str, names: str | list[str]) -> list[int]:
        if module not in self.MODULES:
            raise CatalogValidationError("Módulo inválido.")
        values = [names] if isinstance(names, str) else names
        categories = {name.casefold(): category_id for category_id, name
                      in self.repository.categories(module)}
        selected = []
        for name in values:
            key = name.strip().casefold()
            if key in categories:
                selected.append(categories[key])
            elif key and key != "sem categoria":
                raise CatalogValidationError(f"Categoria não encontrada neste módulo: {name}")
        return list(dict.fromkeys(selected))

    def categories(self, module: str) -> list[str]:
        return [name for _id, name in self.repository.categories(module)]

    def create_category(self, module: str, name: str) -> None:
        if module not in self.MODULES:
            raise CatalogValidationError("Módulo inválido.")
        if not name.strip():
            raise CatalogValidationError("Informe o nome da categoria.")
        try:
            self.repository.create_category(module, name.strip())
        except sqlite3.IntegrityError as error:
            raise CatalogValidationError("Essa categoria já existe.") from error

    def search_sapiens(self, term: str = "") -> list[SapiensUser]:
        return self.repository.search_sapiens(term)

    def create_sapiens(self, name: str, login: str, number: str, sector: str) -> None:
        if not name.strip() or not login.strip():
            raise CatalogValidationError("Nome e login são obrigatórios.")
        try:
            self.repository.create_sapiens(name.strip(), login.strip(), number.strip(), sector.strip())
        except sqlite3.IntegrityError as error:
            raise CatalogValidationError("Esse login do Sapiens já existe.") from error

    def update_sapiens(self, item_id: int, name: str, login: str,
                       number: str, sector: str) -> None:
        if not name.strip() or not login.strip():
            raise CatalogValidationError("Nome e login são obrigatórios.")
        try:
            self.repository.update_sapiens(
                item_id, name.strip(), login.strip(), number.strip(), sector.strip())
        except sqlite3.IntegrityError as error:
            raise CatalogValidationError("Esse login do Sapiens já existe.") from error

    def delete_sapiens(self, item_id: int) -> None:
        self.repository.delete_sapiens(item_id)

    def update(self, record_id: int, module: str, title: str, description: str,
               purpose: str, observation: str, category_name: str | list[str]) -> None:
        if not title.strip():
            raise CatalogValidationError("Informe o título.")
        category_ids = self._category_ids(module, category_name)
        self.repository.update_record(
            record_id, title.strip(), description.strip(), purpose.strip(),
            observation.strip(), category_ids)

    def delete(self, record_id: int) -> None:
        self.repository.delete_record(record_id)

    def add_database_field(self, record_id: int, name: str, description: str) -> None:
        if not name.strip():
            raise CatalogValidationError("Informe o nome do campo.")
        self.repository.add_database_field(record_id, name.strip(), description.strip())

    def database_fields(self, record_id: int) -> list[tuple[str, str]]:
        return self.repository.database_fields(record_id)

    def database_field_entries(self, record_id: int) -> list[tuple[int, str, str]]:
        return self.repository.database_field_entries(record_id)

    def update_database_field(self, field_id: int, name: str, description: str) -> None:
        if not name.strip():
            raise CatalogValidationError("Informe o nome do campo.")
        self.repository.update_database_field(field_id, name.strip(), description.strip())
