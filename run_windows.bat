@echo off
title NEXUS NER Launcher
if not exist .venv (
  echo Creating Python virtual environment...
  py -3.10 -m venv .venv
  if errorlevel 1 (
    echo Could not create environment with Python 3.10.
    echo Install Python 3.10 or 3.11 and create the environment manually.
    pause
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m streamlit run app.py
pause
