import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import App, { buildPayload, parseBuyLinks } from "./App";


afterEach(() => {
  vi.restoreAllMocks();
});


describe("parseBuyLinks", () => {
  it("splits a comma-separated string into an array", () => {
    expect(parseBuyLinks("https://a.com, https://b.com")).toEqual([
      "https://a.com",
      "https://b.com",
    ]);
  });

  it("returns an empty array for empty input", () => {
    expect(parseBuyLinks("")).toEqual([]);
    expect(parseBuyLinks(undefined)).toEqual([]);
  });

  it("trims entries and drops blanks", () => {
    expect(parseBuyLinks(" https://a.com ,  , https://b.com ")).toEqual([
      "https://a.com",
      "https://b.com",
    ]);
  });
});


describe("buildPayload books handling", () => {
  const baseAnswers = {
    author_name: "Jane Doe",
    author_email: "jane@example.com",
    website_name: "Jane Doe Books",
  };

  it("omits the books key when no books are provided", () => {
    const payload = buildPayload(baseAnswers, []);
    expect(payload.books).toBeUndefined();
  });

  it("omits books with a blank title", () => {
    const payload = buildPayload(baseAnswers, [{ title: "  ", description: "", buy_links: "" }]);
    expect(payload.books).toBeUndefined();
  });

  it("includes a book with only a title", () => {
    const payload = buildPayload(baseAnswers, [{ title: "My Book", description: "", buy_links: "" }]);
    expect(payload.books).toEqual([{ title: "My Book" }]);
  });

  it("includes description and buy_links when provided", () => {
    const payload = buildPayload(baseAnswers, [
      { title: "My Book", description: "A great read.", buy_links: "https://buy.me/book" },
    ]);
    expect(payload.books).toEqual([
      { title: "My Book", description: "A great read.", buy_links: ["https://buy.me/book"] },
    ]);
  });
});


async function answerRequiredQuestions(user) {
  await user.type(screen.getByLabelText(/author name/i), "Jane Doe");
  await user.click(screen.getByRole("button", { name: /continue/i }));
  await user.type(screen.getByLabelText(/author email/i), "jane@example.com");
  await user.click(screen.getByRole("button", { name: /continue/i }));
  await user.type(screen.getByLabelText(/website name/i), "Jane Doe Books");
}


describe("onboarding wizard", () => {
  it("renders one question at a time with progress", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /what is your author name/i })).toBeVisible();
    expect(screen.getByText(/question 1 of/i)).toBeVisible();
    expect(screen.queryByLabelText(/author email/i)).not.toBeInTheDocument();
  });

  it("blocks navigation and shows an error for an empty required answer", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/author name is required/i);
    expect(screen.getByLabelText(/author name/i)).toHaveFocus();
  });

  it("validates email before advancing", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/author name/i), "Jane Doe");
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.type(screen.getByLabelText(/author email/i), "invalid");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/valid email/i);
  });

  it("retains answers when navigating backward", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText(/author name/i), "Jane Doe");
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(screen.getByLabelText(/author name/i)).toHaveValue("Jane Doe");
  });

  it("allows optional questions to be skipped", async () => {
    const user = userEvent.setup();
    render(<App />);

    await answerRequiredQuestions(user);
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getByRole("heading", { name: /tagline/i })).toBeVisible();
    expect(screen.getByRole("button", { name: /skip/i })).toBeVisible();

    await user.click(screen.getByRole("button", { name: /skip/i }));

    expect(screen.getByRole("heading", { name: /short bio/i })).toBeVisible();
  });

  it("rejects an invalid optional hex color", async () => {
    const user = userEvent.setup();
    render(<App initialStepId="primary_color" />);

    const input = screen.getByLabelText(/primary brand color/i);
    await user.clear(input);
    await user.type(input, "blue");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/six-digit hex color/i);
  });

  it("rejects an invalid optional social URL", async () => {
    const user = userEvent.setup();
    render(<App initialStepId="social_instagram" />);

    await user.type(screen.getByLabelText(/instagram/i), "instagram.com/janedoe");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(/http.*https/i);
  });

  it("submits normalized answers from the review step", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    render(
      <App
        initialStepId="review"
        initialAnswers={{
          author_name: "Jane Doe",
          author_email: "jane@example.com",
          website_name: "Jane Doe Books",
          genres: "Fantasy, Mystery",
          social_twitter: "https://x.com/janedoe",
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: /generate site/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    expect(fetchMock).toHaveBeenCalledWith(
      "/generate",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(payload).toMatchObject({
      author_name: "Jane Doe",
      genres: ["Fantasy", "Mystery"],
      social_links: { twitter: "https://x.com/janedoe" },
    });
    expect(await screen.findByRole("status")).toHaveTextContent(/information is valid/i);
  });

  it("shows server validation failures without losing answers", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      json: async () => ({
        message: "Please correct the highlighted fields.",
        errors: { author_email: "Enter a valid email address." },
      }),
    });
    render(
      <App
        initialStepId="review"
        initialAnswers={{
          author_name: "Jane Doe",
          author_email: "jane@example.com",
          website_name: "Jane Doe Books",
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: /generate site/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /please correct the highlighted fields/i,
    );
    expect(screen.getByText("Jane Doe Books")).toBeInTheDocument();
  });

  it("shows the book portfolio step and allows adding a book", async () => {
    const user = userEvent.setup();
    render(<App initialStepId="books" />);

    expect(screen.getByRole("heading", { name: /add your books/i })).toBeVisible();

    // Initially no book rows
    expect(screen.queryByLabelText(/^title$/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /add a book/i }));

    expect(screen.getByLabelText(/^title$/i)).toBeVisible();
  });

  it("can add and remove a book row", async () => {
    const user = userEvent.setup();
    render(<App initialStepId="books" />);

    await user.click(screen.getByRole("button", { name: /add a book/i }));
    expect(screen.getByLabelText(/^title$/i)).toBeVisible();

    await user.click(screen.getByRole("button", { name: /remove book 1/i }));
    expect(screen.queryByLabelText(/^title$/i)).not.toBeInTheDocument();
  });

  it("includes book data in the payload submitted from the review step", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });

    render(
      <App
        initialStepId="review"
        initialAnswers={{
          author_name: "Jane Doe",
          author_email: "jane@example.com",
          website_name: "Jane Doe Books",
        }}
        initialBooks={[
          { title: "The Midnight Code", description: "A thriller.", buy_links: "https://example.com/buy" },
        ]}
      />,
    );

    await user.click(screen.getByRole("button", { name: /generate site/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    const payload = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(payload.books).toEqual([
      { title: "The Midnight Code", description: "A thriller.", buy_links: ["https://example.com/buy"] },
    ]);
  });

  it("shows book titles in the review step summary", () => {
    render(
      <App
        initialStepId="review"
        initialAnswers={{
          author_name: "Jane Doe",
          author_email: "jane@example.com",
          website_name: "Jane Doe Books",
        }}
        initialBooks={[
          { title: "The Midnight Code", description: "", buy_links: "" },
          { title: "Ghost Signal", description: "", buy_links: "" },
        ]}
      />,
    );

    expect(screen.getByText(/The Midnight Code.*Ghost Signal/i)).toBeInTheDocument();
  });

  it("submits when the form element receives an Enter submit event", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    render(
      <App
        initialStepId="review"
        initialAnswers={{
          author_name: "Jane Doe",
          author_email: "jane@example.com",
          website_name: "Jane Doe Books",
        }}
      />,
    );

    fireEvent.submit(screen.getByRole("form", { name: /author website onboarding/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
  });
});
