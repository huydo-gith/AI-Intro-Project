FACTS = {
    "fever": {
        "label": "Sốt",
        "category": "symptom",
        "synonyms": ["sot", "sốt", "fever", "nong", "nóng", "nóng sốt"],
    },
    "cough": {
        "label": "Ho",
        "category": "symptom",
        "synonyms": ["ho", "cough"],
    },
    "sore_throat": {
        "label": "Đau họng",
        "category": "symptom",
        "synonyms": ["dau hong", "đau họng", "rat hong", "rát họng", "sore throat"],
    },
    "runny_nose": {
        "label": "Sổ mũi",
        "category": "symptom",
        "synonyms": ["so mui", "sổ mũi", "chay mui", "chảy mũi", "runny nose"],
    },
    "sneezing": {
        "label": "Hắt hơi",
        "category": "symptom",
        "synonyms": ["hat hoi", "hắt hơi", "sneezing"],
    },
    "body_ache": {
        "label": "Đau mỏi người",
        "category": "symptom",
        "synonyms": ["dau moi", "đau mỏi", "body ache", "nhuc moi", "nhức mỏi"],
    },
    "headache": {
        "label": "Đau đầu",
        "category": "symptom",
        "synonyms": ["dau dau", "đau đầu", "headache"],
    },
    "fatigue": {
        "label": "Mệt mỏi",
        "category": "symptom",
        "synonyms": ["met moi", "mệt mỏi", "fatigue", "u oai", "uể oải", "mệt", "hơi mệt"],
    },
    "loss_of_taste": {
        "label": "Mất vị giác/khứu giác",
        "category": "symptom",
        "synonyms": [
            "mat vi giac",
            "mất vị giác",
            "mat khu giac",
            "mất khứu giác",
            "loss of taste",
            "loss of smell",
        ],
    },
    "shortness_of_breath": {
        "label": "Khó thở",
        "category": "symptom",
        "synonyms": ["kho tho", "khó thở", "shortness of breath", "breathless"],
    },
    "chest_pain": {
        "label": "Đau tức ngực",
        "category": "symptom",
        "synonyms": ["dau nguc", "đau ngực", "tuc nguc", "tức ngực", "chest pain"],
    },
    "nausea": {
        "label": "Buồn nôn",
        "category": "symptom",
        "synonyms": ["buon non", "buồn nôn", "nausea"],
    },
    "vomiting": {
        "label": "Nôn",
        "category": "symptom",
        "synonyms": ["non", "nôn", "vomit", "vomiting"],
    },
    "diarrhea": {
        "label": "Tiêu chảy",
        "category": "symptom",
        "synonyms": ["tieu chay", "tiêu chảy", "diarrhea"],
    },
    "abdominal_pain": {
        "label": "Đau bụng",
        "category": "symptom",
        "synonyms": ["dau bung", "đau bụng", "abdominal pain", "stomachache"],
    },
    "itchy_eyes": {
        "label": "Ngứa mắt",
        "category": "symptom",
        "synonyms": ["ngua mat", "ngứa mắt", "itchy eyes"],
    },
    "rash": {
        "label": "Phát ban",
        "category": "symptom",
        "synonyms": ["phat ban", "phát ban", "rash"],
    },
    "high_fever": {"label": "Sốt cao", "category": "derived", "synonyms": []},
    "respiratory_syndrome": {"label": "Hội chứng hô hấp", "category": "derived", "synonyms": []},
    "upper_respiratory_pattern": {"label": "Mẫu viêm đường hô hấp trên", "category": "derived", "synonyms": []},
    "viral_pattern": {"label": "Mẫu nhiễm virus", "category": "derived", "synonyms": []},
    "digestive_syndrome": {"label": "Hội chứng tiêu hóa", "category": "derived", "synonyms": []},
    "allergy_pattern": {"label": "Mẫu dị ứng", "category": "derived", "synonyms": []},
    "respiratory_alert": {"label": "Cảnh báo hô hấp", "category": "derived", "synonyms": []},
    "influenza": {"label": "Nghi cúm", "category": "diagnosis", "synonyms": []},
    "common_cold": {"label": "Nghi cảm lạnh", "category": "diagnosis", "synonyms": []},
    "covid19_suspected": {"label": "Nghi COVID-19", "category": "diagnosis", "synonyms": []},
    "allergic_rhinitis": {"label": "Nghi viêm mũi dị ứng", "category": "diagnosis", "synonyms": []},
    "food_poisoning": {"label": "Nghi rối loạn tiêu hóa / ngộ độc thực phẩm", "category": "diagnosis", "synonyms": []},
    "measles_suspected": {"label": "Nghi sởi hoặc bệnh phát ban do virus", "category": "diagnosis", "synonyms": []},
    "urgent_medical_attention": {"label": "Cần đi khám khẩn cấp", "category": "diagnosis", "synonyms": []},
}

QUICK_FACT_KEYS = [
    "fever",
    "cough",
    "sore_throat",
    "runny_nose",
    "body_ache",
    "fatigue",
    "loss_of_taste",
    "shortness_of_breath",
    "diarrhea",
    "abdominal_pain",
    "itchy_eyes",
    "rash",
]

