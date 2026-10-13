from tkinter import messagebox

import customtkinter as ctk

from app.models.knowledge_article import KnowledgeArticle
from app.models.user import User
from app.services.knowledge_service import KnowledgeService, KnowledgeValidationError
from app.ui.home_view import open_article_detail, ArticleEditDialog
from app.ui.vault_guard import authorize_article
from app.ui.category_widgets import record_heading
from app.ui.text_field_layout import size_text_field
from app.ui.theme import ACTION_BUTTON, SECONDARY_BUTTON, QUIET_BUTTON
from app.ui.theme import (DANGER, DANGER_BORDER, DANGER_TEXT, DARK_GREEN,
                          LEAF_GREEN, LEAF_YELLOW, LIGHT_GREEN,
                          PIXEL_FONT_FAMILY, PRIMARY_BUTTON, SURFACE_GREEN,
                          TEXT_LIGHT, TEXT_MUTED)


class KnowledgeView(ctk.CTkFrame):
    """Tela de pesquisa e manutenção dos problemas e soluções."""

    def __init__(self, master, service: KnowledgeService, user: User,
                 record_kind: str = "problem") -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.service = service
        self.user = user
        self.record_kind = record_kind
        self.selected_marks = self._default_marks()
        self.selected_id: int | None = None
        self._build()
        self.refresh()

    def _build(self) -> None:
        page_title = {"contact": "Contatos", "vault": "Cofre de Acessos"}.get(
            self.record_kind, "Base de Conhecimento")
        ctk.CTkLabel(self, text=page_title,
                     font=(PIXEL_FONT_FAMILY, 24, "bold")).pack(anchor="w", padx=30, pady=(25, 15))

        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", padx=30)
        self.search_entry = ctk.CTkEntry(search_bar, height=40, placeholder_text="Pesquisar registros...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _event: self._search())
        ctk.CTkButton(search_bar, text="Pesquisar", width=110,
                      command=self._search, **SECONDARY_BUTTON, **ACTION_BUTTON).pack(side="left")

        navigation = ctk.CTkFrame(self, fg_color="transparent")
        navigation.pack(fill="x", padx=30, pady=(10, 8))
        self.page_buttons = {}
        for name in ("Cadastro", "Resultados"):
            button = ctk.CTkButton(
                navigation, text=name, width=130, bg_color="transparent",
                **SECONDARY_BUTTON, **ACTION_BUTTON,
                command=lambda page=name: self._show_page(page))
            button.pack(side="left", padx=(0, 8))
            self.page_buttons[name] = button

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self.pages = {name: ctk.CTkFrame(body, fg_color=SURFACE_GREEN, corner_radius=12)
                      for name in self.page_buttons}
        self.form = ctk.CTkScrollableFrame(self.pages["Cadastro"])
        self.form.pack(fill="both", expand=True)
        self._build_form()

        self.results = ctk.CTkScrollableFrame(
            self.pages["Resultados"], label_text="Resultados", height=230,
            border_width=1, border_color=LIGHT_GREEN)
        self.results.pack(side="bottom", fill="both", expand=True)
        self._show_page("Cadastro")

    def _show_page(self, name: str) -> None:
        # Ocultar preserva os widgets e o texto digitado ao alternar as páginas.
        for page_name, frame in self.pages.items():
            if page_name == name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_remove()
            style = PRIMARY_BUTTON if page_name == name else SECONDARY_BUTTON
            self.page_buttons[page_name].configure(**style)

    def _build_form(self) -> None:
        titles = {"problem": "Novo problema", "contact": "Novo contato",
                  "vault": "Novo registro protegido"}
        self.form_title = ctk.CTkLabel(self.form, text=titles.get(self.record_kind, "Novo registro"),
                                       font=(PIXEL_FONT_FAMILY, 20, "bold"))
        self.form_title.pack(pady=(20, 12))
        self.title_entry = self._entry("Título")
        self.selected_categories: list[str] = []
        category_bar = ctk.CTkFrame(self.form, fg_color="transparent")
        category_bar.pack(fill="x", padx=20, pady=6)
        categories = self.service.list_categories() or ["Geral"]
        self.category_menu = ctk.CTkOptionMenu(category_bar, values=categories)
        self.category_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(category_bar, text="Adicionar categoria", width=130,
                      command=self._add_selected_category, **SECONDARY_BUTTON, **ACTION_BUTTON).pack(side="left", padx=3)
        ctk.CTkButton(category_bar, text="+ Nova categoria", width=120,
                      command=self._new_category, **QUIET_BUTTON, **ACTION_BUTTON).pack(side="left", padx=(3, 0))
        self.category_chips = ctk.CTkFrame(self.form, fg_color="transparent")
        self.category_chips.pack(fill="x", padx=20)
        self._show_selected_categories()
        if self.record_kind == "problem":
            self.problem_text = self._textbox("Problema")
            self.solution_text = self._textbox("Solução")
            self.observation_text = self._textbox("Observação (opcional)")
        else:
            field_labels = {
                "contact": "Informações do contato",
                "vault": "Informações protegidas do acesso",
            }
            self.contact_info_text = self._textbox(
                field_labels.get(self.record_kind, "Informações do registro"))
        # O rodapé fica fora da rolagem: Salvar continua acessível em textos longos.
        self.message = ctk.CTkLabel(self.pages["Cadastro"], text="", wraplength=500)
        self.message.pack(pady=(4, 0))

        buttons = ctk.CTkFrame(self.pages["Cadastro"], fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=(8, 20))
        self.save_button = ctk.CTkButton(
            buttons, text="Salvar", width=150,
            command=self.save, **PRIMARY_BUTTON, **ACTION_BUTTON)
        self.save_button.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            buttons, text="Limpar", width=150,
            command=self.clear_form, **QUIET_BUTTON, **ACTION_BUTTON
        ).pack(side="left", padx=(6, 0))

    def _entry(self, placeholder: str):
        entry = ctk.CTkEntry(self.form, placeholder_text=placeholder, height=40)
        entry.pack(fill="x", padx=20, pady=6)
        return entry

    def _textbox(self, label: str):
        # O cartão e o contorno verde deixam evidente toda a área editável.
        field = ctk.CTkFrame(
            self.form, fg_color=SURFACE_GREEN, corner_radius=10,
            border_width=1, border_color=LIGHT_GREEN)
        field.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(field, text=label, text_color=LEAF_YELLOW).pack(
            anchor="w", padx=10, pady=(7, 2))
        textbox = ctk.CTkTextbox(
            field, height=320 if self.record_kind in {"contact", "vault"} else 220,
            fg_color=DARK_GREEN,
            border_width=1, border_color=LEAF_GREEN)
        textbox.pack(fill="x", padx=8, pady=(0, 8))
        size_text_field(textbox, label)
        return textbox

    def _search(self) -> None:
        self.refresh()
        self._show_page("Resultados")

    def refresh(self) -> None:
        for widget in self.results.winfo_children():
            widget.destroy()
        articles = (self.service.search_problems(self.search_entry.get())
                    if self.record_kind == "problem"
                    else self.service.search(self.search_entry.get()))
        if not articles:
            ctk.CTkLabel(self.results, text="Nenhum registro encontrado.").pack(pady=30)
            return
        for article in articles:
            self._article_card(article)

    def _article_card(self, article: KnowledgeArticle) -> None:
        # Cada resultado possui seu próprio contorno e áreas internas separadas.
        card = ctk.CTkFrame(
            self.results, fg_color=SURFACE_GREEN, corner_radius=10,
            border_width=1, border_color=LIGHT_GREEN)
        card.pack(fill="x", padx=6, pady=6)
        information = ctk.CTkFrame(card, fg_color="transparent")
        information.pack(fill="x", padx=12, pady=(9, 5))
        record_heading(information, article.title, article.categories or [article.category]).pack(
            fill="x", pady=2)
        actions = ctk.CTkFrame(
            card, fg_color=DARK_GREEN, corner_radius=7,
            border_width=1, border_color=LIGHT_GREEN)
        actions.pack(fill="x", padx=12, pady=(0, 9))
        ctk.CTkButton(actions, text="Abrir", width=90, **PRIMARY_BUTTON, **ACTION_BUTTON,
                      command=lambda item=article: open_article_detail(
                          self, item, self.service, self.user, self.refresh
                      )).pack(side="right", padx=4, pady=5)
        ctk.CTkButton(actions, text="✎ Editar", width=90, **SECONDARY_BUTTON, **ACTION_BUTTON,
                      command=lambda item=article: self.select(item)).pack(
                          side="right", padx=4, pady=5)
        ctk.CTkButton(actions, text="🗑 Excluir", width=90, **QUIET_BUTTON, **ACTION_BUTTON,
                      command=lambda item=article: self.delete(item)).pack(
                          side="right", padx=4, pady=5)

    def save(self) -> None:
        try:
            if self.record_kind == "problem":
                problem = self.problem_text.get("1.0", "end")
                solution = self.solution_text.get("1.0", "end")
                observation = self.observation_text.get("1.0", "end")
            else:
                problem = self.contact_info_text.get("1.0", "end")
                solution = ""
                observation = ""
            values = (
                self.title_entry.get(),
                problem,
                solution,
                self.selected_categories,
            )
            if self.selected_id is None:
                saved = self.service.create(
                    *values, created_by=self.user.id,
                    observation=observation
                )
            else:
                self.service.update(
                    self.selected_id, *values,
                    observation=observation
                )
                saved = self.service.get(self.selected_id)
            if saved is None:
                raise KnowledgeValidationError("O registro não foi encontrado.")
            current_marks = self.service.marks_for(saved.id, self.user.id)
            for mark_type in {"favorito", "contato", "cofre"}:
                if (mark_type in self.selected_marks) != (mark_type in current_marks):
                    self.service.toggle_mark(saved.id, self.user.id, mark_type)
            self.clear_form()
            self.refresh()
            self.message.configure(text="Registro salvo com sucesso.", text_color=LEAF_YELLOW)
        except KnowledgeValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def select(self, article: KnowledgeArticle) -> None:
        authorize_article(self, article, self.service, self.user,
                          lambda: self._select_authorized(article))

    def _select_authorized(self, article: KnowledgeArticle) -> None:
        marks = self.service.marks_for(article.id, self.user.id)
        kind = "vault" if "cofre" in marks else "contact" if "contato" in marks else "problem"
        if kind != self.record_kind:
            # Resultados podem incluir outro tipo: abrir seu editor evita campos errados.
            def saved(_updated):
                editor.destroy()
                self.refresh()
            editor = ArticleEditDialog(self, article, self.service, saved, record_kind=kind)
            return
        self._show_page("Cadastro")
        self.clear_form()
        self.selected_id = article.id
        self.form_title.configure(text="Editar registro")
        self.save_button.configure(text="Atualizar")
        self.title_entry.insert(0, article.title)
        self.selected_categories = list(article.categories) or [article.category]
        self._show_selected_categories()
        if self.record_kind == "problem":
            self.problem_text.insert("1.0", article.problem)
            self.solution_text.insert("1.0", article.solution)
            self.observation_text.insert("1.0", article.observation)
        else:
            self.contact_info_text.insert("1.0", article.problem)
        self.selected_marks = self.service.marks_for(article.id, self.user.id)

    def delete(self, article: KnowledgeArticle) -> None:
        authorize_article(self, article, self.service, self.user,
                          lambda: self._delete_authorized(article))

    def _delete_authorized(self, article: KnowledgeArticle) -> None:
        if not messagebox.askyesno("Confirmar exclusão", f"Excluir '{article.title}'?"):
            return
        self.service.delete(article.id)
        if self.selected_id == article.id:
            self.clear_form()
        self.refresh()

    def clear_form(self) -> None:
        self.selected_id = None
        titles = {"problem": "Novo problema", "contact": "Novo contato",
                  "vault": "Novo registro protegido"}
        self.form_title.configure(text=titles.get(self.record_kind, "Novo registro"))
        self.save_button.configure(text="Salvar")
        self.message.configure(text="")
        self.title_entry.delete(0, "end")
        self.selected_categories = []
        self._show_selected_categories()
        self.selected_marks = self._default_marks()
        if self.record_kind == "problem":
            self.problem_text.delete("1.0", "end")
            self.solution_text.delete("1.0", "end")
            self.observation_text.delete("1.0", "end")
        else:
            self.contact_info_text.delete("1.0", "end")

    def _add_selected_category(self) -> None:
        category = self.category_menu.get()
        if category and category not in self.selected_categories:
            self.selected_categories.append(category)
            self._show_selected_categories()

    def _show_selected_categories(self) -> None:
        for widget in self.category_chips.winfo_children():
            widget.destroy()
        if not self.selected_categories:
            ctk.CTkLabel(self.category_chips, text="Nenhuma categoria selecionada").pack(side="left")
        for category in self.selected_categories:
            ctk.CTkButton(
                self.category_chips, text=f"🏷 {category}  ×", height=28,
                fg_color=LEAF_GREEN, text_color=DARK_GREEN,
                command=lambda value=category: self._remove_category(value)
            ).pack(side="left", padx=(0, 6), pady=3)

    def _remove_category(self, category: str) -> None:
        self.selected_categories.remove(category)
        self._show_selected_categories()

    def _default_marks(self) -> set[str]:
        return {"contact": {"contato"}, "vault": {"cofre"}}.get(
            self.record_kind, set()).copy()

    def _new_category(self) -> None:
        dialog = ctk.CTkInputDialog(
            text="Digite o nome da nova categoria:", title="Nova categoria")
        name = dialog.get_input()
        if not name:
            return
        try:
            self.service.create_category(name)
            categories = self.service.list_categories()
            self.category_menu.configure(values=categories)
            self.category_menu.set(name.strip())
            self._add_selected_category()
        except KnowledgeValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")
