---
marp: true
theme: gaia
size: 16:9
_class: lead
paginate: true
backgroundColor: #0B1120
color: #F8FAFC
style: |
  section {
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    padding: 30px 48px;
    font-size: 18px;
    background-color: #0B1120;
    color: #F8FAFC;
    letter-spacing: -0.01em;
  }
  h1 {
    color: #FFFFFF;
    font-size: 1.85rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
    line-height: 1.2;
  }
  h2 {
    color: #94A3B8;
    font-size: 1.05rem;
    font-weight: 500;
    margin-top: 0;
    margin-bottom: 0.6rem;
  }
  h3 {
    color: #00A84D;
    font-size: 0.95rem;
    font-weight: 700;
    margin-top: 0;
    margin-bottom: 0.2rem;
  }
  .badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background: rgba(0, 168, 77, 0.15);
    color: #00A84D;
    border: 1px solid rgba(0, 168, 77, 0.35);
    margin-bottom: 0.5rem;
  }
  .badge-gold {
    background: rgba(255, 204, 0, 0.12);
    color: #FFCC00;
    border-color: rgba(255, 204, 0, 0.35);
  }
  .badge-red {
    background: rgba(239, 68, 68, 0.12);
    color: #EF4444;
    border-color: rgba(239, 68, 68, 0.35);
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 14px;
  }
  .grid-split {
    display: grid;
    grid-template-columns: 45% 55%;
    gap: 16px;
    align-items: center;
  }
  .card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
  }
  .card p {
    font-size: 0.8rem;
    color: #94A3B8;
    margin: 0;
    line-height: 1.4;
  }
  .card-highlight {
    background: #132338;
    border-color: #00843D;
  }
  .stat-number {
    font-size: 2.1rem;
    font-weight: 800;
    color: #00A84D;
    line-height: 1.1;
    margin-bottom: 2px;
  }
  .stat-label {
    font-size: 0.75rem;
    color: #94A3B8;
    font-weight: 500;
    line-height: 1.3;
  }
  .slide-img {
    width: 100%;
    border-radius: 8px;
    border: 1px solid #334155;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    display: block;
  }
  .flow-box {
    background: #1E293B;
    border-left: 3px solid #00A84D;
    padding: 8px 12px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 8px;
  }
  .flow-box strong {
    color: #F8FAFC;
    font-size: 0.85rem;
  }
  .flow-box p {
    color: #94A3B8;
    font-size: 0.76rem;
    margin: 2px 0 0 0;
  }
  .table-custom {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
  }
  .table-custom th {
    background: #1E293B;
    color: #F8FAFC;
    padding: 6px 10px;
    text-align: left;
    border-bottom: 2px solid #00843D;
  }
  .table-custom td {
    padding: 6px 10px;
    border-bottom: 1px solid #334155;
    color: #CBD5E1;
  }
  /* Architecture Diagram Styles */
  .arch-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 10px;
  }
  .arch-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }
  .arch-node {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
    flex: 1;
    text-align: center;
  }
  .arch-node-main {
    background: #132338;
    border: 1.5px solid #00A84D;
    box-shadow: 0 0 12px rgba(0, 168, 77, 0.2);
  }
  .arch-node strong {
    display: block;
    color: #F8FAFC;
    font-size: 0.84rem;
    margin-bottom: 3px;
  }
  .arch-node span {
    display: block;
    color: #94A3B8;
    font-size: 0.72rem;
  }
  .arch-arrow {
    color: #00A84D;
    font-weight: 800;
    font-size: 1.1rem;
  }
---

<!-- _class: lead -->
<!-- _paginate: false -->

<div class="badge">Марафон ИТ-стартапов 2026 · РУП «ПО «Белоруснефть»</div>

<br>

# SmartVision AZS
## Автоматизированный комплекс компьютерного зрения, безопасности и безакцептной оплаты для сети АЗС

<br>

