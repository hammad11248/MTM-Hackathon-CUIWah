/**
 * Smart Doctor Connect AI — Home Page Floating Triage Assistant (triage-chat.js)
 * Manages the floating AI receptionist bot on the landing page.
 * Sends symptom inputs to the backend triage endpoint and displays doctor cards directly in-chat.
 */

// ── State ────────────────────────────────────────────────────────────────────
let triageChatOpen = false;
let triageSending = false;
let triagePatientName = "";

// ── Toggle Widget ────────────────────────────────────────────────────────────
function toggleTriageChat() {
  const windowEl = document.getElementById("triageChatWindow");
  const badge = document.getElementById("triageChatBadge");
  
  if (!windowEl) return;
  
  triageChatOpen = !triageChatOpen;
  windowEl.classList.toggle("hidden", !triageChatOpen);
  
  if (triageChatOpen) {
    if (badge) badge.classList.add("hidden");
    
    // Auto-focus name input if empty
    const nameInput = document.getElementById("triagePatientName");
    if (nameInput && !triagePatientName) {
      setTimeout(() => nameInput.focus(), 100);
    } else {
      const msgInput = document.getElementById("triageMessage");
      if (msgInput) setTimeout(() => msgInput.focus(), 100);
    }
  }
}

// ── Initialize Triage Chat ───────────────────────────────────────────────────
function initTriageChat() {
  const container = document.getElementById("triageChatMessages");
  if (!container) return;

  container.innerHTML = "";
  
  // Welcome message
  addTriageBubble(
    "Hello there! I am your AI Health Assistant. Tell me your name and describe what you are feeling (symptoms) to instantly find the best specialists.",
    "ai",
    "Smart Doctor AI"
  );
}

