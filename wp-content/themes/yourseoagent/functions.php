<?php
/**
 * YourSEOAgent theme functions.
 *
 * @package YourSEOAgent
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'YSA_THEME_VERSION', '1.0.0' );
define( 'YSA_TELEGRAM_URL', 'https://t.me/arturcheremisin' );
define( 'YSA_WHATSAPP_URL', 'https://wa.me/79165096868' );
define( 'YSA_PHONE', '+79165096868' );
define( 'YSA_PHONE_DISPLAY', '+7 (916) 509-68-68' );
define( 'YSA_EMAIL', 'shade.mailbox@gmail.com' );

require_once get_template_directory() . '/inc/setup.php';
require_once get_template_directory() . '/inc/enqueue.php';
require_once get_template_directory() . '/inc/pages.php';
require_once get_template_directory() . '/inc/seo.php';

/**
 * URL страницы услуги по slug.
 *
 * @param string $slug Service page slug.
 * @return string
 */
function ysa_service_url( $slug ) {
	$page = get_page_by_path( 'services/' . $slug );
	if ( $page ) {
		return get_permalink( $page );
	}
	return home_url( '/services/' . $slug . '/' );
}

/**
 * URL контактов.
 *
 * @return string
 */
function ysa_contacts_url() {
	$page = get_page_by_path( 'contacts' );
	if ( $page ) {
		return get_permalink( $page );
	}
	return home_url( '/contacts/' );
}

/**
 * Активный класс для пункта меню.
 *
 * @param string $slug Current page slug or 'home' / 'contacts'.
 * @return string
 */
function ysa_nav_active( $slug ) {
	if ( 'home' === $slug && is_front_page() ) {
		return 'active';
	}
	if ( 'contacts' === $slug && is_page( 'contacts' ) ) {
		return 'active';
	}
	if ( is_page( $slug ) ) {
		return 'active';
	}
	return '';
}
