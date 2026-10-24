@echo off
title HavenQuill — AI Story ^& Screenplay Sanctuary
color 0A

echo =====================================================================
echo              HavenQuill — AI Story ^& Screenplay Sanctuary
echo =====================================================================
echo.
echo [1/4] Checking Python Virtual Environment...

if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment .venv...
    python -m venv .venv
    echo [*] Installing dependencies from requirements.txt...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\pip.exe install -r requirements.txt
) else (
    echo [OK] Virtual environment detected.
)

echo.
echo [2/4] Verifying Faster-Whisper Local Installation ^& Model Isolation...
rem Ensure model weights and cache stay strictly inside local project subfolder (no C drive clutter)
set WHISPER_CACHE=%~dp0data\whisper_models
if not exist "%WHISPER_CACHE%" (
    mkdir "%WHISPER_CACHE%" >nul 2>&1
)
set HF_HOME=%WHISPER_CACHE%
set HF_HUB_CACHE=%WHISPER_CACHE%
set TORCH_HOME=%WHISPER_CACHE%

.\.venv\Scripts\python.exe -c "import faster_whisper" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] Faster-Whisper package missing. Installing into project environment...
    .\.venv\Scripts\pip.exe install faster-whisper
) else (
    echo [OK] Faster-Whisper is installed and isolated in %WHISPER_CACHE%.
)

echo.
echo [3/4] Checking Environment Configuration .env...
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
echo [4/4] Launching HavenQuill...
echo Opening browser at http://localhost:8501 ...
echo.

.\.venv\Scripts\python.exe -m streamlit run app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
