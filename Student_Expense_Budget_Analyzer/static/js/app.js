document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".progress-fill[data-progress]").forEach((bar) => {
    bar.style.width = `${Math.max(0, Math.min(100, Number(bar.dataset.progress) || 0))}%`;
  });

  const menuToggle = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => {
      const open = sidebar.classList.toggle("open");
      menuToggle.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("click", (event) => {
      if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
        sidebar.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll(".flash-message button").forEach((button) => {
    button.addEventListener("click", () => button.parentElement.remove());
  });

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  const dataNode = document.querySelector("#dashboard-data, #report-data");
  if (!dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  if (!window.Chart) {
    document.querySelectorAll(".chart-empty[hidden]").forEach((empty) => {
      empty.hidden = false;
      empty.textContent = "Charts need an internet connection to load. Your expense records are saved locally.";
    });
    return;
  }

  Chart.defaults.font.family = '"DM Sans", sans-serif';
  Chart.defaults.color = "#667085";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  const palette = ["#4f46e5", "#0f9f8f", "#e69443", "#d65b78", "#4589c8", "#8764c6", "#7d9d4c", "#9aa4b2"];
  const monthlyCanvas = document.querySelector("#monthlyChart, #reportMonthlyChart");
  if (monthlyCanvas) {
    const context = monthlyCanvas.getContext("2d");
    const gradient = context.createLinearGradient(0, 0, 0, monthlyCanvas.clientHeight || 200);
    gradient.addColorStop(0, "rgba(79, 70, 229, .18)");
    gradient.addColorStop(1, "rgba(79, 70, 229, 0)");
    new Chart(context, {
      type: "line",
      data: {
        labels: data.months,
        datasets: [{
          data: data.monthly,
          borderColor: "#4f46e5",
          backgroundColor: gradient,
          fill: true,
          tension: .38,
          borderWidth: 2.5,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: "#fff",
          pointBorderColor: "#4f46e5",
          pointBorderWidth: 2
        }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => ` ₹${Number(context.parsed.y).toLocaleString("en-IN", { maximumFractionDigits: 2 })}` } } },
        scales: {
          x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 11 } } },
          y: { beginAtZero: true, border: { display: false, dash: [3, 3] }, grid: { color: "#f1eff5" }, ticks: { font: { size: 11 }, callback: (value) => `₹${Number(value).toLocaleString("en-IN")}` } }
        }
      }
    });
  }

  const categoryCanvas = document.querySelector("#categoryChart, #reportCategoryChart");
  if (categoryCanvas && data.categories.length) {
    new Chart(categoryCanvas.getContext("2d"), {
      type: "pie",
      data: {
        labels: data.categories,
        datasets: [{ data: data.categoryValues, backgroundColor: palette, borderColor: "#fff", borderWidth: 4, hoverOffset: 7 }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { boxWidth: 9, boxHeight: 9, padding: 13, font: { size: 11 } } },
          tooltip: { callbacks: { label: (context) => ` ${context.label}: ₹${Number(context.parsed).toLocaleString("en-IN", { maximumFractionDigits: 2 })}` } }
        }
      }
    });
  }
});
