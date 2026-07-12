import { useEffect, useRef, useState } from "react";

import { BookPortfolioStep } from "./components/BookPortfolioStep";
import { ClassicTemplateStep } from "./components/ClassicTemplateStep";
import { ColorField } from "./components/ColorField";
import { DatabaseReview } from "./components/DatabaseReview";
import { GenreStep } from "./components/GenreStep";
import { HeadshotStep } from "./components/HeadshotStep";
import { SocialStep } from "./components/SocialStep";
import { EMPTY_ANSWERS, emptyBook, SOCIAL_FIELDS, STEPS } from "./constants";
import { buildSubmission } from "./submission";
import {
  isHttpUrl,
  isValidGenreTree,
  validateBooks,
  validateOptionalImage,
  validateSimpleStep,
} from "./validation";


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
        selected_template: authorData.selected_template,
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
    } else if (step.type === "template") {
      clearedAnswers[step.id] = null;
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
    || step.type === "template"
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
          ) : step.type === "template" ? (
            <ClassicTemplateStep />
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

        {stepIndex > 0 && (
          <button type="button" className="button-secondary wizard-back" data-testid="wizard-back" onClick={goBack}>
            Back
          </button>
        )}
      </form>
    </main>
  );
}


export { buildPayload, buildSubmission } from "./submission";
export { flattenGenreOptions, searchGenreOptions } from "./genreSearch";
export {
  isValidGenreTree,
  parseBuyLinks,
  validateBooks,
  validateBuyLinks,
} from "./validation";
