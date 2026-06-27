const API_BASE = "/api"

let currentSearchId = null;

const els = {
    tabs: document.querySelectorAll(".tab"),
    forms: {
        pattern: document.getElementById("form-pattern"),
        clue: document.getElementById("form-clue"),
        synonym: document.getElementById("form-synonym"),
    },
    searchBtns: document.querySelectorAll(".search-btn"),
    loading: document.getElementById("loading"),
    error: document.getElementById("error"),
    resultList: document.getElementById("result-list"),
    feedbackContainer: document.getElementById("feedback-container"),
    feedbackLink: document.getElementById("feedback-link"),
    feedbackForm: document.getElementById("feedback-form"),
    correctAnswerInput: document.getElementById("correct-answer-input"),
    feedbackSubmit: document.getElementById("feedback-submit"),
    feedbackThanks: document.getElementById("feedback-thanks"),
};

// Tab switching
els.tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        const mode = tab.dataset.mode;
        els.tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        Object.entries(els.forms).forEach(([m, form]) => {
            form.classList.toggle("hidden", m !== mode);
        });
        clearResults();
    });
});

// Search button handlers
els.searchBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        const mode = btn.dataset.mode;
        handleSearch(mode);
    });
});

async function handleSearch(mode) {
    clearResults();
    setLoading(true);

    try {
        const payload = buildPayload(mode);
        const response = await fetch(`${API_BASE}/${mode}`, {
            method: "POST",
            headers: { "Content-type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (!response.ok) {
            showError(data.error || "Search failed");
            return;
        }

        currentSearchId = data.search_id;
        renderResults(data.results, mode);
        showFeedbackOption(data.results);
    } catch (err) {
        showError("Network error: " + err.message);
    } finally {
        setLoading(false);
    }
}

function buildPayload(mode) {
    if (mode === "pattern") {
        return {
            pattern: document.getElementById("pattern-input").value,
            min_score: parseInt(document.getElementById("pattern-min-score").value) || 0,
        };
    }
    if (mode === "clue") {
        return {
            clue: document.getElementById("clue-text").value,
            pattern: document.getElementById("clue-pattern").value,
        };
    }
    if (mode === "synonym") {
        return {
            meaning: document.getElementById("synonym-meaning").value,
            pattern: document.getElementById("synonym-pattern").value,
        };
    }
    return {};
}

function renderResults(results, mode) {
    if (!results || results.length === 0) {
        els.resultList.innerHTML = `<li class="empty-state">No results found.</li>`;
        return;
    }

    els.resultList.innerHTML = results.map(item => {
        const score = item.score;
        const scoreHtml = score === null || score === undefined
            ? ""
            : `<span class="score ${score >= 70 ? "high" : ""}">${score}</span>`;
        return `<li><span class="word">${item.word}</span>${scoreHtml}</li>`;
    }).join("");
}

function clearResults() {
    els.resultList.innerHTML = "";
    els.error.classList.add("hidden");
    els.error.textContent = "";
    els.feedbackContainer.classList.add("hidden");  
    currentSearchId = null;                        
}

function setLoading(isLoading) {
    els.loading.classList.toggle("hidden", !isLoading);
    els.searchBtns.forEach(btn => btn.disabled = isLoading);
}

function showError(message) {
    els.error.textContent = message;
    els.error.classList.remove("hidden");
}

function showFeedbackOption(results) {
    if (!currentSearchId || !results || results.length === 0) {
        els.feedbackContainer.classList.add("hidden");
        return;
    }
    els.feedbackContainer.classList.remove("hidden");
    els.feedbackForm.classList.add("hidden");
    els.feedbackLink.classList.remove("hidden");
    els.feedbackThanks.classList.add("hidden");
    els.correctAnswerInput.value = "";
}

els.feedbackLink.addEventListener("click", (e) => {
    e.preventDefault();
    els.feedbackLink.classList.add("hidden");
    els.feedbackForm.classList.remove("hidden");
    els.correctAnswerInput.focus();
});

els.feedbackSubmit.addEventListener("click", async () => {
    const corrected = els.correctAnswerInput.value.trim();
    if (!corrected) {
        return;
    }
    if (!currentSearchId) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/feedback`, {
            method: "POST",
            headers: { "Content-type": "application/json" },
            body: JSON.stringify({
                search_id: currentSearchId,
                corrected_answer: corrected,
            }),
        });
        if (response.ok) {
            els.feedbackForm.classList.add("hidden");
            els.feedbackThanks.classList.remove("hidden");
        } else {
            els.feedbackForm.classList.add("hidden");
            els.feedbackThanks.textContent = "Sorry — couldn't record that.";
            els.feedbackThanks.classList.remove("hidden");
        }
    } catch (err) {
        console.error("Feedback submit error:", err);
    }
});

els.correctAnswerInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        els.feedbackSubmit.click();
    }
});