# SmartVision AZS — Белоруснефть

Прототип системы компьютерного зрения и телеметрии для сети АЗС «Белоруснефть»:
1. **Zero-Click Drive&Pay** — автоматическая заправка по распознаванию госномера РБ и списанию средств с баланса профиля.
2. **Модуль предотвращения обрыва шлангов** — детекция преждевременного движения автомобиля при вставленном пистолете и мгновенная блокировка насоса.
3. **Интерактивный ROI-калькулятор** — расчет окупаемости внедрения на сеть из 570 АЗС.
4. **Синтетический генератор видео** — встроенный модуль симуляции трех типовых сценариев на ТРК.

---

## Архитектура системы

```
smartvision_azs/
├── config.py                 # Настройки, пороги детекции, экономические константы
├── database/
│   ├── models.py             # ORM-модели: User, Vehicle, FuelingSession, IncidentLog
│   └── db_session.py         # Async SQLite engine & авто-заполнение seed-данными
├── vision/
│   ├── anpr_engine.py        # Распознавание номеров РБ (Regex + EasyOCR + эвристика)
│   ├── safety_engine.py      # Алгоритм фиксации риска обрыва шланга (ΔD > 15 px / 300 ms)
│   ├── tracker.py            # Трекинг центроидов и расчет скорости
│   └── pipeline.py           # Конвейер обработки кадров и телеметрии
├── core/
│   ├── fsm.py                # Finite State Machine процесса заправки
│   ├── roi_calculator.py     # Модель расчета финансового эффекта и окупаемости
│   └── events.py             # Event Bus и менеджер WebSocket-соединений
├── api/
│   ├── routes.py             # REST API (сессии, логи, расчет ROI, E-STOP)
│   └── ws_handler.py         # WebSocket видеопотока и телеметрии
├── static/
│   ├── index.html            # Главный дашборд (Видео, Drive&Pay, ROI, Аудит)
│   ├── css/styles.css        # Корпоративная тема «Белоруснефть» (#00843D, #FFCC00)
│   └── js/
│       ├── app.js            # Логика интерфейса и WebSocket-клиент
│       ├── canvas_render.js  # Отрисовка Bounding Boxes на видео
│       ├── audio_alerts.js   # Звуковые оповещения (Web Audio API)
│       └── roi_widget.js     # Интерактивный калькулятор окупаемости с графиками Chart.js
├── tools/
│   └── video_generator.py    # Генератор синтетических тестовых видео (3 сценария)
├── main.py                   # Точка входа FastAPI
├── requirements.txt
└── README.md
```

---

## Математические модели и формулы

### 1. Алгоритм защиты от обрыва шланга
- **Условие срабатывания аварийной блокировки (E-STOP):**

$$\text{NozzleInTank} = \text{True} \quad \land \quad \Delta D \ge 15\,\text{px} \quad (\Delta t = 300\,\text{ms})$$

- **Реакция:** мгновенный аппаратный сигнал отключения насоса (`pump_locked = True`), активация двухтональной сирены и запись инцидента безопасности в базу данных.

### 2. Формула расчета экономической эффективности (ROI)

$$\text{Savings}_{\text{hose}} = N_{\text{stations}} \times N_{\text{incidents/year}} \times C_{\text{damage}}$$

$$\text{Profit}_{\text{retail}} = N_{\text{stations}} \times \text{Traffic}_{\text{daily}} \times 365 \times \Delta_{\text{check}} \times \text{Margin}$$

$$\text{Payback (months)} = \frac{\text{Capex}}{(\text{Savings}_{\text{hose}} + \text{Profit}_{\text{retail}} - \text{Opex}) / 12}$$

* **$\text{Savings}_{\text{hose}}$** — годовая экономия на предотвращении повреждений ТРК и разрывов шлангов.
* **$\text{Profit}_{\text{retail}}$** — дополнительная маржинальная прибыль кафе и магазина АЗС за счет ускорения Zero-Click обслуживания (сокращение времени у колонки на $-78\%$).
* **$\text{Payback}$** — срок окупаемости инвестиций в месяцах.

---

## Быстрый запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Генерация тестового видео (опционально, генерируется автоматически при первом запуске)
```bash
python tools/video_generator.py
```

### 3. Запуск веб-сервера
```bash
python main.py
```

После запуска откройте в браузере: `http://localhost:8000`

---

## Тестовые учетные записи (Seed Data)

| Водитель | Госномер | Автомобиль | Топливо | Баланс | Режим |
|---|---|---|---|---|---|
| Иванов И. И. | `7777 AB-7` | Volkswagen Passat B8 (2.0 TSI) | АИ-95 | 150.00 BYN | Drive&Pay (Zero-Click) |
| Петров П. П. | `1234 IE-7` | Geely Tugella 2.0T | АИ-95 | 95.50 BYN | Drive&Pay |
| Гость | `5678 MH-7` | Lada Vesta SW Cross | АИ-92 | 0.00 BYN | Оплата на кассе / терминал |

---

## REST API Endpoints

- `GET /api/status` — состояние системы, активная сессия и FSM-статус.
- `GET /api/sessions` — история завершенных сессий заправки.
- `GET /api/incidents` — журнал инцидентов и безопасности.
- `POST /api/emergency-stop` — ручная блокировка ТРК (кнопка E-STOP).
- `POST /api/reset-alarm` — сброс состояния аварии и разблокировка насоса.
- `POST /api/roi/calculate` — расчет окупаемости по входным параметрам сети.
- `POST /api/simulator/control?action=scenario_1|scenario_2|scenario_3|seek` — управление симуляцией и перемотка.
- `GET /api/video/feed` — видеопоток MJPEG для мониторинга.
- `WS /ws/telemetry` — двусторонний WebSocket телеметрии и координат Bounding Boxes.
