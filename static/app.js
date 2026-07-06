const MAX_TAGS = 10;
const NONE_ID = "__none__";
const WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"];
const PERIODS = ["period11", "period12", "lunchtime"];
const PERIOD_LABELS = { period11: "P11", period12: "P12", lunchtime: "Lunch" };

const state = {
  selectedTags: new Set(),
  blockedSlots: new Set(),
  quizSession: null,
  quizPendingSelections: new Set(),
  quizHistory: [],
  mode: "manual",
};

const els = {
  tagGrid: document.getElementById("tag-grid"),
  tagCount: document.getElementById("tag-count"),
  selectedTags: document.getElementById("selected-tags"),
  manualTagWarning: document.getElementById("manual-tag-warning"),
  quizTagWarning: document.getElementById("quiz-tag-warning"),
  slotGrid: document.getElementById("slot-grid"),
  manualPanel: document.getElementById("manual-panel"),
  quizPanel: document.getElementById("quiz-panel"),
  quizQuestion: document.getElementById("quiz-question"),
  quizHint: document.getElementById("quiz-hint"),
  quizOptions: document.getElementById("quiz-options"),
  quizContinue: document.getElementById("quiz-continue"),
  quizBack: document.getElementById("quiz-back"),
  quizRestart: document.getElementById("quiz-restart"),
  resultsSection: document.getElementById("results-section"),
  resultsSummary: document.getElementById("results-summary"),
  results: document.getElementById("results"),
  error: document.getElementById("error"),
};

function showError(message) {
  els.error.textContent = message;
  els.error.classList.remove("hidden");
}

function clearError() {
  els.error.textContent = "";
  els.error.classList.add("hidden");
}

function formatMeeting(day, period) {
  const days = {
    monday: "Mon",
    tuesday: "Tue",
    wednesday: "Wed",
    thursday: "Thu",
    friday: "Fri",
  };
  const periods = {
    period11: "Period 11",
    period12: "Period 12",
    lunchtime: "Lunch",
    period13: "Period 13",
  };
  return `${days[day] || day} · ${periods[period] || period}`;
}

function updateTagLimitWarnings() {
  const atLimit = state.selectedTags.size >= MAX_TAGS;
  els.manualTagWarning?.classList.toggle("hidden", !atLimit);
  els.quizTagWarning?.classList.toggle("hidden", !atLimit);
}

function updateSelectedDisplay() {
  const tags = [...state.selectedTags];
  const text = tags.length ? tags.join(", ") : "none";
  els.selectedTags.textContent = text;
  els.tagCount.textContent = `${tags.length} / ${MAX_TAGS} selected`;

  document.querySelectorAll(".tag-chip").forEach((btn) => {
    btn.classList.toggle("selected", state.selectedTags.has(btn.dataset.tag));
    btn.disabled =
      !state.selectedTags.has(btn.dataset.tag) && state.selectedTags.size >= MAX_TAGS;
  });

  updateTagLimitWarnings();
}

function clearTags() {
  state.selectedTags.clear();
  updateSelectedDisplay();
  clearError();
}

function toggleTag(tag) {
  if (state.selectedTags.has(tag)) {
    state.selectedTags.delete(tag);
  } else if (state.selectedTags.size < MAX_TAGS) {
    state.selectedTags.add(tag);
  }
  updateSelectedDisplay();
}

function addQuizTags(tags) {
  let addedAny = false;
  for (const tag of tags) {
    if (state.selectedTags.size >= MAX_TAGS) break;
    if (!state.selectedTags.has(tag)) {
      state.selectedTags.add(tag);
      addedAny = true;
    }
  }
  updateSelectedDisplay();
  if (tags.length && !addedAny && state.selectedTags.size >= MAX_TAGS) {
    showError(`Maximum ${MAX_TAGS} tags reached. Clear tags to add more.`);
  } else {
    clearError();
  }
}

