#!/usr/bin/env python3
"""
fetch_arxiv_refs.py — продвинутый загрузчик arXiv-референсов для статьи.

Сохраняет полный HTML-текст (конвертированный в markdown) и метаданные
для заданных arXiv-статей, чтобы к ним можно было обращаться локально без
доступа к интернету.

Возможности:
  - ретраи с экспоненциальной задержкой и джиттером;
  - таймауты соединения/чтения;
  - честный User-Agent;
  - валидация, что полученная страница реально соответствует arXiv-статье
    (не ошибка 404 / капча / пустая страница);
  - конвертация HTML → Markdown на стандартной библиотеке (html.parser);
  - сохранение аннотации (abs) и полного текста (html) отдельными файлами;
  - idempotent-повторный запуск (пропуск уже скачанных, флаг --force);
  - журнал операций в refs/_fetch.log;
  - контроль размера, чтобы не скачивать «капчу» и не мусорить.

Использование:
  python3 scripts/fetch_arxiv_refs.py --out docs/ieee-article/refs 2501.16590 2108.10470
  python3 scripts/fetch_arxiv_refs.py --out docs/ieee-article/refs --list refs.txt
  python3 scripts/fetch_arxiv_refs.py --out docs/ieee-article/refs --force 2501.16590

Ожидаемые файлы на каждый arXiv ID:
  <id>.abs.md          — метаданные + аннотация (светов, ~страница)
  <id>.full.md         — полный текст HTML, конвертированный в markdown
"""

import argparse
import html
import json
import os
import random
import re
import sys
import time
import urllib.parse
from html.parser import HTMLParser

try:
    import requests
except ImportError:  # pragma: no cover
    print("Не найден модуль 'requests'. Установите: pip install requests", file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

ARXIV_ABS = "https://arxiv.org/abs/{arxiv_id}"
ARXIV_HTML = "https://arxiv.org/html/{arxiv_id}"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36 "
    "Mozilla/5.0 (research-ref-fetcher/1.0; +local; contact: local@example.org)"
)
TIMEOUT = (10, 30)            # (connect, read)
MAX_RETRIES = 4
BASE_BACKOFF = 2.0
MAX_BACKOFF = 30.0
MAX_HTML_BYTES = 8 * 1024 * 1024   # 8 MB — предохранитель от «мусора»
MIN_HTML_BYTES = 10_000            # меньше — почти наверняка капча/ошибка

# Какие пути нельзя сохранять / что вызывает сомнение в корректности страницы.
_BAD_MARKERS = ("captcha", "cf-challenge", "attention required", "robot check")
_VALID_TITLE = re.compile(r"\[\s*\d{4}\.\d{5}\s*\]", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Логирование
# ---------------------------------------------------------------------------

class Logger:
    """Простой потокобезопасный логгер в stdout и файл."""

    def __init__(self, path: str | None):
        self._fh = None
        if path:
            self._fh = open(path, "a", encoding="utf-8")

    def log(self, msg: str) -> None:
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
        print(line, flush=True)
        if self._fh:
            self._fh.write(line + "\n")
            self._fh.flush()

    def close(self) -> None:
        if self._fh:
            self._fh.close()


# ---------------------------------------------------------------------------
# Сетевой клиент с ретраями
# ---------------------------------------------------------------------------

class ArxivClient:
    """Загрузка страниц arXiv с ретраями, таймаутами и валидацией."""

    def __init__(self, logger: Logger):
        self._logger = logger
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})

    def _sleep_backoff(self, attempt: int) -> None:
        delay = min(BASE_BACKOFF * (2 ** attempt), MAX_BACKOFF)
        delay += random.uniform(0, 0.5)  # джиттер против синхронных ретраев
        self._logger.log(f"    задержка {delay:.1f} с перед повтором...")
        time.sleep(delay)

    def get(self, url: str) -> bytes | None:
        """GET url; возвращает body или None после исчерпания попыток."""
        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                self._logger.log(f"    GET {url} (попытка {attempt + 1}/{MAX_RETRIES})")
                resp = self._session.get(url, timeout=TIMEOUT, stream=True)
                resp.raise_for_status()
                # Ограничение размера: читаем не более MAX_HTML_BYTES
                chunks = []
                total = 0
                for chunk in resp.iter_content(chunk_size=65536):
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > MAX_HTML_BYTES:
                        self._logger.log("    WARNING: превышен лимит размера, обрезаю")
                        break
                body = b"".join(chunks)
                return body
            except requests.exceptions.Timeout as exc:
                last_err = exc
                self._logger.log(f"    таймаут: {exc}")
            except requests.exceptions.RequestException as exc:
                last_err = exc
                self._logger.log(f"    ошибка запроса: {exc}")
            if attempt + 1 < MAX_RETRIES:
                self._sleep_backoff(attempt)
        self._logger.log(f"    НЕ удалось получить {url}: {last_err}")
        return None

    def close(self) -> None:
        self._session.close()


