#from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from medical_expert.knowledge_base import FACTS, QUICK_FACT_KEYS, RULES, DIAGNOSIS_METADATA, save_kb, reload_kb_in_memory
from medical_expert.service import analyze_symptoms, explain_diagnosis_detail, get_rule_explanation


ROOT_DIR = Path(__file__).resolve().parent


class MedicalExpertHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/bootstrap":
            self.send_json(
                {
                    "facts": {key: {"label": value["label"], "category": value["category"]} for key, value in FACTS.items()},
                    "quickFacts": QUICK_FACT_KEYS,
                }
            )
            return

        if parsed.path == "/api/kb":
            self.send_json(
                {
                    "facts": FACTS,
                    "rules": RULES,
                    "diagnosisMetadata": DIAGNOSIS_METADATA,
                    "quickFacts": QUICK_FACT_KEYS,
                }
            )
            return

        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/kb/save":
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
                return
            
            facts = payload.get("facts")
            rules = payload.get("rules")
            metadata = payload.get("diagnosisMetadata")
            quick_facts = payload.get("quickFacts")
            
            if not isinstance(facts, dict):
                self.send_error(HTTPStatus.BAD_REQUEST, "facts must be an object")
                return
            if not isinstance(rules, list):
                self.send_error(HTTPStatus.BAD_REQUEST, "rules must be a list")
                return
            if not isinstance(metadata, dict):
                self.send_error(HTTPStatus.BAD_REQUEST, "diagnosisMetadata must be an object")
                return
            if not isinstance(quick_facts, list):
                self.send_error(HTTPStatus.BAD_REQUEST, "quickFacts must be a list")
                return
            
            # Validate facts
            for key, val in facts.items():
                if not isinstance(val, dict) or "label" not in val or "category" not in val:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Invalid fact definition for key: {key}")
                    return
                if val["category"] not in ["symptom", "derived", "diagnosis"]:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Invalid category for fact: {key}")
                    return
                if "synonyms" not in val:
                    val["synonyms"] = []
                elif not isinstance(val["synonyms"], list):
                    self.send_error(HTTPStatus.BAD_REQUEST, f"synonyms for fact: {key} must be a list")
                    return

            # Validate rules
            rule_ids = set()
            for r in rules:
                if not isinstance(r, dict) or "id" not in r or "antecedents" not in r or "consequent" not in r:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Rules must contain id, antecedents, and consequent")
                    return
                
                r_id = r["id"]
                if r_id in rule_ids:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Duplicate rule ID: {r_id}")
                    return
                rule_ids.add(r_id)
                
                if not isinstance(r["antecedents"], list) or not r["antecedents"]:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Rule {r_id} must have at least one antecedent")
                    return
                
                for ant in r["antecedents"]:
                    if ant not in facts:
                        self.send_error(HTTPStatus.BAD_REQUEST, f"Rule {r_id} references undefined antecedent: {ant}")
                        return
                
                consequent = r["consequent"]
                if consequent not in facts:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Rule {r_id} references undefined consequent: {consequent}")
                    return
                
                if "confidence" in r:
                    try:
                        conf = float(r["confidence"])
                        if not (0 <= conf <= 100):
                            raise ValueError
                        r["confidence"] = conf
                    except (ValueError, TypeError):
                        self.send_error(HTTPStatus.BAD_REQUEST, f"Rule {r_id} confidence must be a number between 0 and 100")
                        return
                else:
                    r["confidence"] = 80
                    
                if "explanation" not in r:
                    r["explanation"] = ""
            
            # Validate quick facts
            for qf in quick_facts:
                if qf not in facts:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"quickFacts references undefined fact: {qf}")
                    return
                if facts[qf]["category"] != "symptom":
                    self.send_error(HTTPStatus.BAD_REQUEST, f"quickFact {qf} must be a symptom")
                    return
                    
            # Validate metadata
            for diag_key, meta in metadata.items():
                if diag_key not in facts or facts[diag_key]["category"] != "diagnosis":
                    self.send_error(HTTPStatus.BAD_REQUEST, f"diagnosisMetadata references undefined or non-diagnosis fact: {diag_key}")
                    return
                if not isinstance(meta, dict):
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Metadata for {diag_key} must be an object")
                    return
                if "priority" not in meta or meta["priority"] not in ["high", "medium", "low"]:
                    self.send_error(HTTPStatus.BAD_REQUEST, f"Invalid priority for {diag_key} metadata")
                    return
                if "advice" not in meta:
                    meta["advice"] = ""

            # Save and reload
            data_to_save = {
                "FACTS": facts,
                "RULES": rules,
                "DIAGNOSIS_METADATA": metadata,
                "QUICK_FACT_KEYS": quick_facts
            }
            save_kb(data_to_save)
            reload_kb_in_memory()
            
            self.send_json({"status": "success"})
            return

        if parsed.path == "/api/analyze":
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
                return

            message = str(payload.get("message", ""))
            user_facts = payload.get("userFacts", [])
            if not isinstance(user_facts, list):
                self.send_error(HTTPStatus.BAD_REQUEST, "userFacts must be a list")
                return

            response = analyze_symptoms(user_facts=user_facts, message=message)
            self.send_json(response)
            return
        
        if parsed.path == "/api/explain-diagnosis":
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
                return
            
            diagnosis_key = payload.get("diagnosis")
            trace = payload.get("trace", [])
            
            explanation = explain_diagnosis_detail(diagnosis_key, trace)
            self.send_json(explanation)
            return
        
        if parsed.path == "/api/explain-rule":
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            try:
                payload = json.loads(raw_body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
                return
            
            rule_id = payload.get("rule_id")
            trace = payload.get("trace", [])
            diagnoses = payload.get("diagnoses", [])
            
            explanation = get_rule_explanation(rule_id, trace, diagnoses)
            self.send_json(explanation)
            return
        
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def serve_static(self, request_path: str) -> None:
        resolved_path = self.resolve_static_path(request_path)
        if not resolved_path or not resolved_path.exists() or not resolved_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        content_type, _ = mimetypes.guess_type(str(resolved_path))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.end_headers()
        self.wfile.write(resolved_path.read_bytes())

    def resolve_static_path(self, request_path: str) -> Path | None:
        clean_path = request_path.lstrip("/") or "index.html"
        candidate = (ROOT_DIR / clean_path).resolve()
        try:
            candidate.relative_to(ROOT_DIR)
        except ValueError:
            return None
        return candidate

    def send_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), MedicalExpertHandler)
    print("Medical expert chatbot is running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
