import sqlite3
import sys
from pathlib import Path


def application_root() -> Path:
    """Retorna a pasta persistente do projeto ou do executável empacotado."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = application_root()
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "ti_help.db"


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_DATABASE_PATH

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
