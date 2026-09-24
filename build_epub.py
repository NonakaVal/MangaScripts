#!/usr/bin/env python3
"""
Gera EPUB de mangá a partir de pastas de capítulos.
- Fonte: AVIF -> convertido para JPEG quality=92 subsampling 4:4:4 + optimize
- Sem redimensionamento (preserva resolução original)
- Aceita pastas "Capítulo *" ou "chapter *" (compatível com downloader + uso manual)

Uso standalone:
    python build_epub.py
    -> pergunta SRC, saída, título, autor e capa via input.

Uso via main.py:
    from build_epub import build_epub
    build_epub(src_dir, out_epub, capa_src, title, author)
"""
import pathlib
import zipfile
import re
import shutil
import textwrap
import tempfile
from PIL import Image

# Defaults (sobrescritos via input ou via main.py)
SRC_DEFAULT = pathlib.Path("/home/val/Downloads/Vagabond")
TITLE_DEFAULT = "Vagabond"
AUTHOR_DEFAULT = "Takehiko Inoue"
LANG_DEFAULT = "pt-BR"


def _num_key(path: pathlib.Path) -> tuple:
    """Ordenação natural: extrai números do nome para ordenar capítulos/páginas."""
    m = re.search(r"(\d+)", path.name)
    if m:
        return (int(m.group(1)), path.name.lower())
    parts = [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", path.name)]
    return (0, str(parts))


def collect_chapters(src: pathlib.Path):
    """Aceita 'Capítulo *' (legado) e 'chapter *' (downloader)."""
    ch_dirs = list(src.glob("Capítulo *")) + list(src.glob("chapter *"))
    # dedup + ordena numericamente
    ch_dirs = sorted(set(ch_dirs), key=_num_key)
    return ch_dirs


def build_epub(src_dir=None, out_epub=None, capa_src=None,
               title=None, author=None, lang=None, identifier=None):
    src = pathlib.Path(src_dir or SRC_DEFAULT).expanduser()
    title = title or TITLE_DEFAULT
    author = author or AUTHOR_DEFAULT
    lang = lang or LANG_DEFAULT
    identifier = identifier or f"urn:uuid:{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}-epub"

    if not src.is_dir():
        print(f"[✗] Pasta fonte não encontrada: {src}")
        return None

    ch_dirs = collect_chapters(src)
    if not ch_dirs:
        print(f"[✗] Nenhuma pasta 'Capítulo *' ou 'chapter *' encontrada em:\n{src}")
        return None

    # Saída default: <SRC>/<Titulo> - <primeiro>-<último>.epub
    if out_epub is None:
        nums = [re.search(r"(\d+)", d.name) for d in ch_dirs]
        nums = [int(m.group(1)) for m in nums if m]
        suffix = f"Capitulos {min(nums)}-{max(nums)}" if nums else "capitulos"
        out_epub = src / f"{title} - {suffix}.epub"
    out_epub = pathlib.Path(out_epub).expanduser()

    build = pathlib.Path(tempfile.mkdtemp(prefix="epub_build_"))
    oebps = build / "OEBPS"
    images = oebps / "images"

    try:
        (build / "META-INF").mkdir(parents=True)
        oebps.mkdir(parents=True, exist_ok=True)
        images.mkdir(parents=True, exist_ok=True)

        # ---- mimetype (must be uncompressed, first file) ----
        (build / "mimetype").write_text("application/epub+zip", encoding="ascii")

        # ---- META-INF/container.xml ----
        (build / "META-INF" / "container.xml").write_text('''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''', encoding="utf-8")

        # ---- capa (opcional) ----
        has_cover = False
        cover_media = "image/png"
        cover_href = "images/cover.png"
        if capa_src is None:
            # tenta capa.png / cover.* na pasta fonte
            for cand in ["capa.png", "capa.jpg", "cover.png", "cover.jpg", "capa.jpeg"]:
                if (src / cand).exists():
                    capa_src = src / cand
                    break
        if capa_src is not None:
            capa_src = pathlib.Path(capa_src).expanduser()
        if capa_src is not None and capa_src.exists():
            cover_dest = images / "cover.png"
            im = Image.open(capa_src)
            if im.mode == "RGBA":
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[3])
                im = bg
            elif im.mode != "RGB":
                im = im.convert("RGB")
            im.save(cover_dest, "PNG", optimize=False)
            print(f"Capa: {im.size} -> {cover_dest} ({cover_dest.stat().st_size/1024:.1f} KB)")
            has_cover = True
        else:
            print("[!] Sem capa (capa.png não encontrada) — EPUB será gerado sem página de capa.")

        # ---- coleta capítulos em ordem ----
        print(f"Encontrados {len(ch_dirs)} capítulos: {[d.name for d in ch_dirs]}")

        chapters = []
        image_items = []
        if has_cover:
            image_items.append(("cover-image", "images/cover.png", "image/png"))

        total_pages = 0
        for ch_dir in ch_dirs:
            m = re.search(r"(\d+)", ch_dir.name)
            ch = int(m.group(1)) if m else len(chapters) + 1
            avifs = sorted(ch_dir.glob("*.avif"), key=_num_key)
            if not avifs:
                avifs = sorted(
                    list(ch_dir.glob("*.jpg")) + list(ch_dir.glob("*.jpeg"))
                    + list(ch_dir.glob("*.png")) + list(ch_dir.glob("*.webp")),
                    key=_num_key)
            print(f"  {ch_dir.name}: {len(avifs)} imagens")
            chapter_images = []
            idx = 0
            for src_img in avifs:
                if src_img.stat().st_size == 0:
                    print(f"  [ignorado vazio] {src_img.name}")
                    continue
                idx += 1
                dest_name = f"c{ch:02d}_{idx:03d}.jpg"
                dest = images / dest_name
                try:
                    with Image.open(src_img) as im:
                        if im.mode in ("RGBA", "LA"):
                            bg = Image.new("RGB", im.size, (255, 255, 255))
                            bg.paste(im, mask=im.split()[-1])
                            im = bg
                        elif im.mode != "RGB":
                            im = im.convert("RGB")
                        im.save(dest, "JPEG", quality=92, subsampling=0,
                                optimize=True, progressive=False)
                except Exception as e:
                    print(f"ERRO ao converter {src_img}: {e}")
                    continue
                item_id = f"img-c{ch:02d}-{idx:03d}"
                image_items.append((item_id, f"images/{dest_name}", "image/jpeg"))
                chapter_images.append((dest_name, item_id))
                total_pages += 1
            chapters.append((ch, ch_dir.name, chapter_images))

        print(f"Total de páginas: {total_pages}")
        if total_pages == 0:
            print("[✗] Nenhuma imagem encontrada nos capítulos.")
            return None
        total_img_size = sum((images / name).stat().st_size
                             for _, _, imgs in chapters for name, _ in imgs)
        print(f"Tamanho total imagens convertidas: {total_img_size/1024/1024:.2f} MB")

        # ---- styles.css ----
        (oebps / "styles.css").write_text(textwrap.dedent("""\
            @charset "utf-8";
            html, body { margin: 0; padding: 0; }
            body {
                background: #fff;
                text-align: center;
                margin: 0;
                padding: 0;
            }
            .cover { margin: 0; padding: 0; text-align: center; }
            .cover img { width: 100%; height: auto; max-width: 100%; max-height: 100vh; object-fit: contain; }
            .page { margin: 0; padding: 0; text-align: center; page-break-after: always; }
            .page img { width: 100%; height: auto; max-width: 100%; display: block; margin: 0 auto; }
            .page:last-child { page-break-after: auto; }
            h1.ch-title { font-family: serif; font-size: 1.6em; margin: 2em 0 1em; color: #111; text-align: center; page-break-after: avoid; }
            .chapter-header { text-align: center; padding: 3em 0 1em; }
            .chapter-header h1 { font-size: 1.9em; margin: 0; color: #111; }
            .chapter-header p { font-size: 0.9em; color: #666; margin: 0.4em 0 0; }
        """), encoding="utf-8")

        # ---- cover.xhtml ----
        if has_cover:
            (oebps / "cover.xhtml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <title>Capa - {title}</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <div class="cover">
    <img src="{cover_href}" alt="Capa - {title}"/>
  </div>
</body>
</html>''', encoding="utf-8")

        # ---- chapter XHTMLs ----
        for ch_num, ch_label, imgs in chapters:
            fname = f"chapter-{ch_num:02d}.xhtml"
            fpath = oebps / fname
            img_tags = "\n".join(
                f'  <div class="page"><img src="images/{name}" alt="{title} {ch_label} - Página {i}"/></div>'
                for i, (name, _) in enumerate(imgs, start=1)
            )
            fpath.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <title>{ch_label} - {title}</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <div class="chapter-header">
    <h1>{ch_label}</h1>
    <p>{title} — {author}</p>
  </div>
{img_tags}
</body>
</html>''', encoding="utf-8")

        # ---- nav.xhtml ----
        nav_items_html = "\n".join(
            f'      <li><a href="chapter-{ch:02d}.xhtml">{label}</a></li>' for ch, label, _ in chapters
        )
        cover_nav = '      <li><a href="cover.xhtml">Capa</a></li>\n' if has_cover else ''
        (oebps / "nav.xhtml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <title>Sumário</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Sumário</h1>
    <ol>
{cover_nav}{nav_items_html}
    </ol>
  </nav>
  <nav epub:type="landmarks" id="landmarks" hidden="">
    <h2>Guia</h2>
    <ol>
      <li><a epub:type="cover" href="cover.xhtml">Capa</a></li>
    </ol>
  </nav>
</body>
</html>''', encoding="utf-8")

        # ---- toc.ncx ----
        ncx_points = "\n".join(
            f'''    <navPoint id="ch{ch}" playOrder="{i+1}">
      <navLabel><text>{label}</text></navLabel>
      <content src="chapter-{ch:02d}.xhtml"/>
    </navPoint>''' for i, (ch, label, _) in enumerate(chapters, start=1)
        )
        cover_ncx = '''    <navPoint id="cover" playOrder="1">
      <navLabel><text>Capa</text></navLabel>
      <content src="cover.xhtml"/>
    </navPoint>
''' if has_cover else ''
        (oebps / "toc.ncx").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{identifier}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{title}</text></docTitle>
  <navMap>
{cover_ncx}{ncx_points}
  </navMap>
</ncx>''', encoding="utf-8")

        # ---- content.opf ----
        manifest_lines = []
        if has_cover:
            manifest_lines.append('    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
        manifest_lines.append('    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
        manifest_lines.append('    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        manifest_lines.append('    <item id="css" href="styles.css" media-type="text/css"/>')
        if has_cover:
            manifest_lines.append(f'    <item id="cover-image" href="{cover_href}" media-type="{cover_media}" properties="cover-image"/>')
        for ch, _, _ in chapters:
            manifest_lines.append(f'    <item id="ch{ch:02d}" href="chapter-{ch:02d}.xhtml" media-type="application/xhtml+xml"/>')
        for item_id, href, mtype in image_items:
            if item_id == "cover-image":
                continue
            manifest_lines.append(f'    <item id="{item_id}" href="{href}" media-type="{mtype}"/>')

        manifest_str = "\n".join(manifest_lines)
        spine_items = []
        if has_cover:
            spine_items.append('    <itemref idref="cover"/>')
        spine_items += [f'    <itemref idref="ch{ch:02d}"/>' for ch, _, _ in chapters]
        spine_str = "\n".join(spine_items)

        (oebps / "content.opf").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{lang}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="bookid">{identifier}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator id="author">{author}</dc:creator>
    <dc:language>{lang}</dc:language>
    <dc:description>Mangá {title} de {author} — compilação organizada para leitura em ordem.</dc:description>
    <meta property="dcterms:modified">2026-09-24T00:00:00Z</meta>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
{manifest_str}
  </manifest>
  <spine toc="ncx">
{spine_str}
  </spine>
  <guide>
    <reference type="cover" title="Capa" href="cover.xhtml"/>
    <reference type="toc" title="Sumário" href="nav.xhtml"/>
  </guide>
</package>''', encoding="utf-8")

        # ---- build EPUB zip ----
        if out_epub.exists():
            out_epub.unlink()

        with zipfile.ZipFile(out_epub, "w", compresslevel=9) as z:
            z.write(build / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
            for path in build.rglob("*"):
                if path.is_file() and path.name != "mimetype":
                    arc = path.relative_to(build).as_posix()
                    z.write(path, arc, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

        print(f"\nEPUB criado: {out_epub}")
        print(f"Tamanho: {out_epub.stat().st_size/1024/1024:.2f} MB")
        with zipfile.ZipFile(out_epub) as z:
            print(f"Total arquivos no EPUB: {len(z.namelist())}")
        for ch, label, imgs in chapters:
            print(f"  {label}: {len(imgs)} páginas")
        print("\nEPUB pronto (JPEG 92% 4:4:4 optimize).")
        return out_epub
    finally:
        shutil.rmtree(build, ignore_errors=True)


def main(src_dir=None, out_epub=None, capa_src=None, title=None, author=None):
    """Entry-point interativo: pergunta caminhos via input se não informados."""
    src = (src_dir or input(f"Pasta fonte [{SRC_DEFAULT}]: ").strip()
           or str(SRC_DEFAULT))
    default_out = str(pathlib.Path(src).expanduser() / "manga.epub")
    out = (out_epub or input(f"Arquivo EPUB saída [{default_out}]: ").strip()
           or default_out)
    t = title if title is not None else input(f"Título [{TITLE_DEFAULT}]: ").strip() or TITLE_DEFAULT
    a = author if author is not None else input(f"Autor [{AUTHOR_DEFAULT}]: ").strip() or AUTHOR_DEFAULT
    default_capa = str(pathlib.Path(src).expanduser() / "capa.png")
    c = (capa_src if capa_src is not None
         else input(f"Capa (vazio = auto/detectar) [{default_capa}]: ").strip() or default_capa)
    build_epub(src, out, c or None, t, a)


if __name__ == "__main__":
    main()
