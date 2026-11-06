#!/usr/bin/env python3
"""Build recipes PDF from JSON + compressed assets/pdf/*.jpg."""

from __future__ import annotations

import html
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES_JSON = ROOT / "recipes-a-cheremisin-fitness.json"
MAP_JSON = ROOT / "assets" / "recipe-image-map.json"
PDF_ASSETS = ROOT / "assets" / "pdf"
OUT_PDF = ROOT / "recipes-a-cheremisin-fitness.pdf"
ARTIFACTS_PDF = Path("/opt/cursor/artifacts/recipes-a-cheremisin-fitness.pdf")
ARTIFACTS_PDF_ALT = Path("/opt/cursor/artifacts/PP-recepty-a-cheremisin-fitness.pdf")


def clean_caption(caption: str, title: str) -> str:
    lines = caption.split("\n")
    if lines:
        first = lines[0].strip().rstrip(":")
        if first.lower() == title.lower() or (
            first.lower() == "рецепт" and title.lower() != "рецепт"
        ):
            lines = lines[1:]
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        low = s.lower()
        if not s:
            out.append("")
            continue
        if set(s) <= {"_", "—", "-", " "}:
            continue
        if (
            "@a.cheremisin" in low
            or "подписывай" in low
            or "больше рецепт" in low
            or "больше контент" in low
        ):
            continue
        out.append(ln.rstrip())
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)


def caption_to_html(text: str) -> str:
    blocks: list[str] = []
    for para in re.split(r"\n\s*\n", text.strip()):
        bullet_lines = [
            l for l in para.split("\n") if l.strip().startswith(("-", "•", "·"))
        ]
        non_empty = [l for l in para.split("\n") if l.strip()]
        if (
            non_empty
            and len(bullet_lines) >= max(1, len(non_empty) - 1)
            and len(bullet_lines) >= 2
        ):
            items = [
                f"<li>{html.escape(re.sub(r'^[-•·]\\s*', '', l.strip()))}</li>"
                for l in para.split("\n")
                if l.strip()
            ]
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue
        labeled: list[str] = []
        other: list[str] = []
        for l in para.split("\n"):
            s = l.strip()
            if not s:
                continue
            if re.match(
                r"^(ингредиент|приготовлен|процесс|состав|рецепт|коржи|крем|соус|начинк|собираем|готовк|для начинк)",
                s,
                re.I,
            ):
                other.append(s)
            elif re.search(r"\s[-—:]\s*\d|\s[-—]\s", s) and len(s) < 80:
                labeled.append(s)
            else:
                other.append(s)
        if labeled and not other:
            blocks.append(
                "<ul>"
                + "".join(f"<li>{html.escape(x)}</li>" for x in labeled)
                + "</ul>"
            )
            continue
        escaped = "<br>".join(
            html.escape(l.strip()) for l in para.split("\n") if l.strip()
        )
        escaped = re.sub(
            r"^(Ингредиенты[^:<]*|Приготовление|Процесс|Состав[^:<]*|Рецепт[^:<]*|Коржи[^:<]*|Крем|Соус|Начинка|Готовка|Собираем бургеры)(:?)",
            r"<strong>\1\2</strong>",
            escaped,
            flags=re.I | re.M,
        )
        escaped = re.sub(
            r"(К[бБ][жЖ][уУ][^\n<]*)",
            r'<span class="macros-inline">\1</span>',
            escaped,
        )
        if escaped:
            blocks.append(f"<p>{escaped}</p>")
    return "\n".join(blocks)


def img_uri(filename: str) -> str:
    path = PDF_ASSETS / filename
    if not path.exists():
        path = ROOT / "assets" / filename
    return path.resolve().as_uri()


def ingredients_only_html(caption: str, title: str) -> str:
    cleaned = clean_caption(caption, title)
    parts = re.split(
        r"\n\s*\n(?=Приготовление|Процесс|Готовка)",
        cleaned,
        maxsplit=1,
        flags=re.I,
    )
    return caption_to_html(parts[0])


