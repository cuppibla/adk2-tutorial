@echo off
REM One-shot local setup for the ADK 2 tutorial (Windows).
REM   setup_venv.bat
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Done. Edit .env and paste your GOOGLE_API_KEY.
echo Next:
echo   * Browse all levels in the ADK web UI:    run.sh (or: adk web --port 8080)
echo   * Run one level with its teaching output: python -m L0_first_agent.agent
