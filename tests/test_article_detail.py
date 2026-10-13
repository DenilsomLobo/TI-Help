import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.ui.home_view import ArticleDetailDialog


class ArticleDetailTests(unittest.TestCase):
    def render(self, marks, solution="", observation=""):
        view = SimpleNamespace(
            content=Mock(), _section=Mock(),
            article=SimpleNamespace(problem="Texto de exemplo", solution=solution,
                                    observation=observation))
        view.content.winfo_children.return_value = []
        ArticleDetailDialog._render_sections(view, marks)
        return view._section.call_args_list

    def test_problem_keeps_solution(self):
        self.assertEqual([call.args[0] for call in self.render(set())],
                         ["Problema", "Solução"])

    def test_contact_and_vault_use_their_own_fields(self):
        for marks, label in [({"contato"}, "Informações do contato"),
                             ({"cofre"}, "Informações protegidas do acesso"),
                             ({"contato", "cofre"}, "Informações protegidas do acesso")]:
            with self.subTest(marks=marks):
                self.assertEqual([call.args for call in self.render(marks)],
                                 [(label, "Texto de exemplo")])

    def test_legacy_content_remains_visible(self):
        calls = self.render({"contato"}, "Dado antigo", "Nota antiga")
        self.assertEqual([call.args for call in calls][1:],
                         [("Informações adicionais", "Dado antigo"),
                          ("Observação", "Nota antiga")])
