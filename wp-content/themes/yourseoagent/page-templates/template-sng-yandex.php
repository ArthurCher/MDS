<?php
/**
 * Template Name: СНГ/Яндекс
 * Template Post Type: page
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <section class="hero">
    <div class="tag"><a href="<?php echo esc_url( home_url( '/' ) ); ?>">← Все услуги</a></div>
    <div class="hero-word display">СНГ<span>/</span>ЯНДЕКС</div>
    <div class="hero-sub">
      <p>Яндекс и Google ранжируют по разным правилам — поведенческие факторы, ИКС и региональность работают не так, как в Google. Специалист, который мыслит только Google-логикой, оставляет часть трафика в Яндексе на столе.</p>
      <div class="hero-actions">
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить задачу</a>
      </div>
    </div>
  </section>

  <div class="stats">
    <div class="stat"><div class="num">$1000–1300</div><div class="lbl">стоимость</div></div>
    <div class="stat"><div class="num">7 дней</div><div class="lbl">срок поставки</div></div>
    <div class="stat"><div class="num">100</div><div class="lbl">приоритетных запросов в сверке</div></div>
  </div>

  <section>
    <div class="sec-head"><h2>Как устроен аудит</h2></div>
    <div class="cap-list">
      <div class="cap-row">
        <div class="n">01</div>
        <div><h4>Яндекс-специфика</h4><p>Разбираю поведенческие факторы (отказы, глубина, время на сайте) и то, как они соотносятся с текущими позициями. Проверяю ИКС и его динамику, корректность региональности (геопривязка в Яндекс.Вебмастере, региональные поддомены/URL).</p></div>
      </div>
      <div class="cap-row">
        <div class="n">02</div>
        <div><h4>Семантика под СНГ-выдачу</h4><p>Кластеризация запросов отдельно под Яндекс и Google — они не всегда совпадают: часть запросов имеет разную интент-структуру в двух системах.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">03</div>
        <div><h4>Сверка расхождений</h4><p>По 100 приоритетным запросам сравниваю позиции и логику ранжирования в Яндексе и Google — где сайт теряет в одной системе то, что имеет в другой, и почему.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">04</div>
        <div><h4>Конкуренты через Топвизор/Пиксель Тулс</h4><p>Разбираю, за счет чего конкуренты сильнее именно в Яндекс-выдаче — это часто не то же самое, что делает их сильными в Google.</p></div>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Почему это работает</h2></div>
    <p class="sec-lead">14 лет опыта именно на РФ/СНГ-рынке — с 2012 года веду продвижение параллельно в Яндексе и Google, работал с проектами от 40–50 в параллельном ведении до крупных e-commerce с семантикой в тысячи запросов.</p>
  </section>

  <section>
    <div class="price-box">
      <div class="p-left">
        <h3>SEO-аудит для СНГ (Яндекс + Google)</h3>
        <p>PDF-отчет со сверкой расхождений и планом внедрения, разбитым по системам. Объем — до 500 страниц.</p>
      </div>
      <div class="p-right">
        <span class="price">$1000–1300</span>
        <span class="time">срок 5–7 дней</span>
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить</a>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Смотрите также</h2></div>
    <div class="related">
      <a href="<?php echo esc_url( ysa_service_url( 'tehnicheskiy-audit' ) ); ?>">Технический SEO-аудит + Roadmap</a>
      <a href="<?php echo esc_url( ysa_service_url( 'ai-agent' ) ); ?>">Внедрение AI SEO-агента</a>
      <a href="<?php echo esc_url( ysa_service_url( 'geo-aiseo' ) ); ?>">GEO/AISEO Readiness Audit</a>
    </div>
  </section>
</div>

<?php
get_footer();
