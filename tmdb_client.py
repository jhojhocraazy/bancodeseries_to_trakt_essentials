"""Cliente TMDb v3 para séries, com contratos de autenticação, timeout e resposta.

Função: isolar toda a comunicação com a TMDb.
Motivo: manter identidade, confiança e exportação independentes da API externa.
"""

from datetime import datetime


def buscar_estrutura_tmdb(sessao, imdb_id, api_key):
    """Função: obter TMDb ID, temporadas e episódios de uma série.
    Motivo: fornecer a estrutura de consumo já filtrada por data de exibição.
    """
    url_find = f"https://api.themoviedb.org/3/find/{imdb_id}"
    resposta_find = sessao.get(
        url_find,
        params={"api_key": api_key, "external_source": "imdb_id"},
        timeout=15,
    )
    resposta_find.raise_for_status()
    res = resposta_find.json().get("tv_results", [])
    if not res:
        return None, {}

    tmdb_id = str(res[0]["id"])
    resposta_detalhe = sessao.get(
        f"https://api.themoviedb.org/3/tv/{tmdb_id}",
        params={"api_key": api_key},
        timeout=15,
    )
    resposta_detalhe.raise_for_status()
    total_temporadas = resposta_detalhe.json().get("number_of_seasons", 0)

    hoje = datetime.now().strftime("%Y-%m-%d")
    tmdb_struct = {}
    for temporada in range(1, total_temporadas + 1):
        resposta_season = sessao.get(
            f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{temporada}",
            params={"api_key": api_key},
            timeout=15,
        )
        if resposta_season.status_code != 200:
            continue
        tmdb_struct[temporada] = []
        for episodio in resposta_season.json().get("episodes", []):
            numero = episodio.get("episode_number")
            if numero == 0:
                continue
            air_date = episodio.get("air_date")
            tmdb_struct[temporada].append({
                "episode": numero,
                "tmdb_id": episodio.get("id"),
                "air_date": air_date,
                "lancado": bool(air_date and air_date <= hoje),
            })
    return tmdb_id, tmdb_struct


def buscar_fallback_tmdb(sessao, nome_serie, api_key, session_quote=None):
    """Função: procurar um IMDb ID externo quando o identificador direto falha.
    Motivo: recuperar IDs legados sem aceitar automaticamente o primeiro resultado.
    """
    import re
    from urllib.parse import quote

    consulta = re.sub(r"\(.*?\)", "", nome_serie).strip()
    try:
        resposta_busca = sessao.get(
            "https://api.themoviedb.org/3/search/tv",
            params={"api_key": api_key, "query": quote(consulta)},
            timeout=15,
        )
        resposta_busca.raise_for_status()
        resultados = resposta_busca.json().get("results", [])
        if not resultados:
            return None
        resposta_ext = sessao.get(
            f"https://api.themoviedb.org/3/tv/{resultados[0]['id']}/external_ids",
            params={"api_key": api_key},
            timeout=15,
        )
        if resposta_ext.status_code != 200:
            return None
        return resposta_ext.json().get("imdb_id")
    except Exception:
        return None
