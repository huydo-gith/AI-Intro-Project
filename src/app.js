let FACTS = {};
let QUICK_FACT_KEYS = [];

const state = {
  userFacts: new Set(),
  lastResult: null,
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
  conflictStrategySelect: document.querySelector("#conflictStrategySelect"),
  explanationModal: document.querySelector("#explanationModal"),
  closeExpBtn: document.querySelector("#closeExpBtn"),
  expRuleId: document.querySelector("#expRuleId"),
  expRuleFormula: document.querySelector("#expRuleFormula"),
  expDetailedText: document.querySelector("#expDetailedText"),
  expSymptomsList: document.querySelector("#expSymptomsList"),
  expConfidenceBreakdown: document.querySelector("#expConfidenceBreakdown"),

  // Diagnosis Modal Elements
  diagExplanationModal: document.querySelector("#diagExplanationModal"),
  closeDiagExpBtn: document.querySelector("#closeDiagExpBtn"),
  expDiagLabel: document.querySelector("#expDiagLabel"),
  expDiagChain: document.querySelector("#expDiagChain"),
};

void boot();

async function boot() {
  try {
    const bootstrap = await fetchJson("/api/bootstrap");
    FACTS = bootstrap.facts;
    QUICK_FACT_KEYS = bootstrap.quickFacts;
    renderQuickFacts();
    appendBotMessage([
      "👋 Xin chào! Tôi là trợ lý phân tích triệu chứng của hệ chuyên gia y tế. Hãy mô tả những gì bạn đang cảm thấy — tôi sẽ lắng nghe và hỗ trợ bạn nhé.",
      "💡 Bạn có thể nhập tự nhiên như: <em>\"tôi bị sốt, ho và đau họng\"</em>, hoặc bấm vào các triệu chứng gợi ý bên trên để bắt đầu nhanh hơn.",
    ]);
    syncInterface();
  } catch (error) {
    appendBotMessage([
      "❌ Không khởi tạo được ứng dụng từ Python API.",
      "Hãy chạy `python app.py`, sau đó truy cập `http://127.0.0.1:8000` thay vì mở file HTML trực tiếp.",
    ]);
    console.error(error);
  }

  // Original events
  elements.chatForm.addEventListener("submit", handleSubmit);
  elements.resetButton.addEventListener("click", resetSession);
  elements.conflictStrategySelect.addEventListener("change", () => {
    sendAnalyzeRequest("").catch((error) => console.error(error));
  });
  elements.closeExpBtn.addEventListener("click", () => {
    elements.explanationModal.classList.add("hidden");
  });
  elements.closeDiagExpBtn.addEventListener("click", () => {
    elements.diagExplanationModal.classList.add("hidden");
  });
}

/* Original Chat Logic Functions */
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
      "❌ Không gọi được bộ suy diễn Python.",
      "Hãy kiểm tra lại việc chạy `python app.py` và tải lại trang.",
    ]);
    console.error(error);
  }
}

