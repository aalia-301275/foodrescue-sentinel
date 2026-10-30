const page = document.body.dataset.page;
const query = new URLSearchParams(location.search);
const requestedApi = query.get("api");
if (requestedApi) localStorage.setItem("sentinel-api-base", requestedApi);
const API_BASE = requestedApi || localStorage.getItem("sentinel-api-base") || "http://127.0.0.1:8000";
const FIELDS = [
	["product_type", "Product type"], ["quantity", "Quantity"], ["prepared_at", "Prepared at"],
	["storage_temperature", "Storage temperature"], ["storage_history", "Storage history"], ["packaging_condition", "Packaging condition"]
];
const STATUS_LABELS = {
	ready_for_human_review: "Ready for human review",
	more_information_required: "More information required",
	urgent_review_or_hold: "Urgent review or hold"
};
const state = {
	cases: [],
	selectedCase: null,
	selectedCaseId: query.get("case") || localStorage.getItem("sentinel-selected-case"),
	reviews: [],
	limits: [],
	warnings: []
};
const byId = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[char]);

function safeHref(value) {
	try {
		const url = new URL(value);
		return url.protocol === "http:" || url.protocol === "https:" ? url.href : "#";
	} catch (_) { return "#"; }
}

function statusClass(status) {
	if (status === "urgent_review_or_hold") return "urgent";
	if (status === "ready_for_human_review") return "ready";
	return "info";
}

function statusText(status) { return STATUS_LABELS[status] || status || "Unknown status"; }

async function api(path, options = {}) {
	const response = await fetch(`${API_BASE}${path}`, {
		...options,
		headers: { "Content-Type": "application/json", ...(options.headers || {}) }
	});
	if (!response.ok) {
		let detail = `${response.status} ${response.statusText}`;
		try { const body = await response.json(); detail = body.detail || detail; } catch (_) {}
		throw new Error(detail);
	}
	return response.status === 204 ? null : response.json();
}

function updateConnection(online) {
	const dot = byId("connectionDot");
	if (!dot) return;
	dot.classList.toggle("online", online);
	byId("connectionLabel").textContent = online ? "API connected" : "API unavailable";
	byId("apiAddress").textContent = API_BASE;
}

function showNotice(id, message, kind = "") {
	const target = byId(id);
	if (!target) return;
	target.textContent = message;
	target.className = `notice${kind ? ` ${kind}` : ""}`;
}

function hideNotice(id) { byId(id)?.classList.add("hidden"); }
function caseLabel(report) { return report.batch?.product_type?.value || report.case_id; }

function renderQueue(targetId, cases) {
	const target = byId(targetId);
	if (!target) return;
	if (!cases.length) { target.innerHTML = '<div class="empty">No cases have been added yet.</div>'; return; }
	target.innerHTML = cases.map((report) => `<a class="case-row" href="cases.html?case=${encodeURIComponent(report.case_id)}"><span><span class="case-title">${esc(caseLabel(report))}</span><span class="case-meta">${esc(report.case_id)} · ${esc(report.batch?.quantity?.value || "Quantity unknown")}</span></span><span class="badge ${statusClass(report.workflow_status)}">${esc(statusText(report.workflow_status))}</span></a>`).join("");
}

async function loadOverview() {
	hideNotice("globalNotice");
	try {
		const [cases, limits] = await Promise.all([api("/cases"), api("/rules/limits")]);
		state.cases = cases;
		state.limits = limits.limits || [];
		byId("metricCases").textContent = cases.length;
		byId("metricInfo").textContent = cases.filter((item) => item.workflow_status === "more_information_required").length;
		byId("metricUrgent").textContent = cases.filter((item) => item.workflow_status === "urgent_review_or_hold").length;
		byId("metricLimits").textContent = limits.count ?? state.limits.length;
		renderQueue("overviewCases", cases);
		updateConnection(true);
	} catch (error) {
		updateConnection(false);
		showNotice("globalNotice", `Could not connect to the API at ${API_BASE}. ${error.message}`, "error");
		if (byId("overviewCases")) byId("overviewCases").innerHTML = '<div class="empty">The case queue is unavailable until the API is running.</div>';
	}
}

async function loadCases() {
	try {
		state.cases = await api("/cases");
		updateConnection(true);
		if (!state.cases.length) {
			byId("casePicker").innerHTML = '<div class="empty">No cases available.</div>';
			byId("caseDetail").innerHTML = '<div class="panel empty">No cases have been added yet.</div>';
			return;
		}
		if (!state.cases.some((item) => item.case_id === state.selectedCaseId)) state.selectedCaseId = state.cases[0].case_id;
		localStorage.setItem("sentinel-selected-case", state.selectedCaseId);
		renderCasePicker();
		await selectCase(state.selectedCaseId);
	} catch (error) {
		updateConnection(false);
		showNotice("caseNotice", `Could not load cases: ${error.message}`, "error");
		byId("casePicker").innerHTML = '<div class="empty">The case list is unavailable until the API is running.</div>';
		byId("caseDetail").innerHTML = '<div class="panel empty">Case details are unavailable until the API is running.</div>';
	}
}

