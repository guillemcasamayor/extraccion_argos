"""
Servidor Local HTTP nativo (sin dependencias externas) para la Extracción y Resumen en Tiempo Real desde Google Chrome.
Escucha en http://127.0.0.1:5000 y recibe el contenido HTML/Texto directamente desde la pestaña de SAP en Chrome.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from src.scraper.sap_chrome_extractor import SAPChromeExtractor
from src.anonymizer.phi_anonymizer import PHIAnonymizer
from src.llm_engine.ollama_local_engine import OllamaLocalEngine
from src.llm_engine.azure_copilot_engine import AzureCopilotEngine

extractor = SAPChromeExtractor()
anonymizer = PHIAnonymizer()

class RISServerHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            response = {"status": "ok", "message": "Servidor RIS LLM activo en local (http://127.0.0.1:5000)"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/summarize":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode("utf-8"))
            except Exception:
                data = {}

            raw_html = data.get("html", "")
            raw_text = data.get("text", "")
            engine_type = data.get("engine", "local")
            model_name = data.get("model", "qwen2.5:7b-instruct")

            # 1. Extracción de datos
            if raw_html:
                extracted = extractor.parse_html_content(raw_html)
                clinical_notes = extracted.get("full_text", "")
            else:
                clinical_notes = raw_text

            # 2. De-Identificación Local (RGPD / HIPAA)
            anonymized_notes = anonymizer.anonymize_text(clinical_notes)

            # 3. Inferencia o Generación de Prompt Manual para Copilot Chat Web
            if engine_type == "copilot_manual":
                from src.llm_engine.prompts import SYSTEM_PROMPT_RADIOLOGY_SUMMARY, USER_PROMPT_TEMPLATE
                full_prompt = f"{SYSTEM_PROMPT_RADIOLOGY_SUMMARY}\n\n" + USER_PROMPT_TEMPLATE.format(clinical_notes=anonymized_notes)
                
                # Guardar en carpeta data/copilot_prompts/
                import os, time
                prompts_dir = os.path.join(os.path.dirname(__file__), "data", "copilot_prompts")
                os.makedirs(prompts_dir, exist_ok=True)
                file_name = f"prompt_copilot_{int(time.time())}.txt"
                file_path = os.path.join(prompts_dir, file_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(full_prompt)

                result = {
                    "status": "success",
                    "engine": "Copilot_Chat_Manual",
                    "mode": "prompt_only",
                    "file_saved": file_path,
                    "ready_prompt": full_prompt,
                    "elapsed_seconds": 0.05,
                    "summary": f"✅ PROMPT Y HISTORIA ANONIMIZADA LISTOS PARA PEGAR EN COPILOT CHAT WEB.\n\n"
                               f"📄 Se ha guardado una copia en:\n{file_path}\n\n"
                               f"📋 Haz clic en 'Copiar al Portapapeles' y pégalo (Ctrl + V) directamente en Microsoft Copilot."
                }
            elif engine_type == "local":
                llm = OllamaLocalEngine(model_name=model_name)
                result = llm.generate_summary(anonymized_notes)
            else:
                llm = AzureCopilotEngine(deployment_name=model_name)
                result = llm.generate_summary(anonymized_notes)

            result["anonymized_notes_sample"] = anonymized_notes[:300] + "..."


            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=5000):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, RISServerHandler)
    print(f"[OK] Servidor Local RIS LLM activo en http://127.0.0.1:{port} ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")


if __name__ == "__main__":
    run_server()
