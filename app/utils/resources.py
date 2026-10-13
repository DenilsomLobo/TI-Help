import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """Localiza recursos no projeto e no futuro executável criado pelo PyInstaller."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    base_path = Path(bundle_root) if bundle_root else Path(__file__).resolve().parents[2]
    return base_path / relative_path
