import { useEffect, useMemo, useRef, useState } from "react";


const IMAGE_LIMIT = 10 * 1024 * 1024;
const PDF_LIMIT = 20 * 1024 * 1024;
const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];

const STEPS = [
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

const EMPTY_ANSWERS = {
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
  newsletter_link: "",
  social_twitter: "",
  social_instagram: "",
  social_facebook: "",
  social_tiktok: "",
  social_youtube: "",
  social_goodreads: "",
};

const SOCIAL_FIELDS = [
  ["social_twitter", "twitter", "Twitter / X"],
  ["social_instagram", "instagram", "Instagram"],
  ["social_facebook", "facebook", "Facebook"],
  ["social_tiktok", "tiktok", "TikTok"],
  ["social_youtube", "youtube", "YouTube"],
  ["social_goodreads", "goodreads", "Goodreads"],
];


function emptyBook() {
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


function parseBuyLinks(raw) {
  return (raw || "")
    .split(",")
    .map((link) => link.trim())
    .filter(Boolean);
}


function validateBuyLinks(raw) {
  const links = parseBuyLinks(raw);
  if (!links.length) return "At least one buy link is required.";
  if (links.some((link) => !normalizeWebUrl(link))) {
    return "Each buy link must contain a valid domain such as example.com.";
  }
  return "";
}


function normalizeWebUrl(value) {
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


function isHttpUrl(value) {
  return Boolean(normalizeWebUrl(value));
}


function isBareDomain(value) {
  return /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i.test(value);
}


function isValidGenreTree(tree) {
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


function validateImage(file, label) {
  if (!(file instanceof File)) return `${label} is required.`;
  if (!IMAGE_TYPES.includes(file.type)) return `${label} must be a JPG, PNG, or WebP image.`;
  if (file.size > IMAGE_LIMIT) return `${label} must be 10 MB or smaller.`;
  return "";
}


function validateOptionalImage(file, label) {
  return file ? validateImage(file, label) : "";
}


function validatePdf(file) {
  if (!file) return "";
  if (file.type !== "application/pdf") return "Sample chapters must be PDF files.";
  if (file.size > PDF_LIMIT) return "Sample chapter PDFs must be 20 MB or smaller.";
  return "";
}


function validateSimpleStep(step, answers) {
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


function validateBooks(books, genreTree) {
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


function buildPayload(answers, books) {
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

  const socialLinks = {};
  SOCIAL_FIELDS.forEach(([answerField, payloadField]) => {
    const value = String(answers[answerField] || "").trim();
    if (value) socialLinks[payloadField] = normalizeWebUrl(value);
  });
  if (Object.keys(socialLinks).length) payload.social_links = socialLinks;
  return payload;
}


function buildSubmission(answers, books, replaceAuthorId = "") {
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


function flattenGenreOptions(genreTree) {
  const options = [];
  const seen = new Set();

  function add(value, path, level) {
    if (seen.has(value)) return;
    seen.add(value);
    options.push({ value, label: value, path, level });
  }

  Object.entries(genreTree || {}).forEach(([category, genres]) => {
    add(category, category, "Category");
    Object.entries(genres).forEach(([genre, subgenres]) => {
      add(genre, `${category} › ${genre}`, "Genre");
      subgenres.forEach((subgenre) => {
        add(
          subgenre,
          `${category} › ${genre} › ${subgenre}`,
          "Subgenre",
        );
      });
    });
  });
  return options;
}


function searchGenreOptions(options, rawQuery, limit = 8) {
  const query = rawQuery.trim().toLowerCase();
  if (query.length < 2) return [];

  return options
    .map((option) => {
      const label = option.label.toLowerCase();
      const path = option.path.toLowerCase();
      let score = Number.POSITIVE_INFINITY;
      if (label.startsWith(query)) score = 0;
      else if (label.split(/\s+/).some((word) => word.startsWith(query))) score = 1;
      else if (label.includes(query)) score = 2;
      else if (path.includes(query)) score = 3;
      return { option, score };
    })
    .filter(({ score }) => Number.isFinite(score))
    .sort((left, right) => (
      left.score - right.score
      || left.option.label.localeCompare(right.option.label)
      || left.option.path.localeCompare(right.option.path)
    ))
    .slice(0, limit)
    .map(({ option }) => option);
}


function GenreStep({ selected, genreTree, error, onChange }) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef(null);
  const options = useMemo(() => flattenGenreOptions(genreTree), [genreTree]);
  const matches = useMemo(
    () => searchGenreOptions(
      options.filter((option) => !selected.includes(option.value)),
      query,
    ),
    [options, query, selected],
  );

  if (error || !genreTree) {
    return <p className="configuration-error" role="alert">{error || "Loading genre catalog…"}</p>;
  }

  function select(option) {
    if (!selected.includes(option.value)) {
      onChange([...selected, option.value]);
    }
    setQuery("");
    setIsOpen(false);
    setActiveIndex(0);
  }

  function remove(value) {
    onChange(selected.filter((item) => item !== value));
  }

  function handleKeyDown(event) {
    if (event.key === "ArrowDown" && matches.length) {
      event.preventDefault();
      setIsOpen(true);
      setActiveIndex((current) => Math.min(current + 1, matches.length - 1));
    } else if (event.key === "ArrowUp" && matches.length) {
      event.preventDefault();
      setIsOpen(true);
      setActiveIndex((current) => Math.max(current - 1, 0));
    } else if (event.key === "Enter" && isOpen && matches[activeIndex]) {
      event.preventDefault();
      select(matches[activeIndex]);
    } else if (event.key === "Escape") {
      setIsOpen(false);
    }
  }

  return (
    <div
      className="genre-autocomplete"
      ref={containerRef}
      onBlur={(event) => {
        if (!containerRef.current?.contains(event.relatedTarget)) {
          setIsOpen(false);
        }
      }}
    >
      {selected.length > 0 && (
        <div className="genre-chips" aria-label="Selected genres">
          {selected.map((genre) => (
            <span className="genre-chip" key={genre}>
              {genre}
              <button
                type="button"
                data-testid={`remove-genre-${genre.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}`}
                onClick={() => remove(genre)}
                aria-label={`Remove ${genre}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <label htmlFor="genre-search">Search genres</label>
      <input
        id="genre-search"
        data-testid="genre-search"
        type="search"
        role="combobox"
        autoComplete="off"
        value={query}
        placeholder="Start typing, such as cyberpunk or memoir"
        aria-autocomplete="list"
        aria-expanded={isOpen && query.trim().length >= 2}
        aria-controls="genre-suggestions"
        aria-activedescendant={
          isOpen && matches[activeIndex]
            ? `genre-option-${activeIndex}`
            : undefined
        }
        onChange={(event) => {
          const value = event.target.value;
          setQuery(value);
          setActiveIndex(0);
          setIsOpen(value.trim().length >= 2);
        }}
        onFocus={() => {
          if (query.trim().length >= 2) setIsOpen(true);
        }}
        onKeyDown={handleKeyDown}
      />
      <p className="field-hint">Type at least two characters. Select as many as apply.</p>

      {isOpen && query.trim().length >= 2 && (
        <div className="genre-suggestion-panel">
          {matches.length > 0 ? (
            <div id="genre-suggestions" className="genre-suggestions" role="listbox">
              {matches.map((option, index) => (
                <button
                  id={`genre-option-${index}`}
                  data-testid={`genre-option-${index}`}
                  type="button"
                  role="option"
                  aria-label={`${option.path} — ${option.level}`}
                  aria-selected={index === activeIndex}
                  className={`genre-suggestion${index === activeIndex ? " is-active" : ""}`}
                  key={`${option.path}-${option.value}`}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => select(option)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <span>{option.label}</span>
                  <small>{option.path} · {option.level}</small>
                </button>
              ))}
            </div>
          ) : (
            <p className="genre-no-results">No matching genres found.</p>
          )}
        </div>
      )}
    </div>
  );
}


function ColorField({ id, label, value, onChange }) {
  return (
    <div className="color-field">
      <div
        className="color-preview"
        data-testid={`${id}-color-preview`}
        style={{ backgroundColor: value }}
        aria-hidden="true"
      />
      <div className="color-controls">
        <label htmlFor={`${id}-picker`}>{label}</label>
        <div className="color-control-row">
          <input
            id={`${id}-picker`}
            data-testid={`${id}-color-picker`}
            type="color"
            value={value}
            onChange={(event) => onChange(event.target.value)}
          />
          <input
            aria-label={`${label} hex value`}
            data-testid={`${id}-color-hex`}
            type="text"
            value={value}
            pattern="^#[0-9a-fA-F]{6}$"
            onChange={(event) => {
              if (/^#[0-9a-fA-F]{6}$/.test(event.target.value)) {
                onChange(event.target.value);
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}


function SocialStep({ answers, onChange }) {
  return (
    <div className="social-grid">
      {SOCIAL_FIELDS.map(([field, , label]) => (
        <div className="field-stack" key={field}>
          <label htmlFor={field}>{label}</label>
          <input
            id={field}
            data-testid={field}
            type="url"
            value={answers[field]}
            placeholder={`https://${field === "social_twitter" ? "x.com" : `${label.toLowerCase()}.com`}/…`}
            onChange={(event) => onChange(field, event.target.value)}
          />
        </div>
      ))}
    </div>
  );
}


function HeadshotStep({ value, onChange }) {
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!(value instanceof File)) {
      setPreviewUrl("");
      return undefined;
    }

    const objectUrl = URL.createObjectURL(value);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [value]);

  return (
    <div className="field-stack">
      <label htmlFor="author-headshot">
        Author photo
        <span className="optional-label"> Optional</span>
      </label>
      <input
        id="author-headshot"
        data-testid="author-headshot"
        type="file"
        accept={IMAGE_TYPES.join(",")}
        onChange={(e) => onChange(e.target.files[0] || null)}
      />
      <span className="field-hint">JPG, PNG, or WebP; maximum 10 MB.</span>
      {previewUrl && (
        <div className="selected-image" role="status">
          <img src={previewUrl} alt="Selected author photo preview" />
          <div className="selected-image-copy">
            <strong><span aria-hidden="true">✓</span> Photo selected</strong>
            <span>{value.name}</span>
          </div>
        </div>
      )}
    </div>
  );
}


function Repeater({
  title,
  buttonLabel,
  testIdPrefix,
  items,
  emptyItem,
  onChange,
  renderItem,
}) {
  function add() {
    onChange([...items, { ...emptyItem }]);
  }
  function update(index, field, value) {
    onChange(items.map((item, itemIndex) => (
      itemIndex === index ? { ...item, [field]: value } : item
    )));
  }
  function remove(index) {
    onChange(items.filter((_, itemIndex) => itemIndex !== index));
  }

  return (
    <section className="nested-section">
      <h3>{title}</h3>
      {items.map((item, index) => (
        <fieldset className="nested-item" key={index}>
          <legend>{title.replace(/s$/, "")} {index + 1}</legend>
          {renderItem(item, index, update)}
          <button
            type="button"
            className="button-link danger-link"
            data-testid={`${testIdPrefix}-${index}-remove`}
            onClick={() => remove(index)}
          >
            Remove
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        className="button-secondary compact-button"
        data-testid={`${testIdPrefix}-add`}
        onClick={add}
      >
        + {buttonLabel}
      </button>
    </section>
  );
}


function BookEntry({
  book,
  index,
  genreTree,
  canRemove,
  showValidationErrors,
  onChange,
  onRemove,
}) {
  const [buyLinksTouched, setBuyLinksTouched] = useState(false);
  const prefix = `book-${index}`;
  const buyLinksError = buyLinksTouched || showValidationErrors
    ? validateBuyLinks(book.buy_links)
    : "";
  const genres = book.category ? Object.keys(genreTree?.[book.category] || {}) : [];
  const subgenres = book.category && book.genre
    ? genreTree?.[book.category]?.[book.genre] || []
    : [];

  function update(field, value) {
    onChange({ ...book, [field]: value });
  }

  return (
    <fieldset className="book-entry" aria-label={`Book ${index + 1}`}>
      <legend>Book {index + 1}</legend>
      {canRemove && (
        <button
          type="button"
          className="button-link danger-link book-remove"
          data-testid={`${prefix}-remove`}
          onClick={onRemove}
          aria-label={`Remove book ${index + 1}`}
        >
          Remove book
        </button>
      )}

      <div className="book-core-grid">
        <div className="field-stack">
          <label htmlFor={`${prefix}-title`}>Title</label>
          <input id={`${prefix}-title`} data-testid={`${prefix}-title`} required value={book.title} onChange={(e) => update("title", e.target.value)} />
        </div>
        <div className="field-stack">
          <label htmlFor={`${prefix}-cover`}>Cover image</label>
          <input
            id={`${prefix}-cover`}
            data-testid={`${prefix}-cover`}
            type="file"
            required
            accept={IMAGE_TYPES.join(",")}
            onChange={(e) => update("cover_image", e.target.files[0] || null)}
          />
          <span className="field-hint">JPG, PNG, or WebP; maximum 10 MB.</span>
        </div>
        <div className="field-stack full-width">
          <label htmlFor={`${prefix}-description`}>Description</label>
          <textarea id={`${prefix}-description`} data-testid={`${prefix}-description`} required rows={4} value={book.description} onChange={(e) => update("description", e.target.value)} />
        </div>
        <div className="field-stack full-width">
          <label htmlFor={`${prefix}-links`}>Buy links</label>
          <input
            id={`${prefix}-links`}
            data-testid={`${prefix}-links`}
            required
            value={book.buy_links}
            placeholder="For example, amazon.com/book, barnesandnoble.com/book"
            aria-invalid={Boolean(buyLinksError)}
            aria-describedby={buyLinksError ? `${prefix}-links-error` : undefined}
            onBlur={() => setBuyLinksTouched(true)}
            onChange={(e) => update("buy_links", e.target.value)}
          />
          {buyLinksError && (
            <p
              id={`${prefix}-links-error`}
              className="field-error book-field-error"
              role="alert"
            >
              {buyLinksError}
            </p>
          )}
        </div>
        <div className="book-classification-row full-width">
          <div className="field-stack">
            <label htmlFor={`${prefix}-category`}>Category</label>
            <select
              id={`${prefix}-category`}
              data-testid={`${prefix}-category`}
              required
              value={book.category}
              onChange={(e) => onChange({
                ...book,
                category: e.target.value,
                genre: "",
                subgenre: "",
              })}
            >
              <option value="">Select category</option>
              {Object.keys(genreTree || {}).map((category) => <option key={category}>{category}</option>)}
            </select>
          </div>
          <div className="field-stack">
            <label htmlFor={`${prefix}-genre`}>Genre</label>
            <select
              id={`${prefix}-genre`}
              data-testid={`${prefix}-genre`}
              required
              value={book.genre}
              disabled={!book.category}
              onChange={(e) => onChange({ ...book, genre: e.target.value, subgenre: "" })}
            >
              <option value="">Select genre</option>
              {genres.map((genre) => <option key={genre}>{genre}</option>)}
            </select>
          </div>
          <div className="field-stack">
            <label htmlFor={`${prefix}-subgenre`}>
              Subgenre <span className="optional-label">(optional)</span>
            </label>
            <select id={`${prefix}-subgenre`} data-testid={`${prefix}-subgenre`} value={book.subgenre} disabled={!book.genre} onChange={(e) => update("subgenre", e.target.value)}>
              <option value="">Select subgenre</option>
              {subgenres.map((subgenre) => <option key={subgenre}>{subgenre}</option>)}
            </select>
          </div>
          <div className="book-classification-spacer" aria-hidden="true" />
        </div>
        <div className="field-stack full-width">
          <label htmlFor={`${prefix}-series-type`}>
            <input
              id={`${prefix}-series-type`}
              data-testid={`${prefix}-series-type`}
              type="checkbox"
              checked={book.series_type === "series"}
              onChange={(e) => update(
                "series_type",
                e.target.checked ? "series" : "standalone",
              )}
            />
            Part of a series
          </label>
        </div>
        {book.series_type === "series" && (
          <>
            <div className="field-stack">
              <label htmlFor={`${prefix}-series-name`}>Series name</label>
              <input id={`${prefix}-series-name`} data-testid={`${prefix}-series-name`} required value={book.series_name} onChange={(e) => update("series_name", e.target.value)} />
            </div>
            <div className="field-stack">
              <label htmlFor={`${prefix}-book-number`}>Book number</label>
              <input id={`${prefix}-book-number`} data-testid={`${prefix}-book-number`} type="number" min="1" required value={book.book_number} onChange={(e) => update("book_number", e.target.value)} />
            </div>
            <div className="field-stack">
              <label htmlFor={`${prefix}-series-length`}>Total books</label>
              <input id={`${prefix}-series-length`} data-testid={`${prefix}-series-length`} type="number" min="1" required value={book.series_length} onChange={(e) => update("series_length", e.target.value)} />
            </div>
            <div className="field-stack">
              <label htmlFor={`${prefix}-series-complete`}>
                <input
                  id={`${prefix}-series-complete`}
                  data-testid={`${prefix}-series-complete`}
                  type="checkbox"
                  checked={book.series_is_complete}
                  onChange={(e) => update("series_is_complete", e.target.checked)}
                />
                Series is complete
              </label>
            </div>
          </>
        )}
      </div>

      <div className="book-optional-heading">
        <h2>Optional book details</h2>
        <p>Add as many of these items as apply.</p>
      </div>

      <Repeater
        title="Editorial reviews"
        buttonLabel="Add editorial review"
        testIdPrefix={`${prefix}-editorial`}
        items={book.editorial_reviews}
        emptyItem={{
          reviewer_name: "",
          quotation: "",
          original_review_url: "",
          photo: null,
          stars: "",
          is_starred_review: false,
        }}
        onChange={(value) => update("editorial_reviews", value)}
        renderItem={(item, itemIndex, change) => (
          <div className="nested-grid">
            <label htmlFor={`${prefix}-editorial-${itemIndex}-source`}>Publication name</label>
            <input id={`${prefix}-editorial-${itemIndex}-source`} data-testid={`${prefix}-editorial-${itemIndex}-source`} required value={item.reviewer_name} placeholder="For example, Kirkus Reviews" onChange={(e) => change(itemIndex, "reviewer_name", e.target.value)} />
            <label htmlFor={`${prefix}-editorial-${itemIndex}-quote`}>Review quotation</label>
            <textarea id={`${prefix}-editorial-${itemIndex}-quote`} data-testid={`${prefix}-editorial-${itemIndex}-quote`} required value={item.quotation} placeholder="For example, A compelling and masterful novel." onChange={(e) => change(itemIndex, "quotation", e.target.value)} />
            <label htmlFor={`${prefix}-editorial-${itemIndex}-url`}>Review URL (optional)</label>
            <input id={`${prefix}-editorial-${itemIndex}-url`} data-testid={`${prefix}-editorial-${itemIndex}-url`} type="text" value={item.original_review_url} placeholder="For example, kirkusreviews.com/review" onChange={(e) => change(itemIndex, "original_review_url", e.target.value)} />
            <label htmlFor={`${prefix}-editorial-${itemIndex}-photo`}>Review photo (optional)</label>
            <input id={`${prefix}-editorial-${itemIndex}-photo`} data-testid={`${prefix}-editorial-${itemIndex}-photo`} type="file" accept={IMAGE_TYPES.join(",")} onChange={(e) => change(itemIndex, "photo", e.target.files[0] || null)} />
            <label htmlFor={`${prefix}-editorial-${itemIndex}-stars`}>Star rating (optional)</label>
            <select id={`${prefix}-editorial-${itemIndex}-stars`} data-testid={`${prefix}-editorial-${itemIndex}-stars`} value={item.stars} onChange={(e) => change(itemIndex, "stars", e.target.value)}>
              <option value="">No star rating</option>
              {[1, 2, 3, 4, 5].map((stars) => <option key={stars} value={stars}>{stars} star{stars === 1 ? "" : "s"}</option>)}
            </select>
            <label htmlFor={`${prefix}-editorial-${itemIndex}-starred`}>
              <input id={`${prefix}-editorial-${itemIndex}-starred`} data-testid={`${prefix}-editorial-${itemIndex}-starred`} type="checkbox" checked={item.is_starred_review} onChange={(e) => change(itemIndex, "is_starred_review", e.target.checked)} />
              Starred review (optional)
            </label>
          </div>
        )}
      />

      <Repeater
        title="Reader reviews"
        buttonLabel="Add reader review"
        testIdPrefix={`${prefix}-other`}
        items={book.other_reviews}
        emptyItem={{
          reviewer_name: "",
          credentials: "",
          quotation: "",
          original_review_url: "",
          photo: null,
          stars: "",
          is_starred_review: false,
        }}
        onChange={(value) => update("other_reviews", value)}
        renderItem={(item, itemIndex, change) => (
          <div className="nested-grid">
            <label htmlFor={`${prefix}-other-${itemIndex}-name`}>Reviewer name</label>
            <input id={`${prefix}-other-${itemIndex}-name`} data-testid={`${prefix}-other-${itemIndex}-name`} required value={item.reviewer_name} placeholder="For example, Stephen King" onChange={(e) => change(itemIndex, "reviewer_name", e.target.value)} />
            <label htmlFor={`${prefix}-other-${itemIndex}-credentials`}>Reviewer credentials (optional)</label>
            <input id={`${prefix}-other-${itemIndex}-credentials`} data-testid={`${prefix}-other-${itemIndex}-credentials`} value={item.credentials} placeholder="For example, author of The Last Stand" onChange={(e) => change(itemIndex, "credentials", e.target.value)} />
            <label htmlFor={`${prefix}-other-${itemIndex}-quote`}>Review quotation</label>
            <textarea id={`${prefix}-other-${itemIndex}-quote`} data-testid={`${prefix}-other-${itemIndex}-quote`} required value={item.quotation} placeholder="For example, I could not put this book down." onChange={(e) => change(itemIndex, "quotation", e.target.value)} />
            <label htmlFor={`${prefix}-other-${itemIndex}-url`}>Review URL (optional)</label>
            <input id={`${prefix}-other-${itemIndex}-url`} data-testid={`${prefix}-other-${itemIndex}-url`} type="text" value={item.original_review_url} placeholder="For example, goodreads.com/review" onChange={(e) => change(itemIndex, "original_review_url", e.target.value)} />
            <label htmlFor={`${prefix}-other-${itemIndex}-photo`}>Review photo (optional)</label>
            <input id={`${prefix}-other-${itemIndex}-photo`} data-testid={`${prefix}-other-${itemIndex}-photo`} type="file" accept={IMAGE_TYPES.join(",")} onChange={(e) => change(itemIndex, "photo", e.target.files[0] || null)} />
            <label htmlFor={`${prefix}-other-${itemIndex}-stars`}>Star rating (optional)</label>
            <select id={`${prefix}-other-${itemIndex}-stars`} data-testid={`${prefix}-other-${itemIndex}-stars`} value={item.stars} onChange={(e) => change(itemIndex, "stars", e.target.value)}>
              <option value="">No star rating</option>
              {[1, 2, 3, 4, 5].map((stars) => <option key={stars} value={stars}>{stars} star{stars === 1 ? "" : "s"}</option>)}
            </select>
            <label htmlFor={`${prefix}-other-${itemIndex}-starred`}>
              <input id={`${prefix}-other-${itemIndex}-starred`} data-testid={`${prefix}-other-${itemIndex}-starred`} type="checkbox" checked={item.is_starred_review} onChange={(e) => change(itemIndex, "is_starred_review", e.target.checked)} />
              Starred review (optional)
            </label>
          </div>
        )}
      />

      <Repeater
        title="Awards"
        buttonLabel="Add award"
        testIdPrefix={`${prefix}-award`}
        items={book.awards}
        emptyItem={{ name: "", icon: null }}
        onChange={(value) => update("awards", value)}
        renderItem={(item, itemIndex, change) => (
          <div className="nested-grid">
            <label htmlFor={`${prefix}-award-${itemIndex}-name`}>Award name</label>
            <input id={`${prefix}-award-${itemIndex}-name`} data-testid={`${prefix}-award-${itemIndex}-name`} required value={item.name} onChange={(e) => change(itemIndex, "name", e.target.value)} />
            <label htmlFor={`${prefix}-award-${itemIndex}-icon`}>Award icon</label>
            <input id={`${prefix}-award-${itemIndex}-icon`} data-testid={`${prefix}-award-${itemIndex}-icon`} type="file" required accept={IMAGE_TYPES.join(",")} onChange={(e) => change(itemIndex, "icon", e.target.files[0] || null)} />
          </div>
        )}
      />

      <div className="book-core-grid optional-copy-grid">
        <div className="field-stack">
          <label htmlFor={`${prefix}-perfect-for`}>This is perfect for…</label>
          <textarea id={`${prefix}-perfect-for`} data-testid={`${prefix}-perfect-for`} value={book.perfect_for} onChange={(e) => update("perfect_for", e.target.value)} />
        </div>
        <div className="field-stack">
          <label htmlFor={`${prefix}-enjoy-if`}>You’ll enjoy this if…</label>
          <textarea id={`${prefix}-enjoy-if`} data-testid={`${prefix}-enjoy-if`} value={book.enjoy_if} onChange={(e) => update("enjoy_if", e.target.value)} />
        </div>
        <div className="field-stack full-width">
          <label htmlFor={`${prefix}-sample`}>Sample chapter PDF</label>
          <input id={`${prefix}-sample`} data-testid={`${prefix}-sample`} type="file" accept="application/pdf" onChange={(e) => update("sample_chapter", e.target.files[0] || null)} />
          <span className="field-hint">PDF; maximum 20 MB.</span>
        </div>
      </div>
    </fieldset>
  );
}


function BookPortfolioStep({
  books,
  genreTree,
  showValidationErrors,
  onChange,
}) {
  function updateBook(index, value) {
    onChange(books.map((book, bookIndex) => (bookIndex === index ? value : book)));
  }
  function removeBook(index) {
    onChange(books.filter((_, bookIndex) => bookIndex !== index));
  }
  return (
    <div className="book-portfolio">
      {books.map((book, index) => (
        <BookEntry
          key={index}
          book={book}
          index={index}
          genreTree={genreTree}
          canRemove={books.length > 1}
          showValidationErrors={showValidationErrors}
          onChange={(value) => updateBook(index, value)}
          onRemove={() => removeBook(index)}
        />
      ))}
      <button type="button" className="button-secondary book-add" data-testid="book-add" onClick={() => onChange([...books, emptyBook()])}>
        + Add another book
      </button>
    </div>
  );
}


function ReviewField({ label, value }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="review-item">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}


function ColorReviewValue({ label, color }) {
  return (
    <span className="review-color-value">
      <span
        className="review-color-swatch"
        role="img"
        aria-label={`${label} swatch ${color}`}
        style={{ backgroundColor: color }}
      />
      <span>{color}</span>
    </span>
  );
}


function DatabaseReview({ submission }) {
  if (!submission) {
    return <p className="configuration-error">The saved submission could not be loaded.</p>;
  }

  return (
    <div className="database-review">
      <p className="question-help">
        This read-only review was loaded from the saved database record.
      </p>
      <dl className="review-list">
        <ReviewField label="Author name" value={submission.author_name} />
        <ReviewField label="Contact email" value={submission.author_email} />
        <ReviewField label="Site domain" value={submission.site_domain} />
        <ReviewField label="Site tagline" value={submission.site_tagline} />
        <ReviewField label="Author short bio" value={submission.author_bio_short} />
        <ReviewField label="Author long bio" value={submission.author_bio_long} />
        <ReviewField label="Genres" value={(submission.genres || []).join(", ")} />
        <ReviewField
          label="Primary color"
          value={submission.primary_color && (
            <ColorReviewValue label="Primary color" color={submission.primary_color} />
          )}
        />
        <ReviewField
          label="Secondary color"
          value={submission.secondary_color && (
            <ColorReviewValue label="Secondary color" color={submission.secondary_color} />
          )}
        />
        <ReviewField label="Newsletter" value={submission.newsletter_link} />
        {Object.entries(submission.social_links || {}).map(([network, url]) => (
          <ReviewField
            key={network}
            label={network.replaceAll("_", " ")}
            value={(
              <a href={url} data-testid={`review-social-${network}`}>
                {url}
              </a>
            )}
          />
        ))}
      </dl>

      {submission.author_headshot_url && (
        <section className="review-section">
          <h2>Author photo</h2>
          <img
            className="review-image review-headshot"
            src={submission.author_headshot_url}
            alt={`Headshot of ${submission.author_name}`}
          />
        </section>
      )}

      {(submission.books || []).map((book, bookIndex) => {
        const bookHeadingId = `review-book-${bookIndex}-heading`;
        const isSeries = book.series_type === "series";
        return (
        <article
          className="review-book"
          key={`${book.title}-${bookIndex}`}
          aria-labelledby={bookHeadingId}
        >
          <h2 id={bookHeadingId}>{book.title}</h2>
          <div className="review-book-overview">
            <img
              className="review-image review-cover"
              src={book.cover_image_url}
              alt={`Cover for ${book.title}`}
            />
            <dl className="review-list">
              <ReviewField label="Description" value={book.description} />
              <ReviewField label="Category" value={book.category} />
              <ReviewField label="Genre" value={book.genre} />
              <ReviewField
                label="Subgenre"
                value={book.subgenre || "Not provided"}
              />
              <ReviewField
                label="Part of a series"
                value={isSeries ? "Yes" : "No"}
              />
              <ReviewField
                label="Series name"
                value={isSeries ? (book.series_name || "Not provided") : "Not applicable"}
              />
              <ReviewField
                label="Book number"
                value={isSeries ? (book.number_in_series || "Not provided") : "Not applicable"}
              />
              <ReviewField
                label="Total books"
                value={isSeries ? (book.series_length || "Not provided") : "Not applicable"}
              />
              <ReviewField
                label="Series complete"
                value={isSeries ? (book.series_is_complete ? "Yes" : "No") : "Not applicable"}
              />
              <ReviewField
                label="Perfect for"
                value={book.perfect_for || "Not provided"}
              />
              <ReviewField
                label="You'll enjoy this if"
                value={book.enjoy_if || "Not provided"}
              />
              <ReviewField
                label="Sample chapter filename"
                value={book.sample_chapter_name || "Not provided"}
              />
            </dl>
          </div>

          <section className="review-section">
            <h3>Buy links</h3>
            {book.buy_links?.length ? (
              <ul>
                {book.buy_links.map((url, linkIndex) => (
                  <li key={url}>
                    <a
                      href={url}
                      data-testid={`review-book-${bookIndex}-buy-link-${linkIndex}`}
                    >
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            ) : <p>None provided</p>}
          </section>

          <section className="review-section">
            <h3>Editorial reviews</h3>
            {book.editorial_reviews?.length ? book.editorial_reviews.map((review, index) => (
              <div className="review-detail" key={`${review.reviewer_name}-${index}`}>
                <h4>Editorial review {index + 1}</h4>
                <dl className="review-list">
                  <ReviewField label="Publication name" value={review.reviewer_name} />
                  <ReviewField label="Review quotation" value={review.quotation} />
                  <ReviewField
                    label="Review URL"
                    value={review.original_review_url
                      ? (
                        <a
                          href={review.original_review_url}
                          data-testid={`review-book-${bookIndex}-editorial-${index}-url`}
                        >
                          {review.original_review_url}
                        </a>
                      )
                      : "Not provided"}
                  />
                  <ReviewField
                    label="Review photo"
                    value={review.photo_url
                      ? (
                        <img
                          className="review-image review-avatar"
                          src={review.photo_url}
                          alt={`${review.reviewer_name} review`}
                        />
                      )
                      : "Not provided"}
                  />
                  <ReviewField
                    label="Star rating"
                    value={review.stars ? `${review.stars} out of 5 stars` : "Not provided"}
                  />
                  <ReviewField
                    label="Starred review"
                    value={review.is_starred_review ? "Yes" : "No"}
                  />
                </dl>
              </div>
            )) : <p>None provided</p>}
          </section>

          <section className="review-section">
            <h3>Reader reviews</h3>
            {book.other_reviews?.length ? book.other_reviews.map((review, index) => (
              <div className="review-detail" key={`${review.reviewer_name}-${index}`}>
                <h4>Reader review {index + 1}</h4>
                <dl className="review-list">
                  <ReviewField label="Reviewer name" value={review.reviewer_name} />
                  <ReviewField
                    label="Reviewer credentials"
                    value={review.credentials || "Not provided"}
                  />
                  <ReviewField label="Review quotation" value={review.quotation} />
                  <ReviewField
                    label="Review URL"
                    value={review.original_review_url
                      ? (
                        <a
                          href={review.original_review_url}
                          data-testid={`review-book-${bookIndex}-other-${index}-url`}
                        >
                          {review.original_review_url}
                        </a>
                      )
                      : "Not provided"}
                  />
                  <ReviewField
                    label="Review photo"
                    value={review.photo_url
                      ? (
                        <img
                          className="review-image review-avatar"
                          src={review.photo_url}
                          alt={`Reviewer ${review.reviewer_name}`}
                        />
                      )
                      : "Not provided"}
                  />
                  <ReviewField
                    label="Star rating"
                    value={review.stars ? `${review.stars} out of 5 stars` : "Not provided"}
                  />
                  <ReviewField
                    label="Starred review"
                    value={review.is_starred_review ? "Yes" : "No"}
                  />
                </dl>
              </div>
            )) : <p>None provided</p>}
          </section>

          <section className="review-section">
            <h3>Awards</h3>
            {book.awards?.length ? (
              <div className="review-media-grid">
                {book.awards.map((award, index) => (
                  <div className="review-media-item" key={`${award.name}-${index}`}>
                    <img
                      className="review-image review-award"
                      src={award.icon_url}
                      alt={`${award.name} icon`}
                    />
                    <p>{award.name}</p>
                  </div>
                ))}
              </div>
            ) : <p>None provided</p>}
          </section>

          {book.sample_chapter_url ? (
            <a
              className="button-primary review-download"
              href={book.sample_chapter_url}
              data-testid={`review-book-${bookIndex}-sample-download`}
            >
              Download Sample Chapter {bookIndex + 1}
            </a>
          ) : <p>No sample chapter provided.</p>}
        </article>
        );
      })}
    </div>
  );
}


export default function App({
  initialStepId = "author_name",
  initialAnswers = {},
  initialBooks,
  genreTree: suppliedGenreTree,
  genreLoadError = "",
}) {
  const initialIndex = Math.max(0, STEPS.findIndex((step) => step.id === initialStepId));
  const [stepIndex, setStepIndex] = useState(initialIndex);
  const [answers, setAnswers] = useState({ ...EMPTY_ANSWERS, ...initialAnswers });
  const [books, setBooks] = useState(
    initialBooks?.length ? initialBooks : [emptyBook()],
  );
  const [genreTree, setGenreTree] = useState(suppliedGenreTree ?? null);
  const [catalogError, setCatalogError] = useState(genreLoadError);
  const [showBookValidationErrors, setShowBookValidationErrors] = useState(false);
  const [fieldError, setFieldError] = useState("");
  const [submitState, setSubmitState] = useState({ type: "", message: "" });
  const [submitting, setSubmitting] = useState(false);
  const [authorId, setAuthorId] = useState("");
  const [persistedSubmission, setPersistedSubmission] = useState(null);
  const inputRef = useRef(null);
  const step = STEPS[stepIndex];
  const answerSteps = STEPS.length - 1;

  useEffect(() => {
    if (suppliedGenreTree !== undefined) return;
    let active = true;
    fetch("/genres")
      .then((response) => {
        if (!response.ok) throw new Error("Genre catalog is not configured.");
        return response.json();
      })
      .then((tree) => {
        if (!isValidGenreTree(tree)) throw new Error("Genre catalog is invalid.");
        if (active) setGenreTree(tree);
      })
      .catch(() => {
        if (active) setCatalogError("Genre catalog is not configured.");
      });
    return () => {
      active = false;
    };
  }, [suppliedGenreTree]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [stepIndex]);

  function setAnswer(field, value) {
    setAnswers((current) => ({ ...current, [field]: value }));
    setFieldError("");
  }

  // Mirrors setAnswer's side-effect: any book edit clears the stale step-level error
  // that advance() may have set. Without this, fieldError lingers until the next
  // Continue attempt even after the user has fixed the flagged field.
  function updateBooks(value) {
    setBooks(value);
    setFieldError("");
  }

  function validateCurrentStep() {
    if (step.type === "headshot") {
      return validateOptionalImage(answers.author_headshot, "Author photo");
    }
    if (step.type === "genres") {
      if (catalogError || !genreTree) return catalogError || "Genre catalog is loading.";
      if (!answers.genres.length) return "Select at least one genre.";
      return "";
    }
    if (step.type === "books") return validateBooks(books, genreTree);
    if (step.type === "socials") {
      const invalid = SOCIAL_FIELDS.find(([field]) => (
        answers[field].trim() && !isHttpUrl(answers[field].trim())
      ));
      return invalid
        ? `${invalid[2]} must contain a valid domain such as example.com.`
        : "";
    }
    return validateSimpleStep(step, answers);
  }

  function csrfHeaders(json = false) {
    const headers = json ? { "Content-Type": "application/json" } : {};
    const csrfCookie = document.cookie
      .split(";")
      .map((part) => part.trim())
      .find((part) => part.startsWith("csrftoken="));
    if (csrfCookie) {
      headers["X-CSRFToken"] = decodeURIComponent(
        csrfCookie.slice("csrftoken=".length),
      );
    }
    return headers;
  }

  async function persistForReview(answerValues = answers) {
    setSubmitting(true);
    setSubmitState({ type: "progress", message: "Saving your information…" });
    try {
      const saveResponse = await fetch("/onboarding", {
        method: "POST",
        headers: csrfHeaders(),
        body: buildSubmission(answerValues, books, authorId),
      });
      const saveData = await saveResponse.json();
      if (!saveResponse.ok) {
        setSubmitState({
          type: "error",
          message: saveData.message || "We could not save your information.",
        });
        return;
      }

      const authorResponse = await fetch(`/authors/${saveData.author_id}`);
      const authorData = await authorResponse.json();
      if (!authorResponse.ok) {
        setSubmitState({
          type: "error",
          message: authorData.message || "We could not load your saved information.",
        });
        return;
      }

      const booksResponse = await fetch(`/authors/${saveData.author_id}/books`);
      const booksData = await booksResponse.json();
      if (!booksResponse.ok) {
        setSubmitState({
          type: "error",
          message: booksData.message || "We could not load your saved books.",
        });
        return;
      }

      setAuthorId(saveData.author_id);
      setPersistedSubmission({
        author_name: authorData.name,
        author_email: authorData.contact_email,
        site_domain: authorData.site_domain,
        site_tagline: authorData.site_tagline,
        author_bio_short: authorData.bio_short,
        author_bio_long: authorData.bio_long,
        genres: authorData.genres,
        primary_color: authorData.primary_color,
        secondary_color: authorData.secondary_color,
        newsletter_link: authorData.newsletter_link,
        author_headshot_url: authorData.headshot_url,
        social_links: authorData.social_links,
        books: booksData.map((book) => ({
          ...book,
          category: book.category.name,
          genre: book.genre.name,
          subgenre: book.subgenre?.name || "",
          series_type: book.series ? "series" : "standalone",
          series_name: book.series?.name || "",
          series_length: book.series?.total_books || null,
          series_is_complete: book.series?.is_complete || false,
        })),
      });
      setSubmitState({ type: "", message: "" });
      setStepIndex(STEPS.findIndex((item) => item.id === "review"));
    } catch {
      setSubmitState({
        type: "error",
        message: "We could not reach the server. Check your connection and try again.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function advance() {
    const error = validateCurrentStep();
    if (error) {
      if (step.type === "books") setShowBookValidationErrors(true);
      setFieldError(error);
      inputRef.current?.focus();
      return;
    }
    if (step.type === "books") setShowBookValidationErrors(false);
    setFieldError("");
    setSubmitState({ type: "", message: "" });
    if (STEPS[stepIndex + 1]?.id === "review") {
      await persistForReview();
      return;
    }
    setStepIndex((current) => Math.min(current + 1, STEPS.length - 1));
  }

  function goBack() {
    setFieldError("");
    setSubmitState({ type: "", message: "" });
    // Reset so inline per-field errors don't appear on untouched fields when
    // the user returns to the books step after previously triggering validation.
    setShowBookValidationErrors(false);
    setStepIndex((current) => Math.max(current - 1, 0));
  }

  async function skip() {
    const clearedAnswers = { ...answers };
    if (step.type === "socials") {
      SOCIAL_FIELDS.forEach(([field]) => {
        clearedAnswers[field] = "";
      });
    } else {
      clearedAnswers[step.id] = "";
    }
    setAnswers(clearedAnswers);
    setFieldError("");
    setSubmitState({ type: "", message: "" });
    if (STEPS[stepIndex + 1]?.id === "review") {
      await persistForReview(clearedAnswers);
      return;
    }
    setStepIndex((current) => Math.min(current + 1, STEPS.length - 1));
  }

  async function submit(event) {
    event.preventDefault();
    if (step.id !== "review" || submitting || !authorId) return;
    setSubmitting(true);
    setSubmitState({ type: "progress", message: "Calling the generation endpoint…" });
    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: csrfHeaders(true),
        body: JSON.stringify({ author_id: authorId }),
      });
      const data = await response.json();
      if (!response.ok) {
        setSubmitState({
          type: "error",
          message: data.message || "We could not validate your information.",
        });
        return;
      }
      setSubmitState({
        type: "success",
        message: "The generation endpoint was called successfully.",
      });
    } catch {
      setSubmitState({
        type: "error",
        message: "We could not reach the server. Check your connection and try again.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  const isSkippable = (
    (!step.required && !step.type && step.id !== "review")
    || step.type === "socials"
    || step.type === "headshot"
  );
  const continueDisabled = (
    (step.type === "genres" || step.type === "books")
    && (Boolean(catalogError) || !genreTree)
  );

  return (
    <main className="wizard-shell">
      <div className="wizard-brand">Author Website Generator</div>
      <form className="wizard-card" aria-label="Author website onboarding" onSubmit={submit} noValidate>
        <div className="wizard-progress-copy">
          {step.id === "review" ? "Review" : `Question ${stepIndex + 1} of ${answerSteps}`}
        </div>
        <div
          className="wizard-progress"
          role="progressbar"
          aria-label="Onboarding progress"
          aria-valuemin="1"
          aria-valuemax={answerSteps}
          aria-valuenow={step.id === "review" ? answerSteps : stepIndex + 1}
        >
          <span style={{ width: `${((step.id === "review" ? answerSteps : stepIndex + 1) / answerSteps) * 100}%` }} />
        </div>

        {stepIndex > 0 && (
          <button type="button" className="button-secondary wizard-back" data-testid="wizard-back" onClick={goBack}>
            Back
          </button>
        )}

        <section className="wizard-question" key={step.id}>
          <h1>{step.title}</h1>
          {step.help && <p className="question-help step-help">{step.help}</p>}

          {step.id === "review" ? (
            <DatabaseReview submission={persistedSubmission} />
          ) : step.type === "genres" ? (
            <GenreStep
              selected={answers.genres}
              genreTree={genreTree}
              error={catalogError}
              onChange={(value) => setAnswer("genres", value)}
            />
          ) : step.type === "colors" ? (
            <div className="color-fields">
              <ColorField id="primary" label="Primary brand color" value={answers.primary_color} onChange={(value) => setAnswer("primary_color", value)} />
              <ColorField id="secondary" label="Secondary brand color" value={answers.secondary_color} onChange={(value) => setAnswer("secondary_color", value)} />
            </div>
          ) : step.type === "books" ? (
            <BookPortfolioStep
              books={books}
              genreTree={genreTree}
              showValidationErrors={showBookValidationErrors}
              onChange={updateBooks}
            />
          ) : step.type === "headshot" ? (
            <HeadshotStep
              value={answers.author_headshot}
              onChange={(value) => setAnswer("author_headshot", value)}
            />
          ) : step.type === "socials" ? (
            <SocialStep answers={answers} onChange={setAnswer} />
          ) : (
            <div className="field-stack">
              <label htmlFor={step.id}>
                {step.label}
                {!step.required && <span className="optional-label"> Optional</span>}
              </label>
              {step.multiline ? (
                <textarea
                  ref={inputRef}
                  id={step.id}
                  data-testid={step.id}
                  rows={5}
                  value={answers[step.id]}
                  onChange={(event) => setAnswer(step.id, event.target.value)}
                  aria-invalid={Boolean(fieldError)}
                />
              ) : (
                <input
                  ref={inputRef}
                  id={step.id}
                  data-testid={step.id}
                  type="text"
                  required={step.required}
                  value={answers[step.id]}
                  autoComplete={step.autocomplete || "off"}
                  placeholder={step.placeholder || ""}
                  onChange={(event) => setAnswer(step.id, event.target.value)}
                  aria-invalid={Boolean(fieldError)}
                />
              )}
            </div>
          )}
        </section>

        {fieldError && <p className="field-error step-error" role="alert">{fieldError}</p>}
        {submitState.message && (
          <div className={`submission-message submission-${submitState.type}`} role={submitState.type === "error" ? "alert" : "status"}>
            {submitState.message}
          </div>
        )}

        <div className="wizard-actions">
          <div className="wizard-actions-end">
            {step.id === "review" ? (
              <button type="submit" className="button-primary" data-testid="generate-site" disabled={submitting}>
                {submitting ? "Validating…" : "Generate Site"}
              </button>
            ) : (
              <>
                <button type="button" className="button-primary" data-testid="wizard-continue" onClick={advance} disabled={continueDisabled}>
                  Continue
                </button>
                {isSkippable && (
                  <button type="button" className="button-link" data-testid="wizard-skip" onClick={skip} disabled={submitting}>
                    Skip
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </form>
    </main>
  );
}


export {
  buildPayload,
  buildSubmission,
  flattenGenreOptions,
  isValidGenreTree,
  parseBuyLinks,
  searchGenreOptions,
  validateBuyLinks,
  validateBooks,
};
