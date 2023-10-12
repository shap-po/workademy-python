@echo off

PUSHD "%~dp0"

@REM rename venv to .venv
IF EXIST venv (
    RENAME venv .venv
)

call .venv\Scripts\activate
python server.py
