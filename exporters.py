"""Camada de exportação Trakt: contratos de colunas e escrita atômica de CSV.

Função: transformar registros já resolvidos em History, Ratings e nomes de arquivo.
Motivo: manter a exportação independente de rede, identidade e regras de consumo.
"""

import csv
import os
import tempfile
from pathlib import Path

COLUNAS_HISTORY = ["imdb_id", "tmdb_id", "type"]
COLUNAS_RATINGS = ["imdb_id", "tmdb_id", "type", "rating"]


def linhas_history(linhas_exportacao):
    """Função: selecionar as linhas destined ao History.
    Motivo: séries de grades atrasadas não podem marcar a obra inteira como assistida.
    """
    return [linha for linha in linhas_exportacao if not linha.get("ignorar_no_historico")]


def linhas_com_nota(linhas_exportacao):
    """Função: selecionar as linhas que possuem nota disponível.
    Motivo: preservar zero como nota válida e tratar ausência como vazio.
    """
    return [
        linha for linha in linhas_exportacao
        if linha.get("rating") not in (None, "")
    ]


def escrever_csv_atomico(destino, fieldnames, linhas):
    """Função: escrever um CSV em arquivo temporário e publicar por substituição.
    Motivo: uma falha de escrita não pode deixar um CSV final truncado.
    """
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", encoding="utf-8",
            prefix=f"{destino.name}.", suffix=".part", dir=destino.parent,
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            escritor = csv.DictWriter(arquivo, fieldnames=fieldnames, extrasaction="ignore")
            escritor.writeheader()
            escritor.writerows(linhas)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, destino)
    except Exception:
        if temporario is not None:
            try:
                temporario.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def exportar_trakt(linhas_exportacao, timestamp_arquivo):
    """Função: gerar History e Ratings com o mesmo timestamp.
    Motivo: preservar a separação entre histórico de visualização e avaliações.
    """
    history = linhas_history(linhas_exportacao)
    ratings = linhas_com_nota(linhas_exportacao)
    nome_history = f"exportacao_history_{timestamp_arquivo}.csv"
    nome_ratings = f"exportacao_ratings_{timestamp_arquivo}.csv"
    if linhas_exportacao:
        escrever_csv_atomico(Path(nome_history), COLUNAS_HISTORY, history)
        if ratings:
            escrever_csv_atomico(Path(nome_ratings), COLUNAS_RATINGS, ratings)
    return history, ratings, nome_history, nome_ratings