// ── Send Message ─────────────────────────────────────────────────────────────
async function sendTriageMessage() {
  if (triageSending) return;

  const nameInput = document.getElementById("triagePatientName");
  const msgInput = document.getElementById("triageMessage");
  const formArea = document.getElementById("triageNameFormArea");

  if (!nameInput || !msgInput) return;

  const name = nameInput.value.trim();
  const message = msgInput.value.trim();

  if (!triagePatientName) {
    if (!name) {
      showToast("Please enter your name first.");
      nameInput.focus();
      return;
    }
    triagePatientName = name;
    if (formArea) {
      formArea.classList.add("hidden");
    }
  }

  if (!message) {
    showToast("Please type your symptoms.");
    msgInput.focus();
    return;
  }

  // Display user's message
  addTriageBubble(message, "patient", triagePatientName);
  msgInput.value = "";
  triageSending = true;

  const typingId = addTriageTypingIndicator();

  try {
    const resp = await fetch(`${API_BASE}/chat/triage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_name: triagePatientName,
        message: message,
      }),
    });

    removeTriageTypingIndicator(typingId);

    if (!resp.ok) {
      throw new Error(`Server status: ${resp.status}`);
    }

    const data = await resp.json();
    
    // Render AI's response text
    addTriageBubble(data.ai_response, "ai", "Smart Doctor AI");

    // Display recommendation badge
    if (data.specializations?.length) {
      addTriageRecommendationCard(data);
    }

    // Display matching doctor suggestions directly inside chat!
    if (data.doctors && data.doctors.length > 0) {
      addTriageDoctorSuggestions(data.doctors);
    }
  } catch (err) {
    removeTriageTypingIndicator(typingId);
    addTriageBubble(
      "I encountered an issue connecting to the AI service. Don't worry! Try searching your symptoms using the search bar above.",
      "ai",
      "Smart Doctor AI"
    );
    console.error("Triage chat error:", err);
  } finally {
    triageSending = false;
  }
}

// ── Add Chat Bubble ──────────────────────────────────────────────────────────
function addTriageBubble(text, type, sender) {
  const container = document.getElementById("triageChatMessages");
  if (!container) return;

  const bubble = document.createElement("div");
  const isPatient = type === "patient";

  bubble.className = `max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed shadow-md ${
    isPatient
      ? "bg-violet-900/40 text-violet-50 border border-violet-500/30 self-end ml-auto rounded-tr-sm"
      : "bg-cyan-900/40 text-cyan-50 border border-cyan-500/30 self-start mr-auto rounded-tl-sm"
  }`;

  const timeStr = new Date().toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  bubble.innerHTML = `
    <div class="flex items-center gap-1.5 mb-1.5 opacity-70">
      <span class="font-black text-[9px] uppercase tracking-wider">${esc(sender)}</span>
      <span class="text-[8px] opacity-70">${timeStr}</span>
    </div>
    <p class="whitespace-pre-line">${esc(text)}</p>
  `;

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

// ── Add Triage Recommendation Card ───────────────────────────────────────────
function addTriageRecommendationCard(data) {
  const container = document.getElementById("triageChatMessages");
  if (!container) return;

  const urgencyColors = {
    EMERGENCY: "bg-red-500 text-white",
    HIGH: "bg-orange-500 text-white",
    MEDIUM: "bg-yellow-500 text-slate-900",
    LOW: "bg-green-500 text-white",
  };

  const card = document.createElement("div");
  card.className = "bg-slate-900/80 border border-cyan-500/30 rounded-xl p-3 my-2 self-start mr-auto w-[90%] text-xs shadow-sm text-cyan-50";

  card.innerHTML = `
    <div class="font-black text-cyan-400 mb-2 flex items-center justify-between text-[10px] uppercase tracking-wider">
      <span>📋 Medical Triage Analysis</span>
      <span class="px-2 py-0.5 rounded ${urgencyColors[data.urgency]}">${data.urgency}</span>
    </div>
    <div class="text-[10px] text-slate-300 space-y-1.5">
      <p><strong class="text-slate-400">Specialist Needed:</strong> ${esc(data.specializations.join(", "))}</p>
      <p><strong class="text-slate-400">Home Advice:</strong> ${esc(data.home_advice)}</p>
    </div>
  `;

  container.appendChild(card);
  container.scrollTop = container.scrollHeight;
}

// ── Display Doctor Suggestions in Chat ────────────────────────────────────────
function addTriageDoctorSuggestions(doctors) {
  const container = document.getElementById("triageChatMessages");
  if (!container) return;

  const div = document.createElement("div");
  div.className = "self-start w-[90%] my-2 space-y-2";

  const label = document.createElement("div");
  label.className = "text-[9px] font-black text-slate-500 uppercase tracking-widest pl-1 mb-1";
  label.textContent = "Recommended Nodes:";
  div.appendChild(label);

  doctors.forEach((doc) => {
    // Cache doctor availability globally
    window.doctorCache = window.doctorCache || {};
    window.doctorCache[doc._id] = doc.availability || {};

    const card = document.createElement("div");
    card.className = "bg-slate-900/60 border border-white/10 rounded-xl p-3 shadow-sm hover:border-cyan-500/40 transition-all flex items-center justify-between text-white";

    card.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-xl">👨‍⚕️</span>
        <div>
          <h4 class="font-bold text-white text-[11px]">${esc(doc.name)}</h4>
          <p class="text-[9px] font-semibold text-cyan-400 mt-0.5">${esc(doc.specialization)} • ${esc(doc.location)}</p>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-yellow-400 text-[10px]">★</span>
            <span class="text-[9px] font-bold text-slate-400">${doc.rating || "4.5"}</span>
          </div>
        </div>
      </div>
      <button onclick="openBooking('${doc._id}', '${esc(doc.name)}', window.doctorCache['${doc._id}'])" 
        class="bg-cyan-950/40 border border-cyan-500/30 hover:bg-cyan-950/60 text-cyan-400 font-black tracking-wider uppercase px-2.5 py-1.5 rounded-lg text-[9px] shadow-sm transition-colors">
        Book
      </button>
    `;
    div.appendChild(card);
  });

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// ── Typing Indicator ─────────────────────────────────────────────────────────
function addTriageTypingIndicator() {
  const container = document.getElementById("triageChatMessages");
  if (!container) return null;

  const id = "triage-typing-" + Date.now();
  const indicator = document.createElement("div");
  indicator.id = id;
  indicator.className = "self-start mr-auto bg-cyan-900/40 border border-cyan-500/30 text-cyan-400 px-4 py-3 rounded-2xl rounded-bl-sm text-xs shadow-sm w-24";
  indicator.innerHTML = `
    <div class="flex gap-1.5 justify-center items-center h-4">
      <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
      <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
      <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
    </div>`;

  container.appendChild(indicator);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTriageTypingIndicator(id) {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── Bind DOM Elements ────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTriageChat();

  const triageInput = document.getElementById("triageMessage");
  if (triageInput) {
    triageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendTriageMessage();
      }
    });
  }
});
