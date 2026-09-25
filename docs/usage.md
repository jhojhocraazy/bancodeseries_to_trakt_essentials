# Uso — Banco de Séries -> Trakt Essentials

## Requisitos

- Python instalado;
- dependências de `requirements.txt`;
- API key TMDb v3;
- PHPSESSID válido de uma conta Banco de Séries.

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
