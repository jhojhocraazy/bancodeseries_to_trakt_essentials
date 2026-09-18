import os
import csv
import gzip
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from bs4 import BeautifulSoup
except ImportError:
    print("Dependências ausentes. Execute: py -m pip install requests beautifulsoup4 rich")
    sys.exit(1)

console = Console()
BASE_URL = "https://bancodeseries.com.br"
RATINGS_FILE = Path("title.ratings.tsv.gz")
EPISODES_FILE = Path("title.episode.tsv.gz")
TMDB_API_KEY = ""

def limpar_tela():
    """Limpa a tela do terminal independentemente do sistema operacional (Windows/Linux/Mac)."""
    os.system('cls' if os.name == 'nt' else 'clear')

def carregar_credencial(nome_arquivo, prompt_msg):
    """
    Tenta ler uma credencial (API Key ou Sessão) de um arquivo de texto local.
    Por que: Evita que o usuário precise digitar tokens gigantes a cada execução.
    Se o arquivo não existir, solicita via input e o cria automaticamente para as próximas vezes.
    """
    caminho = Path(nome_arquivo)
    if caminho.exists():
        valor = caminho.read_text(encoding="utf-8").strip()
        if valor:
            return valor
    
    console.print(f"[yellow]{nome_arquivo} não encontrado ou vazio.[/yellow]")
    valor = input(f"{prompt_msg}: ").strip()
    caminho.write_text(valor, encoding="utf-8")
    console.print(f"[green]Credencial salva em {nome_arquivo} para execuções futuras.[/green]\n")
    return valor

