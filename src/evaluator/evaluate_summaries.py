"""
Módulo de Evaluación y Benchmarking de Resúmenes Clínicos (Local vs API)
Calcula métricas automáticas de similitud y prepara estructuras para la evaluación cualitativa ciega por radiólogos.
"""

import json
from typing import Dict, List, Any

class SummaryEvaluator:
    def __init__(self):
        pass

    def evaluate_exact_overlap(self, reference: str, summary: str) -> Dict[str, float]:
        """
        Calcula superposición básica de palabras clave (Jaccard similarity).
        """
        ref_words = set(reference.lower().split())
        sum_words = set(summary.lower().split())

        if not ref_words or not sum_words:
            return {"jaccard_similarity": 0.0}

        intersection = ref_words.intersection(sum_words)
        union = ref_words.union(sum_words)

        return {
            "jaccard_similarity": round(len(intersection) / len(union), 4)
        }

    def prepare_blind_review_entry(self, case_id: str, clinical_notes: str, summary_local: str, summary_api: str, clinician_indication: str) -> Dict[str, Any]:
        """
        Genera una entrada anonimizada a ciegas (Blind Review) para que los radiólogos
        evalúen Resumen A vs Resumen B sin saber cuál proviene de qué LLM o del clínico.
        """
        import random
        options = [
            {"id": "Option_A", "source": "Ollama_Local", "text": summary_local},
            {"id": "Option_B", "source": "Azure_Copilot_API", "text": summary_api},
            {"id": "Option_C", "source": "Clinician_Original", "text": clinician_indication}
        ]
        random.shuffle(options)

        return {
            "case_id": case_id,
            "clinical_notes": clinical_notes,
            "blinded_options": options,
            "evaluation_rubric": {
                "comprehensiveness_likert_1_5": "1 (Incompleto) a 5 (Muy Exhaustivo)",
                "factuality_likert_1_5": "1 (Alucinaciones severas) a 5 (100% Factual sin alucinaciones)",
                "conciseness_likert_1_5": "1 (Demasiado largo/redundante) a 5 (Conciso y directo)",
                "usefulness_protocoling_rank": "Orden de preferencia (1 = Mejor, 3 = Peor) para protocolar",
                "usefulness_interpretation_rank": "Orden de preferencia (1 = Mejor, 3 = Peor) para diagnosticar"
            }
        }

if __name__ == "__main__":
    evaluator = SummaryEvaluator()
    print("Módulo SummaryEvaluator listo para benchmarking.")
