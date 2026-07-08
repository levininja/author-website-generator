"""Write the AWG Books custom post type as a WordPress must-use plugin PHP file."""

from pathlib import Path

MU_PLUGIN_SUBPATH = "wp-content/mu-plugins/awg-books.php"

_PHP_CONTENT = """\
<?php
/**
 * AWG Books Custom Post Type
 *
 * Registered as a must-use plugin so WordPress loads it automatically without
 * requiring explicit activation. Custom code stays isolated from WordPress core
 * and third-party plugins so updates never overwrite AWG logic.
 */

add_action( 'init', 'awg_register_books_cpt' );

function awg_register_books_cpt() {
    register_post_type( 'awg_book', array(
        'label'  => 'Books',
        'labels' => array(
            'name'               => 'Books',
            'singular_name'      => 'Book',
            'add_new_item'       => 'Add New Book',
            'edit_item'          => 'Edit Book',
            'view_item'          => 'View Book',
            'search_items'       => 'Search Books',
            'not_found'          => 'No books found',
            'not_found_in_trash' => 'No books found in Trash',
        ),
        'public'       => true,
        'has_archive'  => true,
        'rewrite'      => array( 'slug' => 'books' ),
        'supports'     => array( 'title', 'editor', 'thumbnail' ),
        'show_in_rest' => true,
        'menu_icon'    => 'dashicons-book',
        'menu_position' => 5,
    ) );

    // --- String meta fields ---

    register_post_meta( 'awg_book', '_awg_cover_image', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_genre', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_subgenre', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // Fiction or Nonfiction category from onboarding.
    register_post_meta( 'awg_book', '_awg_category', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_series_name', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_perfect_for', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // Reader-fit copy: the "enjoy if" field from onboarding.
    register_post_meta( 'awg_book', '_awg_enjoy_if', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_sample_chapter_url', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_sample_chapter_name', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // --- Integer meta fields ---

    // One-based position from onboarding; used to order books on the site.
    register_post_meta( 'awg_book', '_awg_onboarding_position', array(
        'type'         => 'integer',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_number_in_series', array(
        'type'         => 'integer',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_series_total_books', array(
        'type'         => 'integer',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // --- Boolean meta fields ---

    register_post_meta( 'awg_book', '_awg_is_standalone', array(
        'type'         => 'boolean',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    register_post_meta( 'awg_book', '_awg_series_is_complete', array(
        'type'         => 'boolean',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // --- JSON collection fields (stored as serialized JSON strings) ---
    // Each collection is a JSON array of objects; stored as a single string
    // value so WordPress meta_query and REST Schema remain straightforward.

    register_post_meta( 'awg_book', '_awg_buy_links', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // Editorial reviews: [{"reviewer_name": str, "credentials": str|null,
    //   "quotation": str, "is_starred_review": bool, "original_review_url": str|null}]
    register_post_meta( 'awg_book', '_awg_editorial_reviews', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // Reader reviews: adds stars, photo_url compared to editorial reviews.
    register_post_meta( 'awg_book', '_awg_reader_reviews', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );

    // Awards: [{"name": str, "icon_url": str}]
    register_post_meta( 'awg_book', '_awg_awards', array(
        'type'         => 'string',
        'single'       => true,
        'show_in_rest' => true,
    ) );
}
"""


def write_books_cpt(site_path: str) -> None:
    """Write the AWG Books CPT mu-plugin PHP file into the generated site.

    Creates wp-content/mu-plugins/ if it does not exist. Safe to call multiple
    times; overwrites the file in place (idempotent).
    """
    plugin_path = Path(site_path) / MU_PLUGIN_SUBPATH
    plugin_path.parent.mkdir(parents=True, exist_ok=True)
    plugin_path.write_text(_PHP_CONTENT)
