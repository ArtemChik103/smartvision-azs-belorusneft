# SmartVision AZS — Белоруснефть

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render%20Online-00843D?style=for-the-badge&logo=render&logoColor=white)](https://smartvision-azs.onrender.com)
[![Desktop Client](https://img.shields.io/badge/GitHub%20Release-v1.2.0%20(Setup%20%26%20ZIP)-00843D?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ArtemChik103/smartvision-azs-belorusneft/releases/latest)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![License](https://img.shields.io/badge/License-MIT-FFCC00?style=for-the-badge)](LICENSE)

> **Комплекс компьютерного зрения и телеметрии для сети АЗС «Белоруснефть» (570 станций).**  
> Автоматизация сценариев заправки **Zero-Click Drive&Pay**, интеллектуальное предотвращение обрыва раздаточных шлангов ТРК ($E\text{-STOP} < 300\text{мс}$) и интерактивная финансово-экономическая модель окупаемости (ТЭО).

* **Рабочая веб-демонстрация:** **[https://smartvision-azs.onrender.com](https://smartvision-azs.onrender.com)**
* **Скачать десктоп-клиент (Setup .EXE / Portable .ZIP):** **[GitHub Releases v1.2.0](https://github.com/ArtemChik103/smartvision-azs-belorusneft/releases/latest)**

---

## Ключевые возможности

### 1. Нативное десктоп-приложение оператора АЗС (Windows x64)
* Автономный нативный клиент на базе Microsoft Edge WebView2 с аппаратным ускорением 60 FPS.
* Полная автономность (Offline) без зависимости от внешнего интернет-соединения.
* Встроенный запуск локального асинхронного FastAPI-сервера и SQLite базы данных в режиме Write-Ahead Logging (WAL).
* Портативный формат развертывания без необходимости сложной инсталляции.

### 2. Zero-Click Drive&Pay (Бесшовный налив)
* Распознавание регистрационных знаков транспортных средств Республики Беларусь (стандартный формат `7777 AB-7`, `1234 IE-7`).
* Автоматическая идентификация пользователя в базе данных «Белоруснефть», проверка баланса и предварительная авторизация ТРК №2.
* Сокращение времени обслуживания на ТРК **с 4.5 минут до 55 секунд** ($-78\%$), ликвидация очередей в часы пик.

### 3. Автоматическая безопасность и защита от обрыва шлангов (E-STOP)
* Непрерывный CV-трекинг смещения автомобиля при установленном пистолете в горловину бака.
* Математический алгоритм фиксации критического риска:
  
  $$\text{NozzleInTank} = \text{True} \quad \land \quad \Delta D \ge 15.0\,\text{px} \quad (\Delta t = 300\,\text{ms})$$

* Мгновенная автоматическая аппаратная блокировка подачи топлива ($< 300\text{мс}$), предотвращающая разрыв шланга, разлив топлива и повреждение ТРК.
* Автоматическая фотофиксация стоп-кадра инцидента с сохранением в журнал безопасности.

### 4. Интерактивная модель ТЭО и ROI-калькулятор
* Динамический расчет эффекта для сети из 570 АЗС, областного филиала (60 АЗС) или пилотного внедрения (1 АЗС).
* Экономический эффект для сети из 570 АЗС:
  * **Чистая годовая выгода:** `+22 006 850 BYN / год`
  * **Срок окупаемости CAPEX:** `< 1 месяца`
  * **5-летний ROI:** `+28 856%`
* Интерактивные графики распределения эффекта и 5-летней динамики денежного потока (Chart.js).

### 5. Корпоративный экспорт (PDF / Excel / CSV / Фискальные чеки)
* **Excel (.XLSX):** Генерация брендированного финансового отчета со стилями «Белоруснефть», 5-летней матрицей cash flow, KPI и подписями.
* **PDF (A4):** Экспорт официального ТЭО в высоком контрасте для руководства и тендерной комиссии.
* **Фискальные чеки:** Печать электронного чека с QR-кодом СКНО и начислением баллов программы лояльности.

### 6. Журнал аудита в реальном времени
* Отображение сессий заправки и инцидентов безопасности в режиме реального времени.
* Поиск по госномеру, фильтрация по типам событий и возможность быстрой очистки журнала.

---

## Архитектура проекта

```
smartvision-azs-belorusneft/
├── desktop_app.py            # Нативное десктоп-приложение (pywebview + Edge WebView2)
├── main.py                   # Точка входа FastAPI сервера
├── config.py                 # Конфигурация, пути, цены на топливо, пороги безопасности
├── database/
│   ├── models.py             # SQLAlchemy ORM: User, Vehicle, FuelingSession, IncidentLog
│   └── db_session.py         # Async SQLite engine (WAL mode) & сид данных
├── vision/
│   ├── anpr_engine.py        # Распознавание номеров РБ (Regex, EasyOCR, эвристика)
│   ├── safety_engine.py      # Детекция риска обрыва шланга (ΔD > 15px / 300ms)
│   ├── tracker.py            # Трекинг центроидов и векторов движения
│   └── pipeline.py           # Конвейер обработки видео, генерация телеметрии и JPEG
├── core/
│   ├── fsm.py                # Конечный автомат (FSM) жизненного цикла заправки
│   ├── roi_calculator.py     # Финансово-экономическая модель ТЭО
│   ├── excel_exporter.py     # Экспорт представительской модели в Excel (.xlsx)
│   └── events.py             # Асинхронный неблокирующий WebSocket-броадкаст
├── api/
│   ├── routes.py             # REST API (сессии, инциденты, ROI, экспорт, стриминг, загрузка)
│   └── ws_handler.py         # WebSocket эндпоинт телеметрии
├── static/
│   ├── index.html            # Главный интерфейс дашборда «Белоруснефть»
│   ├── download.html         # Лендинг-страница загрузки десктоп-клиента
│   ├── css/styles.css        # Корпоративная тема (#00843D, #FFCC00) и печатные стили
│   └── js/
│       ├── app.js            # Контроллер приложения и логика синхронизации
│       ├── canvas_render.js  # Отрисовка Bounding Boxes на Canvas 2D
│       ├── audio_alerts.js   # Звуковые оповещения аварий и успеха
│       └── roi_widget.js     # Виджет ТЭО и графики Chart.js
├── tools/
│   ├── build_desktop.py      # Скрипт сборки дистрибутива Windows-x64 (.zip / .exe)
│   ├── generate_icon.py      # Генератор многослойных иконок .ico и .png
│   └── video_generator.py    # Процедурный генератор синтетических сценариев 30 FPS
├── tests/
│   └── test_smartvision.py   # Набор автотестов (pytest + pytest-asyncio)
├── requirements.txt          # Зависимости Python
└── render.yaml               # Конфигурация развертывания на Render
```

---

## Установка и запуск десктоп-приложения

### Вариант 1. Загрузка готового установщика (.EXE)
Скачайте графический мастер установки: **[SmartVision-AZS-Setup.exe](https://github.com/ArtemChik103/smartvision-azs-belorusneft/releases/download/v1.2.0/SmartVision-AZS-Setup.exe)**.
Мастер автоматически распакует комплекс, создаст ярлыки на Рабочем столе и в меню «Пуск».

### Вариант 2. Портативная версия (.ZIP)
Скачайте архив **[SmartVision-AZS-Windows-x64.zip](https://github.com/ArtemChik103/smartvision-azs-belorusneft/releases/download/v1.2.0/SmartVision-AZS-Windows-x64.zip)**, распакуйте в любую папку и запустите `Запуск_SmartVision_AZS.bat`.

### Вариант 3. Запуск из исходного кода
```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Запуск нативного окна оператора
python desktop_app.py
```

### Сборка дистрибутивов из исходников
* Сборка портативного архива: `python tools/build_desktop.py`
* Сборка исполняемого установщика: `python tools/build_installer_exe.py`

---

## Запуск веб-сервера

```bash
python main.py
```
После запуска:
* Веб-монитор оператора: **`http://localhost:8000`**
* Страница скачивания приложения: **`http://localhost:8000/download`**

---

## Тестирование

```bash
pytest
```

---

## Демонстрационные профили (Seed Data)

| Водитель | Госномер | Модель автомобиля | Топливо | Баланс | Режим заправки |
|---|---|---|---|---|---|
| **Иванов И. И.** | `7777 AB-7` | Volkswagen Passat B8 (2.0 TSI) | АИ-95 | 150.00 BYN | Drive&Pay (Zero-Click) |
| **Петров П. П.** | `1234 IE-7` | Geely Tugella 2.0T | АИ-95 | 95.50 BYN | Drive&Pay |
| **Гость** | `5678 MH-7` | Lada Vesta SW Cross | АИ-92 | 0.00 BYN | Оплата на кассе / терминале |

---

## REST API & WebSocket

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/download` | Страница загрузки десктопного приложения |
| `GET` | `/api/download/windows` | Скачивание дистрибутива Windows-x64 (.zip) |
| `GET` | `/api/download/info` | Метаданные релиза, размер файла и SHA-256 |
| `GET` | `/api/status` | Общий статус системы, активная сессия и FSM-состояние |
| `GET` | `/api/sessions` | Журнал сессий заправки ТРК (включая активный Live-налив) |
| `GET` | `/api/incidents` | Журнал инцидентов и аварийных событий |
| `POST` | `/api/audit/clear` | Очистка всех записей журнала сессий и инцидентов |
| `POST` | `/api/roi/calculate` | Интерактивный расчет финансовой модели ТЭО |
| `POST` | `/api/roi/export-excel` | Экспорт брендированного Excel-отчета (`.xlsx`) |
| `POST` | `/api/simulator/control` | Управление таймлайном симулятора (`scenario_1`, `scenario_2`, `scenario_3`, `seek`) |
| `GET` | `/api/video/feed` | Потоковое MJPEG-видео высокого быстродействия (30 FPS) |
| `WS` | `/ws/telemetry` | WebSocket телеметрии, распознанных рамок и состояния FSM |

---

## Лицензия

Проект разработан в рамках концепции цифровизации сети АЗС «Белоруснефть». Распространяется под лицензией MIT.
