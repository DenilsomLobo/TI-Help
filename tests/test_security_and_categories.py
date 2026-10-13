import tempfile
import unittest
from pathlib import Path

from app.database.connection import Database
from app.database.migrations import run_migrations
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.security_repository import SecurityRepository
from app.repositories.user_repository import UserRepository
from app.services.knowledge_service import KnowledgeService
from app.services.security_service import SecurityService


class SecurityAndCategoriesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        database = Database(Path(self.temp.name) / "test.db")
        run_migrations(database)
        self.user_repository = UserRepository(database)
        self.user = self.user_repository.create_admin("Admin", "admin", "hash")
        self.knowledge = KnowledgeService(KnowledgeRepository(database))
        self.security = SecurityService(SecurityRepository(database))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_article_can_have_multiple_categories_and_marks(self) -> None:
        article = self.knowledge.create(
            "Acesso ao sistema", "Sistema não permite entrar", "Liberar perfil do usuário",
            ["Acessos", "Sistemas"], self.user.id, "Validar com o gestor")
        self.assertEqual(("Acessos", "Sistemas"), article.categories)
        self.assertEqual("Validar com o gestor", article.observation)
        self.assertTrue(self.knowledge.toggle_mark(article.id, self.user.id, "favorito"))
        self.assertEqual([article], self.knowledge.search_marked(self.user.id, "favorito"))
        self.assertFalse(self.knowledge.toggle_mark(article.id, self.user.id, "favorito"))

    def test_vault_uses_a_password_hash(self) -> None:
        self.security.set_vault_password(self.user.id, "segredo", "segredo")
        self.assertTrue(self.security.unlock_vault(self.user.id, "segredo"))
        self.assertFalse(self.security.unlock_vault(self.user.id, "incorreta"))

    def test_vault_recovery_flow(self) -> None:
        self.security.request_vault_recovery(self.user.id)
        self.assertEqual("aguardando", self.security.vault_status(self.user.id))
        self.security.approve(self.user.id, "cofre")
        self.assertEqual("aprovado", self.security.vault_status(self.user.id))
        self.security.set_vault_password(self.user.id, "nova-senha", "nova-senha")
        self.assertTrue(self.security.unlock_vault(self.user.id, "nova-senha"))
        self.assertEqual("nenhuma", self.security.vault_status(self.user.id))

    def test_login_and_vault_requests_reach_the_admin_list(self) -> None:
        self.user_repository.request_login_recovery(self.user.username)
        self.security.request_vault_recovery(self.user.id)

        origins = {request["origem"] for request in self.security.pending_requests()}
        self.assertEqual({"login", "cofre"}, origins)

    def test_records_recent_article(self) -> None:
        article = self.knowledge.create(
            "Problema recente", "Descrição do problema", "Descrição da solução",
            ["Geral"], self.user.id)
        self.knowledge.record_recent(article.id, self.user.id)
        self.assertEqual([article], self.knowledge.recent(self.user.id))


if __name__ == "__main__":
    unittest.main()
