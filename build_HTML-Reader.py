# -*- coding: utf-8 -*-
"""
Manga Library Generator — Single File
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gera UM ÚNICO HTML com todas as imagens embutidas em Base64.
Cada capítulo é uma seção interna — sem arquivos externos.

Uso:
    python manga_singlefile_gen.py

Configuração:
    BASE_DIR    → pasta raiz com subpastas de capítulos
    OUTPUT_FILE → caminho do HTML final
"""

import os
import re
import base64
import mimetypes

# ===== CONFIG (defaults — sobrescritos via input em main() ou via main.py) =====
BASE_DIR = ""
OUTPUT_FILE = ""
IMG_EXTS    = (".png", ".jpg", ".jpeg", ".webp", ".avif")
MANGA_TITLE = ""
# ==================

mimetypes.add_type("image/webp", ".webp")

def natural_sort(files):
    def key(f):
        return [int(c) if c.isdigit() else c.lower()
                for c in re.split(r'(\d+)', f)]
    return sorted(files, key=key)

def get_images(folder):
    return natural_sort([
        f for f in os.listdir(folder)
        if f.lower().endswith(IMG_EXTS)
    ])

def get_chapters(base_dir):
    return natural_sort([
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith('_')
    ])

def to_data_uri(path):
    mt, _ = mimetypes.guess_type(path)
    if not mt:
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        mt = {"jpg":"image/jpeg","jpeg":"image/jpeg",
              "png":"image/png","webp":"image/webp"}.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mt};base64,{data}"

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Zen+Antique+Soft&family=Syne:wght@400;600;700;800&family=Syne+Mono&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#111010;--bg2:#1a1917;--bg3:#222120;
  --border:#333230;--border2:#3d3b38;
  --text:#e8e3da;--text2:#9b9590;--text3:#5e5a55;
  --accent:#e85d3a;--accent-bg:rgba(232,93,58,.12);
  --font-display:'Zen Antique Soft',serif;
  --font-ui:'Syne',sans-serif;
  --font-mono:'Syne Mono',monospace;
  --nav-h:52px;--pager-h:56px;
  --ease:cubic-bezier(.22,.68,0,1.2);--r:3px;
  --shadow:0 2px 12px rgba(0,0,0,.4);
  --shadow-lg:0 8px 40px rgba(0,0,0,.6);
}
html{scroll-behavior:smooth;height:100%}
body{font-family:var(--font-ui);background:var(--bg);color:var(--text);
  min-height:100%;-webkit-font-smoothing:antialiased;overscroll-behavior:none}
a{color:inherit;text-decoration:none}
button{font-family:var(--font-ui);cursor:pointer}
img{display:block}
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:9000;opacity:.7;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E")}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}

/* ── views ── */
#view-library,#view-reader{display:none}
#view-library.active,#view-reader.active{display:block}

/* ══════════════════════════════════════════════════════
   INDEX
══════════════════════════════════════════════════════ */
.lib-nav{position:sticky;top:0;z-index:100;height:var(--nav-h);background:var(--bg);
  border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 1rem;gap:.75rem}
.lib-nav-logo{font-family:var(--font-display);font-size:1.05rem;color:var(--accent);
  letter-spacing:.04em;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lib-nav-badge{font-family:var(--font-mono);font-size:.6rem;color:var(--text3);
  letter-spacing:.12em;text-transform:uppercase;background:var(--bg3);padding:3px 8px;
  border-radius:12px;border:1px solid var(--border);white-space:nowrap}

.lib-hero{padding:2.5rem 1.25rem 1.5rem;position:relative;overflow:hidden}
.lib-hero::before{content:'';position:absolute;top:-60px;right:-60px;width:240px;height:240px;
  background:radial-gradient(circle,rgba(232,93,58,.18) 0%,transparent 70%);pointer-events:none}
.lib-hero-eyebrow{font-family:var(--font-mono);font-size:.6rem;letter-spacing:.22em;
  text-transform:uppercase;color:var(--accent);margin-bottom:.6rem}
.lib-hero-title{font-family:var(--font-display);font-size:clamp(1.8rem,8vw,3.2rem);
  line-height:1.05;color:var(--text);letter-spacing:-.01em}
.lib-hero-meta{font-size:.7rem;color:var(--text3);margin-top:.75rem;
  font-family:var(--font-mono);letter-spacing:.1em}

/* toolbar */
.lib-toolbar{padding:.65rem 1rem;position:sticky;top:var(--nav-h);z-index:90;
  background:var(--bg);border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:flex-end;gap:.6rem}
.view-toggle{display:flex;gap:2px;flex-shrink:0;background:var(--bg2);
  border:1px solid var(--border);border-radius:var(--r);padding:2px}
.view-btn{display:flex;align-items:center;justify-content:center;width:32px;height:32px;
  background:none;border:none;border-radius:calc(var(--r) - 1px);color:var(--text3);
  transition:background .15s,color .15s;-webkit-tap-highlight-color:transparent}
.view-btn.active{background:var(--bg3);color:var(--accent)}
.view-btn:not(.active):active{background:var(--bg3);color:var(--text2)}
@media(hover:hover){.view-btn:not(.active):hover{color:var(--text2)}}

/* grid */
.lib-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));
  gap:1px;background:var(--border);border-top:1px solid var(--border)}