<div style="text-align: center; margin: 0 auto;">
  <div style="display: inline-block; background: #1E293B; border: 1px solid #334155; padding: 10px 24px; border-radius: 8px;">
    <p style="margin: 0; font-size: 0.88rem; color: #CBD5E1;"><strong>Номинация:</strong> <span style="color: #00A84D; font-weight: 700;">Цифровая АЗС</span></p>
  </div>
</div>

<br><br>

<p style="font-size: 0.82rem; color: #64748B; margin-top: 10px;">Разработчик проекта · Минск, 2026 год</p>

---

<div class="badge badge-red">Проблематика</div>

# Потери и риски сети АЗС
## Анализ ключевых факторов простоя колонок и внеплановых расходов

<div class="grid-split">
  <div>
    <div class="flow-box" style="border-left-color: #EF4444;">
      <strong>Очереди на кассах (210с / авто)</strong>
      <p>75% времени колонка заблокирована в ожидании оплаты водителем в торговом зале.</p>
    </div>
    <div class="flow-box" style="border-left-color: #EF4444;">
      <strong>Обрывы шлангов (до 160 инцидентов/год)</strong>
      <p>Прямой ущерб свыше 192 000 BYN (разрывные муфты, ремонт, простой колонок).</p>
    </div>
    <div class="flow-box" style="border-left-color: #EF4444;">
      <strong>Кассовые разрывы в кафе</strong>
      <p>Очереди за топливом отпугивают покупателей сопутствующих товаров и кофе (-12% выручки).</p>
    </div>
  </div>

  <div class="card card-highlight" style="padding: 16px;">
    <div class="stat-number" style="color: #EF4444;">-75%</div>
    <div class="stat-label" style="font-size: 0.85rem; color: #E2E8F0;">Потери пропускной способности ТРК из-за походов на кассу</div>
    <hr style="border-color: #334155; margin: 12px 0;">
    <p style="color: #94A3B8; font-size: 0.78rem;"><strong>Задача:</strong> Автоматизировать идентификацию, налив и безопасность ТРК без установки дорогостоящих уличных терминалов на каждой колонке.</p>
  </div>
</div>

---

<div class="badge">Концепция</div>

# Архитектура комплекса SmartVision AZS
## Превращение стандартной ТРК в автономный пост по существующим камерам

<div class="grid-split">
  <div>
    <div class="flow-box">
      <strong>1. Edge AI Компьютерное зрение</strong>
      <p>YOLOv8 Nano (30 FPS) распознает номера авто (OCR > 98%), кузов и положение пистолета.</p>
    </div>
    <div class="flow-box">
      <strong>2. Предиктивный E-STOP (300 мс)</strong>
      <p>Мгновенная отсечка насоса при смещении авто > 15px до натяжения рукава.</p>
    </div>
    <div class="flow-box">
      <strong>3. Бесшовный налив Zero-Click</strong>
      <p>Интеграция с Drive&Pay: автоматический пуск и безакцептное списание.</p>
    </div>
    <div class="flow-box">
      <strong>4. Фискализация и СКНО</strong>
      <p>Генерация электронных чеков с QR-кодом и передача в налоговые органы.</p>
    </div>
  </div>

  <div>
    <img src="assets/screen_monitor.png" class="slide-img" alt="Интерфейс системы SmartVision AZS">
  </div>
</div>

---

<div class="badge">Сценарий 1</div>

# Сквозной налив Zero-Click (Drive&Pay)
## Полный цикл обслуживания без посещения кассы за 45 секунд

<div class="grid-split">
  <div>
    <div class="flow-box">
      <strong>1. Подъезд и детекция (t=0..3c)</strong>
      <p>Автоматическое распознавание номера (7777 AB-7) и профиля водителя.</p>
    </div>
    <div class="flow-box">
      <strong>2. Вставка пистолета (t=4..8c)</strong>
      <p>Фиксация сопла в горловине бака. Автоматический пуск насоса АИ-95.</p>
    </div>
    <div class="flow-box">
      <strong>3. Автоматический налив (t=9..35c)</strong>
      <p>Отпуск 30.0 л с передачей телеметрии на монитор оператора.</p>
    </div>
    <div class="flow-box">
      <strong>4. Списание и чек (t=36..45c)</strong>
      <p>Безакцептное списание 73.80 BYN и начисление бонусов.</p>
    </div>
  </div>

  <div>
    <img src="assets/screen_zeroclick.png" class="slide-img" alt="Сценарий Zero-Click">
  </div>
