#!/usr/bin/env python3
"""
Gera EPUB de Vagabond Vol 1 (Capítulos 01-10) com ótimo equilíbrio qualidade/tamanho.
- Fonte: AVIF -> convertido para JPEG quality=92 subsampling 4:4:4 + optimize (perda visual imperceptível, ~55% menor)
- Sem redimensionamento (preserva resolução original)
- quality 92 é considerado "visualmente lossless" para mangá; economia grande com perda mínima
"""
import pathlib, zipfile, re, shutil, textwrap
from PIL import Image

SRC = pathlib.Path("/home/val/Downloads/Vagabond")
OUT_EPUB = SRC / "Vagabond - Vol 1 - Capitulos 1-10.epub"
BUILD = pathlib.Path("/tmp/epub_build")
OEBPS = BUILD / "OEBPS"
IMAGES = OEBPS / "images"

# clean
if BUILD.exists():
    shutil.rmtree(BUILD)
BUILD.mkdir(parents=True)
(BUILD / "META-INF").mkdir()
OEBPS.mkdir()
IMAGES.mkdir()

TITLE = "Vagabond"
AUTHOR = "Takehiko Inoue"
LANG = "pt-BR"
IDENTIFIER = "urn:uuid:vagabond-vol1-ch1-10-2026"

# ---- mimetype (must be uncompressed, first file) ----
(BUILD / "mimetype").write_text("application/epub+zip", encoding="ascii")

# ---- META-INF/container.xml ----
(BUILD / "META-INF" / "container.xml").write_text('''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''', encoding="utf-8")

# ---- capa ----
capa_src = SRC / "capa.png"
cover_dest = IMAGES / "cover.jpg"
# Converter capa para JPEG qualidade máxima (melhor compatibilidade)
# Se quiser manter PNG lossless, troque para cover.png; aqui usamos JPEG 100 para consistência mas PNG é ok.
# Vamos manter PNG lossless para capa: melhor qualidade absoluta.
cover_dest = IMAGES / "cover.png"
im = Image.open(capa_src)
if im.mode == "RGBA":
    bg = Image.new("RGB", im.size, (255,255,255))
    bg.paste(im, mask=im.split()[3])
    im = bg
elif im.mode != "RGB":
    im = im.convert("RGB")
# Salva PNG sem compressão extra (optimize=False para evitar perda, mas PNG é lossless)
im.save(cover_dest, "PNG", optimize=False)
print(f"Capa: {im.size} -> {cover_dest} ({cover_dest.stat().st_size/1024:.1f} KB)")

# ---- coleta capítulos em ordem ----
# Pasta formato "Capítulo 01" .. "Capítulo 10"
ch_dirs = sorted(SRC.glob("Capítulo *"), key=lambda p: int(re.search(r'(\d+)', p.name).group(1)))
print(f"Encontrados {len(ch_dirs)} capítulos: {[d.name for d in ch_dirs]}")

chapters = []
image_items = []
image_items.append(("cover-image", "images/cover.png", "image/png"))

total_pages = 0
for ch_dir in ch_dirs:
    m = re.search(r'(\d+)', ch_dir.name)
    ch = int(m.group(1))
    # glob avif, ordenado numericamente pelo stem
    avifs = sorted(ch_dir.glob("*.avif"), key=lambda p: int(re.search(r'(\d+)', p.stem).group(1) or 0) if re.search(r'(\d+)', p.stem) else p.stem)
    # fallback se não houver avif, tenta jpeg/png/webp
    if not avifs:
        avifs = sorted(list(ch_dir.glob("*.jpg")) + list(ch_dir.glob("*.jpeg")) + list(ch_dir.glob("*.png")) + list(ch_dir.glob("*.webp")), key=lambda p: p.name)
    print(f"  {ch_dir.name}: {len(avifs)} imagens")
    chapter_images = []
    idx = 0
    for src in avifs:
        # pula arquivos vazios ou corrompidos
        if src.stat().st_size == 0:
            print(f"  [ignorado vazio] {src.name}")
            continue
        idx += 1
        dest_name = f"c{ch:02d}_{idx:03d}.jpg"
        dest = IMAGES / dest_name
        # Conversão AVIF -> JPEG com ótimo equilíbrio (q92 4:4:4 optimize)
        # q92 = visualmente idêntico a q100, mas ~55% menor. Ideal para reduzir tamanho sem perda perceptível.
        try:
            with Image.open(src) as im:
                if im.mode in ("RGBA", "LA"):
                    bg = Image.new("RGB", im.size, (255,255,255))
                    bg.paste(im, mask=im.split()[-1])
                    im = bg
                elif im.mode != "RGB":
                    im = im.convert("RGB")
                # quality 92 + optimize + subsampling 0 preserva croma, mínima perda visual
                im.save(dest, "JPEG", quality=92, subsampling=0, optimize=True, progressive=False)
        except Exception as e:
            print(f"ERRO ao converter {src}: {e}")
            continue
        item_id = f"img-c{ch:02d}-{idx:03d}"
        image_items.append((item_id, f"images/{dest_name}", "image/jpeg"))
        chapter_images.append((dest_name, item_id))
        total_pages += 1
    chapters.append((ch, ch_dir.name, chapter_images))

