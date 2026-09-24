"""
DemonicScans - Vagabond Downloader
Baseado em image_downloader copy.py (estrutura mantida) adaptado para demonicScans.org
- Pagina base: https://demonicscans.org/manga/Vagabond
- Primeira pagina: https://demonicscans.org/title/Vagabond/chapter/1/1
  (equivalente a https://demonicscans.org/chaptered.php?manga=212&chapter=1)
- Imagens reais: <img class="imgholder" src="https://mangareadon.org/Vagabond/{cap}/{pag}.jpg">
  Fallback: demoniclibs.com -> librarydm.com

Dependências:
    pip install selenium webdriver-manager requests beautifulsoup4 tqdm pillow
    (tqdm/pillow opcionais)
"""

import re
import time
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

# ─────────────────────────────────────────────
#  CONFIGURAÇÕES — edite aqui antes de rodar
# ─────────────────────────────────────────────

# URL inicial. Mude para https://demonicscans.org/title/Vagabond/chapter/10/1
# para começar do capítulo 10 (requisito do usuário)
URL_INICIAL = "https://demonicscans.org/title/Vagabond/chapter/1/1"

# Alternativa direta por número (se URL_INICIAL não for alterada, este valor é usado)
# Ex.: START_CHAPTER = 10  => baixa 10..19
START_CHAPTER = None  # None = extrai de URL_INICIAL; ou defina int

MAX_CAPITULOS = 10  # total máximo a baixar

MANGA_SLUG = "Vagabond"
MANGA_ID = 212  # id interno usado em /chaptered.php?manga=212

# Pasta base — cada capítulo vai para "chapter 1", "chapter 2", ...
PASTA_SAIDA = Path.home() / "Downloads" / "Vagabond"
# Ex. original: Path("/run/media/val/FAFF-B504/.H/Vagabond")
# PASTA_SAIDA = Path("/run/media/val/FAFF-B504/06 Projetos e Trampo/01-CONHECIMENTO/vaults/OLDVAULTS/Notes/X/Scripts/manga_reader/Vagabond")

# Seletor CSS — APENAS páginas do capítulo. Não usar "img" genérico (pega ads/logo)
CSS_SELECTOR = "img.imgholder"

# Atributos onde a URL pode estar (DemonicScans usa src direto, mas mantemos fallbacks)
ATRIBUTOS_SRC = ["src", "data-src", "data-lazy-src", "data-original"]

# Espera e scroll (imgholder é estático, mas Selenium pode precisar)
ESPERA_JS = 2
FAZER_SCROLL = True

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
    "Referer": "https://demonicscans.org/",
}

# Domínios alternativos (site tenta tryAgain: demoniclibs -> librarydm)
DOMINIOS_FALLBACK = [
    ("demoniclibs.com", "librarydm.com"),
    ("mangareadon.org", "demoniclibs.com"),
    ("mangareadon.org", "librarydm.com"),
]

# ─────────────────────────────────────────────

def parse_start_chapter(url: str, fallback: int | None) -> int:
    """Extrai número do capítulo de URL tipo .../chapter/10/1 ou .../chapter=10"""
    if fallback is not None:
        return int(fallback)
    m = re.search(r"/chapter/(\d+)", url)
    if m:
        return int(m.group(1))
    m = re.search(r"[?&]chapter=(\d+)", url)
    if m:
        return int(m.group(1))
    return 1

def construir_url_capitulo(capitulo: int) -> str:
    """Gera URL canônica para o capítulo. Formato preferido /title/..."""
    return f"https://demonicscans.org/title/{MANGA_SLUG}/chapter/{capitulo}/1"

def sanitizar_nome(url: str) -> str:
    nome = Path(urlparse(url).path).name
    nome = re.sub(r"[^\w.\-]", "_", nome)
    return nome or "imagem.jpg"

