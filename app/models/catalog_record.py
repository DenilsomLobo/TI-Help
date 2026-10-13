from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CatalogRecord:
    id: int
    module: str
    title: str
    description: str
    purpose: str
    observation: str
    category: str
    categories: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SapiensUser:
    id: int
    name: str
    login: str
    number: str
    sector: str
