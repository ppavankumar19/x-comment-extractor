const form = document.getElementById("extract-form");
const submitButton = document.getElementById("submit");
const statusText = document.getElementById("status-text");
const progressText = document.getElementById("progress-text");
const commentsText = document.getElementById("comments-text");
const progressBar = document.getElementById("progress-bar");
const statusError = document.getElementById("status-error");
const resultsEl = document.getElementById("results");
const controlsEl = document.getElementById("controls");
const filterKeyword = document.getElementById("filter-keyword");
const exportJson = document.getElementById("export-json");
const exportMarkdown = document.getElementById("export-markdown");

let activeSessionId = null;
let activeResult = null;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  controlsEl.classList.add("hidden");
  resultsEl.innerHTML = "";
  activeResult = null;
  statusError.textContent = "";
  updateStatus({ status: "starting", progress: 0, total_comments: 0, error: null });

  const payload = {
    url: document.getElementById("url").value.trim(),
    max_comments: Number(document.getElementById("max-comments").value || 50),
    include_replies: document.getElementById("include-replies").checked,
    llm_annotate: document.getElementById("llm-annotate").checked,
    llm_backend: document.getElementById("llm-backend").value,
  };

  try {
    const response = await fetch("/extract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to start extraction");
    }

    activeSessionId = data.session_id;
    await pollStatus(activeSessionId);
  } catch (error) {
    updateStatus({ status: "error", progress: 100, total_comments: 0, error: error.message });
    submitButton.disabled = false;
  }
});

filterKeyword.addEventListener("input", renderResults);
exportJson.addEventListener("click", () => {
  if (activeSessionId) {
    window.open(`/export/${activeSessionId}?format=json`, "_blank");
  }
});

exportMarkdown.addEventListener("click", () => {
  if (activeSessionId) {
    window.open(`/export/${activeSessionId}?format=markdown`, "_blank");
  }
});

async function pollStatus(sessionId) {
  const interval = 2000;

  while (true) {
    const response = await fetch(`/status/${sessionId}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to fetch status");
    }

    updateStatus(data);

    if (data.status === "done") {
      await fetchResults(sessionId);
      submitButton.disabled = false;
      return;
    }

    if (data.status === "error") {
      submitButton.disabled = false;
      return;
    }

    await new Promise((resolve) => window.setTimeout(resolve, interval));
  }
}

async function fetchResults(sessionId) {
  const response = await fetch(`/results/${sessionId}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch results");
  }
  activeResult = data;
  controlsEl.classList.remove("hidden");
  renderResults();
}

function updateStatus(status) {
  statusText.textContent = status.status;
  progressText.textContent = `${status.progress}%`;
  commentsText.textContent = String(status.total_comments || 0);
  progressBar.style.width = `${status.progress || 0}%`;
  statusError.textContent = status.error || "";
}

function renderResults() {
  if (!activeResult) {
    resultsEl.innerHTML = '<div class="empty">Run an extraction to see comment cards.</div>';
    return;
  }

  const keyword = filterKeyword.value.trim().toLowerCase();
  const comments = activeResult.comments.filter((comment) => {
    if (!keyword) return true;
    return (
      comment.text.toLowerCase().includes(keyword) ||
      comment.author.username.toLowerCase().includes(keyword) ||
      comment.author.display_name.toLowerCase().includes(keyword) ||
      (comment.emails || []).some((e) => e.toLowerCase().includes(keyword)) ||
      (comment.links || []).some((l) => l.toLowerCase().includes(keyword))
    );
  });

  if (!comments.length) {
    resultsEl.innerHTML = '<div class="empty">No comments matched the current filters.</div>';
    return;
  }

  resultsEl.innerHTML = comments.map(renderComment).join("");
}

function renderComment(comment) {
  const resourceHtml = (comment.resources || [])
    .map(
      (resource) =>
        `<a class="resource" href="${escapeHtml(resource.url)}" target="_blank" rel="noreferrer">${escapeHtml(
          resource.type
        )}: ${escapeHtml(shorten(resource.url, 60))}</a>`
    )
    .join("");

  const emailHtml = (comment.emails || [])
    .map((email) => `<span class="email-chip">${escapeHtml(email)}</span>`)
    .join("");

  const linkHtml = (comment.links || [])
    .map(
      (link) =>
        `<a class="resource" href="${escapeHtml(link)}" target="_blank" rel="noreferrer">${escapeHtml(shorten(link, 60))}</a>`
    )
    .join("");

  const mentionHtml = (comment.mentions || [])
    .map(
      (handle) =>
        `<a class="mention-chip" href="https://x.com/${escapeHtml(handle)}" target="_blank" rel="noreferrer">@${escapeHtml(handle)}</a>`
    )
    .join("");

  const annotation = comment.annotation
    ? `
      <section class="annotation" data-sentiment="${escapeHtml(comment.annotation.sentiment)}">
        <div class="annotation-row">
          <strong>${escapeHtml(comment.annotation.sentiment)}</strong>
          <span class="meta">score ${escapeHtml(String(comment.annotation.sentiment_score))}</span>
        </div>
        <p>${escapeHtml(comment.annotation.summary)}</p>
        <div class="chip-list">
          ${(comment.annotation.topics || []).map((topic) => `<span class="chip">${escapeHtml(topic)}</span>`).join("")}
        </div>
      </section>
    `
    : "";

  return `
    <article class="card">
      <div class="card-header">
        <div class="author">
          ${
            comment.author.avatar_url
              ? `<img class="avatar" src="${escapeHtml(comment.author.avatar_url)}" alt="${escapeHtml(
                  comment.author.display_name
                )}" />`
              : `<div class="avatar"></div>`
          }
          <div>
            <h2>Comment #${escapeHtml(String(comment.index))}</h2>
            <h3>
              <a class="author-username" href="https://x.com/${escapeHtml(comment.author.username)}" target="_blank" rel="noreferrer">@${escapeHtml(comment.author.username)}</a>
              <span class="author-sep">·</span>
              <span class="author-name">${escapeHtml(comment.author.display_name)}</span>
              ${comment.author.verified ? '<span class="verified-badge" title="Verified">✓</span>' : ""}
            </h3>
            <p class="meta">${escapeHtml(formatTimestamp(comment.timestamp))}</p>
          </div>
        </div>
      </div>
      <p class="card-body">${comment.text_html || escapeHtml(comment.text || "")}</p>
      ${mentionHtml ? `<div class="entity-row"><span class="entity-label">mentions</span><div class="chip-list">${mentionHtml}</div></div>` : ""}
      ${emailHtml ? `<div class="entity-row"><span class="entity-label">emails</span><div class="chip-list">${emailHtml}</div></div>` : ""}
      ${linkHtml ? `<div class="entity-row"><span class="entity-label">links</span><div class="resource-list">${linkHtml}</div></div>` : ""}
      ${resourceHtml ? `<div class="resource-list">${resourceHtml}</div>` : ""}
      <div class="metric-row">
        <span class="meta">likes ${escapeHtml(String(comment.like_count))}</span>
        <span class="meta">retweets ${escapeHtml(String(comment.retweet_count))}</span>
        <span class="meta">replies ${escapeHtml(String(comment.reply_count))}</span>
        <span class="meta">bookmarks ${escapeHtml(String(comment.bookmark_count))}</span>
      </div>
      ${annotation}
    </article>
  `;
}

function formatTimestamp(timestamp) {
  if (!timestamp) {
    return "unknown time";
  }
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? "unknown time" : date.toLocaleString();
}

function shorten(value, length) {
  return value.length > length ? `${value.slice(0, length - 1)}…` : value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

renderResults();
