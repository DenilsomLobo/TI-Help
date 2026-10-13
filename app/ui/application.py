import customtkinter as ctk
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.knowledge_service import KnowledgeService
from app.services.security_service import SecurityService
from app.services.catalog_service import CatalogService
from app.ui.dashboard_view import DashboardView
from app.ui.login_view import LoginView
from app.ui.window_utils import apply_app_icon


class TIHelpApplication(ctk.CTk):
    def __init__(self, auth_service: AuthService,
                 knowledge_service: KnowledgeService,
                 security_service: SecurityService,
                 catalog_service: CatalogService) -> None:
        super().__init__()
        self.auth_service = auth_service
        self.knowledge_service = knowledge_service
        self.security_service = security_service
        self.catalog_service = catalog_service
        self.title("TI Help")
        apply_app_icon(self)
        self.geometry("1100x700")
        self.minsize(850, 550)
        self.show_login()

    def _clear(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self) -> None:
        self._clear()
        LoginView(self, self.auth_service, self.show_dashboard).pack(fill="both", expand=True)

    def show_dashboard(self, user: User) -> None:
        self._clear()
        DashboardView(self, user, self.show_login, self.knowledge_service,
                      self.auth_service, self.security_service,
                      self.catalog_service).pack(fill="both", expand=True)