@media(min-width:480px){.lib-grid{grid-template-columns:repeat(auto-fill,minmax(160px,1fr))}}
@media(min-width:768px){.lib-grid{grid-template-columns:repeat(auto-fill,minmax(200px,1fr))}}

/* list mode */
.lib-grid.list-mode{grid-template-columns:1fr;gap:0;background:none}
.lib-grid.list-mode .card{flex-direction:row;align-items:center;height:72px;
  border-bottom:1px solid var(--border);animation:none}
.lib-grid.list-mode .card-cover{aspect-ratio:unset;width:48px;height:68px;
  flex-shrink:0;border-radius:1px;margin:2px 0 2px 2px}
.lib-grid.list-mode .card-cover-grad{display:none}
.lib-grid.list-mode .card-badge{top:4px;left:4px;font-size:.5rem;padding:1px 4px}
.lib-grid.list-mode .card-body{padding:0 .85rem;display:flex;align-items:center;
  gap:.75rem;flex:1;min-width:0}
.lib-grid.list-mode .card-title{font-size:.85rem;font-weight:600;flex:1}
.lib-grid.list-mode .card-sub{font-size:.62rem;white-space:nowrap;flex-shrink:0}
.lib-grid.list-mode .card::after{content:'';display:block;width:5px;height:5px;
  border-right:1.5px solid var(--text3);border-top:1.5px solid var(--text3);
  transform:rotate(45deg);margin-right:1rem;flex-shrink:0;transition:border-color .15s}
.lib-grid.list-mode .card:active::after{border-color:var(--accent)}
@media(hover:hover){.lib-grid.list-mode .card:hover::after{border-color:var(--accent)}}

/* card */
.card{background:var(--bg2);cursor:pointer;display:flex;flex-direction:column;
  transition:background .15s;-webkit-tap-highlight-color:transparent;
  animation:fadeUp .35s ease both}
.card:active{background:var(--bg3)}
@media(hover:hover){
  .card:hover{background:var(--bg3)}
  .card:hover .card-cover-img{transform:scale(1.04)}
  .card:hover .card-badge{background:var(--accent);color:#fff;border-color:var(--accent)}
}
.card-cover{aspect-ratio:2/3;overflow:hidden;position:relative;background:var(--bg3)}
.card-cover-img{width:100%;height:100%;object-fit:cover;transition:transform .4s var(--ease)}
.card-cover-grad{position:absolute;inset:0;
  background:linear-gradient(to top,rgba(17,16,16,.85) 0%,transparent 50%)}
.card-badge{position:absolute;top:8px;left:8px;font-family:var(--font-mono);
  font-size:.55rem;letter-spacing:.1em;background:rgba(17,16,16,.75);color:var(--text2);
  padding:2px 6px;border-radius:2px;backdrop-filter:blur(4px);
  border:1px solid var(--border2);transition:background .2s,color .2s,border-color .2s}
.card-body{padding:.6rem .7rem .7rem;flex:1}
.card-title{font-size:.8rem;font-weight:600;color:var(--text);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:.2rem}
.card-sub{font-family:var(--font-mono);font-size:.6rem;color:var(--text3);letter-spacing:.06em}
.no-results{grid-column:1/-1;text-align:center;padding:4rem 1rem;color:var(--text3);
  font-size:.8rem;font-family:var(--font-mono);letter-spacing:.1em;background:var(--bg)}
.lib-footer{text-align:center;padding:2rem 1rem;font-family:var(--font-mono);
  font-size:.58rem;color:var(--text3);letter-spacing:.14em;text-transform:uppercase;
  border-top:1px solid var(--border)}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}

/* ══════════════════════════════════════════════════════
   READER
══════════════════════════════════════════════════════ */
.reader-section{min-height:100vh;min-height:100dvh}

.ch-topnav{position:sticky;top:0;z-index:300;height:var(--nav-h);background:var(--bg);
  border-bottom:1px solid var(--border);display:flex;align-items:center;
  padding:0 .75rem;gap:.5rem}
.icon-btn{display:flex;align-items:center;justify-content:center;width:36px;height:36px;
  background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);
  color:var(--text2);transition:border-color .2s,color .2s,background .2s;
  flex-shrink:0;-webkit-tap-highlight-color:transparent}
