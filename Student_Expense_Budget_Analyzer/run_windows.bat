@echo off
title Student Expense Analyzer
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Package installation failed. Check your internet connection and Python installation.
  pause
  exit /b 1
)
python app.py
if errorlevel 1 pause
