<?php
/**
 * Default page template.
 *
 * @package YourSEOAgent
 */

get_header();
?>

<div class="wrap">
  <?php
  while ( have_posts() ) :
    the_post();
    ?>
    <section class="hero">
      <div class="hero-word display"><?php the_title(); ?></div>
    </section>
    <section>
      <?php the_content(); ?>
    </section>
  <?php endwhile; ?>
</div>

<?php
get_footer();
