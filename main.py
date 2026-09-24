#!/usr/bin/env python3
"""
EPUBMangaExtractor — Menu central (estilo PyBox).
Centraliza e simplifica o uso dos scripts da pasta:
  1. Baixar capítulos (download-demonicscans.py)
  2. Gerar EPUB (build_epub.py)
  3. Gerar leitor HTML único (build_HTML-Reader.py)

Uso:
    python main.py
"""
import importlib.util
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DL_SCRIPT = ROOT / "download-demonicscans.py"
EPUB_SCRIPT = ROOT / "build_epub.py"
HTML_SCRIPT = ROOT / "build_HTML-Reader.py"


def clear():
    os.system("clear" if os.name != "nt" else "cls")


def header(title):
    print()
    print("╭" + "─" * 60 + "╮")
    print(f"│ {title:<58} │")
    print("╰" + "─" * 60 + "╯")
    print()


def pause():
    input("\nENTER para voltar ao menu...")


def ask(prompt, default=""):
    """Input com default: mostra [default], Enter mantém."""
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def load_module(name, path: Path):
    """Carrega script com hífen no nome via importlib (sem importar no sys.modules global)."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível carregar {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def opt_download():
    clear()
    header("Baixar capítulos — DemonicScans")
    print("Informe o ponto de partida (URL tem prioridade sobre número).")
    print()
    url = ask("URL do capítulo inicial (vazio = usar nº abaixo)",
              "https://demonicscans.org/title/Vagabond/chapter/1/1")
    # Se usuário apagou tudo, permite começar por número
    start = ""
    if not url:
        start = ask("Capítulo inicial", "1")
    else:
        # permite sobrescrever mesmo com URL: pergunta se quer trocar o nº
        pass
    qtd = ask("Quantidade de capítulos", "10")
    pasta = ask("Pasta de saída", str(Path.home() / "Downloads" / "Vagabond"))

    try:
        qtd_i = int(qtd)
    except ValueError:
        print(f"[!] Quantidade inválida '{qtd}', usando 10.")
        qtd_i = 10

    mod = load_module("dl_mod", DL_SCRIPT)
    url_arg = url or None
    start_arg = None
    if not url_arg and start:
        try:
            start_arg = int(start)
        except ValueError:
            print(f"[!] Capítulo inválido '{start}', usando 1.")
            start_arg = 1
    print()
    mod.main(url_inicial=url_arg, start_chapter=start_arg,
             max_capitulos=qtd_i, pasta_saida=pasta)


def opt_epub():
    clear()
    header("Gerar EPUB")
    pasta = ask("Pasta fonte (com subpastas 'chapter N' ou 'Capítulo N')",
                str(Path.home() / "Downloads" / "Vagabond"))
    default_out = str(Path(pasta).expanduser() / "manga.epub")
    out = ask("Arquivo EPUB de saída", default_out)
    titulo = ask("Título", "Vagabond")
    autor = ask("Autor", "Takehiko Inoue")
    capa = ask("Capa (vazio = detectar capa.png/cover.* sozinho)", "")

    mod = load_module("epub_mod", EPUB_SCRIPT)
    print()
    mod.build_epub(pasta, out, capa or None, titulo, autor)


def opt_html():
    clear()
    header("Gerar leitor HTML único")
    base = ask("Pasta base (com subpastas de capítulos)",
               str(Path.home() / "Downloads" / "Vagabond"))
    default_out = str(Path(base).expanduser()
                      / f"{Path(base).expanduser().name}fuka.html")
    out = ask("Arquivo HTML de saída", default_out)
    titulo = ask("Título", Path(base).expanduser().name)

    mod = load_module("html_mod", HTML_SCRIPT)
    print()
    # usa build direto (sem re-perguntar inputs internos)
    mod.build_single_html(base, out, titulo or None)


def menu():
    while True:
        clear()
        header("EPUBMangaExtractor — Menu")
        print("1. Baixar capítulos (DemonicScans)")
        print("2. Gerar EPUB")
        print("3. Gerar leitor HTML único")
        print()
        print("q. sair")
        choice = input("\nEscolha: ").strip().lower()
        if choice == "q":
            print("\nAté mais!")
            sys.exit(0)
        try:
            if choice == "1":
                opt_download()
            elif choice == "2":
                opt_epub()
            elif choice == "3":
                opt_html()
            else:
                print("Opção inválida.")
                pause()
                continue
        except KeyboardInterrupt:
            print("\n[!] Operação interrompida pelo usuário.")
        except Exception:
            print("\n[✗] Erro durante a execução:")
            traceback.print_exc()
        pause()


if __name__ == "__main__":
    menu()
