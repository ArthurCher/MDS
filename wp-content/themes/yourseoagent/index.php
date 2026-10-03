<?php
/**
 * Fallback index template.
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <section class="hero">
    <div class="hero-word display"><?php bloginfo( 'name' ); ?></div>
    <div class="hero-sub">
      <p><?php bloginfo( 'description' ); ?></p>
    </div>
  </section>

  <?php if ( have_posts() ) : ?>
    <section>
      <?php
      while ( have_posts() ) :
        the_post();
        ?>
        <article <?php post_class( 'row' ); ?>>
          <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
          <?php the_excerpt(); ?>
        </article>
      <?php endwhile; ?>
    </section>
  <?php endif; ?>
</div>

<?php
get_footer();
