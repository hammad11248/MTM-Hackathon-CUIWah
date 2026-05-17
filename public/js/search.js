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
  const container = document.getElementById("docResults");
  if (!container) return;

  container.innerHTML = "";

  if (isSearch && data.specializations?.length) {
    const urgencyColors = {
      EMERGENCY: "bg-red-500 text-white",
      HIGH: "bg-amber-500 text-white",
      MEDIUM: "bg-yellow-500 text-slate-800",
      LOW: "bg-green-500 text-white",
    };
    
    container.innerHTML += `
      <div class="bg-brand-50 border border-brand-100 rounded-xl p-4 mb-4 shadow-sm text-sm text-slate-700">
        <div class="font-bold text-brand-600 mb-2 flex items-center justify-between text-[11px] uppercase tracking-wider">
          <span>📋 Medical Triage Analysis</span>
          <span class="px-2 py-0.5 rounded text-white font-semibold ${urgencyColors[data.urgency]}">${data.urgency}</span>
        </div>
        <div class="text-xs text-slate-600 space-y-2 mt-3">
          <p><strong class="text-slate-800">Specialist Needed:</strong> ${esc(data.specializations.join(", "))}</p>
          <p><strong class="text-slate-800">Home Advice:</strong> ${esc(data.home_advice)}</p>
        </div>
      </div>
    `;
  }

  if (!data.doctors?.length) {
    container.innerHTML += `
      <div class="text-center py-10">
        <span class="text-4xl">🔍</span>
        <h3 class="text-slate-900 font-bold mt-4">No doctors found</h3>
        <p class="text-slate-500 text-sm mt-1">Try adjusting your symptoms or filters.</p>
      </div>`;
    return;
  }

  data.doctors.forEach((doc) => {
    // Cache availability
    window.doctorCache = window.doctorCache || {};
    window.doctorCache[doc._id] = doc.availability || {};

    const card = `
      <div class="glass-card p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-full bg-brand-100 flex items-center justify-center text-2xl shadow-inner border border-brand-200">👨‍⚕️</div>
          <div>
            <h3 class="font-bold text-slate-900 text-lg">${esc(doc.name)}</h3>
            <p class="text-sm font-medium text-brand-600">${esc(doc.specialization)} • ${esc(doc.location)}</p>
            <div class="flex items-center gap-4 mt-2 text-xs font-semibold text-slate-500">
              <span class="flex items-center gap-1"><span class="text-amber-400 text-sm">★</span> ${doc.rating || "4.5"} (${doc.total_reviews || 0})</span>
              <span>💰 PKR ${doc.consultation_fee || 1500}</span>
              <span>🕒 ${doc.experience_years || 5} yrs exp</span>
            </div>
          </div>
        </div>
        <div class="flex sm:flex-col gap-2 w-full sm:w-auto mt-2 sm:mt-0">
          <a href="/doctor-profile.html?id=${doc._id}" class="btn-primary flex-1 sm:flex-none text-center px-6 py-2.5 rounded-xl font-bold shadow-sm">Book Slot</a>
        </div>
      </div>
    `;
    container.insertAdjacentHTML("beforeend", card);
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
  const container = document.getElementById("docResults");
  if (!container) return;
  if (visible) {
    container.innerHTML = `
      <div class="skeleton h-24 w-full mb-4"></div>
      <div class="skeleton h-24 w-full mb-4"></div>
      <div class="skeleton h-24 w-full mb-4"></div>
    `;
  }
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
