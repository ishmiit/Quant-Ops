@echo off
start cmd /k "cd /d C:\Quant Station\backend && .\.venv\Scripts\activate && python main.py"
start cmd /k "cd /d C:\Quant Station\frontend && npm run dev"