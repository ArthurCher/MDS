<?php
/**
 * Front page template.
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <section class="hero">
    <div class="tag">Платные аудиты и спринты — фикс-прайс, фикс-срок, без найма</div>
    <div class="hero-word display">SEO<span>/</span>GEO</div>
    <div class="hero-sub">
      <p>14+ лет в SEO, из них 3+ года на позициях SEO Team Lead / Head of SEO. Разовые проекты на 5–10 дней: технический аудит, GEO/AISEO, Betting/Gaming, СНГ/Яндекс, внедрение AI-агента для автоматизации SEO-отчетности.</p>
      <div class="hero-actions">
        <a class="btn" href="#services">Смотреть услуги</a>
        <a class="btn-outline" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить задачу</a>
      </div>
    </div>
  </section>

  <div class="stats">
    <div class="stat"><div class="num">14+</div><div class="lbl">лет в SEO</div></div>
    <div class="stat"><div class="num">×5,5</div><div class="lbl">лучший результат по трафику</div></div>
    <div class="stat"><div class="num">3+</div><div class="lbl">года SEO Team Lead / Head of SEO</div></div>
  </div>

  <section id="services">
    <div class="sec-head"><h2>Что можно заказать</h2></div>
    <p class="sec-lead">Фикс-прайс, фикс-срок. Оплата 50% на старте / 50% по сдаче.</p>
    <div class="svc-grid">
      <div class="svc-card">
        <div class="k">АВТОМАТИЗАЦИЯ</div>
        <h3>Внедрение AI SEO-агента</h3>
        <p>Агент под ваш стек (GSC, Метрика, Topvisor, Ahrefs) — диагностика, отчетность, точки роста.</p>
        <div class="meta"><span>$2000–2500</span><span>7–10 дней</span></div>
        <a class="more" href="<?php echo esc_url( ysa_service_url( 'ai-agent' ) ); ?>">Подробнее →</a>
      </div>
      <div class="svc-card">
        <div class="k">IGAMING</div>
        <h3>SEO для Betting/Gaming</h3>
        <p>Линкбилдинг (в т.ч. PBN), техаудит, мультигео, план роста с учетом блокировок и зеркал.</p>
        <div class="meta"><span>$1500</span><span>5–7 дней</span></div>
        <a class="more" href="<?php echo esc_url( ysa_service_url( 'betting-gaming' ) ); ?>">Подробнее →</a>
      </div>
      <div class="svc-card">
        <div class="k">ТЕХНИЧЕСКИЙ АУДИТ</div>
        <h3>Технический SEO-аудит + Roadmap</h3>
        <p>Индексация, скорость, дубли, разметка, семантика, разбор конкурентов и план на 30/60/90 дней.</p>
        <div class="meta"><span>$1000–1200</span><span>5–7 дней</span></div>
        <a class="more" href="<?php echo esc_url( ysa_service_url( 'tehnicheskiy-audit' ) ); ?>">Подробнее →</a>
      </div>
      <div class="svc-card">
        <div class="k">GEO / AISEO</div>
        <h3>GEO/AISEO Readiness Audit</h3>
        <p>Видимость в ChatGPT, Perplexity, Google AI Overview, Яндекс.Алисе. E-E-A-T, Schema.org, план P0–P3.</p>
        <div class="meta"><span>$1200–1500</span><span>5–7 дней</span></div>
        <a class="more" href="<?php echo esc_url( ysa_service_url( 'geo-aiseo' ) ); ?>">Подробнее →</a>
      </div>
      <div class="svc-card">
        <div class="k">СНГ / ЯНДЕКС</div>
        <h3>SEO-аудит для СНГ</h3>
        <p>Поведенческие факторы, ИКС, региональность. Сверка расхождений Яндекс vs Google.</p>
        <div class="meta"><span>$1000–1300</span><span>5–7 дней</span></div>
        <a class="more" href="<?php echo esc_url( ysa_service_url( 'sng-yandex' ) ); ?>">Подробнее →</a>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Результаты на реальных проектах</h2></div>
    <div class="svc-grid results-grid">
      <div class="under-card"><div class="k">×5,5</div><h4>PrivateProxy.me</h4><p>Global SEO, бурж-рынок, 4 года на проекте</p></div>
      <div class="under-card"><div class="k">+30%</div><h4>МегаФон</h4><p>Media Instinct Group, РФ Google/Яндекс</p></div>
      <div class="under-card"><div class="k">×2,5–8</div><h4>Eldorado / Techport</h4><p>РФ e-commerce, несколько проектов</p></div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Как начать</h2></div>
    <div class="steps">
      <div class="step"><div class="step-num">01</div><h4>Созвон</h4><p>15–20 минут — фиксируем задачу и цели</p></div>
      <div class="step"><div class="step-num">02</div><h4>Фикс-прайс</h4><p>Согласовываем стоимость и срок до старта работ</p></div>
      <div class="step"><div class="step-num">03</div><h4>Предоплата</h4><p>50% на старте, 50% по сдаче</p></div>
      <div class="step"><div class="step-num">04</div><h4>Поставка</h4><p>Готовый результат — 5–10 дней</p></div>
    </div>
  </section>

  <section>
    <div class="price-box">
      <div class="p-left">
        <h3>Готовы обсудить задачу?</h3>
        <p>Опишите, что сейчас происходит с сайтом и трафиком — предложу формат и цену.</p>
      </div>
      <div class="p-right">
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Написать в Telegram</a>
      </div>
    </div>
  </section>
</div>

<?php
get_footer();
