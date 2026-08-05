import os
import json
import time
import requests
from typing import Dict, Any, Optional
from .prompts import SYSTEM_PROMPT_RADIOLOGY_SUMMARY, USER_PROMPT_TEMPLATE

class OllamaLocalEngine:
    def __init__(self, base_url: Optional[str] = None, model_name: Optional[str] = None):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f).get("ollama", {})
            except Exception:
                pass

        self.base_url = (base_url or config.get("base_url", "http://localhost:11434")).rstrip("/")
        self.model_name = model_name or config.get("default_model", "qwen2.5:7b-instruct")

    def generate_summary(self, clinical_notes: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Envía las notas clínicas a la instancia local de Ollama.
        """
        user_content = USER_PROMPT_TEMPLATE.format(clinical_notes=clinical_notes)
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_RADIOLOGY_SUMMARY},
                {"role": "user", "content": user_content}
            ],
            "options": {
                "temperature": temperature
            },
            "stream": False
        }

        start_time = time.time()
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                return {
                    "status": "success",
                    "model": self.model_name,
                    "engine": "Ollama_Local",
                    "elapsed_seconds": round(elapsed_time, 2),
                    "summary": content,
                    "raw_response": result
                }
            else:
                return {
                    "status": "error",
                    "error_message": f"Ollama respondió con error HTTP {response.status_code}. ¿Está descargado el modelo '{self.model_name}'? Ejecuta: 'ollama pull {self.model_name}'",
                    "elapsed_seconds": round(elapsed_time, 2)
                }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"No se pudo conectar con Ollama en {self.base_url}.\n\nPara solucionarlo:\n1. Instala Ollama desde https://ollama.com\n2. Ejecuta en consola: 'ollama run {self.model_name}'\n3. O configura la IP del servidor de IA del hospital en config.json",
                "elapsed_seconds": round(time.time() - start_time, 2)
            }


if __name__ == "__main__":
    engine = OllamaLocalEngine()
    print(f"Motor OllamaLocalEngine instanciado para modelo: {engine.model_name}")
