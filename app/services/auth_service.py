import sqlite3
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.passwords import hash_password, is_password_hash, verify_password


class AuthenticationError(ValueError): pass
class ValidationError(ValueError): pass


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def needs_initial_admin(self) -> bool:
        return self.repository.count() == 0

    def create_initial_admin(self, name: str, username: str, password: str, confirmation: str) -> User:
        name, username = name.strip(), username.strip()
        if not self.needs_initial_admin(): raise ValidationError("O administrador inicial já foi cadastrado.")
        if len(name) < 3: raise ValidationError("Informe um nome com pelo menos 3 caracteres.")
        if len(username) < 3: raise ValidationError("O usuário deve ter pelo menos 3 caracteres.")
        if not password: raise ValidationError("Informe uma senha.")
        if password != confirmation: raise ValidationError("As senhas não coincidem.")
        try:
            return self.repository.create_admin(name, username, hash_password(password))
        except sqlite3.IntegrityError as error:
            raise ValidationError("Esse nome de usuário já está em uso.") from error

    def authenticate(self, username: str, password: str) -> User:
        # Mesmo contas antigas com a coluna de senha vazia nunca podem autenticar
        # apenas pelo login. A validação ocorre antes da consulta das credenciais.
        if not password:
            raise AuthenticationError("Usuário ou senha inválidos.")
        credentials = self.repository.find_credentials(username.strip())
        if credentials is None or not credentials.user.active:
            raise AuthenticationError("Usuário ou senha inválidos.")
        stored = credentials.password_hash
        valid = verify_password(password, stored) if is_password_hash(stored) else hmac_compare(password, stored)
        if not valid: raise AuthenticationError("Usuário ou senha inválidos.")
        if not is_password_hash(stored):
            self.repository.update_password(credentials.user.id, hash_password(password))
        return credentials.user

    def register_user(self, name: str, username: str, password: str,
                      confirmation: str) -> User:
        name, username = name.strip(), username.strip()
        self._validate_registration(name, username, password, confirmation)
        try:
            return self.repository.create(name, username, hash_password(password))
        except sqlite3.IntegrityError as error:
            raise ValidationError("Esse nome de usuário já está em uso.") from error

    def request_password_recovery(self, username: str) -> None:
        if not username.strip():
            raise ValidationError("Informe o nome de usuário.")
        # A resposta não revela se a conta existe, evitando enumeração de usuários.
        self.repository.request_login_recovery(username.strip())

    def complete_password_recovery(self, username: str, password: str,
                                   confirmation: str) -> None:
        if not password:
            raise ValidationError("Informe a nova senha.")
        if password != confirmation:
            raise ValidationError("As senhas não coincidem.")
        if not self.repository.reset_password_if_approved(
                username.strip(), hash_password(password)):
            raise ValidationError("A recuperação ainda está aguardando aprovação.")

    def list_users(self, requester: User) -> list[User]:
        if requester.role != "Administrador":
            raise ValidationError("Apenas administradores podem consultar usuários.")
        return self.repository.list_all()

    def admin_update_user(self, requester: User, user_id: int, name: str,
                          username: str, new_password: str = "",
                          role: str | None = None) -> None:
        if requester.role != "Administrador":
            raise ValidationError("Apenas administradores podem alterar usuários.")
        name, username = name.strip(), username.strip()
        if len(name) < 3 or len(username) < 3:
            raise ValidationError("Nome e usuário devem ter pelo menos 3 caracteres.")
        if role is not None and role not in {"Administrador", "Usuário"}:
            raise ValidationError("Perfil de usuário inválido.")
        if requester.id == user_id and role not in {None, "Administrador"}:
            raise ValidationError("O administrador não pode remover o próprio perfil administrativo.")
        try:
            self.repository.update_user(
                user_id, name, username,
                hash_password(new_password) if new_password else None, role)
        except sqlite3.IntegrityError as error:
            raise ValidationError("Esse nome de usuário já está em uso.") from error

    def admin_set_active(self, requester: User, user_id: int, active: bool) -> None:
        if requester.role != "Administrador":
            raise ValidationError("Apenas administradores podem alterar usuários.")
        if requester.id == user_id and not active:
            raise ValidationError("O administrador não pode desativar a própria conta.")
        self.repository.set_active(user_id, active)

    @staticmethod
    def _validate_registration(name: str, username: str, password: str,
                               confirmation: str) -> None:
        if len(name) < 3:
            raise ValidationError("Informe um nome com pelo menos 3 caracteres.")
        if len(username) < 3:
            raise ValidationError("O usuário deve ter pelo menos 3 caracteres.")
        if not password:
            raise ValidationError("Informe uma senha.")
        if password != confirmation:
            raise ValidationError("As senhas não coincidem.")

    def update_own_profile(self, user: User, name: str, job: str,
                           new_password: str, confirmation: str) -> User:
        name, job = name.strip(), job.strip()
        if len(name) < 3:
            raise ValidationError("Informe um nome com pelo menos 3 caracteres.")
        if new_password != confirmation:
            raise ValidationError("As senhas não coincidem.")
        self.repository.update_profile(
            user.id, name, job, hash_password(new_password) if new_password else None)
        return User(user.id, name, user.username, user.role, user.active, job)


def hmac_compare(value: str, expected: str) -> bool:
    """Compatibilidade segura com senhas antigas em texto puro."""
    import hmac
    return hmac.compare_digest(value, expected)
