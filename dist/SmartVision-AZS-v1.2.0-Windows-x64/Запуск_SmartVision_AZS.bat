@echo off
title SmartVision AZS — Белоруснефть
echo ========================================================
echo  SmartVision AZS — Белоруснефть (Десктоп-клиент)
echo  Запуск локального комплекса телеметрии и компьютерного зрения...
echo ========================================================
python -m pip install -r requirements.txt --quiet >nul 2>&1
python desktop_app.py
pause
