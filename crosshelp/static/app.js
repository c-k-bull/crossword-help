const API_BASE = "/api"

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

        renderResults(data.results, mode);
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
}

function setLoading(isLoading) {
    els.loading.classList.toggle("hidden", !isLoading);
    els.searchBtns.forEach(btn => btn.disabled = isLoading);
}

function showError(message) {
    els.error.textContent = message;
    els.error.classList.remove("hidden");
}