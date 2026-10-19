@echo off
title Storybook Studio - Creative Sanctuary
color 0A

echo =====================================================================
echo                 Storybook Studio - Creative Sanctuary
echo =====================================================================
echo.
echo [1/3] Checking Python Virtual Environment...

if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    echo [*] Installing dependencies from requirements.txt...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\pip.exe install -r requirements.txt
) else (
    echo [OK] Virtual environment detected.
)

echo.
echo [2/3] Checking Environment Configuration (.env)...
if not exist ".env" (
    echo [*] Creating initial .env from .env.example...
    copy .env.example .env >nul
)
echo [OK] Configuration file ready.

echo.
echo =====================================================================
echo                        AI API KEY SETUP LINKS
echo =====================================================================
echo  Gemini API Key:  https://aistudio.google.com/apikey
echo  Groq API Key:    https://console.groq.com/keys
echo.
echo  Paste your keys directly in your local .env file or configure them
echo  inside the application under the Settings tab!
echo  (The application also works 100%% offline using Mock Provider)
echo =====================================================================
echo.
echo [3/3] Launching Storybook Studio...
echo Opening browser at http://localhost:8501 ...
echo.

.\.venv\Scripts\python.exe -m streamlit run app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
