import customtkinter as ctk
from tkinter import messagebox

from app.models.user import User
from app.services.catalog_service import CatalogService, CatalogValidationError
from app.ui.theme import (DANGER, DANGER_BORDER, DANGER_TEXT, DARK_GREEN, LEAF_GREEN, LEAF_YELLOW,
                          FONT_FAMILY, LIGHT_GREEN, PRIMARY_BUTTON, SURFACE_GREEN, TEXT_LIGHT)
from app.ui.window_utils import configure_modal_window
from app.ui.category_widgets import CategoryChips, CategorySelector, record_heading
from app.ui.read_only_text import ReadOnlyText
from app.ui.text_field_layout import size_text_field
from app.ui.theme import ACTION_BUTTON, SECONDARY_BUTTON


class SapiensView(ctk.CTkFrame):
    def __init__(self, master, service: CatalogService) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.service = service
        ctk.CTkLabel(self, text="Usuários Sapiens", font=(FONT_FAMILY, 24, "bold")).pack(
            anchor="w", padx=30, pady=(25, 12))
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=30, pady=8)
        self.entries = [ctk.CTkEntry(form, placeholder_text=value) for value in
                        ("Nome", "Login", "Número", "Setor")]
        for entry in self.entries:
            entry.pack(side="left", fill="x", expand=True, padx=5, pady=15)
        ctk.CTkButton(
            form, text="Salvar", command=self.save, **PRIMARY_BUTTON).pack(side="right", padx=8)
        search = ctk.CTkFrame(self, fg_color="transparent")
        search.pack(fill="x", padx=30, pady=8)
        self.term = ctk.CTkEntry(search, placeholder_text="Pesquisar usuário Sapiens")
        self.term.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.term.bind("<Return>", lambda _event: self.refresh())
        ctk.CTkButton(search, text="Pesquisar", command=self.refresh).pack(side="right")
        self.message = ctk.CTkLabel(self, text=""); self.message.pack()
        self.results = ctk.CTkScrollableFrame(self)
        self.results.pack(fill="both", expand=True, padx=30, pady=8)
        self.refresh()

    def save(self) -> None:
        try:
            self.service.create_sapiens(*(entry.get() for entry in self.entries))
            for entry in self.entries: entry.delete(0, "end")
            self.message.configure(text="Usuário Sapiens cadastrado.", text_color=LEAF_YELLOW)
            self.refresh()
        except CatalogValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def refresh(self) -> None:
        for widget in self.results.winfo_children(): widget.destroy()
        headers = ("Nome", "Login", "Número", "Setor", "Ações")
        for column, title in enumerate(headers):
            self.results.grid_columnconfigure(column, weight=1)
            ctk.CTkLabel(self.results, text=title, font=(FONT_FAMILY, 14, "bold"),
                         fg_color=DARK_GREEN, text_color=LEAF_YELLOW, corner_radius=6).grid(
                row=0, column=column, padx=3, pady=3, sticky="ew")
        for row, item in enumerate(self.service.search_sapiens(self.term.get()), start=1):
            for column, value in enumerate((item.name, item.login, item.number, item.sector)):
                ctk.CTkButton(
                    self.results, text=value or "—", anchor="w", fg_color=SURFACE_GREEN,
                    text_color=TEXT_LIGHT, hover_color=LEAF_GREEN, command=lambda selected=item: SapiensDetail(
                        self, selected, self.service, self.refresh)
                ).grid(row=row, column=column, padx=3, pady=3, sticky="ew")
            actions = ctk.CTkFrame(self.results, fg_color="transparent")
            actions.grid(row=row, column=4, padx=3, pady=3, sticky="ew")
            ctk.CTkButton(actions, text="✎ Editar", width=60,
                          command=lambda selected=item: SapiensDetail(
                              self, selected, self.service, self.refresh)).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="🗑 Excluir", width=60, fg_color=DANGER,
                          text_color=DANGER_TEXT, border_color=DANGER_BORDER,
                          command=lambda selected=item: self._delete_sapiens(selected)).pack(side="left", padx=2)

    def _delete_sapiens(self, item) -> None:
        if messagebox.askyesno("Confirmar exclusão", f"Excluir '{item.name}'?", parent=self):
            self.service.delete_sapiens(item.id)
            self.refresh()


