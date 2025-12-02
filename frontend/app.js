// frontend/app.js
// Simple client for the backend /analyze endpoint.
// Expects backend at the same host + port (change BASE_URL if needed).

const BASE_URL = "https://data-analyzer-agents.onrender.com"; // — leave blank to use same origin
const analyzeForm = document.getElementById("analyzeForm");
const fileInput = document.getElementById("fileInput");
const questionInput = document.getElementById("questionInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusEl = document.getElementById("status");
const resultsSection = document.getElementById("results");
const summaryEl = document.getElementById("summary");
const dataIssuesEl = document.getElementById("dataIssues");
const trendsEl = document.getElementById("trends");
const answerEl = document.getElementById("answer");

function showStatus(text) {
  statusEl.textContent = text;
}

function resetResults() {
  resultsSection.classList.add("hidden");
  summaryEl.textContent = "";
  dataIssuesEl.textContent = "";
  trendsEl.textContent = "";
  answerEl.textContent = "";
}

analyzeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  resetResults();

  const file = fileInput.files[0];
  if (!file) {
    alert("Please choose a CSV or Excel file to upload.");
    return;
  }

  const question = questionInput.value || "What are the most important insights from this data?";

  const formData = new FormData();
  formData.append("file", file);
  formData.append("question", question);

  showStatus("Uploading and analyzing...");
  analyzeBtn.disabled = true;

  try {
    const res = await fetch((BASE_URL || "") + "/analyze", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Server returned ${res.status}: ${text}`);
    }

    const data = await res.json();

    // Fill UI
    resultsSection.classList.remove("hidden");
    summaryEl.textContent = data.summary || "(no summary returned)";
    dataIssuesEl.textContent = data.data_issues || "(no data issues returned)";
    trendsEl.textContent = data.trends || "(no trends returned)";
    answerEl.textContent = data.answer_to_question || "(no answer returned)";

    showStatus("Analysis complete.");
  } catch (err) {
    console.error(err);
    showStatus("Error: " + err.message);
    alert("Analysis failed: " + err.message);
  } finally {
    analyzeBtn.disabled = false;
  }
});
