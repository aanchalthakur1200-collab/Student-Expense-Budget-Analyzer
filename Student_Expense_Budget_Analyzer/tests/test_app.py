import csv
import tempfile
import unittest
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import app as expense_app
import desktop
import storage


class StudentExpenseAppTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        data_dir = Path(self.temporary_directory.name)
        self.patches = ExitStack()
        self.patches.enter_context(patch.object(storage, "DATA_DIR", data_dir))
        self.patches.enter_context(patch.object(storage, "EXPENSES_FILE", data_dir / "expenses.csv"))
        self.patches.enter_context(patch.object(storage, "SETTINGS_FILE", data_dir / "settings.json"))
        expense_app.app.config.update(TESTING=True)
        self.client = expense_app.app.test_client()

    def tearDown(self):
        self.patches.close()
        self.temporary_directory.cleanup()

    def add_expense(self, **overrides):
        values = {
            "title": "Campus lunch",
            "amount": "125.50",
            "category": "Food",
            "date": "2026-10-12",
            "payment_method": "UPI",
            "notes": "With classmates",
        }
        values.update(overrides)
        return self.client.post("/expenses/add", data=values, follow_redirects=False)

    def test_dashboard_and_empty_states_render(self):
        dashboard = self.client.get("/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(b"No expenses just yet", dashboard.data)
        self.assertEqual(self.client.get("/reports").status_code, 200)
        self.assertEqual(self.client.get("/expenses").status_code, 200)

    def test_desktop_launcher_serves_dashboard_on_local_ephemeral_port(self):
        server, thread, app_url = desktop.start_local_server()
        try:
            self.assertTrue(thread.is_alive())
            self.assertTrue(app_url.startswith("http://127.0.0.1:"))
            with urllib.request.urlopen(app_url, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"Your money", response.read())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_expense_crud_filtering_and_export(self):
        response = self.add_expense()
        self.assertEqual(response.status_code, 302)
        expense = storage.load_expenses()[0]
        self.assertEqual(expense["title"], "Campus lunch")
        self.assertEqual(expense["amount"], 125.5)

        updated = self.client.post(
            f"/expenses/{expense['id']}/edit",
            data={
                "title": "Updated lunch",
                "amount": "150",
                "category": "Food",
                "date": "2026-10-12",
                "payment_method": "Cash",
                "notes": "",
            },
        )
        self.assertEqual(updated.status_code, 302)
        filtered = self.client.get("/expenses?q=updated&category=Food")
        self.assertIn(b"Updated lunch", filtered.data)
        self.assertNotIn(b"Campus lunch", filtered.data)

        exported = self.client.get("/expenses/export")
        self.assertEqual(exported.status_code, 200)
        self.assertIn(b"payment_method", exported.data)
        deleted = self.client.post(f"/expenses/{expense['id']}/delete")
        self.assertEqual(deleted.status_code, 302)
        self.assertEqual(storage.load_expenses(), [])

    def test_validation_rejects_empty_title_and_invalid_amount(self):
        response = self.add_expense(title="", amount="-1")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Add a title", response.data)
        self.assertEqual(storage.load_expenses(), [])

    def test_budget_is_persisted_and_invalid_budget_rejected(self):
        response = self.client.post("/budget", data={"monthly_budget": "25000"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(storage.load_budget(), 25000)
        invalid = self.client.post("/budget", data={"monthly_budget": "-2"})
        self.assertEqual(invalid.status_code, 302)
        self.assertEqual(storage.load_budget(), 25000)

    def test_legacy_csv_is_migrated_without_losing_description(self):
        storage.DATA_DIR.mkdir(exist_ok=True)
        with storage.EXPENSES_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["id", "date", "category", "description", "amount"])
            writer.writeheader()
            writer.writerow(
                {"id": 7, "date": "2026-10-01", "category": "Education", "description": "Book", "amount": 300}
            )

        expenses = storage.load_expenses()
        self.assertEqual(expenses[0]["title"], "Book")
        self.assertEqual(expenses[0]["payment_method"], "Cash")
        with storage.EXPENSES_FILE.open("r", newline="", encoding="utf-8") as file:
            self.assertEqual(next(csv.reader(file)), storage.EXPENSE_FIELDS)


if __name__ == "__main__":
    unittest.main()
