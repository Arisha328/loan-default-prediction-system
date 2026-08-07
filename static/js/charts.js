/* charts.js — Chart.js instantiations for dashboard & admin pages.
   Reads data from JSON <script> tags rendered by Jinja so no inline
   Python-in-JS string building is needed. */

function chartTextColor() {
  const styles = getComputedStyle(document.documentElement);
  return styles.getPropertyValue("--text-muted").trim() || "#5B6482";
}
function chartGridColor() {
  const styles = getComputedStyle(document.documentElement);
  return styles.getPropertyValue("--border").trim() || "#E1E5F0";
}

function baseOptions(extra = {}) {
  return Object.assign(
    {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: chartTextColor(), font: { family: "Inter" } },
        },
      },
      scales: {
        x: { ticks: { color: chartTextColor() }, grid: { color: "transparent" } },
        y: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() } },
      },
    },
    extra
  );
}

function readJSON(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch (e) {
    return null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  renderRiskPie();
  renderMonthlyTrend();
  renderAgeDistribution();
  renderIncomeDistribution();
  renderCreditScoreDistribution();
  renderDefaultDistribution();
});

function renderRiskPie() {
  const ctx = document.getElementById("riskPieChart");
  const data = readJSON("riskPieData");
  if (!ctx || !data) return;
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Low Risk", "High Risk"],
      datasets: [
        {
          data: [data.low_risk, data.high_risk],
          backgroundColor: ["#1FAE7A", "#E5484D"],
          borderWidth: 0,
        },
      ],
    },
    options: baseOptions({ cutout: "68%", scales: {} }),
  });
}

function renderMonthlyTrend() {
  const ctx = document.getElementById("monthlyTrendChart");
  const data = readJSON("monthlyTrendData");
  if (!ctx || !data) return;
  new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Predictions",
          data: data.values,
          borderColor: "#3E6BFF",
          backgroundColor: "rgba(62,107,255,0.12)",
          tension: 0.35,
          fill: true,
          pointRadius: 3,
        },
      ],
    },
    options: baseOptions(),
  });
}

function renderAgeDistribution() {
  const ctx = document.getElementById("ageDistChart");
  const data = readJSON("ageDistData");
  if (!ctx || !data) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.edges,
      datasets: [{ label: "Applicants", data: data.bins, backgroundColor: "#3E6BFF", borderRadius: 6 }],
    },
    options: baseOptions({ plugins: { legend: { display: false } } }),
  });
}

function renderIncomeDistribution() {
  const ctx = document.getElementById("incomeDistChart");
  const data = readJSON("incomeDistData");
  if (!ctx || !data) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.edges,
      datasets: [{ label: "Applicants", data: data.bins, backgroundColor: "#F2A93B", borderRadius: 6 }],
    },
    options: baseOptions({ plugins: { legend: { display: false } } }),
  });
}

function renderCreditScoreDistribution() {
  const ctx = document.getElementById("creditScoreDistChart");
  const data = readJSON("creditScoreDistData");
  if (!ctx || !data) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.edges,
      datasets: [{ label: "Applicants", data: data.bins, backgroundColor: "#1FAE7A", borderRadius: 6 }],
    },
    options: baseOptions({ plugins: { legend: { display: false } } }),
  });
}

function renderDefaultDistribution() {
  const ctx = document.getElementById("defaultDistChart");
  const data = readJSON("defaultDistData");
  if (!ctx || !data) return;
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["No Default", "Default"],
      datasets: [{ data: data.counts, backgroundColor: ["#1FAE7A", "#E5484D"] }],
    },
    options: baseOptions({ scales: {} }),
  });
}
