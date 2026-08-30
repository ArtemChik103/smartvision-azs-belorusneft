#!/usr/bin/env bash
echo "Запуск SmartVision AZS..."
python3 -m pip install -r requirements.txt --quiet >/dev/null 2>&1
python3 desktop_app.py
