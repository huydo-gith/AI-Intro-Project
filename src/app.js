let FACTS = {};
let QUICK_FACT_KEYS = [];
let kbData = { facts: {}, rules: [], diagnosisMetadata: {}, quickFacts: [] };
let editingRuleId = null;
let editingFactKey = null;

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

  // Tab elements
  tabChat: document.querySelector("#tabChat"),
  tabKB: document.querySelector("#tabKB"),
  chatTabContent: document.querySelector("#chatTabContent"),
  kbTabContent: document.querySelector("#kbTabContent"),

  // KB Sidebar tabs
  subTabRules: document.querySelector("#subTabRules"),
  subTabFacts: document.querySelector("#subTabFacts"),
  subContentRules: document.querySelector("#subContentRules"),
  subContentFacts: document.querySelector("#subContentFacts"),

  // KB search and add
  ruleSearch: document.querySelector("#ruleSearch"),
  factSearch: document.querySelector("#factSearch"),
  addRuleBtn: document.querySelector("#addRuleBtn"),
  addFactBtn: document.querySelector("#addFactBtn"),

  // KB lists
  rulesTableBody: document.querySelector("#rulesTableBody"),
  factsTableBody: document.querySelector("#factsTableBody"),

  // Modals
  ruleModal: document.querySelector("#ruleModal"),
  factModal: document.querySelector("#factModal"),
  ruleForm: document.querySelector("#ruleForm"),
  factForm: document.querySelector("#factForm"),
  cancelRuleBtn: document.querySelector("#cancelRuleBtn"),
  cancelFactBtn: document.querySelector("#cancelFactBtn"),

  // Rule Modal Fields
  ruleIdInput: document.querySelector("#ruleIdInput"),
  antecedentsSelectGrid: document.querySelector("#antecedentsSelectGrid"),
  consequentSelect: document.querySelector("#consequentSelect"),
  confidenceInput: document.querySelector("#confidenceInput"),
  ruleExplanationInput: document.querySelector("#ruleExplanationInput"),

  // Fact Modal Fields
  factKeyInput: document.querySelector("#factKeyInput"),
  factLabelInput: document.querySelector("#factLabelInput"),
  factCategorySelect: document.querySelector("#factCategorySelect"),
  factSynonymsInput: document.querySelector("#factSynonymsInput"),
  factQuickFactCheckbox: document.querySelector("#factQuickFactCheckbox"),
  quickFactGroup: document.querySelector("#quickFactGroup"),
  diagnosisFields: document.querySelector("#diagnosisFields"),
  diagPrioritySelect: document.querySelector("#diagPrioritySelect"),
  diagAdviceInput: document.querySelector("#diagAdviceInput"),
};

void boot();

