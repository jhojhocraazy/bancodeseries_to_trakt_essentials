# Agente de Integrações Externas

## Responsabilidade

Manter as integrações com Banco de Séries, IMDb, TMDb e as bibliotecas HTTP, respeitando contratos, timeouts e segurança.

## Escopo

- Sessão autenticada do Banco de Séries.
- Datasets `title.ratings.tsv.gz` e `title.episode.tsv.gz`.
- API TMDb v3 para find, detalhes, temporadas e IDs externos.
- `requests`, `HTTPAdapter`, `Retry` e `BeautifulSoup`.

## Regras

- Nunca expor `tmdb_api.txt`, `phpsessid.txt` ou valores equivalentes.
- Preservar timeouts e User-Agent existentes, salvo solicitação explícita.
- Usar `raise_for_status()` e tratar respostas JSON vazias ou inválidas.
- Não fazer uma requisição por episódio quando o dataset IMDb local resolver a relação.
- Datasets só devem ser baixados quando ausentes e necessários.
- Falha de download não deve produzir saída parcial.
- O fallback do IMDb/TMDb deve ser separado da decisão de confiança.
- Não adicionar dependência sem necessidade aprovada.

## Testes

Simular respostas de sucesso, JSON vazio, HTTP 429, 5xx, timeout, dataset corrompido, TMDb sem série e sessão expirada.
