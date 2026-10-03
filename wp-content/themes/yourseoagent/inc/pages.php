<?php
/**
 * Creates required pages on theme activation.
 *
 * @package YourSEOAgent
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Ensures all marketing pages exist with correct templates and hierarchy.
 */
function ysa_ensure_pages() {
	$services_id = ysa_upsert_page(
		array(
			'title'    => 'Услуги',
			'slug'     => 'services',
			'content'  => '',
			'template' => 'page-templates/template-services.php',
			'parent'   => 0,
			'status'   => 'publish',
		)
	);

	$pages = array(
		array(
			'title'       => 'Главная',
			'slug'        => 'home',
			'content'     => '',
			'template'    => '',
			'parent'      => 0,
			'is_front'    => true,
			'description' => 'SEO Team Lead с 14-летним опытом: технический аудит, GEO/AISEO, SEO для iGaming/Betting, СНГ/Яндекс и внедрение собственного AI SEO-агента.',
		),
		array(
			'title'       => 'Контакты',
			'slug'        => 'contacts',
			'content'     => '',
			'template'    => 'page-templates/template-contacts.php',
			'parent'      => 0,
			'description' => 'Контакты для связи: Telegram, WhatsApp, телефон, почта.',
		),
		array(
			'title'       => 'AI SEO-агент',
			'slug'        => 'ai-agent',
			'content'     => '',
			'template'    => 'page-templates/template-ai-agent.php',
			'parent'      => $services_id,
			'description' => 'Кастомный AI-агент на MCP-стеке над GSC, Метрикой, Topvisor, Ahrefs: диагностика падений трафика, поиск точек роста, автоматическая отчетность.',
		),
		array(
			'title'       => 'Betting/Gaming',
			'slug'        => 'betting-gaming',
			'content'     => '',
			'template'    => 'page-templates/template-betting-gaming.php',
			'parent'      => $services_id,
			'description' => 'SEO для iGaming: аудит линкбилдинга (включая PBN), техаудит, мультигео/мультиязычность, план роста трафика с учетом блокировок и зеркал доменов.',
		),
		array(
			'title'       => 'Технический аудит',
			'slug'        => 'tehnicheskiy-audit',
			'content'     => '',
			'template'    => 'page-templates/template-tehnicheskiy-audit.php',
			'parent'      => $services_id,
			'description' => 'Технический SEO-аудит: индексация, скорость, дубли, разметка, семантика, разбор конкурентов и приоритизированный план на 30/60/90 дней.',
		),
		array(
			'title'       => 'GEO/AISEO',
			'slug'        => 'geo-aiseo',
			'content'     => '',
			'template'    => 'page-templates/template-geo-aiseo.php',
			'parent'      => $services_id,
			'description' => 'Проверка видимости бренда в ChatGPT, Perplexity, Google AI Overview, Яндекс.Алисе. Аудит E-E-A-T, Schema.org, приоритетный план внедрения P0–P3.',
		),
		array(
			'title'       => 'СНГ/Яндекс',
			'slug'        => 'sng-yandex',
			'content'     => '',
			'template'    => 'page-templates/template-sng-yandex.php',
			'parent'      => $services_id,
			'description' => 'Аудит по требованиям Яндекса: поведенческие факторы, ИКС, региональность. Сверка расхождений в ранжировании Яндекс vs Google, план внедрения.',
		),
	);

	$front_id = 0;

	foreach ( $pages as $page ) {
		$page_id = ysa_upsert_page( $page );
		if ( ! empty( $page['description'] ) ) {
			update_post_meta( $page_id, '_ysa_meta_description', $page['description'] );
		}
		if ( ! empty( $page['is_front'] ) ) {
			$front_id = $page_id;
		}
	}

	if ( $front_id ) {
		update_option( 'show_on_front', 'page' );
		update_option( 'page_on_front', $front_id );
	}

	update_option( 'ysa_pages_version', YSA_THEME_VERSION );
}

/**
 * Creates or updates a page by slug/parent.
 *
 * @param array $args Page arguments.
 * @return int Page ID.
 */
function ysa_upsert_page( $args ) {
	$parent = isset( $args['parent'] ) ? (int) $args['parent'] : 0;
	$slug   = $args['slug'];

	$path = $parent ? get_page_uri( $parent ) . '/' . $slug : $slug;
	$existing = get_page_by_path( $path );

	$postarr = array(
		'post_title'   => $args['title'],
		'post_name'    => $slug,
		'post_content' => isset( $args['content'] ) ? $args['content'] : '',
		'post_status'  => isset( $args['status'] ) ? $args['status'] : 'publish',
		'post_type'    => 'page',
		'post_parent'  => $parent,
	);

	if ( $existing ) {
		$postarr['ID'] = $existing->ID;
		$page_id       = wp_update_post( $postarr, true );
	} else {
		$page_id = wp_insert_post( $postarr, true );
	}

	if ( is_wp_error( $page_id ) ) {
		return 0;
	}

	if ( ! empty( $args['template'] ) ) {
		update_post_meta( $page_id, '_wp_page_template', $args['template'] );
	}

	return (int) $page_id;
}

/**
 * Re-run page bootstrap if theme was updated.
 */
function ysa_maybe_ensure_pages() {
	if ( get_option( 'ysa_pages_version' ) !== YSA_THEME_VERSION ) {
		ysa_ensure_pages();
	}
}
add_action( 'init', 'ysa_maybe_ensure_pages', 20 );

/**
 * Admin notice with setup tip after activation.
 */
function ysa_admin_notice_permalinks() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$structure = get_option( 'permalink_structure' );
	if ( $structure ) {
		return;
	}
	echo '<div class="notice notice-warning"><p>';
	echo esc_html__( 'YourSEOAgent: включите постоянные ссылки (Настройки → Постоянные ссылки → «Название записи»), чтобы URL вида /services/ai-agent/ работали как на yourseoagent.pro.', 'yourseoagent' );
	echo '</p></div>';
}
add_action( 'admin_notices', 'ysa_admin_notice_permalinks' );
