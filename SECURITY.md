# Security — Banco de Séries -> Trakt Essentials

## Credenciais

- `tmdb_api.txt` e `phpsessid.txt` são locais e ignorados pelo Git.
- Nunca reproduza o conteúdo dessas arquivos em logs, relatórios, issues ou respostas.
- Credenciais são solicitadas por prompt interativo e gravadas apenas em arquivos locais ignorados.
- O isolamento das credenciais é feito pelo `.gitignore` e pela ausência de leitura dessas arquivos em testes.

## Artefatos

CSVs, relatórios, datasets, temporários `.part` e caches não devem ser versionados.

## Erros

Mensagens de erro não devem incluir URLs completas com `api_key`, cookies ou conteúdo de sessão.

## Dados pessoais

Nomes reais de usuário, IDs de sessão e histórico pessoal não devem entrar em documentação ou testes públicos.

## Importação

A ferramenta não importa arquivos no Trakt. A exportação é local e a importação é uma ação manual do usuário.
