import { useCallback, useEffect, useMemo, useRef, useState } from "react";


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
    label: "Author email",
    title: "What email should we use?",
    help: "This is used for your onboarding information.",
    required: true,
    autocomplete: "email",
  },
  {
    id: "website_name",
    label: "Website name",
    title: "What should your new website be called?",
    help: "For example, “Jane Doe Books.” This is not an existing website address.",
    required: true,
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
    id: "genres",
    label: "Genres",
    title: "What genres do you write?",
    help: "Separate multiple genres with commas.",
  },
  {
    id: "primary_color",
    label: "Primary brand color",
    title: "What is your primary brand color?",
    help: "Enter a six-digit hex color, such as #2563EB.",
    placeholder: "#2563EB",
  },
  {
    id: "secondary_color",
    label: "Secondary brand color",
    title: "What is your secondary brand color?",
    help: "Enter a six-digit hex color, such as #64748B.",
    placeholder: "#64748B",
  },
  {
    id: "books",
    label: "Book portfolio",
    title: "Would you like to add your books?",
    help: "Add each book you'd like featured on your site.",
    type: "books",
  },
  {
    id: "newsletter_link",
    label: "Newsletter signup link or Kit form ID",
    title: "How should readers join your newsletter?",
    help: "Enter a signup URL or a Kit form ID.",
  },
  {
    id: "social_twitter",
    label: "Twitter / X",
    title: "What is your Twitter / X profile?",
    help: "Enter the full URL beginning with http:// or https://.",
  },
  {
    id: "social_instagram",
    label: "Instagram",
    title: "What is your Instagram profile?",
    help: "Enter the full URL beginning with http:// or https://.",
  },
  {
    id: "social_facebook",
    label: "Facebook",
    title: "What is your Facebook profile?",
    help: "Enter the full URL beginning with http:// or https://.",
  },
  {
    id: "social_tiktok",
    label: "TikTok",
    title: "What is your TikTok profile?",
    help: "Enter the full URL beginning with http:// or https://.",
  },
  {
    id: "social_youtube",
    label: "YouTube",
    title: "What is your YouTube channel?",
    help: "Enter the full URL beginning with http:// or https://.",
  },
  {
    id: "review",
    title: "Review your new website details",
  },
];

const EMPTY_ANSWERS = Object.fromEntries(
  STEPS.filter((step) => step.id !== "review" && step.type !== "books").map((step) => [step.id, ""]),
);

/** A blank book entry used when adding a new row. */
const EMPTY_BOOK = { title: "", description: "", buy_links: "" };

const SOCIAL_FIELDS = [
  ["social_twitter", "twitter"],
  ["social_instagram", "instagram"],
  ["social_facebook", "facebook"],
  ["social_tiktok", "tiktok"],
  ["social_youtube", "youtube"],
];


function validateAnswer(step, value) {
  const trimmed = value.trim();
  if (step.required && !trimmed) {
    return `${step.label} is required.`;
  }
  if (!trimmed) return "";

  if (step.id === "author_email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    return "Enter a valid email address.";
  }

  if (
    ["primary_color", "secondary_color"].includes(step.id)
    && !/^#[0-9a-fA-F]{6}$/.test(trimmed)
  ) {
    return "Enter a six-digit hex color beginning with #.";
  }

  if (step.id.startsWith("social_")) {
    try {
      const url = new URL(trimmed);
      if (!["http:", "https:"].includes(url.protocol)) throw new Error("Invalid protocol");
    } catch {
      return "Enter a full URL beginning with http:// or https://.";
    }
  }

  return "";
}


function getCsrfToken() {
  const cookie = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith("csrftoken="));
  return cookie ? decodeURIComponent(cookie.slice("csrftoken=".length)) : "";
}


/**
 * Converts a raw buy_links string (comma-separated URLs) into an array of
 * trimmed, non-empty strings for the backend.
 */
function parseBuyLinks(raw) {
  return (raw || "")
    .split(",")
    .map((link) => link.trim())
    .filter(Boolean);
}