RULES = [
    {
        "id": "R1",
        "antecedents": ["fever"],
        "consequent": "high_fever",
        "explanation": "Có sốt, hệ thống kích hoạt trạng thái sốt để hỗ trợ các luật bệnh virus.",
    },
    {
        "id": "R2",
        "antecedents": ["cough", "sore_throat"],
        "consequent": "respiratory_syndrome",
        "explanation": "Ho và đau họng tạo thành mẫu triệu chứng hô hấp ban đầu.",
    },
    {
        "id": "R3",
        "antecedents": ["runny_nose", "sneezing"],
        "consequent": "upper_respiratory_pattern",
        "explanation": "Sổ mũi và hắt hơi tạo thành mẫu đường hô hấp trên.",
    },
    {
        "id": "R4",
        "antecedents": ["fever", "body_ache", "fatigue"],
        "consequent": "viral_pattern",
        "explanation": "Sốt, đau mỏi người và mệt mỏi là một cụm dấu hiệu nhiễm virus.",
    },
    {
        "id": "R5",
        "antecedents": ["nausea", "vomiting"],
        "consequent": "digestive_syndrome",
        "explanation": "Buồn nôn và nôn gợi ý hội chứng tiêu hóa.",
    },
    {
        "id": "R6",
        "antecedents": ["diarrhea", "abdominal_pain"],
        "consequent": "digestive_syndrome",
        "explanation": "Tiêu chảy kèm đau bụng củng cố mẫu rối loạn tiêu hóa.",
    },
    {
        "id": "R7",
        "antecedents": ["runny_nose", "itchy_eyes", "sneezing"],
        "consequent": "allergy_pattern",
        "explanation": "Sổ mũi, ngứa mắt và hắt hơi phù hợp với mẫu dị ứng.",
    },
    {
        "id": "R8",
        "antecedents": ["shortness_of_breath", "chest_pain"],
        "consequent": "respiratory_alert",
        "explanation": "Khó thở kèm đau tức ngực là dấu hiệu cảnh báo cần ưu tiên xử trí.",
    },
    {
        "id": "R9",
        "antecedents": ["viral_pattern", "respiratory_syndrome"],
        "consequent": "influenza",
        "explanation": "Mẫu virus kết hợp hội chứng hô hấp hướng tới cúm.",
    },
    {
        "id": "R10",
        "antecedents": ["upper_respiratory_pattern", "sore_throat"],
        "consequent": "common_cold",
        "explanation": "Đường hô hấp trên kèm đau họng phù hợp với cảm lạnh.",
    },
    {
        "id": "R11",
        "antecedents": ["respiratory_syndrome", "loss_of_taste"],
        "consequent": "covid19_suspected",
        "explanation": "Triệu chứng hô hấp cùng mất vị giác hoặc khứu giác gợi ý COVID-19.",
    },
    {
        "id": "R12",
        "antecedents": ["allergy_pattern"],
        "consequent": "allergic_rhinitis",
        "explanation": "Mẫu dị ứng dẫn tới nghi ngờ viêm mũi dị ứng.",
    },
    {
        "id": "R13",
        "antecedents": ["digestive_syndrome", "fever"],
        "consequent": "food_poisoning",
        "explanation": "Hội chứng tiêu hóa có sốt gợi ý nhiễm khuẩn hoặc ngộ độc thực phẩm.",
    },
    {
        "id": "R14",
        "antecedents": ["fever", "rash"],
        "consequent": "measles_suspected",
        "explanation": "Sốt đi cùng phát ban gợi ý bệnh phát ban do virus như sởi.",
    },
    {
        "id": "R15",
        "antecedents": ["respiratory_alert"],
        "consequent": "urgent_medical_attention",
        "explanation": "Khi có cảnh báo hô hấp, hệ thống kết luận cần khám khẩn cấp.",
    },
    {
        "id": "R16",
        "antecedents": ["covid19_suspected", "shortness_of_breath"],
        "consequent": "urgent_medical_attention",
        "explanation": "Nghi COVID-19 kèm khó thở làm tăng mức độ nguy cơ.",
    },
]

DIAGNOSIS_METADATA = {
    "influenza": {
        "priority": "medium",
        "advice": "Nghỉ ngơi, uống đủ nước, theo dõi sốt và đi khám nếu triệu chứng nặng thêm.",
    },
    "common_cold": {
        "priority": "low",
        "advice": "Theo dõi triệu chứng, nghỉ ngơi, giữ ấm và bổ sung nước.",
    },
    "covid19_suspected": {
        "priority": "high",
        "advice": "Nên test, hạn chế tiếp xúc, theo dõi SpO2 và đi khám nếu khó thở hoặc sốt kéo dài.",
    },
    "allergic_rhinitis": {
        "priority": "low",
        "advice": "Tránh tác nhân dị ứng, theo dõi và cân nhắc khám chuyên khoa nếu tái phát nhiều.",
    },
    "food_poisoning": {
        "priority": "medium",
        "advice": "Bù nước, theo dõi mất nước và đi khám nếu nôn nhiều, sốt cao hoặc tiêu chảy kéo dài.",
    },
    "measles_suspected": {
        "priority": "high",
        "advice": "Cần khám để đánh giá nguyên nhân phát ban, đặc biệt khi sốt cao hoặc mệt nhiều.",
    },
    "urgent_medical_attention": {
        "priority": "high",
        "advice": "Có dấu hiệu cảnh báo. Nên đến cơ sở y tế hoặc gọi hỗ trợ y tế ngay.",
    },
}
