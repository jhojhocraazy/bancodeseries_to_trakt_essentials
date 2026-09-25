"""Regras puras de identidade: normalização de títulos e auditoria de fallback.

Função: isolar a decisão de correspondência sem realizar E/S.
Motivo: impedir que a camada de exportação redecida identidade e manter o fallback auditável.
"""

import re
import unicodedata


def normalize_text(texto):
    """Função: normalizar um título para comparação.
    Motivo: ignorar acentos, caixa e espaços extras na auditoria de fallback.
    """
    if not texto:
        return ""
    normalizado = unicodedata.normalize("NFKD", str(texto))
    normalizado = "".join(c for c in normalizado if not unicodedata.combining(c))
    normalizado = re.sub(r"\(.*?\)", "", normalizado)
    return re.sub(r"\s+", " ", normalizado).strip().lower()


def similarity(primeiro, segundo):
    """Função: calcular similaridade entre dois títulos normalizados.
    Motivo: rejeitar candidatos fracos antes de aceitar um fallback textual.
    """
    a, b = normalize_text(primeiro), normalize_text(segundo)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    palavras_a, palavras_b = set(a.split()), set(b.split())
    if not palavras_a or not palavras_b:
        return 0.0
    return len(palavras_a & palavras_b) / len(palavras_a | palavras_b)


def fallback_confiavel(nome_bds, titulo_candidato, imdb_id_externo, limiar=0.6):
    """Função: decidir se um resultado de busca textual pode ser aceito.
    Motivo: impedir que homônimos ou filmes sejam exportados como a série correta.
    """
    if not imdb_id_externo:
        return False
    return similarity(nome_bds, titulo_candidato) >= limiar
