# Agente de UX e Fluxo de Interação

## Responsabilidade

Manter o menu, as mensagens, a entrada do usuário e a credenciais do ETL claros, seguros e consistentes.

## Escopo

- `exibir_menu_e_obter_selecao()`.
- `exibir_documentacao()`.
- `carregar_credencial()`.
- `limpar_tela()`.
- Mensagens de progresso e relatório final.

## Regras

- O menu deve manter as quatro categorias, a opção todas, a documentação e a saída.
- Entrada inválida deve manter o usuário na etapa atual.
- `0` deve encerrar sem produzir saída.
- A documentação deve retornar ao menu.
- Credenciais devem ser solicitadas uma vez e armazenadas somente nos arquivos locais ignorados.
- Nunca exibir o valor da API key, do PHPSESSID ou conteúdo completo do cookie.
- Falhas de limpeza de tela não devem impedir a operação.
- Mensagens devem distinguir falha, ignorado, sem nota e assistido.

## Testes

Simular entradas do menu, opção inválida, saída, ajuda, cancelamento, credencial ausente/vazia e falhas de `input()`.
