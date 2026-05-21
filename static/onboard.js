/* ─── Genre Tags ──────────────────────────────────────────── */

let genres = [];

const genreContainer = document.getElementById("genre-container");
const genreInput = document.getElementById("genre-input");
const genreHidden = document.getElementById("genre-values");

function addGenre(value) {
  const val = value.trim().replace(/,$/, "");
  if (val && !genres.includes(val)) {
    genres.push(val);
    renderGenreTags();
  }
  genreInput.value = "";
}

function removeGenre(index) {
  genres.splice(index, 1);
  renderGenreTags();
}

function renderGenreTags() {
  genreContainer.querySelectorAll(".tag").forEach((el) => el.remove());

  genres.forEach((g, i) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.innerHTML = `${escapeHtml(g)} <button type="button" class="tag-remove" aria-label="Remove ${escapeHtml(g)}">×</button>`;
    tag.querySelector("button").addEventListener("click", () => removeGenre(i));
    genreContainer.insertBefore(tag, genreInput);
  });

  genreHidden.value = genres.join(",");
}

genreInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === ",") {
    e.preventDefault();
    addGenre(genreInput.value);
  }
  // Backspace on empty input removes the last tag
  if (e.key === "Backspace" && genreInput.value === "" && genres.length > 0) {
    genres.pop();
    renderGenreTags();
  }
});

genreContainer.addEventListener("click", () => genreInput.focus());

/* ─── Color Picker Sync ───────────────────────────────────── */

// Keeps the color swatch picker and its companion hex text input in sync.
function setupColorSync(pickerId, hexInputId) {
  const picker = document.getElementById(pickerId);
  const hexInput = document.getElementById(hexInputId);

  picker.addEventListener("input", () => {
    hexInput.value = picker.value;
  });

  hexInput.addEventListener("input", () => {
    if (/^#[0-9a-fA-F]{6}$/.test(hexInput.value)) {
      picker.value = hexInput.value;
    }
  });
}

setupColorSync("primary_color", "primary_color_hex");
setupColorSync("secondary_color", "secondary_color_hex");

/* ─── Book Portfolio Rows ─────────────────────────────────── */

let bookCount = 1; // First row is already in the HTML

function addBook() {
  bookCount++;
  const row = document.createElement("div");
  row.className = "book-row";
  row.dataset.index = bookCount;
  // innerHTML is safe here because bookCount is an integer, not user input
  row.innerHTML = `
    <div class="book-row-header">
      <span class="book-row-label">Book ${bookCount}</span>
      <button type="button" class="btn-remove-book" onclick="removeBook(this)">Remove</button>
    </div>
    <div class="form-group">
      <label>Title</label>
      <input type="text" name="book_title[]" placeholder="The Midnight Code">
    </div>
    <div class="form-group">
      <label>Cover Image</label>
      <input type="file" name="book_cover[]" accept="image/*">
    </div>
    <div class="form-group">
      <label>Description</label>
      <textarea name="book_description[]" rows="2"
                placeholder="A brief description of the book..."></textarea>
    </div>
    <div class="form-group">
      <label>Buy Links <span class="hint">— Amazon, Barnes &amp; Noble, etc.</span></label>
      <input type="text" name="book_buy_links[]"
             placeholder="https://amazon.com/dp/..., https://barnesandnoble.com/...">
    </div>
  `;
  document.getElementById("books-container").appendChild(row);
  updateRemoveButtons();
}

function removeBook(button) {
  button.closest(".book-row").remove();
  renumberBooks();
  updateRemoveButtons();
}

function renumberBooks() {
  document.querySelectorAll(".book-row").forEach((row, i) => {
    row.querySelector(".book-row-label").textContent = `Book ${i + 1}`;
  });
  bookCount = document.querySelectorAll(".book-row").length;
}

// Hides the Remove button when only one book row remains (can't remove the last one)
function updateRemoveButtons() {
  const rows = document.querySelectorAll(".book-row");
  rows.forEach((row) => {
    const btn = row.querySelector(".btn-remove-book");
    if (btn) btn.style.display = rows.length > 1 ? "inline-flex" : "none";
  });
}

/* ─── Status Messages ─────────────────────────────────────── */

function showStatus(type, message) {
  const el = document.getElementById("status-message");
  el.className = `status status-${type}`;

  if (type === "error") {
    // Dismiss button only on errors; provisioning and success messages are informational
    el.innerHTML =
      `<button type="button" class="status-dismiss" onclick="dismissStatus()" aria-label="Dismiss">×</button>` +
      escapeHtml(message);
  } else {
    el.textContent = message;
  }

  el.classList.remove("hidden");
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function dismissStatus() {
  document.getElementById("status-message").classList.add("hidden");
}

/* ─── Form Validation ─────────────────────────────────────── */

function validateForm(form) {
  const requiredFields = form.querySelectorAll("[required]");
  for (const field of requiredFields) {
    if (!field.value.trim()) {
      field.focus();
      field.reportValidity(); // triggers browser's native validation bubble
      return false;
    }
  }
  return true;
}

/* ─── Form Submission ─────────────────────────────────────── */

document.getElementById("onboard-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!validateForm(e.target)) return;

  const submitBtn = document.getElementById("submit-btn");
  submitBtn.disabled = true;
  showStatus(
    "provisioning",
    "Provisioning your site — this typically takes 5–10 minutes. Please do not close this window."
  );

  try {
    const response = await fetch("/generate", {
      method: "POST",
      body: new FormData(e.target),
    });

    const data = await response.json();

    if (response.ok && data.status === "ok") {
      showStatus(
        "success",
        "Site provisioned successfully! Check email for WordPress login credentials and the live URL."
      );
      submitBtn.disabled = false;
    } else {
      showStatus("error", data.message || "An unexpected error occurred. Please try again.");
      submitBtn.disabled = false;
    }
  } catch (err) {
    showStatus("error", `Network error: ${err.message}. Please check your connection and try again.`);
    submitBtn.disabled = false;
  }
});

/* ─── Utility ─────────────────────────────────────────────── */

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
