<?php
/**
 * Template Name: Технический аудит
 * Template Post Type: page
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <section class="hero">
    <div class="tag"><a href="<?php echo esc_url( home_url( '/' ) ); ?>">← Все услуги</a></div>
    <div class="hero-word display">SEO<span>-</span>АУДИТ</div>
    <div class="hero-sub">
      <p>Большинство SEO-аудитов заканчиваются общими рекомендациями вроде «улучшите контент». Я нахожу конкретную причину, почему сайт теряет трафик — техническую, структурную или семантическую — и отдаю план, который можно внедрять со следующего дня.</p>
      <div class="hero-actions">
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить задачу</a>
      </div>
    </div>
  </section>

  <div class="stats">
    <div class="stat"><div class="num">$1000–1200</div><div class="lbl">стоимость</div></div>
    <div class="stat"><div class="num">7 дней</div><div class="lbl">срок поставки</div></div>
    <div class="stat"><div class="num">500</div><div class="lbl">страниц объем аудита</div></div>
  </div>

  <section>
    <div class="sec-head"><h2>Как устроен аудит</h2></div>
    <div class="cap-list">
      <div class="cap-row">
        <div class="n">01</div>
        <div><h4>Технический слой</h4><p>Проверяю индексацию через GSC и Яндекс.Вебмастер: какие страницы реально в индексе, какие исключены и почему. Screaming Frog — полный краулинг сайта: дубли title/description/H1, битые ссылки, редиректы, глубина вложенности, скорость загрузки, Core Web Vitals, корректность канонических тегов и микроразметки Schema.org.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">02</div>
        <div><h4>Семантика и структура</h4><p>Разбираю фактическую семантику сайта против отслеживаемой и потенциальной. Смотрю на кластеризацию: нет ли каннибализации между страницами, закрывает ли структура сайта всю коммерчески значимую семантику.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">03</div>
        <div><h4>Конкурентный анализ</h4><p>Через Ahrefs и Keys.so сравниваю с топ-3 конкурентами: по каким запросам они ранжируются, а вы — нет; насколько сильнее их ссылочный профиль; где у них лучше техническая реализация.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">04</div>
        <div><h4>Приоритизация</h4><p>Не просто список проблем, а план по соотношению «эффект / трудозатраты» — Quick Wins на 30 дней отдельно от структурных изменений на 60–90 дней.</p></div>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Почему это работает</h2></div>
    <p class="sec-lead">14 лет в SEO, из них 3+ года на позициях SEO Team Lead / Head of SEO. Референсы по результатам похожих аудитов и последующей работы: рост органического трафика в 5,5 раз на проекте под Global-рынок, от 2,5 до 8 раз — на нескольких проектах e-commerce, +30% — на проекте федерального масштаба.</p>
  </section>

  <section>
    <div class="price-box">
      <div class="p-left">
        <h3>Технический SEO-аудит + Roadmap</h3>
        <p>PDF-отчет с чек-листом проблем, скриншотами конкретных ошибок и планом устранения по приоритету, плюс разбор результатов на созвоне.</p>
      </div>
      <div class="p-right">
        <span class="price">$1000–1200</span>
        <span class="time">срок 5–7 дней</span>
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить</a>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Смотрите также</h2></div>
    <div class="related">
      <a href="<?php echo esc_url( ysa_service_url( 'geo-aiseo' ) ); ?>">GEO/AISEO Readiness Audit</a>
      <a href="<?php echo esc_url( ysa_service_url( 'sng-yandex' ) ); ?>">SEO-аудит для СНГ (Яндекс + Google)</a>
      <a href="<?php echo esc_url( ysa_service_url( 'ai-agent' ) ); ?>">Внедрение AI SEO-агента</a>
    </div>
  </section>
</div>

<?php
get_footer();
