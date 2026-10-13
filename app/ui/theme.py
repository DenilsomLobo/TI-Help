import customtkinter as ctk
import ctypes
import sys

from app.utils.resources import resource_path

# Paleta oficial do TI Help. Os aliases semânticos abaixo permitem que cada
# componente descreva sua função sem espalhar códigos hexadecimais pelas telas.
BACKGROUND = "#080B0A"
SIDEBAR = "#0C100F"
SEARCH_BACKGROUND = "#111614"
SURFACE = "#171C1B"
BORDER = "#303535"
PRIMARY = "#00C853"
ACCENT = "#00F05A"
BUTTON_HOVER = "#232A28"
BUTTON_PRESSED = "#005D35"
BUTTON_DISABLED = "#202423"
BUTTON_TEXT = "#D5D7D5"
BUTTON_TEXT_DISABLED = "#666B69"

DEEP_GREEN = BACKGROUND
DARK_GREEN = BACKGROUND
SURFACE_GREEN = SURFACE
FIELD_GREEN = SURFACE
LIGHT_GREEN = BORDER
LEAF_GREEN = PRIMARY
LEAF_YELLOW = ACCENT
YELLOW_HOVER = ACCENT

# Texto e estados destrutivos são cores funcionais de acessibilidade, não cores
# decorativas da marca: garantem leitura e identificação clara de erros.
TEXT_LIGHT = "#F1F3F2"
TEXT_MUTED = "#A6ACAA"
DANGER = "#35191B"
DANGER_TEXT = "#FF4D4D"
DANGER_BORDER = "#7A292E"

# Use em ações principais como Salvar, Adicionar, Entrar e Cadastrar.
PRIMARY_BUTTON = {
    "fg_color": PRIMARY,
    "hover_color": ACCENT,
    "text_color": BACKGROUND,
    "border_color": ACCENT,
    "border_width": 1,
}
# Estilos locais para distinguir ações sem mudar todos os botões da aplicação.
SECONDARY_BUTTON = {
    "fg_color": SURFACE,
    "hover_color": BUTTON_PRESSED,
    "text_color": ACCENT,
    "border_color": PRIMARY,
    "border_width": 1,
}
QUIET_BUTTON = {
    "fg_color": SIDEBAR,
    "hover_color": BUTTON_HOVER,
    "text_color": TEXT_MUTED,
    "border_color": BORDER,
    "border_width": 1,
}
ACTION_BUTTON = {"height": 40, "corner_radius": 12}
# Inter é a família oficial. O Tk usa a fonte padrão do sistema como fallback
# quando ela ainda não estiver instalada (Segoe UI no Windows moderno).
FONT_FAMILY = "Inter"
PIXEL_FONT_FAMILY = FONT_FAMILY  # Alias temporário para telas já existentes.

LOGO_FONT = (FONT_FAMILY, 30, "bold")
PAGE_TITLE_FONT = (FONT_FAMILY, 24, "bold")
SECTION_TITLE_FONT = (FONT_FAMILY, 20, "bold")
NAVIGATION_FONT = (FONT_FAMILY, 15, "normal")
BODY_FONT = (FONT_FAMILY, 14, "normal")
SMALL_FONT = (FONT_FAMILY, 12, "normal")


def _load_bundled_font() -> bool:
    """Registra Inter somente neste processo, sem alterar o Windows do usuário."""
    if sys.platform != "win32":
        return False
    font_path = resource_path("assets/fonts/Inter-Variable.ttf")
    if not font_path.exists():
        return False
    # FR_PRIVATE impede que a fonte seja publicada para outros programas.
    return bool(ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0))


def configure_theme() -> None:
    """Define os padrões dos widgets antes da criação das telas."""
    _load_bundled_font()
    ctk.set_appearance_mode("dark")
    theme = ctk.ThemeManager.theme
    theme["CTkFont"]["family"] = FONT_FAMILY
    theme["CTkFont"]["size"] = 14
    theme["CTkFont"]["weight"] = "normal"
    theme["CTk"]["fg_color"] = [DEEP_GREEN, DEEP_GREEN]
    theme["CTkFrame"]["fg_color"] = [SURFACE_GREEN, SURFACE_GREEN]
    theme["CTkLabel"]["text_color"] = [TEXT_LIGHT, TEXT_LIGHT]
    theme["CTkButton"].update({
        "fg_color": [SURFACE, SURFACE],
        "hover_color": [BUTTON_HOVER, BUTTON_HOVER],
        "border_color": [BORDER, BORDER],
        "border_width": 1,
        "text_color": [BUTTON_TEXT, BUTTON_TEXT],
        "text_color_disabled": [BUTTON_TEXT_DISABLED, BUTTON_TEXT_DISABLED],
        "corner_radius": 10,
    })
    for widget in ("CTkEntry", "CTkTextbox"):
        theme[widget]["fg_color"] = [FIELD_GREEN, FIELD_GREEN]
        theme[widget]["border_color"] = [LIGHT_GREEN, LIGHT_GREEN]
        theme[widget]["text_color"] = [TEXT_LIGHT, TEXT_LIGHT]
    theme["CTkOptionMenu"]["fg_color"] = [LEAF_GREEN, LEAF_GREEN]
    theme["CTkOptionMenu"]["button_color"] = [LEAF_YELLOW, LEAF_YELLOW]
    theme["CTkOptionMenu"]["button_hover_color"] = [YELLOW_HOVER, YELLOW_HOVER]
    theme["CTkOptionMenu"]["text_color"] = [TEXT_LIGHT, TEXT_LIGHT]
