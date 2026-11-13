@echo off
rem Abre o app da balanca sem janela preta (o log fica em app\logs\app.log).
start "" "%~dp0..\python\pythonw.exe" -s "%~dp0..\app\main.py"
