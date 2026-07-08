import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App, * as onboarding from "./App";


const GENRE_TREE = {
  Fiction: {
    "Science Fiction": ["Cyberpunk", "Space Opera"],
    Fantasy: ["Epic Fantasy", "Urban Fantasy"],
  },
  Nonfiction: {
    "Biography & Memoir": ["Biography", "Memoir"],
  },
};

const PNG_FILE = new File(["valid image"], "cover.png", { type: "image/png" });

const STORED_AUTHOR = {
  id: "11111111-1111-4111-8111-111111111111",
  name: "Jane Doe",
  contact_email: "contact@example.com",
  site_domain: "janedoe.com",
  site_tagline: "Code after dark",
  bio_short: "Short biography.",
  bio_long: "Long biography.",
  genres: ["Cyberpunk"],
  primary_color: "#112233",
  secondary_color: "#abcdef",
  newsletter_link: "kit-form-123",
  social_links: {
    goodreads: "https://goodreads.com/author/123",
  },
};

const STORED_BOOKS = [
    {
      id: "22222222-2222-4222-8222-222222222222",
      title: "The Midnight Code",
      cover_image_url: "/media/onboarding/cover.webp",
      description: "A technological thriller.",
      buy_links: ["https://example.com/buy"],
      category: { id: 1, name: "Fiction" },
      genre: { id: 2, name: "Science Fiction" },
      subgenre: { id: 3, name: "Cyberpunk" },
      series: null,
      number_in_series: null,
      editorial_reviews: [
        {
          reviewer_name: "Kirkus",
          credentials: null,
          quotation: "A sharp debut.",
          original_review_url: "https://example.com/review",
          photo_url: "/media/onboarding/kirkus.webp",
          stars: 5,
          is_starred_review: true,
        },
      ],
      other_reviews: [
        {
          reviewer_name: "Reader One",
          credentials: "Author of The Last Stand",
          quotation: "Read this.",
          original_review_url: "https://example.com/reader-review",
          stars: 5,
          photo_url: "/media/onboarding/reviewer.webp",
          is_starred_review: false,
        },
      ],
      awards: [
        {
          name: "Best Debut",
          icon_url: "/media/onboarding/award.webp",
        },
      ],
      perfect_for: "Readers who like code.",
      enjoy_if: "You enjoy thrillers.",
      sample_chapter_url: (
        "/books/22222222-2222-4222-8222-222222222222/sample-chapter"
      ),
      sample_chapter_name: "Chapter One.pdf",
    },
];


function completeBook(overrides = {}) {
  return {
    title: "The Midnight Code",
    cover_image: PNG_FILE,
    description: "A technological thriller.",
    buy_links: "https://example.com/buy",
    category: "Fiction",
    genre: "Science Fiction",
    subgenre: "Cyberpunk",
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
    ...overrides,
  };
}


function requiredAnswers(overrides = {}) {
  return {
    author_name: "Jane Doe",
    author_email: "contact@example.com",
    site_domain: "janedoe.com",
    genres: ["Cyberpunk"],
    ...overrides,
  };
}


function renderApp(props = {}) {
  return render(<App genreTree={GENRE_TREE} {...props} />);
}

function expectInteractiveElementsToHaveUniqueTestIds(container) {
  const elements = [...container.querySelectorAll("a, button, input, select, textarea")];
  const testIds = elements.map((element) => element.getAttribute("data-testid"));

  expect(elements.length).toBeGreaterThan(0);
  testIds.forEach((testId) => expect(testId).toBeTruthy());
  expect(new Set(testIds).size).toBe(testIds.length);
}


beforeEach(() => {
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    value: vi.fn(),
  });
});


afterEach(() => {
  vi.restoreAllMocks();
});


