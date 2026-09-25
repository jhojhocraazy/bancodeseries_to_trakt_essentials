# Agente de Identidade e Confiança

## Responsabilidade

Garantir que séries, temporadas e episódios exportados correspondam às obras corretas e que decisões de fallback não sejam aceitas cegamente.

## Escopo

- IMDb ID matriz extraído do Banco de Séries.
- Resolução de séries e episódios no TMDb.
- `resolver_redirecionamento_imdb()`.
- `buscar_fallback_tmdb()`.
- Regras de confiança absoluta e auditoria das grades atrasadas.

## Regras

- Não aceitar ID apenas porque apareceu em HTML ou URL.
- Validar que a série é uma série, e não um filme, quando o contrato exigir.
- Preservar a relação temporada → episódio do IMDb.
- Um ID legado só pode ser substituído após redirecionamento ou fallback validado.
- A busca textual não deve escolher automaticamente o primeiro resultado sem verificar título, ano e ID externo quando esses dados estiverem disponíveis.
- Confiança absoluta significa crédito do consumo da categoria, não autorização para exportar episódios futuros.
- Divergências entre IMDb e TMDb devem ser registradas como assimetria, não escondidas.
- Identidade não deve decidir nomes de arquivos nem regras de nota.

## Testes

Validar título exato e aproximado, série homônima, ID inexistente, redirecionamento, fallback, temporada ausente, episódio com número inválido, assimetria e rejeição de resultados fracos.
