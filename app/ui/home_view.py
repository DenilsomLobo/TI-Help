import customtkinter as ctk
from collections.abc import Callable
from tkinter import Canvas, messagebox
from PIL import Image, ImageOps, ImageTk

from app.models.knowledge_article import KnowledgeArticle
from app.services.knowledge_service import KnowledgeService
from app.models.user import User
from app.services.catalog_service import CatalogService
from app.ui.theme import (DANGER, DANGER_BORDER, DANGER_TEXT, DARK_GREEN, LEAF_GREEN, LEAF_YELLOW, LIGHT_GREEN,
                          BUTTON_PRESSED, FONT_FAMILY, PIXEL_FONT_FAMILY, PRIMARY_BUTTON,
                          SEARCH_BACKGROUND, SURFACE_GREEN, TEXT_LIGHT, TEXT_MUTED,
                          BACKGROUND)
from app.ui.window_utils import apply_app_icon
from app.ui.vault_guard import authorize_article
from app.ui.category_widgets import CategoryChips, CategorySelector, record_heading
from app.ui.read_only_text import ReadOnlyText
from app.ui.text_field_layout import size_text_field
from app.ui.theme import ACTION_BUTTON, SECONDARY_BUTTON, QUIET_BUTTON
from app.utils.resources import resource_path


