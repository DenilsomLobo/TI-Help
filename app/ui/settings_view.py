from collections.abc import Callable

import customtkinter as ctk

from app.models.user import User
from app.services.auth_service import AuthenticationError, AuthService, ValidationError
from app.services.security_service import SecurityService, SecurityValidationError
from app.ui.theme import (DANGER, DANGER_BORDER, DANGER_TEXT, DARK_GREEN, LEAF_GREEN, LEAF_YELLOW,
                          FONT_FAMILY, PRIMARY_BUTTON, TEXT_LIGHT)
from app.ui.window_utils import apply_app_icon, configure_modal_window


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, user: User, auth: AuthService,
                 security: SecurityService) -> None:
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.user, self.auth, self.security = user, auth, security
        ctk.CTkLabel(self, text="Configurações", font=(FONT_FAMILY, 24, "bold")).pack(
            anchor="w", padx=30, pady=(25, 15))
        self.message = ctk.CTkLabel(self, text="")
        self.message.pack()
        self.content = ctk.CTkScrollableFrame(self)
        self.content.pack(fill="both", expand=True, padx=30, pady=10)
        self._pending_signature: tuple = ()
        self.refresh()
        self.after(1500, self._poll_requests)

    def refresh(self) -> None:
        """Reconstrói os dados para refletir alterações sem reabrir a página."""
        if self.user.role == "Administrador":
            # Mantém nome e login atuais quando o administrador edita a própria conta.
            self.user = next(
                (item for item in self.auth.list_users(self.user)
                 if item.id == self.user.id),
                self.user,
            )
        for widget in self.content.winfo_children():
            widget.destroy()
        self._vault_section()
        if self.user.role == "Administrador":
            self._admin_section()

    def _vault_section(self) -> None:
        frame = ctk.CTkFrame(self.content)
        frame.pack(fill="x", padx=5, pady=8)
        ctk.CTkLabel(frame, text="Segurança e recuperação",
                     font=(FONT_FAMILY, 20, "bold")).pack(anchor="w", padx=20, pady=(15, 8))
        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=(8, 15))
        for column in range(2):
            buttons.grid_columnconfigure(column, weight=1)
        ctk.CTkButton(
            buttons, text="Cadastrar senha do Cofre de Acessos",
            command=self._open_vault_password, **PRIMARY_BUTTON
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)
        ctk.CTkButton(
            buttons, text="Solicitar reset da senha do cofre",
            command=self._request_vault
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=4)
        ctk.CTkButton(
            buttons, text="Solicitar troca da senha no próximo login",
            command=self._request_login_password
        ).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=4)
        if self.user.role == "Administrador":
            ctk.CTkButton(
                buttons, text="Recuperar meu cofre",
                command=self._open_admin_vault_recovery
            ).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=4)
        self.status = ctk.CTkLabel(
            frame, text=f"Estado da solicitação do cofre: {self.security.vault_status(self.user.id)}")
        self.status.pack(anchor="w", padx=20, pady=(0, 15))

    def _open_vault_password(self) -> None:
        VaultPasswordDialog(
            self, self.user, self.security,
            lambda: self._action_completed("Senha do cofre salva."))

    def _open_admin_vault_recovery(self) -> None:
        AdminVaultRecoveryDialog(
            self, self.user, self.auth, self.security,
            lambda: self._action_completed("Senha do cofre administrativo redefinida."))

    def _request_vault(self) -> None:
        self.security.request_vault_recovery(self.user.id)
        self._action_completed("Solicitação de reset do cofre enviada ao administrador.")

    def _request_login_password(self) -> None:
        self.auth.request_password_recovery(self.user.username)
        self._action_completed("Solicitação de troca da senha de login enviada ao administrador.")

    def _action_completed(self, message: str) -> None:
        self.message.configure(text=message, text_color=LEAF_YELLOW)
        self.refresh()

    def _admin_section(self) -> None:
        users = ctk.CTkFrame(self.content)
        users.pack(fill="x", padx=5, pady=8)
        ctk.CTkLabel(users, text="Usuários do sistema",
                     font=(FONT_FAMILY, 20, "bold")).pack(anchor="w", padx=20, pady=12)
        for item in self.auth.list_users(self.user):
            row = ctk.CTkFrame(users, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            state = "Ativo" if item.active else "Desativado"
            ctk.CTkLabel(row, text=f"{item.name} • {item.username} • {item.role} • {state}",
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="Alterar", width=75,
                command=lambda selected=item: UserEditDialog(
                    self, self.user, selected, self.auth, self.refresh)
            ).pack(side="right", padx=3)
            ctk.CTkButton(
                row, text="Ativar" if not item.active else "Desativar", width=85,
                fg_color=LEAF_GREEN if not item.active else DANGER,
                text_color=DARK_GREEN if not item.active else DANGER_TEXT,
                border_color=LEAF_YELLOW if not item.active else DANGER_BORDER,
                command=lambda selected=item: self._toggle_user(selected)
            ).pack(side="right", padx=3)

        requests = ctk.CTkFrame(self.content)
        requests.pack(fill="x", padx=5, pady=8)
        request_header = ctk.CTkFrame(requests, fg_color="transparent")
        request_header.pack(fill="x", padx=20, pady=12)
        ctk.CTkLabel(
            request_header, text="Solicitações aguardando aprovação",
            font=(FONT_FAMILY, 20, "bold")
        ).pack(side="left")
        ctk.CTkButton(
            request_header, text="↻ Atualizar solicitações", width=150,
            command=self.refresh
        ).pack(side="right")
        pending = self.security.pending_requests()
        self._pending_signature = tuple(
            sorted((request["id"], request["origem"], request["status"])
                   for request in pending))
        if not pending:
            ctk.CTkLabel(requests, text="Nenhuma solicitação pendente.").pack(pady=12)
        for request in pending:
            row = ctk.CTkFrame(requests, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(
                row, text=f"{request['nome']} • recuperação de {request['origem']}", anchor="w"
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="✓ Aprovar", width=90, **PRIMARY_BUTTON,
                command=lambda data=request: self._approve(data)
            ).pack(side="right")

    def _poll_requests(self) -> None:
        """Atualiza a tela se uma solicitação externa chegar enquanto ela está aberta."""
        if not self.winfo_exists():
            return
        if self.user.role == "Administrador":
            pending = self.security.pending_requests()
            signature = tuple(
                sorted((request["id"], request["origem"], request["status"])
                       for request in pending))
            if signature != self._pending_signature:
                self.refresh()
        self.after(1500, self._poll_requests)

    def _approve(self, request: dict) -> None:
        self.security.approve(request["id"], request["origem"])
        self.message.configure(text="Recuperação aprovada.", text_color=LEAF_YELLOW)
        self.refresh()

    def _toggle_user(self, selected: User) -> None:
        try:
            self.auth.admin_set_active(self.user, selected.id, not selected.active)
            self.message.configure(
                text="Situação do usuário atualizada.",
                text_color=LEAF_YELLOW)
            self.refresh()
        except ValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")


class VaultPasswordDialog(ctk.CTkToplevel):
    """Solicita a nova senha do cofre somente em uma janela dedicada."""

    def __init__(self, master, user: User, security: SecurityService,
                 on_saved: Callable[[], None]) -> None:
        super().__init__(master)
        configure_modal_window(self, master)
        self.user, self.security, self.on_saved = user, security, on_saved
        self.title("Cadastrar senha do Cofre de Acessos")
        self.geometry("440x300")
        self.resizable(False, False)
        ctk.CTkLabel(
            self, text="Senha do Cofre de Acessos",
            font=(FONT_FAMILY, 22, "bold")
        ).pack(pady=(25, 15))
        self.password = ctk.CTkEntry(self, placeholder_text="Nova senha", show="*")
        self.password.pack(fill="x", padx=45, pady=6)
        self.confirmation = ctk.CTkEntry(
            self, placeholder_text="Confirmar nova senha", show="*")
        self.confirmation.pack(fill="x", padx=45, pady=6)
        self.confirmation.bind("<Return>", lambda _event: self._save())
        self.message = ctk.CTkLabel(self, text="", wraplength=350)
        self.message.pack(pady=5)
        ctk.CTkButton(
            self, text="Salvar senha", command=self._save, **PRIMARY_BUTTON
        ).pack(padx=45, pady=8, fill="x")
        self.password.focus_set()

    def _save(self) -> None:
        try:
            self.security.set_vault_password(
                self.user.id, self.password.get(), self.confirmation.get())
            self.destroy()
            self.on_saved()
        except SecurityValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")


class AdminVaultRecoveryDialog(ctk.CTkToplevel):
    """Recupera o cofre do administrador após confirmar sua identidade."""

    def __init__(self, master, user: User, auth: AuthService,
                 security: SecurityService, on_saved: Callable[[], None]) -> None:
        super().__init__(master)
        configure_modal_window(self, master)
        self.user, self.auth, self.security = user, auth, security
        self.on_saved = on_saved
        self.title("Recuperar meu cofre")
        self.geometry("460x370")
        self.resizable(False, False)
        ctk.CTkLabel(
            self, text="Recuperar Cofre de Acessos",
            font=(FONT_FAMILY, 22, "bold")
        ).pack(pady=(24, 8))
        ctk.CTkLabel(
            self,
            text="Confirme a senha da sua conta administrativa e defina uma nova senha.",
            wraplength=370, text_color=TEXT_LIGHT
        ).pack(padx=40, pady=(0, 10))
        self.account_password = self._entry("Senha da conta administrativa")
        self.new_password = self._entry("Nova senha do cofre")
        self.confirmation = self._entry("Confirmar nova senha do cofre")
        self.confirmation.bind("<Return>", lambda _event: self._save())
        self.message = ctk.CTkLabel(self, text="", wraplength=370)
        self.message.pack(pady=5)
        ctk.CTkButton(
            self, text="Redefinir senha do cofre", command=self._save,
            **PRIMARY_BUTTON
        ).pack(fill="x", padx=45, pady=8)
        self.account_password.focus_set()

    def _entry(self, placeholder: str):
        entry = ctk.CTkEntry(self, placeholder_text=placeholder, show="*")
        entry.pack(fill="x", padx=45, pady=5)
        return entry

    def _save(self) -> None:
        new_password = self.new_password.get()
        confirmation = self.confirmation.get()
        if not new_password:
            self.message.configure(
                text="Informe a nova senha do cofre.", text_color="#ff6b6b")
            return
        if new_password != confirmation:
            self.message.configure(text="As senhas não coincidem.", text_color="#ff6b6b")
            return
        try:
            authenticated = self.auth.authenticate(
                self.user.username, self.account_password.get())
            if authenticated.id != self.user.id or authenticated.role != "Administrador":
                raise AuthenticationError("Conta administrativa inválida.")
            # A própria autenticação substitui a aprovação de um segundo administrador.
            self.security.request_vault_recovery(self.user.id)
            self.security.approve(self.user.id, "cofre")
            self.security.set_vault_password(
                self.user.id, new_password, confirmation)
            self.destroy()
            self.on_saved()
        except (AuthenticationError, SecurityValidationError):
            self.message.configure(
                text="Senha da conta administrativa inválida.",
                text_color="#ff6b6b")


class UserEditDialog(ctk.CTkToplevel):
    def __init__(self, master, admin: User, selected: User, auth: AuthService,
                 on_saved: Callable[[], None]) -> None:
        super().__init__(master)
        configure_modal_window(self, master)
        self.admin, self.selected, self.auth = admin, selected, auth
        self.on_saved = on_saved
        self.title("Alterar usuário")
        self.geometry("430x430")
        ctk.CTkLabel(self, text="Alterar usuário", font=(FONT_FAMILY, 22, "bold")).pack(pady=22)
        self.name = ctk.CTkEntry(self, placeholder_text="Nome")
        self.name.pack(fill="x", padx=45, pady=6); self.name.insert(0, selected.name)
        self.username = ctk.CTkEntry(self, placeholder_text="Login")
        self.username.pack(fill="x", padx=45, pady=6); self.username.insert(0, selected.username)
        self.password = ctk.CTkEntry(
            self, placeholder_text="Nova senha (deixe vazio para manter)", show="*")
        self.password.pack(fill="x", padx=45, pady=6)
        ctk.CTkLabel(self, text="Perfil de acesso", anchor="w").pack(
            fill="x", padx=45, pady=(8, 2))
        self.role = ctk.CTkOptionMenu(
            self, values=["Usuário", "Administrador"])
        self.role.pack(fill="x", padx=45, pady=(0, 6))
        self.role.set(selected.role)
        self.message = ctk.CTkLabel(self, text="")
        self.message.pack(pady=5)
        ctk.CTkButton(
            self, text="Salvar alterações", command=self._save, **PRIMARY_BUTTON).pack(pady=8)

    def _save(self) -> None:
        try:
            self.auth.admin_update_user(
                self.admin, self.selected.id, self.name.get(),
                self.username.get(), self.password.get(), self.role.get())
            self.destroy()
            self.on_saved()
        except ValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")


class VaultAccessDialog(ctk.CTkToplevel):
    def __init__(self, master, user: User, security: SecurityService, on_success) -> None:
        super().__init__(master)
        apply_app_icon(self)
        self.user, self.security, self.on_success = user, security, on_success
        self.title("Desbloquear Cofre")
        self.geometry("400x250")
        self.transient(master.winfo_toplevel())
        self.grab_set()
        ctk.CTkLabel(self, text="Senha do Cofre", font=(FONT_FAMILY, 22, "bold")).pack(pady=(30, 15))
        self.password = ctk.CTkEntry(self, placeholder_text="Senha", show="*")
        self.password.pack(fill="x", padx=45, pady=8)
        self.password.bind("<Return>", lambda _event: self._submit())
        self.message = ctk.CTkLabel(self, text="")
        self.message.pack()
        ctk.CTkButton(
            self, text="Desbloquear", command=self._submit, **PRIMARY_BUTTON).pack(pady=8)

    def _submit(self) -> None:
        if self.security.unlock_vault(self.user.id, self.password.get()):
            self.destroy()
            self.on_success()
        else:
            self.message.configure(
                text="Senha inválida. Cadastre ou recupere-a em Configurações.",
                text_color="#ff6b6b")


class ProfileDialog(ctk.CTkToplevel):
    """Permite ao usuário alterar seus próprios dados sem acesso administrativo."""

    def __init__(self, master, user: User, auth: AuthService, on_updated) -> None:
        super().__init__(master)
        apply_app_icon(self)
        self.user, self.auth, self.on_updated = user, auth, on_updated
        self.title("Meu perfil"); self.geometry("470x440")
        self.transient(master.winfo_toplevel()); self.grab_set()
        ctk.CTkLabel(self, text="Meu perfil", font=(FONT_FAMILY, 24, "bold")).pack(pady=(22, 5))
        self.summary = ctk.CTkLabel(
            self, text=f"{user.name}\n{user.job or 'Função não informada'}",
            text_color="#94a3b8")
        self.summary.pack(pady=(0, 18))
        choices = ctk.CTkFrame(self, fg_color="transparent")
        choices.pack(fill="x", padx=35)
        for text, mode in (("Alterar nome completo", "name"),
                           ("Alterar função", "job"),
                           ("Alterar senha", "password")):
            ctk.CTkButton(
                choices, text=text, height=38,
                command=lambda selected=mode: self._show_form(selected)
            ).pack(fill="x", pady=4)
        self.editor = ctk.CTkFrame(self, fg_color="transparent")
        self.editor.pack(fill="both", expand=True, padx=35, pady=12)
        self.message = ctk.CTkLabel(self, text="")
        self.message.pack(pady=(0, 10))

    def _show_form(self, mode: str) -> None:
        for widget in self.editor.winfo_children():
            widget.destroy()
        self.mode = mode
        self.fields = []
        definitions = {
            "name": [("Digite o novo nome completo", False)],
            "job": [("Digite a função exercida na empresa", False)],
            "password": [("Digite a nova senha", True),
                         ("Digite novamente a nova senha", True)],
        }
        for placeholder, secret in definitions[mode]:
            entry = ctk.CTkEntry(
                self.editor, placeholder_text=placeholder,
                show="*" if secret else "", height=40)
            entry.pack(fill="x", pady=5)
            self.fields.append(entry)
        self.fields[0].focus_set()
        self.fields[-1].bind("<Return>", lambda _event: self._save())
        ctk.CTkButton(self.editor, text="Salvar alteração", command=self._save,
                      **PRIMARY_BUTTON).pack(fill="x", pady=(10, 0))

    def _save(self) -> None:
        if not hasattr(self, "mode"):
            return
        name, job, password, confirmation = self.user.name, self.user.job, "", ""
        if self.mode == "name":
            name = self.fields[0].get()
        elif self.mode == "job":
            job = self.fields[0].get()
        else:
            password, confirmation = self.fields[0].get(), self.fields[1].get()
        try:
            updated = self.auth.update_own_profile(
                self.user, name, job, password, confirmation)
            self.user = updated
            self.on_updated(updated)
            self.message.configure(text="Perfil atualizado.", text_color=LEAF_YELLOW)
            self.summary.configure(
                text=f"{updated.name}\n{updated.job or 'Função não informada'}")
            for widget in self.editor.winfo_children():
                widget.destroy()
        except ValidationError as error:
            self.message.configure(text=str(error), text_color="#ff6b6b")