function renderQuickFacts() {
  elements.quickFacts.innerHTML = "";

  QUICK_FACT_KEYS.forEach((factKey) => {
    if (!FACTS[factKey]) return;
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
    appendBotMessage([`Tôi đã bỏ triệu chứng "${FACTS[factKey].label.toLowerCase()}" khỏi bộ nhớ làm việc.`]);
    syncInterface(emptyResult());
    return;
  }

  state.userFacts.add(factKey);
  appendUserMessage(FACTS[factKey].label);
  void sendAnalyzeRequest("").catch((error) => {
    appendBotMessage([
      "❌ Không gọi được bộ suy diễn Python.",
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

  const memoryItems = workingMemory
    .map((item) => {
      const [factKey, confidence] = Array.isArray(item) ? item : [item, 100];
      return { key: factKey, confidence };
    })
    .filter((item) => FACTS[item.key])
    .sort((a, b) => FACTS[a.key].label.localeCompare(FACTS[b.key].label, "vi"));

  if (memoryItems.length === 0) {
    elements.workingMemory.innerHTML = `<p class="empty-state">Chưa có dữ kiện nào.</p>`;
    return;
  }

  memoryItems.forEach(({ key, confidence }) => {
    const pill = document.createElement("span");
    pill.className = `pill confidence-${getConfidenceLevel(confidence)}`;
    const confidenceDisplay = confidence < 100 ? ` (${confidence.toFixed(0)}%)` : "";
    pill.innerHTML = `
      ${FACTS[key].label}
      <span class="confidence-badge" title="Độ tin cậy">${confidenceDisplay || "✓"}</span>
    `;
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
    const confidenceLevel = getConfidenceLevel(diagnosis.confidence);
    card.className = `diagnosis-card ${diagnosis.priority} confidence-${confidenceLevel}`;

    const confidenceBar = createConfidenceBar(diagnosis.confidence);

    card.innerHTML = `
      <div class="diagnosis-header">
        <span class="badge ${diagnosis.priority}">${priorityLabel(diagnosis.priority)}</span>
        <h4>${diagnosis.label}</h4>
        <span class="confidence-pct">${(diagnosis.confidence || 0).toFixed(0)}%</span>
      </div>
      <div class="confidence-bar">${confidenceBar}</div>
      <p class="diagnosis-advice">${diagnosis.advice}</p>
      <button class="ghost-button explain-diag-btn" type="button" style="margin-top: 10px; width: 100%; font-size: 0.85rem; padding: 6px;" data-key="${diagnosis.key}">
        🔍 Giải thích lập luận bệnh
      </button>
    `;

    card.querySelector(".explain-diag-btn").addEventListener("click", () => {
      showDiagnosisExplanation(diagnosis.key);
    });

    elements.diagnosisList.appendChild(card);
  });
}

function renderTrace(trace) {
  elements.traceList.innerHTML = "";

  if (trace.length === 0) {
    elements.traceList.innerHTML = `<p class="empty-state">Chưa có luật nào được kích hoạt.</p>`;
    return;
  }

  const traceContainer = document.createElement("div");
  traceContainer.className = "trace-flow";

  trace.forEach((step, index) => {
    const item = document.createElement("div");
    item.className = "trace-step";
    item.title = "Bấm để xem giải thích chi tiết cho luật này";

    const antecedents = step.antecedents
      .map((fact) => `<span class="fact-label">${FACTS[fact]?.label || fact}</span>`)
      .join('<span class="operator"> ∧ </span>');

    const consequent = `<span class="fact-label derived">${FACTS[step.consequent]?.label || step.consequent}</span>`;
    const ruleConfidence = step.confidence || 80;
    const derivedConfidence = step.derivedConfidence || "?";

    item.innerHTML = `
      <div class="trace-rule">
        <div class="trace-antecedents">${antecedents}</div>
        <div class="trace-arrow">⟹ <span class="rule-id">${step.ruleId}</span> <span class="rule-conf" title="Độ tin cậy luật">${ruleConfidence}%</span></div>
        <div class="trace-consequent">${consequent}</div>
        <div class="trace-derived-conf">Độ tin cậy: <strong>${derivedConfidence}%</strong></div>
      </div>
      <p class="trace-explanation">${step.explanation}</p>
    `;

    item.addEventListener("click", () => showRuleExplanation(step.ruleId));

    if (index > 0) {
      const connector = document.createElement("div");
      connector.className = "trace-connector";
      connector.innerHTML = "↓";
      traceContainer.appendChild(connector);
    }

    traceContainer.appendChild(item);
  });

  elements.traceList.appendChild(traceContainer);
}

async function showRuleExplanation(ruleId) {
  if (!state.lastResult) return;
  try {
    const explanation = await fetchJson("/api/explain-rule", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        rule_id: ruleId,
        trace: state.lastResult.trace,
        diagnoses: state.lastResult.diagnoses,
      }),
    });

    elements.expRuleId.textContent = explanation.rule_id;
    
    const antecedentsText = explanation.contributing_symptoms.map(s => s.label).join(" ∧ ") || "Điều kiện dẫn xuất";
    elements.expRuleFormula.innerHTML = `<span class="fact-label">${antecedentsText}</span> <span class="operator">⟹</span> <span class="fact-label derived">${explanation.consequent_label} (${explanation.confidence_percentage})</span>`;
    
    elements.expDetailedText.textContent = explanation.detailed_explanation || explanation.short_explanation;
    
    elements.expSymptomsList.innerHTML = "";
    if (!explanation.contributing_symptoms || explanation.contributing_symptoms.length === 0) {
      elements.expSymptomsList.innerHTML = '<span style="color: var(--muted); font-style: italic;">Không có triệu chứng trực tiếp (sử dụng sự kiện dẫn xuất)</span>';
    } else {
      explanation.contributing_symptoms.forEach(s => {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = s.label;
        elements.expSymptomsList.appendChild(pill);
      });
    }
    
    elements.expConfidenceBreakdown.textContent = explanation.confidence_breakdown;
    elements.explanationModal.classList.remove("hidden");
  } catch (error) {
    console.error("Failed to fetch rule explanation:", error);
    alert("Không thể tải thông tin giải thích cho luật này.");
  }
}

function createConfidenceBar(confidence) {
  const percentage = Math.round(confidence);
  return `<span class="bar-visual">
    <span class="bar-filled" style="width: ${percentage}%"></span>
    <span class="bar-label">${percentage}%</span>
  </span>`;
}

function getConfidenceLevel(confidence) {
  if (confidence >= 80) return "high";
  if (confidence >= 50) return "medium";
  return "low";
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
    if (role === "bot") {
      paragraph.innerHTML = paragraphText;
    } else {
      paragraph.textContent = paragraphText;
    }
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
    high: "🔴 Ưu tiên cao",
    medium: "🟡 Theo dõi sát",
    low: "🟢 Ưu tiên thấp",
  }[priority] || "⚪ Chưa phân loại";
}

function resetSession() {
  state.userFacts.clear();
  state.lastResult = null;
  elements.chatMessages.innerHTML = "";
  appendBotMessage([
    "🔄 Phiên tư vấn đã được làm mới. Bạn hãy mô tả lại triệu chứng để bắt đầu phân tích mới nhé!",
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
      conflictStrategy: elements.conflictStrategySelect ? elements.conflictStrategySelect.value : "all_rules",
    }),
  });

  state.userFacts = new Set(result.userFacts);
  state.lastResult = result;
  syncInterface(result);
  if (result.botMessages?.length) {
    appendBotMessage(result.botMessages);
  }
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
  }
  return response.json();
}

function emptyResult() {
  return {
    workingMemory: [...state.userFacts].map((fact) => [fact, 100]),
    diagnoses: [],
    trace: [],
  };
}

async function showDiagnosisExplanation(diagnosisKey) {
  if (!state.lastResult) return;
  try {
    const explanation = await fetchJson("/api/explain-diagnosis", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        diagnosis: diagnosisKey,
        trace: state.lastResult.trace,
      }),
    });

    elements.expDiagLabel.textContent = explanation.diagnosis_label;
    elements.expDiagChain.textContent = explanation.reasoning_chain.join("\n");
    elements.diagExplanationModal.classList.remove("hidden");
  } catch (error) {
    console.error("Failed to fetch diagnosis explanation:", error);
    alert("Không thể tải thông tin giải thích lập luận.");
  }
}
