from collections.abc import Callable
import customtkinter as ctk
from PIL import Image
from app.models.user import User
from app.services.knowledge_service import KnowledgeService
from app.services.auth_service import AuthService
from app.services.security_service import SecurityService
from app.services.catalog_service import CatalogService
from app.ui.knowledge_view import KnowledgeView
from app.ui.home_view import HomeView, SearchResultsView
from app.ui.library_views import CategoriesView, FilteredArticlesView, RecentView
from app.ui.settings_view import SettingsView, VaultAccessDialog, ProfileDialog
from app.ui.catalog_views import CatalogView, SapiensView
from app.ui.new_record_hub import NewRecordHub
from app.ui.navigation_icons import PAGE_ICONS
from app.ui.theme import (DANGER, DANGER_BORDER, DANGER_TEXT, DARK_GREEN, LEAF_GREEN, LEAF_YELLOW,
                          LIGHT_GREEN, PIXEL_FONT_FAMILY, SURFACE_GREEN,
                          TEXT_LIGHT, YELLOW_HOVER, LOGO_FONT,
                          PAGE_TITLE_FONT, BODY_FONT, SIDEBAR, TEXT_MUTED)
from app.utils.resources import resource_path


class DashboardView(ctk.CTkFrame):
    SIDEBAR_WIDTH = 280
    COLLAPSED_WIDTH = 76
    # Cabe na coluna disponível também depois de recolher e reabrir a sidebar.
    MENU_BUTTON_WIDTH = 152
    MENU_BUTTON_HEIGHT = 36
    ICON_COLUMN_WIDTH = 34
    MENU_SPACING = 2
    SIDEBAR_PADDING = 8
    TOGGLE_RAIL_WIDTH = 16
    SCROLLBAR_GAP = 10
    MENU_FONT = (PIXEL_FONT_FAMILY, 12, "normal")

    PAGES = {
        "Início": "Pesquise informações do TI Help.",
        "Base de Conhecimento": "Problemas e soluções aparecerão aqui.",
        "Problemas": "Categorias dos problemas.",
        "Categorias": "Procure problemas pelas categorias.",
        "Favoritos": "Seus conteúdos favoritos aparecerão aqui.",
        "Recentes": "Os últimos conteúdos visualizados aparecerão aqui.",
        "Contatos": "Telefones e contatos aparecerão aqui.",
        "Cofre de Acessos": "Área protegida para armazenamento de acessos.",
        "Usuários Sapiens": "Cadastros do Sapiens.",
        "Relatórios": "Documentação de relatórios.",
        "Telas Senior": "Documentação das telas do Senior.",
        "Tabelas de Banco": "Documentação das tabelas de banco.",
        "Regras": "Documentação de regras.",
        "Configurações": "Usuários, permissões e backup do sistema.",
    }
    def __init__(self, master, user: User, on_logout: Callable[[], None],
                 knowledge_service: KnowledgeService, auth_service: AuthService,
                 security_service: SecurityService, catalog_service: CatalogService) -> None:
        super().__init__(master, corner_radius=0)
        self.user = user
        self.knowledge_service = knowledge_service
        self.auth_service, self.security_service = auth_service, security_service
        self.catalog_service = catalog_service
        self.menu_expanded = True
        self.menu = ctk.CTkFrame(
            self, width=self.SIDEBAR_WIDTH, corner_radius=0,
            fg_color=SIDEBAR, border_width=1, border_color=LEAF_GREEN)
        self.menu.pack(side="left", fill="y")
        self.menu.pack_propagate(False)
        self.menu.grid_propagate(False)
        self.menu.grid_columnconfigure(0, weight=1)
        self.menu.grid_columnconfigure(1, weight=0, minsize=self.TOGGLE_RAIL_WIDTH)
        self.menu.grid_rowconfigure(2, weight=1)
        self.brand = ctk.CTkFrame(self.menu, fg_color="transparent", height=58)
        self.brand.grid(
            row=0, column=0, sticky="ew", padx=self.SIDEBAR_PADDING,
            pady=(self.SIDEBAR_PADDING, 10))
        self.brand.pack_propagate(False)
        logo_path = resource_path("assets/capa_login.png")
        if logo_path.exists():
            with Image.open(logo_path) as source_image:
                logo_source = source_image.copy()
            self.menu_logo = ctk.CTkImage(
                light_image=logo_source, dark_image=logo_source, size=(58, 40))
            self.logo_label = ctk.CTkLabel(self.brand, text="", image=self.menu_logo)
            self.logo_label.pack(side="left")
        self.brand_title = ctk.CTkLabel(
            self.brand, text="TI HELP", font=LOGO_FONT, text_color=LEAF_YELLOW)
        self.brand_title.pack(side="left", padx=(8, 0))

        self.user_card = ctk.CTkFrame(
            self.menu, height=82, corner_radius=14, fg_color=SURFACE_GREEN,
            border_width=1, border_color=LIGHT_GREEN)
        self.user_card.grid(
            row=1, column=0, sticky="ew", padx=self.SIDEBAR_PADDING, pady=(0, 10))
        self.user_card.pack_propagate(False)
        self.user_avatar = ctk.CTkLabel(
            self.user_card, text="👤", width=42, font=("Segoe UI Emoji", 24))
        self.user_avatar.pack(side="left", padx=(10, 4))
        self.user_details = ctk.CTkFrame(self.user_card, fg_color="transparent")
        self.user_details.pack(side="left", fill="both", expand=True, pady=10)
        self.user_name = ctk.CTkLabel(
            self.user_details, text=self._short_user_name(user), height=18,
            anchor="w", font=(PIXEL_FONT_FAMILY, 13, "bold"))
        self.user_name.pack(fill="x")
        self.user_caption = ctk.CTkLabel(
            self.user_details, text="Usuário logado", anchor="w",
            height=18, text_color=TEXT_MUTED, font=(PIXEL_FONT_FAMILY, 11))
        self.user_caption.pack(fill="x")
        self.user_status = ctk.CTkLabel(
            self.user_details, text="● Online", anchor="w",
            height=18, text_color=LEAF_GREEN, font=(PIXEL_FONT_FAMILY, 11))
        self.user_status.pack(fill="x")
        for widget in (self.user_card, self.user_avatar, self.user_details,
                       self.user_name, self.user_caption, self.user_status):
            widget.bind("<Button-1>", lambda _event: self._open_profile())
        self.navigation = ctk.CTkScrollableFrame(
            self.menu, fg_color="transparent", scrollbar_button_color=LIGHT_GREEN,
            scrollbar_button_hover_color=SURFACE_GREEN)
        self.navigation.grid(
            row=2, column=0, sticky="nsew", padx=self.SIDEBAR_PADDING, pady=(0, 6))
        self.navigation_items = {}
        for name in self.PAGES:
            row = ctk.CTkFrame(
                self.navigation, fg_color="transparent", height=40)
            # O CTkScrollableFrame calcula corretamente a largura de linhas com
            # pack; dentro de cada linha, grid mantém todas as colunas alinhadas.
            row.pack(fill="x", pady=self.MENU_SPACING)
            # A coluna não absorve pixels excedentes ao restaurar a sidebar.
            row.grid_columnconfigure(2, weight=0)
            indicator = ctk.CTkFrame(
                row, width=4, height=32, corner_radius=2,
                fg_color="transparent")
            indicator.grid(row=0, column=0, padx=(0, 6), pady=4)
            indicator.pack_propagate(False)
            icon = ctk.CTkButton(
                row, text=PAGE_ICONS[name], width=self.ICON_COLUMN_WIDTH,
                height=34, font=("Segoe UI Emoji", 17), text_color=TEXT_LIGHT,
                fg_color="transparent", border_width=0,
                command=lambda page=name: self.open_page(page),
            )
            icon.grid(row=0, column=1, padx=(0, 8))
            button = ctk.CTkButton(
                row, text=name, width=self.MENU_BUTTON_WIDTH,
                height=self.MENU_BUTTON_HEIGHT, corner_radius=10, anchor="w",
                font=self.MENU_FONT,
                fg_color=SURFACE_GREEN, text_color=TEXT_LIGHT,
                command=lambda page=name: self.open_page(page)
            )
            # Reserva uma faixa antes da barra de rolagem. Sem esse espaço, a
            # borda arredondada direita fica sob o canvas/scrollbar ao reabrir.
            button.grid(
                row=0, column=2, sticky="ew", padx=(0, self.SCROLLBAR_GAP)
            )
            self.navigation_items[name] = (button, indicator, icon)
            button.bind(
                "<Enter>", lambda _event, page=name: self._hover_navigation(page, True), add="+"
            )
            button.bind(
                "<Leave>", lambda _event, page=name: self._hover_navigation(page, False), add="+"
            )
        self.footer = ctk.CTkFrame(self.menu, fg_color="transparent")
        self.footer.grid(
            row=3, column=0, sticky="ew", padx=self.SIDEBAR_PADDING,
            pady=(6, self.SIDEBAR_PADDING))
        self.footer.grid_columnconfigure(0, weight=1)
        self.logout_button = ctk.CTkButton(
            self.footer, text="↪ Deslogar", width=self.MENU_BUTTON_WIDTH,
            height=self.MENU_BUTTON_HEIGHT,
            command=on_logout, fg_color=SURFACE_GREEN,
            text_color=TEXT_LIGHT, hover_color=LEAF_GREEN)
        self.logout_button.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.exit_button = ctk.CTkButton(
            self.footer, text="Sair do programa", width=self.MENU_BUTTON_WIDTH,
            height=self.MENU_BUTTON_HEIGHT,
            command=master.quit,
            fg_color=DANGER, text_color=DANGER_TEXT, border_color=DANGER_BORDER)
        self.exit_button.grid(row=1, column=0, sticky="w")

        self.toggle_rail = ctk.CTkFrame(
            self.menu, width=self.TOGGLE_RAIL_WIDTH, corner_radius=0,
            fg_color=SIDEBAR)
        self.toggle_rail.grid(row=0, column=1, rowspan=4, sticky="ns")
        self.toggle_rail.grid_propagate(False)
        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)
        self.menu_toggle = ctk.CTkButton(
            self.toggle_rail, text="‹", width=16, height=38, corner_radius=0,
            bg_color=SIDEBAR, fg_color=SIDEBAR, text_color=LEAF_YELLOW,
            hover_color=SURFACE_GREEN, border_width=0,
            font=("Segoe UI Symbol", 18, "bold"),
            command=self._toggle_menu)
        self.menu_toggle.pack(expand=True)
        self.open_page("Início")

    @staticmethod
    def _short_user_name(user: User) -> str:
        """Evita que nomes longos ultrapassem o card; o perfil mantém o nome completo."""
        name = user.name.strip() or user.username
        return name if len(name) <= 26 else f"{name[:25]}…"

    def open_page(self, name: str) -> None:
        self._select_navigation(name)
        for widget in self.content.winfo_children(): widget.destroy()
        if name == "Início":
            HomeView(self.content, self.show_search_results).pack(fill="both", expand=True)
            return
        if name == "Base de Conhecimento":
            NewRecordHub(
                self.content, self._open_creator, self.knowledge_service,
                self.catalog_service, self.security_service, self.user
            ).pack(fill="both", expand=True)
            return
        if name == "Configurações":
            SettingsView(self.content, self.user, self.auth_service,
                         self.security_service).pack(fill="both", expand=True)
            return
        if name == "Recentes":
            RecentView(
                self.content, self.knowledge_service, self.user, self.security_service
            ).pack(fill="both", expand=True)
            return
        marked_pages = {
            "Favoritos": "favorito", "Contatos": "contato", "Cofre de Acessos": "cofre"
        }
        if name == "Cofre de Acessos":
            VaultAccessDialog(
                self, self.user, self.security_service,
                lambda: self._show_marked(name, marked_pages[name]))
            return
        if name in marked_pages:
            self._show_marked(name, marked_pages[name])
            return
        if name == "Categorias":
            CategoriesView(self.content, self.knowledge_service, self.user).pack(
                fill="both", expand=True)
            return
        if name == "Problemas":
            FilteredArticlesView(
                self.content, "Problemas", "problema", self.knowledge_service, self.user,
                on_create=lambda: self._open_creator("problem")).pack(
                fill="both", expand=True)
            return
        if name == "Usuários Sapiens":
            SapiensView(self.content, self.catalog_service).pack(fill="both", expand=True)
            return
        modules = {"Relatórios": "relatorio", "Telas Senior": "tela_senior",
                   "Tabelas de Banco": "banco", "Regras": "regra"}
        if name in modules:
            CatalogView(self.content, modules[name], self.catalog_service, self.user).pack(
                fill="both", expand=True)
            return
        ctk.CTkLabel(self.content, text=name, font=PAGE_TITLE_FONT).pack(pady=(45, 15))
        ctk.CTkLabel(self.content, text=self.PAGES[name], font=BODY_FONT).pack(pady=10)

    def _select_navigation(self, selected: str) -> None:
        """Destaca a página atual sem preencher todo o botão de verde."""
        self.active_page = selected
        for name, (button, indicator, icon) in self.navigation_items.items():
            active = name == selected
            color = LEAF_YELLOW if active else TEXT_LIGHT
            button.configure(
                fg_color=SURFACE_GREEN,
                text_color=color,
                border_color=LEAF_GREEN if active else LIGHT_GREEN,
            )
            icon.configure(text_color=color)
            indicator.configure(fg_color=LEAF_GREEN if active else "transparent")

    def _hover_navigation(self, name: str, hovering: bool) -> None:
        """Colore texto e borda no hover, além do fundo tratado pelo tema."""
        if name == self.active_page:
            return
        button, _indicator, icon = self.navigation_items[name]
        color = LEAF_YELLOW if hovering else TEXT_LIGHT
        button.configure(
            text_color=color,
            border_color=LEAF_GREEN if hovering else LIGHT_GREEN,
        )
        icon.configure(text_color=color)

    def _show_marked(self, name: str, mark_type: str) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        FilteredArticlesView(
            self.content, name, mark_type, self.knowledge_service, self.user,
            on_create=(lambda: self._open_creator(
                "contact" if mark_type == "contato" else "vault"
            )) if mark_type in {"contato", "cofre"} else None,
        ).pack(fill="both", expand=True)

    def show_search_results(self, term: str) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        SearchResultsView(
            self.content, term, self.knowledge_service, self.user, self.catalog_service
        ).pack(fill="both", expand=True)

    def _open_profile(self) -> None:
        ProfileDialog(self, self.user, self.auth_service, self._profile_updated)

    def _toggle_menu(self) -> None:
        """Reduz a sidebar sem destruir widgets ou perder a navegação atual."""
        self.menu_expanded = not self.menu_expanded
        width = self.SIDEBAR_WIDTH if self.menu_expanded else self.COLLAPSED_WIDTH
        self.menu.configure(width=width)
        self.menu_toggle.configure(text="‹" if self.menu_expanded else "›")

        if self.menu_expanded:
            self.menu.grid_columnconfigure(1, minsize=self.TOGGLE_RAIL_WIDTH)
            self.brand.grid_configure(padx=self.SIDEBAR_PADDING)
            self.brand_title.pack(side="left", padx=(8, 0))
            self.menu_logo.configure(size=(58, 40))
            self.user_details.pack(side="left", fill="both", expand=True, pady=10)
            self.user_card.configure(height=82)
            self.user_card.grid_configure(padx=self.SIDEBAR_PADDING)
            self.user_avatar.pack_configure(padx=(10, 4))
            self.navigation.grid_configure(padx=self.SIDEBAR_PADDING)
            self.footer.grid_configure(padx=self.SIDEBAR_PADDING)
            self.logout_button.configure(text="↪ Deslogar")
            self.exit_button.configure(text="Sair do programa")
            self.logout_button.configure(width=self.MENU_BUTTON_WIDTH)
            self.exit_button.configure(width=self.MENU_BUTTON_WIDTH)
            for button, _indicator, _icon in self.navigation_items.values():
                button.grid()
        else:
            self.menu.grid_columnconfigure(1, minsize=20)
            self.brand_title.pack_forget()
            self.menu_logo.configure(size=(42, 29))
            self.brand.grid_configure(padx=5)
            self.user_details.pack_forget()
            self.user_card.configure(height=54)
            self.user_card.grid_configure(padx=5)
            self.user_avatar.pack_configure(padx=0)
            self.navigation.grid_configure(padx=2)
            self.footer.grid_configure(padx=5)
            self.logout_button.configure(text="↪")
            self.exit_button.configure(text="×")
            self.logout_button.configure(width=42)
            self.exit_button.configure(width=42)
            for button, _indicator, _icon in self.navigation_items.values():
                button.grid_remove()

    def _profile_updated(self, updated: User) -> None:
        self.user = updated
        self.user_name.configure(text=self._short_user_name(updated))

    def _open_creator(self, kind: str) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        if kind == "categories":
            CategoriesView(self.content, self.knowledge_service, self.user).pack(
                fill="both", expand=True)
            return
        if kind in {"problem", "contact", "vault"}:
            KnowledgeView(
                self.content, self.knowledge_service, self.user, record_kind=kind
            ).pack(fill="both", expand=True)
            return
        if kind == "sapiens":
            SapiensView(self.content, self.catalog_service).pack(fill="both", expand=True)
            return
        module = {"report": "relatorio", "senior": "tela_senior",
                  "database": "banco", "rule": "regra"}[kind]
        CatalogView(self.content, module, self.catalog_service, self.user).pack(
            fill="both", expand=True)
