# Student Expense Analyzer

A beginner-friendly local web app for students to record expenses, keep a monthly budget in view, and explore spending patterns.

## Features

- Responsive dashboard with monthly totals, budget progress, recent expenses, and charts
- Add, edit, search, filter, delete, and export expenses
- Expense title, amount, category, date, payment method, and optional notes
- Persistent monthly budget settings
- Pandas and NumPy summaries for category and monthly reports
- CSV storage in `data/expenses.csv`; budget settings in `data/settings.json`
- Automatically migrates the original desktop app's `description` column to `title`
- No sample transactions are preloaded

## Requirements

- Python 3.10 or newer
- Microsoft Edge WebView2 Runtime (normally included with current Windows installations)
- Internet access for the first dependency installation and for CDN-hosted fonts/charts

## Run on Windows

Double-click `run_windows.bat`. It installs the dependencies and opens the analyzer in its own desktop window. Close the window to stop the app.

To start it manually from a terminal in this folder:

```powershell
python -m pip install -r requirements.txt
python desktop.py
```

The app runs its Flask server on a temporary localhost port while the desktop window is open. It does not open a regular browser or listen on your network. To run the web version in a browser instead, use `python app.py` and open <http://127.0.0.1:5000>.

## Project structure

```text
app.py                  Flask routes, input validation, and report calculations
desktop.py              Native Windows window and private local server lifecycle
storage.py              CSV and budget settings persistence/migration
templates/              Dashboard and application pages
static/css/style.css    Responsive styling
static/js/app.js        Navigation, confirmations, and interactive charts
data/                   Local expense CSV and budget settings
```

## Data and privacy

Expense data and budget settings are stored locally in the project’s `data` folder. The desktop app binds its temporary server to `127.0.0.1` and is intended for local use, not public deployment. Chart.js and the web fonts are loaded from CDNs; all transaction data stays local.

The original CSV rows are preserved during the schema migration. Legacy `description` values become expense titles; payment method defaults to `Cash` and notes are blank. If no expenses have been added, charts show a friendly empty state rather than invented sample data.

## Learning concepts

- Flask routes, form handling, redirects, validation, and templates
- Responsive HTML/CSS and JavaScript interactions
- CSV file I/O and organized storage helpers
- Pandas grouping and monthly summaries
- NumPy aggregation and average calculations
- Chart.js line and doughnut charts
"# Student-Expense-Budget-Analyzer" 
