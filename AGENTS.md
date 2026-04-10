# Ateneo-KB Public — Agent Rules

## What this repository is

A small public edition of an editorial knowledge base for humanities-oriented AI research.

It demonstrates a method:

- `raw -> fuente -> concepto -> output`
- visible provenance
- explicit confidence
- distinction between evidence and interpretation

## Structure

- `01_raw/` - immutable sample captures
- `02_wiki/` - curated notes and indices
- `03_outputs/` - derived public-facing artifacts
- `04_ops/` - scripts, templates, log

## Non-negotiables

1. Do not rewrite `01_raw/`.
2. Do not invent citations or sources.
3. Keep three levels visible whenever relevant:
   - `Evidencia firme`
   - `Lectura abierta`
   - `Hipótesis abierta`
4. Every curated note needs frontmatter with:
   - `tipo`
   - `dominio`
   - `estado`
   - `fuentes`
   - `confianza`
   - `actualizado`
5. Treat this repo as a public demo of a method, not as a personal vault.
6. When ingesting new raw material, prefer `python ingest_to_raw.py "path/to/file" --write-meta`; preserve the original by default, use `MarkItDown` as the default PDF path, and treat `--skip-original-copy` as an explicit exception. Use `--converter pdf2md` only when page-sensitive extraction matters more than speed.
7. When a source is not yet fixed, record a reproducible lookup trace before curation. Use `04_ops/templates/search-trail.md` to preserve the query trail, candidate records, and the reason a source was selected.

## Goal

Make the editorial logic legible to outsiders. Do not optimize for volume; optimize for clarity, defensibility, and portability.
