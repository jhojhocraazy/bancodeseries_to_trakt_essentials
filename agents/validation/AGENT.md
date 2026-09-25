# Agente de Validação e Testes

## Responsabilidade

Criar validações reproduzíveis para parsing, identidade, integrações, resiliência, performance, exportação e UX sem acessar dados reais por padrão.

## Estratégia

- Usar `unittest` na pasta `tests/`.
- Simular respostas HTTP e respostas HTML representativas.
- Isolar datasets e chamadas de rede.
- Não ler `tmdb_api.txt` ou `phpsessid.txt` em testes.
- Não usar nomes reais de usuário.

## Cenários obrigatórios

- Parsing das quatro categorias e `darkchecked.png`.
- ID inexistente, redirecionamento e fallback.
- Episódio futuro e data vazia.
- Nota ausente, nota zero e nota válida.
- History sem nota e Ratings com nota.
- `type` show e episode.
- Assimetria entre IMDb e TMDb.
- HTTP 429, 5xx, timeout e JSON inválido.
- Cancelamento, menu, ajuda e entrada inválida.

## Comandos

```text
py -m py_compile bancodeseries_to_trakt_essentials.py
py -m unittest discover -s tests -v
```

Não declarar quantidade de testes, cobertura ou benchmark sem executar o comando correspondente.
