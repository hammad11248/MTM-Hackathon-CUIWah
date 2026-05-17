/**
 * Smart Doctor Connect AI — Search Logic (search.js)
 * Handles AI-powered symptom search, result rendering, and analysis banner display.
 */

// ── Search State ────────────────────────────────────────────────────────────
let searchDebounceTimer = null;

// ── Fill Search Input & Trigger ─────────────────────────────────────────────
function fillSearch(text) {
  const input = document.getElementById("searchInput");
  if (input) {
    input.value = text;
    handleSearch();
  }
}

// ── Main Search Handler ─────────────────────────────────────────────────────
async function handleSearch() {
  const input = document.getElementById("searchInput");
  if (!input) return;

  const q = input.value.trim();
  if (q.length < 3) {
    showToast("Please describe your symptoms (at least 3 characters).");
    return;
  }

  showSkeleton(true);
  hideAnalysisBanner();

  try {
    const resp = await fetch(
      `${API_BASE}/doctors/search?q=${encodeURIComponent(q)}&limit=6`
    );
    if (!resp.ok) throw new Error(`Server error ${resp.status}`);
    const data = await resp.json();
    renderSearchResults(data);
  } catch (err) {
    showToast("Search failed. Please try again.");
    console.error("Search error:", err);
  } finally {
    showSkeleton(false);
  }
}

// ── Render Search Results ───────────────────────────────────────────────────
function renderSearchResults(data, isSearch = true) {
  const grid = document.getElementById("doctorGrid");
  const empty = document.getElementById("emptyState");
  const heading = document.getElementById("resultsHeading");
  const count = document.getElementById("resultCount");

  if (!grid) return;
  grid.innerHTML = "";

  // Show analysis banner if it is an AI search result
  if (isSearch && data.specializations?.length) {
    showAnalysisBanner(data);
  } else {
    hideAnalysisBanner();
  }

  if (!data.doctors?.length) {
    if (empty) empty.classList.remove("hidden");
    if (heading) heading.classList.add("hidden");
    if (count) count.textContent = "";
    return;
  }

  if (empty) empty.classList.add("hidden");
  if (heading) {
    heading.textContent = isSearch ? "Matching Doctors" : "Featured Specialists Across Pakistan";
    heading.classList.remove("hidden");
  }
  if (count)
    count.textContent = isSearch 
      ? `${data.doctors.length} result${data.doctors.length !== 1 ? "s" : ""}`
      : `${data.doctors.length} available doctor${data.doctors.length !== 1 ? "s" : ""}`;

  data.doctors.forEach((doc) => {
    grid.insertAdjacentHTML("beforeend", buildDoctorCard(doc));
  });
}

// ── Load Featured Doctors by Default ────────────────────────────────────────
async function loadFeaturedDoctors() {
  showSkeleton(true);
  try {
    const resp = await fetch(`${API_BASE}/doctors/?limit=9`);
    if (!resp.ok) throw new Error(`Server error ${resp.status}`);
    const doctors = await resp.json();
    renderSearchResults({ doctors }, false);
  } catch (err) {
    showToast("Failed to load doctors. Please try again.");
    console.error("Load featured error:", err);
  } finally {
    showSkeleton(false);
  }
}

// ── Analysis Banner ─────────────────────────────────────────────────────────
function showAnalysisBanner(data) {
  const urgencyColors = {
    EMERGENCY: "bg-red-950/40 text-red-400 border border-red-500/20",
    HIGH: "bg-orange-950/40 text-orange-400 border border-orange-500/20",
    MEDIUM: "bg-yellow-950/40 text-yellow-400 border border-yellow-500/20",
    LOW: "bg-green-950/40 text-green-400 border border-green-500/20",
  };

  const banner = document.getElementById("analysisBanner");
  if (!banner) return;

  const advice = document.getElementById("bannerAdvice");
  const spec = document.getElementById("bannerSpec");
  const urgencyEl = document.getElementById("bannerUrgency");

  if (advice) advice.textContent = data.home_advice || "—";
  if (spec) spec.textContent = data.specializations?.join(", ") || "—";
  if (urgencyEl) {
    urgencyEl.textContent = data.urgency || "—";
    urgencyEl.className = `px-3 py-1 rounded-full text-xs font-bold ${
      urgencyColors[data.urgency] || "bg-slate-100 text-slate-600"
    }`;
  }

  banner.classList.remove("hidden");
}

function hideAnalysisBanner() {
  const banner = document.getElementById("analysisBanner");
  if (banner) banner.classList.add("hidden");
}

// ── Skeleton Toggle ─────────────────────────────────────────────────────────
function showSkeleton(visible) {
  const skeleton = document.getElementById("skeletonGrid");
  const grid = document.getElementById("doctorGrid");
  if (skeleton) skeleton.classList.toggle("hidden", !visible);
  if (grid) grid.classList.toggle("hidden", visible);
}

// ── Auto-init: bind Enter key and query params ──────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleSearch();
    });

    // Auto-search if ?q= param present
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) {
      searchInput.value = q;
      handleSearch();
    } else {
      loadFeaturedDoctors();
    }
  }
});