class CatalogView(ctk.CTkFrame):
    TITLES = {"relatorio": "Relatórios", "banco": "Tabelas de Banco de Dados",
              "regra": "Regras", "tela_senior": "Telas Senior"}

    def __init__(self, master, module: str, service: CatalogService, user: User) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.module, self.service, self.user = module, service, user
        ctk.CTkLabel(self, text=self.TITLES[module], font=(FONT_FAMILY, 24, "bold")).pack(
            anchor="w", padx=30, pady=(20, 8))
        # Todos os módulos usam rolagem para manter campos grandes acessíveis.
        navigation = ctk.CTkFrame(self, fg_color="transparent")
        navigation.pack(fill="x", padx=30, pady=4)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30, pady=4)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self.pages = {}
        self.page_buttons = {}
        for name in ("Cadastro", "Resultados"):
            self.pages[name] = ctk.CTkFrame(body, fg_color="transparent")
            button = ctk.CTkButton(
                navigation, text=name, **SECONDARY_BUTTON, **ACTION_BUTTON,
                command=lambda page=name: self._show_page(page))
            button.pack(side="left", padx=(0, 8))
            self.page_buttons[name] = button
        form_parent = self.pages["Cadastro"]
        results_parent = self.pages["Resultados"]
        self._show_page("Cadastro")
        form = ctk.CTkScrollableFrame(form_parent)
        form.pack(fill="both", expand=True)
        self.title_entry = ctk.CTkEntry(form, placeholder_text="Título")
        self.title_entry.pack(fill="x", padx=15, pady=(12, 5))
        category_row = ctk.CTkFrame(form, fg_color="transparent")
        category_row.pack(fill="x", padx=15, pady=4)
        self.category = CategorySelector(category_row, self.service.categories(module))
        self.category.pack(side="left", anchor="n", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            category_row, text="+ Categoria", command=self.new_category,
            **PRIMARY_BUTTON).pack(side="right", anchor="n")
        fields = ctk.CTkFrame(form, fg_color="transparent"); fields.pack(fill="x", padx=10)
        self.description = self._text(fields, "Descrição")
        self.purpose = self._text(fields, "O que faz")
        self.observation = self._text(fields, "Observações")
        ctk.CTkButton(
            form_parent,
            text="Salvar novo registro", command=self.save,
            **PRIMARY_BUTTON).pack(pady=10)
        tools = ctk.CTkFrame(results_parent, fg_color="transparent"); tools.pack(fill="x", padx=30, pady=5)
        self.term = ctk.CTkEntry(tools, placeholder_text=f"Pesquisar em {self.TITLES[module]}")
        self.term.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.term.bind("<Return>", lambda _event: self.refresh())
        ctk.CTkButton(tools, text="Pesquisar", command=self.refresh).pack(side="right")
        self.message = ctk.CTkLabel(self, text=""); self.message.pack()
        self.results = ctk.CTkScrollableFrame(results_parent)
        self.results.pack(fill="both", expand=True, padx=30, pady=5)
        self.refresh()

    def _show_page(self, name):
        for page_name, page in self.pages.items():
            if page_name == name:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_remove()
            self.page_buttons[page_name].configure(
                **(PRIMARY_BUTTON if page_name == name else SECONDARY_BUTTON))

    def _text(self, parent, placeholder):
        # O contorno diferencia cada área editável do fundo do formulário.
        column = ctk.CTkFrame(
            parent, fg_color=SURFACE_GREEN, corner_radius=10,
            border_width=1, border_color=LIGHT_GREEN)
        column.pack(side="top", fill="x", padx=5, pady=4)
        ctk.CTkLabel(column, text=placeholder, text_color=LEAF_YELLOW).pack(
            anchor="w", padx=10, pady=(4, 2))
        box = ctk.CTkTextbox(
            column, fg_color=DARK_GREEN,
            border_width=1, border_color=LEAF_GREEN)
        size_text_field(box, placeholder)
        box.pack(fill="x", padx=8, pady=(0, 5))
        return box

    def new_category(self) -> None:
        name = ctk.CTkInputDialog(text="Nome da categoria:", title="Nova categoria").get_input()
        if not name: return
        try:
            self.service.create_category(self.module, name)
            values = self.service.categories(self.module)
            self.category.set_values(values)
            self.category.set_selected(self.category.get() + [name.strip()])
        except CatalogValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def save(self) -> None:
        try:
            self.service.create(
                self.module, self.title_entry.get(), self.description.get("1.0", "end"),
                self.purpose.get("1.0", "end"), self.observation.get("1.0", "end"),
                self.category.get(), self.user.id)
            self.message.configure(text="Registro salvo.", text_color=LEAF_YELLOW)
            self.title_entry.delete(0, "end")
            for box in (self.description, self.purpose, self.observation):
                box.delete("1.0", "end")
            self.category.set_selected([])
            self.refresh()
        except CatalogValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def refresh(self) -> None:
        for widget in self.results.winfo_children(): widget.destroy()
        headers = ("Registro / categorias", "Descrição", "O que faz", "Observações", "Ações")
        for column, title in enumerate(headers):
            self.results.grid_columnconfigure(column, weight=1)
            ctk.CTkLabel(self.results, text=title, font=(FONT_FAMILY, 13, "bold"),
                         fg_color=DARK_GREEN, text_color=LEAF_YELLOW, corner_radius=6).grid(
                row=0, column=column, padx=3, pady=3, sticky="ew")
        for row, item in enumerate(self.service.search(self.module, self.term.get()), start=1):
            record_heading(
                self.results, item.title, item.categories or [item.category],
                command=lambda selected=item: CatalogDetail(
                    self, selected, self.service, self.refresh)
            ).grid(row=row, column=0, padx=3, pady=3, sticky="ew")
            values = (item.description, item.purpose, item.observation)
            for column, value in enumerate(values, start=1):
                ctk.CTkButton(
                    self.results, text=(value.strip()[:35] if value.strip() else "—"),
                    anchor="w", fg_color=SURFACE_GREEN, text_color=TEXT_LIGHT,
                    hover_color=LEAF_GREEN,
                    command=lambda selected=item: CatalogDetail(
                        self, selected, self.service, self.refresh)
                ).grid(row=row, column=column, padx=3, pady=3, sticky="ew")
            actions = ctk.CTkFrame(self.results, fg_color="transparent")
            actions.grid(row=row, column=4, padx=3, pady=3, sticky="ew")
            ctk.CTkButton(
                actions, text="✎", width=58,
                command=lambda selected=item: CatalogEditDialog(
                    self, selected, self.service, self.refresh)
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                actions, text="🗑", width=58, fg_color=DANGER, text_color=DANGER_TEXT,
                border_color=DANGER_BORDER,
                command=lambda selected=item: self._delete_record(selected)
            ).pack(side="left", padx=2)

    def _delete_record(self, item) -> None:
        if messagebox.askyesno("Confirmar exclusão", f"Excluir '{item.title}'?", parent=self):
            self.service.delete(item.id); self.refresh()


