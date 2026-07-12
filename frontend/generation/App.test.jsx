import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import App, { resolveWebsiteBriefId } from "./App";


const BRIEF_ID = "11111111-1111-4111-8111-111111111111";
const JOB_ID = "33333333-3333-4333-8333-333333333333";

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
  vi.useRealTimers();
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

  it("posts to the generation endpoint with the correct author ID on generate", async () => {
    const user = userEvent.setup();
    setLocation(`/?brief=${BRIEF_ID}`);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(WEBSITE_BRIEF))
      .mockResolvedValue(jsonResponse({ job_id: JOB_ID }));

    render(<App />);
    await screen.findByRole("heading", { name: /generate jane doe's website/i });
    await user.click(screen.getByRole("button", { name: /generate site/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/generate",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ author_id: BRIEF_ID }),
        }),
      );
    });
  });

  it("shows generating message while polling after a successful POST", async () => {
    const user = userEvent.setup();
    setLocation(`/?brief=${BRIEF_ID}`);
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(WEBSITE_BRIEF))
      .mockResolvedValue(jsonResponse({ job_id: JOB_ID }));

    render(<App />);
    await screen.findByRole("heading", { name: /generate jane doe's website/i });
    await user.click(screen.getByRole("button", { name: /generate site/i }));

    expect(await screen.findByText(/generating your website/i)).toBeVisible();
  });

  it("shows success message when job status is complete", async () => {
    vi.useFakeTimers();
    setLocation(`/?brief=${BRIEF_ID}`);
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(WEBSITE_BRIEF))
      .mockResolvedValueOnce(jsonResponse({ job_id: JOB_ID }))
      .mockResolvedValue(jsonResponse({ status: "complete", preview_url: null }));

    render(<App />);

    // Flush the brief fetch + React state update
    await act(() => vi.runAllTimersAsync());
    expect(screen.getByRole("heading", { name: /generate jane doe's website/i })).toBeVisible();

    // Click generate, flush the POST fetch + React state update
    await act(async () => {
      screen.getByRole("button", { name: /generate site/i }).click();
      await vi.runAllTimersAsync();
    });

    // Advance past the 3-second poll interval; flush the status fetch + React state update
    await act(() => vi.advanceTimersByTimeAsync(3100));

    expect(screen.getByText(/generated successfully/i)).toBeVisible();
  });

  it("shows error message when job status is failed", async () => {
    vi.useFakeTimers();
    setLocation(`/?brief=${BRIEF_ID}`);
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(WEBSITE_BRIEF))
      .mockResolvedValueOnce(jsonResponse({ job_id: JOB_ID }))
      .mockResolvedValue(
        jsonResponse({ status: "failed", error_message: "WP-CLI not found." }),
      );

    render(<App />);
    await act(() => vi.runAllTimersAsync());
    expect(screen.getByRole("heading", { name: /generate jane doe's website/i })).toBeVisible();

    await act(async () => {
      screen.getByRole("button", { name: /generate site/i }).click();
      await vi.runAllTimersAsync();
    });

    await act(() => vi.advanceTimersByTimeAsync(3100));

    expect(screen.getByText("WP-CLI not found.")).toBeVisible();
  });

  it("disables the generate button while generating", async () => {
    const user = userEvent.setup();
    setLocation(`/?brief=${BRIEF_ID}`);
    // Status endpoint returns pending indefinitely to keep the button disabled
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(WEBSITE_BRIEF))
      .mockResolvedValueOnce(jsonResponse({ job_id: JOB_ID }))
      .mockResolvedValue(jsonResponse({ status: "pending" }));

    render(<App />);
    await screen.findByRole("heading", { name: /generate jane doe's website/i });
    await user.click(screen.getByRole("button", { name: /generate site/i }));

    await screen.findByText(/generating your website/i);
    expect(screen.getByRole("button", { name: /generate site/i })).toBeDisabled();
  });

  it("shows an error when the generation endpoint fails", async () => {
    const user = userEvent.setup();
    setLocation(`/?brief=${BRIEF_ID}`);
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(WEBSITE_BRIEF))
      .mockResolvedValueOnce(
        jsonResponse({ message: "A generation job is already in progress." }, false),
      );

    render(<App />);
    await screen.findByRole("heading", { name: /generate jane doe's website/i });
    await user.click(screen.getByRole("button", { name: /generate site/i }));

    expect(
      await screen.findByText(/a generation job is already in progress/i),
    ).toBeVisible();
  });
});
