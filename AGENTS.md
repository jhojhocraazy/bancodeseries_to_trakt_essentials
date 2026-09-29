# Agente do Projeto Banco de Séries → Trakt

## Responsabilidade

Manter o ETL que lê o histórico público/account-level do Banco de Séries, resolve séries e episódios no IMDb/TMDb, aplica as regras de consumo do usuário e gera arquivos CSV compatíveis com o Trakt.

## Escopo

- `bancodeseries_to_trakt_essentials.py`: CLI e orquestração do ETL.
- `agents/`: instruções documentais dos agentes especializados.
- `README.md`: instalação, operação e visão arquitetural.
- `requirements.txt`: dependências externas.
- `.gitignore`: proteção de credenciais, datasets e artefatos gerados.
- Artefatos locais ignorados: `tmdb_api.txt`, `phpsessid.txt`, `*.csv`, `relatorio_execucao_*.txt` e `*.gz`.

## Arquitetura atual

A aplicação é uma CLI predominantemente procedural, concentrada no módulo principal. O fluxo atual é:

1. carregar credenciais locais;
2. baixar, quando ausentes, `title.ratings.tsv.gz` e `title.episode.tsv.gz` do IMDb;
3. indexar notas e relações série/temporada/episódio em memória;
4. autenticar no Banco de Séries usando `PHPSESSID`;
5. extrair as quatro grades do usuário;
6. extrair o IMDb ID e, nas grades atrasadas, os episódios marcados;
7. resolver a série e suas temporadas no TMDb;
8. usar redirecionamento do IMDb e busca no TMDb como fallback;
9. ignorar episódios com data futura;
10. exportar History e Ratings separadamente;
11. gerar relatório operacional.

## Agentes especializados

- `agents/extraction/`: parsing do Banco de Séries e das grades.
- `agents/identity/`: IDs, fallback e auditoria de correspondência.
- `agents/integrations/`: IMDb, TMDb, sessão HTTP e credenciais.
- `agents/resilience/`: WAF, erros, retentativas, paginação e downloads.
- `agents/performance/`: índices em RAM, cache, tempo e memória.
- `agents/export/`: CSV History, CSV Ratings e relatório.
- `agents/validation/`: testes offline e critérios de regressão.
- `agents/ux/`: menu, mensagens, confirmação, credenciais e terminal.

## Contratos de exportação a preservar

- `exportacao_history_<timestamp>.csv` usa `imdb_id`, `tmdb_id`, `type` e não deve receber coluna de nota.
- `exportacao_ratings_<timestamp>.csv` usa `imdb_id`, `tmdb_id`, `type`, `rating` e contém somente linhas com nota disponível.
- History e Ratings são arquivos separados; Ratings não substitui History.
- Séries completas e grades em dia usam confiança absoluta; grades atrasadas usam a auditoria de `darkchecked.png`.
- Episódios futuros nunca devem ser exportados como assistidos.
- A identificação da origem de uma nota, flags internas e campos de diagnóstico não devem vazar para o CSV público.

## Segurança

- Nunca reproduzir `tmdb_api.txt` ou `phpsessid.txt` em código, documentação, logs, commits ou respostas.
- Preservar esses arquivos e os datasets/artefatos gerados sob o `.gitignore`.
- Não registrar a API key, o cookie de sessão ou URLs contendo credenciais.
- Não usar nomes reais de usuário em documentação ou testes públicos.
- Não executar testes offline com rede ou credenciais reais.

## Regras de manutenção

- Alterar somente o necessário para a solicitação aprovada.
- Preservar o contrato dos dois CSVs e a ordem das colunas.
- Preservar o filtro de episódios futuros.
- Não misturar parsing, identidade, nota e exportação.
- Fallback deve ser auditado; não aceitar o primeiro resultado textual sem validação.
- Manter timeouts, intervalos, número de tentativas e limites existentes, salvo pedido explícito.
- Não introduzir frameworks, bancos, dependências ou infraestrutura sem necessidade aprovada.
- Não declarar testes, cobertura ou benchmarks não executados.
- Após mudanças, executar os testes relevantes e, quando possível:

```text
py -m py_compile bancodeseries_to_trakt_essentials.py
py -m unittest discover -s tests -v
```

## Critérios de conclusão

- A mudança atende ao objetivo sem expor credenciais ou dados pessoais.
- O parsing continua compatível com os seletores atuais.
- IDs e fallback continuam submetidos à validação.
- Episódios futuros continuam ignorados.
- History e Ratings permanecem separados e com os cabeçalhos corretos.
- Falhas não deixam arquivos parciais.
- Testes e validações executados são relacionados na resposta final.
