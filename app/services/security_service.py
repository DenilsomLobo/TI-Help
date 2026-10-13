from app.repositories.security_repository import SecurityRepository
from app.utils.passwords import hash_password, verify_password


class SecurityValidationError(ValueError):
    pass


class SecurityService:
    def __init__(self, repository: SecurityRepository) -> None:
        self.repository = repository

    def set_vault_password(self, user_id: int, password: str, confirmation: str) -> None:
        if not password:
            raise SecurityValidationError("Informe uma senha para o cofre.")
        if password != confirmation:
            raise SecurityValidationError("As senhas não coincidem.")
        data = self.repository.vault_data(user_id)
        if data and data["senha_hash"] and data["recuperacao_status"] != "aprovado":
            raise SecurityValidationError(
                "Para trocar uma senha já cadastrada, solicite a recuperação e aguarde a aprovação.")
        self.repository.save_vault_password(user_id, hash_password(password))

    def unlock_vault(self, user_id: int, password: str) -> bool:
        data = self.repository.vault_data(user_id)
        return bool(data and data["senha_hash"] and verify_password(password, data["senha_hash"]))

    def vault_status(self, user_id: int) -> str:
        data = self.repository.vault_data(user_id)
        return data["recuperacao_status"] if data else "nenhuma"

    def has_vault_password(self, user_id: int) -> bool:
        data = self.repository.vault_data(user_id)
        return bool(data and data["senha_hash"])

    def request_vault_recovery(self, user_id: int) -> None:
        self.repository.request_vault_recovery(user_id)

    def pending_requests(self) -> list[dict]:
        return self.repository.pending_requests()

    def approve(self, user_id: int, origin: str) -> None:
        self.repository.approve(user_id, origin)
