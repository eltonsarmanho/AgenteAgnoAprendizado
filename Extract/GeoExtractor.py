"""
GeoExtractor - Extrator de Coordenadas Geograficas
===================================================

Script para extrair coordenadas geograficas de documentos PDF
usando processamento de linguagem natural.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Coordenada:
    """Representa uma coordenada geografica."""
    latitude: float
    longitude: float
    formato_original: str
    contexto: str = ""


class GeoExtractor:
    """Extrator de coordenadas geograficas de textos."""
    
    PADRAO_DECIMAL = r'[-+]?\d{1,3}\.\d+'
    PADRAO_GMS = r"(\d{1,3})[°º]\s*(\d{1,2})['′]\s*(\d{1,2}(?:\.\d+)?)[\"″]?\s*([NSEW])"
    
    def __init__(self):
        self.coordenadas_extraidas = []
    
    def extrair_decimal(self, texto: str) -> List[Tuple[float, float]]:
        """Extrai coordenadas em formato decimal."""
        matches = re.findall(self.PADRAO_DECIMAL, texto)
        coordenadas = []
        
        for i in range(0, len(matches) - 1, 2):
            try:
                lat = float(matches[i])
                lon = float(matches[i + 1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    coordenadas.append((lat, lon))
            except (ValueError, IndexError):
                continue
        
        return coordenadas
    
    def gms_para_decimal(self, graus: float, minutos: float, segundos: float, direcao: str) -> float:
        """Converte graus, minutos, segundos para decimal."""
        decimal = graus + minutos / 60 + segundos / 3600
        if direcao in ['S', 'W']:
            decimal = -decimal
        return decimal
    
    def extrair_gms(self, texto: str) -> List[Coordenada]:
        """Extrai coordenadas em formato GMS."""
        matches = re.findall(self.PADRAO_GMS, texto)
        coordenadas = []
        
        for match in matches:
            graus, minutos, segundos, direcao = match
            decimal = self.gms_para_decimal(
                float(graus), float(minutos), float(segundos), direcao
            )
            coordenadas.append(Coordenada(
                latitude=decimal if direcao in ['N', 'S'] else 0,
                longitude=decimal if direcao in ['E', 'W'] else 0,
                formato_original=f"{graus}°{minutos}'{segundos}\"{direcao}"
            ))
        
        return coordenadas
    
    def extrair_todas(self, texto: str) -> Dict:
        """Extrai todas as coordenadas do texto."""
        resultado = {
            'decimal': self.extrair_decimal(texto),
            'gms': self.extrair_gms(texto),
            'total': 0
        }
        resultado['total'] = len(resultado['decimal']) + len(resultado['gms'])
        return resultado
    
    def validar_coordenada(self, lat: float, lon: float) -> bool:
        """Valida se uma coordenada esta dentro dos limites."""
        return -90 <= lat <= 90 and -180 <= lon <= 180


def main():
    """Funcao principal de demonstracao."""
    extractor = GeoExtractor()
    
    texto_teste = """
    O terreno esta localizado nas coordenadas -23.550520, -46.633308.
    Tambem foi identificado o ponto 23°33'05"S 46°37'59"W.
    """
    
    resultado = extractor.extrair_todas(texto_teste)
    
    print("Coordenadas encontradas:")
    print(f"  Decimal: {resultado['decimal']}")
    print(f"  GMS: {resultado['gms']}")
    print(f"  Total: {resultado['total']}")


if __name__ == "__main__":
    main()
