from collections.abc import Callable
import customtkinter as ctk
from PIL import Image
from app.models.user import User
from app.services.auth_service import AuthenticationError, AuthService, ValidationError
from app.ui.theme import (DEEP_GREEN, LEAF_GREEN, LEAF_YELLOW, LIGHT_GREEN,
                          LOGO_FONT, PAGE_TITLE_FONT, PRIMARY_BUTTON,
                          SURFACE_GREEN, TEXT_LIGHT)
from app.ui.window_utils import apply_app_icon
from app.utils.resources import resource_path


class LoginView(ctk.CTkFrame):
    def __init__(self, master, service: AuthService, on_success: Callable[[User], None]) -> None:
        super().__init__(master, corner_radius=0, fg_color=DEEP_GREEN)
        self.service, self.on_success = service, on_success
        self.card = ctk.CTkFrame(
            self, width=480, fg_color=SURFACE_GREEN, corner_radius=20,
            border_width=1, border_color=LEAF_YELLOW)
        self.card.place(relx=.5, rely=.5, anchor="center")
        self._title("Configuração inicial" if service.needs_initial_admin() else "Entrar")
        if service.needs_initial_admin():
            self.name = self._entry("Nome completo")
        self.username = self._entry("Usuário")
        self.password = self._entry("Senha", True)
        if service.needs_initial_admin():
            self.confirmation = self._entry("Confirmar senha", True)
        self.message = ctk.CTkLabel(self.card, text="", text_color="#ff6b6b")
        self.message.pack(pady=5)
        initial = service.needs_initial_admin()
        # Enter executa a mesma ação do botão, inclusive no cadastro inicial.
        submit = self._create_initial_admin if initial else self._login
        fields = [self.username, self.password]
        if initial:
            fields.extend([self.name, self.confirmation])
        for field in fields:
            field.bind("<Return>", lambda _event: submit())
        ctk.CTkButton(self.card, text="Criar administrador" if initial else "Entrar",
                      command=submit, height=42, **PRIMARY_BUTTON).pack(
            padx=50, pady=(5, 10), fill="x")
        if not initial:
            links = ctk.CTkFrame(self.card, fg_color="transparent")
            links.pack(padx=50, pady=(0, 30), fill="x")
            ctk.CTkButton(links, text="Novo usuário", fg_color="transparent",
                          text_color=LEAF_YELLOW, hover_color=LEAF_GREEN,
                          command=lambda: AccountDialog(self, service, "register")).pack(side="left")
            ctk.CTkButton(links, text="Recuperar senha", fg_color="transparent",
                          text_color=LEAF_YELLOW, hover_color=LEAF_GREEN,
                          command=lambda: AccountDialog(self, service, "recover")).pack(side="right")

    def _title(self, text: str) -> None:
        ctk.CTkLabel(self.card, text="❖  TI Help", font=LOGO_FONT,
                     text_color=LEAF_YELLOW).pack(pady=(35, 5))
        ctk.CTkLabel(self.card, text=text, font=PAGE_TITLE_FONT).pack(pady=(3, 10))
        image_path = resource_path("assets/capa_login.png")
        if image_path.exists():
            # CTkImage mantém a proporção e conserva uma referência durante toda a tela.
            with Image.open(image_path) as source_image:
                cover = source_image.copy()
            image_size = (300, 208) if self.service.needs_initial_admin() else (360, 250)
            self.cover_image = ctk.CTkImage(
                light_image=cover,
                dark_image=cover,
                size=image_size,
            )
            ctk.CTkLabel(
                self.card, text="", image=self.cover_image, corner_radius=14
            ).pack(padx=45, pady=(0, 12))

    def _entry(self, placeholder: str, secret: bool = False):
        entry = ctk.CTkEntry(self.card, placeholder_text=placeholder, width=320,
                             height=42, show="*" if secret else "")
        entry.pack(padx=50, pady=7)
        return entry

    def _login(self) -> None:
        try:
            self.on_success(self.service.authenticate(self.username.get(), self.password.get()))
        except AuthenticationError as error:
            self.message.configure(text=str(error))

    def _create_initial_admin(self) -> None:
        """Cadastra o primeiro usuário sem sobrescrever métodos internos do Tkinter."""
        try:
            user = self.service.create_initial_admin(self.name.get(), self.username.get(),
                                                     self.password.get(), self.confirmation.get())
            self.on_success(user)
        except ValidationError as error:
            self.message.configure(text=str(error))


class AccountDialog(ctk.CTkToplevel):
    """Janela simples para cadastro ou solicitação de recuperação."""

    def __init__(self, master, service: AuthService, mode: str) -> None:
        super().__init__(master)
        apply_app_icon(self)
        self.service, self.mode = service, mode
        self.title("Novo usuário" if mode == "register" else "Recuperar senha")
        self.geometry("420x500" if mode == "register" else "420x430")
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        ctk.CTkLabel(self, text=self.title(), font=PAGE_TITLE_FONT).pack(pady=(25, 15))
        if mode == "register":
            self.name = self._entry("Nome completo")
        self.username = self._entry("Usuário")
        if mode in {"register", "recover"}:
            self.password = self._entry("Senha", True)
            self.confirmation = self._entry("Confirmar senha", True)
        self.message = ctk.CTkLabel(self, text="", wraplength=350)
        self.message.pack(pady=8)
        if mode == "register":
            ctk.CTkButton(
                self, text="Cadastrar", command=self._submit,
                **PRIMARY_BUTTON).pack(padx=45, pady=8, fill="x")
        else:
            ctk.CTkButton(
                self, text="Solicitar recuperação", command=self._request_recovery,
                **PRIMARY_BUTTON).pack(padx=45, pady=(8, 4), fill="x")
            ctk.CTkButton(
                self, text="Definir nova senha após aprovação",
                command=self._complete_recovery).pack(padx=45, pady=4, fill="x")

    def _entry(self, placeholder: str, secret: bool = False):
        entry = ctk.CTkEntry(self, placeholder_text=placeholder, show="*" if secret else "")
        entry.pack(padx=45, pady=7, fill="x")
        return entry

    def _submit(self) -> None:
        try:
            self.service.register_user(
                self.name.get(), self.username.get(), self.password.get(),
                self.confirmation.get()
            )
            self.message.configure(
                text="Usuário criado. Você já pode entrar.", text_color=LEAF_YELLOW)
        except ValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def _request_recovery(self) -> None:
        try:
            self.service.request_password_recovery(self.username.get())
            self.message.configure(
                text=("Solicitação registrada. Após a aprovação do administrador, "
                      "informe a nova senha e use o botão abaixo."),
                text_color=LEAF_YELLOW)
        except ValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")

    def _complete_recovery(self) -> None:
        try:
            self.service.complete_password_recovery(
                self.username.get(), self.password.get(), self.confirmation.get())
            self.message.configure(
                text="Senha redefinida. Você já pode entrar.", text_color=LEAF_YELLOW)
        except ValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")
