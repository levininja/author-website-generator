import { useMemo, useRef, useState } from "react";

import { flattenGenreOptions, searchGenreOptions } from "../genreSearch";


export function GenreStep({ selected, genreTree, error, onChange }) {
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