describe("wording, navigation, and grouped steps", () => {
  it.each([
    ["author_name"],
    ["author_bio_short"],
    ["colors"],
    ["social_links"],
    ["author_headshot"],
  ])("gives every interactive element a unique test ID on the %s step", (initialStepId) => {
    const { container } = renderApp({ initialStepId });

    expectInteractiveElementsToHaveUniqueTestIds(container);
  });

  it("gives genre search, suggestions, and selected-genre controls unique test IDs", async () => {
    const user = userEvent.setup();
    const { container } = renderApp({ initialStepId: "genres" });

    await user.type(screen.getByRole("combobox", { name: /search genres/i }), "cy");
    await user.click(screen.getByRole("option", { name: /cyberpunk/i }));

    expectInteractiveElementsToHaveUniqueTestIds(container);
  });

  it("loads the genre catalog from the database-backed endpoint", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => GENRE_TREE,
    });

    render(<App initialStepId="genres" />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/genres"));
    expect(screen.getByRole("combobox", { name: /search genres/i })).toBeVisible();
  });

  it("explains that email receives reader contact-form messages", () => {
    renderApp({ initialStepId: "author_email" });

    expect(
      screen.getByRole("heading", { name: /what email should reader messages go to/i }),
    ).toBeVisible();
    expect(screen.getByText(/contact form/i)).toBeVisible();
  });

  it("asks for a purchased or aspirational site domain using the requested guidance", () => {
    renderApp({ initialStepId: "site_domain" });

    expect(
      screen.getByRole("heading", { name: /what is your site domain/i }),
    ).toBeVisible();
    expect(screen.getByText(/already purchased through a DNS provider/i)).toBeVisible();
    expect(screen.getByText(/GoDaddy or Namecheap/i)).toBeVisible();
    expect(screen.getByText(/aspirational domain name/i)).toBeVisible();
  });

  it("tabs from the active input to Continue instead of Back", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "author_email",
      initialAnswers: requiredAnswers(),
    });

    const input = screen.getByLabelText(/contact email/i);
    await waitFor(() => expect(input).toHaveFocus());
    await user.tab();

    expect(screen.getByRole("button", { name: /continue/i })).toHaveFocus();
  });

  it("tabs from Continue to Back on a non-skippable step when Back is present", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "author_email",
      initialAnswers: requiredAnswers(),
    });

    const input = screen.getByLabelText(/contact email/i);
    await waitFor(() => expect(input).toHaveFocus());
    await user.tab();
    expect(screen.getByRole("button", { name: /continue/i })).toHaveFocus();

    await user.tab();

    expect(screen.getByRole("button", { name: /^back$/i })).toHaveFocus();
  });

  it("tabs from Continue to Skip on a skippable step", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "site_tagline" });

    screen.getByRole("button", { name: /continue/i }).focus();
    await user.tab();

    expect(screen.getByRole("button", { name: /^skip$/i })).toHaveFocus();
  });

  it("tabs from Skip to Back on a skippable step when Back is present", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "site_tagline" });

    screen.getByRole("button", { name: /^skip$/i }).focus();
    await user.tab();

    expect(screen.getByRole("button", { name: /^back$/i })).toHaveFocus();
  });

  it("renders a catalog-backed autocomplete instead of the genre checkbox list", () => {
    renderApp({ initialStepId: "genres" });

    expect(screen.getByRole("combobox", { name: /search genres/i })).toBeVisible();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("matches all hierarchy levels case-insensitively and shows full paths", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "genres" });

    const input = screen.getByRole("combobox", { name: /search genres/i });
    await user.type(input, "CYB");

    expect(
      screen.getByRole("option", {
        name: /Fiction.*Science Fiction.*Cyberpunk/i,
      }),
    ).toBeVisible();

    await user.clear(input);
    await user.type(input, "nonf");
    expect(
      screen.getByRole("option", { name: /Nonfiction.*category/i }),
    ).toBeVisible();
  });

  it("ranks prefix matches before contains matches and caps results", () => {
    const options = onboarding.flattenGenreOptions(GENRE_TREE);
    const matches = onboarding.searchGenreOptions(options, "fiction", 2);

    expect(matches).toHaveLength(2);
    expect(matches[0].value).toBe("Fiction");
    expect(matches[0].label.toLowerCase().startsWith("fiction")).toBe(true);
  });

  it("selects with the mouse and renders a removable chip", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "genres" });

    await user.type(screen.getByRole("combobox", { name: /search genres/i }), "cyber");
    await user.click(screen.getByRole("option", { name: /Cyberpunk/i }));

    expect(screen.getByText("Cyberpunk")).toBeVisible();
    expect(
      screen.getByRole("button", { name: /remove Cyberpunk/i }),
    ).toBeVisible();
    expect(screen.getByRole("combobox", { name: /search genres/i })).toHaveValue("");
  });

  it("supports ArrowDown, Enter, and Escape keyboard interaction", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "genres" });

    const input = screen.getByRole("combobox", { name: /search genres/i });
    await user.type(input, "space");
    await user.keyboard("{ArrowDown}{Enter}");

    expect(screen.getByText("Space Opera")).toBeVisible();

    await user.type(input, "fant");
    expect(screen.getByRole("listbox")).toBeVisible();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("removes selected genres and does not offer duplicates", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "genres",
      initialAnswers: requiredAnswers({ genres: ["Cyberpunk"] }),
    });

    const input = screen.getByRole("combobox", { name: /search genres/i });
    await user.type(input, "cyber");
    expect(screen.queryByRole("option", { name: /Cyberpunk/i })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /remove Cyberpunk/i }));
    expect(
      screen.queryByRole("button", { name: /remove Cyberpunk/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Cyberpunk/i })).toBeVisible();
  });

  it("shows a no-results state and still requires one selection", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "genres" });

    await user.type(
      screen.getByRole("combobox", { name: /search genres/i }),
      "not-a-real-genre",
    );
    expect(screen.getByText(/no matching genres/i)).toBeVisible();

    await user.click(screen.getByRole("button", { name: /continue/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/select at least one genre/i);
  });

  it("blocks genre selection when the catalog is unavailable", () => {
    render(<App genreTree={null} genreLoadError="Genre catalog is not configured." initialStepId="genres" />);

    expect(screen.getByRole("alert")).toHaveTextContent(/not configured/i);
    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
  });

  it("shows both color pickers and live preview blocks on one page", async () => {
    renderApp({ initialStepId: "brand_colors" });

    const primary = screen.getByLabelText(/^primary brand color$/i);
    const secondary = screen.getByLabelText(/^secondary brand color$/i);
    expect(primary).toHaveAttribute("type", "color");
    expect(secondary).toHaveAttribute("type", "color");

    fireEvent.change(primary, { target: { value: "#123456" } });

    expect(screen.getByTestId("primary-color-preview")).toHaveStyle({
      backgroundColor: "#123456",
    });
  });

  it("shows all social links, including Goodreads, on one page", () => {
    renderApp({ initialStepId: "social_links" });

    expect(screen.getByLabelText(/twitter.*x/i)).toBeVisible();
    expect(screen.getByLabelText(/instagram/i)).toBeVisible();
    expect(screen.getByLabelText(/facebook/i)).toBeVisible();
    expect(screen.getByLabelText(/tiktok/i)).toBeVisible();
    expect(screen.getByLabelText(/youtube/i)).toBeVisible();
    expect(screen.getByLabelText(/goodreads/i)).toBeVisible();
  });

  it("offers Skip on the optional social links page", () => {
    renderApp({ initialStepId: "social_links" });

    expect(screen.getByRole("button", { name: /^skip$/i })).toBeVisible();
  });

  it("shows the author photo upload step with a file input and a Skip button", () => {
    renderApp({ initialStepId: "author_headshot" });

    expect(
      screen.getByRole("heading", { name: /add a photo/i }),
    ).toBeVisible();
    expect(screen.getByLabelText(/author photo/i)).toHaveAttribute("type", "file");
    expect(screen.getByRole("button", { name: /^skip$/i })).toBeVisible();
  });

  it("shows a thumbnail and selected status after choosing an author photo", async () => {
    const user = userEvent.setup();
    const createObjectURL = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:author-photo");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
    renderApp({ initialStepId: "author_headshot" });

    const photo = new File(["photo"], "author-photo.png", {
      type: "image/png",
    });
    await user.upload(screen.getByLabelText(/author photo/i), photo);

    expect(screen.getByText(/photo selected/i)).toBeVisible();
    expect(screen.getByText("author-photo.png")).toBeVisible();
    expect(screen.getByRole("img", { name: /selected author photo/i }))
      .toHaveAttribute("src", "blob:author-photo");
    expect(createObjectURL).toHaveBeenCalledWith(photo);
  });

  it("releases the author-photo preview URL when the step unmounts", () => {
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:author-photo");
    const revokeObjectURL = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => {});
    const photo = new File(["photo"], "author-photo.png", {
      type: "image/png",
    });

    const view = renderApp({
      initialStepId: "author_headshot",
      initialAnswers: { author_headshot: photo },
    });
    view.unmount();

    expect(revokeObjectURL).toHaveBeenCalledWith("blob:author-photo");
  });

  it("skipping the author photo step advances to the genre step", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "author_headshot" });

    await user.click(screen.getByRole("button", { name: /^skip$/i }));

    expect(
      screen.getByRole("heading", { name: /what genres do you write/i }),
    ).toBeVisible();
  });

  it("shows the 'Website Templates' heading on the template step", () => {
    renderApp({ initialStepId: "selected_template" });

    expect(screen.getByRole("heading", { name: /website templates/i })).toBeVisible();
  });

  it("shows coming-soon copy on the template step", () => {
    renderApp({ initialStepId: "selected_template" });

    expect(
      screen.getByText(/more website templates are coming soon/i),
    ).toBeVisible();
  });

  it("does not render image card elements on the template step", () => {
    const { container } = renderApp({ initialStepId: "selected_template" });

    expect(container.querySelector(".template-card")).toBeNull();
  });

  it("sets selected_template to 'Classic' in the payload after continuing from the template step", () => {
    const payload = onboarding.buildPayload(
      requiredAnswers({ selected_template: "Classic" }),
      [completeBook()],
    );

    expect(payload.selected_template).toBe("Classic");
  });

  it("offers Skip on the template step", () => {
    renderApp({ initialStepId: "selected_template" });

    expect(screen.getByRole("button", { name: /^skip$/i })).toBeVisible();
  });
});


