import csv
import io
import os
from datetime import date

import numpy as np
import pandas as pd
from flask import Flask, abort, flash, make_response, redirect, render_template, request, url_for

from storage import (
    CATEGORIES,
    EXPENSE_FIELDS,
    PAYMENT_METHODS,
    load_budget,
    load_expenses,
    save_budget,
    save_expenses,
)

app = Flask(__name__)
app.secret_key = os.environ.get("STUDENT_EXPENSE_SECRET_KEY", "student-expense-local-development-key")
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.template_filter("currency")
def currency(value):
    return f"₹{float(value):,.2f}"


def month_total(expenses, month):
    return sum(float(item["amount"]) for item in expenses if item["date"].startswith(month))


def expense_form_values(form):
    title = form.get("title", "").strip()
    category = form.get("category", "").strip()
    expense_date = form.get("date", "").strip()
    payment_method = form.get("payment_method", "").strip()
    notes = form.get("notes", "").strip()
    try:
        amount = float(form.get("amount", ""))
    except ValueError:
        amount = 0

    if not title:
        return None, "Add a title for this expense."
    if len(title) > 100:
        return None, "Expense titles must be 100 characters or fewer."
    if not np.isfinite(amount) or amount <= 0:
        return None, "Enter an amount greater than zero."
    if category not in CATEGORIES:
        return None, "Choose a category from the list."
    if payment_method not in PAYMENT_METHODS:
        return None, "Choose a payment method from the list."
    try:
        date.fromisoformat(expense_date)
    except ValueError:
        return None, "Choose a valid expense date."
    if len(notes) > 500:
        return None, "Notes must be 500 characters or fewer."

    return {
        "date": expense_date,
        "title": title,
        "category": category,
        "amount": amount,
        "payment_method": payment_method,
        "notes": notes,
    }, None


def get_expense(expense_id):
    for expense in load_expenses():
        if expense["id"] == expense_id:
            return expense
    abort(404)


@app.context_processor
def inject_navigation_data():
    return {
        "categories": CATEGORIES,
        "payment_methods": PAYMENT_METHODS,
        "today": date.today().isoformat(),
    }


@app.get("/")
def dashboard():
    expenses = load_expenses()
    budget = load_budget()
    current_month = date.today().strftime("%Y-%m")
    current_expenses = [item for item in expenses if item["date"].startswith(current_month)]
    spent = month_total(expenses, current_month)
    remaining = budget - spent
    used_percent = spent / budget * 100 if budget else (100 if spent else 0)

    month_labels = pd.date_range(end=pd.Timestamp.today().normalize().replace(day=1), periods=6, freq="MS")
    monthly_totals = [
        month_total(expenses, month.strftime("%Y-%m")) for month in month_labels
    ]
    category_totals = (
        pd.DataFrame(current_expenses).groupby("category")["amount"].sum().sort_values(ascending=False)
        if current_expenses
        else pd.Series(dtype=float)
    )
    return render_template(
        "dashboard.html",
        active="dashboard",
        budget=budget,
        spent=spent,
        remaining=remaining,
        used_percent=used_percent,
        transaction_count=len(current_expenses),
        recent_expenses=sorted(expenses, key=lambda item: item["date"], reverse=True)[:6],
        month_labels=[item.strftime("%b") for item in month_labels],
        monthly_totals=monthly_totals,
        category_labels=category_totals.index.tolist(),
        category_values=category_totals.tolist(),
        has_monthly_data=any(monthly_totals),
        current_month=date.today().strftime("%B %Y"),
    )


