"""Caixa de consulta que permite selecionar e copiar sem editar."""

import customtkinter as ctk

from app.ui.theme import DARK_GREEN, TEXT_LIGHT, LIGHT_GREEN


class ReadOnlyText(ctk.CTkTextbox):
    def __init__(self, master, text, height=160):
        super().__init__(master, height=height, wrap="word", fg_color=DARK_GREEN,
                         text_color=TEXT_LIGHT, border_width=1, border_color=LIGHT_GREEN)
        self.insert("1.0", text)
        # O estado bloqueia mudanças, mas mantém a seleção nativa do Tk.
        self.configure(state="disabled")
        self.bind("<Button-1>", lambda _event: self.focus_set())
        self.bind("<Control-a>", self._select_all)
        self.bind("<Control-c>", self._copy)

    def _select_all(self, _event):
        self.tag_add("sel", "1.0", "end-1c")
        return "break"

    def _copy(self, _event):
        if self.tag_ranges("sel"):
            self.clipboard_clear()
            self.clipboard_append(self.get("sel.first", "sel.last"))
        return "break"
