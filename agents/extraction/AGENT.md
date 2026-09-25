# Agente de Extração

## Responsabilidade

Extrair do Banco de Séries as grades, séries e marcações de episódios sem depender de estrutura frágil além dos seletores já suportados.

## Escopo

- `extrair_todas_grades()`.
- `extrair_dados_serie_bds()`.
- Expressões regulares e `BeautifulSoup` usados para `serieid`, IMDb ID, temporadas e `darkchecked.png`.
- Dados de categoria, título e episódios assistidos.

## Regras

- Preservar as quatro categorias: Ativas em dia, Finalizadas Completas, Ativas Atrasadas e Finalizadas Atrasadas.
- Não tratar `serieid` como ID IMDb ou TMDb.
- Não aceitar títulos vazios, links de navegação ou duplicatas como séries válidas.
- A auditoria de histórico só deve ser aplicada às grades atrasadas.
- `darkchecked.png` é indicador de marcação parcial; não representa confiança absoluta.
- Parsing deve preservar IDs como strings quando o contrato assim exigir.
- Falhas de uma série não devem apagar resultados já processados.
- Não registrar PHPSESSID, conteúdo de sessão ou dados pessoais.

## Testes

Validar cada categoria, duplicatas, link sem `serieid`, página sem IMDb ID, temporadas inválidas, episódios marcados e respostas HTTP simuladas.

## Critérios

O parser deve produzir apenas dados estruturados necessários ao fluxo do ETL e deve falhar de forma explícita quando a estrutura esperada não estiver disponível.
