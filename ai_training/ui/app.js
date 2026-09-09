/**
 * ISKRA SMART METER — EXECUTIVE AI COMMAND CENTER
 * Frontend Client Controller
 * Pure Vanilla JavaScript — zero external JS dependencies
 */

const API_BASE = window.location.origin;

// Application State
let isProcessing = false;
let currentCaseData = null;

// DOM Elements
const chatStream = document.getElementById("chat-stream");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send");
const btnReset = document.getElementById("btn-reset");
const btnDemo = document.getElementById("btn-demo");
const btnExport = document.getElementById("btn-export");

// Decision Trace DOM
const traceLanguage = document.getElementById("trace-language");
const traceIntent = document.getElementById("trace-intent");
const traceStrategy = document.getElementById("trace-strategy");
const traceRouting = document.getElementById("trace-routing");
const traceRoutingNote = document.getElementById("trace-routing-note");
const traceKnowledgeStatus = document.getElementById("trace-knowledge-status");
const traceEvidenceStatus = document.getElementById("trace-evidence-status");
const traceResolutionStatus = document.getElementById("trace-resolution-status");
const traceTechnicalEntity = document.getElementById("trace-technical-entity");
const evidencePanelTitle = document.getElementById("evidence-panel-title");
const evidencePanelBadge = document.getElementById("evidence-panel-badge");
const evidencePanelSubtitle = document.getElementById("evidence-panel-subtitle");
const evidenceContainer = document.getElementById("evidence-container");
const safetyShieldStatus = document.getElementById("safety-shield-status");
const badgeGuardGrounding = document.getElementById("badge-guard-grounding");
const badgeGuardTechId = document.getElementById("badge-guard-tech-id");
const badgeGuardSeal = document.getElementById("badge-guard-seal");
const badgeGuardInjection = document.getElementById("badge-guard-injection");

// Operational Memory DOM
const memErrorCode = document.getElementById("mem-error-code");
const memMeterModel = document.getElementById("mem-meter-model");
const memSystem = document.getElementById("mem-system");
const memIssue = document.getElementById("mem-issue");
const memUserLimitations = document.getElementById("mem-user-limitations");
const subjectSwitchBox = document.getElementById("subject-switch-box");
const subjectSwitchContent = document.getElementById("subject-switch-content");

// Coverage & Advisor DOM
const coverageTbody = document.getElementById("coverage-tbody");
const recommendationsContainer = document.getElementById("recommendations-container");
const totalMessagesCount = document.getElementById("total-messages-count");

// Modals & Banners
const exportModal = document.getElementById("export-modal");
const btnCloseModal = document.getElementById("btn-close-modal");
const modalCasePreview = document.getElementById("modal-case-preview");
const btnDownloadJson = document.getElementById("btn-download-json");
const btnDownloadCsv = document.getElementById("btn-download-csv");
const demoBanner = document.getElementById("demo-banner");
const demoBannerText = document.getElementById("demo-banner-text");

// Status Dots in Header
const dotAgent = document.getElementById("dot-agent");
const dotOllama = document.getElementById("dot-ollama");
const dotChroma = document.getElementById("dot-chroma");
const dotKB = document.getElementById("dot-kb");
const dotSafety = document.getElementById("dot-safety");
const labelOllamaModel = document.getElementById("label-ollama-model");
const labelChromaCount = document.getElementById("label-chroma-count");

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    initEventListeners();
    fetchSystemStatus();
    fetchAnalytics();
    fetchCurrentState();

    // Poll health every 6 seconds
    setInterval(fetchSystemStatus, 6000);
});

function initEventListeners() {
    btnSend.addEventListener("click", handleSendMessage);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    btnReset.addEventListener("click", handleResetSession);
    btnDemo.addEventListener("click", runExecutiveDemo);
    btnExport.addEventListener("click", openExportModal);
    btnCloseModal.addEventListener("click", closeExportModal);

    // Quick Chips
    document.querySelectorAll(".chip-btn").forEach((chip) => {
        chip.addEventListener("click", () => {
            const prompt = chip.getAttribute("data-prompt");
            if (prompt) {
                chatInput.value = prompt;
                handleSendMessage();
            }
        });
    });

    // Modal Export Buttons
    btnDownloadJson.addEventListener("click", () => {
        window.open(`${API_BASE}/api/case/export?format=json`, "_blank");
    });
    btnDownloadCsv.addEventListener("click", () => {
        window.open(`${API_BASE}/api/case/export?format=csv`, "_blank");
    });

    // Close modal on background click
    exportModal.addEventListener("click", (e) => {
        if (e.target === exportModal) {
            closeExportModal();
        }
    });
}

