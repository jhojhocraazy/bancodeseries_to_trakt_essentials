# Agente de Resiliência

## Responsabilidade

Manter o comportamento previsível diante de WAF, falhas temporárias, paginação, downloads interrompidos e IDs desatualizados.

## Escopo

- Retentativas da sessão HTTP.
- Tratamento de HTTP 429 e 5xx.
- WAF e timeouts.
- Downloads dos arquivos IMDb.
- Recuperação de falhas por série e por execução.
- Redirecionamentos e fallback.

## Regras

- Preservar os limites e backoff existentes, salvo pedido explícito.
- Não transformar exceção de uma obra em motivo para abortar todo o lote.
- Não mascarar falha de autenticação como lista vazia.
- Não publicar CSV parcial quando a coleta ou a escrita falhar.
- Intervalo entre acessos deve ser mantido ou justificado por benchmark.
- Falhas de rede não devem ser descritas como sucesso.
- Não implementar evasão de WAF que exceda os limites técnicos e éticos já definidos pelo projeto.

## Testes

Validar retry, backoff, HTTP 429, 500, timeout, resposta sem JSON, download parcial, sessão expirada e retomada segura.
