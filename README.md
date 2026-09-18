# Banco de Séries to Trakt Essentials

Um motor de extração, transformação e carga (ETL - *Extract, Transform, Load*) arquitetado para migrar históricos de consumo televisivo do portal Banco de Séries para arquivos de importação nativos do Trakt.tv. O sistema cruza os metadados locais com os bancos de dados do The Movie Database (TMDb) e Internet Movie Database (IMDb), mitigando latência de rede e assimetrias de versionamento.

## Arquitetura e Lógica Operacional

A extração opera em estágios autônomos projetados para garantir a integridade do histórico e evadir firewalls de aplicação (WAF - *Web Application Firewall*).

A indexação offline (*Zero-Network Data*) ocorre na inicialização. O script baixa os arquivos de despejo (*dumps*) oficiais do IMDb (`title.ratings.tsv.gz` e `title.episode.tsv.gz`) e constrói estruturas associativas (*Hash Maps*) diretamente na memória de acesso aleatório (RAM). Isso erradica o problema N+1, permitindo a localização de chaves primárias e notas em milissegundos sem disparar requisições web individuais para cada episódio.

O roteamento de consumo aplica regras assimétricas conforme a categoria da grade do usuário. Para obras nas listas "Ativas em dia" e "Finalizadas Completas", o motor injeta a diretiva de Confiança Absoluta, creditando o consumo integral sem auditar o histórico de marcações manuais. Para as listas "Ativas Atrasadas" e "Finalizadas Atrasadas", o algoritmo aciona uma auditoria estrita, varrendo a árvore de objetos do documento (*DOM - Document Object Model*) da página local para rastrear as marcações visuais parciais consolidadas sob o selo `darkchecked.png`.

Uma barreira temporal bloqueia a injeção de lixo de cadastro. O sistema cruza a data de transmissão original (`air_date`) fornecida pelo TMDb com a data do sistema operacional. Episódios com agendamento futuro são classificados como não lançados e sumariamente cortados do lote de exportação, independentemente da categoria da série ou do preenchimento incorreto no portal de origem.

Um duplo mecanismo de contingência (*Fallback*) repara identificadores descontinuados. Se o Banco de Séries fornecer uma chave matriz obsoleta, o roteador simula uma conexão ao portal do IMDb para interceptar redirecionamentos canônicos e, em caso de falha absoluta, executa uma busca semântica (*Semantic Search*) por aproximação textual na API do TMDb para ancorar o novo ID oficial de forma autônoma.

## Estrutura de Exportação

O importador do Trakt.tv exige separação estrita entre o registro de consumo e a qualificação da obra. Para contornar a sobrescrita acidental de histórico por diretivas de avaliações, o script divide a saída final em dois arquivos de valores separados por vírgula (CSV - *Comma-Separated Values*):

* `exportacao_history_YYYYMMDD_HHMMSS.csv`: Contém os IDs matrizes e fracionados destinados ao registro de visualização. O motor oculta a marcação estrutural da série inteira (`type: show`) em blocos com visualização parcial para impedir que o Trakt preencha lacunas e force os episódios não assistidos para 100%.
* `exportacao_ratings_YYYYMMDD_HHMMSS.csv`: Contém exclusivamente as obras e episódios que possuem métricas de nota validadas, direcionando a carga para o endpoint de avaliações sem corromper o log de visualização.

Um arquivo de texto puro (TXT) com o laudo de assimetrias de granularidade é gerado paralelamente para guiar as correções manuais de séries que divergem na contagem de capítulos entre as plataformas.

## Dependências e Instalação

O ambiente exige o interpretador Python instalado localmente e bibliotecas externas para o tratamento de conexões, raspagem de dados e renderização do painel de telemetria.

1. Clone este repositório para o disco local utilizando a interface de linha de comando (CLI - *Command Line Interface*) do Git.
2. Instale os pacotes requeridos executando `pip install -r requirements.txt` no terminal. Se o seu sistema retornar erro de comando não reconhecido (comum em ambientes Windows), force a instalação utilizando o Python Launcher nativo: `py -m pip install -r requirements.txt`.
3. Inicie o orquestrador executando `python bancodeseries_to_trakt_essentials.py` ou `py bancodeseries_to_trakt_essentials.py`.

Na primeira execução, o motor pausará para solicitar a inserção do `PHPSESSID` (capturado nos cookies de sessão do navegador ao autenticar no Banco de Séries) e a chave primária da API do TMDb v3. Estas credenciais serão gravadas em arquivos locais de texto plano para automatizar inicializações subsequentes, estando permanentemente isoladas pelas regras do `.gitignore` para mitigar vazamentos durante confirmações de versionamento (*commits*).