// ============================================================
// SYSTEM STATUS & HEALTH CHECKS
// ============================================================
async function fetchSystemStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        if (!res.ok) return;
        const data = await res.json();
        const comp = data.components || {};

        // Update Agent Dot
        if (comp.agent) {
            setDotStatus(dotAgent, comp.agent.status === "READY" ? "verified" : "offline");
        }

        // Update Ollama Dot
        if (comp.ollama) {
            setDotStatus(dotOllama, comp.ollama.status === "ONLINE" ? "verified" : "warning");
            if (labelOllamaModel) labelOllamaModel.textContent = comp.ollama.model || "granite4.2:8b";
        }

        // Update ChromaDB Dot
        if (comp.chromadb) {
            setDotStatus(dotChroma, comp.chromadb.status === "ONLINE" ? "verified" : "not-found");
            if (labelChromaCount) labelChromaCount.textContent = `${comp.chromadb.indexed_chunks || 0} chunks`;
        }

        // Knowledge Base & Safety
        if (comp.knowledge_base) setDotStatus(dotKB, "verified");
        if (comp.safety_shield) setDotStatus(dotSafety, "verified");

    } catch (err) {
        console.warn("Status fetch warning:", err);
    }
}

function setDotStatus(element, type) {
    if (!element) return;
    element.className = "health-dot";
    if (type === "verified") {
        element.classList.remove("offline", "warning");
    } else if (type === "warning") {
        element.classList.add("warning");
    } else {
        element.classList.add("offline");
    }
}

// ============================================================
// CHAT INTERACTION
// ============================================================
async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text || isProcessing) return;

    chatInput.value = "";
    isProcessing = true;
    btnSend.disabled = true;

    // Render user message bubble
    appendBubble("user", text);

    // Render live typing indicator
    const typingId = appendTypingIndicator();
    const startTime = performance.now();

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });

        const data = await res.json();
        removeElement(typingId);

        const elapsed = Math.round(performance.now() - startTime);

        if (res.ok) {
            appendBubble("agent", data.response, elapsed);
            updateDecisionTrace(data.trace, data.decision);
            updateOperationalMemory(data.state);
            updateAnalyticsView(data.analytics);
        } else {
            appendBubble("agent", `Error: ${data.detail || "Unable to process request."}`);
        }
    } catch (err) {
        removeElement(typingId);
        appendBubble("agent", "Error: Communication failure with AI agent backend.");
        console.error(err);
    } finally {
        isProcessing = false;
        btnSend.disabled = false;
        chatInput.focus();
    }
}

function appendBubble(role, text, latencyMs = null) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;

    const contentDiv = document.createElement("div");
    contentDiv.textContent = text;
    bubble.appendChild(contentDiv);

    const metaDiv = document.createElement("div");
    metaDiv.className = "chat-bubble-meta";
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    metaDiv.innerHTML = `<span>${role === "user" ? "Customer" : "ISKRA AI Agent"}</span> • <span>${timeStr}</span>`;
    if (latencyMs !== null) {
        metaDiv.innerHTML += ` • <span style="color: var(--accent-cyan); font-family: var(--font-mono);">${latencyMs}ms</span>`;
    }
    bubble.appendChild(metaDiv);

    chatStream.appendChild(bubble);
    chatStream.scrollTop = chatStream.scrollHeight;
}