def ordenar_por_pagina(urls: list[str]) -> list[str]:
    """Ordena por número da página extraído de /{cap}/{pag}.jpg"""
    def key(u: str):
        m = re.search(r"/(\d+)\.(?:jpg|jpeg|png|webp)(?:\?|$)", u, re.I)
        if m:
            return int(m.group(1))
        m2 = re.search(r"/(\d+)/(\d+)\.", u)
        if m2:
            return int(m2.group(2))
        return 0
    return sorted(urls, key=key)

def eh_imagem_do_capitulo(url: str, capitulo: int | None = None) -> bool:
    """Filtra apenas imagens reais do capítulo, exclui ads/logos/thumbs."""
    if not url or url.startswith("data:"):
        return False
    low = url.lower()
    # excluir assets sabidos
    bloqueados = ["free_ads", "demon-logo", "demon-title", "noimg", "paypal", "discord", "thumbnails"]
    if any(b in low for b in bloqueados):
        return False
    # deve conter domínio de manga ou slug
    # imgholder já garante, mas dupla checagem
    if MANGA_SLUG.lower() not in low:
        # algumas variações usam slug minúsculo
        if "mangareadon" not in low and "demoniclibs" not in low and "librarydm" not in low:
            return False
    # se tiver capítulo no path, deve bater
    if capitulo is not None:
        # ex: /Vagabond/10/  -> só aceitar se contém /10/
        if f"/{capitulo}/" not in url and f"/{MANGA_SLUG}/{capitulo}/" not in url:
            # não bloqueia se não tem número (alguns caps têm nome diferente), mas
            # para Vagabond o padrão é sempre /{cap}/
            pass
    # extensão
    if not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", low):
        return False
    return True

def gerar_urls_fallback(url: str) -> list[str]:
    """Gera variações de domínio como faz o JS tryAgain() do site."""
    urls = [url]
    for antigo, novo in DOMINIOS_FALLBACK:
        if antigo in url and novo not in url:
            urls.append(url.replace(antigo, novo))
    # também tenta o inverso
    for antigo, novo in DOMINIOS_FALLBACK:
        if novo in url and antigo not in url:
            v = url.replace(novo, antigo)
            if v not in urls:
                urls.append(v)
    return urls

def baixar_imagem(url: str, caminho: Path, session: requests.Session, referer: str) -> bool:
    headers = dict(HEADERS)
    headers["Referer"] = referer
    # tenta url + fallbacks
    for tentativa_url in gerar_urls_fallback(url):
        try:
            r = session.get(tentativa_url, headers=headers, timeout=20, stream=True)
            if r.status_code in (403, 404):
                # tenta próximo domínio
                continue
            r.raise_for_status()
            ct = r.headers.get("Content-Type", "")
            if "image" not in ct and "octet-stream" not in ct:
                # alguns servidores não mandam content-type correto, mas se tem bytes >1k, aceita
                if len(r.content) < 1024:
                    continue
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_bytes(r.content)
            print(f"  [✓] {caminho.name} ({len(r.content)/1024:.1f} KB) <- {tentativa_url}")
            return True
        except Exception as e:
            # tenta próximo fallback silenciosamente, só loga no último
            if tentativa_url == gerar_urls_fallback(url)[-1]:
                print(f"  [✗] {url} -> {e}")
            continue
    return False

