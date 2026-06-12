@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "G:\claude code\.claude\LangChain"
uv run langgraph dev --no-browser