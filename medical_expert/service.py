from __future__ import annotations

import re
import unicodedata

from medical_expert.inference_engine import ForwardChainingEngine
from medical_expert.knowledge_base import FACTS, QUICK_FACT_KEYS, RULES


engine = ForwardChainingEngine(RULES)


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
            "Bạn có thể nhập theo mẫu như: 'sốt, ho, đau họng'."
        )

    if result["diagnoses"]:
        diagnosis_lines = [
            f'{diagnosis["label"]}: {diagnosis["advice"]}'
            for diagnosis in result["diagnoses"][:3]
        ]
        bot_messages.append("Kết luận tạm thời:\n" + "\n".join(diagnosis_lines))
    else:
        bot_messages.append("Hiện chưa đủ dữ kiện để kết luận. Tôi sẽ hỏi thêm để hoàn thiện bộ nhớ làm việc.")

    if next_facts:
        question = ", ".join(FACTS[fact]["label"].lower() for fact in next_facts)
        bot_messages.append(f"Bạn có thêm các dấu hiệu sau không: {question}?")

    if any(item["key"] == "urgent_medical_attention" for item in result["diagnoses"]):
        bot_messages.append("Hệ thống phát hiện dấu hiệu cảnh báo. Bạn nên liên hệ cơ sở y tế sớm.")

    return {
        "recognizedFacts": extracted_facts,
        "userFacts": merged_facts,
        "workingMemory": result["workingMemory"],
        "trace": result["trace"],
        "diagnoses": result["diagnoses"],
        "botMessages": bot_messages,
        "quickFacts": QUICK_FACT_KEYS,
    }