class HomeView(ctk.CTkFrame):
    """Página inicial com acesso rápido à pesquisa da base."""

    def __init__(self, master, on_search: Callable[[str], None]) -> None:
        super().__init__(master, corner_radius=0, fg_color=BACKGROUND)
        self.on_search = on_search
        self.background_source = self._open_asset("assets/fundo", "RGB")
        self.logo_source = self._open_asset("assets/logo_meio_tela", "RGBA")
        self.background_resize_job = None
        self.canvas = Canvas(
            self, background=BACKGROUND, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._schedule_background_resize)
        self.background_item = self.canvas.create_image(0, 0, anchor="nw")
        self.logo_item = self.canvas.create_image(0, 0, anchor="center")
        self.heading_light = self.canvas.create_text(
            0, 0, text="Qual é seu ", anchor="e", fill=TEXT_LIGHT,
            font=(FONT_FAMILY, 40, "bold"))
        self.heading_green = self.canvas.create_text(
            0, 0, text="problema?", anchor="w", fill=LEAF_YELLOW,
            font=(FONT_FAMILY, 40, "bold"))
        self.search_shape = self.canvas.create_polygon(
            0, 0, 0, 0, fill=SEARCH_BACKGROUND, outline=BUTTON_PRESSED,
            width=1, smooth=True, splinesteps=24)
        self.search_icon = self.canvas.create_text(
            0, 0, text="⌕", fill=TEXT_MUTED, font=("Segoe UI Symbol", 28))
        self.search_entry = ctk.CTkEntry(
            self, width=300, height=48, border_width=0,
            fg_color=SEARCH_BACKGROUND, bg_color=SEARCH_BACKGROUND,
            placeholder_text="Pesquise por problema, erro ou solução...",
        )
        self.search_entry.bind("<Return>", lambda _event: self.search())
        self.search_entry.bind("<FocusIn>", lambda _event: self._set_search_focus(True))
        self.search_entry.bind("<FocusOut>", lambda _event: self._set_search_focus(False))
        self.search_button = ctk.CTkButton(
            self, text="⌕  Pesquisar", height=46, width=145,
            bg_color=SEARCH_BACKGROUND, command=self.search, **PRIMARY_BUTTON)


    @staticmethod
    def _open_asset(relative_path: str, mode: str) -> Image.Image | None:
        path = resource_path(relative_path)
        if not path.exists():
            return None
        with Image.open(path) as source_image:
            return source_image.convert(mode).copy()

    def _set_search_focus(self, focused: bool) -> None:
        """Realça o conjunto da pesquisa quando o campo recebe foco."""
        self.canvas.itemconfigure(
            self.search_shape, outline=LEAF_GREEN if focused else BUTTON_PRESSED)

    @staticmethod
    def _rounded_points(x1: float, y1: float, x2: float, y2: float,
                        radius: float) -> tuple[float, ...]:
        """Retorna pontos suavizados para uma caixa arredondada no Canvas."""
        return (
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        )

    def _schedule_background_resize(self, event=None) -> None:
        """Agrupa eventos rápidos de redimensionamento para evitar trabalho repetido."""
        if event is not None:
            self.pending_canvas_size = (event.width, event.height)
        if self.background_resize_job is not None:
            self.after_cancel(self.background_resize_job)
        self.background_resize_job = self.after(40, self._resize_background)

    def _resize_background(self) -> None:
        """Preenche a home preservando a proporção original da imagem de fundo."""
        self.background_resize_job = None
        width, height = getattr(
            self, "pending_canvas_size",
            (self.canvas.winfo_width(), self.canvas.winfo_height()),
        )
        if width < 10 or height < 10:
            return
        if self.background_source is not None:
            fitted = ImageOps.fit(
                self.background_source, (width, height), method=Image.Resampling.LANCZOS)
            self.background_image = ImageTk.PhotoImage(fitted)
            self.canvas.itemconfigure(self.background_item, image=self.background_image)

        # 255 px é um aumento exato de 70% sobre os 150 px anteriores.
        if self.logo_source is not None:
            logo = ImageOps.contain(
                self.logo_source, (255, 255), method=Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(logo)
            self.canvas.itemconfigure(self.logo_item, image=self.logo_image)

        center_x = width / 2
        logo_y = max(145, height * .30)
        heading_y = logo_y + 160
        self.canvas.coords(self.logo_item, center_x, logo_y)
        self.canvas.coords(self.heading_light, center_x, heading_y)
        self.canvas.coords(self.heading_green, center_x, heading_y)

        bar_width = width * .82
        bar_x = (width - bar_width) / 2
        bar_y = height * .67 - 29
        self.canvas.coords(
            self.search_shape,
            *self._rounded_points(bar_x, bar_y, bar_x + bar_width, bar_y + 58, 18),
        )
        self.canvas.coords(self.search_icon, bar_x + 28, bar_y + 29)
        entry_width = max(120, bar_width - 215)
        self.search_entry.configure(width=entry_width)
        self.search_entry.place(x=bar_x + 48, y=bar_y + 5)
        self.search_button.place(x=bar_x + bar_width - 151, y=bar_y + 6)

    def search(self) -> None:
        self.on_search(self.search_entry.get().strip())


class SearchResultsView(ctk.CTkFrame):
    def __init__(self, master, term: str, service: KnowledgeService, user: User,
                 catalog: CatalogService) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.service, self.user = service, user
        ctk.CTkLabel(self, text=f"Pesquisa geral: {term or 'todos'}",
                     font=(PIXEL_FONT_FAMILY, 24, "bold")).pack(anchor="w", padx=35, pady=(30, 15))
        self.results = ctk.CTkScrollableFrame(self)
        self.results.pack(fill="both", expand=True, padx=35, pady=(0, 25))
        articles = service.search(term)
        found = bool(articles)
        if articles:
            ctk.CTkLabel(self.results, text="Problemas", font=(PIXEL_FONT_FAMILY, 18, "bold")).pack(
                anchor="w", padx=8, pady=(8, 3))
        for article in articles:
            record_heading(
                self.results, article.title, article.categories or [article.category],
                command=lambda item=article: open_article_detail(
                    self, item, self.service, self.user
                ),
            ).pack(fill="x", padx=8, pady=5)
        from app.ui.catalog_views import CatalogDetail
        for module, title in (("relatorio", "Relatórios"), ("banco", "Tabelas de Banco"),
                              ("regra", "Regras"), ("tela_senior", "Telas Senior")):
            records = catalog.search(module, term)
            found = found or bool(records)
            if records:
                ctk.CTkLabel(self.results, text=title, font=(PIXEL_FONT_FAMILY, 18, "bold")).pack(
                    anchor="w", padx=8, pady=(12, 3))
            for record in records:
                record_heading(
                    self.results, record.title, record.categories or [record.category],
                    command=lambda item=record: CatalogDetail(self, item, catalog)
                ).pack(fill="x", padx=8, pady=4)
        sapiens = catalog.search_sapiens(term)
        found = found or bool(sapiens)
        if sapiens:
            ctk.CTkLabel(self.results, text="Usuários Sapiens",
                         font=(PIXEL_FONT_FAMILY, 18, "bold")).pack(anchor="w", padx=8, pady=(12, 3))
        for item in sapiens:
            ctk.CTkLabel(self.results, text=f"{item.name} • {item.login} • {item.setor}",
                         anchor="w").pack(fill="x", padx=12, pady=4)
        if not found:
            ctk.CTkLabel(self.results, text="Nenhum registro encontrado.").pack(pady=25)


def open_article_detail(master, article, service, user, on_changed=None):
    authorize_article(master, article, service, user,
                      lambda: ArticleDetailDialog(master, article, service, user, on_changed))


class ArticleDetailDialog(ctk.CTkToplevel):
    LABELS = {"favorito": "★ Favorito", "cofre": "🔒 Cofre"}

    def __init__(self, master, article: KnowledgeArticle,
                 service: KnowledgeService, user: User, on_changed=None) -> None:
        super().__init__(master)
        apply_app_icon(self)
        self.title(article.title)
        self.geometry("950x700")
        self.minsize(600, 450)
        self.transient(master.winfo_toplevel())
        self.article, self.service, self.user = article, service, user
        self.on_changed = on_changed
        self.service.record_recent(article.id, user.id)
        ctk.CTkLabel(self, text=article.title, font=(PIXEL_FONT_FAMILY, 24, "bold"),
                     wraplength=620).pack(padx=35, pady=(30, 5))
        CategoryChips(self, article.categories or [article.category]).pack(
            fill="x", padx=35, pady=(0, 20))
        self.content = ctk.CTkScrollableFrame(self)
        self.content.pack(fill="both", expand=True, padx=25)
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=35, pady=25)
        self.mark_buttons = {}
        for mark_type in self.LABELS:
            button = ctk.CTkButton(
                actions, **SECONDARY_BUTTON, **ACTION_BUTTON,
                command=lambda value=mark_type: self._toggle(value)
            )
            button.pack(side="left", padx=5, expand=True, fill="x")
            self.mark_buttons[mark_type] = button
        self._refresh_marks()
        management = ctk.CTkFrame(self, fg_color="transparent")
        management.pack(fill="x", padx=35, pady=(0, 20))
        ctk.CTkButton(management, text="✎ Editar", **SECONDARY_BUTTON, **ACTION_BUTTON,
                      command=self._edit).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(management, text="🗑 Excluir", **QUIET_BUTTON, **ACTION_BUTTON,
                      command=self._delete).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _section(self, title: str, content: str) -> None:
        ctk.CTkLabel(self.content, text=title, font=(PIXEL_FONT_FAMILY, 17, "bold"),
                     anchor="w").pack(fill="x", padx=35, pady=(10, 3))
        box = ReadOnlyText(self.content, content)
        size_text_field(box, title)
        box.pack(fill="x", padx=35, pady=(0, 8))

    def _render_sections(self, marks: set[str]) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        title = ("Informações protegidas do acesso" if "cofre" in marks else
                 "Informações do contato" if "contato" in marks else "Problema")
        self._section(title, self.article.problem)
        # Registros antigos podem conter solução mesmo após virarem contato/cofre.
        if title == "Problema" or self.article.solution:
            self._section("Solução" if title == "Problema" else "Informações adicionais",
                          self.article.solution)
        if self.article.observation:
            self._section("Observação", self.article.observation)

    def _toggle(self, mark_type: str) -> None:
        authorize_article(self, self.article, self.service, self.user,
                          lambda: self._apply_toggle(mark_type))

    def _apply_toggle(self, mark_type: str) -> None:
        self.service.toggle_mark(self.article.id, self.user.id, mark_type)
        self._refresh_marks()

    def _refresh_marks(self) -> None:
        marks = self.service.marks_for(self.article.id, self.user.id)
        self._render_sections(marks)
        for mark_type, button in self.mark_buttons.items():
            button.configure(
                text=self.LABELS[mark_type] + (" ✓" if mark_type in marks else ""),
                fg_color=LEAF_GREEN if mark_type in marks else SURFACE_GREEN,
                text_color=DARK_GREEN if mark_type in marks else TEXT_LIGHT,
            )

    def _edit(self) -> None:
        marks = self.service.marks_for(self.article.id, self.user.id)
        kind = "vault" if "cofre" in marks else "contact" if "contato" in marks else "problem"
        authorize_article(self, self.article, self.service, self.user,
                          lambda: ArticleEditDialog(
                              self, self.article, self.service, self._changed, record_kind=kind))

    def _delete(self) -> None:
        authorize_article(self, self.article, self.service, self.user, self._delete_confirmed)

    def _delete_confirmed(self) -> None:
        if not messagebox.askyesno("Confirmar exclusão", f"Excluir '{self.article.title}'?",
                                   parent=self):
            return
        self.service.delete(self.article.id)
        if self.on_changed:
            self.on_changed()
        self.destroy()

    def _changed(self, updated: KnowledgeArticle) -> None:
        self.article = updated
        if self.on_changed:
            self.on_changed()
        self.destroy()


