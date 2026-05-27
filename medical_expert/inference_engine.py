

#from __future__ import annotaations

from medical_expert.knowledge_base import DIAGNOSIS_METADATA, FACTS


class ForwardChainingEngine:
    def __init__(self, rules: list[dict]) -> None:
        self.rules = rules

    def infer(self, initial_facts: list[str]) -> dict:
        working_memory = set(initial_facts)
        trace = []
        fired_rules = set()
        changed = True

        while changed:
            changed = False
            for rule in self.rules:
                if rule["id"] in fired_rules:
                    continue

                antecedents = rule["antecedents"]
                if not all(fact in working_memory for fact in antecedents):
                    continue

                consequent = rule["consequent"]
                if consequent in working_memory:
                    continue

                working_memory.add(consequent)
                fired_rules.add(rule["id"])
                trace.append(
                    {
                        "ruleId": rule["id"],
                        "antecedents": antecedents.copy(),
                        "consequent": consequent,
                        "explanation": rule["explanation"],
                    }
                )
                changed = True

        diagnoses = []
        for fact in working_memory:
            if FACTS.get(fact, {}).get("category") != "diagnosis":
                continue

            metadata = DIAGNOSIS_METADATA.get(fact, {})
            diagnoses.append(
                {
                    "key": fact,
                    "label": FACTS[fact]["label"],
                    "priority": metadata.get("priority", "low"),
                    "advice": metadata.get("advice", ""),
                }
            )

        diagnoses.sort(key=lambda item: self.priority_weight(item["priority"]), reverse=True)
        return {
            "workingMemory": sorted(working_memory),
            "trace": trace,
            "diagnoses": diagnoses,
        }

    def suggest_next_facts(self, current_facts: list[str]) -> list[str]:
        current = set(current_facts)
        ranked: dict[str, float] = {}

        for rule in self.rules:
            antecedents = rule["antecedents"]
            known_count = sum(1 for fact in antecedents if fact in current)
            missing_facts = [fact for fact in antecedents if fact not in current]

            if known_count == 0 or not missing_facts:
                continue

            for fact in missing_facts:
                if FACTS.get(fact, {}).get("category") != "symptom":
                    continue

                score = known_count / len(antecedents)
                ranked[fact] = max(ranked.get(fact, 0), score)

        return [fact for fact, _ in sorted(ranked.items(), key=lambda item: item[1], reverse=True)[:3]]

    @staticmethod
    def priority_weight(priority: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 0)