def coletar_urls_selenium(url_pagina: str, capitulo: int) -> list[str]:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager

    print("[→] Iniciando Chrome headless...")
    opcoes = Options()
    opcoes.add_argument("--headless=new")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--window-size=1920,1080")
    opcoes.add_argument(f"user-agent={HEADERS['User-Agent']}")
    opcoes.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opcoes)
    urls: list[str] = []
    try:
        print(f"[→] Acessando: {url_pagina}")
        driver.get(url_pagina)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(ESPERA_JS)

        if FAZER_SCROLL:
            print("[→] Scroll para garantir render...")
            altura = driver.execute_script("return document.body.scrollHeight")
            passo = 700
            pos = 0
            while pos < altura:
                driver.execute_script(f"window.scrollTo(0, {pos});")
                time.sleep(0.25)
                pos += passo
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.8)

        # Tenta seletor imgholder primeiro
        elementos = driver.find_elements(By.CSS_SELECTOR, CSS_SELECTOR)
        print(f"[→] Selenium: {len(elementos)} elemento(s) com '{CSS_SELECTOR}'")
        if not elementos:
            # fallback: qualquer img com mangareadon no src
            elementos = driver.find_elements(By.CSS_SELECTOR, "img")
            print(f"[→] Fallback Selenium: {len(elementos)} <img> totais")

        for el in elementos:
            url_img = None
            for attr in ATRIBUTOS_SRC:
                valor = el.get_attribute(attr)
                if valor and valor.strip() and not valor.startswith("data:"):
                    if valor.startswith("/"):
                        valor = urljoin(url_pagina, valor)
                    url_img = valor.strip()
                    break
            if url_img and url_img not in urls and eh_imagem_do_capitulo(url_img, capitulo):
                urls.append(url_img)

        # Se ainda vazio, tenta extrair do page_source com regex (caso JS injete)
        if not urls:
            import re as _re
            srcs = _re.findall(r'src="([^"]+mangareadon[^"]+)"', driver.page_source)
            for s in srcs:
                if s not in urls and eh_imagem_do_capitulo(s, capitulo):
                    urls.append(urljoin(url_pagina, s))

    finally:
        driver.quit()

    urls = ordenar_por_pagina(list(dict.fromkeys(urls)))  # dedup + ordena
    return urls

