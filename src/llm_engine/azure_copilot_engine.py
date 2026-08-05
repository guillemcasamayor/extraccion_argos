"""
Motor de Inferencia LLM Corporativo vía API (Azure OpenAI / Copilot Enterprise)
Conexión cifrada segura con cumplimiento de RGPD / HIPAA (Zero Data Retention).
"""

import os
import time
import requests
from typing import Dict, Any, Optional
from .prompts import SYSTEM_PROMPT_RADIOLOGY_SUMMARY, USER_PROMPT_TEMPLATE

class AzureCopilotEngine:
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, deployment_name: Optional[str] = None):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f).get("azure_openai", {})
            except Exception:
                pass

        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY") or config.get("api_key", "")
        self.endpoint = (endpoint or os.getenv("AZURE_OPENAI_ENDPOINT") or config.get("endpoint", "")).rstrip("/")
        self.deployment_name = deployment_name or config.get("deployment_name", "gpt-4o")


    def generate_summary(self, clinical_notes: str, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Envía las notas clínicas anonimizadas a la API Corporativa de Azure OpenAI / Copilot.
        """
        if not self.endpoint or not self.api_key:
            return {
                "status": "error",
                "error_message": "Credenciales no configuradas. Defina AZURE_OPENAI_API_KEY y AZURE_OPENAI_ENDPOINT.",
                "elapsed_seconds": 0
            }

        user_content = USER_PROMPT_TEMPLATE.format(clinical_notes=clinical_notes)
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version=2024-02-15-preview"
        
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_RADIOLOGY_SUMMARY},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature
        }

        start_time = time.time()
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return {
                    "status": "success",
                    "model": self.deployment_name,
                    "engine": "Azure_Copilot_API",
                    "elapsed_seconds": round(elapsed_time, 2),
                    "summary": content,
                    "raw_response": result
                }
            else:
                return {
                    "status": "error",
                    "error_message": f"Error HTTP {response.status_code}: {response.text}",
                    "elapsed_seconds": round(elapsed_time, 2)
                }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Error al conectar con Azure Copilot API: {str(e)}",
                "elapsed_seconds": round(time.time() - start_time, 2)
            }

if __name__ == "__main__":
    engine = AzureCopilotEngine()
    print(f"Motor AzureCopilotEngine instanciado para despliegue: {engine.deployment_name}")
