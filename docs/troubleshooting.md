# Troubleshooting — Banco de Séries -> Trakt Essentials

## `main` não encontrado

Atualize o código para a versão atual e execute `py -m py_compile bancodeseries_to_trakt_essentials.py`.

## Falha ao acessar o Banco de Séries

Verifique o PHPSESSID e a validade da sessão. Uma sessão expirada não é uma lista vazia.

## Falha definitiva na TMDb

Verifique:

- API key válida;
- endpoint v3 acessível;
- IMDb ID extraído corretamente;
- resposta JSON da TMDb.

A API v3 usa `api_key` como parâmetro de requisição. A credencial não deve aparecer em mensagens de erro.

## Dataset corrompido

Remova o dataset local afetado e execute novamente. O download deve ser atômico e validado.

## Episódios futuros

A ferramenta ignora episódios cuja `air_date` é futura ou vazia. Isso é intencional.

## Arquivos antigos

Verifique o timestamp do relatório e dos CSVs antes de comparar uma nova execução.

## Problema de console no Windows

A saída deve evitar caracteres incompatíveis com o terminal legado. Se necessário, use um terminal UTF-8.