def render_steps_html(steps: list[dict]) -> str:
    parts: list[str] = ['<div class="steps"><h3>Приготовление по шагам</h3>']
    for idx, step in enumerate(steps, 1):
        parts.append(
            f'<div class="step">'
            f'<div class="step-label">Шаг {idx}</div>'
            f'<img src="{img_uri(step["file"])}" alt="Шаг {idx}">'
            f'<p class="step-text">{html.escape(step["text"])}</p>'
            f"</div>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def load_all_steps() -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for path in sorted((ROOT / "assets").glob("recipe-*-steps.json")):
        m = re.search(r"recipe-(\d+)-steps\.json$", path.name)
        if not m:
            continue
        result[m.group(1)] = json.loads(path.read_text(encoding="utf-8"))
    return result


def build_html(
    recipes: list[dict], mapping: dict, recipe_steps: dict[str, list[dict]]
) -> str:
    toc_items: list[str] = []
    sections: list[str] = []
    for i, r in enumerate(recipes, 1):
        title = r["title"]
        macros = r.get("macros") or ""
        if "чебурек" in title.lower() and "кбжу)" in macros.lower():
            macros = "КБЖУ на 1 чебурек: 269 ккал, 22 г белка, 9 г жира, 23 г углеводов"
        steps = recipe_steps.get(str(i)) or []
        if steps:
            body_html = ingredients_only_html(r["caption"], title)
            macros_match = re.search(r"К[бБ][жЖ][уУ][^\n]*", r["caption"])
            if macros_match:
                body_html += (
                    f'<p><span class="macros-inline">'
                    f"{html.escape(macros_match.group(0))}</span></p>"
                )
            body_html += render_steps_html(steps)
            featured = " recipe-featured recipe-with-steps"
        else:
            body_html = caption_to_html(clean_caption(r["caption"], title))
            featured = ""
        toc_items.append(
            f'<li><a href="#r{i}"><span class="n">{i}.</span> {html.escape(title)}</a></li>'
        )
        media = ""
        meta = mapping.get(str(i)) or mapping.get(i)
        if meta:
            media = (
                f'<figure class="hero-photo">'
                f'<img src="{img_uri(meta["file"])}" alt="{html.escape(title)}">'
                f"<figcaption>Готовое блюдо</figcaption>"
                f"</figure>"
            )
            if not featured:
                featured = " recipe-featured"
        sections.append(
            f"""
    <article class="recipe{featured}" id="r{i}">
      <header>
        <div class="num">{i:02d}</div>
        <div class="head-text">
          <h2>{html.escape(title)}</h2>
          <p class="macros">{html.escape(macros)}</p>
        </div>
      </header>
      {media}
      <div class="body">{body_html}</div>
      <p class="source"><a href="{html.escape(r["url"])}">Рилс в Instagram</a></p>
    </article>"""
        )

    n_img = sum(1 for i in range(1, len(recipes) + 1) if mapping.get(str(i)))
    n_stepped = len(recipe_steps)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>ПП-рецепты — @a.cheremisin_fitness</title>
<style>
@page {{ size: A4; margin: 16mm 14mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: "Noto Sans", "DejaVu Sans", sans-serif; color: #1a1f1c; font-size: 10.5pt; line-height: 1.45; margin: 0; }}
.cover {{ page-break-after: always; min-height: 240mm; display: flex; flex-direction: column; justify-content: center; padding: 24mm 8mm;
  background: radial-gradient(ellipse at 20% 0%, #e8f2ea 0%, transparent 55%), #fafaf7; }}
.cover .brand {{ font-size: 12pt; letter-spacing: 0.08em; text-transform: uppercase; color: #2f6b45; font-weight: 700; margin-bottom: 18px; }}
.cover h1 {{ font-size: 34pt; line-height: 1.1; margin: 0 0 16px; font-weight: 800; color: #14201a; }}
.cover .lead {{ font-size: 12.5pt; color: #3d4a42; max-width: 420px; margin: 0 0 28px; }}
.cover .meta {{ border-top: 1px solid #c9d5cc; padding-top: 16px; color: #4b5563; font-size: 10pt; }}
h2.toc-title {{ font-size: 18pt; margin: 0 0 14px; color: #14201a; }}
.toc {{ page-break-after: always; columns: 2; column-gap: 28px; list-style: none; padding: 0; margin: 0; }}
.toc li {{ break-inside: avoid; margin: 0 0 7px; font-size: 9.5pt; }}
.toc a {{ color: #1a1f1c; text-decoration: none; }}
.toc .n {{ color: #2f6b45; font-weight: 700; margin-right: 4px; }}
.recipe {{ break-inside: avoid; margin: 0 0 16px; padding: 12px; border: 1px solid #d7e0d9; border-radius: 10px; background: #fff; }}
.recipe-featured, .recipe-with-steps {{ break-inside: auto; }}
.recipe header {{ display: flex; gap: 12px; align-items: flex-start; margin-bottom: 10px; }}
.recipe .num {{ flex: 0 0 auto; width: 34px; height: 34px; border-radius: 8px; background: #2f6b45; color: #fff; font-weight: 800; font-size: 11pt; display: flex; align-items: center; justify-content: center; }}
.recipe h2 {{ margin: 0 0 4px; font-size: 13pt; line-height: 1.25; color: #14201a; }}
.macros {{ margin: 0; color: #2f6b45; font-weight: 600; font-size: 9.5pt; }}
.macros-inline {{ display: inline-block; margin-top: 4px; color: #2f6b45; font-weight: 600; }}
.hero-photo {{ margin: 0 0 10px; padding: 0; }}
.hero-photo img {{ display: block; width: 100%; max-height: 70mm; object-fit: cover; border-radius: 8px; }}
.hero-photo figcaption {{ margin-top: 4px; font-size: 8pt; color: #6b7280; }}
.body p {{ margin: 0 0 8px; }}
.body ul {{ margin: 4px 0 10px 18px; padding: 0; }}
.body li {{ margin: 0 0 3px; }}
.body strong {{ color: #1f3d2c; }}
.steps {{ margin-top: 12px; }}
.steps h3 {{ margin: 0 0 10px; font-size: 12pt; color: #1f3d2c; }}
.step {{ break-inside: avoid; margin: 0 0 14px; padding: 10px; border: 1px solid #e5ebe6; border-radius: 8px; background: #fbfcfb; }}
.step-label {{ font-size: 9pt; font-weight: 700; color: #2f6b45; margin-bottom: 6px; letter-spacing: 0.04em; text-transform: uppercase; }}
.step img {{ display: block; width: 100%; max-height: 72mm; object-fit: cover; border-radius: 6px; margin-bottom: 8px; }}
.step-text {{ margin: 0; font-size: 10pt; color: #1a1f1c; }}
.source {{ margin: 8px 0 0; font-size: 8.5pt; }}
.source a {{ color: #6b7280; text-decoration: none; }}
.note {{ margin-top: 20px; font-size: 9pt; color: #6b7280; }}
</style>
</head>
<body>
  <section class="cover">
    <div class="brand">@a.cheremisin_fitness</div>
    <h1>ПП-рецепты<br>из Instagram</h1>
    <p class="lead">Сборник из {len(recipes)} рецептов с ингредиентами, способом приготовления, КБЖУ и визуализациями блюд.</p>
    <div class="meta">
      <div><strong>{len(recipes)} рецепта</strong> · {n_img} фото блюд · пошаговые кадры у {n_stepped}</div>
      <div>instagram.com/a.cheremisin_fitness</div>
    </div>
  </section>
  <h2 class="toc-title">Содержание</h2>
  <ol class="toc">{"".join(toc_items)}</ol>
  {"".join(sections)}
  <p class="note">Тексты — из описаний рилсов автора. Макросы как в оригинальных captions. Изображения сгенерированы как визуализации блюд.</p>
</body>
</html>"""


def print_pdf(html_path: Path, pdf_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "timeout",
            "120",
            "google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--user-data-dir={tmp}",
            "--allow-file-access-from-files",
            "--virtual-time-budget=20000",
            "--run-all-compositor-stages-before-draw",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
        subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        raise RuntimeError(f"PDF was not created: {pdf_path}")


def rewrite_compat(pdf_path: Path) -> None:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    tmp = pdf_path.with_suffix(".tmp.pdf")
    with open(tmp, "wb") as f:
        writer.write(f)
    tmp.replace(pdf_path)


def main() -> None:
    recipes = json.loads(RECIPES_JSON.read_text(encoding="utf-8"))
    raw_map = json.loads(MAP_JSON.read_text(encoding="utf-8"))
    recipe_steps = load_all_steps()
    html_doc = build_html(recipes, raw_map, recipe_steps)
    html_path = Path("/tmp/recipes_compat.html")
    html_path.write_text(html_doc, encoding="utf-8")
    print(f"html_kb={html_path.stat().st_size / 1024:.1f}")
    print(f"stepped_recipes={sorted(recipe_steps)}")
    for key, steps in sorted(recipe_steps.items()):
        print(f"  recipe {key}: {len(steps)} steps")
    print_pdf(html_path, OUT_PDF)
    rewrite_compat(OUT_PDF)
    ARTIFACTS_PDF.parent.mkdir(parents=True, exist_ok=True)
    data = OUT_PDF.read_bytes()
    ARTIFACTS_PDF.write_bytes(data)
    ARTIFACTS_PDF_ALT.write_bytes(data)
    print(f"pdf_kb={OUT_PDF.stat().st_size / 1024:.1f}")


if __name__ == "__main__":
    main()