async function loadTags() {
  const res = await fetch("/api/tags");
  const data = await res.json();
  els.tagGrid.innerHTML = "";
  data.tags.forEach(({ id, label }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tag-chip";
    btn.dataset.tag = id;
    btn.textContent = label;
    btn.addEventListener("click", () => toggleTag(id));
    els.tagGrid.appendChild(btn);
  });
  updateSelectedDisplay();
}

function loadSlots() {
  if (!els.slotGrid) return;

  els.slotGrid.innerHTML = "";

  const header = document.createElement("div");
  header.className = "slot-row slot-header";
  header.innerHTML = "<span></span>";
  PERIODS.forEach((period) => {
    const label = document.createElement("span");
    label.textContent = PERIOD_LABELS[period] || period;
    header.appendChild(label);
  });
  els.slotGrid.appendChild(header);

  WEEKDAYS.forEach((day) => {
    const row = document.createElement("div");
    row.className = "slot-row";
    const dayLabel = document.createElement("span");
    dayLabel.className = "slot-day";
    dayLabel.textContent = day.charAt(0).toUpperCase() + day.slice(1, 3);
    row.appendChild(dayLabel);

    PERIODS.forEach((period) => {
      const id = `${day}:${period}`;
      const label = document.createElement("label");
      label.className = "slot-cell";
      label.title = `${dayLabel.textContent} · ${PERIOD_LABELS[period]}`;
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = id;
      input.addEventListener("change", () => {
        if (input.checked) state.blockedSlots.add(id);
        else state.blockedSlots.delete(id);
      });
      label.appendChild(input);
      row.appendChild(label);
    });
    els.slotGrid.appendChild(row);
  });
}

async function postQuiz(body) {
  const res = await fetch("/api/quiz", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    showError(data.error || "Quiz failed.");
    return null;
  }
  return data;
}

function bindQuizCheckbox(input, opt) {
  input.addEventListener("change", () => {
    const noneInput = els.quizOptions.querySelector(`input[value="${NONE_ID}"]`);
    const otherInputs = [...els.quizOptions.querySelectorAll('input[type="checkbox"]')].filter(
      (el) => el.value !== NONE_ID
    );

    if (opt.is_none) {
      if (input.checked) {
        state.quizPendingSelections.clear();
        state.quizPendingSelections.add(NONE_ID);
        otherInputs.forEach((el) => {
          el.checked = false;
        });
      } else {
        state.quizPendingSelections.delete(NONE_ID);
      }
      return;
    }

    if (input.checked) {
      if (noneInput) noneInput.checked = false;
      state.quizPendingSelections.delete(NONE_ID);
      state.quizPendingSelections.add(opt.id);
    } else {
      state.quizPendingSelections.delete(opt.id);
    }
  });
}

function renderQuizStep(step) {
  els.quizQuestion.textContent = step.question;
  els.quizHint.textContent =
    step.phase === "complete"
      ? "Your tags are kept. Answer more questions or click Find clubs."
      : "Select one or more, then click Continue. Choose None to use the parent category instead.";
  els.quizOptions.innerHTML = "";
  state.quizPendingSelections.clear();
  updateTagLimitWarnings();

  if (step.phase === "complete") {
    els.quizContinue.classList.add("hidden");
    els.quizBack.disabled = true;
    setTimeout(() => initQuiz({ keepHistory: false }), 600);
    return;
  }

  els.quizContinue.classList.remove("hidden");

  step.options.forEach((opt) => {
    const label = document.createElement("label");
    label.className = opt.is_none ? "quiz-check quiz-none" : "quiz-check";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = opt.id;
    bindQuizCheckbox(input, opt);
    label.appendChild(input);
    label.appendChild(document.createTextNode(opt.label));
    els.quizOptions.appendChild(label);
  });

  els.quizBack.disabled = state.quizHistory.length === 0;
}