describe("required book portfolio", () => {
  it("gives all book, series, repeater, and optional controls unique test IDs", async () => {
    const user = userEvent.setup();
    const { container } = renderApp({ initialStepId: "books" });

    await user.click(screen.getByLabelText(/part of a series/i));
    await user.click(screen.getByRole("button", { name: /add editorial review/i }));
    await user.click(screen.getByRole("button", { name: /add reader review/i }));
    await user.click(screen.getByRole("button", { name: /add award/i }));
    await user.click(screen.getByRole("button", { name: /add another book/i }));

    expectInteractiveElementsToHaveUniqueTestIds(container);
  });

  it("starts with one book and exposes every required core field", () => {
    renderApp({ initialStepId: "books" });

    const book = screen.getByRole("group", { name: /book 1/i });
    expect(within(book).getByLabelText(/^title/i)).toBeRequired();
    expect(within(book).getByLabelText(/cover image/i)).toBeRequired();
    expect(within(book).getByLabelText(/^description/i)).toBeRequired();
    expect(within(book).getByLabelText(/buy links/i)).toBeRequired();
    expect(within(book).getByLabelText(/^category/i)).toBeRequired();
    expect(within(book).getByLabelText(/^genre/i)).toBeRequired();
    expect(within(book).getByLabelText(/^subgenre/i)).not.toBeRequired();
    const seriesCheckbox = within(book).getByLabelText(/part of a series/i);
    const category = within(book).getByLabelText(/^category/i);
    const classificationRow = category.closest(".book-classification-row");
    expect(classificationRow).not.toBeNull();
    expect(classificationRow.children).toHaveLength(4);
    expect(classificationRow.lastElementChild).toHaveClass(
      "book-classification-spacer",
    );
    expect(seriesCheckbox).toHaveAttribute("type", "checkbox");
    expect(
      category.compareDocumentPosition(seriesCheckbox)
      & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("prevents continuing with an incomplete book", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "books" });

    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getByText(/complete book 1/i)).toHaveClass("step-error");
  });

  it("uses dependent category, genre, and subgenre options", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "books" });

    await user.selectOptions(screen.getByLabelText(/^category/i), "Fiction");
    expect(screen.getByRole("option", { name: "Science Fiction" })).toBeVisible();
    await user.selectOptions(screen.getByLabelText(/^genre/i), "Science Fiction");

    expect(screen.getByRole("option", { name: "Cyberpunk" })).toBeVisible();
    expect(screen.getByRole("option", { name: "Space Opera" })).toBeVisible();
    expect(screen.queryByRole("option", { name: "Memoir" })).not.toBeInTheDocument();
  });

  it("requires series details only when the book belongs to a series", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "books" });

    await user.click(screen.getByLabelText(/part of a series/i));

    expect(screen.getByLabelText(/series name/i)).toBeRequired();
    expect(screen.getByLabelText(/book number/i)).toBeRequired();
    expect(screen.getByLabelText(/total books/i)).toBeRequired();
    expect(screen.getByLabelText(/series is complete/i)).toHaveAttribute(
      "type",
      "checkbox",
    );
  });

  it("adds editorial and other reviews that share the review fields", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "books" });

    await user.click(screen.getByRole("button", { name: /add editorial review/i }));
    expect(screen.getByLabelText(/publication name/i)).toBeRequired();
    expect(screen.getByLabelText(/publication name/i)).toHaveAttribute(
      "placeholder",
      "For example, Kirkus Reviews",
    );
    expect(
      screen.queryByLabelText(/editorial review credentials/i),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^review quotation$/i)).toBeRequired();
    expect(screen.getByLabelText(/review URL \(optional\)/i)).toBeVisible();
    expect(screen.getByLabelText(/review photo \(optional\)/i)).not.toBeRequired();
    expect(screen.getByLabelText(/star rating \(optional\)/i)).not.toBeRequired();
    expect(screen.getByLabelText(/starred review \(optional\)/i))
      .toHaveAttribute("type", "checkbox");

    await user.click(screen.getByRole("button", { name: /add reader review/i }));
    expect(screen.getByRole("heading", { name: /reader reviews/i })).toBeVisible();
    expect(screen.getByRole("group", { name: /reader review 1/i })).toBeVisible();
    expect(screen.getByLabelText(/reviewer name/i)).toBeRequired();
    expect(screen.getByLabelText(/reviewer credentials/i)).not.toBeRequired();
    expect(screen.getByLabelText(/reviewer credentials/i)).toHaveAttribute(
      "placeholder",
      "For example, author of The Last Stand",
    );
    expect(screen.queryByText(/other review/i)).not.toBeInTheDocument();
  });

  it("keeps award uploads required", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "books" });

    await user.click(screen.getByRole("button", { name: /add award/i }));
    expect(screen.getByLabelText(/award name/i)).toBeRequired();
    expect(screen.getByLabelText(/award icon/i)).toBeRequired();
  });

  it("offers reader-fit copy and an optional PDF sample", () => {
    renderApp({ initialStepId: "books" });

    expect(screen.getByLabelText(/this is perfect for/i)).toBeVisible();
    expect(screen.getByLabelText(/you.ll enjoy this if/i)).toBeVisible();
    expect(screen.getByLabelText(/sample chapter PDF/i)).toHaveAttribute(
      "accept",
      "application/pdf",
    );
  });

  it("accepts a bare-domain Buy link when the field loses focus", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "books",
      initialBooks: [completeBook({ buy_links: "amazon.com" })],
    });

    const input = screen.getByLabelText(/buy links/i);
    await user.click(input);
    await user.tab();

    expect(input).toHaveAttribute("aria-invalid", "false");
  });

  it("marks an empty Buy links field invalid on blur", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "books",
      initialBooks: [completeBook({ buy_links: "" })],
    });

    const input = screen.getByLabelText(/buy links/i);
    await user.click(input);
    await user.tab();

    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText(/at least one buy link is required/i)).toBeVisible();
  });

  it("rejects the whole Buy links field when any comma-separated URL is invalid", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "books",
      initialBooks: [
        completeBook({
          buy_links: "https://amazon.com/book, not-a-domain",
        }),
      ],
    });

    const input = screen.getByLabelText(/buy links/i);
    await user.click(input);
    await user.tab();

    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("highlights invalid Buy links when Continue performs validation", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "books",
      initialBooks: [completeBook({ buy_links: "not-a-domain" })],
    });

    const input = screen.getByLabelText(/buy links/i);
    expect(input).toHaveAttribute("aria-invalid", "false");

    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(
      screen.getAllByText(/valid domain such as example.com/i),
    ).not.toHaveLength(0);
  });

  it("clears the Buy links field error immediately after correction", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "books",
      initialBooks: [completeBook({ buy_links: "not-a-domain" })],
    });

    const input = screen.getByLabelText(/buy links/i);
    await user.click(input);
    await user.tab();
    expect(input).toHaveAttribute("aria-invalid", "true");

    await user.clear(input);
    await user.type(input, "amazon.com");

    expect(input).toHaveAttribute("aria-invalid", "false");
    expect(
      screen.queryByText(/valid domain such as example.com/i),
    ).not.toBeInTheDocument();
  });

  it("clears the step-level error when the user edits a book field after validation", async () => {
    const user = userEvent.setup();
    renderApp({ initialStepId: "books" });

    await user.click(screen.getByRole("button", { name: /continue/i }));
    // fieldError is now "Complete Book 1: title is required."
    expect(screen.getByText(/complete book 1.*title is required/i)).toBeVisible();

    await user.type(screen.getByTestId("book-0-title"), "My Book");

    // Editing any book field must clear the stale step-level error immediately
    expect(screen.queryByText(/complete book 1.*title is required/i)).not.toBeInTheDocument();
  });

  it("does not show inline buy-links error on untouched field after Back navigation clears validation state", async () => {
    const user = userEvent.setup();
    // selected_template sits immediately before books in the step list
    renderApp({ initialStepId: "selected_template" });

    // Advance to books
    await user.click(screen.getByRole("button", { name: /continue/i }));
    // Trigger validation — sets showBookValidationErrors=true
    await user.click(screen.getByRole("button", { name: /continue/i }));
    expect(screen.getByText(/complete book 1/i)).toBeVisible();

    // Navigate away and return
    await user.click(screen.getByRole("button", { name: /back/i }));
    await user.click(screen.getByRole("button", { name: /continue/i }));

    // showBookValidationErrors should have been cleared on Back, so the
    // buy-links field must not show an error before the user touches it
    expect(screen.queryByText(/at least one buy link is required/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("book-0-links")).toHaveAttribute("aria-invalid", "false");
  });

  it("does not mark valid HTTP and HTTPS Buy links as invalid", async () => {
    const user = userEvent.setup();
    renderApp({
      initialStepId: "books",
      initialBooks: [
        completeBook({
          buy_links: "https://amazon.com/book, http://example.com/book",
        }),
      ],
    });

    const input = screen.getByLabelText(/buy links/i);
    await user.click(input);
    await user.tab();

    expect(input).toHaveAttribute("aria-invalid", "false");
    expect(screen.queryByText(/buy link.*required/i)).not.toBeInTheDocument();
  });

  it("normalizes bare-domain links to HTTPS in the payload", () => {
    const payload = onboarding.buildPayload(
      requiredAnswers({ social_goodreads: "goodreads.com/author/123" }),
      [
        completeBook({
          buy_links: "amazon.com/book",
          editorial_reviews: [{
            reviewer_name: "Kirkus Reviews",
            quotation: "Excellent.",
            original_review_url: "kirkusreviews.com/review",
            photo: null,
            stars: "",
            is_starred_review: true,
          }],
        }),
      ],
    );

    expect(payload.books[0].buy_links).toEqual(["https://amazon.com/book"]);
    expect(payload.books[0].editorial_reviews[0]).toMatchObject({
      original_review_url: "https://kirkusreviews.com/review",
      is_starred_review: true,
    });
    expect(payload.social_links.goodreads).toBe(
      "https://goodreads.com/author/123",
    );
  });
});


