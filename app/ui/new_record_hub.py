from collections.abc import Callable

import customtkinter as ctk

from app.models.user import User
from app.services.catalog_service import CatalogService
from app.services.knowledge_service import KnowledgeService
from app.services.security_service import SecurityService
from app.ui.catalog_views import CatalogDetail, SapiensDetail
from app.ui.home_view import open_article_detail
from app.ui.navigation_icons import PAGE_ICONS
from app.ui.category_widgets import CategoryChips
from app.ui.theme import (DARK_GREEN, DEEP_GREEN, LEAF_YELLOW, LIGHT_GREEN,
                          PIXEL_FONT_FAMILY, TEXT_LIGHT, TEXT_MUTED)


class NewRecordHub(ctk.CTkFrame):
    """Central para criar e consultar registros de todos os módulos."""

    OPTIONS = (
        ("problem", "Problemas", "Documente um problema e sua solução"),
        ("contact", "Contatos", "Cadastre uma informação de contato"),
        ("vault", "Cofre de Acessos", "Guarde uma informação protegida"),
        ("categories", "Categorias", "Consulte, altere ou exclua categorias"),
        ("sapiens", "Usuários Sapiens", "Registre um usuário do sistema"),
        ("report", "Relatórios", "Documente um relatório"),
        ("senior", "Telas Senior", "Documente uma tela do Senior"),
        ("database", "Tabelas de Banco", "Descreva uma tabela e seus campos"),
        ("rule", "Regras", "Cadastre uma regra de negócio"),
    )

    def __init__(self, master, on_select: Callable[[str], None],
                 knowledge_service: KnowledgeService, catalog_service: CatalogService,
                 security_service: SecurityService, user: User) -> None:
        super().__init__(master, corner_radius=0, fg_color=DEEP_GREEN)
        self.knowledge_service = knowledge_service
        self.catalog_service = catalog_service
        self.security_service = security_service
        self.user = user

        ctk.CTkLabel(
            self, text="NOVO REGISTRO", font=(PIXEL_FONT_FAMILY, 24, "bold"),
            text_color=LEAF_YELLOW).pack(pady=(24, 5))
        ctk.CTkLabel(
            self, text="Selecione uma opção para um novo registro",
            font=(PIXEL_FONT_FAMILY, 15), text_color=TEXT_MUTED).pack(pady=(0, 12))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=45, pady=(0, 15))
        for column in range(3):
            grid.grid_columnconfigure(column, weight=1)
        for index, (key, title, description) in enumerate(self.OPTIONS):
            ctk.CTkButton(
                grid, text=f"{PAGE_ICONS.get(title, '🏷')}  {title}\n{description}",
                height=72, font=(PIXEL_FONT_FAMILY, 15, "normal"),
                text_color=TEXT_LIGHT, corner_radius=16, border_width=1,
                command=lambda value=key: on_select(value),
            ).grid(row=index // 3, column=index % 3, sticky="nsew", padx=7, pady=7)

        ctk.CTkLabel(
            self, text="REGISTROS SALVOS", font=(PIXEL_FONT_FAMILY, 20, "bold"),
            text_color=LEAF_YELLOW
        ).pack(anchor="w", padx=52, pady=(5, 7))
        self.records = ctk.CTkScrollableFrame(self)
        self.records.pack(fill="both", expand=True, padx=45, pady=(0, 22))
        self.refresh_records()

    def refresh_records(self) -> None:
        """Reúne os registros dos módulos em uma única grade visual."""
        for widget in self.records.winfo_children():
            widget.destroy()
        for column, weight in enumerate((0, 2, 1, 0)):
            self.records.grid_columnconfigure(column, weight=weight)
        for column, title in enumerate(("Tipo", "Título", "Categoria / detalhe", "Ação")):
            ctk.CTkLabel(
                self.records, text=title, font=(PIXEL_FONT_FAMILY, 13, "bold"),
                fg_color=DARK_GREEN, text_color=LEAF_YELLOW, corner_radius=6
            ).grid(row=0, column=column, padx=3, pady=3, sticky="ew")

        rows: list[tuple[str, str, str, Callable[[], None]]] = []
        for article in self.knowledge_service.search():
            marks = self.knowledge_service.marks_for(article.id, self.user.id)
            if "cofre" in marks:
                kind = "Cofre de Acessos"
                display_title = "Conteúdo protegido"
                categories = "Desbloqueie para visualizar"
            elif "contato" in marks:
                kind = "Contato"
                display_title = article.title
                categories = article.categories or [article.category]
            else:
                kind = "Problema"
                display_title = article.title
                categories = article.categories or [article.category]
            rows.append((
                kind, display_title, categories,
                lambda item=article, protected="cofre" in marks:
                    self._open_article(item, protected),
            ))

        module_names = {
            "relatorio": "Relatório", "banco": "Tabela de Banco", "regra": "Regra",
            "tela_senior": "Telas Senior"
        }
        for module, kind in module_names.items():
            for record in self.catalog_service.search(module):
                rows.append((
                    kind, record.title, record.categories or [record.category],
                    lambda item=record: CatalogDetail(
                        self, item, self.catalog_service, self.refresh_records),
                ))
        for sapiens_user in self.catalog_service.search_sapiens():
            rows.append((
                "Usuário Sapiens", sapiens_user.name,
                f"{sapiens_user.login} • {sapiens_user.sector}",
                lambda item=sapiens_user: SapiensDetail(
                    self, item, self.catalog_service, self.refresh_records),
            ))

        if not rows:
            ctk.CTkLabel(self.records, text="Nenhum registro salvo.").grid(
                row=1, column=0, columnspan=4, pady=22)
            return
        for row_index, (kind, title, detail, command) in enumerate(rows, start=1):
            for column, value in enumerate((kind, title, detail)):
                if column == 2 and isinstance(value, (list, tuple)):
                    CategoryChips(self.records, value).grid(
                        row=row_index, column=column, padx=3, pady=2, sticky="ew")
                    continue
                ctk.CTkLabel(
                    self.records, text=value or "—", anchor="w",
                    fg_color=LIGHT_GREEN if row_index % 2 else DARK_GREEN,
                    text_color=TEXT_LIGHT, corner_radius=5
                ).grid(row=row_index, column=column, padx=3, pady=2, sticky="ew")
            ctk.CTkButton(
                self.records, text="Abrir", width=70, command=command
            ).grid(row=row_index, column=3, padx=3, pady=2)

    def _open_article(self, article, protected: bool) -> None:
        open_detail = lambda: open_article_detail(
            self, article, self.knowledge_service, self.user, self.refresh_records)
        open_detail()
