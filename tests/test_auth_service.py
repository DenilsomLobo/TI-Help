import tempfile
import unittest
from pathlib import Path
from app.database.connection import Database
from app.database.migrations import run_migrations
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthenticationError, AuthService, ValidationError
from app.utils.passwords import is_password_hash


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db = Database(Path(self.temp.name) / "test.db"); run_migrations(db)
        self.repo = UserRepository(db); self.service = AuthService(self.repo)

    def tearDown(self): self.temp.cleanup()

    def test_create_and_authenticate(self):
        created = self.service.create_initial_admin("Administrador", "admin", "senha-segura", "senha-segura")
        self.assertEqual(created, self.service.authenticate("admin", "senha-segura"))
        saved = self.repo.find_credentials("admin").password_hash
        self.assertTrue(is_password_hash(saved)); self.assertNotIn("senha-segura", saved)

    def test_rejects_wrong_password(self):
        self.service.create_initial_admin("Administrador", "admin", "senha-segura", "senha-segura")
        with self.assertRaises(AuthenticationError): self.service.authenticate("admin", "errada")

    def test_accepts_password_without_minimum_length(self):
        user = self.service.create_initial_admin("Administrador", "admin", "1", "1")
        self.assertEqual(user, self.service.authenticate("admin", "1"))

    def test_rejects_empty_password(self):
        with self.assertRaises(ValidationError):
            self.service.create_initial_admin("Administrador", "admin", "", "")

    def test_rejects_login_without_password_for_legacy_account(self):
        self.repo.create_admin("Administrador", "admin", "")
        with self.assertRaises(AuthenticationError):
            self.service.authenticate("admin", "")

    def test_admin_reset_requires_the_new_password_at_login(self):
        admin = self.service.create_initial_admin(
            "Administrador", "admin", "senha-admin", "senha-admin")
        user = self.service.register_user(
            "Maria Silva", "maria", "senha-antiga", "senha-antiga")

        self.service.admin_update_user(
            admin, user.id, user.name, user.username, "senha-temporaria")

        with self.assertRaises(AuthenticationError):
            self.service.authenticate("maria", "")
        self.assertEqual(user, self.service.authenticate("maria", "senha-temporaria"))

    def test_admin_can_promote_and_demote_another_user(self):
        admin = self.service.create_initial_admin("Administrador", "admin", "1", "1")
        user = self.service.register_user("Maria Silva", "maria", "2", "2")

        self.service.admin_update_user(
            admin, user.id, user.name, user.username, role="Administrador")
        promoted = next(item for item in self.service.list_users(admin) if item.id == user.id)
        self.assertEqual("Administrador", promoted.role)

        self.service.admin_update_user(
            admin, user.id, user.name, user.username, role="Usuário")
        demoted = next(item for item in self.service.list_users(admin) if item.id == user.id)
        self.assertEqual("Usuário", demoted.role)

    def test_admin_cannot_demote_self(self):
        admin = self.service.create_initial_admin("Administrador", "admin", "1", "1")
        with self.assertRaises(ValidationError):
            self.service.admin_update_user(
                admin, admin.id, admin.name, admin.username, role="Usuário")

    def test_updates_own_profile(self):
        user = self.service.create_initial_admin("Administrador", "admin", "1", "1")
        updated = self.service.update_own_profile(user, "Administrador TI", "Analista", "2", "2")
        self.assertEqual("Analista", updated.job)
        self.assertEqual(updated, self.service.authenticate("admin", "2"))

    def test_migrates_legacy_password(self):
        self.repo.create_admin("Legado", "legado", "1234")
        self.service.authenticate("legado", "1234")
        self.assertTrue(is_password_hash(self.repo.find_credentials("legado").password_hash))

    def test_registers_normal_user(self):
        self.service.create_initial_admin("Administrador", "admin", "senha-segura", "senha-segura")
        user = self.service.register_user("Maria Silva", "maria", "outra-senha", "outra-senha")
        self.assertEqual("Usuário", user.role)
        self.assertEqual(user, self.service.authenticate("maria", "outra-senha"))

    def test_accepts_password_recovery_without_revealing_account(self):
        self.service.request_password_recovery("usuario-inexistente")

    def test_completes_approved_password_recovery(self):
        user = self.service.create_initial_admin(
            "Administrador", "admin", "senha-antiga", "senha-antiga")
        self.service.request_password_recovery("admin")
        from app.repositories.security_repository import SecurityRepository
        # O mesmo banco temporário é acessado pelo repositório utilizado pelo serviço.
        SecurityRepository(self.repo.database).approve(user.id, "login")
        self.service.complete_password_recovery("admin", "senha-nova", "senha-nova")
        self.assertEqual(user, self.service.authenticate("admin", "senha-nova"))
