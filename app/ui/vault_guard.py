from collections.abc import Callable

from app.ui.settings_view import VaultAccessDialog


def authorize_article(master, article, service, user, action: Callable[[], None]) -> None:
    """Só executa a ação protegida após confirmar a senha, sem guardar desbloqueio."""
    if "cofre" not in service.marks_for(article.id, user.id):
        action()
        return
    # A aplicação possui o serviço; subir pelos pais também atende janelas filhas.
    owner = master
    while owner is not None and not hasattr(owner, "security_service"):
        owner = owner.master
    if owner is None:
        raise RuntimeError("Serviço de segurança indisponível para acessar o cofre.")
    VaultAccessDialog(master, user, owner.security_service, action)
