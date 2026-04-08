#!/usr/bin/env python3
"""
render_editorial_dashboard.py - Renderiza superficies editoriales para Ateneo-KB.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = REPO_ROOT / "02_wiki"
OUTPUT_DIR = REPO_ROOT / "03_outputs"
INBOX_DIR = REPO_ROOT / "00_inbox"
GRAPH_FILE = WIKI_DIR / "indices" / "graph.json"
OUTPUT_FILE = WIKI_DIR / "indices" / "editorial-dashboard.html"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"\*([^*]+)\*")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

SECTION_KIND = {
    "Evidencia firme": "evidence",
    "Lectura abierta": "reading",
    "Hipotesis abierta": "hypothesis",
    "Hipótesis abierta": "hypothesis",
    "Resumen": "summary",
    "Takeaways para Ateneo-KB": "takeaways",
    "Relacion con Ateneo": "relation",
    "Relación con Ateneo": "relation",
    "Descripcion": "summary",
    "Descripción": "summary",
}


def frontmatter_block(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def parse_frontmatter(text: str) -> dict:
    block = frontmatter_block(text)
    if not block:
        return {}

    meta = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def extract_title(text: str, fallback: str) -> str:
    body = FRONTMATTER_RE.sub("", text, count=1).lstrip()
    match = TITLE_RE.search(body)
    return match.group(1).strip() if match else fallback


def normalize_path_ref(value: str) -> str:
    return value.strip().strip('"').strip("'").replace("\\", "/")


def extract_source_refs(text: str) -> list[str]:
    block = frontmatter_block(text)
    if not block:
        return []

    refs = []
    seen = set()
    lines = block.splitlines()
    in_sources = False
    source_indent = 0

    def push(ref: str) -> None:
        if ref and ref not in seen:
            seen.add(ref)
            refs.append(ref)

    for raw_line in lines:
        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip())

        if not in_sources:
            if not stripped.startswith("fuentes:"):
                continue
            in_sources = True
            source_indent = indent
            tail = stripped.partition(":")[2].strip()
            if tail and tail != "[]":
                for match in WIKILINK_RE.finditer(tail):
                    push(match.group(1))
                normalized = normalize_path_ref(tail)
                if normalized.startswith("01_raw/"):
                    push(normalized)
            continue

        if stripped and indent <= source_indent and not raw_line.lstrip().startswith("-"):
            break
        if not stripped or not raw_line.lstrip().startswith("-"):
            continue

        item = normalize_path_ref(raw_line.lstrip()[1:].strip())
        if not item:
            continue

        links = list(WIKILINK_RE.finditer(item))
        if links:
            for match in links:
                push(match.group(1))
            continue

        if item.startswith("01_raw/"):
            push(item)

    return refs


def stage_for_path(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel.startswith("02_wiki/fuentes/"):
        return "fuente"
    if rel.startswith("03_outputs/"):
        return "output"
    if rel.startswith("01_raw/"):
        return "raw"
    return "curado"


def clean_markdown(text: str) -> str:
    text = MD_LINK_RE.sub(r"\1", text)
    text = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), text)
    text = BOLD_RE.sub(r"\1", text)
    text = ITALIC_RE.sub(r"\1", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    text = text.replace(">", "").replace("#", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sections(text: str) -> dict:
    body = FRONTMATTER_RE.sub("", text, count=1).lstrip()
    matches = list(SECTION_RE.finditer(body))
    sections = {}

    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[title] = body[start:end].strip()
    return sections


def section_snippets(content: str, limit: int = 3) -> list[str]:
    snippets = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("---"):
            continue
        if line.startswith(("* ", "- ")):
            snippets.append(clean_markdown(line[2:]))
        elif re.match(r"^\d+\.\s+", line):
            snippets.append(clean_markdown(re.sub(r"^\d+\.\s+", "", line)))
        elif not line.startswith("###"):
            snippets.append(clean_markdown(line))
        if len(snippets) >= limit:
            break
    return [snippet for snippet in snippets if snippet]


def excerpt(text: str, max_length: int = 200) -> str:
    body = FRONTMATTER_RE.sub("", text, count=1).lstrip()
    lines = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(clean_markdown(line))
        if len(" ".join(lines)) >= max_length:
            break
    joined = " ".join(lines).strip()
    if len(joined) > max_length:
        return joined[: max_length - 1].rstrip() + "..."
    return joined


def load_lineage_maps(graph: dict) -> tuple[dict, dict, dict]:
    lineage = graph.get("lineage", {})
    nodes = {node["id"]: node for node in lineage.get("nodes", [])}
    incoming = {}
    outgoing = {}
    for edge in lineage.get("edges", []):
        outgoing.setdefault(edge["source"], []).append(edge)
        incoming.setdefault(edge["target"], []).append(edge)
    return nodes, incoming, outgoing


def build_note_records(lineage_nodes: dict, incoming: dict, outgoing: dict) -> tuple[list, list]:
    notes = []
    proof_items = []

    paths = list(WIKI_DIR.rglob("*.md")) + list(OUTPUT_DIR.rglob("*.md"))
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == "02_wiki/index.md" or rel.startswith("02_wiki/indices/"):
            continue

        text = path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        note_id = path.stem if not rel.startswith("03_outputs/") else f"output:{rel}"
        title = extract_title(text, path.stem.replace("-", " "))
        sections = split_sections(text)
        source_refs = extract_source_refs(text)
        stage = stage_for_path(path)
        tipo = meta.get("tipo", "")
        estado = meta.get("estado", "")
        confianza = meta.get("confianza", "")

        incoming_edges = incoming.get(note_id, [])
        outgoing_edges = outgoing.get(note_id, [])
        upstream_raw = [lineage_nodes[edge["source"]] for edge in incoming_edges if edge["source"].startswith("raw:")]
        upstream_notes = [
            lineage_nodes[edge["source"]]
            for edge in incoming_edges
            if not edge["source"].startswith("raw:") and edge["source"] in lineage_nodes
        ]
        downstream_outputs = [
            lineage_nodes[edge["target"]]
            for edge in outgoing_edges
            if str(edge["target"]).startswith("output:") and edge["target"] in lineage_nodes
        ]

        claim_blocks = []
        for section_name, kind in SECTION_KIND.items():
            if section_name not in sections:
                continue
            snippets = section_snippets(sections[section_name])
            if not snippets:
                continue
            claim_blocks.append(
                {
                    "section": section_name,
                    "kind": kind,
                    "snippets": snippets,
                }
            )

        note = {
            "id": note_id,
            "title": title,
            "path": rel,
            "stage": stage,
            "tipo": tipo,
            "estado": estado,
            "confianza": confianza,
            "source_refs": source_refs,
            "excerpt": excerpt(text),
            "claim_blocks": claim_blocks,
            "upstream_raw": [
                {"id": item["id"], "label": item["label"], "path": item["path"]}
                for item in upstream_raw
            ],
            "upstream_notes": [
                {"id": item["id"], "label": item["label"], "path": item["path"], "tipo": item.get("tipo", "")}
                for item in upstream_notes
            ],
            "downstream_outputs": [
                {"id": item["id"], "label": item["label"], "path": item["path"], "tipo": item.get("tipo", "")}
                for item in downstream_outputs
            ],
        }
        notes.append(note)

        if stage == "curado" and any(
            block["kind"] in {"evidence", "reading", "hypothesis"} for block in claim_blocks
        ):
            proof_blocks = {block["kind"]: block for block in claim_blocks}
            proof_items.append(
                {
                    "id": note_id,
                    "title": title,
                    "path": rel,
                    "tipo": tipo,
                    "confianza": confianza,
                    "evidence": proof_blocks.get("evidence", {}).get("snippets", []),
                    "reading": proof_blocks.get("reading", {}).get("snippets", []),
                    "hypothesis": proof_blocks.get("hypothesis", {}).get("snippets", []),
                    "upstream_raw": note["upstream_raw"],
                    "upstream_notes": note["upstream_notes"],
                    "downstream_outputs": note["downstream_outputs"],
                }
            )

    notes.sort(key=lambda item: (item["stage"], item["title"].lower()))
    proof_items.sort(key=lambda item: item["title"].lower())
    return notes, proof_items


def build_review_queue(notes: list) -> dict:
    queue = {
        "propuesto": [],
        "curado": [],
        "promovido": [],
        "publicado": [],
        "rechazado": [],
    }

    for path in sorted(INBOX_DIR.glob("*")):
        if path.name.startswith("_") or path.is_dir():
            continue
        queue["propuesto"].append(
            {
                "title": path.name,
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "tipo": "inbox",
                "estado": "propuesto",
            }
        )

    for note in notes:
        item = {
            "title": note["title"],
            "path": note["path"],
            "tipo": note["tipo"] or note["stage"],
            "estado": note["estado"] or "",
            "confianza": note["confianza"] or "",
        }

        if note["estado"] in {"draft", "review", "raw"}:
            queue["propuesto"].append(item)
        elif note["tipo"] == "obra" and note["estado"] == "publicado":
            queue["publicado"].append(item)
        elif note["stage"] == "fuente" and note["estado"] == "curado":
            queue["curado"].append(item)
        elif note["stage"] == "curado" and note["estado"] in {"curado", "publicado"}:
            queue["promovido"].append(item)
        elif note["stage"] == "output" and note["estado"] == "publicado":
            queue["publicado"].append(item)

    return queue


HTML = r"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ateneo-KB · Editorial Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300;1,400&display=swap">
  <style>
    :root {
      --cream: #f8f3ea;
      --ink: #1c1c18;
      --muted: rgba(28,28,24,0.50);
      --line: rgba(28,28,24,0.15);
      --line-dash: rgba(28,28,24,0.20);
      --dark: #1c1c18;
      --dark-text: #e8e4dc;
      --dark-muted: rgba(232,228,220,0.55);
      --raw: #b8aa94;
      --fuente: #8e6d48;
      --curado: #2a5754;
      --output: #8a3f34;
      --firme: #1f514b;
      --media: #92661c;
      --abierta: #934038;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--cream);
      color: var(--ink);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    /* ── Navbar ── */
    .navbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 40px;
      border-bottom: 1px solid var(--line);
    }
    .navbar-brand {
      font-family: 'Merriweather', Georgia, serif;
      font-weight: 700;
      font-style: italic;
      font-size: 1.25rem;
      letter-spacing: -0.02em;
      color: var(--ink);
    }
    .navbar-label {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      font-weight: 500;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--muted);
      margin-left: 16px;
    }
    .navbar-right {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--muted);
    }
    /* ── Shell ── */
    .shell {
      max-width: 1640px;
      margin: 0 auto;
      padding: 0 40px 60px;
    }
    /* ── Section tag ── */
    .section-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--muted);
    }
    /* ── Hero ── */
    .hero {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      border-bottom: 1px solid var(--line);
    }
    .hero-main {
      padding: 48px 48px 44px 0;
      border-right: 1px dashed var(--line-dash);
    }
    .hero-main h1 {
      font-family: 'Merriweather', Georgia, serif;
      font-weight: 300;
      font-size: clamp(2rem, 3vw, 2.8rem);
      line-height: 1.08;
      letter-spacing: -0.03em;
      margin-bottom: 16px;
    }
    .hero-main h1 em { font-style: italic; font-weight: 400; }
    .hero-main p {
      font-size: 0.95rem; line-height: 1.7; color: var(--muted); max-width: 55ch;
    }
    .hero-stats {
      padding: 48px 0 44px 48px;
      display: grid;
      grid-template-columns: 1fr 1fr;
    }
    .stat {
      padding: 18px 0;
      border-bottom: 1px solid var(--line);
    }
    .stat:nth-child(odd) { padding-right: 24px; border-right: 1px solid var(--line); }
    .stat:nth-child(even) { padding-left: 24px; }
    .stat:nth-last-child(-n+2) { border-bottom: none; }
    .stat-value {
      font-family: 'Merriweather', Georgia, serif;
      font-size: 2rem; font-weight: 300; line-height: 1; margin-bottom: 6px;
    }
    .stat-label {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted);
    }
    /* ── Dark quote ── */
    .quote-block {
      background: var(--dark); color: var(--dark-text);
      padding: 40px 48px; border-bottom: 1px solid var(--line);
    }
    .quote-block .section-tag {
      color: var(--dark-muted); border-left: 3px solid var(--firme);
      padding-left: 12px; margin-bottom: 20px;
    }
    .quote-block blockquote {
      font-family: 'Merriweather', Georgia, serif;
      font-style: italic; font-weight: 300;
      font-size: clamp(1.05rem, 1.6vw, 1.35rem); line-height: 1.55; max-width: 72ch;
    }
    /* ── Section headings ── */
    .section-header {
      padding: 32px 0 18px;
      border-bottom: 1px solid var(--line);
    }
    .section-header h2 {
      font-family: 'Merriweather', Georgia, serif;
      font-weight: 400;
      font-size: 1.5rem;
      letter-spacing: -0.02em;
      margin-bottom: 8px;
    }
    .section-header p {
      font-size: 0.9rem; line-height: 1.65; color: var(--muted); max-width: 72ch;
    }
    /* ── Controls ── */
    .controls {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 20px;
      padding: 20px 0;
      border-bottom: 1px solid var(--line);
    }
    label {
      display: block;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem; font-weight: 500;
      letter-spacing: 0.15em; text-transform: uppercase;
      color: var(--muted); margin-bottom: 8px;
    }
    input, select {
      width: 100%; border: 1px solid var(--line);
      background: rgba(255,255,255,0.6); color: var(--ink);
      padding: 10px 12px; font-family: 'Inter', sans-serif;
      font-size: 0.85rem; border-radius: 0; outline: none;
      transition: border-color 200ms;
    }
    input:focus, select:focus { border-color: var(--ink); }
    /* ── Claim layout ── */
    .claim-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) 340px;
      border-bottom: 1px solid var(--line);
    }
    .claims {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0;
      padding: 16px 0;
    }
    .claim {
      padding: 18px;
      border-bottom: 1px solid var(--line);
      border-right: 1px solid var(--line);
      cursor: pointer;
      transition: background 160ms;
    }
    .claim:hover { background: rgba(28,28,24,0.025); }
    .claim.selected { background: rgba(28,28,24,0.04); }
    .claim h3 {
      font-family: 'Merriweather', Georgia, serif;
      font-weight: 400; font-size: 0.95rem; line-height: 1.3; margin-bottom: 6px;
    }
    .claim p {
      font-size: 0.82rem; line-height: 1.55; color: var(--muted);
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
    }
    .pill-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
    .pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.62rem; font-weight: 500;
      letter-spacing: 0.1em; text-transform: uppercase;
      padding: 3px 9px; border: 1px solid var(--line);
      background: rgba(255,255,255,0.5); color: var(--muted);
      display: inline-flex; align-items: center; gap: 5px;
    }
    .dot {
      width: 7px; height: 7px; border-radius: 50%;
      display: inline-block; flex-shrink: 0;
    }
    /* ── Detail sidebar ── */
    .detail {
      padding: 24px;
      border-left: 1px dashed var(--line-dash);
      position: sticky; top: 0; align-self: start;
    }
    .detail h2 {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem; font-weight: 500;
      letter-spacing: 0.18em; text-transform: uppercase;
      color: var(--muted); margin-bottom: 16px;
    }
    .detail h3 {
      font-family: 'Merriweather', Georgia, serif;
      font-weight: 400; font-size: 1rem; line-height: 1.3; margin-bottom: 8px;
    }
    .detail-path {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem; color: var(--muted); word-break: break-all;
    }
    .detail-section {
      margin-top: 16px; padding-top: 16px;
      border-top: 1px solid var(--line);
    }
    .detail-section strong {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem; font-weight: 500;
      letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--muted); display: block; margin-bottom: 8px;
    }
    .detail-section ul {
      list-style: none; padding: 0; margin: 0;
    }
    .detail-section li {
      font-size: 0.82rem; line-height: 1.55; padding: 3px 0;
      color: var(--ink);
    }
    .empty {
      font-family: 'Merriweather', Georgia, serif;
      font-style: italic; font-size: 0.85rem; color: var(--muted);
    }
    /* ── Queue ── */
    .queue {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 0;
      border-bottom: 1px solid var(--line);
    }
    .column {
      padding: 20px 18px;
      border-right: 1px solid var(--line);
    }
    .column:last-child { border-right: none; }
    .column h3 {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem; font-weight: 500;
      letter-spacing: 0.15em; text-transform: uppercase;
      color: var(--muted); margin-bottom: 6px;
    }
    .column > p { font-size: 0.82rem; color: var(--muted); margin-bottom: 12px; }
    .item {
      padding: 12px 0;
      border-bottom: 1px solid var(--line);
    }
    .item:last-child { border-bottom: none; }
    .item strong {
      font-family: 'Merriweather', Georgia, serif;
      font-size: 0.85rem; font-weight: 400; line-height: 1.3;
      display: block; margin-bottom: 4px;
    }
    .path {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem; color: var(--muted); margin-top: 4px; word-break: break-all;
    }
    /* ── Proof surface ── */
    .proof-layout {
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      border-bottom: 1px solid var(--line);
    }
    .proof-sidebar {
      padding: 24px;
      border-right: 1px dashed var(--line-dash);
    }
    .proof-sidebar label {
      margin-bottom: 10px;
    }
    .proof-sidebar select {
      margin-bottom: 16px;
    }
    .proofgrid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0;
      padding: 0;
    }
    .proofcard {
      padding: 24px;
      border-right: 1px solid var(--line);
    }
    .proofcard:last-child { border-right: none; }
    .proofcard h4 {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem; font-weight: 500;
      letter-spacing: 0.15em; text-transform: uppercase;
      margin-bottom: 14px;
    }
    .proofcard.evidence { border-top: 3px solid var(--firme); }
    .proofcard.evidence h4 { color: var(--firme); }
    .proofcard.reading { border-top: 3px solid var(--media); }
    .proofcard.reading h4 { color: var(--media); }
    .proofcard.hypothesis { border-top: 3px solid var(--abierta); }
    .proofcard.hypothesis h4 { color: var(--abierta); }
    .proofcard ul {
      list-style: none; padding: 0; margin: 0;
    }
    .proofcard li {
      font-size: 0.85rem; line-height: 1.6; padding: 4px 0;
      border-bottom: 1px solid var(--line); color: var(--ink);
    }
    .proofcard li:last-child { border-bottom: none; }
    /* ── Footer ── */
    .footer {
      display: flex; align-items: center; justify-content: space-between;
      padding: 20px 40px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--muted);
    }
    /* ── Responsive ── */
    @media (max-width: 1200px) {
      .hero, .controls, .claim-layout, .queue, .proof-layout, .proofgrid { grid-template-columns: 1fr; }
      .claims { grid-template-columns: 1fr; }
      .detail, .proof-sidebar { position: static; border-left: none; border-right: none; border-top: 1px solid var(--line); }
      .shell { padding: 0 20px 40px; }
      .navbar, .footer { padding: 18px 20px; }
      .quote-block { padding: 32px 20px; }
    }
  </style>
</head>
<body>
  <nav class="navbar">
    <div>
      <span class="navbar-brand">ATENEO</span>
      <span class="navbar-label">Editorial Dashboard</span>
    </div>
    <span class="navbar-right">Ateneo-KB · Superficies editoriales</span>
  </nav>

  <div class="shell">
    <section class="hero">
      <div class="hero-main">
        <h1>Tres superficies<br>para hacer visible<br>la <em>diferencia.</em></h1>
        <p>Lineage por nota, cola de revisión editorial y una prueba pública de cómo se separan evidencia, lectura e hipótesis dentro de la misma base.</p>
      </div>
      <div class="hero-stats" id="summary"></div>
    </section>

    <div class="quote-block">
      <div class="section-tag">Lectura</div>
      <blockquote>
        "El agente propone, el humano aprueba. Lo que está en la wiki es lo que
        el humano ha validado. Lo que está en raw es inmutable. Lo que está en outputs
        cristaliza desde la wiki."
      </blockquote>
    </div>

    <div class="section-header">
      <h2>Claim Lineage</h2>
      <p>Notas leídas desde su procedencia y hacia su cristalización. No es un mapa temático general: es una lectura de la cadena editorial.</p>
    </div>

    <div class="controls">
      <div><label for="search">Buscar</label><input id="search" type="search" placeholder="concepto, fuente, proyecto..."></div>
      <div><label for="stage">Etapa</label><select id="stage"><option value="all">Todas</option><option value="fuente">Fuente</option><option value="curado">Curado</option><option value="output">Output</option></select></div>
      <div><label for="confidence">Confianza</label><select id="confidence"><option value="all">Todas</option><option value="firme">Firme</option><option value="media">Media</option><option value="abierta">Abierta</option></select></div>
    </div>

    <div class="claim-layout">
      <div class="claims" id="claims"></div>
      <aside class="detail" id="detail"></aside>
    </div>

    <div class="section-header">
      <h2>Editorial Review Queue</h2>
      <p>Versión mínima del paso "el agente propone, el humano aprueba", leída desde el estado real de la vault.</p>
    </div>
    <div class="queue" id="queue"></div>

    <div class="section-header">
      <h2>Public Proof Surface</h2>
      <p>Una superficie legible para terceros donde se ve qué parte de una nota es evidencia, qué parte es lectura y qué parte queda como hipótesis abierta.</p>
    </div>

    <div class="proof-layout">
      <aside class="proof-sidebar">
        <label for="proof-select">Nota curada</label>
        <select id="proof-select"></select>
        <div id="proof-meta"></div>
      </aside>
      <div>
        <div class="proofgrid">
          <div class="proofcard evidence"><h4>Evidencia firme</h4><div id="proof-evidence"></div></div>
          <div class="proofcard reading"><h4>Lectura abierta</h4><div id="proof-reading"></div></div>
          <div class="proofcard hypothesis"><h4>Hipótesis abierta</h4><div id="proof-hypothesis"></div></div>
        </div>
      </div>
    </div>
  </div>

  <footer class="footer">
    <span>Ateneo-KB · Editorial Dashboard generado automáticamente</span>
    <span>© 2026 Ateneo Editorial</span>
  </footer>

  <script>
    const DATA = __DATA__;
    const STAGE_COLORS = {raw:"#b8aa94",fuente:"#8e6d48",curado:"#2a5754",output:"#8a3f34"};
    const CONFIDENCE_COLORS = {firme:"#1f514b",media:"#92661c",abierta:"#934038"};
    const summary = document.getElementById("summary"), claims = document.getElementById("claims"), detail = document.getElementById("detail"), search = document.getElementById("search"), stage = document.getElementById("stage"), confidence = document.getElementById("confidence"), queue = document.getElementById("queue"), proofSelect = document.getElementById("proof-select"), proofMeta = document.getElementById("proof-meta"), proofEvidence = document.getElementById("proof-evidence"), proofReading = document.getElementById("proof-reading"), proofHypothesis = document.getElementById("proof-hypothesis");
    let selectedClaimId = null;
    const pill = (label,color=null) => `<span class="pill">${color?`<span class="dot" style="background:${color}"></span>`:""}${label}</span>`;
    const listHtml = (items) => items.length ? `<ul>${items.map((item)=>`<li>${item}</li>`).join("")}</ul>` : `<p class="empty">Sin contenido visible.</p>`;
    summary.innerHTML = [["Notas leídas",DATA.claims.length],["Bloques epistémicos",DATA.proof.length],["Items en cola",DATA.queue_totals.total],["Publicados",DATA.queue_totals.publicado]].map(([label,value])=>`<div class="stat"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`).join("");
    const matches = (item) => { const term = search.value.trim().toLowerCase(); if(stage.value!=="all" && item.stage!==stage.value) return false; if(confidence.value!=="all" && item.confianza!==confidence.value) return false; if(!term) return true; return `${item.title} ${item.path} ${item.tipo} ${item.excerpt}`.toLowerCase().includes(term); };
    function renderDetail(item){ if(!item){ detail.innerHTML = `<h2>Detalle</h2><p class="empty">Selecciona una nota para ver su lineage editorial.</p>`; return; } detail.innerHTML = `<h2>Detalle</h2><h3>${item.title}</h3><p>${item.excerpt || "Sin extracto."}</p><div class="pill-row">${pill(item.stage,STAGE_COLORS[item.stage]||STAGE_COLORS.curado)}${item.tipo?pill(item.tipo):""}${item.confianza?pill(item.confianza,CONFIDENCE_COLORS[item.confianza]):""}${item.estado?pill(item.estado):""}</div><p class="detail-path">${item.path}</p><div class="detail-section"><strong>Upstream raw</strong>${item.upstream_raw.length?`<ul>${item.upstream_raw.map((entry)=>`<li>${entry.label}</li>`).join("")}</ul>`:`<p class="empty">Sin raw directo visible.</p>`}</div><div class="detail-section"><strong>Upstream curado</strong>${item.upstream_notes.length?`<ul>${item.upstream_notes.map((entry)=>`<li>${entry.label}</li>`).join("")}</ul>`:`<p class="empty">Sin notas previas registradas.</p>`}</div><div class="detail-section"><strong>Downstream outputs</strong>${item.downstream_outputs.length?`<ul>${item.downstream_outputs.map((entry)=>`<li>${entry.label}</li>`).join("")}</ul>`:`<p class="empty">Todavía no cristaliza en output visible.</p>`}</div>${item.claim_blocks.length?item.claim_blocks.map((block)=>`<div class="detail-section"><strong>${block.section}</strong><ul>${block.snippets.map((snippet)=>`<li>${snippet}</li>`).join("")}</ul></div>`).join(""):""}`; }
    function renderClaims(){ const visible = DATA.claims.filter(matches); if(!selectedClaimId || !visible.some((item)=>item.id===selectedClaimId)) selectedClaimId = visible[0]?.id || null; claims.innerHTML = visible.length ? visible.map((item)=>`<article class="claim ${item.id===selectedClaimId?"selected":""}" data-id="${item.id}"><h3>${item.title}</h3><p>${item.excerpt || "Sin extracto."}</p><div class="pill-row">${pill(item.stage,STAGE_COLORS[item.stage]||STAGE_COLORS.curado)}${item.tipo?pill(item.tipo):""}${item.confianza?pill(item.confianza,CONFIDENCE_COLORS[item.confianza]):""}</div><div class="pill-row">${pill(`raw ${item.upstream_raw.length}`)}${pill(`upstream ${item.upstream_notes.length}`)}${pill(`outputs ${item.downstream_outputs.length}`)}</div></article>`).join("") : `<div style="padding:24px"><p class="empty">No hay resultados para ese filtro.</p></div>`; renderDetail(visible.find((item)=>item.id===selectedClaimId) || null); claims.querySelectorAll("[data-id]").forEach((node)=>node.addEventListener("click",()=>{selectedClaimId=node.dataset.id;renderClaims();})); }
    ["propuesto","curado","promovido","publicado","rechazado"].forEach((bucket)=>{ const labels = {propuesto:"Propuesto",curado:"Curado",promovido:"Promovido",publicado:"Publicado",rechazado:"Rechazado"}; queue.insertAdjacentHTML("beforeend", `<article class="column"><h3>${labels[bucket]}</h3><p>${DATA.queue[bucket].length} items</p>${DATA.queue[bucket].length?DATA.queue[bucket].map((item)=>`<div class="item"><strong>${item.title}</strong><div class="pill-row">${item.tipo?pill(item.tipo):""}${item.confianza?pill(item.confianza,CONFIDENCE_COLORS[item.confianza]):""}${item.estado?pill(item.estado):""}</div><div class="path">${item.path}</div></div>`).join(""):`<p class="empty">Sin items.</p>`}</article>`); });
    proofSelect.innerHTML = DATA.proof.map((item)=>`<option value="${item.id}">${item.title}</option>`).join("");
    function renderProof(id){ const item = DATA.proof.find((entry)=>entry.id===id) || DATA.proof[0]; if(!item) return; proofSelect.value = item.id; proofMeta.innerHTML = `<h3 style="font-family:'Merriweather',Georgia,serif;font-weight:400;font-size:1rem;line-height:1.3;margin:12px 0 8px">${item.title}</h3><p class="detail-path">${item.path}</p><div class="pill-row">${item.tipo?pill(item.tipo):""}${item.confianza?pill(item.confianza,CONFIDENCE_COLORS[item.confianza]):""}</div><div class="detail-section"><strong>Trazabilidad</strong><ul><li>Raw directos: ${item.upstream_raw.length}</li><li>Notas previas: ${item.upstream_notes.length}</li><li>Outputs derivados: ${item.downstream_outputs.length}</li></ul></div>`; proofEvidence.innerHTML = listHtml(item.evidence); proofReading.innerHTML = listHtml(item.reading); proofHypothesis.innerHTML = listHtml(item.hypothesis); }
    search.addEventListener("input",renderClaims); stage.addEventListener("change",renderClaims); confidence.addEventListener("change",renderClaims); proofSelect.addEventListener("change",()=>renderProof(proofSelect.value)); renderClaims(); renderProof(DATA.proof[0]?.id);
  </script>
</body>
</html>"""


def main() -> None:
    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    lineage_nodes, incoming, outgoing = load_lineage_maps(graph)
    claims, proof = build_note_records(lineage_nodes, incoming, outgoing)
    queue = build_review_queue(claims)

    payload = {
        "claims": claims,
        "proof": proof,
        "queue": queue,
        "queue_totals": {
            "total": sum(len(items) for items in queue.values()),
            "publicado": len(queue["publicado"]),
        },
    }

    html = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"editorial dashboard renderizado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
