from __future__ import annotations

import re
import unicodedata

from medical_expert.inference_engine import ForwardChainingEngine
from medical_expert.knowledge_base import FACTS, QUICK_FACT_KEYS, RULES



# Initialize engine with conflict resolution
engine = ForwardChainingEngine(RULES, conflict_strategy="highest_confidence")


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


def analyze_symptoms(user_facts: list[str], message: str = "") -> dict:
    extracted_facts = extract_facts_from_text(message) if message else []
    merged_facts = list(dict.fromkeys([*user_facts, *extracted_facts]))
    result = engine.infer(merged_facts)
    next_facts = engine.suggest_next_facts(merged_facts)

    bot_messages = []
    if extracted_facts:
        labels = ", ".join(FACTS[fact]["label"] for fact in extracted_facts)
        bot_messages.append(f"Tôi đã ghi nhận các triệu chứng: {labels}.")
    elif message:
        bot_messages.append(
            "Tôi chưa nhận diện được triệu chứng rõ ràng từ câu vừa rồi. "
            "Bạn có thể nhập theo mẫu như: 'Tôi bị sốt, ho, đau họng'."
        )

    if result["diagnoses"]:
        diagnosis_lines = []
        for diagnosis in result["diagnoses"][:3]:
            confidence_pct = diagnosis.get("confidence", 0)
            confidence_bar = _confidence_bar(confidence_pct)
            diagnosis_lines.append(
                f'{diagnosis["label"]} ({confidence_pct:.0f}%) {confidence_bar}: {diagnosis["advice"]}'
            )
        bot_messages.append("Kết luận tạm thời:\n" + "\n".join(diagnosis_lines))
    else:
        bot_messages.append("Hiện tại chưa đủ dữ kiện để kết luận.")

    if next_facts:
        question = ", ".join(FACTS[fact]["label"].lower() for fact in next_facts)
        bot_messages.append(f"Để chẩn đoán chính xác hơn, bạn có thêm các dấu hiệu sau không: {question}?")

    if any(item["key"] == "urgent_medical_attention" for item in result["diagnoses"]):
        bot_messages.append("HỆ THỐNG PHÁT HIỆN DẤU HIỆU CẢnh báo. BẠN NÊN LIÊN HỆ CƠ SỞ Y TẾ SỚM.")

    return {
        "recognizedFacts": extracted_facts,
        "userFacts": merged_facts,
        "workingMemory": result["workingMemory"],
        "trace": result["trace"],
        "diagnoses": result["diagnoses"],
        "botMessages": bot_messages,
        "quickFacts": QUICK_FACT_KEYS,
    }


def _confidence_bar(confidence: float) -> str:
    """Create a visual confidence bar."""
    filled = int(confidence / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty


def explain_diagnosis_detail(diagnosis_key: str, trace: list[dict]) -> dict:
    """Get detailed explanation for a specific diagnosis."""
    return engine.explain_diagnosis(diagnosis_key, trace)


def get_rule_explanation(rule_id: str, trace: list[dict], diagnoses: list[dict]) -> dict:
    """Get detailed explanation for a specific rule."""
    return engine.enhance_explanation(rule_id, trace, diagnoses)
