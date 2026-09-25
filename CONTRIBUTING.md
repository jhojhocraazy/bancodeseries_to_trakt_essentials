# Contribuindo

## Antes de alterar

Leia `AGENT.md`, os agente relevantes e `docs/export-contracts.md`.

## Regras

- preserve os contratos History e Ratings;
- preserve a ordem das colunas;
- não publique credenciais;
- não adicione dependência sem necessidade;
- não altere timeouts, retries e intervalos sem justificativa;
- não transforme falhas parciais em sucesso;
- adicione testes offline para cada mudança de parsing, identidade, integração ou exportação.

## Validação local

```text
py -m py_compile bancodeseries_to_trakt_essentials.py
py -m unittest discover -s tests -v
```

Não declarar testes, cobertura ou benchmark não executados.
