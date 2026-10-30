
const API_URL = "http://127.0.0.1:8000/chat";

const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const chatMessages = document.getElementById("chatMessages");
const activityLog = document.getElementById("activityLog");
const reportContent = document.getElementById("reportContent");
const agentStatus = document.getElementById("agentStatus");

let caseId = null;
let isRunning = false;

function addMessage(role, text) {
  const message = document.createElement("div");
  message.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "✳";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  message.append(avatar, bubble);
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setStatus(text, type = "") {
  agentStatus.textContent = text;
  agentStatus.className = `status-pill ${type}`;
}

function addActivity(event, data) {
  const empty = activityLog.querySelector(".empty-state");
  if (empty) empty.remove();

  const item = document.createElement("div");
  item.className = "activity-item";

  const title = document.createElement("strong");
  title.textContent = event.replaceAll("_", " ").toUpperCase();

  const description = document.createElement("p");
  description.textContent =
    typeof data === "string"
      ? data
      : JSON.stringify(data, null, 2);

  item.append(title, description);
  activityLog.appendChild(item);
  activityLog.scrollTop = activityLog.scrollHeight;
}

function addReportSection(title, content) {
  const section = document.createElement("div");
  section.className = "report-section";

  const heading = document.createElement("h4");
  heading.textContent = title;
  section.appendChild(heading);

  if (Array.isArray(content)) {
    const list = document.createElement("ul");

    for (const entry of content) {
      const li = document.createElement("li");
      li.textContent =
        typeof entry === "string"
          ? entry
          : JSON.stringify(entry);
      list.appendChild(li);
    }

    section.appendChild(list);
  } else {
    const paragraph = document.createElement("p");
    paragraph.textContent = String(content ?? "Not available");
    section.appendChild(paragraph);
  }

  reportContent.appendChild(section);
}

function renderReport(report) {
  reportContent.replaceChildren();

  const status = document.createElement("div");
  status.className = "report-status";

  const workflow = report.workflow_status || "unknown";

  if (workflow === "urgent_review_or_hold") {
    status.classList.add("hold");
  } else if (workflow === "more_information_required") {
    status.classList.add("pending");
  }

  status.textContent = workflow.replaceAll("_", " ").toUpperCase();
  reportContent.appendChild(status);

  addReportSection("Summary", report.summary);

  if (report.batch) {
    const section = document.createElement("div");
    section.className = "report-section";

    const heading = document.createElement("h4");
    heading.textContent = "Extracted Batch Evidence";
    section.appendChild(heading);

    for (const [field, tracked] of Object.entries(report.batch)) {
      const row = document.createElement("div");
      row.className = "evidence-row";

      const label = document.createElement("span");
      label.textContent = field.replaceAll("_", " ");

      const value = document.createElement("span");
      value.textContent =
        `${tracked?.value ?? "Unknown"} (${tracked?.status ?? "unknown"})`;

      row.append(label, value);
      section.appendChild(row);
    }

    reportContent.appendChild(section);
  }

  addReportSection("Missing Evidence", report.missing_evidence || []);
  addReportSection("Safety Concerns", report.concerns || []);
  addReportSection("References", report.references || []);
  addReportSection("Next Step", report.next_step);
}

function handleEvent(event, data) {
  if (event === "case") {
    caseId = data.case_id;
    return;
  }

  if (event === "error") {
    addActivity(event, data);
    addMessage("assistant", data.message || "The agent encountered an error.");
    setStatus("Error", "error");
    return;
  }

  addActivity(event, data);

  if (event === "question") {
    addMessage("assistant", data.text || "Could you provide more information?");
  }

  if (event === "final_report") {
    renderReport(data);

    if (data.summary) {
      addMessage("assistant", data.summary);
    }

    setStatus("Review complete");
  }
}

async function readEventStream(response) {
  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    buffer = buffer.replace(/\r\n/g, "\n");

    let boundary;

    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      let eventName = "message";
      const dataLines = [];

      for (const line of rawEvent.split("\n")) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        }

        if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trimStart());
        }
      }

      if (dataLines.length === 0) continue;

      try {
        const data = JSON.parse(dataLines.join("\n"));
        handleEvent(eventName, data);
      } catch (error) {
        console.error("Could not parse SSE event:", error);
      }
    }
  }
}

async function sendMessage(text) {
  if (isRunning) return;

  isRunning = true;
  sendButton.disabled = true;
  messageInput.disabled = true;
  setStatus("Analyzing...", "running");

  addMessage("user", text);

  activityLog.replaceChildren();

  try {
    const payload = { message: text };

    if (caseId) {
      payload.case_id = caseId;
    }

    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const details = await response.text();
      throw new Error(`Backend returned HTTP ${response.status}: ${details}`);
    }

    await readEventStream(response);

    if (agentStatus.textContent === "Analyzing...") {
      setStatus("Finished");
    }
  } catch (error) {
    console.error(error);
    setStatus("Connection error", "error");
    addMessage("assistant", `Connection failed: ${error.message}`);
  } finally {
    isRunning = false;
    sendButton.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const text = messageInput.value.trim();
  if (!text || isRunning) return;

  messageInput.value = "";
  sendMessage(text);
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});