function renderCasePicker() {
	byId("caseCount").textContent = `${state.cases.length}`;
	byId("casePicker").innerHTML = state.cases.map((report) => `<button class="case-option ${state.selectedCaseId === report.case_id ? "selected" : ""}" data-case-id="${esc(report.case_id)}"><strong>${esc(caseLabel(report))}</strong><small>${esc(report.case_id)}</small></button>`).join("");
}

async function selectCase(caseId) {
	hideNotice("caseNotice");
	state.selectedCaseId = caseId;
	localStorage.setItem("sentinel-selected-case", caseId);
	try {
		const [report, reviews] = await Promise.all([
			api(`/cases/${encodeURIComponent(caseId)}`),
			api(`/cases/${encodeURIComponent(caseId)}/reviews`)
		]);
		state.selectedCase = report;
		state.reviews = reviews;
		renderCasePicker();
		renderCaseDetail();
		updateConnection(true);
	} catch (error) { showNotice("caseNotice", `Could not load this case: ${error.message}`, "error"); }
}

function renderCaseDetail() {
	const report = state.selectedCase;
	const fields = FIELDS.map(([key, label]) => {
		const item = report.batch?.[key] || { value: null, status: "unknown" };
		return `<div class="field-item"><div class="field-label">${esc(label)}</div><div class="field-value">${esc(item.value || "Not provided")}</div><span class="field-status ${esc(item.status)}">${esc(item.status)}</span></div>`;
	}).join("");
	const concerns = (report.concerns || []).map((item) => `<li class="concern">${esc(item.text)} <span class="case-meta">${esc(item.source)}</span></li>`).join("") || "<li>No concerns recorded.</li>";
	const references = (report.references || []).map((item) => `<div class="reference"><strong>${esc(item.title)}</strong><small>${esc(item.passage)}</small></div>`).join("") || '<div class="empty">No references attached.</div>';
	const missing = (report.missing_evidence || []).map((item) => `<li>${esc(item)}</li>`).join("") || "<li>No missing evidence listed.</li>";
	const reviews = state.reviews.length ? state.reviews.map((item) => `<div class="review-entry"><div class="review-entry-head"><span>${esc(item.reviewer)} · ${esc(item.decision.replaceAll("_", " "))}</span><time>${esc(item.reviewed_at)}</time></div><p>${esc(item.notes || "No notes added.")}</p></div>`).join("") : '<div class="empty">No human decisions recorded for this case.</div>';
	byId("caseDetail").innerHTML = `
		<section class="panel"><div class="case-summary"><div><div class="case-id">${esc(report.case_id)}</div><h2>${esc(caseLabel(report))}</h2><p class="summary-text">${esc(report.summary)}</p></div><span class="badge ${statusClass(report.workflow_status)}">${esc(statusText(report.workflow_status))}</span></div><div class="field-grid">${fields}</div><div class="notice" style="margin:14px 0 0">Next step: ${esc(report.next_step)}</div></section>
		<div class="detail-grid"><section class="panel"><h2>Missing evidence</h2><ul class="plain-list">${missing}</ul><h3 style="margin-top:19px">Concerns</h3><ul class="plain-list">${concerns}</ul></section><section class="panel"><h2>References</h2>${references}</section></div>
		<div class="review-grid"><section class="panel"><div class="panel-heading"><div><h2>Record human review</h2><div class="panel-note">A human decision is required for every case.</div></div></div><form id="reviewForm"><div class="form-grid"><div class="form-field"><label for="reviewer">Reviewer</label><input id="reviewer" name="reviewer" required placeholder="Name" autocomplete="name"></div><div class="form-field"><label for="decision">Decision</label><select id="decision" name="decision"><option value="proceed">Proceed</option><option value="request_info">Request information</option><option value="hold">Hold</option><option value="reject">Reject</option></select></div><div class="form-field full"><label for="reviewNotes">Notes</label><textarea id="reviewNotes" name="notes" placeholder="Context, evidence reviewed, and follow-up…"></textarea></div></div><button class="button primary" type="submit">Save review</button></form></section><section class="panel"><h2>Review history</h2><div class="review-history">${reviews}</div></section></div>
		<section class="panel"><div class="panel-heading"><div><h2>Ask about this case</h2><div class="panel-note">Chat currently streams the backend's demo analysis events.</div></div></div><div id="chatStream" class="chat-stream"><div class="chat-event"><strong>System</strong>Send a message to start the streamed analysis.</div></div><form id="chatForm" class="chat-form"><input name="message" required placeholder="Ask a follow-up or provide additional context"><button class="button primary" type="submit">Send</button></form></section>`;
	byId("reviewForm").addEventListener("submit", submitReview);
	byId("chatForm").addEventListener("submit", sendChat);
}

