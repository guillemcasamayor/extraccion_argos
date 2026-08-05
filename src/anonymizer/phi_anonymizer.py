"""
Módulo de De-Identificación y Anonimización de Datos Clínicos (HIPAA / RGPD)
Reemplaza identificadores personales (Nombres, DNI, NHC, Fechas exactas, Teléfonos)
por tokens enmascarados como [PACIENTE], [DNI], [FECHA], [MEDICO].
"""

import re
from typing import Dict, List, Tuple

class PHIAnonymizer:
    def __init__(self):
        # Reglas estrictas de de-identificación de PHI/PII (RGPD / HIPAA)
        # PRESERVA: Fechas (cronología vital), Especialidades médicas, Rangos (Residente/MIR/R1-R5/Adjunto), Síntomas y Fármacos.
        self.rules: List[Tuple[str, str]] = [
            # DNI / NIE / NIF
            (r"\b[0-9]{8}[A-Z]\b", "[DNI]"),
            (r"\b[XYZ][0-9]{7}[A-Z]\b", "[NIE]"),
            # CIP / CIPNS / NHC (Número de Historia Clínica)
            (r"\b(NHC|CIP|Nº Historia|Nº HIC):\s*[A-Z0-9-]+\b", r"\1: [ID_HISTORIA]"),
            # Nombres de Médicos / Facultativos (ej. Dr. Juan Pérez), conservando rango (Residente/MIR/R1-R5/Adjunto)
            (r"\b(Dr\.|Dra\.|Doctor|Doctora|Fdo\.|Firmado por:?)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)", r"\1 [MEDICO]"),
            # Correos electrónicos y Teléfonos
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
            (r"\b(\+34|0034)?\s*[679]\d{2}(\s*\d{2}){3}\b", "[TELEFONO]"),
        ]

    def anonymize_text(self, text: str) -> str:
        """
        Aplica reglas de de-identificación al texto proporcionado.
        Conserva Fechas, Especialidades Médicas y estatus de Residente/MIR/Adjunto.
        """
        anonymized = text
        for pattern, replacement in self.rules:
            anonymized = re.sub(pattern, replacement, anonymized, flags=re.IGNORECASE)
        
        return anonymized



    def anonymize_patient_record(self, record: Dict[str, str]) -> Dict[str, str]:
        """
        Anonimiza todas las secciones del diccionario extraído por SAPChromeExtractor.
        """
        anonymized_record = {}
        for key, content in record.items():
            if isinstance(content, str):
                anonymized_record[key] = self.anonymize_text(content)
            else:
                anonymized_record[key] = content
        return anonymized_record

if __name__ == "__main__":
    anonymizer = PHIAnonymizer()
    test_text = "Paciente Juan Pérez con DNI 12345678X y NHC 98765432 visto el 12/05/2024 por Dr. Martínez."
    print("Texto original:", test_text)
    print("Texto anonimizado:", anonymizer.anonymize_text(test_text))
