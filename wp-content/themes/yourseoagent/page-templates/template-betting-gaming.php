<?php
/**
 * Template Name: Betting/Gaming
 * Template Post Type: page
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <section class="hero">
    <div class="tag"><a href="<?php echo esc_url( home_url( '/' ) ); ?>">← Все услуги</a></div>
    <div class="hero-word display">iGAMING<span>/</span>SEO</div>
    <div class="hero-sub">
      <p>У Betting/Gaming своя механика проблем. Google держит гэмблинг под усиленным контролем как YMYL-нишу. Площадки регулярно блокируют по юрисдикциям, whitehat-сайты почти не ссылаются на букмекера, а десятки гео-версий одной продуктовой линейки почти всегда каннибализируют друг друга в выдаче.</p>
      <div class="hero-actions">
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить задачу</a>
      </div>
    </div>
  </section>

  <div class="stats">
    <div class="stat"><div class="num">$1500</div><div class="lbl">стоимость</div></div>
    <div class="stat"><div class="num">7 дней</div><div class="lbl">срок поставки</div></div>
    <div class="stat"><div class="num">×5,5</div><div class="lbl">рост трафика на мультиязычном проекте</div></div>
  </div>

  <section>
    <div class="sec-head"><h2>Как устроен аудит</h2></div>
    <div class="cap-list">
      <div class="cap-row">
        <div class="n">01</div>
        <div><h4>Ссылочный профиль</h4><p>Через Ahrefs и Keys.so разбираю текущий линкбилдинг, включая PBN-составляющую: DR доноров, анкор-лист, риск-факторы (шаблонность сети, пересечение IP/хостинга), битые backlinks.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">02</div>
        <div><h4>Технический аудит и мультигео</h4><p>Проверяю корректность hreflang, дублирование контента между языковыми/гео-версиями, индексацию каждой версии отдельно, скорость и CWV.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">03</div>
        <div><h4>Архитектура каталога</h4><p>Структура каталога (линии ставок, категории игр) — то, что либо помогает масштабировать семантику, либо создает тысячи почти дублирующих страниц. Разбираю, что из этого происходит у вас.</p></div>
      </div>
      <div class="cap-row">
        <div class="n">04</div>
        <div><h4>План с учетом рисков ниши</h4><p>Что делать при возможной блокировке домена, как быстро выводить зеркало без потери накопленного веса, как избежать санкций за агрессивный линкбилдинг.</p></div>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Реальный опыт в нише</h2></div>
    <p class="sec-lead">Вел SEO-направление СНГ для букмекера, строил линкбилдинг на PBN для игрового маркетплейса, разворачивал мультиязычную стратегию под бурж-рынок с ростом трафика в 5,5 раз. Сейчас веду Senior Global SEO/GEO по всем Tier-1 локалям одновременно (США, Европа, Латинская Америка, Африка) для проекта с рейтингами и обзорами букмекеров.</p>
  </section>

  <section>
    <div class="price-box">
      <div class="p-left">
        <h3>SEO-аудит для Betting/Gaming</h3>
        <p>PDF-отчет с приоритизированным планом и оценкой рисков по каждому направлению. Объем — до 500 страниц, до 500 referring domains, до 5 языковых/гео-версий.</p>
      </div>
      <div class="p-right">
        <span class="price">$1500</span>
        <span class="time">срок 5–7 дней</span>
        <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Обсудить</a>
      </div>
    </div>
  </section>

  <section>
    <div class="sec-head"><h2>Смотрите также</h2></div>
    <div class="related">
      <a href="<?php echo esc_url( ysa_service_url( 'ai-agent' ) ); ?>">Внедрение AI SEO-агента</a>
      <a href="<?php echo esc_url( ysa_service_url( 'tehnicheskiy-audit' ) ); ?>">Технический SEO-аудит + Roadmap</a>
      <a href="<?php echo esc_url( ysa_service_url( 'geo-aiseo' ) ); ?>">GEO/AISEO Readiness Audit</a>
    </div>
  </section>
</div>

<?php
get_footer();
