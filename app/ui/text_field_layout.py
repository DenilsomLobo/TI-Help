"""Altura visual dos campos, sem limitar a quantidade de texto armazenado."""

from math import ceil
from tkinter.font import Font


def size_text_field(box, label: str) -> None:
    lines = {"Problema": 4, "Solução": 15,
             "Informações do contato": 15, "Informações protegidas do acesso": 15,
             "Descrição": 6, "O que faz": 20, "Observações": 3,
             "Observação": 3, "Observação (opcional)": 3}.get(label)
    if lines is None:
        return
    # O Tk mede a fonte em pixels; CTk recebe altura sem a escala do Windows.
    font = Font(root=box, font=box._textbox.cget("font"))
    text_height = lines * font.metrics("linespace")
    text_padding = 2 * int(box._textbox.cget("pady"))
    margin = max(box.cget("corner_radius"),
                 box.cget("border_width") + box.cget("border_spacing"))
    box.configure(height=ceil(box._reverse_widget_scaling(text_height + text_padding)
                              + 2 * margin), wrap="word")