</div>

---

<div class="badge badge-red">Сценарий 2 · Безопасность</div>

# Предотвращение обрыва шлангов (E-STOP)
## Аппаратная отсечка насоса за 300 мс при начале движения авто

<div class="grid-split">
  <div>
    <div class="flow-box" style="border-left-color: #EF4444;">
      <strong>Оптический трекинг смещения (ΔD > 15px)</strong>
      <p>Пока пистолет в баке, система контролирует координаты кузова 30 раз в секунду.</p>
    </div>
    <div class="flow-box" style="border-left-color: #EF4444;">
      <strong>Мгновенное реле E-STOP (< 300 мс)</strong>
      <p>Снятие питания с электромагнитного клапана ТРК до натяжения разрывной муфты.</p>
    </div>
    <div class="flow-box" style="border-left-color: #EF4444;">
      <strong>Тревога и фотофиксация</strong>
      <p>Включение светозвуковой сирены и запись HD стоп-кадра инцидента в журнал.</p>
    </div>
    <div class="card card-highlight" style="margin-top: 10px; padding: 10px;">
      <p style="color: #00A84D; font-weight: 700; font-size: 0.82rem;">Экономия 192 000 BYN/год на сохранности колонок</p>
    </div>
  </div>

  <div>
    <img src="assets/screen_estop.png" class="slide-img" alt="Сценарий E-STOP тревоги">
  </div>
</div>

---

<div class="badge">Сценарий 3 · Фискализация</div>

# Гостевой режим и электронные чеки
## Универсальная поддержка клиентов без приложения и наличных расчетов

<div class="grid-split">
  <div>
    <div class="flow-box">
      <strong>Гостевой режим (5678 MH-7)</strong>
      <p>Обслуживание незарегистрированных клиентов через кассу / терминал.</p>
    </div>
    <div class="flow-box">
      <strong>Электронный чек с QR-кодом</strong>
      <p>Фискализация стандартов МНС РБ (наименование, литры, сумма, бонусы).</p>
    </div>
    <div class="flow-box">
      <strong>Совместимость с СКНО</strong>
      <p>Бесшовная передача данных в учетные и налоговые системы «Белоруснефть».</p>
    </div>
  </div>

  <div>
    <img src="assets/screen_receipt.png" class="slide-img" alt="Фискальный чек Белоруснефть">
  </div>
</div>

---

<div class="badge">Архитектура и потоки данных</div>

# Схема работы контура SmartVision AZS
## Взаимодействие Edge AI, исполнительных реле ТРК и облачной экосистемы

<div class="arch-container">
  <!-- Tier 1: Input -->
  <div class="arch-row">
    <div class="arch-node">
      <strong>Обзорная IP-камера ТРК</strong>
      <span>RTSP / 30 FPS / H.264 (Штатная камера)</span>
    </div>
    <div class="arch-arrow">➔</div>
    <div class="arch-node arch-node-main">
      <strong style="color: #00A84D;">Edge AI Core (YOLOv8 + OpenCV)</strong>
      <span>Детекция госномеров (OCR > 98%), кузова и пистолета</span>
    </div>
    <div class="arch-arrow">➔</div>
    <div class="arch-node arch-node-main">
      <strong style="color: #00A84D;">FSM Контроллер состояния</strong>
      <span>IDLE ➔ IDENTIFIED ➔ FUELING ➔ COMPLETE</span>
    </div>
  </div>

  <!-- Tier 2: Output split -->
  <div class="arch-row" style="margin-top: 6px;">
    <div class="arch-node" style="border-color: #EF4444; background: #24141E;">
      <strong style="color: #F87171;">Аппаратный E-STOP (< 300мс)</strong>
      <span>Отсечка электромагнитного клапана ТРК</span>
    </div>
    <div class="arch-node" style="border-color: #38BDF8; background: #112233;">
      <strong style="color: #38BDF8;">Десктоп оператора (WebView2)</strong>
      <span>Локальная телеметрия по WebSockets 12.5 Гц</span>
    </div>
    <div class="arch-node" style="border-color: #FFCC00; background: #262215;">
      <strong style="color: #FFCC00;">Процессинг Drive&Pay / СКНО</strong>
      <span>Безакцептное списание и фискальный чек</span>
    </div>
  </div>
