<?php
/**
 * Template Name: GEO/AISEO
 * Template Post Type: page
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <section class="hero">
    <div class="tag"><a href="<?php echo esc_url( home_url( '/' ) ); ?>">← Все услуги</a></div>
    <div class="hero-word display">GEO<span>/</span>AISEO</div>
    <div class="hero-sub">
      <p>Люди все чаще ищут через ChatGPT и Google AI Overview, а не через десять синих ссылок — и это трафик, который большинство сайтов теряет молча, потому что никто не проверял, как бренд выглядит в AI-поиске.</p>
      <div class="hero-actions">
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить задачу</a>
      </div>
    </div>
  </section>

  <div class="stats">
    <div class="stat"><div class="num">$1200–1500</div><div class="lbl">стоимость</div></div>
    <div class="stat"><div class="num">7 дней</div><div class="lbl">срок поставки</div></div>
    <div class="stat"><div class="num">15–20</div><div class="lbl">сценариев проверки видимости</div></div>
  </div>

  <section>
    <div class="sec-head"><h2>Как устроен аудит</h2></div>
    <div class="cap-list">
      <div class="cap-row">
        <div class="n">01</div>
        <div><h4>Проверка видимости</h4><p>Прогоняю 15–20 приоритетных сценариев/запросов через ChatGPT, Perplexity, Google AI Overview и Яндекс.Алису — фиксирую, упоминается ли бренд, в каком контексте, и кто упоминается вместо вас.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">02</div>
        <div><h4>Аудит E-E-A-T</h4><p>AI-системы сильнее людей ориентируются на сигналы экспертности и достоверности: авторство, ссылки на источники, структура ответа на конкретный вопрос. Разбираю, где контенту не хватает этих сигналов.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">03</div>
        <div><h4>Техническая база</h4><p>Проверяю Schema.org разметку (Organization, Article, FAQ, Product — в зависимости от типа сайта), структуру заголовков и то, насколько легко LLM-краулерам вычленить факт из текста.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">04</div>
        <div><h4>Приоритизация</h4><p>Чек-лист по системе P0–P3: что дает видимость быстрее всего, а что — долгосрочная работа над структурой контента.</p></div>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Почему это работает</h2></div>
    <p class="sec-lead">Одним из первых в своей команде занялся системным построением видимости в LLM-поиске: оценивал и выбирал инструменты для трекинга видимости бренда в AI-поисковых surfaces (Яндекс.Алиса, Google AI Overview, ChatGPT, Perplexity, DeepSeek), разработал внутреннюю документацию по E-E-A-T с приоритетным фреймворком P0–P3.</p>
  </section>

  <section>
    <div class="price-box">
      <div class="p-left">
        <h3>GEO/AISEO Readiness Audit</h3>
        <p>PDF-отчет с результатами проверки по каждому сценарию, аудитом E-E-A-T и приоритетным чек-листом внедрения.</p>
      </div>
      <div class="p-right">
        <span class="price">$1200–1500</span>
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
      <a href="<?php echo esc_url( ysa_service_url( 'betting-gaming' ) ); ?>">SEO для Betting/Gaming</a>
    </div>
  </section>
</div>

<?php
get_footer();
