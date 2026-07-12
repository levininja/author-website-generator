import { SOCIAL_FIELDS } from "./constants";
import { normalizeWebUrl, parseBuyLinks } from "./validation";


export function buildPayload(answers, books) {
  const payload = {
    author_name: answers.author_name.trim(),
    author_email: answers.author_email.trim(),
    site_domain: answers.site_domain.trim().toLowerCase(),
    genres: answers.genres,
    books: books.map((book, bookIndex) => {
      const entry = {
        title: book.title.trim(),
        cover_image_key: `book_${bookIndex}_cover_image`,
        description: book.description.trim(),
        buy_links: parseBuyLinks(book.buy_links).map(normalizeWebUrl),
        category: book.category,
        genre: book.genre,
        ...(book.subgenre ? { subgenre: book.subgenre } : {}),
        series_type: book.series_type,
        editorial_reviews: book.editorial_reviews.map((review, reviewIndex) => ({
          reviewer_name: review.reviewer_name.trim(),
          quotation: review.quotation.trim(),
          ...(review.original_review_url.trim()
            ? { original_review_url: normalizeWebUrl(review.original_review_url) }
            : {}),
          ...(review.stars ? { stars: Number(review.stars) } : {}),
          is_starred_review: Boolean(review.is_starred_review),
          ...(review.photo
            ? { photo_key: `book_${bookIndex}_editorial_review_${reviewIndex}_photo` }
            : {}),
        })),
        other_reviews: book.other_reviews.map((review, reviewIndex) => ({
          reviewer_name: review.reviewer_name.trim(),
          quotation: review.quotation.trim(),
          ...(review.credentials.trim()
            ? { credentials: review.credentials.trim() }
            : {}),
          ...(review.original_review_url.trim()
            ? { original_review_url: normalizeWebUrl(review.original_review_url) }
            : {}),
          ...(review.stars ? { stars: Number(review.stars) } : {}),
          is_starred_review: Boolean(review.is_starred_review),
          ...(review.photo
            ? { photo_key: `book_${bookIndex}_other_review_${reviewIndex}_photo` }
            : {}),
        })),
        awards: book.awards.map((award, awardIndex) => ({
          name: award.name.trim(),
          icon_key: `book_${bookIndex}_award_${awardIndex}_icon`,
        })),
      };
      if (book.series_type === "series") {
        entry.series_name = book.series_name.trim();
        entry.book_number = Number(book.book_number);
        entry.series_length = Number(book.series_length);
        entry.series_is_complete = book.series_is_complete;
      }
      if (book.perfect_for.trim()) entry.perfect_for = book.perfect_for.trim();
      if (book.enjoy_if.trim()) entry.enjoy_if = book.enjoy_if.trim();
      if (book.sample_chapter) {
        entry.sample_chapter_key = `book_${bookIndex}_sample_chapter`;
      }
      return entry;
    }),
  };

  [
    "site_tagline",
    "author_bio_short",
    "author_bio_long",
    "primary_color",
    "secondary_color",
    "newsletter_link",
  ].forEach((field) => {
    const value = String(answers[field] || "").trim();
    if (value) {
      payload[field] = field === "newsletter_link" && value.includes(".")
        ? normalizeWebUrl(value)
        : value;
    }
  });

  if (answers.author_headshot) {
    payload.author_headshot_key = "author_headshot";
  }

  if (answers.selected_template) {
    payload.selected_template = answers.selected_template;
  }

  const socialLinks = {};
  SOCIAL_FIELDS.forEach(([answerField, payloadField]) => {
    const value = String(answers[answerField] || "").trim();
    if (value) socialLinks[payloadField] = normalizeWebUrl(value);
  });
  if (Object.keys(socialLinks).length) payload.social_links = socialLinks;
  return payload;
}


export function buildSubmission(answers, books, replaceAuthorId = "") {
  const data = new FormData();
  data.append("payload", JSON.stringify(buildPayload(answers, books)));
  if (replaceAuthorId) {
    data.append("replace_author_id", replaceAuthorId);
  }
  if (answers.author_headshot) {
    data.append("author_headshot", answers.author_headshot);
  }
  books.forEach((book, bookIndex) => {
    data.append(`book_${bookIndex}_cover_image`, book.cover_image);
    book.editorial_reviews.forEach((review, reviewIndex) => {
      if (review.photo) {
        data.append(
          `book_${bookIndex}_editorial_review_${reviewIndex}_photo`,
          review.photo,
        );
      }
    });
    book.other_reviews.forEach((review, reviewIndex) => {
      if (review.photo) {
        data.append(
          `book_${bookIndex}_other_review_${reviewIndex}_photo`,
          review.photo,
        );
      }
    });
    book.awards.forEach((award, awardIndex) => {
      data.append(`book_${bookIndex}_award_${awardIndex}_icon`, award.icon);
    });
    if (book.sample_chapter) {
      data.append(`book_${bookIndex}_sample_chapter`, book.sample_chapter);
    }
  });
  return data;
}
