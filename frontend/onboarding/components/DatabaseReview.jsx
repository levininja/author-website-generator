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


export function DatabaseReview({ submission }) {
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
        <ReviewField label="Website template" value={submission.selected_template || "None selected"} />
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
