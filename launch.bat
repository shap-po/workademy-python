@echo off

PUSHD "%~dp0"

call venv\Scripts\activate
python server.py
