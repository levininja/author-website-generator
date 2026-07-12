import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import App, { resolveWebsiteBriefId } from "./App";


const BRIEF_ID = "11111111-1111-4111-8111-111111111111";

const WEBSITE_BRIEF = {
  id: BRIEF_ID,
  author: {
    id: BRIEF_ID,
    name: "Jane Doe",
    site_domain: "janedoe.com",
    selected_template: "classic",
  },
  books: [
    {
      id: "22222222-2222-4222-8222-222222222222",
      title: "The Midnight Code",
    },
  ],
  generation: {
    status: "ready",
  },
};


function jsonResponse(body, ok = true) {
  return {
    ok,
    json: async () => body,
  };
}


function setLocation(path) {
  window.history.pushState({}, "", path);
}


afterEach(() => {
  vi.restoreAllMocks();
  document.body.innerHTML = "";
  setLocation("/");
});


describe("website brief resolution", () => {
  it("prefers the brief query parameter for Vite development", () => {
    document.body.innerHTML = (
      `<div id="generation-root" data-brief-id="mounted-id"></div>`
    );
    setLocation(`/?brief=${BRIEF_ID}`);

    expect(resolveWebsiteBriefId()).toBe(BRIEF_ID);
  });

  it("falls back to the Django mount data attribute", () => {
    document.body.innerHTML = (
      `<div id="generation-root" data-brief-id="${BRIEF_ID}"></div>`
    );

    expect(resolveWebsiteBriefId()).toBe(BRIEF_ID);
  });
});


describe("Generation App", () => {
  it("loads a website brief from Django using the resolved brief ID", async () => {
    setLocation(`/?brief=${BRIEF_ID}`);
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(WEBSITE_BRIEF),
    );

    render(<App />);

    expect(screen.getByText(/loading website brief/i)).toBeVisible();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(`/website-briefs/${BRIEF_ID}`);
    });
    expect(
      await screen.findByRole("heading", { name: /generate jane doe's website/i }),
    ).toBeVisible();
    expect(screen.getByText("The Midnight Code")).toBeVisible();
  });

  it("shows a helpful error when no website brief ID is available", () => {
    render(<App />);

    expect(screen.getByText(/missing website brief id/i)).toBeVisible();
  });

  it("shows a server error when the website brief cannot be loaded", async () => {
    setLocation(`/?brief=${BRIEF_ID}`);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ message: "Website brief not found." }, false),
    );

    render(<App />);

    expect(await screen.findByText("Website brief not found.")).toBeVisible();
  });

  it("calls the generation endpoint for the loaded website brief", async () => {
    const user = userEvent.setup();
    setLocation(`/?brief=${BRIEF_ID}`);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(WEBSITE_BRIEF))
      .mockResolvedValueOnce(jsonResponse({ status: "ok", author_id: BRIEF_ID }));

    render(<App />);

    await screen.findByRole("heading", { name: /generate jane doe's website/i });
    await user.click(screen.getByRole("button", { name: /generate site/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/generate",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ author_id: BRIEF_ID }),
        }),
      );
    });
    expect(screen.getByText(/generation endpoint was called successfully/i)).toBeVisible();
  });
});
