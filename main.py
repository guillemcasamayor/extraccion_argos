"""
Script Principal del Proyecto: Pipeline de Extracción, Anonimización y Resumen con LLM
"""

import sys
import json
import argparse
from src.scraper.sap_chrome_extractor import SAPChromeExtractor
from src.anonymizer.phi_anonymizer import PHIAnonymizer
from src.llm_engine.ollama_local_engine import OllamaLocalEngine
from src.llm_engine.azure_copilot_engine import AzureCopilotEngine
from src.evaluator.evaluate_summaries import SummaryEvaluator

def run_pipeline(html_path: str, engine_type: str = "local", model_name: str = "qwen2.5:7b-instruct"):
    print(f"--- 1. Extrayendo datos de SAP/Chrome desde: {html_path} ---")
    extractor = SAPChromeExtractor()
    extracted_data = extractor.parse_html_file(html_path)
    
    print("--- 2. Aplicando De-Identificación Local RGPD/HIPAA ---")
    anonymizer = PHIAnonymizer()
    clean_data = anonymizer.anonymize_patient_record(extracted_data)
    clinical_notes = clean_data.get("full_text", "")
    
    print(f"--- 3. Generando Resumen Radiológico con Motor [{engine_type.upper()}] ---")
    if engine_type.lower() == "local":
        engine = OllamaLocalEngine(model_name=model_name)
        result = engine.generate_summary(clinical_notes)
    else:
        engine = AzureCopilotEngine(deployment_name=model_name)
        result = engine.generate_summary(clinical_notes)
        
    print("\n================ RESULTADO DEL RESUMEN ================")
    print(f"Estado: {result.get('status')}")
    print(f"Tiempo de ejecución: {result.get('elapsed_seconds')} segundos")
    print(f"Resumen generado:\n{result.get('summary')}")
    print("========================================================\n")
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline RIS LLM Summary")
    parser.add_argument("--html", type=str, help="Ruta al archivo HTML de SAP/Chrome", required=False)
    parser.add_argument("--engine", type=str, choices=["local", "api"], default="local", help="Motor LLM a usar")
    parser.add_argument("--model", type=str, default="qwen2.5:7b-instruct", help="Nombre del modelo")
    
    args = parser.parse_args()
    
    if args.html:
        run_pipeline(args.html, args.engine, args.model)
    else:
        print("Pipeline instalado y listo. Ejecuta con --html <ruta_archivo.html> para procesar un expediente.")
