from __future__ import annotations

import re
import unicodedata

from medical_expert.inference_engine import ForwardChainingEngine
from medical_expert.knowledge_base import FACTS, QUICK_FACT_KEYS, RULES



# Initialize engine with conflict resolution
engine = ForwardChainingEngine(RULES, conflict_strategy="all_rules")


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def extract_facts_from_text(input_text: str) -> list[str]:
    normalized_input = normalize_text(input_text)
    detected: list[str] = []

    for key, fact in FACTS.items():
        if fact["category"] != "symptom":
            continue

        if any(matches_keyword(normalized_input, keyword) for keyword in fact["synonyms"]):
            detected.append(key)

    return list(dict.fromkeys(detected))


def matches_keyword(normalized_input: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword).strip()
    if not normalized_keyword:
        return False

    pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"
    return re.search(pattern, normalized_input) is not None

def _diagnosis_intro(top: dict) -> str:
    """Intro tự nhiên theo phong cách bác sĩ tư vấn, tuỳ mức độ."""
    confidence = top.get("confidence", 0)
    priority = top.get("priority", "low")

    if priority == "high":
        return (
            "Nhìn vào tổng thể các triệu chứng, tôi thấy có một số điểm cần chú ý. "
            "Dưới đây là những khả năng tôi đang nghĩ đến:"
        )
    elif confidence >= 75:
        return (
            "Dựa trên những gì bạn chia sẻ, tôi có thể đưa ra nhận định khá rõ. "
            "Đây là những khả năng phù hợp nhất với tình trạng của bạn:"
        )
    elif confidence >= 50:
        return (
            "Với các triệu chứng hiện tại, tôi có một vài hướng đang cân nhắc. "
            "Chưa thể khẳng định chắc chắn, nhưng đây là những khả năng đáng lưu ý:"
        )
    else:
        return (
            "Thông tin hiện tại còn khá ít, nên tôi chỉ có thể đưa ra gợi ý ban đầu. "
            "Bạn càng mô tả thêm, tôi càng có thể đánh giá chính xác hơn:"
        )


