<?php
/**
 * Styles and scripts.
 *
 * @package YourSEOAgent
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Enqueues Google Fonts and theme stylesheet.
 */
function ysa_enqueue_assets() {
	wp_enqueue_style(
		'ysa-fonts',
		'https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap',
		array(),
		null
	);

	wp_enqueue_style(
		'ysa-theme',
		get_stylesheet_uri(),
		array( 'ysa-fonts' ),
		YSA_THEME_VERSION
	);

	wp_enqueue_script(
		'ysa-nav',
		get_template_directory_uri() . '/assets/js/nav.js',
		array(),
		YSA_THEME_VERSION,
		true
	);
}
add_action( 'wp_enqueue_scripts', 'ysa_enqueue_assets' );

/**
 * Preconnect for Google Fonts.
 *
 * @param array  $urls          URLs to print for resource hints.
 * @param string $relation_type Relation type.
 * @return array
 */
function ysa_resource_hints( $urls, $relation_type ) {
	if ( 'preconnect' === $relation_type ) {
		$urls[] = array(
			'href' => 'https://fonts.googleapis.com',
		);
		$urls[] = array(
			'href'        => 'https://fonts.gstatic.com',
			'crossorigin' => 'anonymous',
		);
	}
	return $urls;
}
add_filter( 'wp_resource_hints', 'ysa_resource_hints', 10, 2 );
