# EPUBMangaExtractor

Ferramentas para baixar capítulos de `Vagabond` do DemonicScans e gerar dois formatos de leitura local:

- EPUB com imagens convertidas para JPEG otimizado.
- HTML único com a biblioteca e todas as imagens embutidas em Base64.

Use o projeto somente para conteúdo que você tenha direito de baixar e armazenar.

## Requisitos

- Python 3.10 ou mais recente.
- Google Chrome ou Chromium para a coleta via Selenium.
- Conexão com a internet para o downloader.

Instale as dependências Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

O `webdriver-manager` baixa e seleciona o ChromeDriver quando necessário. Se o Chrome não estiver instalado ou não puder ser iniciado em modo headless, a coleta via Selenium falhará; nesse caso o script tenta usar `requests` e BeautifulSoup.

## Fluxo recomendado

### 1. Baixar capítulos

Por padrão, o downloader salva os capítulos em `~/Downloads/Vagabond`:

```bash
python download-demonicscans.py
```

Para escolher o capítulo inicial e a quantidade:

```bash
python download-demonicscans.py 10 5
```

Também é possível passar uma URL de capítulo:

```bash
python download-demonicscans.py \
	https://demonicscans.org/title/Vagabond/chapter/10/1 5
```

A estrutura gerada é semelhante a:

```text
Vagabond/
├── chapter 1/
│   ├── 001.jpg
│   └── ...
└── chapter 2/
		└── ...
```

O downloader ignora imagens já existentes com mais de 1 KiB e tenta domínios alternativos quando a imagem principal não responde.

### 2. Gerar o EPUB

O arquivo [build_epub.py](build_epub.py) usa atualmente estes caminhos fixos:

- Entrada: `/home/val/Downloads/Vagabond`
- Capa: `/home/val/Downloads/Vagabond/capa.png`
- Saída: `/home/val/Downloads/Vagabond/Vagabond - Vol 1 - Capitulos 1-10.epub`

Depois de baixar os capítulos e colocar `capa.png` na pasta de entrada, execute:

```bash
python build_epub.py
```

O script procura pastas no formato `Capítulo 01`, `Capítulo 02`, etc. Se os capítulos vierem do downloader, renomeie ou organize as pastas para esse padrão antes de executar o gerador. As páginas AVIF são convertidas para JPEG em qualidade 92, sem redimensionamento.

### 3. Gerar o leitor HTML

Execute o gerador e informe a pasta raiz que contém as subpastas dos capítulos:

```bash
python build_HTML-Reader.py
```

Quando solicitado, informe, por exemplo:

```text
/home/val/Downloads/Vagabond
```

O resultado será salvo na própria pasta como `<nome-da-pasta>fuka.html`. Ele pode ser aberto diretamente no navegador, sem servidor local e sem dependências JavaScript externas. O arquivo final pode ficar grande, pois todas as imagens são embutidas em Base64.

## Dependências

As dependências estão em [requirements.txt](requirements.txt):

- `requests`: download das imagens e páginas.
- `beautifulsoup4`: fallback de coleta HTML.
- `selenium`: coleta das imagens em navegador headless.
- `webdriver-manager`: gerenciamento do ChromeDriver.
- `tqdm`: barra de progresso opcional do download.
- `Pillow`: conversão e otimização das imagens no EPUB.

Os scripts de geração usam apenas a biblioteca padrão além de Pillow; o leitor HTML gerado não precisa instalar nada no computador que fará a leitura.

## Observações

- O site, os seletores HTML e os domínios de imagens podem mudar; se a coleta retornar zero páginas, verifique `CSS_SELECTOR` e as URLs em `download-demonicscans.py`.
- O EPUB é montado diretamente com `zipfile` e XML, sem `EbookLib`.
- O HTML incorpora as imagens originais, enquanto o EPUB converte as páginas para JPEG.
- Respeite os termos de uso do site e os direitos autorais da obra.