.icon-btn:active{border-color:var(--accent);color:var(--accent);background:var(--accent-bg)}
@media(hover:hover){.icon-btn:hover{border-color:var(--accent);color:var(--accent)}}
.icon-btn.lit{background:var(--accent-bg);border-color:var(--accent);color:var(--accent)}
.ch-title-wrap{flex:1;min-width:0}
.ch-manga-name{font-family:var(--font-mono);font-size:.55rem;color:var(--text3);
  letter-spacing:.1em;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ch-chapter-name{font-size:.82rem;font-weight:600;color:var(--text);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ch-pg-counter{font-family:var(--font-mono);font-size:.62rem;color:var(--text3);
  letter-spacing:.06em;white-space:nowrap;flex-shrink:0}

.ch-settings{position:sticky;top:var(--nav-h);z-index:280;background:var(--bg2);
  border-bottom:1px solid var(--border);overflow:hidden;max-height:0;
  transition:max-height .28s ease}
.ch-settings.open{max-height:200px}
.ch-settings-inner{padding:.75rem 1rem;display:flex;flex-direction:column;gap:.65rem}
.ch-settings-row{display:flex;align-items:center;gap:.4rem;flex-wrap:wrap}
.ch-settings-label{font-family:var(--font-mono);font-size:.58rem;color:var(--text3);
  letter-spacing:.12em;text-transform:uppercase;width:52px;flex-shrink:0}
.mode-btn{padding:5px 11px;font-family:var(--font-mono);font-size:.65rem;
  letter-spacing:.06em;background:var(--bg3);border:1px solid var(--border);
  border-radius:var(--r);color:var(--text2);transition:all .15s;
  -webkit-tap-highlight-color:transparent}
.mode-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.mode-btn:active:not(.active){background:var(--bg)}
@media(hover:hover){.mode-btn:not(.active):hover{border-color:var(--accent);color:var(--accent)}}
.ch-arr-btn{padding:5px 11px;font-family:var(--font-mono);font-size:.65rem;
  background:var(--bg3);border:1px solid var(--border);border-radius:var(--r);
  color:var(--text2);transition:all .15s;-webkit-tap-highlight-color:transparent}
.ch-arr-btn:disabled{opacity:.3;cursor:default}
.ch-arr-btn:not(:disabled):active{background:var(--accent);color:#fff;border-color:var(--accent)}

.scroll-progress{position:fixed;top:var(--nav-h);left:0;height:2px;
  background:var(--accent);z-index:200;pointer-events:none;transition:width .1s linear}

/* readers */
.reader-scroll{display:none;flex-direction:column;align-items:center;gap:2px;padding:2px 0}
.reader-scroll.active{display:flex}
.reader-scroll .page{width:100%;max-width:800px;position:relative}
.reader-scroll .page img{width:100%;height:auto}
.reader-scroll .page-num{position:absolute;bottom:6px;right:8px;font-family:var(--font-mono);
  font-size:.52rem;color:rgba(255,255,255,.35);letter-spacing:.05em;pointer-events:none}

.reader-single{display:none;height:calc(100vh - var(--nav-h) - var(--pager-h));
  height:calc(100dvh - var(--nav-h) - var(--pager-h));align-items:center;
  justify-content:center;overflow:hidden;user-select:none;-webkit-user-select:none}
.reader-single.active{display:flex}
.reader-single .page{display:none;width:100%;height:100%;align-items:center;justify-content:center}
.reader-single .page.active{display:flex}
.reader-single .page img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain}

.reader-double{display:none;height:calc(100vh - var(--nav-h) - var(--pager-h));
  height:calc(100dvh - var(--nav-h) - var(--pager-h));align-items:center;
  justify-content:center;overflow:hidden;user-select:none;-webkit-user-select:none}
.reader-double.active{display:flex}
.reader-double .pair{display:none;width:100%;height:100%;align-items:center;justify-content:center;gap:2px}
.reader-double .pair.active{display:flex}
.reader-double .pair .page{flex:1;height:100%;display:flex;align-items:center;justify-content:center}
.reader-double .pair .page img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain}
.reader-double.rtl .pair{flex-direction:row-reverse}

/* rtl toggle badge */
.rtl-badge{font-family:var(--font-mono);font-size:.48rem;letter-spacing:.08em;
  position:absolute;bottom:4px;right:4px;line-height:1;opacity:.7;pointer-events:none}
.icon-btn{position:relative}
.icon-btn.rtl-active .rtl-badge{color:var(--accent);opacity:1}

.tap-zone{position:absolute;top:0;bottom:0;width:28%;z-index:10;-webkit-tap-highlight-color:transparent}
.tap-prev{left:0}.tap-next{right:0}
.tap-zone:active::after{content:'';position:absolute;inset:0;background:rgba(255,255,255,.04)}

/* RTL: inverte tap zones no modo página/dupla */
.rtl-mode .tap-prev{left:auto;right:0}
.rtl-mode .tap-next{right:auto;left:0}

.pager-bar{height:var(--pager-h);background:var(--bg);border-top:1px solid var(--border);
  display:flex;align-items:center;padding:0 .75rem;gap:.5rem}
.pager-bar.hidden{display:none}
.pager-main{display:flex;align-items:center;gap:.5rem;flex:1}
.pg-btn{display:flex;align-items:center;justify-content:center;width:40px;height:38px;
  background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);
  color:var(--text2);transition:all .15s;flex-shrink:0;-webkit-tap-highlight-color:transparent}