print(f"Total de páginas: {total_pages}")
# tamanho após conversão
total_img_size = sum((IMAGES / name).stat().st_size for _, _, imgs in chapters for name, _ in imgs)
print(f"Tamanho total imagens convertidas: {total_img_size/1024/1024:.2f} MB")

# ---- styles.css ----
(OEBPS / "styles.css").write_text(textwrap.dedent("""\
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
(OEBPS / "cover.xhtml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <title>Capa - Vagabond</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <div class="cover">
    <img src="images/cover.png" alt="Capa - Vagabond vol. 1 por Takehiko Inoue"/>
  </div>
</body>
</html>''', encoding="utf-8")

# ---- chapter XHTMLs ----
for ch_num, ch_label, imgs in chapters:
    fname = f"chapter-{ch_num:02d}.xhtml"
    fpath = OEBPS / fname
    img_tags = "\n".join(
        f'  <div class="page"><img src="images/{name}" alt="Vagabond {ch_label} - Página {i}"/></div>'
        for i, (name, _) in enumerate(imgs, start=1)
    )
    fpath.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <title>{ch_label} - Vagabond</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <div class="chapter-header">
    <h1>{ch_label}</h1>
    <p>Vagabond — Takehiko Inoue</p>
  </div>
{img_tags}
</body>
</html>''', encoding="utf-8")

# ---- nav.xhtml ----
nav_items_html = "\n".join(
    f'      <li><a href="chapter-{ch:02d}.xhtml">{label}</a></li>' for ch, label, _ in chapters
)
(OEBPS / "nav.xhtml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="pt-BR">
<head>
  <meta charset="utf-8"/>
  <title>Sumário</title>
  <link rel="stylesheet" type="text/css" href="styles.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Sumário</h1>
    <ol>
      <li><a href="cover.xhtml">Capa</a></li>
{nav_items_html}
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
(OEBPS / "toc.ncx").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{IDENTIFIER}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>Vagabond — Vol. 1 (Capítulos 1–10)</text></docTitle>
  <navMap>
    <navPoint id="cover" playOrder="1">
      <navLabel><text>Capa</text></navLabel>
      <content src="cover.xhtml"/>
    </navPoint>
{ncx_points}
  </navMap>
</ncx>''', encoding="utf-8")

# ---- content.opf ----
manifest_lines = []
manifest_lines.append('    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
manifest_lines.append('    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
manifest_lines.append('    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
manifest_lines.append('    <item id="css" href="styles.css" media-type="text/css"/>')
manifest_lines.append('    <item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>')
for ch, _, _ in chapters:
    manifest_lines.append(f'    <item id="ch{ch:02d}" href="chapter-{ch:02d}.xhtml" media-type="application/xhtml+xml"/>')
for item_id, href, mtype in image_items:
    if item_id == "cover-image":
        continue
    manifest_lines.append(f'    <item id="{item_id}" href="{href}" media-type="{mtype}"/>')

manifest_str = "\n".join(manifest_lines)
spine_str = "    <itemref idref=\"cover\"/>\n" + "\n".join(f'    <itemref idref="ch{ch:02d}"/>' for ch, _, _ in chapters)

(OEBPS / "content.opf").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="pt-BR">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="bookid">{IDENTIFIER}</dc:identifier>
    <dc:title>Vagabond — Vol. 1 (Capítulos 1–10)</dc:title>
    <dc:creator id="author">Takehiko Inoue</dc:creator>
    <dc:language>pt-BR</dc:language>
    <dc:description>Mangá Vagabond de Takehiko Inoue — Compilação dos capítulos 1 a 10, organizado para leitura em ordem. Imagens otimizadas (JPEG 92% 4:4:4 optimize, sem redimensionamento, perda visual mínima).</dc:description>
    <dc:publisher>Seanime — Edição local</dc:publisher>
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
if OUT_EPUB.exists():
    OUT_EPUB.unlink()

with zipfile.ZipFile(OUT_EPUB, "w", compresslevel=9) as z:
    z.write(BUILD / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
    for path in BUILD.rglob("*"):
        if path.is_file() and path.name != "mimetype":
            arc = path.relative_to(BUILD).as_posix()
            # Para versão otimizada, usa DEFLATED em tudo (ganho extra de ~1-2% mesmo em JPEG)
            z.write(path, arc, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

print(f"\nEPUB criado: {OUT_EPUB}")
print(f"Tamanho: {OUT_EPUB.stat().st_size/1024/1024:.2f} MB")
with zipfile.ZipFile(OUT_EPUB) as z:
    print(f"Total arquivos no EPUB: {len(z.namelist())}")
    for n in z.namelist()[:10]:
        print(" ", n)
    print(" ...")
    for n in z.namelist()[-5:]:
        print(" ", n)
for ch, label, imgs in chapters:
    print(f"  {label}: {len(imgs)} páginas")

# Validação rápida com epubcheck se disponível? Apenas estrutura
print("\nEPUB pronto (JPEG 92% 4:4:4 optimize, perda visual mínima, tamanho reduzido ~55%).")
