from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from app.models.user import User
from app.services.knowledge_service import KnowledgeService, KnowledgeValidationError
from app.ui.home_view import open_article_detail, ArticleEditDialog
from app.ui.vault_guard import authorize_article
from app.ui.category_widgets import record_heading
from app.services.security_service import SecurityService
from app.ui.theme import FONT_FAMILY, LEAF_YELLOW, PRIMARY_BUTTON, TEXT_MUTED
from app.ui.theme import (ACTION_BUTTON, SECONDARY_BUTTON, QUIET_BUTTON,
                          SURFACE, BORDER)


class FilteredArticlesView(ctk.CTkFrame):
    """Lista reutilizável para Favoritos, Contatos e itens do Cofre."""

    def __init__(self, master, title: str, mark_type: str,
                 service: KnowledgeService, user: User,
                 on_create: Callable[[], None] | None = None) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.mark_type, self.service, self.user = mark_type, service, user
        ctk.CTkLabel(self, text=title, font=(FONT_FAMILY, 24, "bold")).pack(
            anchor="w", padx=30, pady=(25, 15))
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=30)
        self.category = ctk.CTkOptionMenu(
            filters, values=["Todas"] + service.list_categories(),
            command=lambda _value: self.refresh())
        self.category.pack(side="left", padx=(0, 10))
        self.term = ctk.CTkEntry(filters, placeholder_text="Pesquisar...", height=40)
        self.term.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.term.bind("<Return>", lambda _event: self.refresh())
        ctk.CTkButton(filters, text="Pesquisar", width=100, command=self.refresh,
                      **SECONDARY_BUTTON, **ACTION_BUTTON).pack(side="right")
        if on_create is not None:
            labels = {"contato": "+ Novo contato", "cofre": "+ Novo acesso",
                      "problema": "+ Novo problema"}
            ctk.CTkButton(
                filters, text=labels[mark_type], command=on_create,
                **PRIMARY_BUTTON, **ACTION_BUTTON
            ).pack(side="right", padx=(0, 10))
        self.results = ctk.CTkScrollableFrame(self)
        self.results.pack(fill="both", expand=True, padx=30, pady=20)
        self.refresh()

    def refresh(self) -> None:
        for widget in self.results.winfo_children():
            widget.destroy()
        category = self.category.get()
        selected_category = "" if category == "Todas" else category
        if self.mark_type == "problema":
            articles = self.service.search_problems(self.term.get(), selected_category)
        else:
            articles = self.service.search_marked(
                self.user.id, self.mark_type, self.term.get(), selected_category)
        if not articles:
            ctk.CTkLabel(self.results, text="Nenhum registro encontrado.").pack(pady=25)
        for article in articles:
            card = ctk.CTkFrame(self.results, fg_color=SURFACE, corner_radius=14,
                                border_width=1, border_color=BORDER)
            card.pack(fill="x", padx=8, pady=5)
            record_heading(card, article.title, article.categories or [article.category]).pack(
                fill="x", padx=12, pady=8)
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkButton(
                actions, text="Visualizar", width=110, **PRIMARY_BUTTON, **ACTION_BUTTON,
                command=lambda item=article: open_article_detail(
                    self, item, self.service, self.user, self.refresh)
            ).pack(side="left", padx=4)
            ctk.CTkButton(actions, text="Editar", width=110, **SECONDARY_BUTTON, **ACTION_BUTTON,
                          command=lambda item=article: self._edit(item)).pack(side="left", padx=4)
            ctk.CTkButton(actions, text="Excluir", width=110, **QUIET_BUTTON, **ACTION_BUTTON,
                          command=lambda item=article: self._delete(item)).pack(side="left", padx=4)

    def _edit(self, article) -> None:
        def open_editor():
            def saved(_updated):
                editor.destroy()
                self.refresh()
            marks = self.service.marks_for(article.id, self.user.id)
            kind = "vault" if "cofre" in marks else "contact" if "contato" in marks else "problem"
            editor = ArticleEditDialog(self, article, self.service, saved, record_kind=kind)
        authorize_article(self, article, self.service, self.user, open_editor)

    def _delete(self, article) -> None:
        def delete_confirmed():
            if messagebox.askyesno("Confirmar exclusão", f"Excluir '{article.title}'?",
                                   parent=self):
                self.service.delete(article.id)
                self.refresh()
        authorize_article(self, article, self.service, self.user, delete_confirmed)


