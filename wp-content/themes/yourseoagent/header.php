<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<nav>
  <div class="nav-inner">
    <a href="<?php echo esc_url( home_url( '/' ) ); ?>" style="text-decoration:none;">
      <div class="brand">
        <span class="n">Артур Черемисин</span>
        <span class="r">SEO / GEO эксперт</span>
      </div>
    </a>
    <button class="nav-toggle" type="button" aria-label="Меню" aria-expanded="false" aria-controls="ysa-nav-links">
      <span></span>
    </button>
    <div class="nav-links" id="ysa-nav-links">
      <a href="<?php echo esc_url( ysa_service_url( 'ai-agent' ) ); ?>" class="<?php echo esc_attr( ysa_nav_active( 'ai-agent' ) ); ?>">AI-агент</a>
      <a href="<?php echo esc_url( ysa_service_url( 'betting-gaming' ) ); ?>" class="<?php echo esc_attr( ysa_nav_active( 'betting-gaming' ) ); ?>">Betting/Gaming</a>
      <a href="<?php echo esc_url( ysa_service_url( 'tehnicheskiy-audit' ) ); ?>" class="<?php echo esc_attr( ysa_nav_active( 'tehnicheskiy-audit' ) ); ?>">Технический аудит</a>
      <a href="<?php echo esc_url( ysa_service_url( 'geo-aiseo' ) ); ?>" class="<?php echo esc_attr( ysa_nav_active( 'geo-aiseo' ) ); ?>">GEO/AISEO</a>
      <a href="<?php echo esc_url( ysa_service_url( 'sng-yandex' ) ); ?>" class="<?php echo esc_attr( ysa_nav_active( 'sng-yandex' ) ); ?>">СНГ/Яндекс</a>
      <a href="<?php echo esc_url( ysa_contacts_url() ); ?>" class="<?php echo esc_attr( ysa_nav_active( 'contacts' ) ); ?>">Контакты</a>
    </div>
    <a class="btn" href="<?php echo esc_url( YSA_TELEGRAM_URL ); ?>" target="_blank" rel="noopener">Написать</a>
  </div>
</nav>
