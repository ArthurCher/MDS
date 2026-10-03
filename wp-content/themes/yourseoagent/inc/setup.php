<?php
/**
 * Theme setup.
 *
 * @package YourSEOAgent
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Registers theme supports and menus.
 */
function ysa_theme_setup() {
	add_theme_support( 'title-tag' );
	add_theme_support( 'html5', array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' ) );

	register_nav_menus(
		array(
			'primary' => __( 'Primary Menu', 'yourseoagent' ),
		)
	);

	load_theme_textdomain( 'yourseoagent', get_template_directory() . '/languages' );
}
add_action( 'after_setup_theme', 'ysa_theme_setup' );

/**
 * Flush rewrite rules after theme switch so /services/* pages resolve.
 */
function ysa_after_switch_theme() {
	ysa_ensure_pages();
	flush_rewrite_rules();
}
add_action( 'after_switch_theme', 'ysa_after_switch_theme' );
