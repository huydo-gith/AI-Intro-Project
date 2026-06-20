

#from __future__ import annotaations

from medical_expert.knowledge_base import DIAGNOSIS_METADATA, FACTS


class ForwardChainingEngine:
    def __init__(self, rules: list[dict], conflict_strategy: str = "all_rules") -> None:
        self.rules = rules
        self.conflict_strategy = conflict_strategy

    def infer(self, initial_facts: list[str], conflict_strategy: str = None) -> dict:
        """Forward chaining with confidence calculation."""
        strategy = conflict_strategy if conflict_strategy is not None else self.conflict_strategy
        working_memory = {} 
        for fact in initial_facts:
            working_memory[fact] = 100  

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

                rule_confidence = rule.get("confidence", 80) / 100
                antecedent_confidences = [working_memory[fact] / 100 for fact in antecedents]
                min_confidence = min(antecedent_confidences) if antecedent_confidences else 1.0
                derived_confidence = min_confidence * rule_confidence * 100

                working_memory[consequent] = derived_confidence
                fired_rules.add(rule["id"])
                trace.append(
                    {
                        "ruleId": rule["id"],
                        "antecedents": antecedents.copy(),
                        "consequent": consequent,
                        "explanation": rule["explanation"],
                        "confidence": rule.get("confidence", 80),
                        "derivedConfidence": round(derived_confidence, 1),
                    }
                )
                changed = True

        diagnoses = []
        for fact, confidence in working_memory.items():
            if FACTS.get(fact, {}).get("category") != "diagnosis":
                continue

            metadata = DIAGNOSIS_METADATA.get(fact, {})
            diagnoses.append(
                {
                    "key": fact,
                    "label": FACTS[fact]["label"],
                    "priority": metadata.get("priority", "low"),
                    "advice": metadata.get("advice", ""),
                    "confidence": round(confidence, 1),
                }
            )

        diagnoses.sort(key=lambda item: (self.priority_weight(item["priority"]), item["confidence"]), reverse=True)
        resolved_diagnoses = self._resolve_conflicts(diagnoses, trace, strategy)
        
        return {
            "workingMemory": sorted([(fact, round(conf, 1)) for fact, conf in working_memory.items()]),
            "trace": trace,
            "diagnoses": resolved_diagnoses,
            "alternativeDiagnoses": self._get_alternative_diagnoses(diagnoses),
        }

    def _resolve_conflicts(self, diagnoses: list[dict], trace: list[dict], strategy: str = None) -> list[dict]:
        """Apply conflict resolution strategy to diagnoses."""
        strategy = strategy if strategy is not None else self.conflict_strategy
        if strategy == "all_rules":
            return diagnoses
        
        # Group diagnoses by priority
        by_priority = {}
        for d in diagnoses:
            priority = d["priority"]
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(d)
        
        resolved = []
        for priority in ["high", "medium", "low"]:
            group = by_priority.get(priority, [])
            
            if strategy == "highest_confidence":
                # Keep only highest confidence in each priority group
                if group:
                    max_conf = max(d["confidence"] for d in group)
                    resolved.extend([d for d in group if d["confidence"] == max_conf])
            
            elif strategy == "specificity":
                # For each diagnosis, find which rule produced it
                # Keep diagnosis from rule with most antecedents (more specific)
                best_by_diagnosis = {}
                for diagnosis in group:
                    diag_key = diagnosis["key"]
                    # Find rules that led to this diagnosis
                    max_antecedent_count = 0
                    for trace_item in trace:
                        if trace_item["consequent"] == diag_key:
                            rule_id = trace_item["ruleId"]
                            rule = next((r for r in self.rules if r["id"] == rule_id), None)
                            if rule:
                                ant_count = len(rule["antecedents"])
                                max_antecedent_count = max(max_antecedent_count, ant_count)
                    
                    diagnosis["_specificity"] = max_antecedent_count
                    best_by_diagnosis[diag_key] = diagnosis
                
                # Keep highest specificity per diagnosis
                for diagnosis in best_by_diagnosis.values():
                    diagnosis.pop("_specificity", None)
                    resolved.append(diagnosis)
        
        return resolved

    def _get_alternative_diagnoses(self, primary_diagnoses: list[dict]) -> list[dict]:
        """Identify alternative diagnoses that were close but not selected."""
        all_diagnoses = [d for d in primary_diagnoses]
        
        # In a real system, we'd track all possible diagnoses and their confidence
        # For now, if there's only 1 primary diagnosis, provide context
        if len(primary_diagnoses) <= 1:
            return []
        
        # Return diagnoses ranked 2nd and below as alternatives
        return primary_diagnoses[1:] if len(primary_diagnoses) > 1 else []

    def enhance_explanation(self, rule_id: str, trace: list[dict], diagnoses: list[dict]) -> dict:
        """Generate detailed explanation for why a conclusion was reached."""
        rule = next((r for r in self.rules if r["id"] == rule_id), None)
        if not rule:
            return {}
        
        # Find trace entries for this rule and backtrack
        relevant_traces = [t for t in trace if t["ruleId"] == rule_id]
        
        explanations = []
        for trace_item in relevant_traces:
            consequent = trace_item["consequent"]
            antecedent_facts = trace_item["antecedents"]
            confidence = trace_item["derivedConfidence"]
            
            explanation = {
                "rule_id": rule_id,
                "consequent": consequent,
                "consequent_label": FACTS.get(consequent, {}).get("label", consequent),
                "confidence": confidence,
                "confidence_percentage": f"{confidence:.0f}%",
                "rule_confidence": trace_item["confidence"],
                "short_explanation": rule["explanation"],
                "detailed_explanation": self._build_detailed_explanation(
                    antecedent_facts, consequent, rule, confidence
                ),
                "contributing_symptoms": [
                    {"fact": fact, "label": FACTS.get(fact, {}).get("label")} 
                    for fact in antecedent_facts
                    if FACTS.get(fact, {}).get("category") == "symptom"
                ],
                "confidence_breakdown": self._explain_confidence_calculation(
                    antecedent_facts, rule
                ),
            }
            explanations.append(explanation)
        
        return explanations[0] if explanations else {}

    def _build_detailed_explanation(self, antecedents: list[str], consequent: str, rule: dict, confidence: float) -> str:
        """Build detailed natural language explanation."""
        antecedent_labels = [FACTS.get(fact, {}).get("label", fact) for fact in antecedents]
        consequent_label = FACTS.get(consequent, {}).get("label", consequent)
        
        if len(antecedent_labels) == 1:
            return f"Hiện tại bạn có triệu chứng {antecedent_labels[0].lower()}, hệ thống suy diễn {consequent_label.lower()} với độ tin cậy {confidence:.0f}. {rule['explanation']}"
        else:
            antecedent_text = ", ".join(antecedent_labels[:-1]) + f", and {antecedent_labels[-1]}"
            return f"Hiện tại bạn khai báo các triệu chứng {antecedent_text.lower()}, hệ thống suy diễn {consequent_label.lower()} với độ tin cậy {confidence:.0f}. {rule['explanation']}"

    def _explain_confidence_calculation(self, antecedents: list[str], rule: dict) -> str:
        """Explain how confidence was calculated."""
        rule_conf = rule.get("confidence", 80)
        
        return (
            f"Confidence Calculation: "
            f"(Minimum antecedent confidence) × (Rule confidence) = Result\n"
            f"= (All user symptoms are typically reported reliably) × ({rule_conf}%) "
            f"= High confidence in this diagnosis"
        )

    def explain_diagnosis(self, diagnosis_key: str, trace: list[dict]) -> dict:
        """Generate comprehensive explanation for a diagnosis."""
        diagnosis_label = FACTS.get(diagnosis_key, {}).get("label", diagnosis_key)
        
        # Find all rules that contributed to this diagnosis (directly or indirectly)
        contributing_rules = []
        visited = set()
        
        def find_contributors(fact: str):
            if fact in visited:
                return
            visited.add(fact)
            
            for trace_item in trace:
                if trace_item["consequent"] == fact:
                    rule = next((r for r in self.rules if r["id"] == trace_item["ruleId"]), None)
                    if rule:
                        contributing_rules.append({
                            "rule_id": trace_item["ruleId"],
                            "explanation": rule["explanation"],
                            "confidence": trace_item["confidence"],
                            "derived_confidence": trace_item["derivedConfidence"],
                        })
                    
                    # Recursively find contributors to antecedents
                    for antecedent in trace_item["antecedents"]:
                        find_contributors(antecedent)
        
        find_contributors(diagnosis_key)
        
        return {
            "diagnosis": diagnosis_key,
            "diagnosis_label": diagnosis_label,
            "summary": f"The system inferred '{diagnosis_label}' based on {len(contributing_rules)} logical rules.",
            "contributing_rules": contributing_rules,
            "reasoning_chain": self._build_reasoning_chain(diagnosis_key, trace),
        }

    def _build_reasoning_chain(self, target_fact: str, trace: list[dict]) -> list[str]:
        """Build a step-by-step reasoning chain to reach target fact."""
        chain = []
        visited = set()
        
        def build_chain_recursive(fact: str, indent: int = 0):
            if fact in visited:
                return
            visited.add(fact)
            
            # Check if this is an initial fact (no rule produced it)
            produced = any(t["consequent"] == fact for t in trace)
            
            if not produced:
                chain.append("  " * indent + f"✓ {FACTS.get(fact, {}).get('label', fact)}")
            else:
                for trace_item in trace:
                    if trace_item["consequent"] == fact:
                        antecedent_str = " ∧ ".join(
                            FACTS.get(ant, {}).get("label", ant) 
                            for ant in trace_item["antecedents"]
                        )
                        chain.append(
                            "  " * indent + 
                            f"→ {trace_item['ruleId']}: {antecedent_str} ⟹ " +
                            f"{FACTS.get(fact, {}).get('label', fact)} ({trace_item['derivedConfidence']}%)"
                        )
                        
                        # Add antecedents
                        for antecedent in trace_item["antecedents"]:
                            build_chain_recursive(antecedent, indent + 1)
        
        build_chain_recursive(target_fact)
        return chain

    def suggest_next_facts(self, current_facts: list[str]) -> list[str]:
        """Smart question selection based on rules that are close to firing (forward approach)."""
        current = set(current_facts)
        ranked: dict[str, float] = {}

        for rule in self.rules:
            antecedents = rule["antecedents"]
            known_count = sum(1 for fact in antecedents if fact in current)
            missing_facts = [fact for fact in antecedents if fact not in current]

            if known_count == 0 or not missing_facts:
                continue

            # Score based on how close we are to firing this rule
            for fact in missing_facts:
                if FACTS.get(fact, {}).get("category") != "symptom":
                    continue

                score = known_count / len(antecedents)
                ranked[fact] = max(ranked.get(fact, 0), score)

        return [fact for fact, _ in sorted(ranked.items(), key=lambda item: item[1], reverse=True)[:5]]

    @staticmethod
    def priority_weight(priority: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 0)
