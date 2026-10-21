@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m tracker --report >> report.log 2>&1
