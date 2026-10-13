import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import customtkinter as ctk

from app.ui.category_widgets import CategorySelector
from app.ui.catalog_views import CatalogView, CatalogDetail, CatalogEditDialog
from app.ui.library_views import CategoriesView
from app.ui.home_view import ArticleEditDialog


class CategoryWidgetTests(unittest.TestCase):
    def setUp(self):
        self.root = ctk.CTk()
        self.root.withdraw()
        self.service = Mock()
        self.service.categories.return_value = ["ERP", "Rede"]
        self.service.list_categories.return_value = ["ERP", "Rede"]
        self.record = SimpleNamespace(id=1, module="relatorio", title="Exemplo",
                                      category="ERP", categories=("ERP",), description="Descrição",
                                      purpose="Finalidade", observation="Nota")

    def tearDown(self):
        # CTk agenda tarefas de ícone/DPI; cancele-as antes de encerrar o Tk do teste.
        for callback in self.root.tk.call("after", "info"):
            self.root.tk.call("after", "cancel", callback)
        self.root.destroy()

    def test_selector_adds_existing_category_without_duplicates_and_removes(self):
        selector = CategorySelector(self.root, ["ERP", "Rede"], ["ERP"])
        selector.menu.set("Rede")
        selector._add()
        selector._add()
        self.assertEqual(selector.get(), ["ERP", "Rede"])
        selector._remove("ERP")
        self.assertEqual(selector.get(), ["Rede"])

    def test_article_edit_sends_selected_categories_and_preserves_hidden_content(self):
        article = SimpleNamespace(id=1, title="Contato", problem="Informação",
                                  category="ERP", categories=("ERP",),
                                  solution="Legado", observation="Nota")
        editor = ArticleEditDialog(self.root, article, self.service, Mock(), "contact")
        editor.categories.menu.set("Rede")
        editor.categories._add()
        editor._save()
        args = self.service.update.call_args.args
        self.assertEqual(args[3:], ("Legado", ["ERP", "Rede"], "Nota"))

    def test_category_navigation_uses_exact_problem_filter(self):
        self.service.search_problems.return_value = []
        view = CategoriesView(self.root, self.service, SimpleNamespace(id=1))
        view._show_category("ERP")
        self.service.search_problems.assert_called_once_with(category="ERP")
        view.refresh()
        view.search.insert(0, "rede")
        view.refresh()

    def test_catalog_screens_render_with_categories(self):
        self.service.search.return_value = [self.record]
        view = CatalogView(self.root, "relatorio", self.service, SimpleNamespace(id=1))
        view._show_page("Resultados")
        view._show_page("Cadastro")
        detail = CatalogDetail(self.root, self.record, self.service)
        editor = CatalogEditDialog(detail, self.record, self.service, Mock())
        self.assertEqual(editor.category.get(), ["ERP"])
        self.root.update_idletasks()

    def test_senior_creation_and_edit_submit_multiple_categories(self):
        self.record.module = "tela_senior"
        self.service.search.return_value = [self.record]
        view = CatalogView(self.root, "tela_senior", self.service, SimpleNamespace(id=1))
        view.title_entry.insert(0, "Tela de pedidos")
        view.category.set_selected(["ERP", "Rede"])
        view.save()
        args = self.service.create.call_args.args
        self.assertEqual(args[0], "tela_senior")
        self.assertEqual(args[-2], ["ERP", "Rede"])
        self.assertEqual(view.category.get(), [])
        view._show_page("Resultados")
        editor = CatalogEditDialog(self.root, self.record, self.service, Mock())
        editor.category.menu.set("Rede")
        editor.category._add()
        editor._save()
        self.assertEqual(self.service.update.call_args.args[-1], ["ERP", "Rede"])

    def test_catalog_layout_has_no_empty_category_gap_and_requested_visible_lines(self):
        self.service.search.return_value = []
        self.root.geometry("1100x850")
        self.root.deiconify()
        for module in CatalogView.TITLES:
            with self.subTest(module=module):
                view = CatalogView(self.root, module, self.service, SimpleNamespace(id=1))
                view.pack(fill="both", expand=True)
                self.root.update_idletasks()
                self.assertLess(view.category.winfo_height(), 70)
                for box, lines in ((view.description, 6), (view.purpose, 20),
                                   (view.observation, 3)):
                    box.insert("1.0", "\n".join("Linha" for _ in range(lines + 5)))
                    self.root.update_idletasks()
                    last = box._textbox.dlineinfo(f"{lines}.0")
                    self.assertIsNotNone(last)
                    self.assertLessEqual(last[1] + last[3], box._textbox.winfo_height())
                    self.assertIsNone(box._textbox.dlineinfo(f"{lines + 1}.0"))
                    self.assertEqual(len(box.get("1.0", "end-1c").splitlines()), lines + 5)
                view.destroy()
