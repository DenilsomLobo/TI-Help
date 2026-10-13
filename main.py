import ctypes
import sys

from app.database.connection import Database
from app.database.migrations import run_migrations
from app.repositories.user_repository import UserRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.security_repository import SecurityRepository
from app.repositories.catalog_repository import CatalogRepository
from app.services.auth_service import AuthService
from app.services.knowledge_service import KnowledgeService
from app.services.security_service import SecurityService
from app.services.catalog_service import CatalogService
from app.ui.application import TIHelpApplication
from app.ui.theme import configure_theme


def configure_windows_app_identity() -> None:
    """Define a identidade usada pelo Windows para agrupar o ícone na barra de tarefas."""
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "TIHelp.Desktop"
        )


def main() -> None:
    """Prepara as camadas e inicia a interface."""
    configure_windows_app_identity()
    configure_theme()
    database = Database()
    run_migrations(database)
    auth_service = AuthService(UserRepository(database))
    knowledge_service = KnowledgeService(KnowledgeRepository(database))
    security_service = SecurityService(SecurityRepository(database))
    catalog_service = CatalogService(CatalogRepository(database))
    app = TIHelpApplication(auth_service, knowledge_service, security_service, catalog_service)
    app.mainloop()


if __name__ == "__main__":
    main()
