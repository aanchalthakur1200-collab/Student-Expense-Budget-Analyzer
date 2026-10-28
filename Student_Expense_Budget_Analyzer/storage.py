import csv
import json
import math
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
EXPENSES_FILE = DATA_DIR / "expenses.csv"
SETTINGS_FILE = DATA_DIR / "settings.json"
DEFAULT_BUDGET = 10000.0
CATEGORIES = [
    "Food",
    "Transport",
    "Education",
    "Shopping",
    "Bills",
    "Health",
    "Entertainment",
    "Other",
]
PAYMENT_METHODS = ["Cash", "Debit card", "Credit card", "UPI", "Bank transfer", "Other"]
EXPENSE_FIELDS = ["id", "date", "title", "category", "amount", "payment_method", "notes"]


def ensure_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not EXPENSES_FILE.exists():
        with EXPENSES_FILE.open("w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=EXPENSE_FIELDS).writeheader()


def load_expenses():
    ensure_data_files()
    with EXPENSES_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            return []
        legacy_schema = "title" not in reader.fieldnames
        expenses = []
        used_ids = set()
        for index, row in enumerate(reader, start=1):
            try:
                expense_id = int(row.get("id") or index)
            except (TypeError, ValueError):
                expense_id = index
            while expense_id in used_ids:
                expense_id += 1
            used_ids.add(expense_id)
            try:
                amount = float(row.get("amount") or 0)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid amount in expense row {index + 1}.") from error
            if not math.isfinite(amount):
                raise ValueError(f"Invalid amount in expense row {index + 1}.")
            expenses.append(
                {
                    "id": expense_id,
                    "date": (row.get("date") or "").strip(),
                    "title": (row.get("title") or row.get("description") or "").strip(),
                    "category": (row.get("category") or "Other").strip(),
                    "amount": amount,
                    "payment_method": (row.get("payment_method") or "Cash").strip(),
                    "notes": (row.get("notes") or "").strip(),
                }
            )
    if legacy_schema:
        save_expenses(expenses)
    return expenses


def save_expenses(expenses):
    ensure_data_files()
    temporary_file = EXPENSES_FILE.with_suffix(".csv.tmp")
    with temporary_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=EXPENSE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(expenses)
    os.replace(temporary_file, EXPENSES_FILE)


def load_budget():
    ensure_data_files()
    if not SETTINGS_FILE.exists():
        return DEFAULT_BUDGET
    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        settings = json.load(file)
    return float(settings.get("monthly_budget", DEFAULT_BUDGET))


def save_budget(budget):
    ensure_data_files()
    temporary_file = SETTINGS_FILE.with_suffix(".json.tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump({"monthly_budget": budget}, file, indent=2)
    os.replace(temporary_file, SETTINGS_FILE)
