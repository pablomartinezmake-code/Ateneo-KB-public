#!/usr/bin/env python3
"""
wiki_graph.py — Genera graph.json + lint ligero para Ateneo-KB.

Uso:
    python 04_ops/scripts/wiki_graph.py           # genera graph.json + lint warnings
    python 04_ops/scripts/wiki_graph.py --strict  # falla (exit 1) si hay warnings

Se ejecuta automaticamente como pre-commit hook.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = REPO_ROOT / "02_wiki"
OUTPUT_DIR = REPO_ROOT / "03_outputs"
INDEX_FILE = WIKI_DIR / "index.md"
GRAPH_OUTPUT = WIKI_DIR / "indices" / "graph.json"

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def frontmatter_block(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML-like parser for flat frontmatter fields."""
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


def extract_wikilinks(text: str) -> list[str]:
    return WIKILINK_RE.findall(text)


def extract_title(text: str, fallback: str) -> str:
    body = FRONTMATTER_RE.sub("", text, count=1).lstrip()
    match = TITLE_RE.search(body)
    return match.group(1).strip() if match else fallback


def normalize_path_ref(value: str) -> str:
    return value.strip().strip('"').strip("'").replace("\\", "/")


def extract_source_refs(text: str) -> list[str]:
    """Extracts the refs listed under frontmatter `fuentes:` preserving order."""
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
                for link in extract_wikilinks(tail):
                    push(link)
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

        wikilinks = extract_wikilinks(item)
        if wikilinks:
            for link in wikilinks:
                push(link)
            continue

        if item.startswith("01_raw/"):
            push(item)

    return refs


def stage_for_wiki_rel(rel: str) -> str:
    folder = Path(rel).parts[0]
    if folder == "fuentes":
        return "fuente"
    return "curado"


def output_kind(rel: str) -> str:
    parts = Path(rel).parts
    return parts[1] if len(parts) > 1 else "output"


def build_lineage(all_files: dict, note_cache: dict) -> dict:
    lineage_nodes = {}
    lineage_edges = {}

    def ensure_node(node_id: str, payload: dict) -> None:
        if node_id not in lineage_nodes:
            lineage_nodes[node_id] = payload

    def add_edge(source: str, target: str, relation: str) -> None:
        key = (source, target, relation)
        lineage_edges[key] = lineage_edges.get(key, 0) + 1

    def wiki_node_payload(stem: str) -> dict:
        cache = note_cache[stem]
        rel = all_files[stem][0]
        meta = cache["meta"]
        return {
            "id": stem,
            "label": cache["title"],
            "kind": "wiki",
            "stage": stage_for_wiki_rel(rel),
            "path": f"02_wiki/{rel}",
            "tipo": meta.get("tipo", ""),
            "confianza": meta.get("confianza", ""),
            "estado": meta.get("estado", ""),
        }

    for stem in all_files:
        ensure_node(stem, wiki_node_payload(stem))
        stage = lineage_nodes[stem]["stage"]

        for ref in note_cache[stem]["source_refs"]:
            if ref.startswith("01_raw/"):
                raw_id = f"raw:{ref}"
                ensure_node(
                    raw_id,
                    {
                        "id": raw_id,
                        "label": Path(ref).stem,
                        "kind": "raw",
                        "stage": "raw",
                        "path": ref,
                        "tipo": "raw",
                        "confianza": "",
                        "estado": "inmutable",
                    },
                )
                add_edge(raw_id, stem, "ingest")
                continue

            target = ref.split("/")[-1]
            if target not in all_files or target == stem:
                continue

            ensure_node(target, wiki_node_payload(target))
            source_tipo = note_cache[target]["meta"].get("tipo", "")
            relation = "promote" if source_tipo == "fuente" and stage != "fuente" else "derive"
            add_edge(target, stem, relation)

    for md in OUTPUT_DIR.rglob("*.md"):
        rel = md.relative_to(REPO_ROOT).as_posix()
        text = md.read_text(encoding="utf-8")
        source_refs = extract_source_refs(text)
        if not source_refs:
            continue

        meta = parse_frontmatter(text)
        output_id = f"output:{rel}"
        ensure_node(
            output_id,
            {
                "id": output_id,
                "label": extract_title(text, md.stem.replace("-", " ")),
                "kind": "output",
                "stage": "output",
                "path": rel,
                "tipo": meta.get("tipo", output_kind(rel)),
                "confianza": meta.get("confianza", ""),
                "estado": meta.get("estado", ""),
            },
        )

        for ref in source_refs:
            if ref.startswith("01_raw/"):
                raw_id = f"raw:{ref}"
                ensure_node(
                    raw_id,
                    {
                        "id": raw_id,
                        "label": Path(ref).stem,
                        "kind": "raw",
                        "stage": "raw",
                        "path": ref,
                        "tipo": "raw",
                        "confianza": "",
                        "estado": "inmutable",
                    },
                )
                add_edge(raw_id, output_id, "cite")
                continue

            target = ref.split("/")[-1]
            if target not in all_files:
                continue

            ensure_node(target, wiki_node_payload(target))
            add_edge(target, output_id, "publish")

    connected = set()
    for source, target, _relation in lineage_edges:
        connected.add(source)
        connected.add(target)

    stage_order = {"raw": 0, "fuente": 1, "curado": 2, "output": 3}
    nodes = [
        lineage_nodes[node_id]
        for node_id in sorted(
            connected,
            key=lambda node_id: (
                stage_order.get(lineage_nodes[node_id]["stage"], 9),
                lineage_nodes[node_id]["label"].lower(),
            ),
        )
    ]
    edges = [
        {
            "source": source,
            "target": target,
            "relation": relation,
            "weight": weight,
        }
        for (source, target, relation), weight in sorted(lineage_edges.items())
    ]

    stats = {
        "nodes": len(nodes),
        "edges": len(edges),
        "raw_nodes": sum(1 for node in nodes if node["stage"] == "raw"),
        "fuente_nodes": sum(1 for node in nodes if node["stage"] == "fuente"),
        "curado_nodes": sum(1 for node in nodes if node["stage"] == "curado"),
        "output_nodes": sum(1 for node in nodes if node["stage"] == "output"),
    }

    return {
        "generated": "auto",
        "stages": ["raw", "fuente", "curado", "output"],
        "stats": stats,
        "nodes": nodes,
        "edges": edges,
    }