def carregar_datasets_imdb():
    """
    Baixa e indexa os arquivos oficiais do IMDb diretamente na memória RAM.
    Por que: 
    1. Evita o problema N+1 no TMDb (fazer uma requisição web para cada episódio para descobrir o ID).
    2. Burla o WAF (Firewall) da Amazon, não acessando as páginas HTML deles.
    3. Tempo de descoberta do ID cai de ~1 segundo pela rede para 0.001ms na RAM.
    """
    url_ratings = "https://datasets.imdbws.com/title.ratings.tsv.gz"
    url_episodes = "https://datasets.imdbws.com/title.episode.tsv.gz"
    
    if not RATINGS_FILE.exists():
        console.print("[cyan]Baixando base de notas oficial do IMDb (~30MB)...[/cyan]")
        resp = requests.get(url_ratings, stream=True, timeout=60)
        resp.raise_for_status()
        with open(RATINGS_FILE, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
                
    if not EPISODES_FILE.exists():
        console.print("[cyan]Baixando topologia oficial do IMDb (~30MB)...[/cyan]")
        resp = requests.get(url_episodes, stream=True, timeout=60)
        resp.raise_for_status()
        with open(EPISODES_FILE, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)

    ratings_dict = {}
    imdb_struct = {}
    
    console.print("[cyan]Indexando datasets do IMDb na RAM...[/cyan]")
    try:
        with gzip.open(RATINGS_FILE, "rt", encoding="utf-8") as f:
            next(f)
            for linha in f:
                partes = linha.strip().split("\t")
                if len(partes) == 3:
                    ratings_dict[partes[0]] = {"rating": float(partes[1]), "votes": int(partes[2])}
                    
        with gzip.open(EPISODES_FILE, "rt", encoding="utf-8") as f:
            next(f)
            for linha in f:
                partes = linha.strip("\n").split("\t")
                if len(partes) == 4:
                    tconst, parent_id, season, episode = partes
                    if season in ('\\N', '0') or episode in ('\\N', '0'): continue
                    try:
                        s_int = int(season)
                        ep_int = int(episode)
                        if parent_id not in imdb_struct: imdb_struct[parent_id] = {}
                        if s_int not in imdb_struct[parent_id]: imdb_struct[parent_id][s_int] = {}
                        
                        imdb_struct[parent_id][s_int][ep_int] = tconst
                    except ValueError: pass
                    
        console.print(f"[green]Índices construídos: {len(ratings_dict):,} notas e {len(imdb_struct):,} séries mapeadas na RAM.[/green]\n")
    except Exception as e:
        console.print(f"[bold red]Erro crítico ao compilar matrizes offline: {e}[/bold red]")
        sys.exit(1)
        
    return ratings_dict, imdb_struct

def extrair_todas_grades(sessao):
    """
    Acessa a página principal do usuário no Banco de Séries e mapeia todas as categorias.
    Por que: Isola e cataloga os IDs internos de cada série por status, utilizando Regex.
    """
    url = f"{BASE_URL}/index.php?action=mygrade"
    resposta = sessao.get(url, timeout=30)
    resposta.raise_for_status()
    
    categorias = {
        "Ativas em dia": r"<b>Ativas em dia.*?(<small>.*?</small>)",
        "Finalizadas Completas": r"<b>Finalizadas Completas.*?</b><br>\s*<small>(.*?)</small>",
        "Ativas Atrasadas": r"<b>Ativas Atrasadas.*?</b><br>(.*?)<br><b>",
        "Finalizadas Atrasadas": r"<b>Finalizadas Atrasadas.*?</b><br>(.*?)<br><b>"
    }
    
    grades = {}
    for nome, regex in categorias.items():
        match_bloco = re.search(regex, resposta.text, re.DOTALL | re.IGNORECASE)
        series = []
        if match_bloco:
            sopa = BeautifulSoup(match_bloco.group(1), "html.parser")
            links = sopa.find_all("a", href=re.compile(r"serieid=(\d+)"))
            vistos = set()
            for link in links:
                match_id = re.search(r"serieid=(\d+)", link["href"])
                titulo = link.get_text(strip=True)
                if match_id and titulo and not titulo.startswith("("):
                    serie_id = match_id.group(1)
                    if serie_id not in vistos:
                        vistos.add(serie_id)
                        series.append({"id": serie_id, "nome": titulo, "categoria": nome})
        grades[nome] = series
    return grades

def extrair_dados_serie_bds(sessao, serie_id, rastrear_historico):
    """
    Visita a página individual da série no Banco de Séries para resgatar o IMDb ID matriz e, 
    se necessário, mapear os episódios fracionados que foram assistidos (darkchecked).
    """
    url = f"{BASE_URL}/index.php?action=ss&serieid={serie_id}"
    resposta = sessao.get(url, timeout=30)
    resposta.raise_for_status()
    sopa = BeautifulSoup(resposta.text, "html.parser")
    
    imdb_id = ""
    link_imdb = sopa.find("a", href=re.compile(r"imdb\.com/title/(tt\d+)"))
    if link_imdb: imdb_id = re.search(r"(tt\d+)", link_imdb["href"]).group(1)
        
    episodios_assistidos = set()
    if rastrear_historico:
        for painel in sopa.find_all("div", class_=lambda c: c and "panel-seasons" in c):
            div_rate = painel.find("div", class_="rate")
            temporada = div_rate.get("data-season", "") if div_rate else ""
            if not temporada or int(temporada) == 0: continue
            
            if painel.find("img", src=re.compile(r"darkchecked\.png")):
                tag_b = painel.find("b")
                if tag_b:
                    match_ep = re.search(r"(\d+)\s*-", tag_b.get_text())
                    if match_ep:
                        episodios_assistidos.add((int(temporada), int(match_ep.group(1))))
                        
    return imdb_id, episodios_assistidos

def buscar_estrutura_tmdb(sessao, imdb_id):
    """
    Consulta o TMDb usando o IMDb ID. Obtém a contagem de temporadas e itera para extrair
    os metadados de cada episódio, incluindo a data de exibição (air_date) para o filtro temporal.
    """
    url_find = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={TMDB_API_KEY}&external_source=imdb_id"
    res = sessao.get(url_find, timeout=15).json().get("tv_results", [])
    if not res: return None, {}
        
    tmdb_id = str(res[0]["id"])
    total_temporadas = sessao.get(f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_API_KEY}", timeout=15).json().get("number_of_seasons", 0)
    
    hoje = datetime.now().strftime("%Y-%m-%d")
    tmdb_struct = {}
    
    for s in range(1, total_temporadas + 1):
        resp_season = sessao.get(f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s}?api_key={TMDB_API_KEY}", timeout=15)
        if resp_season.status_code == 200:
            tmdb_struct[s] = []
            for ep in resp_season.json().get("episodes", []):
                ep_num = ep.get("episode_number")
                if ep_num == 0: continue
                
                air_date = ep.get("air_date")
                lancado = bool(air_date and air_date <= hoje)
                
                tmdb_struct[s].append({
                    "episode": ep_num,
                    "tmdb_id": ep.get("id"),
                    "air_date": air_date,
                    "lancado": lancado
                })
    return tmdb_id, tmdb_struct

def resolver_redirecionamento_imdb(imdb_id):
    """
    Mecanismo de Contingência 1: Bate na URL da Amazon para verificar redirecionamentos silenciosos de chaves antigas.
    """
    url = f"https://www.imdb.com/title/{imdb_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "close"
    }
    try:
        resposta = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resposta.status_code == 200:
            match_url = re.search(r"(tt\d+)", resposta.url)
            if match_url and match_url.group(1) != imdb_id: return match_url.group(1)
            tag = BeautifulSoup(resposta.text, "html.parser").find("link", rel="canonical")
            if tag and "href" in tag.attrs:
                match = re.search(r"(tt\d+)", tag["href"])
                if match and match.group(1) != imdb_id: return match.group(1)
    except: pass
    return imdb_id

