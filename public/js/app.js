/**
 * Smart Doctor Connect AI — Shared Utilities (app.js)
 * Common functions used across all frontend pages:
 * - API base URL configuration
 * - XSS escaping
 * - Toast notifications
 * - Doctor card rendering (Cyber Dark Theme)
 * - Date/time utilities
 */

const API_BASE = "/api";

// ── XSS Escape Helper ──────────────────────────────────────────────────────
function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Toast Notification ──────────────────────────────────────────────────────
function showToast(msg, duration = 3500) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    document.body.appendChild(toast);
  }
  toast.className =
    "fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-cyan-950/80 border border-cyan-500/30 text-white text-xs font-bold px-6 py-3.5 rounded-full shadow-2xl flex items-center gap-2 backdrop-blur-md transition-all";
  
  toast.textContent = msg;
  toast.classList.remove("hidden");
  toast.style.opacity = "1";
  toast.style.transform = "translateX(-50%) translateY(0)";
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(-50%) translateY(20px)";
    setTimeout(() => toast.classList.add("hidden"), 300);
  }, duration);
}

// ── Build Doctor Card HTML (Cyber Theme) ────────────────────────────────────
function buildDoctorCard(doc, options = {}) {
  const score = doc.match_score ?? 0;
  
  // High-fidelity neon progress bars
  const scoreColor =
    score >= 70 ? "bg-gradient-to-r from-emerald-400 to-cyan-400" : score >= 40 ? "bg-gradient-to-r from-yellow-400 to-amber-500" : "bg-slate-600";
    
  const availBadge = doc.is_available
    ? '<span class="bg-cyan-950/40 text-cyan-400 border border-cyan-500/20 text-[9px] font-black px-2.5 py-1 rounded-full uppercase tracking-wider">Available</span>'
    : '<span class="bg-red-950/40 text-red-400 border border-red-500/20 text-[9px] font-black px-2.5 py-1 rounded-full uppercase tracking-wider">Offline</span>';

  const stars =
    "★".repeat(Math.round(doc.rating || 0)) +
    "☆".repeat(5 - Math.round(doc.rating || 0));

  const docId = doc._id || doc.id || "";
  const showScore = options.showScore !== false;
  const showBookBtn = options.showBookBtn !== false;

  // Cache doctor availability globally
  window.doctorCache = window.doctorCache || {};
  window.doctorCache[docId] = doc.availability || {};

  let ctaHtml = "";
  if (showBookBtn) {
    ctaHtml = `
      <div class="flex gap-2.5 mt-auto pt-2">
        <button onclick="openBooking('${esc(docId)}','${esc(doc.name)}', window.doctorCache['${esc(docId)}'])"
          class="flex-1 btn-neon-cyan text-white text-xs font-black uppercase tracking-widest py-3 rounded-xl transition-all
                 ${doc.is_available ? '' : 'opacity-50 cursor-not-allowed'}"
          ${doc.is_available ? '' : 'disabled'}>Book Slot</button>
        <a href="/doctor-profile.html?id=${esc(docId)}"
          class="px-4 py-3 bg-slate-900/60 border border-white/5 rounded-xl text-xs font-black uppercase tracking-widest text-slate-400 hover:border-violet-500/30 hover:text-violet-400 transition-colors flex items-center justify-center">
          Profile
        </a>
      </div>`;
  }

  let scoreHtml = "";
  if (showScore) {
    scoreHtml = `
      <div class="mt-1">
        <div class="flex justify-between text-[9px] font-black uppercase tracking-widest text-slate-500 mb-1.5">
          <span>AI Match Matrix</span><span class="text-cyan-400">${score}%</span>
        </div>
        <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden border border-white/5">
          <div class="score-bar h-full ${scoreColor} rounded-full relative" style="width:${score}%">
             <div class="absolute inset-0 bg-white/20 w-full animate-pulse"></div>
          </div>
        </div>
      </div>`;
  }

  return `
    <div class="cyber-card rounded-[2rem] rounded-tr-md p-5 flex flex-col gap-3 font-sans">
      <div class="flex items-start justify-between gap-2 border-b border-white/5 pb-3">
        <div class="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-2xl shrink-0 shadow-inner">👨‍⚕️</div>
        <div class="flex-1 min-w-0">
          <h3 class="font-display font-extrabold text-white truncate text-base">${esc(doc.name)}</h3>
          <p class="text-cyan-400 text-[10px] font-black uppercase tracking-widest mt-0.5">${esc(doc.specialization)}</p>
        </div>
        ${availBadge}
      </div>
      <div class="flex flex-wrap gap-x-4 gap-y-2 text-[10px] text-slate-400 font-semibold py-1">
        <span class="flex items-center gap-1"><span class="text-xs">📍</span> ${esc(doc.location)}</span>
        <span class="flex items-center gap-1"><span class="text-xs">🏥</span> ${esc(doc.consultation_type)}</span>
        <span class="flex items-center gap-1"><span class="text-xs">💰</span> Rs. ${doc.consultation_fee?.toLocaleString() ?? "—"}</span>
        <span class="flex items-center gap-1"><span class="text-xs">🎓</span> ${doc.experience_years} yrs exp.</span>
      </div>
      <div class="flex items-center gap-2 text-xs bg-slate-950/40 p-2 rounded-xl border border-white/5">
        <span class="text-yellow-400 tracking-tight">${stars}</span>
        <span class="text-slate-500 font-bold">${doc.rating?.toFixed(1) ?? "N/A"} (${doc.total_reviews} reviews)</span>
      </div>
      ${scoreHtml}
      ${ctaHtml}
    </div>`;
}

// ── Date Utilities ──────────────────────────────────────────────────────────
function getDayName(dateStr) {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
    weekday: "long",
  });
}

function getTodayStr() {
  return new Date().toISOString().split("T")[0];
}

// ── Fetch Helper ────────────────────────────────────────────────────────────
async function apiFetch(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw { status: resp.status, detail: err.detail || "Request failed" };
  }
  return resp.json();
}
