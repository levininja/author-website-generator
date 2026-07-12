import { useState } from "react";

import { IMAGE_TYPES } from "../constants";
import { validateBuyLinks } from "../validation";
import { Repeater } from "./Repeater";


export function BookEntry({
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
