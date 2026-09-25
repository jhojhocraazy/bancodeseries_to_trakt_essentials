# Uso — Banco de Séries -> Trakt Essentials

## Requisitos

- Python instalado;
- dependências de `requirements.txt`;
- API key TMDb v3;
- PHPSESSID válido de uma conta Banco de Séries.

## Como obter o PHPSESSID

O `PHPSESSID` é o cookie de sessão da sua conta Banco de Séries. Ele não é sua senha e não deve ser compartilhado.

1. Abra o site `bancodeseries.com.br` no navegador e faça login na sua conta.
2. Abra as ferramentas do desenvolvedor do navegador:
   - Chrome/Edge: `F12` ou `Ctrl+Shift+I`;
   - Firefox: `F12`.
3. Vá até a aba **Application** (Chrome/Edge) ou **Storage** (Firefox).
4. Em **Cookies**, selecione o domínio `bancodeseries.com.br`.
5. Localize a entrada `PHPSESSID` e copie o **valor** do cookie.
6. Cole esse valor quando o programa solicitar a credencial.

Cuidados:

- não copie o atributo `HttpOnly` ou outras colunas, apenas o valor do cookie;
- não envie o valor para ninguém, nem para issues ou suporte;
- não coloque o valor em arquivos versionados;
- o arquivo `phpsessid.txt` é ignorado pelo Git;
- a sessão expira; nesse caso, repita o procedimento após fazer login novamente.

## Execução

```powershell
py bancodeseries_to_trakt_essentials.py
```

## Menu

- `1`: Ativas em dia
- `2`: Finalizadas Completas
- `3`: Ativas Atrasadas
- `4`: Finalizadas Atrasadas
- `5`: Todas as categorias
- `6`: Documentação
- `0`: Sair

O progresso é exibido como:

```text
[1/46] Processando: Nome da série
```

## Arquivos gerados

- `exportacao_history_<timestamp>.csv`
- `exportacao_ratings_<timestamp>.csv`
- `relatorio_execucao_<timestamp>.txt`

A importação para o Trakt é manual e ocorre somente após a conferência dos arquivos.