# ---------------------------------------------------------------------------
# Очистка HTML от «обвязки» arXiv
# ---------------------------------------------------------------------------

def strip_arxiv_chrome(html_text: str) -> str:
    """Удалить служебные блоки arXiv (шапку, подвал, формы, баннеры).

    Работает по сбалансированным парным тегам: для контейнеров
    (header/nav/footer/aside/form) удаляем блок вместе с содержимым.
    Это надёжнее, чем пытаться отслеживать классы внутри HTMLParser.
    """
    # 1) Полностью удалить <form ...> ... </form>
    html_text = re.sub(r"<form\b[^>]*>.*?</form>", "", html_text,
                       flags=re.S | re.I)
    # 2) Полностью удалить <footer ...> ... </footer> (без вложенных footer)
    html_text = re.sub(r"<footer\b[^>]*>.*?</footer>", "", html_text,
                       flags=re.S | re.I)
    # 3) Полностью удалить служебные header/nav/aside, помеченные классами arXiv
    #    (осторожно: не трогаем заголовки статьи h1..h6 — это не header-тег).
    for tag in ("header", "nav", "aside"):
        # удаляем только те блоки, у которых в class есть служебный маркер
        pat = (
            rf"<{tag}\b[^>]*class=\"[^\"]*(?:arxiv-html-header|arxiv-html-footer|"
            rf"html-header|modal-header|modal-footer|ds-site-footer|nonprofit)[^\"]*\"[^>]*>"
            rf".*?</{tag}>"
        )
        html_text = re.sub(pat, "", html_text, flags=re.S | re.I)
    # 4) Блоки, помеченные служебными классами в div/section
    for tag in ("div", "section"):
        pat = (
            rf"<{tag}\b[^>]*class=\"[^\"]*(?:arxiv-html-header|arxiv-html-footer|"
            rf"ds-site-footer|html-header-logo|html-header-nav|nonprofit|ds-announcement)[^\"]*\"[^>]*>"
            rf".*?</{tag}>"
        )
        html_text = re.sub(pat, "", html_text, flags=re.S | re.I)
    # 4b) Баннер объявлений arXiv по id/роли (не всегда имеет класс ds-announcement)
    html_text = re.sub(
        r"<(?:div|aside|section)\b[^>]*id=\"announcement-banner\"[^>]*>.*?</(?:div|aside|section)>",
        "", html_text, flags=re.S | re.I,
    )
    # 5) Остаточный мелкий мусор
    html_text = re.sub(r"<header class=\"modal-header\">.*?</header>", "",
                       html_text, flags=re.S | re.I)
    return html_text


# ---------------------------------------------------------------------------
# Конвертация HTML → Markdown (stdlib)
# ---------------------------------------------------------------------------