class ArticleEditDialog(ctk.CTkToplevel):
    def __init__(self, master, article: KnowledgeArticle,
                 service: KnowledgeService, on_saved, record_kind: str = "problem") -> None:
        super().__init__(master)
        apply_app_icon(self)
        self.article, self.service, self.on_saved = article, service, on_saved
        self.record_kind = record_kind
        title = {"problem": "Editar problema", "contact": "Editar contato",
                 "vault": "Editar acesso protegido"}[record_kind]
        self.title(title); self.geometry("950x750")
        self.minsize(600, 450)
        self.transient(master.winfo_toplevel()); self.grab_set()
        ctk.CTkLabel(self, text=title, font=(PIXEL_FONT_FAMILY, 23, "bold")).pack(pady=18)
        self.content = ctk.CTkScrollableFrame(self)
        self.content.pack(fill="both", expand=True, padx=20)
        self.title_entry = ctk.CTkEntry(self.content, placeholder_text="Título", height=40)
        self.title_entry.pack(fill="x", padx=35, pady=5); self.title_entry.insert(0, article.title)
        self.categories = CategorySelector(
            self.content, service.list_categories(), article.categories or [article.category])
        self.categories.pack(fill="x", padx=35, pady=5)
        label = {"problem": "Problema", "contact": "Informações do contato",
                 "vault": "Informações protegidas do acesso"}[record_kind]
        self.problem = self._text(label, article.problem)
        self.solution = self.observation = None
        if record_kind == "problem":
            self.solution = self._text("Solução", article.solution)
            self.observation = self._text("Observação", article.observation)
        self.message = ctk.CTkLabel(self, text=""); self.message.pack()
        ctk.CTkButton(
            self, text="Salvar alterações", command=self._save,
            **PRIMARY_BUTTON, **ACTION_BUTTON).pack(pady=10)

    def _text(self, label: str, value: str):
        ctk.CTkLabel(self.content, text=f"{label}:", text_color=LEAF_YELLOW).pack(
            anchor="w", padx=35, pady=(12, 4))
        # O contorno separa cada área editável do fundo e dos campos vizinhos.
        box = ctk.CTkTextbox(
            self.content, height=240, fg_color=DARK_GREEN,
            border_width=1, border_color=LEAF_GREEN, corner_radius=10)
        box.pack(fill="x", padx=35, pady=(0, 8))
        box.insert("1.0", value)
        size_text_field(box, label)
        return box

    def _save(self) -> None:
        try:
            # Campos que não pertencem a esta tela preservam eventuais dados antigos.
            solution = (self.solution.get("1.0", "end") if self.solution is not None
                        else self.article.solution)
            observation = (self.observation.get("1.0", "end") if self.observation is not None
                           else self.article.observation)
            self.service.update(
                self.article.id, self.title_entry.get(), self.problem.get("1.0", "end"),
                solution,
                self.categories.get(),
                observation)
            updated = self.service.get(self.article.id)
            if updated:
                self.on_saved(updated)
        except ValueError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")
