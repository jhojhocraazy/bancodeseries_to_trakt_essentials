# Contratos de exportação — Banco de Séries -> Trakt Essentials

## History

Arquivo: `exportacao_history_<timestamp>.csv`

Cabeçalho exato:

```csv
imdb_id,tmdb_id,type
```

- `type` usa `show` para a série e `episode` para episódios.
- History não contém nota.
- Séries de grades atrasadas não geram linha `show` no History.
- Episódios futuros não são exportados como assistidos.

## Ratings

Arquivo: `exportacao_ratings_<timestamp>.csv`

Cabeçalho exato:

```csv
imdb_id,tmdb_id,type,rating
```

- Somente linhas com nota disponível são exportadas.
- `0.0` é uma nota válida e deve ser preservado.
- Nota ausente não é convertida em zero.
- Ratings é independente de History.

## Regras comuns

- UTF-8.
- Ordem de colunas é contrato público.
- Campos internos, como `ignorar_no_historico`, nunca vazam.
- History e Ratings usam o mesmo timestamp.
- A publicação dos arquivos é atômica.
- A ferramenta não importa arquivos no Trakt; a importação é manual.

## Validação

Antes de entregar os arquivos, confirmar:

1. cabeçalho exato;
2. ordem das colunas;
3. ausência de campos internos;
4. ausência de credenciais;
5. ausência de episódios futuros;
6. relatório coerente com a quantidade de linhas.