def analyze_symptoms(user_facts: list[str], message: str = "", conflict_strategy: str = "all_rules") -> dict:
    extracted_facts = extract_facts_from_text(message) if message else []
    merged_facts = list(dict.fromkeys([*user_facts, *extracted_facts]))
    result = engine.infer(merged_facts, conflict_strategy=conflict_strategy)
    next_facts = engine.suggest_next_facts(merged_facts)

    bot_messages = []

    # --- Nhận diện triệu chứng ---
    if extracted_facts:
        labels = [FACTS[f]["label"] for f in extracted_facts]
        if len(labels) == 1:
            symptom_text = f"<b>{labels[0].lower()}</b>"
            ack = f"Được rồi, bạn đang bị {symptom_text}. Để tôi xem thêm nhé."
        elif len(labels) == 2:
            symptom_text = f"<b>{labels[0].lower()}</b> và <b>{labels[1].lower()}</b>"
            ack = f"Tôi hiểu rồi — bạn đang có {symptom_text}. Tôi sẽ phân tích ngay."
        else:
            parts = ", ".join(f"<b>{l.lower()}</b>" for l in labels[:-1])
            symptom_text = parts + f" và <b>{labels[-1].lower()}</b>"
            ack = f"Bạn đang có khá nhiều triệu chứng cùng lúc: {symptom_text}. Tôi sẽ xem xét kỹ hơn."

        bot_messages.append(
            f'<div class="bot-msg-inner"><span class="msg-icon">📋</span><span>{ack}</span></div>'
        )
    elif message:
        bot_messages.append(
            '<div class="bot-msg-inner"><span class="msg-icon">🤔</span>'
            '<span>Xin lỗi, tôi chưa nắm rõ được triệu chứng bạn mô tả. '
            'Bạn thử nói cụ thể hơn nhé, ví dụ: <em>"sốt cao, ho nhiều, đau họng"</em>. '
            'Hoặc bấm thẳng vào các triệu chứng gợi ý phía trên cho nhanh.</span></div>'
        )

    # --- Kết luận chẩn đoán ---
    if result["diagnoses"]:
        top_diagnoses = result["diagnoses"][:3]
        items_html = ""
        for i, d in enumerate(top_diagnoses):
            pct = d.get("confidence", 0)
            priority = d.get("priority", "low")
            priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            icon = priority_icons.get(priority, "⚪")
            # Nhãn thứ tự tự nhiên
            order_label = ["Khả năng cao nhất", "Khả năng thứ hai", "Cũng cần lưu ý"][i] if i < 3 else ""
            items_html += (
                f'<li class="diag-item diag-{priority}">'
                f'  <span class="diag-order">{order_label}</span>'
                f'  <span class="diag-name">{icon} {d["label"]}</span>'
                f'  <span class="diag-confidence-text">Độ phù hợp: {pct:.0f}%</span>'
                f'  <span class="diag-advice">{d["advice"]}</span>'
                f'</li>'
            )

        intro = _diagnosis_intro(top_diagnoses[0])
        bot_messages.append(
            f'<div class="bot-msg-inner"><span class="msg-icon">🩺</span>'
            f'<div class="diag-block">'
            f'  <p class="diag-intro">{intro}</p>'
            f'  <ul class="diag-list">{items_html}</ul>'
            f'</div></div>'
        )
    elif merged_facts:
        bot_messages.append(
            '<div class="bot-msg-inner"><span class="msg-icon">💭</span>'
            '<span>Với những gì bạn mô tả, tôi chưa thể khoanh vùng được nguyên nhân cụ thể. '
            'Không sao — hãy cho tôi biết thêm bạn còn cảm thấy gì khác không nhé.</span></div>'
        )

    # --- Gợi ý câu hỏi tiếp theo ---
    if next_facts:
        symptom_questions = [FACTS[f]["label"].lower() for f in next_facts[:3]]
        if len(symptom_questions) == 1:
            q_text = f"<b>{symptom_questions[0]}</b>"
            question = f"Ngoài ra, bạn có bị {q_text} không?"
        elif len(symptom_questions) == 2:
            q_text = f"<b>{symptom_questions[0]}</b> hay <b>{symptom_questions[1]}</b>"
            question = f"Tôi muốn hỏi thêm một chút — bạn có bị {q_text} không?"
        else:
            q_parts = ", ".join(f"<b>{s}</b>" for s in symptom_questions[:-1])
            q_text = q_parts + f" hay <b>{symptom_questions[-1]}</b>"
            question = f"Để đánh giá chính xác hơn, bạn có thêm các dấu hiệu như {q_text} không?"

        bot_messages.append(
            f'<div class="bot-msg-inner"><span class="msg-icon">❓</span><span>{question}</span></div>'
        )

    # --- Cảnh báo khẩn cấp ---
    if any(item["key"] == "urgent_medical_attention" for item in result["diagnoses"]):
        bot_messages.append(
            '<div class="bot-msg-inner msg-type-urgent"><span class="msg-icon">🚨</span>'
            '<span><strong>Tôi thấy có một số dấu hiệu không nên chủ quan. '
            'Bạn nên đến gặp bác sĩ hoặc cơ sở y tế gần nhất sớm nhé — '
            'đừng để quá lâu.</strong></span></div>'
        )

    return {
        "recognizedFacts": extracted_facts,
        "userFacts": merged_facts,
        "workingMemory": result["workingMemory"],
        "trace": result["trace"],
        "diagnoses": result["diagnoses"],
        "botMessages": bot_messages,
        "quickFacts": QUICK_FACT_KEYS,
    }

def explain_diagnosis_detail(diagnosis_key: str, trace: list[dict]) -> dict:
    """Get detailed explanation for a specific diagnosis."""
    return engine.explain_diagnosis(diagnosis_key, trace)


def get_rule_explanation(rule_id: str, trace: list[dict], diagnoses: list[dict]) -> dict:
    """Get detailed explanation for a specific rule."""
    return engine.enhance_explanation(rule_id, trace, diagnoses)