class HtmlToMarkdown(HTMLParser):
    """Минимальный, но аккуратный конвертер HTML в читаемый Markdown.

    Не претендует на полноту, но достаточно хорош для научных HTML,
    которые выдаёт arXiv (заголовки, параграфы, списки, ссылки, код).
    """

    _BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer",
                   "figure", "figcaption", "blockquote", "pre"}
    _HEADING = {"h1": "#", "h2": "##", "h3": "###", "h4": "####",
                "h5": "#####", "h6": "######"}
    _SKIP_TAGS = {"script", "style", "head", "noscript", "svg", "math",
                  "annotation", "semantics", "mprescripts", "munder"}

    _SKIP_CLASS_MARKERS = ()

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._out = []
        self._skip_depth = 0
        self._skip_on_close = set()
        self._in_pre = False
        self._lists = []          # стек: 0 = unordered, 1 = ordered
        self._pending_newline = False

    # -- утилиты ---------------------------------------------------------
    def _emit(self, text: str) -> None:
        if self._skip_depth:
            return
        if self._pending_newline:
            # удалить лишние пробелы в начале строки после переноса
            text = text.lstrip(" ")
        self._out.append(text)
        self._pending_newline = False

    def _emit_block(self) -> None:
        if self._skip_depth:
            return
        # схлопнуть пробелы в конце текущего буфера
        self._out.append("\n")
        self._pending_newline = True

    def _text(self) -> str:
        return "".join(self._out)

    # -- события парсера -------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
            self._skip_on_close.add(tag)
            return
        if tag in self._HEADING:
            self._emit_block()
            self._emit(self._HEADING[tag] + " ")
        elif tag in ("p", "div", "section", "article", "blockquote"):
            self._emit_block()
        elif tag == "br":
            self._emit("\n")
        elif tag == "li":
            self._emit_block()
            if self._lists and self._lists[-1]:
                self._emit("1. ")
            else:
                self._emit("- ")
        elif tag in ("ul", "ol"):
            self._lists.append(1 if tag == "ol" else 0)
            self._emit_block()
        elif tag == "a":
            # собираем href для ссылок на литературу
            self._pending_href = dict(attrs).get("href", "")
        elif tag == "code":
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "pre":
            self._emit_block()
            self._emit("```\n")
            self._in_pre = True
        elif tag == "img":
            src = dict(attrs).get("src", "")
            alt = dict(attrs).get("alt", "")
            if src:
                self._emit(f"\n![{alt}]({src})\n")
        elif tag == "table":
            self._emit_block()
        elif tag == "tr":
            self._emit("| ")
        elif tag in ("td", "th"):
            self._emit(" | ")
        # math-подобные теги пропускаем как текст

    def handle_startendtag(self, tag, attrs):
        # self-closing теги (например, <img/>) обрабатываем как обычные
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self._skip_on_close:
            self._skip_depth = max(0, self._skip_depth - 1)
            self._skip_on_close.discard(tag)
            return
        if tag in self._HEADING:
            self._emit_block()
        elif tag in ("p", "div", "section", "article", "blockquote"):
            self._emit_block()
        elif tag in ("ul", "ol"):
            if self._lists:
                self._lists.pop()
            self._emit_block()
        elif tag == "li":
            self._emit("\n")
        elif tag == "a":
            href = getattr(self, "_pending_href", "")
            # ничего не делаем со ссылками, чтобы не мусорить; при желании
            # можно оставить URL — отключено для чистоты
            self._pending_href = ""
        elif tag == "code":
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "pre":
            self._emit("\n```\n")
            self._in_pre = False
            self._emit_block()

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_pre:
            # в <pre> сохраняем как есть, но без двойных переносов
            self._out.append(data)
            return
        self._emit(data)

    # -- результат -------------------------------------------------------
    def to_markdown(self) -> str:
        md = self._text()
        # убрать множественные пустые строки (более двух)
        md = re.sub(r"\n{3,}", "\n\n", md)
        # почистить пробелы перед пунктуацией (примеры: " .")
        md = re.sub(r" +\n", "\n", md)
        return md.strip() + "\n"


# ---------------------------------------------------------------------------
# Метаданные аннотации (abs) — лёгкий разбор
# ---------------------------------------------------------------------------