.pg-btn:active{background:var(--accent);border-color:var(--accent);color:#fff}
@media(hover:hover){.pg-btn:hover{background:var(--accent);border-color:var(--accent);color:#fff}}
.pg-btn:disabled{opacity:.25;cursor:default;pointer-events:none}
.progress-track{flex:1;height:4px;background:var(--bg3);border-radius:2px;
  cursor:pointer;position:relative}
.progress-track::before{content:'';position:absolute;inset:-12px 0}
.progress-fill{height:100%;background:var(--accent);border-radius:2px;
  transition:width .1s;pointer-events:none}
.pager-info{font-family:var(--font-mono);font-size:.62rem;color:var(--text3);
  letter-spacing:.06em;min-width:44px;text-align:center;flex-shrink:0}

.filmstrip{position:fixed;bottom:var(--pager-h);left:0;right:0;z-index:250;
  background:rgba(17,16,16,.97);border-top:1px solid var(--border2);
  display:flex;gap:3px;padding:6px;overflow-x:auto;
  transform:translateY(100%);transition:transform .28s var(--ease);
  -webkit-overflow-scrolling:touch;overscroll-behavior-x:contain}
.filmstrip.scroll-mode{bottom:0}
.filmstrip.open{transform:translateY(0)}
.filmstrip::-webkit-scrollbar{display:none}
.film-thumb{flex-shrink:0;width:44px;border:1.5px solid transparent;border-radius:2px;
  background:none;padding:0;position:relative;overflow:hidden;
  transition:border-color .15s;-webkit-tap-highlight-color:transparent}
.film-thumb.cur{border-color:var(--accent)}
.film-thumb img{width:44px;height:60px;object-fit:cover}
.film-thumb span{position:absolute;bottom:0;left:0;right:0;background:rgba(17,16,16,.8);
  color:var(--text3);font-family:var(--font-mono);font-size:.45rem;
  text-align:center;padding:2px 0;letter-spacing:.04em}
.film-thumb.cur span{color:var(--accent)}

@media(max-height:500px) and (orientation:landscape){:root{--nav-h:40px;--pager-h:44px}}
@supports(padding:env(safe-area-inset-bottom)){
  .pager-bar{padding-bottom:env(safe-area-inset-bottom);
    height:calc(var(--pager-h) + env(safe-area-inset-bottom))}
  .filmstrip{padding-bottom:calc(6px + env(safe-area-inset-bottom))}
}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  BUILD
# ══════════════════════════════════════════════════════════════════════════════

def build_single_html(base_dir, output_file=None, manga_title=None):
    manga_title = manga_title or MANGA_TITLE or os.path.basename(os.path.abspath(base_dir))
    if not output_file:
        output_file = os.path.join(base_dir, f"{os.path.basename(os.path.abspath(base_dir))}fuka.html")
    chapters = get_chapters(base_dir)
    if not chapters:
        print("Nenhuma subpasta encontrada.")
        return

    total_ch = len(chapters)
    print(f"Encontrados {total_ch} capítulos. Embutindo imagens em Base64...\n")

    # ── Coleta + converte ────────────────────────────────────────────────────
    chapters_data = []
    total_images = sum(len(get_images(os.path.join(base_dir, ch))) for ch in chapters)
    processed_images = 0
    for ch in chapters:
        folder = os.path.join(base_dir, ch)
        imgs   = get_images(folder)
        images = []
        for img in imgs:
            print(f"Encoding {ch}/{img}... ({processed_images + 1}/{total_images})")
            uri = to_data_uri(os.path.join(folder, img))
            images.append({"uri": uri})
            processed_images += 1
        chapters_data.append({"name": ch, "images": images})
        print(f"  [OK] {ch}: {len(imgs)} imagens")

    # ── LIBRARY CARDS ────────────────────────────────────────────────────────
    cards_html = ""
    for i, ch in enumerate(chapters_data):
        cover = ch["images"][0]["uri"] if ch["images"] else ""
        count = len(ch["images"])
        delay = min(i * 0.03, 0.5)
        img_tag = (
            f'<img class="card-cover-img" src="{cover}" alt="{ch["name"]}" loading="lazy"/>'
            if cover else
            '<div class="card-cover-img" style="display:flex;align-items:center;justify-content:center;font-size:2rem;color:var(--text3)">📖</div>'
        )
        cards_html += f"""
    <div class="card" onclick="openChapter({i})" data-name="{ch['name'].lower()}"
         style="animation-delay:{delay:.2f}s" role="button" tabindex="0"
         onkeydown="if(event.key==='Enter')openChapter({i})">
      <div class="card-cover">
        {img_tag}
        <div class="card-cover-grad"></div>
        <span class="card-badge">#{i+1:02d}</span>
      </div>
      <div class="card-body">
        <p class="card-title">{ch['name']}</p>
        <p class="card-sub">{count} págs.</p>
      </div>
    </div>"""

    # ── READER SECTIONS ──────────────────────────────────────────────────────
    all_sections = ""
    for ci, ch in enumerate(chapters_data):
        total = len(ch["images"])

        scroll_pages = ""
        single_pages = ""
        double_pairs = ""
        thumbs       = ""

        for pi, img in enumerate(ch["images"]):
            uri = img["uri"]
            scroll_pages += f'<div class="page" data-idx="{pi}"><img loading="lazy" src="{uri}" alt="p{pi+1}"/><span class="page-num">{pi+1}</span></div>\n'
            single_pages += f'<div class="page"><img src="{uri}" alt="p{pi+1}"/></div>\n'
            thumbs       += f'<button class="film-thumb" onclick="chGoTo({ci},{pi})" title="p{pi+1}"><img src="{uri}" loading="lazy"/><span>{pi+1}</span></button>\n'

        for pi in range(0, total, 2):
            r = f'<div class="page"><img src="{ch["images"][pi+1]["uri"]}" alt="p{pi+2}"/></div>' if pi+1 < total else '<div class="page"></div>'
            double_pairs += f'<div class="pair" data-pair="{pi}"><div class="page"><img src="{ch["images"][pi]["uri"]}" alt="p{pi+1}"/></div>{r}</div>\n'

        prev_btn = (f'<button class="ch-arr-btn" onclick="openChapter({ci-1})">← Anterior</button>'
                    if ci > 0 else '<button class="ch-arr-btn" disabled>← Anterior</button>')
        next_btn = (f'<button class="ch-arr-btn" onclick="openChapter({ci+1})">Próximo →</button>'
                    if ci < total_ch-1 else '<button class="ch-arr-btn" disabled>Próximo →</button>')

        all_sections += f"""
<div class="reader-section" id="chapter-{ci}" style="display:none">
  <nav class="ch-topnav">
    <button class="icon-btn" onclick="goLibrary()" aria-label="Biblioteca">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
    </button>
    <div class="ch-title-wrap">
      <div class="ch-manga-name">{manga_title}</div>
      <div class="ch-chapter-name">{ch['name']}</div>
    </div>
    <span class="ch-pg-counter" id="counter-{ci}">1/{total}</span>
    <button class="icon-btn" id="rtlbtn-{ci}" onclick="toggleRTL({ci})" aria-label="Direção de leitura" title="Alternar direção (RTL/LTR)">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 18l6-6-6-6"/><path d="M3 6h10a4 4 0 0 1 0 8H3"/>
      </svg>
      <span class="rtl-badge">LTR</span>
    </button>
    <button class="icon-btn" id="stbtn-{ci}" onclick="toggleStrip({ci})" aria-label="Miniaturas">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="5" height="7" rx="1"/><rect x="9.5" y="3" width="5" height="7" rx="1"/><rect x="16" y="3" width="5" height="7" rx="1"/></svg>
    </button>
    <button class="icon-btn" id="menubtn-{ci}" onclick="toggleSettings({ci})" aria-label="Configurações">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
    </button>
  </nav>

  <div class="ch-settings" id="settings-{ci}">
    <div class="ch-settings-inner">
      <div class="ch-settings-row">
        <span class="ch-settings-label">Modo</span>
        <button class="mode-btn active" data-mode="scroll" onclick="chSetMode({ci},'scroll',this)">↕ Scroll</button>
        <button class="mode-btn"        data-mode="single" onclick="chSetMode({ci},'single',this)">□ Página</button>
        <button class="mode-btn"        data-mode="double" onclick="chSetMode({ci},'double',this)">⊟ Dupla</button>
      </div>
      <div class="ch-settings-row">
        <span class="ch-settings-label">Direção</span>
        <button class="mode-btn" id="rtlmbtn-{ci}" onclick="toggleRTL({ci})">→ LTR (Ocidental)</button>
      </div>
      <div class="ch-settings-row">
        <span class="ch-settings-label">Cap.</span>
        {prev_btn}
        {next_btn}
      </div>
    </div>
  </div>

  <div class="scroll-progress" id="prog-{ci}" style="width:0"></div>

  <div style="position:relative">
    <div class="reader-scroll active" id="rs-{ci}">{scroll_pages}</div>
    <div class="reader-single" id="rp-{ci}">
      <div class="tap-zone tap-prev" onclick="chStep({ci},-1)"></div>
      <div class="tap-zone tap-next" onclick="chStep({ci},1)"></div>
      {single_pages}
    </div>
    <div class="reader-double" id="rd-{ci}">
      <div class="tap-zone tap-prev" onclick="chStep({ci},-2)"></div>
      <div class="tap-zone tap-next" onclick="chStep({ci},2)"></div>
      {double_pairs}
    </div>
  </div>

  <div class="pager-bar hidden" id="pager-{ci}">
    <div class="pager-main">
      <button class="pg-btn" id="prev-{ci}" onclick="chStep({ci},-1)" aria-label="Anterior">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
      </button>
      <div class="progress-track" id="track-{ci}" onclick="chSeek({ci},event)">
        <div class="progress-fill" id="fill-{ci}" style="width:0%"></div>
      </div>
      <button class="pg-btn" id="next-{ci}" onclick="chStep({ci},1)" aria-label="Próximo">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
      </button>
    </div>
    <span class="pager-info" id="pinfo-{ci}">1/{total}</span>
  </div>

  <div class="filmstrip scroll-mode" id="strip-{ci}">{thumbs}</div>
</div>"""

    # ── JAVASCRIPT ───────────────────────────────────────────────────────────
    chapter_sizes = [len(ch["images"]) for ch in chapters_data]

    js = f"""
const CH_SIZES = {chapter_sizes};
const TOTAL_CH = {total_ch};
let curCh = -1;
const S   = {{}};

function gs(ci) {{
  if (!S[ci]) S[ci] = {{ mode:'scroll', cur:0, stripOpen:false, settingsOpen:false, rtl:false }};
  return S[ci];
}}

/* ── LIBRARY / READER ── */
function goLibrary() {{
  if (curCh >= 0) _hideChapter(curCh);
  curCh = -1;
  document.getElementById('view-library').classList.add('active');
  document.getElementById('view-reader').classList.remove('active');
  window.scrollTo(0,0);
  history.replaceState(null,'','#');
}}

function openChapter(ci) {{
  if (curCh >= 0) _hideChapter(curCh);
  curCh = ci;
  document.getElementById('view-library').classList.remove('active');
  document.getElementById('view-reader').classList.add('active');
  document.getElementById('chapter-'+ci).style.display = '';
  _applyMode(ci, gs(ci).mode);
  _updateUI(ci);
  _setupObserver(ci);
  /* aplica estado RTL salvo */
  if (gs(ci).rtl) {{
    const rd=document.getElementById('rd-'+ci);
    if(rd){{rd.classList.add('rtl');rd.classList.add('rtl-mode');}}
    const rp=document.getElementById('rp-'+ci);
    if(rp) rp.classList.add('rtl-mode');
    const btn=document.getElementById('rtlbtn-'+ci);
    if(btn){{btn.classList.add('rtl-active');const b=btn.querySelector('.rtl-badge');if(b)b.textContent='RTL';}}
    const mbtn=document.getElementById('rtlmbtn-'+ci);
    if(mbtn){{mbtn.classList.add('active');mbtn.textContent='← RTL (Oriental)';}}
  }}
  window.scrollTo(0,0);
  history.replaceState(null,'','#ch'+ci);
}}

function _hideChapter(ci) {{
  const el = document.getElementById('chapter-'+ci);
  if (el) el.style.display = 'none';
  ['strip-','settings-'].forEach(p => {{
    const e = document.getElementById(p+ci);
    if (e) e.classList.remove('open');
  }});
  gs(ci).settingsOpen = false;
  gs(ci).stripOpen    = false;
}}

/* ── SETTINGS ── */
function toggleSettings(ci) {{
  const el  = document.getElementById('settings-'+ci);
  const btn = document.getElementById('menubtn-'+ci);
  gs(ci).settingsOpen = !gs(ci).settingsOpen;
  el.classList.toggle('open', gs(ci).settingsOpen);
  btn.classList.toggle('lit',  gs(ci).settingsOpen);
}}

/* ── MODE ── */
function chSetMode(ci, mode, btn) {{
  gs(ci).mode = mode;
  _applyMode(ci, mode);
  document.querySelectorAll('#settings-'+ci+' .mode-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  try {{ localStorage.setItem('manga_mode', mode); }} catch(e) {{}}
}}

function _applyMode(ci, mode) {{
  const rs    = document.getElementById('rs-'+ci);
  const rp    = document.getElementById('rp-'+ci);
  const rd    = document.getElementById('rd-'+ci);
  const pager = document.getElementById('pager-'+ci);
  const strip = document.getElementById('strip-'+ci);
  const prog  = document.getElementById('prog-'+ci);
  const open  = gs(ci).stripOpen;

  rs.classList.remove('active');
  rp.classList.remove('active');
  rd.classList.remove('active');

  if (mode === 'scroll') {{
    rs.classList.add('active');
    pager.classList.add('hidden');
    strip.className = 'filmstrip scroll-mode' + (open ? ' open' : '');
    if (prog) prog.style.display = 'block';
  }} else if (mode === 'single') {{
    rp.classList.add('active');
    pager.classList.remove('hidden');
    strip.className = 'filmstrip' + (open ? ' open' : '');
    if (prog) prog.style.display = 'none';
    _activateSingle(ci, gs(ci).cur);
  }} else {{
    rd.classList.add('active');
    pager.classList.remove('hidden');
    strip.className = 'filmstrip' + (open ? ' open' : '');
    if (prog) prog.style.display = 'none';
    _activateDouble(ci, gs(ci).cur);
  }}
}}

/* ── NAVIGATE ── */
function chGoTo(ci, idx) {{
  const total = CH_SIZES[ci];
  idx = Math.max(0, Math.min(total-1, idx));
  gs(ci).cur = idx;
  const mode = gs(ci).mode;
  if (mode === 'scroll') {{
    document.querySelectorAll('#rs-'+ci+' .page')[idx]?.scrollIntoView({{behavior:'smooth',block:'start'}});
  }} else if (mode === 'single') {{
    _activateSingle(ci, idx);
  }} else {{
    _activateDouble(ci, idx);
  }}
  _updateUI(ci);
  if (gs(ci).stripOpen) _syncStrip(ci);
}}

function chStep(ci, d) {{ chGoTo(ci, gs(ci).cur + d); }}

function chSeek(ci, e) {{
  const r = document.getElementById('track-'+ci).getBoundingClientRect();
  chGoTo(ci, Math.round(Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)) * (CH_SIZES[ci]-1)));
}}

function _activateSingle(ci, idx) {{
  document.querySelectorAll('#rp-'+ci+' .page').forEach((p,i) => p.classList.toggle('active', i===idx));
}}
function _activateDouble(ci, idx) {{
  const pi = Math.floor(idx/2)*2;
  document.querySelectorAll('#rd-'+ci+' .pair').forEach(p => p.classList.toggle('active', parseInt(p.dataset.pair)===pi));
}}

/* ── UI ── */
function _updateUI(ci) {{
  const total = CH_SIZES[ci], cur = gs(ci).cur;
  const $ = id => document.getElementById(id);
  const c = $('counter-'+ci), pi=$('pinfo-'+ci), f=$('fill-'+ci), p=$('prev-'+ci), n=$('next-'+ci);
  if (c) c.textContent = (cur+1)+'/'+total;
  if (pi) pi.textContent = (cur+1)+'/'+total;
  if (f)  f.style.width  = (total>1 ? cur/(total-1)*100 : 100)+'%';
  if (p)  p.disabled = cur===0;
  if (n)  n.disabled = cur>=total-1;
}}

/* ── FILMSTRIP ── */
function toggleStrip(ci) {{
  const strip=$('strip-'+ci), btn=$('stbtn-'+ci);
  gs(ci).stripOpen = !gs(ci).stripOpen;
  strip.classList.toggle('open', gs(ci).stripOpen);
  btn.classList.toggle('lit',   gs(ci).stripOpen);
  if (gs(ci).stripOpen) _syncStrip(ci);
}}
function _syncStrip(ci) {{
  const cur = gs(ci).cur;
  document.querySelectorAll('#strip-'+ci+' .film-thumb').forEach((t,i)=>t.classList.toggle('cur',i===cur));
  document.querySelectorAll('#strip-'+ci+' .film-thumb')[cur]
    ?.scrollIntoView({{behavior:'smooth',inline:'center',block:'nearest'}});
}}

/* ── RTL TOGGLE ── */
function toggleRTL(ci) {{
  gs(ci).rtl = !gs(ci).rtl;
  const rtl = gs(ci).rtl;

  /* double-page reader: inverte ordem visual das páginas no par */
  const rd = document.getElementById('rd-'+ci);
  if (rd) rd.classList.toggle('rtl', rtl);

  /* aplica rtl-mode no container para inverter tap zones */
  const rp = document.getElementById('rp-'+ci);
  if (rp) rp.classList.toggle('rtl-mode', rtl);
  const rd2 = document.getElementById('rd-'+ci);
  if (rd2) rd2.classList.toggle('rtl-mode', rtl);

  /* botão na topnav */
  const btn = document.getElementById('rtlbtn-'+ci);
  if (btn) {{
    btn.classList.toggle('rtl-active', rtl);
    const badge = btn.querySelector('.rtl-badge');
    if (badge) badge.textContent = rtl ? 'RTL' : 'LTR';
  }}

  /* botão no painel de settings */
  const mbtn = document.getElementById('rtlmbtn-'+ci);
  if (mbtn) {{
    mbtn.classList.toggle('active', rtl);
    mbtn.textContent = rtl ? '← RTL (Oriental)' : '→ LTR (Ocidental)';
  }}

  try {{ localStorage.setItem('manga_rtl', rtl ? '1' : '0'); }} catch(e) {{}}
}}
function $( id){{return document.getElementById(id);}}

/* ── SCROLL OBSERVER ── */
const _obs = {{}};
function _setupObserver(ci) {{
  if (_obs[ci]) return;
  const rs = document.getElementById('rs-'+ci);
  const prog = document.getElementById('prog-'+ci);
  const io = new IntersectionObserver(entries => {{
    if (gs(ci).mode !== 'scroll') return;
    entries.forEach(en => {{
      if (en.isIntersecting) {{
        const idx = parseInt(en.target.dataset.idx);
        if (!isNaN(idx)) {{ gs(ci).cur=idx; _updateUI(ci); if(gs(ci).stripOpen)_syncStrip(ci); }}
      }}
    }});
  }}, {{rootMargin:'-40% 0px -40% 0px',threshold:0}});
  rs.querySelectorAll('.page').forEach(p => io.observe(p));
  if (prog) window.addEventListener('scroll', ()=>{{
    if (curCh!==ci||gs(ci).mode!=='scroll') return;
    const d=document.documentElement;
    prog.style.width=Math.min(d.scrollTop/(d.scrollHeight-d.clientHeight)*100,100)+'%';
  }},{{passive:true}});
  _obs[ci]=io;
}}

/* ── VIEW TOGGLE ── */
function setLibView(v) {{
  document.getElementById('lib-grid').classList.toggle('list-mode', v==='list');
  document.getElementById('vbtn-grid').classList.toggle('active', v==='grid');
  document.getElementById('vbtn-list').classList.toggle('active', v==='list');
  try {{ localStorage.setItem('lib_view', v); }} catch(e) {{}}
}}

/* ── KEYBOARD ── */
document.addEventListener('keydown', e=>{{
  if (e.target.tagName==='INPUT'||curCh<0) return;
  const mode=gs(curCh).mode, step=mode==='double'?2:1;
  const rtl=gs(curCh).rtl;
  const fwd = rtl ? -step : step, bwd = rtl ? step : -step;
  if(e.key==='ArrowRight'||e.key==='ArrowDown'){{e.preventDefault();chStep(curCh,fwd);}}
  if(e.key==='ArrowLeft' ||e.key==='ArrowUp'  ){{e.preventDefault();chStep(curCh,bwd);}}
  if(e.key==='Escape') goLibrary();
  if(e.key==='f'||e.key==='F'){{
    if(!document.fullscreenElement)document.documentElement.requestFullscreen().catch(()=>{{}});
    else document.exitFullscreen();
  }}
  if(e.key==='t'||e.key==='T') toggleStrip(curCh);
  if(e.key==='s'||e.key==='S') toggleSettings(curCh);
  if(e.key==='[') openChapter(Math.max(0,curCh-1));
  if(e.key===']') openChapter(Math.min(TOTAL_CH-1,curCh+1));
}});

/* ── SWIPE ── */
let _tx=null,_ty=null;
document.addEventListener('touchstart',e=>{{_tx=e.changedTouches[0].clientX;_ty=e.changedTouches[0].clientY;}},{{passive:true}});
document.addEventListener('touchend',e=>{{
  if(_tx===null||curCh<0)return;
  const dx=e.changedTouches[0].clientX-_tx,dy=e.changedTouches[0].clientY-_ty;
  if(Math.abs(dx)>Math.abs(dy)&&Math.abs(dx)>45&&gs(curCh).mode!=='scroll') {{
    const step=gs(curCh).mode==='double'?2:1;
    const rtl=gs(curCh).rtl;
    /* swipe esquerda (dx<0): avança em LTR, recua em RTL */
    const d = dx<0 ? (rtl?-step:step) : (rtl?step:-step);
    chStep(curCh,d);
  }}
  _tx=null;_ty=null;
}},{{passive:true}});

/* ── INIT ── */
(function(){{
  try{{
    const m=localStorage.getItem('manga_mode');
    if(m&&['scroll','single','double'].includes(m)) for(let i=0;i<TOTAL_CH;i++) gs(i).mode=m;
    const v=localStorage.getItem('lib_view');
    if(v==='list') setLibView('list');
    const r=localStorage.getItem('manga_rtl');
    if(r==='1') for(let i=0;i<TOTAL_CH;i++) gs(i).rtl=true;
  }}catch(e){{}}
  const h=location.hash;
  if(h&&h.startsWith('#ch')){{
    const ci=parseInt(h.slice(3));
    if(!isNaN(ci)&&ci>=0&&ci<TOTAL_CH){{openChapter(ci);return;}}
  }}
  goLibrary();
}})();
"""

    # ── HTML FINAL ───────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover"/>
<meta name="mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"/>
<meta name="theme-color" content="#111010"/>
<title>{manga_title}</title>
<style>{CSS}</style>
</head>
<body>

<!-- ═══ LIBRARY ═══ -->
<div id="view-library">
  <nav class="lib-nav">
    <span class="lib-nav-logo">{manga_title}</span>
    <span class="lib-nav-badge">{total_ch} cap.</span>
  </nav>
  <header class="lib-hero">
    <p class="lib-hero-eyebrow">Biblioteca · Mangá</p>
    <h1 class="lib-hero-title">{manga_title}</h1>
    <p class="lib-hero-meta">{total_ch} capítulos disponíveis</p>
  </header>
  <div class="lib-toolbar">
    <div class="view-toggle" role="group" aria-label="Modo de visualização">
      <button class="view-btn active" id="vbtn-grid" onclick="setLibView('grid')" title="Grade">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
      </button>
      <button class="view-btn" id="vbtn-list" onclick="setLibView('list')" title="Lista">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
      </button>
    </div>
  </div>
  <main class="lib-grid" id="lib-grid">{cards_html}</main>
  <footer class="lib-footer">{manga_title} &mdash; Arquivo único gerado localmente</footer>
</div>

<!-- ═══ READER ═══ -->
<div id="view-reader">{all_sections}</div>

<script>{js}</script>
</body>
</html>"""

    print(f"\nEscrevendo {output_file} ...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"Concluído! Tamanho: {size_mb:.1f} MB")
    print(f"Abra no navegador: {output_file}")

# ─────────────────────────────────────────────────────────────────────────────
def main(base_dir=None, output_file=None, manga_title=None):
    """Entry-point interativo: permite uso via main.py ou standalone."""
    base_dir = (base_dir or input("Base directory: ").strip()
                or BASE_DIR or os.getcwd())
    if not os.path.isdir(base_dir):
        print(f"[✗] Pasta não encontrada: {base_dir}")
        return
    default_out = os.path.join(
        base_dir, f"{os.path.basename(os.path.abspath(base_dir))}fuka.html")
    output_file = output_file or input(
        f"Arquivo de saída [{default_out}]: ").strip() or default_out
    title_default = (manga_title or MANGA_TITLE
                     or os.path.basename(os.path.abspath(base_dir)))
    manga_title = (input(f"Título [{title_default}]: ").strip()
                   if manga_title is None else manga_title) or title_default
    build_single_html(base_dir, output_file, manga_title)


if __name__ == "__main__":
    main()