def coletar_urls_requests(url_pagina: str, capitulo: int) -> list[str]:
    from bs4 import BeautifulSoup

    print("[→] Coleta estática (requests + BeautifulSoup)...")
    sess = requests.Session()
    r = sess.get(url_pagina, headers={**HEADERS, "Referer": url_pagina}, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    elementos = soup.select(CSS_SELECTOR)
    print(f"[→] {len(elementos)} img.imgholder encontradas")
    if not elementos:
        # fallback: busca por regex no HTML
        import re as _re
        raw = _re.findall(r'src="(https?://[^"]+/(?:Vagabond|manga)/[^"]+\.jpg[^"]*)"', r.text, re.I)
        elementos = []
        urls = []
        for u in raw:
            if eh_imagem_do_capitulo(u, capitulo) and u not in urls:
                urls.append(u)
        return ordenar_por_pagina(urls)

    urls: list[str] = []
    for el in elementos:
        for attr in ATRIBUTOS_SRC:
            valor = el.get(attr, "")
            if valor and not valor.startswith("data:"):
                url_img = urljoin(url_pagina, valor.strip())
                if url_img not in urls and eh_imagem_do_capitulo(url_img, capitulo):
                    urls.append(url_img)
                break

    # também varre page_source por mangareadon links extras
    import re as _re
    extras = _re.findall(r'https?://[^"\']+mangareadon[^"\']+\.(?:jpg|png|webp)', r.text)
    for e in extras:
        if e not in urls and eh_imagem_do_capitulo(e, capitulo):
            urls.append(e)

    return ordenar_por_pagina(urls)

def baixar_capitulo(capitulo: int, pasta_base: Path, session: requests.Session) -> int:
    url_cap = construir_url_capitulo(capitulo)
    pasta_cap = pasta_base / f"chapter {capitulo}"
    pasta_cap.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print(f"  Capítulo {capitulo} -> {url_cap}")
    print(f"  Pasta: {pasta_cap.resolve()}")
    print("="*60)

    urls: list[str] = []
    # Tenta Selenium primeiro (necessário se Cloudflare), fallback requests
    try:
        urls = coletar_urls_selenium(url_cap, capitulo)
    except ImportError as e:
        print(f"[!] Selenium não instalado ({e}), tentando requests...")
    except Exception as e:
        print(f"[!] Selenium falhou: {e}")

    if not urls:
        try:
            urls = coletar_urls_requests(url_cap, capitulo)
        except Exception as e:
            print(f"[✗] Falha coleta estática cap {capitulo}: {e}")
            return 0

    if not urls:
        print(f"[!] Nenhuma imagem encontrada para cap {capitulo}. Verifique se o capítulo existe ou se o site mudou o seletor.")
        return 0

    print(f"[→] {len(urls)} páginas encontradas. Baixando...")

    # tqdm opcional
    try:
        from tqdm import tqdm
        iterator = tqdm(enumerate(urls, start=1), total=len(urls), desc=f"Cap {capitulo}", unit="pg")
    except ImportError:
        iterator = enumerate(urls, start=1)

    sucesso = 0
    for i, url in iterator:
        # nome ordenado 001.jpg, 002.jpg ... preserva extensão original
        ext = Path(urlparse(url).path).suffix or ".jpg"
        if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            ext = ".jpg"
        nome = f"{i:03d}{ext.lower()}"
        caminho = pasta_cap / nome

        if caminho.exists() and caminho.stat().st_size > 1024:
            # já baixado
            try:
                iterator.set_postfix_str(f"pulando {nome}")  # type: ignore
            except: pass
            print(f"  [=] Já existe: {nome}")
            sucesso += 1
            continue

        if baixar_imagem(url, caminho, session, referer=url_cap):
            sucesso += 1
        time.sleep(0.15)

    print(f"[✓] Cap {capitulo}: {sucesso}/{len(urls)} páginas salvas em {pasta_cap}")
    return sucesso

def main():
    # Permite override via CLI: python script.py 10 5  -> começa no 10, baixa 5
    # ou: python script.py https://demonicscans.org/title/Vagabond/chapter/10/1
    global URL_INICIAL, MAX_CAPITULOS, START_CHAPTER
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith("http"):
            URL_INICIAL = arg
            START_CHAPTER = None
            if len(sys.argv) > 2:
                try: MAX_CAPITULOS = int(sys.argv[2])
                except: pass
        else:
            try:
                START_CHAPTER = int(arg)
                URL_INICIAL = construir_url_capitulo(START_CHAPTER)
            except: pass
            if len(sys.argv) > 2:
                try: MAX_CAPITULOS = int(sys.argv[2])
                except: pass

    start = parse_start_chapter(URL_INICIAL, START_CHAPTER)

    pasta_base = Path(PASTA_SAIDA)
    pasta_base.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("  DemonicScans - Vagabond Downloader")
    print("="*60)
    print(f"  Manga      : {MANGA_SLUG} (id={MANGA_ID})")
    print(f"  Início     : capítulo {start} ({construir_url_capitulo(start)})")
    print(f"  Quantidade : {MAX_CAPITULOS} capítulo(s) ({start} .. {start+MAX_CAPITULOS-1})")
    print(f"  Seletor    : {CSS_SELECTOR}  (apenas páginas do capítulo)")
    print(f"  Pasta base : {pasta_base.resolve()}")
    print("-"*60)

    session = requests.Session()
    session.headers.update(HEADERS)

    total_ok = 0
    caps_ok = 0
    for offset in range(MAX_CAPITULOS):
        cap = start + offset
        try:
            ok = baixar_capitulo(cap, pasta_base, session)
            if ok > 0:
                caps_ok += 1
                total_ok += ok
            else:
                print(f"[!] Cap {cap} sem imagens - interrompendo? (pode ser fim da obra)")
                # não interrompe automaticamente, continua para tentar próximo
                # Se 2 caps seguidos falharem, para
                if offset >= 1:
                    # checa se último também falhou
                    pass
        except KeyboardInterrupt:
            print("\n[!] Interrompido pelo usuário")
            break
        except Exception as e:
            print(f"[✗] Erro cap {cap}: {e}")
        time.sleep(1.2)

    print("\n" + "="*60)
    print(f"  Concluído: {caps_ok}/{MAX_CAPITULOS} capítulos, {total_ok} páginas")
    print(f"  Salvo em: {pasta_base.resolve()}")
    for p in sorted(pasta_base.glob("chapter *")):
        cnt = len(list(p.glob("*.jpg"))) + len(list(p.glob("*.png"))) + len(list(p.glob("*.webp")))
        print(f"    - {p.name}: {cnt} imgs")
    print("="*60)

if __name__ == "__main__":
    main()