async function initQuiz({ keepHistory = false } = {}) {
  if (!keepHistory) {
    state.quizHistory = [];
  }
  state.quizPendingSelections.clear();
  const res = await fetch("/api/quiz");
  const step = await res.json();
  state.quizSession = step.session;
  renderQuizStep(step);
}

async function continueQuiz() {
  if (!state.quizPendingSelections.size) {
    showError("Select at least one option.");
    return;
  }
  state.quizHistory.push(JSON.parse(JSON.stringify(state.quizSession)));
  const data = await postQuiz({
    session: state.quizSession,
    action: "continue",
    selections: [...state.quizPendingSelections],
  });
  if (!data) return;
  state.quizSession = data.session;
  if (data.tags_added?.length) addQuizTags(data.tags_added);
  renderQuizStep(data);
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.mode === mode);
  });
  els.manualPanel.classList.toggle("hidden", mode !== "manual");
  els.quizPanel.classList.toggle("hidden", mode !== "quiz");
  if (mode === "quiz" && !state.quizSession) initQuiz();
}

async function recommend() {
  clearError();
  const tags = [...state.selectedTags];
  if (!tags.length) {
    showError("Select at least one interest tag.");
    return;
  }

  const res = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tags,
      blocked_slots: [...state.blockedSlots],
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    showError(data.error || "Recommendation failed.");
    return;
  }

  els.resultsSection.classList.remove("hidden");
  if (data.count === 0) {
    els.resultsSummary.textContent =
      "No clubs matched your filters. Try fewer blocked times or different tags.";
    els.results.innerHTML = "";
    return;
  }

  const above = data.above_threshold || 0;
  const summary =
    above >= data.count
      ? `${data.count} club${data.count === 1 ? "" : "s"} (all above 50%).`
      : `${data.count} club${data.count === 1 ? "" : "s"} (${above} above 50%, rest fill minimum of ${data.min_results}).`;
  els.resultsSummary.textContent = summary;

  els.results.innerHTML = data.results
    .map((club, i) => {
      const scoreNote = club.above_threshold ? "" : ' <span class="below">below 50%</span>';
      const description = club.description
        ? `<details class="club-description">
             <summary>Description</summary>
             <p>${escapeHtml(club.description)}</p>
           </details>`
        : "";
      return `
      <article class="card">
        <h3>${i + 1}. ${escapeHtml(club.name)}</h3>
        <p class="score">Final score: ${club.final_score_pct}%${scoreNote}</p>
        <p>${escapeHtml(club.category)} · ${club.member_count} members · ${escapeHtml(formatMeeting(club.day, club.period))}</p>
        <p><strong>Matching tags:</strong> ${escapeHtml(club.matching_tags.join(", ") || "None")}</p>
        <p>${escapeHtml(club.explanation)}</p>
        ${description}
      </article>`;
    })
    .join("");
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function clearAll() {
  clearTags();
  state.blockedSlots.clear();
  state.quizSession = null;
  state.quizHistory = [];
  document.querySelectorAll("#slot-grid input").forEach((input) => {
    input.checked = false;
  });
  els.resultsSection.classList.add("hidden");
  clearError();
  if (state.mode === "quiz") initQuiz();
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => setMode(tab.dataset.mode));
});

document.getElementById("clear-tags-btn").addEventListener("click", clearTags);
document.getElementById("quiz-clear-tags").addEventListener("click", clearTags);
els.quizContinue.addEventListener("click", continueQuiz);
els.quizBack.addEventListener("click", async () => {
  const prev = state.quizHistory.pop();
  if (!prev) return;
  state.quizSession = prev;
  const step = await postQuiz({ session: prev, action: "status" });
  if (step) renderQuizStep(step);
});
els.quizRestart.addEventListener("click", () => initQuiz());
document.getElementById("recommend-btn").addEventListener("click", recommend);
document.getElementById("clear-btn").addEventListener("click", clearAll);

loadSlots();
loadTags().catch((err) => showError(`Failed to load tags: ${err.message}`));