function appendTypingIndicator() {
    const id = "typing-" + Date.now();
    const bubble = document.createElement("div");
    bubble.id = id;
    bubble.className = "chat-bubble agent";
    bubble.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <div class="demo-spinner" style="width: 14px; height: 14px; border-width: 2px;"></div>
            <span style="font-size: 12px; color: var(--text-muted);">Evaluating RAG evidence & grounding...</span>
        </div>
    `;
    chatStream.appendChild(bubble);
    chatStream.scrollTop = chatStream.scrollHeight;
    return id;
}

function removeElement(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ============================================================
// DECISION TRACE & GROUNDING UPDATES
// ============================================================
function updateDecisionTrace(trace, decision) {
    if (!trace) return;

    // Language & Intent
    if (traceLanguage) traceLanguage.textContent = trace.language || "English";
    if (traceIntent) traceIntent.textContent = (trace.intent || "GENERAL_QUESTION").toUpperCase();

    // Strategy & Routing
    const strategy = (decision && decision.action) ? decision.action : "ANSWER";
    if (traceStrategy) traceStrategy.textContent = strategy;

    const routingTier = trace.routing || "L1 Review";
    if (traceRouting) traceRouting.textContent = routingTier;

    // Mark routing type
    if (traceRoutingNote) {
        if (routingTier.includes("Hardware") || routingTier.includes("Firmware")) {
            traceRoutingNote.innerHTML = `<span class="badge badge-verified">VERIFIED POLICY</span>`;
        } else if (routingTier.includes("Software")) {
            traceRoutingNote.innerHTML = `<span class="badge badge-configured">DEFAULT CONFIGURATION</span>`;
        } else {
            traceRoutingNote.innerHTML = `<span class="badge badge-neutral">L1 RESOLUTION</span>`;
        }
    }

    // Knowledge & Evidence & Resolution Status
    if (traceKnowledgeStatus) {
        const kStatus = trace.knowledge_status || "NOT_FOUND";
        traceKnowledgeStatus.innerHTML = `<span class="badge badge-${getBadgeClass(kStatus)}">${kStatus}</span>`;
    }

    const evStatus = trace.evidence_status || (trace.evidence && trace.evidence.length > 0 ? "CONTEXT ONLY" : "NO VERIFIED EVIDENCE");
    if (traceEvidenceStatus) {
        traceEvidenceStatus.innerHTML = `<span class="badge badge-${getBadgeClass(evStatus)}">${evStatus}</span>`;
    }

    if (traceResolutionStatus) {
        traceResolutionStatus.textContent = trace.resolution_status || "Completed";
    }

    if (traceTechnicalEntity) {
        traceTechnicalEntity.textContent = trace.technical_entity || "None detected";
    }

    // Grounded Evidence vs Retrieved Context Panel
    if (evidenceContainer) {
        evidenceContainer.innerHTML = "";
        const items = trace.evidence || [];

        if (evStatus === "VERIFIED") {
            if (evidencePanelTitle) evidencePanelTitle.textContent = "GROUNDED KNOWLEDGE EVIDENCE";
            if (evidencePanelBadge) {
                evidencePanelBadge.className = "badge badge-verified";
                evidencePanelBadge.textContent = "VERIFIED";
            }
            if (evidencePanelSubtitle) evidencePanelSubtitle.textContent = "Direct exact line verification from ISKRA technical documentation (MT514):";

            items.forEach((ev) => {
                const card = document.createElement("div");
                card.className = "evidence-card verified-card";
                card.innerHTML = `
                    <div class="evidence-header">
                        <span class="evidence-source">${ev.source} (Page ${ev.page})</span>
                        <span class="badge badge-verified">VERIFIED</span>
                    </div>
                    <div style="font-size: 10px; color: var(--accent-cyan); margin-bottom: 4px; font-family: var(--font-mono);">
                        MATCH TYPE: DIRECT EXACT MATCH | RETRIEVAL: DIRECT ERROR CODE LOOKUP
                    </div>
                    <div class="evidence-quote">"${escapeHtml(ev.matched_line || "")}"</div>
                `;
                evidenceContainer.appendChild(card);
            });
        } else if (evStatus === "CONTEXT ONLY") {
            if (evidencePanelTitle) evidencePanelTitle.textContent = "GROUNDED KNOWLEDGE RETRIEVAL";
            if (evidencePanelBadge) {
                evidencePanelBadge.className = "badge badge-configured";
                evidencePanelBadge.textContent = "RETRIEVED CONTEXT";
            }
            if (evidencePanelSubtitle) evidencePanelSubtitle.textContent = "The knowledge base returned related technical documentation, but no source directly verifies the cause or resolution of the reported symptom.";

            const banner = document.createElement("div");
            banner.className = "context-alert-box";
            banner.innerHTML = `
                <div style="font-size: 11px; font-weight: 700; color: var(--accent-amber); margin-bottom: 3px;">
                    RETRIEVED CONTEXT (CONTEXT ONLY)
                </div>
                <div style="font-size: 11px; color: var(--text-secondary); line-height: 1.4;">
                    The knowledge base returned related technical documentation, but no source directly verifies the cause or resolution of the reported symptom.
                </div>
            `;
            evidenceContainer.appendChild(banner);

            items.forEach((ev) => {
                const card = document.createElement("div");
                card.className = "evidence-card context-card";
                card.innerHTML = `
                    <div class="evidence-header">
                        <span class="evidence-source">${ev.source} — Page ${ev.page}</span>
                        <span class="badge badge-configured">CONTEXT ONLY</span>
                    </div>
                    <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 4px; font-family: var(--font-mono);">
                        MATCH TYPE: SEMANTIC CONTEXT (NOT VERIFIED EVIDENCE)
                    </div>
                    <div class="evidence-quote context-quote">"${escapeHtml(ev.matched_line || "")}"</div>
                `;
                evidenceContainer.appendChild(card);
            });
        } else {
            // NO VERIFIED EVIDENCE
            if (evidencePanelTitle) evidencePanelTitle.textContent = "GROUNDED KNOWLEDGE RETRIEVAL";
            if (evidencePanelBadge) {
                evidencePanelBadge.className = "badge badge-not-found";
                evidencePanelBadge.textContent = "NO VERIFIED EVIDENCE";
            }
            if (evidencePanelSubtitle) evidencePanelSubtitle.textContent = "No verified documentation was found in the current knowledge base for this inquiry.";

            const banner = document.createElement("div");
            banner.className = "notfound-alert-box";
            const topic = trace.technical_entity && trace.technical_entity !== "None detected" ? trace.technical_entity : (trace.issue || "this inquiry");
            banner.innerHTML = `
                <div style="font-size: 11px; font-weight: 700; color: var(--accent-rose); margin-bottom: 3px;">
                    NO VERIFIED EVIDENCE
                </div>
                <div style="font-size: 11px; color: var(--text-secondary); line-height: 1.4;">
                    No verified documentation for <strong>${escapeHtml(topic)}</strong> was found in the current knowledge base. Unrelated error manual chunks are strictly excluded from evidence.
                </div>
            `;
            evidenceContainer.appendChild(banner);
        }
    }

    // Safety Shield Diagnostics
    const isBlocked = trace.safety === "BLOCKED";
    if (safetyShieldStatus) {
        safetyShieldStatus.innerHTML = isBlocked
            ? `<span class="badge badge-not-found">BLOCKED (INJECTION)</span>`
            : `<span class="badge badge-verified">SAFE & ARMED</span>`;
    }

    if (badgeGuardGrounding) {
        badgeGuardGrounding.className = "badge badge-verified";
        badgeGuardGrounding.textContent = "ACTIVE";
    }
    if (badgeGuardTechId) {
        badgeGuardTechId.className = "badge badge-verified";
        badgeGuardTechId.textContent = "PROTECTED";
    }
    if (badgeGuardSeal) {
        badgeGuardSeal.className = "badge badge-verified";
        badgeGuardSeal.textContent = "ENFORCED";
    }
    if (badgeGuardInjection) {
        if (isBlocked) {
            badgeGuardInjection.className = "badge badge-not-found";
            badgeGuardInjection.textContent = "BLOCKED";
        } else {
            badgeGuardInjection.className = "badge badge-verified";
            badgeGuardInjection.textContent = "ACTIVE";
        }
    }
}

function getBadgeClass(status) {
    if (!status) return "neutral";
    const s = status.toUpperCase();
    if (s.includes("VERIFIED") || s.includes("STRONG")) return "verified";
    if (s.includes("CONFIGURED") || s.includes("PARTIAL") || s.includes("LIMITED")) return "configured";
    if (s.includes("NOT_FOUND") || s.includes("NOT FOUND") || s.includes("BLOCKED")) return "not-found";
    return "neutral";
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ============================================================
// OPERATIONAL MEMORY & SUBJECT SWITCH
// ============================================================
function updateOperationalMemory(state) {
    if (!state) return;

    if (memErrorCode) memErrorCode.textContent = state.error_code ? `Error ${state.error_code}` : "None";
    if (memMeterModel) memMeterModel.textContent = state.meter_model ? state.meter_model : "Unknown";
    if (memSystem) memSystem.textContent = state.system ? state.system : "Unknown";
    if (memIssue) memIssue.textContent = state.issue ? state.issue : "None recorded";

    if (memUserLimitations) {
        const limits = state.user_does_not_know || [];
        memUserLimitations.textContent = limits.length > 0 ? limits.join(", ") : "None stated";
    }
}

function updateAnalyticsView(analytics) {
    if (!analytics) return;

    if (totalMessagesCount) {
        totalMessagesCount.textContent = analytics.total_messages || 0;
    }

    // Subject switch
    if (analytics.subject_switch && subjectSwitchBox && subjectSwitchContent) {
        const sw = analytics.subject_switch;
        subjectSwitchBox.style.display = "flex";
        subjectSwitchContent.innerHTML = `
            <span>Switch: <strong>${escapeHtml(sw.previous_topic)}</strong> ➔ <strong>${escapeHtml(sw.current_topic)}</strong></span>
            <span class="badge badge-verified">${escapeHtml(sw.context_status)}</span>
        `;
    }

    // Knowledge Coverage Matrix
    if (analytics.knowledge_coverage && coverageTbody) {
        coverageTbody.innerHTML = "";
        const coverage = analytics.knowledge_coverage;
        for (const [key, item] of Object.entries(coverage)) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight: 500; color: #fff;">${item.category}</td>
                <td><span class="badge badge-${getBadgeClass(item.status)}">${item.status}</span></td>
                <td style="color: var(--text-muted); font-size: 10px;">${item.indexed_source}</td>
            `;
            coverageTbody.appendChild(tr);
        }
    }

    // Knowledge Expansion Recommendations
    if (analytics.expansion_recommendations && recommendationsContainer) {
        recommendationsContainer.innerHTML = "";
        analytics.expansion_recommendations.forEach((rec) => {
            const item = document.createElement("div");
            item.className = "recommendation-item";
            item.innerHTML = `
                <div class="rec-header">
                    <span class="rec-title">${escapeHtml(rec.recommended_manual)}</span>
                    <span class="badge badge-${rec.priority === 'HIGH' ? 'not-found' : 'configured'}">${rec.priority}</span>
                </div>
                <div class="rec-rationale">${escapeHtml(rec.rationale)}</div>
            `;
            recommendationsContainer.appendChild(item);
        });
    }
}

