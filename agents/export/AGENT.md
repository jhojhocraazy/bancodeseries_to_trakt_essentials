# Agente de Exportação Trakt

## Responsabilidade

Transformar registros já resolvidos em arquivos History e Ratings compatíveis com o Trakt e gerar o relatório da execução.

## Escopo

- `linhas_exportacao`.
- `exportacao_history_<timestamp>.csv`.
- `exportacao_ratings_<timestamp>.csv`.
- `relatorio_execucao_<timestamp>.txt`.
- Métricas de séries, temporadas e episódios.

## Contratos

History deve manter a ordem:

```text
imdb_id,tmdb_id,type
```

Ratings deve manter a ordem:

```text
imdb_id,tmdb_id,type,rating
```

History não deve incluir `rating`. Ratings deve conter somente linhas com nota válida/disponível e deve preservar a linha original sem flags internas. `csv.DictWriter` deve continuar ignorando campos como `ignorar_no_historico`.

## Regras

- Não reconsultar a rede na camada de exportação.
- Não decidir identidade ou assistidos.
- Não publicar arquivo quando a coleta estiver incompleta por erro fatal.
- Ratings e History devem ser escritos de forma independente e com a mesma marca de tempo.
- Preservar UTF-8, timestamp e nomenclatura dos arquivos.
- Assimetrias devem ir para o relatório, não para o CSV público.

## Testes

Validar cabeçalhos, ordem, linhas sem nota, zero válido, flags internas omitidas, `type` show/episode, escrita vazia, escrita parcial e geração do relatório.
