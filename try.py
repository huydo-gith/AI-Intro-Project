
from medical_expert.knowledge_base import DIAGNOSIS_METADATA, FACTS, RULES

class ForwardChainingEngine:
    @staticmethod
    def priority_weight(priority: str) -> int:
        return {'high': 3, 'medium': 2, 'low': 1}.get(priority, 0)

    def __init__(self, rules: list[dict]):
        self.rules = rules

    def infer(self, initial_facts: list[str]) -> dict:
        working_memory = set(initial_facts) # tập chứa các sự kiện ban đầu (triệu chứng của bệnh nhân)
        fired_rules = set()
        inferred = True # Biến boolean biểu diễn trạng thái quá trình suy diễn

        # Cơ chế suy diễn
        # Tìm ra luật hợp lý, thêm các sự kiện mới vào working memory

        while inferred:
            inferred = False
            for rule in self.rules:
                # nếu luật đã được kích hoạt thì bỏ qua xét luật mới tránh việc xét luật lặp vô tận
                if rule['id'] in fired_rules:
                    continue

                antecedents = rule['antecedents']

                #nếu các sự kiện trong tiền đề (antecedents) đều nằm trong working memory thì tiếp tục luật
                if not all(fact in working_memory for fact in antecedents):
                    continue
                
                consequent = rule['consequent']
                if consequent in working_memory:
                    continue

                working_memory.add(consequent)
                fired_rules.add(rule['id'])
                inferred = True

        #sau khi xong hàm infer ta có một set working_memory được cập nhật các sự kiện mới

        diagnoses = [] 
        for fact in working_memory:
            if FACTS.get(fact, {}).get('category') != 'diagnosis':
                continue

            metadata = DIAGNOSIS_METADATA.get(fact, {})
            diagnoses.append(
                {
                    'key': fact,
                    'label': FACTS[fact]['label'],
                    'priority': metadata.get('priority', 'low'),
                    'advice': metadata.get('advice', "")
                }
            )

            diagnoses.sort(key=lambda item: self.priority_weight(item['priority']), reverse=True)


