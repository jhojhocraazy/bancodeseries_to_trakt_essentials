# Banco de Séries to Trakt Essentials

Ferramenta de linha de comando para transformar o histórico de séries do Banco de Séries em arquivos CSV compatíveis com o Trakt.

O programa lê as grades da conta, resolve a identidade das séries e episódios no IMDb/TMDb, aplica as regras de consumo de cada categoria e gera History e Ratings localmente. A importação para o Trakt é manual.

## O que você pode exportar

| Categoria | Regra de consumo | History | Ratings |
| --- | --- | --- | --- |
| Ativas em dia | Confiança absoluta: toda série é considerada assistida | `imdb_id, tmdb_id, type` | Somente linhas com nota |
| Finalizadas Completas | Confiança absoluta: toda série é considerada assistida | `imdb_id, tmdb_id, type` | Somente linhas com nota |
| Ativas Atrasadas | Auditoria de `darkchecked.png` | Apenas episódios confirmados | Somente linhas com nota |
| Finalizadas Atrasadas | Auditoria de `darkchecked.png` | Apenas episódios confirmados | Somente linhas com nota |
| Todas as categorias | Regras aplicadas por categoria | Conforme a categoria | Conforme a categoria |

Em todas as categorias, episódios com data futura ou sem data nunca são exportados como assistidos.

O relatório de execução é o formato indicado para conferir séries, temporadas, episódios ignorados e assimetrias entre IMDb e TMDb.

## Requisitos

- Python 3.10 ou mais recente;
- acesso à internet na execução real;
- uma chave da API TMDb v3;
- um PHPSESSID válido de uma conta Banco de Séries;
- uma conta de teste própria, se for realizar uma validação controlada.

As credenciais são solicitadas na primeira execução e salvas localmente em `tmdb_api.txt` e `phpsessid.txt`. Esses arquivos são ignorados pelo Git e nunca devem ser enviados ao repositório.

## Instalação no Windows

### 1. Escolha uma pasta para o projeto

Abra o PowerShell e escolha uma pasta dedicada:

```powershell
$Projeto = "$HOME\MeusProjetos\bancodeseries_to_trakt_essentials"
New-Item -ItemType Directory -Path $Projeto
Set-Location $Projeto
```

Evite escolher uma pasta que contenha outros projetos ou arquivos importantes.

### 2. Obtenha o projeto

```powershell
git clone https://github.com/jhojhocraazy/bancodeseries_to_trakt_essentials.git .
```

Confirme os arquivos principais:

```powershell
Test-Path requirements.txt
Test-Path bancodeseries_to_trakt_essentials.py
```

Os dois comandos devem retornar `True`.

### 3. Crie o ambiente virtual

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se a ativação for bloqueada pelo PowerShell, use o interpretador do ambiente diretamente:

```powershell
.\.venv\Scripts\python.exe
```

### 4. Instale as dependências

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se a ativação não estiver disponível:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5. Confirme a instalação

```powershell
python -m pip check
python -m unittest discover -s tests -v
```

O primeiro comando não deve relatar dependências quebradas. O segundo deve terminar com `OK`.

## Como executar

```powershell
python bancodeseries_to_trakt_essentials.py
```

Ou, sem ativação:

```powershell
.\.venv\Scripts\python.exe bancodeseries_to_trakt_essentials.py
```

O menu usa esta ordem:

1. escolha uma categoria;
2. confira as colunas e as regras;
3. confirme a operação;
4. aguarde o processamento com o progresso por série;
5. verifique o relatório e os arquivos gerados.

Para sair, escolha `0`. A ajuda pode ser aberta com `H` e não inicia uma exportação.

## Regras das categorias

- **Ativas em dia:** toda série é considerada assistida, exceto episódios futuros.
- **Finalizadas Completas:** toda série é considerada assistida, exceto episódios futuros.
- **Ativas Atrasadas:** somente episódios confirmados por `darkchecked.png` são exportados.
- **Finalizadas Atrasadas:** somente episódios confirmados por `darkchecked.png` são exportados.

Em grades atrasadas, a linha da série não entra no History para evitar que a plataforma de destino preencha episódios não assistidos.

## Arquivos gerados

Os arquivos são gravados na pasta de trabalho atual.

- `exportacao_history_<timestamp>.csv`
- `exportacao_ratings_<timestamp>.csv`
- `relatorio_execucao_<timestamp>.txt`

History mantém o cabeçalho `imdb_id,tmdb_id,type` e Ratings mantém `imdb_id,tmdb_id,type,rating`. Zero é uma nota válida e é preservado; ausência de nota permanece vazia.

## Como funciona, em linguagem simples

1. O programa lê as quatro grades da conta Banco de Séries.
2. Para cada série, extrai o IMDb ID e as marcações parciais quando a categoria exige auditoria.
3. O ID é resolvido no TMDb v3, com redirecionamento do IMDb e busca textual como contingência.
4. Os dumps públicos do IMDb são indexados em memória para evitar uma requisição por episódio.
5. O filtro de data impede que episódios futuros sejam exportados.
6. As linhas History e Ratings são escritas de forma atômica em arquivos separados.

## Segurança e privacidade

- `tmdb_api.txt` e `phpsessid.txt` são locais e ignorados pelo Git.
- Credenciais são solicitadas por prompt interativo e salvas somente em arquivos locais ignorados pelo Git.
- Erros de rede não imprimem URLs com a chave da TMDb.
- CSVs, relatórios, datasets e temporários são ignorados pelo Git.
- Não coloque API keys, exports ou relatórios em issues públicas.
- O índice do IMDb é mantido em memória durante a execução.

Leia também [SECURITY.md](SECURITY.md).

## Testes e desenvolvimento

A suíte é offline e usa `unittest`:

```powershell
python -m unittest discover -s tests -v
```

Compilação do módulo principal:

```powershell
python -m py_compile bancodeseries_to_trakt_essentials.py
```

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para o processo de alteração e [CHANGELOG.md](CHANGELOG.md) para o histórico da versão.

## Limitações

- O acesso depende da disponibilidade e do HTML do Banco de Séries, da TMDb e do IMDb.
- Mudanças no layout do portal podem exigir atualização do parser.
- O dataset do IMDb ocupa memória durante a execução.
- O fallback textual não elimina toda ambiguidade de títulos homônimos.
- A correspondência nunca deve ser interpretada como prova absoluta; consulte o relatório.
- O programa não importa arquivos no Trakt; a importação é manual.

## Documentação adicional

- [docs/usage.md](docs/usage.md): passo a passo para usuários;
- [docs/export-contracts.md](docs/export-contracts.md): colunas e regras dos CSV;
- [docs/architecture.md](docs/architecture.md): organização interna;
- [docs/troubleshooting.md](docs/troubleshooting.md): solução de problemas;
- `agents/`: instruções de manutenção e responsabilidades das áreas do projeto.

## Licença

Projeto sob a licença MIT. Consulte [LICENSE](LICENSE).