describe("payload and upload submission", () => {
  it("includes author_headshot_key in payload and appends file to FormData when a headshot is uploaded", () => {
    const headshot = new File(["img"], "headshot.png", { type: "image/png" });
    const answers = requiredAnswers({ author_headshot: headshot });
    const submission = onboarding.buildSubmission(answers, [completeBook()]);
    const payload = JSON.parse(submission.get("payload"));

    expect(payload.author_headshot_key).toBe("author_headshot");
    expect(submission.get("author_headshot")).toBe(headshot);
  });

  it("omits author_headshot_key and file from FormData when headshot is null", () => {
    const answers = requiredAnswers({ author_headshot: null });
    const submission = onboarding.buildSubmission(answers, [completeBook()]);
    const payload = JSON.parse(submission.get("payload"));

    expect(payload.author_headshot_key).toBeUndefined();
    expect(submission.get("author_headshot")).toBeNull();
  });

  it("shows the author headshot image in the review page when returned from the database", async () => {
    const user = userEvent.setup();
    const authorWithHeadshot = {
      ...STORED_AUTHOR,
      headshot_url: "/media/onboarding/headshot.webp",
    };
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
          author_url: `/authors/${STORED_AUTHOR.id}`,
          books_url: `/authors/${STORED_AUTHOR.id}/books`,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => authorWithHeadshot,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_BOOKS,
      });
    renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers(),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /continue/i }));

    const img = await screen.findByRole("img", { name: /headshot of Jane Doe/i });
    expect(img).toHaveAttribute("src", "/media/onboarding/headshot.webp");
    expect(img).toHaveClass("review-headshot");
  });

  it("builds nested payload metadata and indexed file keys", () => {
    const reviewerPhoto = new File(["photo"], "reader.png", { type: "image/png" });
    const awardIcon = new File(["icon"], "award.webp", { type: "image/webp" });
    const sample = new File(["%PDF-1.7"], "sample.pdf", { type: "application/pdf" });
    const books = [
      completeBook({
        other_reviews: [
          {
            stars: "5",
            photo: reviewerPhoto,
            reviewer_name: "Reader One",
            credentials: "Author of The Shining",
            quotation: "Excellent.",
            original_review_url: "",
          },
        ],
        awards: [{ name: "Best Debut", icon: awardIcon }],
        sample_chapter: sample,
      }),
    ];

    const submission = onboarding.buildSubmission(requiredAnswers(), books);
    const payload = JSON.parse(submission.get("payload"));

    expect(payload.site_domain).toBe("janedoe.com");
    expect(payload.books[0]).toMatchObject({
      cover_image_key: "book_0_cover_image",
      sample_chapter_key: "book_0_sample_chapter",
      other_reviews: [{
        credentials: "Author of The Shining",
        photo_key: "book_0_other_review_0_photo",
      }],
      awards: [{ icon_key: "book_0_award_0_icon" }],
    });
    expect(submission.get("book_0_cover_image")).toBe(PNG_FILE);
    expect(submission.get("book_0_other_review_0_photo")).toBe(reviewerPhoto);
    expect(submission.get("book_0_award_0_icon")).toBe(awardIcon);
    expect(submission.get("book_0_sample_chapter")).toBe(sample);
  });

  it("persists before review, then loads the review content from the database", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
          author_url: `/authors/${STORED_AUTHOR.id}`,
          books_url: `/authors/${STORED_AUTHOR.id}/books`,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_AUTHOR,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_BOOKS,
      });
    renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers({
        social_goodreads: "https://goodreads.com/author/123",
      }),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(fetchMock.mock.calls[0][0]).toBe("/onboarding");
    const options = fetchMock.mock.calls[0][1];
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.headers).not.toHaveProperty("Content-Type");
    const payload = JSON.parse(options.body.get("payload"));
    expect(payload.social_links.goodreads).toContain("goodreads.com");
    expect(fetchMock.mock.calls[1][0]).toBe(`/authors/${STORED_AUTHOR.id}`);
    expect(fetchMock.mock.calls[2][0]).toBe(
      `/authors/${STORED_AUTHOR.id}/books`,
    );

    expect(
      await screen.findByRole("heading", { name: /review your new website details/i }),
    ).toBeVisible();
    expect(screen.getByText("Code after dark")).toBeVisible();
    expect(screen.getByText("A sharp debut.")).toBeVisible();
    expect(screen.getByRole("img", { name: /cover for The Midnight Code/i })).toHaveAttribute(
      "src",
      "/media/onboarding/cover.webp",
    );
    const download = screen.getByRole("link", {
      name: /^download sample chapter 1$/i,
    });
    expect(download).toHaveAttribute(
      "href",
      "/books/22222222-2222-4222-8222-222222222222/sample-chapter",
    );
    expect(download).toHaveClass("button-primary", "review-download");
    expect(screen.getByRole("img", { name: /primary color swatch #112233/i })).toBeVisible();
    expect(screen.getByRole("img", { name: /secondary color swatch #abcdef/i })).toBeVisible();
    expect(screen.getByText("#112233")).toBeVisible();
    expect(screen.getByText("#abcdef")).toBeVisible();
  });

  it("gives every review action and link a unique test ID", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "ok", author_id: STORED_AUTHOR.id }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_AUTHOR,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_BOOKS,
      });
    const { container } = renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers(),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /continue/i }));
    await screen.findByRole("heading", { name: /review your new website details/i });

    expectInteractiveElementsToHaveUniqueTestIds(container);
  });

  it("shows every user-facing book field on the database confirmation page", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_AUTHOR,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_BOOKS,
      });
    renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers(),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /continue/i }));
    const book = await screen.findByRole("article", {
      name: "The Midnight Code",
    });

    [
      "Description",
      "Category",
      "Genre",
      "Subgenre",
      "Part of a series",
      "Series name",
      "Book number",
      "Total books",
      "Series complete",
      "Perfect for",
      "You'll enjoy this if",
      "Sample chapter filename",
    ].forEach((label) => {
      expect(within(book).getByText(label)).toBeVisible();
    });
    expect(within(book).getAllByText("Not applicable").length).toBeGreaterThan(0);
    expect(within(book).getByText("Author of The Last Stand")).toBeVisible();
    expect(within(book).getAllByText("Starred review")).toHaveLength(2);
    expect(
      within(book).getByRole("img", { name: /kirkus review/i }),
    ).toHaveAttribute("src", "/media/onboarding/kirkus.webp");
    expect(within(book).getByText("Chapter One.pdf")).toBeVisible();
  });

  it("shows explicit empty values for optional book content", async () => {
    const user = userEvent.setup();
    const sparseBook = {
      ...STORED_BOOKS[0],
      subgenre: null,
      editorial_reviews: [],
      other_reviews: [],
      awards: [],
      perfect_for: "",
      enjoy_if: "",
      sample_chapter_url: null,
      sample_chapter_name: "",
    };
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_AUTHOR,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [sparseBook],
      });
    renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers(),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /continue/i }));
    const book = await screen.findByRole("article", {
      name: "The Midnight Code",
    });

    expect(within(book).getAllByText("Not provided").length).toBeGreaterThan(0);
    expect(within(book).getAllByText("None provided")).toHaveLength(3);
    expect(
      within(book).getByText("No sample chapter provided."),
    ).toBeVisible();
  });

  it("skips empty socials, persists without social links, and advances to review", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
          author_url: `/authors/${STORED_AUTHOR.id}`,
          books_url: `/authors/${STORED_AUTHOR.id}/books`,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...STORED_AUTHOR, social_links: {} }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_BOOKS,
      });
    renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers({
        social_goodreads: "not-a-valid-url",
      }),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /^skip$/i }));

    await screen.findByRole("heading", { name: /review your new website details/i });
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body.get("payload"));
    expect(payload.social_links).toBeUndefined();
  });

  it("returns to the survey from the read-only review with answers retained", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
          author_url: `/authors/${STORED_AUTHOR.id}`,
          books_url: `/authors/${STORED_AUTHOR.id}/books`,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_AUTHOR,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_BOOKS,
      });
    renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers({
        social_goodreads: "https://goodreads.com/author/123",
      }),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /continue/i }));
    await screen.findByRole("heading", { name: /review your new website details/i });
    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(screen.getByRole("heading", { name: /where can readers follow you/i })).toBeVisible();
    expect(screen.getByLabelText(/goodreads/i)).toHaveValue(
      "https://goodreads.com/author/123",
    );
  });

  it("calls the no-op generate endpoint with the persisted author ID", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
          author_url: `/authors/${STORED_AUTHOR.id}`,
          books_url: `/authors/${STORED_AUTHOR.id}/books`,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_AUTHOR,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => STORED_BOOKS,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          author_id: STORED_AUTHOR.id,
        }),
      });
    renderApp({
      initialStepId: "social_links",
      initialAnswers: requiredAnswers(),
      initialBooks: [completeBook()],
    });

    await user.click(screen.getByRole("button", { name: /continue/i }));
    await screen.findByRole("heading", { name: /review your new website details/i });
    await user.click(screen.getByRole("button", { name: /generate site/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(fetchMock.mock.calls[3][0]).toBe("/generate");
    expect(fetchMock.mock.calls[3][1]).toMatchObject({
      method: "POST",
      headers: expect.objectContaining({ "Content-Type": "application/json" }),
      body: JSON.stringify({ author_id: STORED_AUTHOR.id }),
    });
    expect(await screen.findByText(/generation endpoint was called successfully/i)).toBeVisible();
  });
});
