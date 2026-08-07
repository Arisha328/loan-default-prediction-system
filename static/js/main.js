/* main.js — theme toggle, navbar behavior, small UI helpers */

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initResetButton();
  initGaugeAnimation();
  initFadeIn();
});

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

function initThemeToggle() {
  const toggleBtn = document.getElementById("themeToggleBtn");
  if (!toggleBtn) return;

  toggleBtn.addEventListener("click", async () => {
    const html = document.documentElement;
    const current = html.getAttribute("data-theme") || "light";
    const next = current === "light" ? "dark" : "light";
    html.setAttribute("data-theme", next);
    updateToggleIcon(next);

    const isAuthenticated = document.body.dataset.authenticated === "true";
    if (isAuthenticated) {
      try {
        await fetch("/toggle-theme", {
          method: "POST",
          headers: { "X-CSRFToken": getCsrfToken() },
        });
      } catch (err) {
        console.warn("Could not persist theme preference:", err);
      }
    } else {
      localStorage.setItem("theme", next);
    }
  });

  // Apply saved theme for guests
  const isAuthenticated = document.body.dataset.authenticated === "true";
  if (!isAuthenticated) {
    const saved = localStorage.getItem("theme");
    if (saved) {
      document.documentElement.setAttribute("data-theme", saved);
      updateToggleIcon(saved);
    }
  } else {
    updateToggleIcon(document.documentElement.getAttribute("data-theme") || "light");
  }
}

function updateToggleIcon(theme) {
  const icon = document.querySelector("#themeToggleBtn i");
  if (!icon) return;
  icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
}

function initResetButton() {
  const resetBtn = document.getElementById("resetFormBtn");
  const form = document.getElementById("predictionForm");
  if (resetBtn && form) {
    resetBtn.addEventListener("click", () => {
      form.reset();
      form.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));
    });
  }
}

/* Rotates the gauge needle based on data-probability (0-100) found on #resultGauge or #heroGauge */
function initGaugeAnimation() {
  document.querySelectorAll("[data-gauge-probability]").forEach((wrap) => {
    const probability = parseFloat(wrap.dataset.gaugeProbability || "0");
    const needle = wrap.querySelector(".gauge-needle");
    if (!needle) return;
    // Gauge sweeps -90deg (0%) to +90deg (100%)
    const angle = -90 + (probability / 100) * 180;
    requestAnimationFrame(() => {
      needle.style.transform = `rotate(${angle}deg)`;
    });
  });
}

function initFadeIn() {
  const items = document.querySelectorAll(".animate-in");
  if (!("IntersectionObserver" in window) || items.length === 0) return;
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = "running";
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );
  items.forEach((item) => observer.observe(item));
}
