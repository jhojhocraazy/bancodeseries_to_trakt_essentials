# Arquitetura — Banco de Séries -> Trakt Essentials

## Objetivo

A aplicação é uma CLI local de exportação. Ela lê o histórico de uma conta do Banco de Séries, resolve identidades no IMDb/TMDb, aplica as regras de consumo das quatro grades e grava CSV e relatório local.

A aplicação não autentica no Trakt e não importa arquivos.

## Módulos

```text
bancodeseries_to_trakt_essentials.py  -> CLI, extração, regras de consumo e orquestração
tmdb_client.py                        -> cliente TMDb v3, timeouts e respostas
identity_matching.py                 -> normalização de títulos e auditoria de fallback
exporters.py                         -> contratos de colunas e escrita atômica de CSV
```

## Fluxo

```text
credenciais locais
-> sessão HTTP
-> grades do Banco de Séries
-> página de cada série
-> IMDb ID
-> TMDb v3
-> fallback auditado
-> regra de consumo
-> filtro de episódios futuros
-> registros intermediários
-> History/Ratings atômicos
-> relatório
```

## Responsabilidades atuais

- `bancodeseries_to_trakt_essentials.py`: CLI, extração, integração, processamento e orquestração.
- `agents/`: contratos documentais das áreas especializadas.
- `tests/`: caracterização e regressão offline.

## Regras invariantes

- quatro categorias de grades;
- confiança absoluta para grades em dia/completas;
- auditoria de `darkchecked.png` para grades atrasadas;
- episódios futuros nunca são publicados;
- History e Ratings permanecem separados;
- IDs e campos internos não são expostos indevidamente;
- a camada de exportação não consulta a rede;
- credenciais permanecem locais e não aparecem em logs.

## Evolução futura

A separação em módulos deve ocorrer somente após testes de caracterização, preservando as assinaturas e os contratos públicos.
