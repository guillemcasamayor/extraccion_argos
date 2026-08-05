"""
Módulo de Extracción de Historia Clínica desde SAP / RIS (Google Chrome)
Soporta:
1. Parseo de archivos HTML / HTM guardados localmente desde la interfaz de SAP.
2. Extracción directa del DOM desde Chrome utilizando BeautifulSoup / Playwright.
"""

import os
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

class SAPChromeExtractor:
    def __init__(self):
        pass

    def parse_html_file(self, file_path: str) -> Dict[str, str]:
        """
        Lee un archivo HTML exportado/guardado de SAP en Google Chrome
        y extrae las secciones clínicas relevantes.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No se encontró el archivo HTML en: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        return self.parse_html_content(html_content)

    def parse_html_content(self, html_content: str) -> Dict[str, str]:
        """
        Parsea el código HTML de la interfaz de SAP y extrae los campos clave.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Eliminamos elementos irrelevantes (scripts, estilos, navegación)
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        # Extraemos todo el texto estructurado o párrafos relevantes
        text_lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
        full_text = "\n".join(text_lines)

        # Secciones clínicas aproximadas (ajustables según la plantilla exacta de SAP del hospital)
        sections = {
            "full_text": full_text,
            "motivo_consulta": self._extract_section(full_text, ["Motivo", "Indicación", "Petición", "Reason"]),
            "antecedentes": self._extract_section(full_text, ["Antecedentes", "History", "Historial", "Patologías"]),
            "evolutivos": self._extract_section(full_text, ["Curso clínico", "Evolutivo", "Notas", "Notes"]),
            "informes_previos": self._extract_section(full_text, ["Informes previos", "Radiología previa", "Pruebas anteriores"])
        }

        return sections

    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """
        Busca bloques de texto encabezados por palabras clave clínicas.
        """
        extracted = []
        lines = text.splitlines()
        capturing = False
        
        pattern = re.compile(r"|".join(keywords), re.IGNORECASE)
        
        for line in lines:
            if pattern.search(line):
                capturing = True
                extracted.append(line)
            elif capturing:
                if len(line) < 3 or line.endswith(":"):
                    # Si parece un nuevo encabezado, detiene la captura del bloque
                    if any(header_word in line.lower() for header_word in ["médico", "fecha", "servicio", "firmado"]):
                        capturing = False
                    else:
                        extracted.append(line)
                else:
                    extracted.append(line)

        return "\n".join(extracted[:30])  # Limitar tamaño máximo del bloque capturado

if __name__ == "__main__":
    extractor = SAPChromeExtractor()
    print("Módulo SAPChromeExtractor inicializado correctamente.")