def buscar_fallback_tmdb(sessao, nome_serie):
    """
    Mecanismo de Contingência 2: Se o ID do IMDb estiver irremediavelmente morto, faz uma busca textual
    aproximada (Semantic Search) na API do TMDb e resgata o ID Externo da obra encontrada.
    """
    query = requests.utils.quote(re.sub(r"\(.*?\)", "", nome_serie).strip())
    try:
        res = sessao.get(f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={query}", timeout=15).json().get("results", [])
        if res:
            resp_ext = sessao.get(f"https://api.themoviedb.org/3/tv/{str(res[0]['id'])}/external_ids?api_key={TMDB_API_KEY}", timeout=15)
            if resp_ext.status_code == 200: return resp_ext.json().get("imdb_id")
    except: pass
    return None

def processar_bloco(sessao, obras, regras_confianca, ratings_dict, imdb_struct_db, linhas_csv):
    """
    O motor principal de Extração, Transformação e Carga (ETL). 
    Gere o fluxo entre os metadados do BDS, a indexação offline e o espelhamento da grade do TMDb.
    """
    metricas_bloco = {
        "series": 0, "temporadas": 0, "episodios_mapeados": 0,
        "episodios_ignorados": 0, "episodios_assistidos": 0, "assimetrias": []
    }

    for obra in obras:
        try:
            time.sleep(2.5)
            console.print(f"\n[bold magenta]---[/bold magenta]")
            console.print(f"Série: [bold white]{obra['nome']}[/bold white]")
            console.print(f"Categoria: {obra['categoria']}")
            
            rastrear_historico = not regras_confianca
            imdb_id_bds, ep_vistos = extrair_dados_serie_bds(sessao, obra["id"], rastrear_historico)
            
            if not imdb_id_bds:
                console.print("[red]Falha: IMDb ID matriz não encontrado no BDS.[/red]")
                continue
            
            imdb_id = imdb_id_bds
            metricas_bloco["series"] += 1
            
            tmdb_id, tmdb_struct = buscar_estrutura_tmdb(sessao, imdb_id)
            if not tmdb_id:
                novo_imdb = resolver_redirecionamento_imdb(imdb_id)
                if novo_imdb == imdb_id: 
                    novo_imdb = buscar_fallback_tmdb(sessao, obra["nome"])
                if novo_imdb and novo_imdb != imdb_id:
                    imdb_id = novo_imdb
                    tmdb_id, tmdb_struct = buscar_estrutura_tmdb(sessao, imdb_id)
            
            if not tmdb_id:
                console.print("[red]Falha definitiva: Série não localizada na API do TMDb.[/red]")
                continue

            r_info = ratings_dict.get(imdb_id)
            nota_matriz = f"[bold yellow]{r_info['rating']}[/bold yellow] ({r_info['votes']:,} votos)" if r_info else "[dim]Não encontrada[/dim]"
            
            if imdb_id != imdb_id_bds:
                console.print(f"[dim]ID Legado BDS: {imdb_id_bds} → Corrigido pelo Fallback[/dim]")
                
            console.print(f"IMDb ID Matriz: {imdb_id} | Nota: {nota_matriz}\n")
            
            # Ancoragem da série principal (Show) com a flag de retenção para blocos atrasados
            linhas_csv.append({
                "imdb_id": imdb_id,
                "tmdb_id": tmdb_id,
                "type": "show",
                "rating": r_info['rating'] if r_info else "",
                "ignorar_no_historico": not regras_confianca
            })

            vol_imdb_local = imdb_struct_db.get(imdb_id, {})
            assimetria = False
            relatorio_assimetria = []
            
            for s in sorted(set(vol_imdb_local.keys()).union(set(tmdb_struct.keys()))):
                vol_imdb = len(vol_imdb_local.get(s, {}))
                vol_tmdb = len(tmdb_struct.get(s, []))
                
                if vol_tmdb == 0 and vol_imdb > 0: continue
                
                if vol_imdb != vol_tmdb:
                    assimetria = True
                    relatorio_assimetria.append(f"  Temporada {s}: IMDb ({vol_imdb} episódios) vs TMDb ({vol_tmdb} episódios)")
                    
            if assimetria:
                metricas_bloco["assimetrias"].append({"nome": obra["nome"], "imdb_id": imdb_id})
                console.print("[bold red][!] Assimetria de granularidade detectada:[/bold red]")
                for linha in relatorio_assimetria:
                    console.print(f"[red]{linha}[/red]")

            for s in sorted(tmdb_struct.keys()):
                if all(not ep["lancado"] for ep in tmdb_struct[s]): continue
                
                metricas_bloco["temporadas"] += 1
                console.print(f"[bold cyan]Temporada {s}:[/bold cyan]")
                
                for ep in sorted(tmdb_struct[s], key=lambda x: x["episode"]):
                    metricas_bloco["episodios_mapeados"] += 1
                    ep_imdb = vol_imdb_local.get(s, {}).get(ep["episode"])
                    r_ep = ratings_dict.get(ep_imdb) if ep_imdb else None
                    nota_str = f"Nota: {r_ep['rating']} ({r_ep['votes']})" if r_ep else "Sem nota"
                    
                    is_assistido = False
                    
                    if not ep["lancado"]:
                        metricas_bloco["episodios_ignorados"] += 1
                        status = f"[dim]ignorado (Estreia: {ep['air_date'] or 'TBD'})[/dim]"
                    else:
                        if regras_confianca:
                            is_assistido = True
                            metricas_bloco["episodios_assistidos"] += 1
                            status = "[green]assistido (Confiança Absoluta)[/green]"
                        else:
                            is_assistido = (s, ep["episode"]) in ep_vistos
                            if is_assistido: metricas_bloco["episodios_assistidos"] += 1
                            status = "[green]assistido[/green]" if is_assistido else "[red]não assistido[/red]"
                            
                    if is_assistido:
                        linhas_csv.append({
                            "imdb_id": ep_imdb if ep_imdb else "",
                            "tmdb_id": ep["tmdb_id"],
                            "type": "episode",
                            "rating": r_ep['rating'] if r_ep else "",
                            "ignorar_no_historico": False
                        })
                        
                    console.print(f"E{ep['episode']:02d} → TMDb {ep['tmdb_id']} | IMDb: {ep_imdb or 'N/A'} | [yellow]{nota_str}[/yellow] | {status}")
                console.print("")
                
        except Exception as e:
            console.print(f"[bold red]Erro na obra '{obra['nome']}': {e}[/bold red]")
            
    return metricas_bloco

def exibir_documentacao():
    """Renderiza um painel formatado explicando todo o funcionamento e a arquitetura lógica do script."""
    doc_texto = """[bold cyan]1. VISÃO GERAL[/bold cyan]
Este script é um extrator (ETL) arquitetado para varrer a sua conta do Banco de Séries, contornar gargalos de rede 
(WAF e latência) utilizando matrizes de dados em memória, e gerar tabelas (CSVs) compatíveis com o Trakt.tv.

[bold cyan]2. INTELIGÊNCIA OFFLINE (ZERO NETWORK)[/bold cyan]
Na primeira execução, o motor baixa os dicionários oficiais do IMDb (~60MB compactados) e joga na RAM do seu PC.
Isso impede o problema do "N+1" e bloqueios por tráfego. Ele consulta o IMDb ID de cada episódio na sua RAM 
em frações de milissegundo.

[bold cyan]3. REGRAS DE CATEGORIAS E CONSUMO[/bold cyan]
• [bold white]Confiança Absoluta (Ativas em dia / Finalizadas Completas):[/bold white] Assume que tudo foi assistido. Não lê seu histórico, mas trava o que é futuro com base no calendário.
• [bold white]Auditoria Estrita (Atrasadas):[/bold white] Ignora a Confiança Absoluta. Rastreia meticulosamente a imagem [italic]darkchecked.png[/italic] no site e marca apenas o que você confirmou.

[bold cyan]4. PROTEÇÕES (FILTRO TEMPORAL E FALLBACK)[/bold cyan]
• O motor lê o relógio do seu PC. Episódios com data de transmissão superior ao dia atual são sumariamente ignorados e nunca exportados.
• Se o Banco de Séries fornecer um ID do IMDb antigo, ele varre silenciosamente a internet atrás do redirecionamento 
ou forçando aproximação por nome no TMDb para curar os links quebrados (Fallback).

[bold cyan]5. OS ARQUIVOS GERADOS[/bold cyan]
O roteador exporta dois arquivos propositalmente para o Trakt.tv não misturar lógicas:
→ [bold white]History.csv[/bold white]: Ignora sua coluna de nota e impede a importação no formato 'show' para grades atrasadas, garantindo que o seu percentual quebrado não atinja acidentalmente o 100%.
→ [bold white]Ratings.csv[/bold white]: Extrai apenas o que possui nota e credita ao seu perfil oficial."""
    
    limpar_tela()
    console.print(Panel.fit(doc_texto, title="[bold white]📖 MANUAL DE OPERAÇÃO E ARQUITETURA[/bold white]", border_style="blue"))

def exibir_menu_e_obter_selecao():
    """Exibe o seletor visual e converte a resposta do usuário nas categorias a serem processadas pelo core."""
    menu_texto = """[bold cyan]Selecione o bloco para processamento visual:[/bold cyan]

[bold white]1.[/bold white] Ativas em dia
[bold white]2.[/bold white] Finalizadas Completas
[bold white]3.[/bold white] Ativas Atrasadas
[bold white]4.[/bold white] Finalizadas Atrasadas
[bold white]5.[/bold white] Todas as categorias

[bold white]6.[/bold white] [bold green]📖 Documentação e Como Usar[/bold green]

[bold white]0.[/bold white] Sair"""
    
    console.print("\n")
    console.print(Panel.fit(menu_texto.strip(), title="[bold white]MENU DE OPERAÇÃO[/bold white]", border_style="blue"))
    
    opcoes_map = {
        "1": ["Ativas em dia"],
        "2": ["Finalizadas Completas"],
        "3": ["Ativas Atrasadas"],
        "4": ["Finalizadas Atrasadas"],
        "5": ["Ativas em dia", "Finalizadas Completas", "Ativas Atrasadas", "Finalizadas Atrasadas"],
        "6": "DOC"
    }
    
    while True:
        escolha = input("\nDigite o número da opção desejada: ").strip()
        if escolha == "0":
            sys.exit(0)
        if escolha in opcoes_map:
            return opcoes_map[escolha]
        console.print("[red]Opção inválida. Tente novamente.[/red]")

def main():
    limpar_tela()
    
    global TMDB_API_KEY
    TMDB_API_KEY = carregar_credencial("tmdb_api.txt", "Digite sua API Key do TMDb v3")
    cookie_bds = carregar_credencial("phpsessid.txt", "Digite seu PHPSESSID do Banco de Séries")

    ratings_dict, imdb_struct_db = carregar_datasets_imdb()
    
    adaptador = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504]))
    sessao = requests.Session()
    sessao.mount("https://", adaptador)
    sessao.mount("http://", adaptador)
    sessao.cookies.set("PHPSESSID", cookie_bds, domain="bancodeseries.com.br")
    sessao.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Connection": "close"})
    
    primeira_execucao = True
    
    while True:
        if not primeira_execucao:
            limpar_tela()
        primeira_execucao = False
        
        selecao = exibir_menu_e_obter_selecao()
        
        if selecao == "DOC":
            exibir_documentacao()
            console.input("\n[bold cyan]Pressione ENTER para voltar ao menu inicial...[/bold cyan]")
            continue
            
        categorias_alvo = selecao
        
        console.print(f"\n[cyan]Varrendo interface do Banco de Séries...[/cyan]")
        try:
            grades = extrair_todas_grades(sessao)
        except Exception as e:
            console.print(f"[bold red]Erro ao acessar o Banco de Séries (Sessão vencida ou queda): {e}[/bold red]")
            console.input("\n[bold cyan]Pressione ENTER para voltar ao menu inicial...[/bold cyan]")
            continue
        
        metricas_globais = {
            "series": 0, "temporadas": 0, "episodios_mapeados": 0,
            "episodios_ignorados": 0, "episodios_assistidos": 0, "assimetrias": []
        }
        
        linhas_exportacao = []
        start_time = time.time()
        
        for categoria in categorias_alvo:
            obras = grades.get(categoria, [])
            if not obras:
                console.print(f"[yellow]Nenhuma série elegível encontrada no bloco '{categoria}'.[/yellow]")
                continue
                
            console.print(f"\n[bold green]=== INICIANDO BLOCO: {categoria.upper()} ({len(obras)} obras) ===[/bold green]")
            confianca_absoluta = categoria in ["Ativas em dia", "Finalizadas Completas"]
            metricas_bloco = processar_bloco(sessao, obras, confianca_absoluta, ratings_dict, imdb_struct_db, linhas_exportacao)
            
            for chave in metricas_globais:
                if chave == "assimetrias":
                    metricas_globais["assimetrias"].extend(metricas_bloco["assimetrias"])
                else:
                    metricas_globais[chave] += metricas_bloco[chave]
                    
        tempo_execucao_segundos = time.time() - start_time
        h, rem = divmod(tempo_execucao_segundos, 3600)
        m, s = divmod(rem, 60)
        tempo_formatado = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        
        # Marca de tempo padrão para todos os arquivos da rodada
        timestamp_arquivo = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        relatorio_texto = f"""[bold cyan]Métricas de Execução[/bold cyan]
Tempo Total de Varredura: [bold white]{tempo_formatado}[/bold white]
Séries Processadas: [bold white]{metricas_globais['series']}[/bold white]
Temporadas Lidas: [bold white]{metricas_globais['temporadas']}[/bold white]

[bold cyan]Métricas de Consumo[/bold cyan]
Episódios Mapeados: [bold white]{metricas_globais['episodios_mapeados']}[/bold white]
Episódios Lançados Futuros (Ignorados): [bold white]{metricas_globais['episodios_ignorados']}[/bold white]
Episódios Marcados como Assistidos: [bold white]{metricas_globais['episodios_assistidos']}[/bold white]
"""
        if metricas_globais['assimetrias']:
            relatorio_texto += "\n[bold red][!] AÇÃO MANUAL EXIGIDA NO TRAKT.TV[/bold red]\n"
            relatorio_texto += "As séries abaixo apresentaram quebra de granularidade entre IMDb e TMDb e\nprecisarão de homologação manual na plataforma de destino:\n\n"
            for i, serie in enumerate(metricas_globais['assimetrias'], 1):
                relatorio_texto += f"{i}. {serie['nome']} (IMDb: {serie['imdb_id']})\n"
        else:
            relatorio_texto += "\n[bold green][✓] Nenhuma assimetria estrutural detectada.[/bold green]\n"

        if linhas_exportacao:
            linhas_history = [linha for linha in linhas_exportacao if not linha.get("ignorar_no_historico")]
            nome_arquivo_history = f"exportacao_history_{timestamp_arquivo}.csv"
            with open(nome_arquivo_history, mode='w', newline='', encoding='utf-8') as f:
                escritor_history = csv.DictWriter(f, fieldnames=["imdb_id", "tmdb_id", "type"], extrasaction='ignore')
                escritor_history.writeheader()
                escritor_history.writerows(linhas_history)
                
            nome_arquivo_ratings = f"exportacao_ratings_{timestamp_arquivo}.csv"
            linhas_com_nota = [linha for linha in linhas_exportacao if linha.get("rating")]
            if linhas_com_nota:
                with open(nome_arquivo_ratings, mode='w', newline='', encoding='utf-8') as f:
                    escritor_ratings = csv.DictWriter(f, fieldnames=["imdb_id", "tmdb_id", "type", "rating"], extrasaction='ignore')
                    escritor_ratings.writeheader()
                    escritor_ratings.writerows(linhas_com_nota)
            
            relatorio_texto += "\n[bold green][✓] Arquivos de exportação gerados:[/bold green]\n"
            relatorio_texto += f"    → {nome_arquivo_history} ([bold white]{len(linhas_history)}[/bold white] check-ins)\n"
            if linhas_com_nota:
                relatorio_texto += f"    → {nome_arquivo_ratings} ([bold white]{len(linhas_com_nota)}[/bold white] avaliações)\n"

        # GRAVAÇÃO DO LOG EM TEXTO PURO
        nome_arquivo_log = f"relatorio_execucao_{timestamp_arquivo}.txt"
        # O Regex abaixo captura e destrói qualquer tag entre colchetes do Rich antes de salvar no bloco de notas
        relatorio_limpo = re.sub(r'\[.*?\]', '', relatorio_texto)
        with open(nome_arquivo_log, "w", encoding="utf-8") as f:
            f.write("=== RELATORIO OPERACIONAL DE EXPORTACAO ===\n")
            f.write(relatorio_limpo)
            
        relatorio_texto += f"\n[bold green][✓] Log salvo para consulta:[/bold green] {nome_arquivo_log}\n"

        console.print("\n")
        console.print(Panel.fit(relatorio_texto.strip(), title="[bold white]RELATÓRIO OPERACIONAL DE EXPORTAÇÃO[/bold white]", border_style="blue"))
        
        console.input("\n[bold cyan]Pressione ENTER para voltar ao menu inicial...[/bold cyan]")

if __name__ == "__main__":
    sys.exit(main())