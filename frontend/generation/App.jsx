import { useEffect, useRef, useState } from "react";


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


export function resolveWebsiteBriefId() {
  const params = new URLSearchParams(window.location.search);
  const queryBrief = params.get("brief");
  if (queryBrief) return queryBrief;
  return document.getElementById("generation-root")?.dataset.briefId || "";
}


export default function App() {
  const [briefId] = useState(resolveWebsiteBriefId);
  const [brief, setBrief] = useState(null);
  const [loadState, setLoadState] = useState({
    type: briefId ? "loading" : "error",
    message: briefId ? "Loading Website brief..." : "Missing Website brief ID.",
  });
  const [generateState, setGenerateState] = useState({
    type: "idle",
    jobId: null,
    message: "",
    previewUrl: null,
  });
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    if (!briefId) return undefined;

    let active = true;
    async function loadBrief() {
      try {
        const response = await fetch(`/website-briefs/${briefId}`);
        const data = await response.json();
        if (!active) return;
        if (!response.ok) {
          setLoadState({
            type: "error",
            message: data.message || "We could not load this Website brief.",
          });
          return;
        }
        setBrief(data);
        setLoadState({ type: "success", message: "" });
      } catch {
        if (!active) return;
        setLoadState({
          type: "error",
          message: "We could not reach the server. Check Django and try again.",
        });
      }
    }

    loadBrief();
    return () => {
      active = false;
    };
  }, [briefId]);

  // Poll /generate/<jobId>/status every 3 seconds while the job is active.
  useEffect(() => {
    if (generateState.type !== "polling" || !generateState.jobId) return undefined;

    const jobId = generateState.jobId;
    let active = true;

    async function pollStatus() {
      if (!active) return;
      try {
        const response = await fetch(`/generate/${jobId}/status`);
        const data = await response.json();
        if (!active) return;
        if (!response.ok) {
          clearInterval(pollIntervalRef.current);
          setGenerateState({
            type: "failed",
            jobId: null,
            message: data.message || "Generation failed.",
            previewUrl: null,
          });
          return;
        }
        if (data.status === "complete") {
          clearInterval(pollIntervalRef.current);
          setGenerateState({
            type: "complete",
            jobId: null,
            message: "Your website has been generated successfully!",
            previewUrl: data.preview_url,
          });
        } else if (data.status === "failed") {
          clearInterval(pollIntervalRef.current);
          setGenerateState({
            type: "failed",
            jobId: null,
            message: data.error_message || "Generation failed.",
            previewUrl: null,
          });
        }
        // pending/running: keep polling
      } catch {
        if (!active) return;
        clearInterval(pollIntervalRef.current);
        setGenerateState({
          type: "failed",
          jobId: null,
          message: "We could not reach the server. Check Django and try again.",
          previewUrl: null,
        });
      }
    }

    pollIntervalRef.current = setInterval(pollStatus, 3000);

    return () => {
      active = false;
      clearInterval(pollIntervalRef.current);
    };
  }, [generateState.type, generateState.jobId]);

  async function generateSite() {
    const isActive = generateState.type === "starting" || generateState.type === "polling";
    if (!brief || isActive) return;
    setGenerateState({ type: "starting", jobId: null, message: "Starting generation...", previewUrl: null });
    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: csrfHeaders(true),
        body: JSON.stringify({ author_id: brief.id }),
      });
      const data = await response.json();
      if (!response.ok) {
        setGenerateState({
          type: "failed",
          jobId: null,
          message: data.message || "We could not start generation.",
          previewUrl: null,
        });
        return;
      }
      setGenerateState({
        type: "polling",
        jobId: data.job_id,
        message: "Generating your website...",
        previewUrl: null,
      });
    } catch {
      setGenerateState({
        type: "failed",
        jobId: null,
        message: "We could not reach the server. Check Django and try again.",
        previewUrl: null,
      });
    }
  }

  if (loadState.type === "loading") {
    return (
      <main className="onboarding-shell">
        <p className="status-message">{loadState.message}</p>
      </main>
    );
  }

  if (loadState.type === "error") {
    return (
      <main className="onboarding-shell">
        <p className="error-message">{loadState.message}</p>
      </main>
    );
  }

  const isGenerating = generateState.type === "starting" || generateState.type === "polling";

  return (
    <main className="onboarding-shell">
      <form className="onboarding-card" onSubmit={(event) => event.preventDefault()}>
        <div className="step-header">
          <p className="step-kicker">Website brief</p>
          <h1>Generate {brief.author.name}&apos;s website</h1>
          <p>{brief.author.site_domain}</p>
        </div>

        <section aria-labelledby="generation-books-heading">
          <h2 id="generation-books-heading">Books</h2>
          <ul>
            {brief.books.map((book) => (
              <li key={book.id}>{book.title}</li>
            ))}
          </ul>
        </section>

        <div className="actions">
          <button
            type="button"
            className="button-primary"
            data-testid="generate-site"
            disabled={isGenerating}
            onClick={generateSite}
          >
            Generate site
          </button>
        </div>

        {generateState.message ? (
          <p className={`${generateState.type}-message`}>{generateState.message}</p>
        ) : null}
      </form>
    </main>
  );
}