async function boot() {
  try {
    const bootstrap = await fetchJson("/api/bootstrap");
    FACTS = bootstrap.facts;
    QUICK_FACT_KEYS = bootstrap.quickFacts;
    renderQuickFacts();
    appendBotMessage([
      "👋 Xin chào. Tôi là chatbot hệ chuyên gia rule-based hỗ trợ phân tích triệu chứng ở mức học thuật.",
      "Bạn hãy mô tả triệu chứng hoặc bấm các nút gợi ý bên trên. Hệ thống sẽ cập nhật bộ nhớ làm việc, tính độ tin cậy và suy diễn tiến để đưa ra kết luận tạm thời.",
    ]);
    syncInterface();

    // Load initial full KB data
    await loadKBData();
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

  // Bind KB Admin events
  initTabs();
  initKBEvents();
}

/* Tab Switching and Initialization */
function initTabs() {
  elements.tabChat.addEventListener("click", () => {
    elements.tabChat.classList.add("active");
    elements.tabKB.classList.remove("active");
    elements.chatTabContent.classList.remove("hidden");
    elements.kbTabContent.classList.add("hidden");
  });

  elements.tabKB.addEventListener("click", () => {
    elements.tabKB.classList.add("active");
    elements.tabChat.classList.remove("active");
    elements.kbTabContent.classList.remove("hidden");
    elements.chatTabContent.classList.add("hidden");

    renderRulesTable(elements.ruleSearch.value);
    renderFactsTable(elements.factSearch.value);
  });

  elements.subTabRules.addEventListener("click", () => {
    elements.subTabRules.classList.add("active");
    elements.subTabFacts.classList.remove("active");
    elements.subContentRules.classList.remove("hidden");
    elements.subContentFacts.classList.add("hidden");
  });

  elements.subTabFacts.addEventListener("click", () => {
    elements.subTabFacts.classList.add("active");
    elements.subTabRules.classList.remove("active");
    elements.subContentFacts.classList.remove("hidden");
    elements.subContentRules.classList.add("hidden");
  });
}

/* Bind KB Modals and Search */
function initKBEvents() {
  elements.addRuleBtn.addEventListener("click", () => openRuleModal());
  elements.addFactBtn.addEventListener("click", () => openFactModal());
  elements.cancelRuleBtn.addEventListener("click", () => elements.ruleModal.classList.add("hidden"));
  elements.cancelFactBtn.addEventListener("click", () => elements.factModal.classList.add("hidden"));

  elements.ruleForm.addEventListener("submit", handleRuleFormSubmit);
  elements.factForm.addEventListener("submit", handleFactFormSubmit);

  elements.ruleSearch.addEventListener("input", (e) => renderRulesTable(e.target.value));
  elements.factSearch.addEventListener("input", (e) => renderFactsTable(e.target.value));

  elements.factCategorySelect.addEventListener("change", (e) => {
    if (e.target.value === "diagnosis") {
      elements.diagnosisFields.classList.remove("hidden");
    } else {
      elements.diagnosisFields.classList.add("hidden");
    }
    toggleQuickFactCheckboxVisibility(e.target.value);
  });
}

async function loadKBData() {
  try {
    const kb = await fetchJson("/api/kb");
    kbData = {
      facts: kb.facts || {},
      rules: kb.rules || [],
      diagnosisMetadata: kb.diagnosisMetadata || {},
      quickFacts: kb.quickFacts || []
    };
    FACTS = kbData.facts;
    QUICK_FACT_KEYS = kbData.quickFacts;
    renderQuickFacts();
    syncQuickFactState();
  } catch (error) {
    console.error("Failed to load full KB data:", error);
  }
}

/* Render Rules in Table */
function renderRulesTable(filterText = "") {
  elements.rulesTableBody.innerHTML = "";
  const query = filterText.toLowerCase().trim();

  const filteredRules = kbData.rules.filter(r => {
    const consequentLabel = FACTS[r.consequent]?.label || r.consequent;
    return r.id.toLowerCase().includes(query) || consequentLabel.toLowerCase().includes(query);
  });

  if (filteredRules.length === 0) {
    elements.rulesTableBody.innerHTML = `<tr><td colspan="6" class="empty-state" style="text-align: center; padding: 24px;">Không tìm thấy luật nào.</td></tr>`;
    return;
  }

  filteredRules.forEach(rule => {
    const tr = document.createElement("tr");
    const antecedentsLabels = rule.antecedents
      .map(ant => `<span class="fact-label">${FACTS[ant]?.label || ant}</span>`)
      .join('<span class="operator"> ∧ </span>');

    const consequentLabel = `<span class="fact-label derived">${FACTS[rule.consequent]?.label || rule.consequent}</span>`;

    tr.innerHTML = `
      <td style="font-family: monospace; font-weight: 700; color: var(--accent);">${rule.id}</td>
      <td><div class="trace-antecedents">${antecedentsLabels}</div></td>
      <td>${consequentLabel}</td>
      <td style="font-weight: 700; color: var(--accent-dark);">${rule.confidence}%</td>
      <td style="font-size: 0.9rem; color: var(--muted);">${rule.explanation}</td>
      <td>
        <div class="action-buttons">
          <button type="button" class="edit-btn">Sửa</button>
          <button type="button" class="delete-btn">Xóa</button>
        </div>
      </td>
    `;

    tr.querySelector(".edit-btn").addEventListener("click", () => openRuleModal(rule));
    tr.querySelector(".delete-btn").addEventListener("click", () => deleteRule(rule.id));

    elements.rulesTableBody.appendChild(tr);
  });
}

/* Render Facts in Table */
function renderFactsTable(filterText = "") {
  elements.factsTableBody.innerHTML = "";
  const query = filterText.toLowerCase().trim();

  const filteredFacts = Object.entries(kbData.facts).filter(([key, value]) => {
    return key.toLowerCase().includes(query) || value.label.toLowerCase().includes(query);
  });

  if (filteredFacts.length === 0) {
    elements.factsTableBody.innerHTML = `<tr><td colspan="5" class="empty-state" style="text-align: center; padding: 24px;">Không tìm thấy sự kiện nào.</td></tr>`;
    return;
  }

  filteredFacts.forEach(([key, fact]) => {
    const tr = document.createElement("tr");
    const synonymsList = (fact.synonyms || [])
      .map(s => `<span class="pill" style="font-size: 0.8rem; padding: 2px 8px; margin: 2px;">${s}</span>`)
      .join(" ");

    tr.innerHTML = `
      <td style="font-family: monospace; font-weight: 600;">${key}</td>
      <td style="font-weight: 600;">${fact.label}</td>
      <td><span class="table-badge ${fact.category}">${fact.category}</span></td>
      <td><div style="display: flex; flex-wrap: wrap; gap: 4px;">${synonymsList || '<span style="color: var(--muted); font-style: italic;">Không có</span>'}</div></td>
      <td>
        <div class="action-buttons">
          <button type="button" class="edit-btn">Sửa</button>
          <button type="button" class="delete-btn">Xóa</button>
        </div>
      </td>
    `;

    tr.querySelector(".edit-btn").addEventListener("click", () => openFactModal(key, fact));
    tr.querySelector(".delete-btn").addEventListener("click", () => deleteFact(key));

    elements.factsTableBody.appendChild(tr);
  });
}

/* Open Rule Modal */
function openRuleModal(rule = null) {
  elements.antecedentsSelectGrid.innerHTML = "";
  elements.consequentSelect.innerHTML = '<option value="" disabled selected>Chọn kết luận...</option>';

  // Antecedents select checkboxes (symptoms or derived facts only)
  Object.entries(kbData.facts)
    .filter(([_, value]) => value.category !== "diagnosis")
    .sort((a, b) => a[1].label.localeCompare(b[1].label, "vi"))
    .forEach(([key, value]) => {
      const div = document.createElement("div");
      div.className = "fact-checkbox-item";
      const isChecked = rule ? rule.antecedents.includes(key) : false;
      div.innerHTML = `
        <input type="checkbox" id="check_ant_${key}" value="${key}" ${isChecked ? 'checked' : ''}>
        <label for="check_ant_${key}">${value.label}</label>
      `;
      elements.antecedentsSelectGrid.appendChild(div);
    });

  // Consequent select options (derived or diagnosis only)
  Object.entries(kbData.facts)
    .filter(([_, value]) => value.category !== "symptom")
    .sort((a, b) => a[1].label.localeCompare(b[1].label, "vi"))
    .forEach(([key, value]) => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = `${value.label} (${value.category === "derived" ? "dẫn xuất" : "bệnh lý"})`;
      if (rule && rule.consequent === key) {
        option.selected = true;
      }
      elements.consequentSelect.appendChild(option);
    });

  if (rule) {
    editingRuleId = rule.id;
    elements.ruleModalTitle.textContent = `Sửa luật: ${rule.id}`;
    elements.ruleIdInput.value = rule.id;
    elements.ruleIdInput.disabled = true;
    elements.confidenceInput.value = rule.confidence;
    elements.ruleExplanationInput.value = rule.explanation;
  } else {
    editingRuleId = null;
    elements.ruleModalTitle.textContent = "Thêm luật mới";
    elements.ruleIdInput.value = "";
    elements.ruleIdInput.disabled = false;
    elements.confidenceInput.value = 80;
    elements.ruleExplanationInput.value = "";
  }

  elements.ruleModal.classList.remove("hidden");
}

