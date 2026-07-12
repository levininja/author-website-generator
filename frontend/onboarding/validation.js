import { IMAGE_LIMIT, IMAGE_TYPES, PDF_LIMIT } from "./constants";


export function parseBuyLinks(raw) {
  return (raw || "")
    .split(",")
    .map((link) => link.trim())
    .filter(Boolean);
}


export function validateBuyLinks(raw) {
  const links = parseBuyLinks(raw);
  if (!links.length) return "At least one buy link is required.";
  if (links.some((link) => !normalizeWebUrl(link))) {
    return "Each buy link must contain a valid domain such as example.com.";
  }
  return "";
}


export function normalizeWebUrl(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) return "";
  const candidate = /^[a-z][a-z0-9+.-]*:\/\//i.test(trimmed)
    ? trimmed
    : `https://${trimmed}`;
  try {
    const parsed = new URL(candidate);
    const validProtocol = ["http:", "https:"].includes(parsed.protocol);
    const validHostname = /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i
      .test(parsed.hostname);
    return validProtocol && validHostname ? parsed.href : "";
  } catch {
    return "";
  }
}


export function isHttpUrl(value) {
  return Boolean(normalizeWebUrl(value));
}


export function isBareDomain(value) {
  return /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i.test(value);
}


export function isValidGenreTree(tree) {
  if (!tree || typeof tree !== "object") return false;
  if (!tree.Fiction || !tree.Nonfiction) return false;
  return Object.values(tree).every(
    (genres) => genres
      && typeof genres === "object"
      && Object.values(genres).every(
        (subgenres) => Array.isArray(subgenres) && subgenres.length > 0,
      ),
  );
}


export function validateImage(file, label) {
  if (!(file instanceof File)) return `${label} is required.`;
  if (!IMAGE_TYPES.includes(file.type)) return `${label} must be a JPG, PNG, or WebP image.`;
  if (file.size > IMAGE_LIMIT) return `${label} must be 10 MB or smaller.`;
  return "";
}


export function validateOptionalImage(file, label) {
  return file ? validateImage(file, label) : "";
}


export function validatePdf(file) {
  if (!file) return "";
  if (file.type !== "application/pdf") return "Sample chapters must be PDF files.";
  if (file.size > PDF_LIMIT) return "Sample chapter PDFs must be 20 MB or smaller.";
  return "";
}


export function validateSimpleStep(step, answers) {
  const value = String(answers[step.id] || "").trim();
  if (step.required && !value) return `${step.label} is required.`;
  if (!value) return "";
  if (step.id === "author_email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    return "Enter a valid email address.";
  }
  if (step.id === "site_domain" && !isBareDomain(value)) {
    return "Enter a bare domain such as janedoe.com, without https:// or a path.";
  }
  return "";
}


export function validateBooks(books, genreTree) {
  if (!books.length) return "Add at least one book.";
  for (let index = 0; index < books.length; index += 1) {
    const book = books[index];
    const prefix = `Complete Book ${index + 1}:`;
    if (!book.title.trim()) return `${prefix} title is required.`;
    const coverError = validateImage(book.cover_image, "Cover image");
    if (coverError) return `${prefix} ${coverError}`;
    if (!book.description.trim()) return `${prefix} description is required.`;
    const buyLinksError = validateBuyLinks(book.buy_links);
    if (buyLinksError) return `${prefix} ${buyLinksError}`;
    if (!book.category || !book.genre) {
      return `${prefix} category and genre are required.`;
    }
    if (
      !genreTree?.[book.category]?.[book.genre]
      || (
        book.subgenre
        && !genreTree[book.category][book.genre].includes(book.subgenre)
      )
    ) {
      return `${prefix} select a valid category, genre, and subgenre.`;
    }
    if (!["standalone", "series"].includes(book.series_type)) {
      return `${prefix} select standalone or series.`;
    }
    if (book.series_type === "series") {
      const number = Number(book.book_number);
      const total = Number(book.series_length);
      if (!book.series_name.trim() || !number || !total) {
        return `${prefix} series name, book number, and total books are required.`;
      }
      if (number > total) return `${prefix} book number cannot exceed total books.`;
    }
    for (const [label, reviews] of [
      ["editorial", book.editorial_reviews],
      ["other", book.other_reviews],
    ]) {
      for (const review of reviews) {
        if (!review.reviewer_name.trim() || !review.quotation.trim()) {
          return `${prefix} complete every ${label} review.`;
        }
        if (
          review.original_review_url.trim()
          && !isHttpUrl(review.original_review_url.trim())
        ) {
          return `${prefix} review URLs must contain a valid public domain.`;
        }
        const photoError = validateOptionalImage(review.photo, "Reviewer photo");
        if (photoError) return `${prefix} ${photoError}`;
      }
    }
    for (const award of book.awards) {
      if (!award.name.trim()) return `${prefix} award name is required.`;
      const iconError = validateOptionalImage(award.icon, "Award icon");
      if (iconError || !award.icon) return `${prefix} ${iconError || "Award icon is required."}`;
    }
    const pdfError = validatePdf(book.sample_chapter);
    if (pdfError) return `${prefix} ${pdfError}`;
  }
  return "";
}
