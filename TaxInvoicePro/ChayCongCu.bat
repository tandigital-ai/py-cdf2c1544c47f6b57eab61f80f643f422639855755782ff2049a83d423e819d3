@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate
python cong_cu.py
echo.
echo (Cua so se dong khi ban bam phim bat ky)
pause >nul