</div>

<div class="card card-highlight" style="margin-top: 14px; padding: 10px 14px;">
  <p style="color: #E2E8F0; font-size: 0.8rem;"><strong>Автономность станции (Offline Survivability):</strong> При обрыве связи с интернетом налив и система защиты от обрыва продолжают функционировать локально на 100%.</p>
</div>

---

<div class="badge badge-gold">ТЭО и Финансы</div>

# Экономическая эффективность и окупаемость
## Расчет финансовой модели на масштабе сети «Белоруснефть» (570 АЗС)

<div class="grid-split">
  <div>
    <table class="table-custom">
      <thead>
        <tr>
          <th>Статья эффекта</th>
          <th>Эффект (BYN/год)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Предотвращение обрывов шлангов (160 инцидентов)</td>
          <td style="color: #00A84D; font-weight: 700;">+192 000</td>
        </tr>
        <tr>
          <td>Рост продаж топлива (+4% трафика)</td>
          <td style="color: #00A84D; font-weight: 700;">+12 450 000</td>
        </tr>
        <tr>
          <td>Маржа кафе и сопутствующих товаров</td>
          <td style="color: #00A84D; font-weight: 700;">+9 364 850</td>
        </tr>
        <tr style="background: #1E293B;">
          <td><strong>ЧИСТЫЙ ГОДОВОЙ ЭФФЕКТ</strong></td>
          <td style="color: #FFCC00; font-weight: 900;">22 006 850 BYN</td>
        </tr>
      </tbody>
    </table>
    <div style="margin-top: 10px;" class="card card-highlight">
      <p style="color: #F8FAFC;"><strong>CAPEX на всю сеть:</strong> 380 000 BYN · <strong>Окупаемость:</strong> &lt; 1 мес.</p>
    </div>
  </div>

  <div>
    <img src="assets/screen_roi.png" class="slide-img" alt="График окупаемости ROI">
  </div>
</div>

---

<div class="badge">Масштабирование</div>

# Пресеты поэтапного внедрения
## Сценарии развертывания от пилотной станции до масштаба всей сети

<div class="grid-3">
  <div class="card">
    <div class="badge">Этап 1 · Пилот</div>
    <h3>1 АЗС / 4 ТРК</h3>
    <p><strong>CAPEX:</strong> 6 500 BYN</p>
    <p><strong>Эффект:</strong> 38 600 BYN/год</p>
    <p><strong>Окупаемость:</strong> 2 месяца</p>
    <p style="margin-top: 6px;">Тестирование на АЗС №1 г. Минск, калибровка камер.</p>
  </div>
  <div class="card">
    <div class="badge">Этап 2 · Область</div>
    <h3>60 АЗС / 360 ТРК</h3>
    <p><strong>CAPEX:</strong> 85 000 BYN</p>
    <p><strong>Эффект:</strong> 2.31 млн BYN/год</p>
    <p><strong>Окупаемость:</strong> 1 месяц</p>
    <p style="margin-top: 6px;">Оснащение магистралей М1, М3, М5 и областных центров.</p>
  </div>
  <div class="card card-highlight">
    <div class="badge badge-gold">Этап 3 · Вся сеть</div>
    <h3>570 АЗС / 3 420 ТРК</h3>
    <p><strong>CAPEX:</strong> 380 000 BYN</p>
    <p><strong>Эффект:</strong> 22.0 млн BYN/год</p>
    <p><strong>Окупаемость:</strong> 20 дней</p>
    <p style="margin-top: 6px;">Полная раскатка на все заправочные станции сети.</p>
  </div>
