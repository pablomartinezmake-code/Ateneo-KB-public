"""
PDF → Markdown converter for Ateneo-KB vault.

Usage:
  python pdf2md.py archivo.pdf                  # output to 01_raw/web/
  python pdf2md.py archivo.pdf --out 01_raw/notion/  # custom output dir
"""

import sys
import os
import re
import pymupdf4llm


def slugify(name: str) -> str:
    name = os.path.splitext(os.path.basename(name))[0]
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    return name


def resolve_repo_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(os.path.dirname(__file__), path)


def default_output_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "01_raw", "web")


def resolve_output_dir(out_dir: str | None = None) -> str:
    target = out_dir or default_output_dir()
    target = resolve_repo_path(target)
    os.makedirs(target, exist_ok=True)
    return target


def convert_pdf_to_markdown(pdf_path: str) -> str:
    return pymupdf4llm.to_markdown(pdf_path)


def write_markdown(out_path: str, text: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    if len(sys.argv) < 2:
        print("Uso: python pdf2md.py <archivo.pdf> [--out <carpeta>]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    out_dir = default_output_dir()

    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        if idx + 1 < len(sys.argv):
            out_dir = sys.argv[idx + 1]

    out_dir = resolve_output_dir(out_dir)

    slug = slugify(pdf_path)
    out_path = os.path.join(out_dir, f"{slug}.md")

    print(f"Convirtiendo: {pdf_path}")
    md_text = convert_pdf_to_markdown(pdf_path)
    write_markdown(out_path, md_text)

    print(f"Guardado en:  {out_path}")


if __name__ == "__main__":
    main()