@app.route("/expenses", methods=["GET"])
def expenses_page():
    expenses = load_expenses()
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    filtered = []
    for item in expenses:
        searchable = " ".join(
            str(item[key]) for key in ("title", "category", "payment_method", "notes")
        ).lower()
        if query and query not in searchable:
            continue
        if category and item["category"] != category:
            continue
        if date_from and item["date"] < date_from:
            continue
        if date_to and item["date"] > date_to:
            continue
        filtered.append(item)
    filtered.sort(key=lambda item: (item["date"], item["id"]), reverse=True)
    return render_template(
        "expenses.html",
        active="expenses",
        expenses=filtered,
        filters={"q": query, "category": category, "date_from": date_from, "date_to": date_to},
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        expense, error = expense_form_values(request.form)
        if error:
            flash(error, "error")
            return render_template("expense_form.html", active="add", expense=request.form, editing=False), 400
        expenses = load_expenses()
        expense["id"] = max((item["id"] for item in expenses), default=0) + 1
        expenses.append(expense)
        save_expenses(expenses)
        flash("Expense added. Your dashboard is up to date.", "success")
        return redirect(url_for("expenses_page"))
    return render_template("expense_form.html", active="add", expense={}, editing=False)


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    existing = get_expense(expense_id)
    if request.method == "POST":
        expense, error = expense_form_values(request.form)
        if error:
            flash(error, "error")
            return render_template(
                "expense_form.html",
                active="expenses",
                expense={**request.form, "id": expense_id},
                editing=True,
            ), 400
        expenses = load_expenses()
        for item in expenses:
            if item["id"] == expense_id:
                item.update(expense)
                break
        save_expenses(expenses)
        flash("Expense updated.", "success")
        return redirect(url_for("expenses_page"))
    return render_template("expense_form.html", active="expenses", expense=existing, editing=True)


@app.post("/expenses/<int:expense_id>/delete")
def delete_expense(expense_id):
    get_expense(expense_id)
    save_expenses([item for item in load_expenses() if item["id"] != expense_id])
    flash("Expense deleted.", "success")
    return redirect(url_for("expenses_page"))


@app.get("/expenses/export")
def export_expenses():
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=EXPENSE_FIELDS)
    writer.writeheader()
    writer.writerows(load_expenses())
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="student-expenses.csv"'
    return response


@app.route("/budget", methods=["GET", "POST"])
def budget_page():
    if request.method == "POST":
        raw_budget = request.form.get("monthly_budget", "").strip()
        try:
            budget = float(raw_budget)
            if not np.isfinite(budget) or budget < 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid budget of zero or more.", "error")
            return redirect(url_for("budget_page"))
        save_budget(budget)
        flash("Monthly budget saved.", "success")
        return redirect(url_for("budget_page"))

    budget = load_budget()
    spent = month_total(load_expenses(), date.today().strftime("%Y-%m"))
    used_percent = spent / budget * 100 if budget else (100 if spent else 0)
    return render_template(
        "budget.html",
        active="budget",
        budget=budget,
        spent=spent,
        remaining=budget - spent,
        used_percent=used_percent,
    )


@app.get("/reports")
def reports_page():
    expenses = load_expenses()
    current_month = date.today().strftime("%Y-%m")
    current_expenses = [item for item in expenses if item["date"].startswith(current_month)]
    categories = (
        pd.DataFrame(current_expenses).groupby("category")["amount"].sum().sort_values(ascending=False)
        if current_expenses
        else pd.Series(dtype=float)
    )
    months = pd.date_range(end=pd.Timestamp.today().normalize().replace(day=1), periods=6, freq="MS")
    monthly_totals = [month_total(expenses, month.strftime("%Y-%m")) for month in months]
    amounts = np.array([item["amount"] for item in expenses], dtype=float)
    return render_template(
        "reports.html",
        active="reports",
        category_labels=categories.index.tolist(),
        category_values=categories.tolist(),
        month_labels=[item.strftime("%b %Y") for item in months],
        monthly_totals=monthly_totals,
        highest_category=categories.index[0] if not categories.empty else "—",
        average_expense=float(np.mean(amounts)) if amounts.size else 0,
        transaction_count=len(expenses),
        total_spent=float(np.sum(amounts)) if amounts.size else 0,
        current_month=date.today().strftime("%B %Y"),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
