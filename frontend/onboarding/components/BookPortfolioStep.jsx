import { emptyBook } from "../constants";
import { BookEntry } from "./BookEntry";


export function BookPortfolioStep({
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