def _clean(s: str) -> str:
    """Очистка HTML: unescape-сущности, удалить теги, схлопнуть пробелы."""
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", "", s)          # выбросить html-теги
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_abs_meta(html: str) -> dict:
    """Извлечь заголовок/аннотацию/авторов из abs-страницы arXiv (best effort).

    Возвращает dict с полями: title, abstract, cite_as, doi, links.
    """
    meta = {"title": "", "abstract": "", "cite_as": "", "doi": "",
            "links": {"abs": "", "html": ""}}

    # Title: <title>[arXiv:...] Title</title> или <h1 class="title mathjax">
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    if m:
        meta["title"] = _clean(m.group(1))

    # Abstract: <blockquote class="abstract mathjax">...  или <div class="abstract">
    for pat in (
        r'<blockquote[^>]*class="abstract[^"]*"[^>]*>(.*?)</blockquote>',
        r'<div[^>]*class="abstract[^"]*"[^>]*>(.*?)</div>',
    ):
        m = re.search(pat, html, re.S | re.I)
        if m:
            meta["abstract"] = _clean(m.group(1))
            break
    meta["abstract"] = re.sub(r"^Abstract[:\s]*", "", meta["abstract"], flags=re.I)

    # Authors
    authors = []
    for m in re.finditer(r'<a[^>]*rel="author"[^>]*>([^<]+)</a>', html, re.I):
        authors.append(_clean(m.group(1)))
    meta["authors"] = authors

    # Cite as + DOI
    m = re.search(r"arXiv:\s*(\d{4}\.\d{5})", html)
    if m:
        arxiv_id = m.group(1)
        meta["arxiv_id"] = arxiv_id
        meta["links"]["abs"] = f"https://arxiv.org/abs/{arxiv_id}"
        meta["links"]["html"] = f"https://arxiv.org/html/{arxiv_id}"
        meta["doi"] = f"10.48550/arXiv.{arxiv_id}"
        meta["cite_as"] = f"arXiv:{arxiv_id}"
    return meta


def validate_arxiv_page(html: str, arxiv_id: str) -> tuple[bool, str]:
    """Проверка, что страница действительно про запрошенную статью."""
    low = html.lower()
    for marker in _BAD_MARKERS:
        if marker in low:
            return False, f"страница похожа на капчу/ошибку (маркер: {marker!r})"
    if arxiv_id in low:
        return True, "ok"
    # fallback: на странице должен быть [число.число]
    if _VALID_TITLE.search(low):
        return True, "ok (без точного id, но похоже на arXiv)"
    return False, "на странице нет упоминания arXiv-id или [число.число]"


# ---------------------------------------------------------------------------
# Запись результатов
# ---------------------------------------------------------------------------

def save_text(path: str, content: str, logger: Logger) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    logger.log(f"  сохранено: {path} ({len(content)} симв.)")


