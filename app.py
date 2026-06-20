#from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from medical_expert.knowledge_base import FACTS, QUICK_FACT_KEYS, RULES, DIAGNOSIS_METADATA, reload_kb_in_memory
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
            conflict_strategy = str(payload.get("conflictStrategy", "all_rules"))
            if not isinstance(user_facts, list):
                self.send_error(HTTPStatus.BAD_REQUEST, "userFacts must be a list")
                return

            response = analyze_symptoms(
                user_facts=user_facts,
                message=message,
                conflict_strategy=conflict_strategy
            )
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