</div>

<br>

<div class="card" style="background: rgba(15, 23, 42, 0.6); border-color: #334155;">
  <p style="color: #E2E8F0;">Комплекс окупается уже на стадии пилота за счет предотвращения даже 1–2 инцидентов обрыва гидравлики.</p>
</div>

---

<div class="badge">Сравнение</div>

# Преимущества перед терминалами самообслуживания (OPT)
## Почему SmartVision AZS эффективнее и экономичнее классических терминалов

<div class="grid-2">
  <div class="card" style="border-color: rgba(239, 68, 68, 0.4);">
    <h3 style="color: #F87171;">Стационарные терминалы (OPT)</h3>
    <p>• Стоимость от 15 000 BYN на каждую колонку.</p>
    <p>• Земляные работы, кабельные трассы, сертификация.</p>
    <p>• Не защищают от обрыва раздаточного рукава.</p>
    <p>• Клиент мерзнет на улице, набирая данные на клавиатуре.</p>
  </div>
  <div class="card card-highlight" style="border-color: #00A84D;">
    <h3 style="color: #00A84D;">Комплекс SmartVision AZS</h3>
    <p>• В <strong>10 раз дешевле</strong> (использует штатные камеры).</p>
    <p>• Развертывание за <strong>1 рабочий день</strong> без простоя АЗС.</p>
    <p>• Встроенная защита <strong>E-STOP (&lt; 300 мс)</strong> от обрыва шланга.</p>
    <p>• Сценарий <strong>Zero-Click</strong> — водитель вообще не касается экрана.</p>
  </div>
</div>

<br>

<div class="grid-3">
  <div class="card">
    <div class="stat-number">1 день</div>
    <div class="stat-label">Монтаж и запуск на станции</div>
  </div>
  <div class="card">
    <div class="stat-number">x10</div>
    <div class="stat-label">Экономия бюджета против OPT</div>
  </div>
  <div class="card">
    <div class="stat-number">100%</div>
    <div class="stat-label">Отечественный стек ПО</div>
  </div>
</div>

---

<!-- _class: lead -->
<!-- _paginate: false -->

<div class="badge">Готовность к внедрению</div>

# SmartVision AZS — Готов к промышленному пилоту
## Работающий прототип развернут и доступен для тестирования комиссии

<div class="grid-2" style="text-align: left; margin-top: 12px;">
  <div class="card card-highlight">
    <h3>Инфраструктура проекта</h3>
    <p>• <strong>Онлайн-дашборд и симулятор ТРК:</strong><br><a href="https://smartvision-azs.onrender.com" style="color: #38BDF8; text-decoration: none;">https://smartvision-azs.onrender.com</a></p>
    <p style="margin-top: 6px;">• <strong>Десктоп-клиент (GitHub Releases):</strong><br><a href="https://github.com/ArtemChik103/smartvision-azs-belorusneft/releases/latest" style="color: #38BDF8; text-decoration: none;">GitHub Releases (Setup .EXE / Portable)</a></p>
    <p style="margin-top: 6px;">• <strong>Открытый репозиторий и исходный код:</strong><br><a href="https://github.com/ArtemChik103/smartvision-azs-belorusneft" style="color: #38BDF8; text-decoration: none;">GitHub: ArtemChik103/smartvision-azs-belorusneft</a></p>
  </div>
  <div class="card card-highlight">
    <h3>Контакты и согласование пилота</h3>
    <p><strong>Номинация:</strong> Цифровая АЗС</p>
    <p><strong>Конкурс:</strong> «Марафон ИТ-стартапов» 2026</p>
    <p><strong>Заказчик:</strong> РУП «ПО «Белоруснефть»</p>
    <p style="margin-top: 10px; color: #00A84D; font-weight: 700;">Готовы к развертыванию пилотной зоны на АЗС №1 г. Минска</p>
  </div>
</div>

<br>

<p style="font-size: 0.8rem; color: #64748B;">SmartVision AZS · Белоруснефть · 2026</p>
