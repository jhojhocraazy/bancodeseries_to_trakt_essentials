# Agente de Performance

## Responsabilidade

Reduzir trabalho redundante sem alterar decisões de identidade, consumo ou exportação.

## Escopo

- Índices `ratings_dict` e `imdb_struct` em memória.
- Downloads e cache local dos datasets IMDb.
- Tempo entre requisições.
- Processamento por série, temporada e episódio.
- Consumo de RAM e tamanho dos dumps.

## Regras

- Preservar o uso dos dumps para evitar N+1.
- Não persistir índices de RAM sem necessidade aprovada.
- Não aumentar concorrência ou eliminar intervalos apenas por optimização.
- Medir antes de alterar timeouts, retries, delays ou limites.
- Cache não pode cruzar contratos diferentes sem validação.
- Otimização não pode alterar IDs, status de assistido ou filtros temporais.
- Não trocar `csv.DictWriter` por caminho que quebre ordem, UTF-8 ou cabeçalhos.

## Testes

Validar que o dataset é reutilizado, que a estrutura de episódios é indexada corretamente e que a otimização mantém os mesmos resultados do fluxo original.
