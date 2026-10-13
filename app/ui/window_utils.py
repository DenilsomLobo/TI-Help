import customtkinter as ctk

from app.utils.resources import resource_path


def apply_app_icon(window: ctk.CTk | ctk.CTkToplevel) -> None:
    """Aplica o ícone do TI Help em uma janela principal ou secundária."""
    icon_path = resource_path("assets/ti_help.ico")
    if icon_path.exists():
        window.iconbitmap(str(icon_path))


def configure_modal_window(window: ctk.CTkToplevel, master) -> None:
    """Mantém uma janela secundária vinculada e à frente de sua janela pai."""
    apply_app_icon(window)
    window.transient(master.winfo_toplevel())
    window.grab_set()
    window.after_idle(window.lift)
    window.after_idle(window.focus_force)
