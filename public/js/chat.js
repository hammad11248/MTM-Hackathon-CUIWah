/**
 * Smart Doctor Connect AI — Real-time Chat Interface (chat.js)
 * Handles the AI receptionist chatbot on doctor profile pages.
 * Sends messages to the backend, displays AI responses, and loads chat history.
 */

// ── Chat State ──────────────────────────────────────────────────────────────
let chatDoctorId = null;
let chatSending = false;

// ── Initialize Chat ─────────────────────────────────────────────────────────
function initChat(doctorId) {
  chatDoctorId = doctorId;
  if (doctorId) {
    loadChatHistory(doctorId);
  }
}

// ── Send Message ────────────────────────────────────────────────────────────
async function sendChatMessage() {
  if (chatSending) return;

  const nameInput = document.getElementById("chatName");
  const contactInput = document.getElementById("chatContact");
  const msgInput = document.getElementById("chatMessage");

  if (!nameInput || !msgInput) return;

  const name = nameInput.value.trim();
  const contact = contactInput?.value.trim() || null;
  const message = msgInput.value.trim();

  if (!name) {
    showToast("Please enter your name.");
    nameInput.focus();
    return;
  }
  if (!message) {
    showToast("Please type a message.");
    msgInput.focus();
    return;
  }
  if (!chatDoctorId) {
    showToast("No doctor selected.");
    return;
  }

  // Add patient bubble immediately
  addChatBubble(message, "patient", name);
  msgInput.value = "";
  chatSending = true;

  // Show typing indicator
  const typingId = addTypingIndicator();

  try {
    const resp = await fetch(`${API_BASE}/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doctor_id: chatDoctorId,
        patient_name: name,
        patient_contact: contact,
        message: message,
      }),
    });

    removeTypingIndicator(typingId);

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to send message");
    }

    const data = await resp.json();
    addChatBubble(data.ai_response, "ai", "AI Receptionist");

    // Show notification about doctor availability
    if (!data.doctor_available) {
      showToast("📧 Doctor has been notified via email.", 4000);
    }
  } catch (err) {
    removeTypingIndicator(typingId);
    addChatBubble(
      "Sorry, something went wrong. Please try again.",
      "ai",
      "System"
    );
    console.error("Chat error:", err);
  } finally {
    chatSending = false;
  }
}

// ── Load Chat History ───────────────────────────────────────────────────────
async function loadChatHistory(doctorId) {
  const container = document.getElementById("chatMessages");
  if (!container) return;

  try {
    const resp = await fetch(
      `${API_BASE}/chat/history/${doctorId}?limit=20`
    );
    if (!resp.ok) return;

    const messages = await resp.json();
    if (!messages.length) {
      addChatBubble(
        "Welcome! Send a message and our AI receptionist will assist you.",
        "ai",
        "AI Receptionist"
      );
      return;
    }

    messages.forEach((msg) => {
      addChatBubble(msg.message, "patient", msg.patient_name);
      addChatBubble(msg.ai_response, "ai", "AI Receptionist");
    });
  } catch (err) {
    console.error("Failed to load chat history:", err);
  }
}

// ── Add Chat Bubble ─────────────────────────────────────────────────────────
function addChatBubble(text, type, sender) {
  const container = document.getElementById("chatMessages");
  if (!container) return;

  const bubble = document.createElement("div");
  const isPatient = type === "patient";

  bubble.className = `max-w-[80%] p-3.5 rounded-2xl text-sm leading-relaxed shadow-md ${
    isPatient
      ? "bg-violet-900/40 text-violet-50 border border-violet-500/30 self-end ml-auto rounded-br-sm"
      : "bg-cyan-900/40 text-cyan-50 border border-cyan-500/30 self-start mr-auto rounded-bl-sm"
  }`;

  const timeStr = new Date().toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  bubble.innerHTML = `
    <div class="flex items-center gap-1.5 mb-1 opacity-70">
      <span class="text-[10px] font-black uppercase tracking-wider">${esc(sender)}</span>
      <span class="text-[9px] opacity-60">${timeStr}</span>
    </div>
    <p>${esc(text)}</p>
  `;

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

// ── Typing Indicator ────────────────────────────────────────────────────────
function addTypingIndicator() {
  const container = document.getElementById("chatMessages");
  if (!container) return null;

  const id = "typing-" + Date.now();
  const indicator = document.createElement("div");
  indicator.id = id;
  indicator.className =
    "self-start mr-auto bg-cyan-900/40 border border-cyan-500/30 text-cyan-400 px-4 py-3 rounded-2xl rounded-bl-sm text-sm shadow-md";
  indicator.innerHTML = `
    <div class="flex items-center gap-1">
      <span class="text-[10px] font-black uppercase tracking-wider opacity-70">AI Receptionist</span>
    </div>
    <div class="flex gap-1.5 mt-2">
      <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
      <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
      <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
    </div>`;

  container.appendChild(indicator);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── Init: keyboard shortcut ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const chatInput = document.getElementById("chatMessage");
  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }
});

// ── Finish Chat and Summarize ───────────────────────────────────────────────
async function finishChatAndSummarize() {
  if (!chatDoctorId) {
    showToast("No doctor selected.");
    return;
  }

  const nameInput = document.getElementById("chatName");
  const name = nameInput?.value.trim() || "Patient";

  const container = document.getElementById("chatMessages");
  if (!container || !container.children.length) {
    showToast("No conversation to summarize.");
    return;
  }

  const history = [];
  Array.from(container.children).forEach((bubble) => {
    if (bubble.id && bubble.id.startsWith("typing")) return;
    const isPatient = bubble.className.includes("self-end");
    const role = isPatient ? "Patient" : "AI";
    const pTag = bubble.querySelector("p");
    if (pTag) {
      history.push({ role, content: pTag.textContent });
    }
  });

  if (!history.length) return;

  const btn = event.currentTarget;
  const originalText = btn.innerHTML;
  btn.innerHTML = `<span class="animate-pulse">Syncing Briefing...</span>`;
  btn.disabled = true;

  try {
    const resp = await fetch(`${API_BASE}/chat/summary`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doctor_id: chatDoctorId,
        patient_name: name,
        chat_history: history,
      }),
    });

    if (!resp.ok) throw new Error("Failed to generate summary");
    
    const data = await resp.json();
    showToast("✅ Triage summary successfully linked to appointment!");

    // Agentic Doctor Matching
    const matchResp = await fetch(`${API_BASE}/agents/match-doctor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        triage_summary: data.triage_summary,
      }),
    });

    if (matchResp.ok) {
      const matchData = await matchResp.json();
      displayAgentRecommendations(matchData);
    }

  } catch (err) {
    console.error(err);
    showToast("⚠️ Could not generate summary. Please check connection.");
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

function displayAgentRecommendations(matchData) {
  const container = document.getElementById("chatMessages");
  if (!container) return;

  const bubble = document.createElement("div");
  bubble.className = "self-start bg-brand-50 border border-brand-100 text-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[85%] shadow-sm";
  
  let docsHtml = matchData.doctors.map(d => {
    return `<div class="bg-white p-3 rounded-xl mt-2 border border-slate-200 shadow-sm">
      <p class="text-sm font-bold text-slate-900">${d.name}</p>
      <p class="text-xs font-medium text-brand-600">${d.specialization} • ${d.location}</p>
    </div>`;
  }).join("");

  bubble.innerHTML = `
    <div class="flex items-center gap-1.5 mb-1.5">
      <span class="text-[10px] font-bold tracking-widest uppercase text-brand-600">Agent Specialist Matching</span>
    </div>
    <p class="text-sm leading-relaxed mb-2 text-slate-700">${matchData.reasoning}</p>
    ${docsHtml}
  `;
  
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