class SapiensDetail(ctk.CTkToplevel):
    def __init__(self, master, user, service: CatalogService, on_changed) -> None:
        super().__init__(master); configure_modal_window(self, master)
        self.title(user.name); self.geometry("480x430")
        self.user, self.service, self.on_changed = user, service, on_changed
        ctk.CTkLabel(self, text="Editar usuário Sapiens",
                     font=(FONT_FAMILY, 23, "bold")).pack(pady=24)
        self.entries = []
        for label, value in (("Nome", user.name), ("Login", user.login),
                             ("Número", user.number), ("Setor", user.sector)):
            entry = ctk.CTkEntry(self, placeholder_text=label)
            entry.pack(fill="x", padx=45, pady=6); entry.insert(0, value)
            self.entries.append(entry)
        self.message = ctk.CTkLabel(self, text=""); self.message.pack(pady=5)
        buttons = ctk.CTkFrame(self, fg_color="transparent"); buttons.pack(fill="x", padx=45)
        ctk.CTkButton(buttons, text="Salvar", command=self._save, **PRIMARY_BUTTON).pack(
            side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(buttons, text="🗑 Excluir", fg_color=DANGER, text_color=DANGER_TEXT,
                      border_color=DANGER_BORDER,
                      command=self._delete).pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _save(self) -> None:
        try:
            self.service.update_sapiens(self.user.id, *(entry.get() for entry in self.entries))
            self.on_changed(); self.destroy()
        except CatalogValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def _delete(self) -> None:
        if messagebox.askyesno("Confirmar exclusão", f"Excluir '{self.user.name}'?", parent=self):
            self.service.delete_sapiens(self.user.id); self.on_changed(); self.destroy()


class CatalogDetail(ctk.CTkToplevel):
    def __init__(self, master, record, service: CatalogService, on_changed=None) -> None:
        super().__init__(master); configure_modal_window(self, master)
        self.title(record.title); self.geometry("950x750")
        self.minsize(600, 450)
        self.service, self.record, self.on_changed = service, record, on_changed
        ctk.CTkLabel(self, text=record.title, font=(FONT_FAMILY, 24, "bold")).pack(pady=(12, 5))
        CategoryChips(self, record.categories or [record.category]).pack(fill="x", padx=35, pady=5)
        content = ctk.CTkScrollableFrame(self)
        content.pack(fill="both", expand=True, padx=25, pady=8)
        for title, value in (("Descrição", record.description),
                             ("O que faz", record.purpose), ("Observações", record.observation)):
            ctk.CTkLabel(content, text=title, text_color=LEAF_YELLOW,
                         anchor="w").pack(fill="x", padx=15, pady=(8, 3))
            box = ReadOnlyText(content, value)
            size_text_field(box, title)
            box.pack(fill="x", padx=15, pady=(0, 5))
        if record.module == "banco":
            self.editing_field_id: int | None = None
            self.fields = ctk.CTkFrame(self); self.fields.pack(fill="x", padx=35, pady=8)
            self.field_name = ctk.CTkEntry(self.fields, placeholder_text="Nome do campo")
            self.field_name.pack(side="left", fill="x", expand=True, padx=3)
            self.field_description = ctk.CTkEntry(self.fields, placeholder_text="Descrição")
            self.field_description.pack(side="left", fill="x", expand=True, padx=3)
            self.field_save_button = ctk.CTkButton(
                self.fields, text="+ Campo", width=100,
                command=self._save_field, **PRIMARY_BUTTON)
            self.field_save_button.pack(side="right", padx=3)
            self.field_list = ctk.CTkScrollableFrame(self, height=105)
            self.field_list.pack(fill="both", expand=True, padx=35, pady=5)
            self._refresh_fields()
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=35, pady=12)
        ctk.CTkButton(
            actions, text="✎ Editar",
            command=lambda: CatalogEditDialog(
                self, self.record, self.service, self._after_edit)
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(actions, text="🗑 Excluir", fg_color=DANGER, text_color=DANGER_TEXT,
                      border_color=DANGER_BORDER,
                      command=self._delete).pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _save_field(self) -> None:
        try:
            if self.editing_field_id is None:
                self.service.add_database_field(
                    self.record.id, self.field_name.get(), self.field_description.get())
            else:
                self.service.update_database_field(
                    self.editing_field_id, self.field_name.get(),
                    self.field_description.get())
            self._clear_field_editor()
            self._refresh_fields()
        except CatalogValidationError as error:
            messagebox.showerror("Campo inválido", str(error), parent=self)

    def _edit_field(self, field_id: int, name: str, description: str) -> None:
        """Carrega o campo escolhido no formulário para permitir sua alteração."""
        self.editing_field_id = field_id
        self.field_name.delete(0, "end")
        self.field_name.insert(0, name)
        self.field_description.delete(0, "end")
        self.field_description.insert(0, description)
        self.field_save_button.configure(text="Salvar edição")
        self.field_name.focus_set()

    def _clear_field_editor(self) -> None:
        self.editing_field_id = None
        self.field_name.delete(0, "end")
        self.field_description.delete(0, "end")
        self.field_save_button.configure(text="+ Campo")

    def _refresh_fields(self) -> None:
        for widget in self.field_list.winfo_children():
            widget.destroy()
        fields = self.service.database_field_entries(self.record.id)
        if not fields:
            ctk.CTkLabel(self.field_list, text="Nenhum campo cadastrado.").pack(pady=12)
            return
        for field_id, name, description in fields:
            row = ctk.CTkFrame(self.field_list, fg_color=SURFACE_GREEN)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=f"{name}: {description}", justify="left", anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10, pady=6)
            ctk.CTkButton(
                row, text="✎ Editar", width=82,
                command=lambda item_id=field_id, item_name=name, item_description=description:
                    self._edit_field(item_id, item_name, item_description)
            ).pack(side="right", padx=6, pady=4)

    def _after_edit(self) -> None:
        if self.on_changed: self.on_changed()
        self.destroy()

    def _delete(self) -> None:
        if messagebox.askyesno("Confirmar exclusão", f"Excluir '{self.record.title}'?", parent=self):
            self.service.delete(self.record.id)
            self.destroy()
            if self.on_changed: self.on_changed()