/* Open Fact Modal */
function openFactModal(key = null, fact = null) {
  if (fact) {
    editingFactKey = key;
    elements.factModalTitle.textContent = `Sửa sự kiện: ${key}`;
    elements.factKeyInput.value = key;
    elements.factKeyInput.disabled = true;
    elements.factLabelInput.value = fact.label;
    elements.factCategorySelect.value = fact.category;
    elements.factSynonymsInput.value = (fact.synonyms || []).join(", ");
    elements.factQuickFactCheckbox.checked = kbData.quickFacts.includes(key);

    if (fact.category === "diagnosis") {
      elements.diagnosisFields.classList.remove("hidden");
      const diagMeta = kbData.diagnosisMetadata[key] || {};
      elements.diagPrioritySelect.value = diagMeta.priority || "low";
      elements.diagAdviceInput.value = diagMeta.advice || "";
    } else {
      elements.diagnosisFields.classList.add("hidden");
      elements.diagPrioritySelect.value = "low";
      elements.diagAdviceInput.value = "";
    }
    toggleQuickFactCheckboxVisibility(fact.category);
  } else {
    editingFactKey = null;
    elements.factModalTitle.textContent = "Thêm sự kiện mới";
    elements.factKeyInput.value = "";
    elements.factKeyInput.disabled = false;
    elements.factLabelInput.value = "";
    elements.factCategorySelect.value = "symptom";
    elements.factSynonymsInput.value = "";
    elements.factQuickFactCheckbox.checked = false;

    elements.diagnosisFields.classList.add("hidden");
    elements.diagPrioritySelect.value = "low";
    elements.diagAdviceInput.value = "";
    toggleQuickFactCheckboxVisibility("symptom");
  }

  elements.factModal.classList.remove("hidden");
}

function toggleQuickFactCheckboxVisibility(category) {
  if (category === "symptom") {
    elements.quickFactGroup.classList.remove("hidden");
  } else {
    elements.quickFactGroup.classList.add("hidden");
  }
}

