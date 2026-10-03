<?php
/**
 * Meta description, robots.txt and XML sitemap helpers.
 *
 * @package YourSEOAgent
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Outputs custom meta description when set.
 */
function ysa_meta_description() {
	$description = '';

	if ( is_singular() ) {
		$description = get_post_meta( get_queried_object_id(), '_ysa_meta_description', true );
	}

	if ( ! $description && is_front_page() ) {
		$description = 'SEO Team Lead с 14-летним опытом: технический аудит, GEO/AISEO, SEO для iGaming/Betting, СНГ/Яндекс и внедрение собственного AI SEO-агента.';
	}

	if ( $description ) {
		echo '<meta name="description" content="' . esc_attr( $description ) . '">' . "\n";
	}
}
add_action( 'wp_head', 'ysa_meta_description', 1 );

/**
 * Appends Sitemap line to virtual robots.txt.
 *
 * @param string $output Robots output.
 * @return string
 */
function ysa_robots_txt( $output ) {
	$sitemap = home_url( '/sitemap.xml' );
	if ( false === strpos( $output, 'Sitemap:' ) ) {
		$output .= "\nSitemap: " . esc_url_raw( $sitemap ) . "\n";
	}
	return $output;
}
add_filter( 'robots_txt', 'ysa_robots_txt' );

/**
 * Registers custom rewrite for /sitemap.xml when core sitemap is unavailable.
 */
function ysa_register_sitemap_route() {
	add_rewrite_rule( '^sitemap\.xml$', 'index.php?ysa_sitemap=1', 'top' );
	add_rewrite_tag( '%ysa_sitemap%', '1' );
}
add_action( 'init', 'ysa_register_sitemap_route' );

/**
 * Serves a minimal XML sitemap matching the marketing pages.
 */
function ysa_serve_sitemap() {
	if ( ! get_query_var( 'ysa_sitemap' ) ) {
		return;
	}

	// Prefer WordPress 5.5+ core sitemaps when available.
	if ( function_exists( 'wp_sitemaps_get_server' ) ) {
		wp_safe_redirect( home_url( '/wp-sitemap.xml' ), 301 );
		exit;
	}

	$urls = array(
		array( 'loc' => home_url( '/' ), 'priority' => '1.0' ),
		array( 'loc' => ysa_service_url( 'tehnicheskiy-audit' ), 'priority' => '0.8' ),
		array( 'loc' => ysa_service_url( 'geo-aiseo' ), 'priority' => '0.8' ),
		array( 'loc' => ysa_service_url( 'betting-gaming' ), 'priority' => '0.8' ),
		array( 'loc' => ysa_service_url( 'sng-yandex' ), 'priority' => '0.8' ),
		array( 'loc' => ysa_service_url( 'ai-agent' ), 'priority' => '0.8' ),
		array( 'loc' => ysa_contacts_url(), 'priority' => '0.5' ),
	);

	header( 'Content-Type: application/xml; charset=UTF-8' );
	echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
	echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
	foreach ( $urls as $url ) {
		echo '  <url><loc>' . esc_url( $url['loc'] ) . '</loc><priority>' . esc_html( $url['priority'] ) . '</priority></url>' . "\n";
	}
	echo '</urlset>';
	exit;
}
add_action( 'template_redirect', 'ysa_serve_sitemap' );

/**
 * Document title for front page.
 *
 * @param array $parts Title parts.
 * @return array
 */
function ysa_document_title_parts( $parts ) {
	if ( is_front_page() ) {
		$parts['title'] = 'Артур Черемисин — SEO/GEO эксперт: аудиты и AI SEO-агент';
		unset( $parts['tagline'] );
	}
	return $parts;
}
add_filter( 'document_title_parts', 'ysa_document_title_parts' );
