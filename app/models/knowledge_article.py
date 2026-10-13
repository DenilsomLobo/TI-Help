from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeArticle:
    """Representa um problema e sua solução na Base de Conhecimento."""

    id: int
    title: str
    problem: str
    solution: str
    category: str
    created_by: int
    created_at: str
    updated_at: str
    observation: str = ""
    categories: tuple[str, ...] = ()
