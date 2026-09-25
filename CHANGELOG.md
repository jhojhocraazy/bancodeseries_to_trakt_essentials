# Changelog

## Não publicado

- Modularização inicial em `tmdb_client.py`, `identity_matching.py` e `exporters.py`.
- Prompt de credencial alinhado ao padrão `jhojhocraazy` com `input()` visível.
- Instruções para obter o `PHPSESSID` no README e em `docs/usage.md`.
- Testes reorganizados por área conforme a família de projetos.

- Entry point `main()` restaurado e coberto por teste de bootstrap.
- Progresso por série no formato `[1/46]`.
- Autenticação TMDb v3 corrigida com `api_key` via parâmetros.
- Erros sanitizados para não expor credenciais.
- Downloads IMDb atômicos e gzip validados.
- History e Ratings escritos atomicamente.
- Nota válida `0.0` preservada em Ratings.
- Credenciais solicitadas com entrada mascarada.
- Documentação de arquitetura, contratos, uso, segurança e troubleshooting.
