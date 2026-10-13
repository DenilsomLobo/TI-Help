"""Etiquetas e seleção de categorias compartilhadas pelas telas."""

import customtkinter as ctk

from app.ui.theme import DARK_GREEN, LEAF_GREEN, TEXT_LIGHT, SURFACE_GREEN


class CategoryChips(ctk.CTkFrame):
    """Distribui etiquetas em linhas para não cortar listas de categorias."""

    def __init__(self, master, values, on_remove=None):
        super().__init__(master, fg_color="transparent", height=1)
        self.chips = []
        for value in dict.fromkeys(value for value in values if value):
            if on_remove:
                chip = ctk.CTkButton(
                    self, text=f"{value}  ×", width=30, height=28,
                    fg_color=DARK_GREEN, border_color=LEAF_GREEN, border_width=1,
                    text_color=TEXT_LIGHT, hover_color=SURFACE_GREEN,
                    command=lambda name=value: on_remove(name))
            else:
                chip = ctk.CTkLabel(
                    self, text=value, height=28, corner_radius=7,
                    fg_color="#005D35", text_color=TEXT_LIGHT, padx=10)
            self.chips.append(chip)
        self.bind("<Configure>", self._layout)

    def _layout(self, event):
        available = max(event.width, 1)
        row = column = used = 0
        for chip in self.chips:
            width = chip.winfo_reqwidth() + 8
            if used and used + width > available:
                row += 1
                column = used = 0
            chip.grid(row=row, column=column, padx=(0, 8), pady=3, sticky="w")
            used += width
            column += 1


class CategorySelector(ctk.CTkFrame):
    """Escolhe categorias existentes e mostra a seleção como etiquetas removíveis."""

    def __init__(self, master, values, selected=(), multiple=True):
        super().__init__(master, fg_color="transparent", height=1)
        self.multiple = multiple
        self.selected = list(dict.fromkeys(selected))
        controls = ctk.CTkFrame(self, fg_color="transparent", height=28)
        controls.pack(fill="x")
        self.menu = ctk.CTkOptionMenu(controls, values=list(values) or ["Sem categorias"])
        self.menu.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(controls, text="Adicionar categoria" if multiple else "Selecionar categoria",
                      command=self._add).pack(side="left")
        self.chips = None
        self.set_selected(self.selected)

    def _add(self):
        value = self.menu.get()
        if value == "Sem categorias":
            return
        self.set_selected(self.selected + [value] if self.multiple else [value])

    def set_selected(self, values):
        self.selected = list(dict.fromkeys(values))
        if self.chips is not None:
            self.chips.destroy()
        self.chips = CategoryChips(self, self.selected, self._remove)
        # Sem seleção, não reservar uma área vazia abaixo dos controles.
        if self.selected:
            self.chips.pack(fill="x", pady=(3, 0))

    def _remove(self, value):
        self.set_selected([name for name in self.selected if name != value])

    def get(self):
        return list(self.selected)

    def set_values(self, values):
        self.menu.configure(values=list(values) or ["Sem categorias"])


def record_heading(master, title, categories, command=None):
    """Título seguido de etiquetas, separado dos botões de ação do registro."""
    row = ctk.CTkFrame(master, fg_color="transparent")
    row.grid_columnconfigure(1, weight=1)
    if command:
        label = ctk.CTkButton(row, text=title, anchor="w", width=220,
                             fg_color=SURFACE_GREEN, command=command)
    else:
        label = ctk.CTkLabel(row, text=title, anchor="w", wraplength=320)
    label.grid(row=0, column=0, padx=(0, 12), pady=4, sticky="w")
    CategoryChips(row, categories).grid(row=0, column=1, sticky="ew")
    return row
