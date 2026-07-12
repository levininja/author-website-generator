export const IMAGE_LIMIT = 10 * 1024 * 1024;
export const PDF_LIMIT = 20 * 1024 * 1024;
export const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];


export const STEPS = [
  {
    id: "author_name",
    label: "Author name",
    title: "What is your author name?",
    help: "Enter it exactly as you want readers to see it.",
    required: true,
    autocomplete: "name",
  },
  {
    id: "author_email",
    label: "Contact email",
    title: "What email should reader messages go to?",
    help: "Messages submitted through your website’s contact form will be sent to this email.",
    required: true,
    autocomplete: "email",
  },
  {
    id: "site_domain",
    label: "Site domain",
    title: "What is your site domain?",
    help: "This should be a domain name (such as www.georgemartin.com) you have already purchased through a DNS provider such as GoDaddy or Namecheap. If you have not purchased a domain name yet, just enter in your aspirational domain name and we can figure it out later.",
    required: true,
    placeholder: "janedoe.com",
  },
  {
    id: "site_tagline",
    label: "Site tagline",
    title: "Would you like a site tagline?",
    help: "A short author one-liner, such as “Heart-pounding thrillers after dark.”",
  },
  {
    id: "author_bio_short",
    label: "Author short bio",
    title: "What is your short bio?",
    help: "A concise paragraph for the new site’s About section.",
    multiline: true,
  },
  {
    id: "author_bio_long",
    label: "Author long bio",
    title: "Would you like to add a longer bio?",
    help: "Use this for a future full About page.",
    multiline: true,
  },
  {
    id: "author_headshot",
    label: "Author photo",
    title: "Would you like to add a photo for your About section?",
    help: "JPG, PNG, or WebP; maximum 10 MB.",
    type: "headshot",
  },
  {
    id: "genres",
    title: "What genres do you write?",
    help: "Start typing to find broad or specific genres, then select every one that applies.",
    required: true,
    type: "genres",
  },
  {
    id: "brand_colors",
    title: "Choose your brand colors",
    help: "Choose a primary and secondary color for your new website.",
    type: "colors",
  },
  {
    id: "selected_template",
    title: "Website Templates",
    help: "Your site will be built on the Classic template.",
    type: "template",
  },
  {
    id: "books",
    title: "Tell us about your books",
    help: "At least one complete book is required.",
    required: true,
    type: "books",
  },
  {
    id: "newsletter_link",
    label: "Newsletter signup link or Kit form ID",
    title: "How should readers join your newsletter?",
    help: "Enter a signup URL or a Kit form ID.",
  },
  {
    id: "social_links",
    title: "Where can readers follow you?",
    help: "Add any social profiles you want displayed. All are optional.",
    type: "socials",
  },
  {
    id: "review",
    title: "Review your new website details",
  },
];

export const EMPTY_ANSWERS = {
  author_name: "",
  author_email: "",
  site_domain: "",
  site_tagline: "",
  author_bio_short: "",
  author_bio_long: "",
  author_headshot: null,
  genres: [],
  primary_color: "#2563eb",
  secondary_color: "#64748b",
  selected_template: "Classic",
  newsletter_link: "",
  social_twitter: "",
  social_instagram: "",
  social_facebook: "",
  social_tiktok: "",
  social_youtube: "",
  social_goodreads: "",
};

export const SOCIAL_FIELDS = [
  ["social_twitter", "twitter", "Twitter / X"],
  ["social_instagram", "instagram", "Instagram"],
  ["social_facebook", "facebook", "Facebook"],
  ["social_tiktok", "tiktok", "TikTok"],
  ["social_youtube", "youtube", "YouTube"],
  ["social_goodreads", "goodreads", "Goodreads"],
];


export function emptyBook() {
  return {
    title: "",
    cover_image: null,
    description: "",
    buy_links: "",
    category: "",
    genre: "",
    subgenre: "",
    series_type: "standalone",
    series_name: "",
    book_number: "",
    series_length: "",
    series_is_complete: false,
    editorial_reviews: [],
    other_reviews: [],
    awards: [],
    perfect_for: "",
    enjoy_if: "",
    sample_chapter: null,
  };
}
