import tempfile
import unittest
from pathlib import Path

from app.database.connection import Database
from app.database.migrations import run_migrations
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.user_repository import UserRepository
from app.services.knowledge_service import KnowledgeService, KnowledgeValidationError


class KnowledgeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        database = Database(Path(self.temp.name) / "test.db")
        run_migrations(database)
        self.user = UserRepository(database).create_admin(
            "Administrador", "admin", "hash-apenas-para-o-teste"
        )
        self.service = KnowledgeService(KnowledgeRepository(database))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_create_and_search_article(self) -> None:
        created = self.service.create(
            "Impressora offline",
            "A impressora não aparece na rede.",
            "Reiniciar o equipamento e verificar o cabo.",
            "Impressoras",
            self.user.id,
        )

        results = self.service.search("offline")

        self.assertEqual([created], results)

    def test_searches_in_solution_and_category(self) -> None:
        self.service.create(
            "Falha de conexão", "O computador está sem internet.",
            "Renovar o endereço IP.", "Rede", self.user.id
        )

        self.assertEqual(1, len(self.service.search("endereço IP")))
        self.assertEqual(1, len(self.service.search("Rede")))

    def test_update_article(self) -> None:
        article = self.service.create(
            "Título original", "Problema original", "Solução original", "Geral", self.user.id
        )
        self.service.update(
            article.id, "Título atualizado", "Problema atualizado",
            "Solução atualizada", "Sistemas"
        )

        self.assertEqual("Título atualizado", self.service.search("atualizado")[0].title)

    def test_delete_article(self) -> None:
        article = self.service.create(
            "Excluir registro", "Problema temporário", "Solução temporária", "Geral", self.user.id
        )

        self.service.delete(article.id)

        self.assertEqual([], self.service.search())

    def test_rejects_incomplete_article(self) -> None:
        with self.assertRaises(KnowledgeValidationError):
            self.service.create("Oi", "Curto", "Solução válida", "Geral", self.user.id)

    def test_rename_category_preserves_links_and_primary_name(self):
        article = self.service.create("Teste", "Texto", "Solução", ["Rede", "Geral"], self.user.id)
        self.service.rename_category("Rede", "Redes")
        updated = self.service.get(article.id)
        self.assertEqual("Redes", updated.category)
        self.assertIn("Redes", updated.categories)
        self.assertIn("Geral", updated.categories)
        self.assertNotIn("Rede", self.service.list_categories())

    def test_duplicate_rename_preserves_existing_category(self):
        self.service.create_category("Rede")
        self.service.create_category("Outra")
        with self.assertRaises(KnowledgeValidationError):
            self.service.rename_category("Rede", "Outra")
        self.assertIn("Rede", self.service.list_categories())

    def test_delete_category_only_when_unused(self):
        article = self.service.create("Teste", "Texto", "Solução", ["Rede", "Secundária"], self.user.id)
        for category in ("Rede", "Secundária"):
            with self.assertRaises(KnowledgeValidationError):
                self.service.delete_category(category)
        self.assertIsNotNone(self.service.get(article.id))
        self.service.create_category("Livre")
        self.service.delete_category("Livre")
        self.assertNotIn("Livre", self.service.list_categories())

    def test_problems_exclude_contacts_and_vault_but_keep_favorites(self):
        problem = self.service.create("Problema", "Texto", "Solução", "Rede", self.user.id)
        self.service.toggle_mark(problem.id, self.user.id, "favorito")
        for mark in ("contato", "cofre"):
            article = self.service.create("Outro registro", "Texto", "", "Rede", self.user.id)
            self.service.toggle_mark(article.id, self.user.id, mark)
        self.assertEqual([problem], self.service.search_problems("", "Rede"))
        self.assertEqual([], self.service.search_problems("inexistente"))


if __name__ == "__main__":
    unittest.main()
