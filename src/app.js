let FACTS = {};
let QUICK_FACT_KEYS = [];
const state = {
  userFacts: new Set(),
};

const elements = {
  chatMessages: document.querySelector("#chatMessages"),
  chatForm: document.querySelector("#chatForm"),
  chatInput: document.querySelector("#chatInput"),
  quickFacts: document.querySelector("#quickFacts"),
  workingMemory: document.querySelector("#workingMemory"),
  diagnosisList: document.querySelector("#diagnosisList"),
  traceList: document.querySelector("#traceList"),
  resetButton: document.querySelector("#resetButton"),
};

void boot();

async function boot() {
  try {
    const bootstrap = await fetchJson("/api/bootstrap");
    FACTS = bootstrap.facts;
    QUICK_FACT_KEYS = bootstrap.quickFacts;
    renderQuickFacts();
    appendBotMessage([
      "Xin chào. Tôi là chatbot hệ chuyên gia rule-based hỗ trợ phân tích triệu chứng ở mức học thuật.",
      "Bạn hãy mô tả triệu chứng hoặc bấm các nút gợi ý bên trên. Hệ thống sẽ cập nhật bộ nhớ làm việc và suy diễn tiến để đưa ra kết luận tạm thời.",
    ]);
    syncInterface();
  } catch (error) {
    appendBotMessage([
      "Không khởi tạo được ứng dụng từ Python API.",
      "Hãy chạy `python app.py`, sau đó truy cập `http://127.0.0.1:8000` thay vì mở file HTML trực tiếp.",
    ]);
    console.error(error);
  }

  elements.chatForm.addEventListener("submit", handleSubmit);
  elements.resetButton.addEventListener("click", resetSession);
}

async function handleSubmit(event) {
  event.preventDefault();
  const rawText = elements.chatInput.value.trim();
  if (!rawText) {
    return;
  }

  appendUserMessage(rawText);
  elements.chatInput.value = "";
  try {
    await sendAnalyzeRequest(rawText);
  } catch (error) {
    appendBotMessage([
      "Không gọi được bộ suy diễn Python.",
      "Hãy kiểm tra lại việc chạy `python app.py` và tải lại trang.",
    ]);
    console.error(error);
  }
}

function renderQuickFacts() {
  elements.quickFacts.innerHTML = "";

  QUICK_FACT_KEYS.forEach((factKey) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "fact-chip";
    button.textContent = FACTS[factKey].label;
    button.addEventListener("click", () => toggleQuickFact(factKey));
    elements.quickFacts.appendChild(button);
  });
}

function toggleQuickFact(factKey) {
  if (state.userFacts.has(factKey)) {
    state.userFacts.delete(factKey);
    appendBotMessage([`Tôi đã bỏ triệu chứng ${FACTS[factKey].label.toLowerCase()} khỏi bộ nhớ làm việc.`]);
    syncInterface(emptyResult());
    return;
  }

  state.userFacts.add(factKey);
  appendUserMessage(FACTS[factKey].label);
  void sendAnalyzeRequest("").catch((error) => {
    appendBotMessage([
      "Không gọi được bộ suy diễn Python.",
      "Hãy kiểm tra lại việc chạy `python app.py` và tải lại trang.",
    ]);
    console.error(error);
  });
}

function syncInterface(result = emptyResult()) {
  renderWorkingMemory(result.workingMemory);
  renderDiagnoses(result.diagnoses);
  renderTrace(result.trace);
  syncQuickFactState();
}

function renderWorkingMemory(workingMemory) {
  elements.workingMemory.innerHTML = "";

  const userVisibleFacts = workingMemory
    .filter((fact) => FACTS[fact])
    .sort((a, b) => FACTS[a].label.localeCompare(FACTS[b].label, "vi"));

  if (userVisibleFacts.length === 0) {
    elements.workingMemory.innerHTML = `<p class="empty-state">Chưa có dữ kiện nào.</p>`;
    return;
  }

  userVisibleFacts.forEach((fact) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = FACTS[fact].label;
    elements.workingMemory.appendChild(pill);
  });
}

function renderDiagnoses(diagnoses) {
  elements.diagnosisList.innerHTML = "";

  if (diagnoses.length === 0) {
    elements.diagnosisList.innerHTML = `<p class="empty-state">Chưa đủ điều kiện để sinh kết luận.</p>`;
    return;
  }

  diagnoses.forEach((diagnosis) => {
    const card = document.createElement("article");
    card.className = `diagnosis-card ${diagnosis.priority}`;
    card.innerHTML = `
      <span class="badge ${diagnosis.priority}">${priorityLabel(diagnosis.priority)}</span>
      <h4>${diagnosis.label}</h4>
      <p>${diagnosis.advice}</p>
    `;
    elements.diagnosisList.appendChild(card);
  });
}

function renderTrace(trace) {
  elements.traceList.innerHTML = "";

  if (trace.length === 0) {
    elements.traceList.innerHTML = `<p class="empty-state">Chưa có luật nào được kích hoạt.</p>`;
    return;
  }

  trace.forEach((step) => {
    const item = document.createElement("article");
    item.className = "trace-item";
    const antecedents = step.antecedents.map((fact) => FACTS[fact].label).join(" ∧ ");
    item.innerHTML = `
      <strong>${step.ruleId}: ${antecedents} → ${FACTS[step.consequent].label}</strong>
      <p>${step.explanation}</p>
    `;
    elements.traceList.appendChild(item);
  });
}

function appendUserMessage(text) {
  appendMessage(text, "user");
}

function appendBotMessage(lines) {
  appendMessage(lines.join("\n\n"), "bot");
}

function appendMessage(text, role) {
  const message = document.createElement("article");
  message.className = `message ${role}`;

  text.split("\n\n").forEach((paragraphText) => {
    const paragraph = document.createElement("p");
    paragraph.textContent = paragraphText;
    message.appendChild(paragraph);
  });

  elements.chatMessages.appendChild(message);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function syncQuickFactState() {
  const buttons = [...elements.quickFacts.querySelectorAll(".fact-chip")];
  QUICK_FACT_KEYS.forEach((factKey, index) => {
    buttons[index]?.classList.toggle("active", state.userFacts.has(factKey));
  });
}

function priorityLabel(priority) {
  return {
    high: "Ưu tiên cao",
    medium: "Theo dõi sát",
    low: "Ưu tiên thấp",
  }[priority] || "Chưa phân loại";
}

function resetSession() {
  state.userFacts.clear();
  elements.chatMessages.innerHTML = "";
  appendBotMessage([
    "Phiên tư vấn đã được làm mới.",
    "Bạn hãy nhập lại triệu chứng để hệ thống xây dựng bộ nhớ làm việc mới.",
  ]);
  syncInterface();
}

async function sendAnalyzeRequest(message) {
  const result = await fetchJson("/api/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      userFacts: [...state.userFacts],
    }),
  });

  state.userFacts = new Set(result.userFacts);
  syncInterface(result);
  if (result.botMessages?.length) {
    appendBotMessage(result.botMessages);
  }
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function emptyResult() {
  return {
    workingMemory: [...state.userFacts],
    diagnoses: [],
    trace: [],
  };
}