function buildPayload(answers, books = []) {
  const payload = {};
  const plainFields = [
    "author_name",
    "author_email",
    "website_name",
    "site_tagline",
    "author_bio_short",
    "author_bio_long",
    "primary_color",
    "secondary_color",
    "newsletter_link",
  ];

  plainFields.forEach((field) => {
    const value = answers[field]?.trim();
    if (value) payload[field] = value;
  });

  const genres = (answers.genres || "")
    .split(",")
    .map((genre) => genre.trim())
    .filter(Boolean);
  if (genres.length) payload.genres = genres;

  // Only include books that have at least a title
  const bookEntries = books
    .filter((b) => b.title.trim())
    .map((b) => {
      const entry = { title: b.title.trim() };
      if (b.description?.trim()) entry.description = b.description.trim();
      const links = parseBuyLinks(b.buy_links);
      if (links.length) entry.buy_links = links;
      return entry;
    });
  if (bookEntries.length) payload.books = bookEntries;

  const socialLinks = {};
  SOCIAL_FIELDS.forEach(([answerField, payloadField]) => {
    const value = answers[answerField]?.trim();
    if (value) socialLinks[payloadField] = value;
  });
  if (Object.keys(socialLinks).length) payload.social_links = socialLinks;

  return payload;
}


/**
 * BookPortfolioStep renders a dynamic list of book entry rows.
 * Books are stored separately from the flat answers map because each book is
 * a nested object (title, description, buy_links), not a single string.
 */
function BookPortfolioStep({ books, onChange }) {
  function addBook() {
    onChange([...books, { ...EMPTY_BOOK }]);
  }

  function removeBook(index) {
    onChange(books.filter((_, i) => i !== index));
  }

  function updateBook(index, field, value) {
    onChange(books.map((book, i) => (i === index ? { ...book, [field]: value } : book)));
  }

  return (
    <div className="book-portfolio">
      {books.length === 0 && (
        <p className="question-help">No books added yet. Click the button below to add one.</p>
      )}
      {books.map((book, index) => (
        <div key={index} className="book-entry">
          <div className="book-entry-header">
            <span className="book-entry-label">Book {index + 1}</span>
            <button
              type="button"
              className="button-link book-remove"
              onClick={() => removeBook(index)}
              aria-label={`Remove book ${index + 1}`}
            >
              Remove
            </button>
          </div>
          <div className="book-entry-fields">
            <label htmlFor={`book-title-${index}`}>Title</label>
            <input
              id={`book-title-${index}`}
              type="text"
              value={book.title}
              placeholder="The Midnight Code"
              onChange={(e) => updateBook(index, "title", e.target.value)}
            />
            <label htmlFor={`book-desc-${index}`}>
              Description <span className="optional-label">Optional</span>
            </label>
            <textarea
              id={`book-desc-${index}`}
              value={book.description}
              placeholder="A brief description of the book…"
              rows={2}
              onChange={(e) => updateBook(index, "description", e.target.value)}
            />
            <label htmlFor={`book-links-${index}`}>
              Buy links <span className="optional-label">Optional — comma-separated URLs</span>
            </label>
            <input
              id={`book-links-${index}`}
              type="text"
              value={book.buy_links}
              placeholder="https://amazon.com/dp/…, https://barnesandnoble.com/…"
              onChange={(e) => updateBook(index, "buy_links", e.target.value)}
            />
          </div>
        </div>
      ))}
      <button type="button" className="button-secondary book-add" onClick={addBook}>
        + Add {books.length === 0 ? "a book" : "another book"}
      </button>
    </div>
  );
}


