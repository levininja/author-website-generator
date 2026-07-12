export function flattenGenreOptions(genreTree) {
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


export function searchGenreOptions(options, rawQuery, limit = 8) {
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