class CatalogEditDialog(ctk.CTkToplevel):
    def __init__(self, master, record, service: CatalogService, on_changed) -> None:
        super().__init__(master); configure_modal_window(self, master)
        self.title("Editar registro"); self.geometry("950x750")
        self.record, self.service, self.on_changed = record, service, on_changed
        ctk.CTkLabel(self, text="Editar registro", font=(FONT_FAMILY, 23, "bold")).pack(pady=18)
        self.minsize(600, 450)
        self.form = ctk.CTkScrollableFrame(self)
        self.form.pack(fill="both", expand=True, padx=20)
        self.title_entry = ctk.CTkEntry(self.form, placeholder_text="Título")
        self.title_entry.pack(fill="x", padx=35, pady=5); self.title_entry.insert(0, record.title)
        categories = service.categories(record.module) or ["Sem categoria"]
        self.category = CategorySelector(
            self.form, categories, record.categories or [record.category])
        self.category.pack(fill="x", padx=35, pady=5)
        self.description = self._text("Descrição", record.description)
        self.purpose = self._text("O que faz", record.purpose)
        self.observation = self._text("Observações", record.observation)
        self.message = ctk.CTkLabel(self, text=""); self.message.pack()
        ctk.CTkButton(
            self, text="Salvar alterações", command=self._save,
            **PRIMARY_BUTTON).pack(pady=8)

    def _text(self, label: str, value: str):
        ctk.CTkLabel(self.form, text=f"{label}:", text_color=LEAF_YELLOW).pack(
            anchor="w", padx=35)
        box = ctk.CTkTextbox(
            self.form,
            fg_color=DARK_GREEN, border_width=1, border_color=LEAF_GREEN,
            corner_radius=10)
        box.pack(fill="x", padx=35, pady=(4, 6))
        size_text_field(box, label)
        box.insert("1.0", value); return box

    def _save(self) -> None:
        try:
            self.service.update(
                self.record.id, self.record.module, self.title_entry.get(),
                self.description.get("1.0", "end"), self.purpose.get("1.0", "end"),
                self.observation.get("1.0", "end"),
                self.category.get())
            self.destroy()
            if self.on_changed: self.on_changed()
        except CatalogValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")