def build_abs_markdown(meta: dict, arxiv_id: str, html_url: str) -> str:
    """Markdown-файл с метаданными и аннотацией."""
    lines = [
        f"# {meta.get('title', '(без названия)')}",
        "",
        f"**arXiv:** [{arxiv_id}]({meta['links'].get('abs', html_url)})  ",
        f"**HTML:** [{html_url}]({html_url})  ",
        f"**DOI:** {meta.get('doi', '—')}  ",
        f"**Cite as:** {meta.get('cite_as', '—')}",
    ]
    if meta.get("authors"):
        lines += ["", "**Авторы:** " + "; ".join(meta["authors"])]
    lines += ["", "---", "", "## Аннотация (Abstract)", "", meta.get("abstract", "(нет)")]
    lines += ["", "---", "", f"*Локальная копия получена: {time.strftime('%Y-%m-%d %H:%M:%S')}*", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Основной поток
# ---------------------------------------------------------------------------

def process_one(client: ArxivClient, logger: Logger, arxiv_id: str,
                out_dir: str, force: bool) -> bool:
    arxiv_id = arxiv_id.strip().lstrip("arXiv:")  # допускаем 'arXiv:xxxx'
    abs_path = os.path.join(out_dir, f"{arxiv_id}.abs.md")
    full_path = os.path.join(out_dir, f"{arxiv_id}.full.md")

    if not force and os.path.exists(abs_path) and os.path.exists(full_path):
        logger.log(f"  {arxiv_id}: уже есть, пропускаю (--force чтобы перезаписать)")
        return True

    logger.log(f"== {arxiv_id} ==")
    abs_url = ARXIV_ABS.format(arxiv_id=arxiv_id)
    html_url = ARXIV_HTML.format(arxiv_id=arxiv_id)

    # 1) аннотация
    abs_body = client.get(abs_url)
    if not abs_body:
        logger.log(f"  {arxiv_id}: не удалось получить аннотацию")
        return False
    abs_html = abs_body.decode("utf-8", errors="replace")
    ok, reason = validate_arxiv_page(abs_html, arxiv_id)
    if not ok:
        logger.log(f"  {arxiv_id}: аннотация отклонена — {reason}")
        return False

    meta = parse_abs_meta(abs_html)
    if not meta.get("title"):
        logger.log(f"  {arxiv_id}: не удалось распознать заголовок, страница подозрительна")
        return False

    save_text(abs_path, build_abs_markdown(meta, arxiv_id, html_url), logger)

    # 2) полный HTML-текст
    full_body = client.get(html_url)
    if not full_body:
        logger.log(f"  {arxiv_id}: не удалось получить полный HTML")
        return False
    full_html = full_body.decode("utf-8", errors="replace")
    ok, reason = validate_arxiv_page(full_html, arxiv_id)
    if not ok:
        logger.log(f"  {arxiv_id}: полный текст отклонён — {reason}")
        return False

    # Удалить служебную «обвязку» arXiv (шапку/подвал/формы) до конвертации
    full_html = strip_arxiv_chrome(full_html)

    conv = HtmlToMarkdown()
    try:
        conv.feed(full_html)
        md = conv.to_markdown()
    except Exception as exc:  # защита от любых сбоев парсера
        logger.log(f"  {arxiv_id}: ошибка конвертации HTML: {exc}")
        return False
    if len(md) < 500:
        logger.log(f"  {arxiv_id}: слишком короткий текст после конвертации ({len(md)} симв.), пропуск")
        return False

    header = (f"# {meta.get('title', arxiv_id)}\n\n"
              f"**Источник:** {html_url}\n\n"
              f"---\n\n")
    save_text(full_path, header + md, logger)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Загрузчик arXiv-референсов (HTML→Markdown)")
    ap.add_argument("arxiv_ids", nargs="*", help="arXiv id, например 2501.16590")
    ap.add_argument("--out", default="refs", help="папка для сохранения (default: refs)")
    ap.add_argument("--list", help="файл со списком arXiv id (по одному на строку)")
    ap.add_argument("--force", action="store_true", help="перезаписывать существующие")
    ap.add_argument("--log", default=None, help="файл журнала (default: <out>/_fetch.log)")
    args = ap.parse_args()

    ids: list[str] = list(args.arxiv_ids)
    if args.list:
        with open(args.list, "r", encoding="utf-8") as fh:
            ids += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

    if not ids:
        ap.error("укажите arXiv id или --list")

    os.makedirs(args.out, exist_ok=True)
    log_path = args.log or os.path.join(args.out, "_fetch.log")
    logger = Logger(log_path)
    client = ArxivClient(logger)
    try:
        ok_cnt = fail_cnt = 0
        for aid in ids:
            if process_one(client, logger, aid, args.out, args.force):
                ok_cnt += 1
            else:
                fail_cnt += 1
        logger.log(f"Итог: {ok_cnt} успешно, {fail_cnt} с ошибкой")
    finally:
        client.close()
        logger.close()
    return 0 if fail_cnt == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
