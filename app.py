from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from medical_expert.knowledge_base import FACTS, QUICK_FACT_KEYS
from medical_expert.service import analyze_symptoms


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

        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return

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