class CategoriesView(ctk.CTkFrame):
    def __init__(self, master, service: KnowledgeService, user: User) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.service, self.user = service, user
        ctk.CTkLabel(self, text="Categorias", font=(FONT_FAMILY, 24, "bold")).pack(
            anchor="w", padx=30, pady=(25, 15))
        ctk.CTkLabel(self, text="Categorias", font=(FONT_FAMILY, 20, "bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 10))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=30)
        self.new_name = ctk.CTkEntry(bar, placeholder_text="Nome da nova categoria")
        self.new_name.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(
            bar, text="+ Nova categoria", command=self.create, **PRIMARY_BUTTON).pack(side="right")
        self.message = ctk.CTkLabel(self, text="")
        self.message.pack()
        self.search = ctk.CTkEntry(self, placeholder_text="Pesquisar categorias...")
        self.search.pack(fill="x", padx=30, pady=5)
        self.search.bind("<KeyRelease>", lambda _event: self.refresh())
        self.content = ctk.CTkScrollableFrame(self)
        self.content.pack(fill="both", expand=True, padx=30, pady=15)
        self.refresh()

    def create(self) -> None:
        try:
            self.service.create_category(self.new_name.get())
            self.new_name.delete(0, "end")
            self.message.configure(text="Categoria criada.", text_color=LEAF_YELLOW)
            self.refresh()
        except KnowledgeValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def refresh(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        categories = [name for name in self.service.list_categories()
                      if self.search.get().strip().casefold() in name.casefold()]
        if not categories:
            ctk.CTkLabel(self.content, text="Nenhuma categoria encontrada.").grid(
                row=0, column=0, padx=8, pady=20)
        for column in range(3):
            self.content.grid_columnconfigure(column, weight=1)
        for index, category in enumerate(categories):
            card = ctk.CTkFrame(self.content, border_width=1, border_color=BORDER)
            card.grid(row=index // 3, column=index % 3, padx=8, pady=8, sticky="nsew")
            ctk.CTkButton(
                card, text=f"🏷\n{category}", height=75,
                font=(FONT_FAMILY, 15, "normal"),
                command=lambda value=category: self._show_category(value)
            ).pack(fill="x", padx=8, pady=8)
            ctk.CTkButton(card, text="Alterar", **SECONDARY_BUTTON,
                          command=lambda value=category: self._rename(value)).pack(
                              fill="x", padx=8, pady=4)
            ctk.CTkButton(card, text="Excluir", **QUIET_BUTTON,
                          command=lambda value=category: self._delete(value)).pack(
                              fill="x", padx=8, pady=(4, 8))

    def _rename(self, category: str) -> None:
        name = ctk.CTkInputDialog(text=f"Novo nome para '{category}':",
                                  title="Alterar categoria").get_input()
        if name is None:
            return
        try:
            self.service.rename_category(category, name)
            self.message.configure(text="Categoria atualizada.", text_color=LEAF_YELLOW)
            self.refresh()
        except KnowledgeValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def _delete(self, category: str) -> None:
        if not messagebox.askyesno("Excluir categoria", f"Excluir a categoria '{category}'?", parent=self):
            return
        try:
            self.service.delete_category(category)
            self.message.configure(text="Categoria excluída.", text_color=LEAF_YELLOW)
            self.refresh()
        except KnowledgeValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def _show_category(self, category: str) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()
        ctk.CTkButton(self.content, text="← Voltar às categorias", width=170,
                      command=self.refresh).pack(anchor="w", padx=8, pady=8)
        ctk.CTkLabel(self.content, text=f"🏷 {category}",
                     font=(FONT_FAMILY, 22, "bold")).pack(anchor="w", padx=10, pady=10)
        articles = self.service.search_problems(category=category)
        if not articles:
            ctk.CTkLabel(self.content, text="Nenhum problema nesta categoria.").pack(pady=20)
        for article in articles:
            record_heading(
                self.content, article.title, article.categories or [article.category],
                command=lambda item=article: open_article_detail(
                    self, item, self.service, self.user)
            ).pack(fill="x", padx=10, pady=4)


class RecentView(ctk.CTkFrame):
    def __init__(self, master, service: KnowledgeService, user: User,
                 security: SecurityService) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.service, self.user, self.security = service, user, security
        ctk.CTkLabel(self, text="Acessados recentemente",
                     font=(FONT_FAMILY, 24, "bold")).pack(anchor="w", padx=30, pady=(25, 15))
        content = ctk.CTkScrollableFrame(self)
        content.pack(fill="both", expand=True, padx=30, pady=(0, 25))
        articles = service.recent(user.id)
        if not articles:
            ctk.CTkLabel(content, text="Nenhum problema foi aberto recentemente.").pack(pady=25)
        for article in articles:
            is_vault = "cofre" in service.marks_for(article.id, user.id)
            prefix = "🔒 " if is_vault else "🕘 "
            record_heading(
                content, prefix + article.title, article.categories or [article.category],
                command=lambda item=article, protected=is_vault: self._open(item, protected)
            ).pack(fill="x", padx=8, pady=5)

    def _open(self, article, protected: bool) -> None:
        open_detail = lambda: open_article_detail(
            self, article, self.service, self.user)
        open_detail()