export default function App({ initialStepId = "author_name", initialAnswers = {}, initialBooks = [] }) {
  const initialIndex = Math.max(
    0,
    STEPS.findIndex((step) => step.id === initialStepId),
  );
  const [stepIndex, setStepIndex] = useState(initialIndex);
  const [answers, setAnswers] = useState({ ...EMPTY_ANSWERS, ...initialAnswers });
  // Books are stored as a separate array of objects, not in the flat answers map
  const [books, setBooks] = useState(initialBooks);
  const [fieldError, setFieldError] = useState("");
  const [submitState, setSubmitState] = useState({ type: "", message: "" });
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef(null);
  const step = STEPS[stepIndex];
  const answerSteps = STEPS.length - 1;

  useEffect(() => {
    inputRef.current?.focus();
  }, [stepIndex]);

  const answeredItems = useMemo(
    () => STEPS.slice(0, -1)
      .map((item) => ({
        ...item,
        value: answers[item.id]?.trim() || "",
      }))
      .filter((item) => item.value),
    [answers],
  );

  function updateAnswer(event) {
    setAnswers((current) => ({ ...current, [step.id]: event.target.value }));
    setFieldError("");
  }

  function advance() {
    const error = validateAnswer(step, answers[step.id] || "");
    if (error) {
      setFieldError(error);
      inputRef.current?.focus();
      return;
    }
    setFieldError("");
    setSubmitState({ type: "", message: "" });
    setStepIndex((current) => Math.min(current + 1, STEPS.length - 1));
  }

  function goBack() {
    setFieldError("");
    setSubmitState({ type: "", message: "" });
    setStepIndex((current) => Math.max(current - 1, 0));
  }

  function skip() {
    setAnswers((current) => ({ ...current, [step.id]: "" }));
    setFieldError("");
    setStepIndex((current) => Math.min(current + 1, STEPS.length - 1));
  }

  async function submit(event) {
    event.preventDefault();
    if (step.id !== "review" || submitting) return;

    setSubmitting(true);
    setSubmitState({ type: "progress", message: "Validating your information…" });

    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCsrfToken();
    if (csrfToken) headers["X-CSRFToken"] = csrfToken;

    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers,
        body: JSON.stringify(buildPayload(answers, books)),
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
        message: "Your information is valid and ready for website generation.",
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

  const progressValue = step.id === "review" ? answerSteps : stepIndex + 1;

  return (
    <main className="wizard-shell">
      <div className="wizard-brand">Author Website Generator</div>
      <form
        className="wizard-card"
        aria-label="Author website onboarding"
        onSubmit={submit}
        noValidate
      >
        <div className="wizard-progress-copy">
          {step.id === "review"
            ? "Review"
            : `Question ${stepIndex + 1} of ${answerSteps}`}
        </div>
        <div
          className="wizard-progress"
          role="progressbar"
          aria-label="Onboarding progress"
          aria-valuemin="1"
          aria-valuemax={answerSteps}
          aria-valuenow={progressValue}
        >
          <span style={{ width: `${(progressValue / answerSteps) * 100}%` }} />
        </div>

        <section className="wizard-question" key={step.id}>
          <h1>{step.title}</h1>

          {step.id === "review" ? (
            <>
              <p className="question-help">
                Confirm the details below. You can go back to make changes.
              </p>
              <dl className="review-list">
                {answeredItems.map((item) => (
                  <div className="review-item" key={item.id}>
                    <dt>{item.label}</dt>
                    <dd>{item.value}</dd>
                  </div>
                ))}
                {books.filter((b) => b.title.trim()).length > 0 && (
                  <div className="review-item">
                    <dt>Books</dt>
                    <dd>{books.filter((b) => b.title.trim()).map((b) => b.title.trim()).join(", ")}</dd>
                  </div>
                )}
              </dl>
            </>
          ) : step.type === "books" ? (
            <>
              <p className="question-help">{step.help}</p>
              <BookPortfolioStep books={books} onChange={setBooks} />
            </>
          ) : (
            <>
              <label htmlFor={step.id}>
                {step.label}
                {!step.required && <span className="optional-label"> Optional</span>}
              </label>
              {step.multiline ? (
                <textarea
                  ref={inputRef}
                  id={step.id}
                  value={answers[step.id]}
                  onChange={updateAnswer}
                  rows={5}
                  aria-invalid={Boolean(fieldError)}
                  aria-describedby={`${step.id}-help ${step.id}-error`}
                />
              ) : (
                <input
                  ref={inputRef}
                  id={step.id}
                  type="text"
                  value={answers[step.id]}
                  onChange={updateAnswer}
                  autoComplete={step.autocomplete || "off"}
                  placeholder={step.placeholder || ""}
                  aria-invalid={Boolean(fieldError)}
                  aria-describedby={`${step.id}-help ${step.id}-error`}
                />
              )}
              <p className="question-help" id={`${step.id}-help`}>{step.help}</p>
              {fieldError && (
                <p className="field-error" id={`${step.id}-error`} role="alert">
                  {fieldError}
                </p>
              )}
            </>
          )}
        </section>

        {submitState.message && (
          <div
            className={`submission-message submission-${submitState.type}`}
            role={submitState.type === "error" ? "alert" : "status"}
          >
            {submitState.message}
          </div>
        )}

        <div className="wizard-actions">
          {stepIndex > 0 && (
            <button type="button" className="button-secondary" onClick={goBack}>
              Back
            </button>
          )}
          <div className="wizard-actions-end">
            {step.id !== "review" && !step.required && (
              <button type="button" className="button-link" onClick={skip}>
                Skip
              </button>
            )}
            {step.id === "review" ? (
              <button type="submit" className="button-primary" disabled={submitting}>
                {submitting ? "Validating…" : "Generate Site"}
              </button>
            ) : (
              <button type="button" className="button-primary" onClick={advance}>
                Continue
              </button>
            )}
          </div>
        </div>
      </form>
    </main>
  );
}

export { buildPayload, parseBuyLinks, validateAnswer };
