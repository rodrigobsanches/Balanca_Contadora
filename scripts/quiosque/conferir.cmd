@echo off
rem Roda o .ps1 de mesmo nome como administrador (pede permissao se precisar).
net session >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dpn0.ps1"
pause