/* Submit Handlers */
async function handleRuleFormSubmit(e) {
  e.preventDefault();

  const id = elements.ruleIdInput.value.trim();
  const confidence = parseInt(elements.confidenceInput.value, 10);
  const explanation = elements.ruleExplanationInput.value.trim();
  const consequent = elements.consequentSelect.value;

  const checkedBoxes = elements.antecedentsSelectGrid.querySelectorAll("input[type='checkbox']:checked");
  const antecedents = Array.from(checkedBoxes).map(cb => cb.value);

  if (antecedents.length === 0) {
    alert("⚠️ Vui lòng chọn ít nhất một điều kiện vế trái (Antecedents).");
    return;
  }
  if (!consequent) {
    alert("⚠️ Vui lòng chọn một kết luận vế phải (Consequent).");
    return;
  }

  const ruleData = { id, antecedents, consequent, confidence, explanation };

  if (editingRuleId) {
    const idx = kbData.rules.findIndex(r => r.id === editingRuleId);
    if (idx !== -1) {
      kbData.rules[idx] = ruleData;
    }
  } else {
    if (kbData.rules.some(r => r.id === id)) {
      alert(`❌ Mã luật "${id}" đã tồn tại. Vui lòng chọn mã khác.`);
      return;
    }
    kbData.rules.push(ruleData);
  }

  const success = await saveKBOnServer();
  if (success) {
    elements.ruleModal.classList.add("hidden");
  }
}

async function handleFactFormSubmit(e) {
  e.preventDefault();

  const key = elements.factKeyInput.value.trim().toLowerCase();
  const label = elements.factLabelInput.value.trim();
  const category = elements.factCategorySelect.value;
  const synonyms = elements.factSynonymsInput.value
    .split(",")
    .map(s => s.trim())
    .filter(s => s.length > 0);

  if (!key.match(/^[a-z0-9_]+$/)) {
    alert("❌ Mã sự kiện chỉ được chứa chữ thường không dấu, số và dấu gạch dưới.");
    return;
  }

  const factData = { label, category, synonyms };

  if (editingFactKey) {
    kbData.facts[editingFactKey] = factData;
  } else {
    if (kbData.facts[key]) {
      alert(`❌ Mã sự kiện "${key}" đã tồn tại. Vui lòng chọn mã khác.`);
      return;
    }
    kbData.facts[key] = factData;
  }

  if (category === "symptom" && elements.factQuickFactCheckbox.checked) {
    if (!kbData.quickFacts.includes(key)) {
      kbData.quickFacts.push(key);
    }
  } else {
    kbData.quickFacts = kbData.quickFacts.filter(qf => qf !== key);
  }

  if (category === "diagnosis") {
    kbData.diagnosisMetadata[key] = {
      priority: elements.diagPrioritySelect.value,
      advice: elements.diagAdviceInput.value.trim()
    };
  } else {
    delete kbData.diagnosisMetadata[key];
  }

  const success = await saveKBOnServer();
  if (success) {
    elements.factModal.classList.add("hidden");
  }
}

async function saveKBOnServer() {
  try {
    const res = await fetchJson("/api/kb/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(kbData),
    });

    if (res.status === "success") {
      await loadKBData();
      renderRulesTable(elements.ruleSearch.value);
      renderFactsTable(elements.factSearch.value);
      return true;
    }
  } catch (error) {
    alert("❌ Lỗi lưu dữ liệu: " + error.message);
  }
  return false;
}

function deleteRule(ruleId) {
  if (!confirm(`Bạn có chắc chắn muốn xóa luật ${ruleId}?`)) {
    return;
  }

  kbData.rules = kbData.rules.filter(r => r.id !== ruleId);
  void saveKBOnServer();
}

function deleteFact(key) {
  const usingRules = kbData.rules.filter(r => r.antecedents.includes(key) || r.consequent === key);
  if (usingRules.length > 0) {
    const ids = usingRules.map(r => r.id).join(", ");
    alert(`❌ Không thể xóa sự kiện này vì đang được sử dụng trong các luật: ${ids}. Hãy sửa hoặc xóa luật trước.`);
    return;
  }

  if (!confirm(`Bạn có chắc chắn muốn xóa sự kiện "${kbData.facts[key].label}" (${key})?`)) {
    return;
  }

  delete kbData.facts[key];
  kbData.quickFacts = kbData.quickFacts.filter(qf => qf !== key);
  delete kbData.diagnosisMetadata[key];

  void saveKBOnServer();
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

  const traceContainer = document.createElement("div");
  traceContainer.className = "trace-flow";

  trace.forEach((step, index) => {
    const item = document.createElement("div");
    item.className = "trace-step";

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
    high: "🔴 Ưu tiên cao",
    medium: "🟡 Theo dõi sát",
    low: "🟢 Ưu tiên thấp",
  }[priority] || "⚪ Chưa phân loại";
}

function resetSession() {
  state.userFacts.clear();
  elements.chatMessages.innerHTML = "";
  appendBotMessage([
    "🔄 Phiên tư vấn đã được làm mới.",
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