async function submitReview(event) {
	event.preventDefault();
	const form = event.currentTarget;
	const submit = form.querySelector("button[type=submit]");
	submit.disabled = true;
	try {
		const data = Object.fromEntries(new FormData(form).entries());
		await api(`/cases/${encodeURIComponent(state.selectedCase.case_id)}/review`, { method: "POST", body: JSON.stringify(data) });
		await selectCase(state.selectedCase.case_id);
		showNotice("caseNotice", "Human review saved.", "success");
	} catch (error) { showNotice("caseNotice", `Review was not saved: ${error.message}`, "error"); }
	finally { if (submit.isConnected) submit.disabled = false; }
}

function appendChatEvent(stream, title, text, kind = "") {
	const item = document.createElement("div");
	item.className = `chat-event ${kind}`;
	const heading = document.createElement("strong");
	heading.textContent = title;
	item.append(heading, document.createTextNode(text));
	stream.append(item);
	stream.scrollTop = stream.scrollHeight;
}

async function sendChat(event) {
	event.preventDefault();
	const form = event.currentTarget;
	const input = form.elements.message;
	const button = form.querySelector("button");
	const stream = byId("chatStream");
	const message = input.value.trim();
	if (!message) return;
	stream.innerHTML = "";
	appendChatEvent(stream, "You", message);
	input.value = "";
	button.disabled = true;
	try {
		const response = await fetch(`${API_BASE}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ case_id: state.selectedCase.case_id, message }) });
		if (!response.ok || !response.body) throw new Error(`Chat request failed (${response.status})`);
		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let buffer = "";
		while (true) {
			const { value, done } = await reader.read();
			buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
			const parts = buffer.split("\n\n");
			buffer = parts.pop() || "";
			for (const part of parts) {
				const eventName = part.match(/^event:\s*(.+)$/m)?.[1] || "update";
				const payload = part.match(/^data:\s*(.+)$/m)?.[1];
				if (!payload) continue;
				const data = JSON.parse(payload);
				const detail = eventName === "final_report" ? `${data.summary || "Report received."} ${data.next_step || ""}` : data.text || data.summary || data.input || data.rule || JSON.stringify(data);
				const kind = eventName === "question" ? "question" : eventName === "final_report" ? "final" : "";
				appendChatEvent(stream, eventName.replaceAll("_", " "), detail, kind);
			}
			if (done) break;
		}
	} catch (error) { appendChatEvent(stream, "Connection error", error.message, "question"); }
	finally { button.disabled = false; }
}

function renderRuleFields(batch = null) {
	byId("ruleFields").innerHTML = FIELDS.map(([key, label]) => {
		const item = batch?.[key] || { value: "", status: "unknown" };
		return `<div class="tracked-field"><div class="form-field"><label for="field-${key}">${esc(label)}</label><input id="field-${key}" name="${key}.value" value="${esc(item.value || "")}" placeholder="Enter ${esc(label.toLowerCase())}"></div><div class="form-field"><label for="status-${key}">Evidence</label><select id="status-${key}" name="${key}.status"><option value="unknown" ${item.status === "unknown" ? "selected" : ""}>Unknown</option><option value="inferred" ${item.status === "inferred" ? "selected" : ""}>Inferred</option><option value="confirmed" ${item.status === "confirmed" ? "selected" : ""}>Confirmed</option></select></div></div>`;
	}).join("");
}

function batchFromRuleForm(form) {
	const data = new FormData(form);
	return Object.fromEntries(FIELDS.map(([key]) => [key, { value: String(data.get(`${key}.value`) || "").trim() || null, status: data.get(`${key}.status`) }]));
}

function renderRuleOutput(result) {
	const status = result.workflow_status;
	const resultRows = (result.results || []).map((item) => {
		const flag = item.passed === true ? "PASS" : item.passed === false ? "CHECK" : "N/A";
		const cls = item.passed === true ? "pass" : item.passed === false ? "fail" : "na";
		const source = item.source ? `<a href="${esc(safeHref(item.link))}" target="_blank" rel="noreferrer">Source: ${esc(item.source)}</a>` : "";
		return `<div class="rule-result"><div class="rule-result-head"><span class="rule-result-name">${esc(item.rule.replaceAll("_", " "))}</span><span class="result-flag ${cls}">${flag}</span></div><p>${esc(item.message)}</p>${source}</div>`;
	}).join("");
	byId("ruleOutput").innerHTML = `<div class="workflow-box"><span class="badge ${statusClass(status)}">Workflow status</span><strong>${esc(statusText(status))}</strong><p>This is not a safety verdict. A human reviewer must assess the case.</p></div><div class="rule-results">${resultRows}</div>`;
}

async function evaluateRules(event) {
	event.preventDefault();
	hideNotice("rulesNotice");
	const button = event.currentTarget.querySelector("button[type=submit]");
	button.disabled = true;
	try {
		const result = await api("/rules/check", { method: "POST", body: JSON.stringify(batchFromRuleForm(event.currentTarget)) });
		renderRuleOutput(result);
	} catch (error) { showNotice("rulesNotice", `Could not evaluate this batch: ${error.message}`, "error"); }
	finally { button.disabled = false; }
}

async function loadSelectedCaseIntoRules() {
	if (!state.selectedCaseId) { showNotice("rulesNotice", "Select a case in Case review first."); return; }
	try {
		const report = await api(`/cases/${encodeURIComponent(state.selectedCaseId)}`);
		state.selectedCase = report;
		localStorage.setItem("sentinel-selected-case", report.case_id);
		renderRuleFields(report.batch);
		showNotice("rulesNotice", `Loaded ${report.case_id}. Check the evidence status before evaluating.`, "success");
	} catch (error) { showNotice("rulesNotice", `Could not load the selected case: ${error.message}`, "error"); }
}

async function loadLimits() {
	try {
		const data = await api("/rules/limits");
		state.limits = data.limits || [];
		state.warnings = data.warnings || [];
		renderLimits(data.count);
		updateConnection(true);
	} catch (error) {
		updateConnection(false);
		byId("limitsTable").innerHTML = `<div class="empty">Could not load limits: ${esc(error.message)}</div>`;
	}
}

function renderLimits(count = state.limits.length) {
	byId("limitsCount").textContent = `${count} loaded`;
	if (!state.limits.length) {
		byId("limitsTable").innerHTML = '<div class="notice">No source-backed time limits are configured. The evaluator will not invent a limit; time-window results may be unavailable.</div>';
	} else {
		byId("limitsTable").innerHTML = `<table><thead><tr><th>Food keyword</th><th>Storage</th><th>Maximum</th><th>Clock starts</th><th>Source</th></tr></thead><tbody>${state.limits.map((item) => `<tr><td>${esc(item.keyword)}</td><td>${esc(item.condition)}</td><td>${esc(item.max_hours)} h</td><td>${esc(item.clock_starts || "Not stated")}</td><td><a href="${esc(safeHref(item.link))}" target="_blank" rel="noreferrer">${esc(item.source_document)}, ${esc(item.section)}</a></td></tr>`).join("")}</tbody></table>`;
	}
	byId("limitsWarnings").innerHTML = state.warnings.length ? state.warnings.map((warning) => `<div class="warning-row">${esc(warning)}</div>`).join("") : "";
}

async function reloadLimits() {
	const button = byId("reloadLimits");
	button.disabled = true;
	hideNotice("limitsNotice");
	try {
		const data = await api("/rules/reload", { method: "POST" });
		await loadLimits();
		showNotice("limitsNotice", `Reload complete. ${data.count} source-backed limit${data.count === 1 ? "" : "s"} loaded.`, "success");
	} catch (error) { showNotice("limitsNotice", `Could not reload limits: ${error.message}`, "error"); }
	finally { button.disabled = false; }
}

document.addEventListener("click", (event) => {
	const caseButton = event.target.closest("[data-case-id]");
	if (caseButton) selectCase(caseButton.dataset.caseId);
});

const dateLabel = byId("todayLabel");
if (dateLabel) dateLabel.textContent = new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" }).format(new Date());

api("/health").then(() => updateConnection(true)).catch(() => updateConnection(false));
if (page === "overview") {
	byId("refreshOverview").addEventListener("click", loadOverview);
	loadOverview();
} else if (page === "cases") {
	byId("refreshCases").addEventListener("click", loadCases);
	loadCases();
} else if (page === "rules") {
	renderRuleFields();
	byId("loadCaseIntoRules").addEventListener("click", loadSelectedCaseIntoRules);
	byId("ruleForm").addEventListener("submit", evaluateRules);
} else if (page === "limits") {
	byId("reloadLimits").addEventListener("click", reloadLimits);
	loadLimits();
}