async function fetchAnalytics() {
    try {
        const res = await fetch(`${API_BASE}/api/analytics`);
        if (res.ok) {
            const data = await res.json();
            updateAnalyticsView(data.analytics);
        }
    } catch (err) {
        console.warn("Analytics fetch error:", err);
    }
}

async function fetchCurrentState() {
    try {
        const res = await fetch(`${API_BASE}/api/state`);
        if (res.ok) {
            const data = await res.json();
            updateOperationalMemory(data.state);
        }
    } catch (err) {
        console.warn("State fetch error:", err);
    }
}

// ============================================================
// RESET SESSION
// ============================================================
async function handleResetSession() {
    if (isProcessing) return;
    try {
        const res = await fetch(`${API_BASE}/api/reset`, { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            chatStream.innerHTML = "";
            appendBubble("agent", "A new support case has been opened. How can I assist you with your ISKRA meter today?");
            updateOperationalMemory(data.state);
            updateAnalyticsView(data.analytics);
            if (subjectSwitchBox) subjectSwitchBox.style.display = "none";
            if (evidenceContainer) evidenceContainer.innerHTML = "<div style='font-size: 11px; color: var(--text-muted);'>No evidence evaluated yet.</div>";
        }
    } catch (err) {
        console.error("Reset error:", err);
    }
}

// ============================================================
// EXECUTIVE DEMO RUNNER
// ============================================================
async function runExecutiveDemo() {
    if (isProcessing) return;
    isProcessing = true;
    btnDemo.disabled = true;
    btnSend.disabled = true;

    demoBanner.classList.add("active");
    demoBannerText.textContent = "Running Executive Demo (7 Turns)...";

    // Clear chat
    chatStream.innerHTML = "";
    appendBubble("agent", "Starting live Executive Demo session. Executing 7 adversarial scenarios through verified agent pipeline...");

    try {
        const res = await fetch(`${API_BASE}/api/demo/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
        });

        if (!res.ok) {
            throw new Error(`Demo failed with status ${res.status}`);
        }

        const data = await res.json();
        const steps = data.steps || [];

        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            demoBannerText.textContent = `Demo Step ${step.step}/7: ${step.title}`;

            // Add user bubble
            appendBubble("user", step.input);
            await sleep(600);

            // Add agent response
            appendBubble("agent", step.response, step.latency_ms);

            // Update UI panels with this turn's live trace
            updateDecisionTrace(step.trace, step.decision);
            await sleep(900);
        }

        updateOperationalMemory(data.current_state);
        updateAnalyticsView(data.analytics);
        demoBannerText.textContent = "Executive Demo Complete ✓";
        await sleep(1500);

    } catch (err) {
        appendBubble("agent", `Executive Demo Error: ${err.message}`);
    } finally {
        demoBanner.classList.remove("active");
        isProcessing = false;
        btnDemo.disabled = false;
        btnSend.disabled = false;
    }
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// ============================================================
// AUDIT-READY CASE EXPORT MODAL
// ============================================================
async function openExportModal() {
    try {
        const res = await fetch(`${API_BASE}/api/case/create`, { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            currentCaseData = data.case;
            modalCasePreview.textContent = JSON.stringify(currentCaseData, null, 2);
            exportModal.classList.add("active");
        }
    } catch (err) {
        alert("Failed to generate case preview: " + err.message);
    }
}

function closeExportModal() {
    exportModal.classList.remove("active");
}