def build_graph() -> tuple[dict, list[str]]:
    """Returns (graph_data, warnings)."""
    nodes = {}
    edge_weights = {}
    warnings = []

    all_files = {}
    note_cache = {}

    for md in WIKI_DIR.rglob("*.md"):
        rel = md.relative_to(WIKI_DIR).as_posix()
        if rel == "index.md" or rel.startswith("indices/"):
            continue
        all_files.setdefault(md.stem, []).append(rel)

    for stem, rels in all_files.items():
        all_links = []

        for index, rel in enumerate(rels):
            md_path = WIKI_DIR / rel
            text = md_path.read_text(encoding="utf-8")
            all_links.extend(extract_wikilinks(text))

            if index == 0:
                meta = parse_frontmatter(text)
                primary_rel = rel
                note_cache[stem] = {
                    "meta": meta,
                    "title": extract_title(text, stem.replace("-", " ")),
                    "source_refs": extract_source_refs(text),
                }

        nodes[stem] = {
            "id": stem,
            "title": note_cache[stem]["title"],
            "path": f"02_wiki/{primary_rel}",
            "tipo": note_cache[stem]["meta"].get("tipo", ""),
            "dominio": note_cache[stem]["meta"].get("dominio", ""),
            "confianza": note_cache[stem]["meta"].get("confianza", ""),
            "estado": note_cache[stem]["meta"].get("estado", ""),
            "stage": stage_for_wiki_rel(primary_rel),
            "links_out": len(all_links),
        }

        for target in all_links:
            normalized = target.split("/")[-1]
            if normalized == stem or normalized.endswith(".html") or normalized.endswith(".pdf"):
                continue
            edge_weights[(stem, normalized)] = edge_weights.get((stem, normalized), 0) + 1

    edges = [
        {"source": source, "target": target, "weight": weight}
        for (source, target), weight in sorted(edge_weights.items())
    ]

    broken = set()
    for edge in edges:
        target = edge["target"]
        if target not in all_files:
            broken.add((edge["source"], target))
    if broken:
        warnings.append(f"Wikilinks rotos ({len(broken)}):")
        for source, target in sorted(broken):
            warnings.append(f"  {source} -> [[{target}]]")

    linked_targets = {edge["target"] for edge in edges}
    index_text = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.exists() else ""
    index_stems = set(WIKILINK_RE.findall(index_text))
    orphans = []
    for stem in all_files:
        if stem not in linked_targets and stem not in index_stems:
            orphans.append(stem)
    if orphans:
        warnings.append(f"Notas huerfanas ({len(orphans)}):")
        for orphan in sorted(orphans):
            warnings.append(f"  {orphan}")

    missing_from_index = []
    for stem in all_files:
        if stem not in index_stems:
            missing_from_index.append(stem)
    if missing_from_index:
        warnings.append(f"Notas no listadas en index.md ({len(missing_from_index)}):")
        for missing in sorted(missing_from_index):
            warnings.append(f"  {missing}")

    required = {"tipo", "dominio", "estado", "confianza", "actualizado"}
    for stem in nodes:
        md_path = WIKI_DIR / all_files[stem][0]
        text = md_path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        missing = required - set(meta.keys())
        if missing:
            warnings.append(
                f"Frontmatter incompleto en {stem}: faltan {', '.join(sorted(missing))}"
            )

    graph = {
        "generated": "auto",
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "broken_links": len(broken),
        },
        "nodes": list(nodes.values()),
        "edges": edges,
        "lineage": build_lineage(all_files, note_cache),
    }

    return graph, warnings


def main() -> None:
    strict = "--strict" in sys.argv
    graph, warnings = build_graph()

    GRAPH_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_OUTPUT.write_text(
        json.dumps(graph, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    stats = graph["stats"]
    print(
        f"graph.json: {stats['nodes']} nodos, {stats['edges']} aristas, "
        f"{stats['broken_links']} links rotos"
    )

    if warnings:
        print("\nLint warnings:")
        for warning in warnings:
            print(f"  {warning}")

    if strict and warnings:
        print("\n--strict: commit abortado por warnings.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
