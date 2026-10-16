@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate
python cua_so_bao_cao.py
echo.
echo (Bam phim bat ky de dong)
pause >nul
