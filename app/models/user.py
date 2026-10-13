from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class User:
    id: int
    name: str
    username: str
    role: str
    active: bool
    job: str = ""
