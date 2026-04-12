"""
Hybrid file → Markdown ingest for Ateneo-KB.

Default behaviour:
- PDF -> MarkItDown by default; use pdf2md explicitly when page-sensitive extraction matters
- Markdown / text -> plain passthrough
- Other supported office / web formats -> MarkItDown (if installed)

Examples:
  python ingest_to_raw.py path/to/file.pdf
  python ingest_to_raw.py path/to/file.docx
  python ingest_to_raw.py notes.txt --copy-original
  python ingest_to_raw.py book.pdf --converter pdf2md
  python ingest_to_raw.py slides.pptx --out 01_raw/notion --write-meta
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, UTC
from pathlib import Path

from pdf2md import (
    convert_pdf_to_markdown,
    resolve_output_dir,
    resolve_repo_path,
    slugify,
    write_markdown,
)

REPO_ROOT = Path(__file__).resolve().parent
RAW_ROOT = REPO_ROOT / "01_raw"
DEFAULT_MD_OUT = "01_raw/web"
TEXT_PASSTHROUGH_EXTENSIONS = {".md", ".txt"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingesta híbrida a Markdown para Ateneo-KB."
    )
    parser.add_argument("input", help="Ruta al archivo de entrada.")
    parser.add_argument(
        "--out",
        default=DEFAULT_MD_OUT,
        help=f"Carpeta de salida para el Markdown derivado (default: {DEFAULT_MD_OUT}).",
    )
    parser.add_argument(
        "--converter",
        choices=["auto", "pdf2md", "markitdown", "epub_clean"],
        default="auto",
        help="Conversor a usar. 'auto' enruta por extensión.",
    )
    parser.add_argument(
        "--stem",
        help="Nombre base del archivo de salida (sin extensión).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescribe el .md derivado si ya existe.",
    )
    parser.add_argument(
        "--copy-original",
        action="store_true",
        help=(
            "Compatibilidad hacia atrás. La preservación del original ahora es el "
            "comportamiento por defecto."
        ),
    )
    parser.add_argument(
        "--skip-original-copy",
        action="store_true",
        help=(
            "No copia el original a la vault. Úsalo solo si el archivo ya vive en "
            "01_raw o si quieres forzar una ingesta derivada sin original."
        ),
    )
    parser.add_argument(
        "--original-out",
        help="Carpeta de destino para el original copiado. Si se omite, se infiere por extensión.",
    )
    parser.add_argument(
        "--write-meta",
        action="store_true",
        help="Escribe un sidecar .meta.json con detalles de la conversión.",
    )
    return parser


def infer_converter(input_path: Path, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    suffix = input_path.suffix.lower()
    if suffix == ".pdf":
        return "markitdown"
    if suffix == ".epub":
        return "epub_clean"
    if suffix in TEXT_PASSTHROUGH_EXTENSIONS:
        return "copy"
    return "markitdown"


def infer_original_out(input_path: Path) -> str:
    suffix = input_path.suffix.lower()
    if suffix == ".pdf":
        return "01_raw/pdf"
    if suffix in {".html", ".htm", ".md", ".txt"}:
        return "01_raw/web"
    if suffix == ".epub":
        return "01_raw/papers"
    return "01_raw/imported"


def ensure_input_exists(input_path: Path) -> None:
    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")


def is_in_raw(input_path: Path) -> bool:
    try:
        input_path.resolve().relative_to(RAW_ROOT.resolve())
    except ValueError:
        return False
    return True


def convert_with_markitdown(input_path: Path) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown no está instalado. Instálalo con "
            "\"pip install 'markitdown[all]'\" o usa --converter pdf2md para PDFs."
        ) from exc

    init_params = inspect.signature(MarkItDown.__init__).parameters
    if "enable_plugins" in init_params:
        md = MarkItDown(enable_plugins=False)
    else:
        md = MarkItDown()
    result = md.convert(str(input_path))
    text = getattr(result, "text_content", None)
    if not text:
        raise RuntimeError(f"MarkItDown no devolvió texto para: {input_path}")
    return text


def convert_with_epub_clean(input_path: Path) -> str:
    """
    Custom clean extraction for EPUB files. 
    Dives into zip to extract only text from HTML/XHTML, avoiding XML/CSS junk.
    """
    with zipfile.ZipFile(input_path, 'r') as z:
        # Get all html/xhtml/htm files
        text_files = [f for f in z.namelist() if f.lower().endswith(('.xhtml', '.html', '.htm'))]
        # Sort them (usually alphabetically works for OEBPS)
        text_files.sort()
        
        full_text = []
        for f in text_files:
            content = z.read(f).decode('utf-8', errors='ignore')
            # Basic HTML cleaning
            # Remove scripts and styles
            content = re.sub(r'<(script|style).*?>.*?</\1>', '', content, flags=re.DOTALL | re.IGNORECASE)
            # Remove tags
            content = re.sub(r'<.*?>', ' ', content, flags=re.DOTALL)
            # Normalize whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            if content:
                # We don't add titles per file to keep it cleaner for RAG, 
                # but we separate them.
                full_text.append(content)
        
        return "\n\n".join(full_text)


def convert_with_copy(input_path: Path) -> str:
    return input_path.read_text(encoding="utf-8")


def write_meta(
    meta_path: Path,
    *,
    source_path: Path,
    original_copy: Path | None,
    original_preserved: bool,
    preservation_mode: str,
    converter: str,
) -> None:
    payload = {
        "source_path": str(source_path.resolve()),
        "original_copy": str(original_copy.resolve()) if original_copy else None,
        "original_preserved": original_preserved,
        "preservation_mode": preservation_mode,
        "converter": converter,
        "converted_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "input_extension": source_path.suffix.lower(),
    }
    meta_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def maybe_copy_original(
    *,
    input_path: Path,
    skip_original_copy: bool,
    original_out: str | None,
    overwrite: bool,
) -> tuple[Path | None, str]:
    if is_in_raw(input_path):
        return input_path.resolve(), "already_in_vault"

    if skip_original_copy:
        return None, "skipped"

    target_dir = resolve_output_dir(original_out or infer_original_out(input_path))
    target_path = Path(target_dir) / input_path.name
    if target_path.exists() and not overwrite:
        raise FileExistsError(
            f"El original ya existe en la vault: {target_path}. Usa --overwrite para reemplazarlo."
        )
    shutil.copy2(input_path, target_path)
    return target_path, "copied"


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(resolve_repo_path(args.input))
    ensure_input_exists(input_path)

    converter = infer_converter(input_path, args.converter)
    out_dir = Path(resolve_output_dir(args.out))
    stem = args.stem or slugify(input_path.name)
    out_path = out_dir / f"{stem}.md"

    if out_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"El Markdown derivado ya existe: {out_path}. Usa --overwrite para reemplazarlo."
        )

    if converter == "pdf2md":
        markdown = convert_pdf_to_markdown(str(input_path))
    elif converter == "markitdown":
        markdown = convert_with_markitdown(input_path)
    elif converter == "epub_clean":
        markdown = convert_with_epub_clean(input_path)
    else:
        markdown = convert_with_copy(input_path)

    write_markdown(str(out_path), markdown)
    copied_original, preservation_mode = maybe_copy_original(
        input_path=input_path,
        skip_original_copy=args.skip_original_copy,
        original_out=args.original_out,
        overwrite=args.overwrite,
    )

    if preservation_mode == "skipped":
        print(
            "Warning: original no preservado en 01_raw. Esta ingesta pierde trazabilidad "
            "editorial salvo que el usuario lo haya pedido explícitamente.",
            file=sys.stderr,
        )

    if args.write_meta:
        write_meta(
            out_path.with_suffix(".meta.json"),
            source_path=input_path,
            original_copy=copied_original,
            original_preserved=preservation_mode != "skipped",
            preservation_mode=preservation_mode,
            converter=converter,
        )

    print(f"Conversor: {converter}")
    print(f"Markdown:  {out_path}")
    if preservation_mode == "already_in_vault":
        print(f"Original:  ya estaba preservado en {copied_original}")
    elif copied_original:
        print(f"Original:  {copied_original}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
