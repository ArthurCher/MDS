<?php
/**
 * Template Name: Контакты
 * Template Post Type: page
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <section class="hero">
    <div class="tag"><a href="<?php echo esc_url( home_url( '/' ) ); ?>">← Все услуги</a></div>
    <div class="hero-word display">КОНТАКТЫ</div>
    <div class="hero-sub">
      <p>Отвечаю в течение дня. Быстрее всего — через Telegram.</p>
    </div>
  </section>

  <section>
    <div class="under-grid contacts-grid">
      <div class="under-card">
        <div class="k">TELEGRAM</div>
        <h4>Самый быстрый способ связи</h4>
        <p><a href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">@arturcheremisin</a></p>
      </div>
      <div class="under-card">
        <div class="k">WHATSAPP</div>
        <h4>Пишите или звоните</h4>
        <p><a href="<?php echo esc_url( YSA_WHATSAPP_URL ); ?>" target="_blank" rel="noopener"><?php echo esc_html( YSA_PHONE_DISPLAY ); ?></a></p>
      </div>
      <div class="under-card">
        <div class="k">ТЕЛЕФОН</div>
        <h4>Звонок</h4>
        <p><a href="tel:<?php echo esc_attr( YSA_PHONE ); ?>"><?php echo esc_html( YSA_PHONE_DISPLAY ); ?></a></p>
      </div>
      <div class="under-card">
        <div class="k">ПОЧТА</div>
        <h4>Для документов и формальной переписки</h4>
        <p><a href="mailto:<?php echo esc_attr( YSA_EMAIL ); ?>"><?php echo esc_html( YSA_EMAIL ); ?></a></p>
      </div>
    </div>
  </section>
</div>

<?php
get_footer();
