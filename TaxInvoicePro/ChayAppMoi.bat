@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate
python khoi_dong.py
echo.
echo (Bam phim bat ky de dong cua so nay)
pause >nul
