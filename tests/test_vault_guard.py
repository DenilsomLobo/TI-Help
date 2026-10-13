import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.ui.vault_guard import authorize_article


class VaultGuardTests(unittest.TestCase):
    def setUp(self):
        self.owner = SimpleNamespace(security_service=Mock())
        self.master = SimpleNamespace(master=self.owner)
        self.article = SimpleNamespace(id=1)
        self.user = SimpleNamespace(id=2)
        self.service = Mock()
        self.action = Mock()

    @patch("app.ui.vault_guard.VaultAccessDialog")
    def test_protected_action_waits_for_password_and_asks_again(self, dialog):
        self.service.marks_for.return_value = {"cofre"}
        for _ in range(2):
            authorize_article(self.master, self.article, self.service, self.user, self.action)
        self.action.assert_not_called()
        self.assertEqual(dialog.call_count, 2)
        dialog.call_args.args[-1]()
        self.action.assert_called_once()

    @patch("app.ui.vault_guard.VaultAccessDialog")
    def test_public_article_does_not_require_password(self, dialog):
        self.service.marks_for.return_value = set()
        authorize_article(self.master, self.article, self.service, self.user, self.action)
        self.action.assert_called_once()
        dialog.assert_not_called()

    def test_missing_security_service_blocks_protected_action(self):
        self.service.marks_for.return_value = {"cofre"}
        with self.assertRaises(RuntimeError):
            authorize_article(SimpleNamespace(master=None), self.article,
                              self.service, self.user, self.action)
        self.action.assert_not_called()
