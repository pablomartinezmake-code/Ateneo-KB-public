# Quickstart

This repo is meant to be inspected, not just read about.

In five minutes you can see the whole method:

1. Run the graph and dashboards
2. Open the generated HTML surfaces
3. Trace one claim from raw capture to output

## Requirements

- Python 3.10+
- No external dependencies

## 1. Run the scripts

```bash
python 04_ops/scripts/wiki_graph.py --strict
python 04_ops/scripts/render_lineage_map.py
python 04_ops/scripts/render_editorial_dashboard.py
```

This generates:

- `02_wiki/indices/graph.json`
- `02_wiki/indices/lineage-map.html`
- `02_wiki/indices/editorial-dashboard.html`

## 2. Open the public surfaces

Start here:

- `02_wiki/indices/lineage-map.html`
- `02_wiki/indices/editorial-dashboard.html`

What to look for:

- `Lineage map` shows how material moves across the vault
- `Editorial dashboard` shows confidence, review states, and proof surfaces
- `Strict graph` catches broken links and forces the sample to stay coherent

## 3. Follow two complementary chains

For editorial density, start with this one:

```text
01_raw/books/miller-establecimiento-seminario-lacan.md
  -> 02_wiki/fuentes/miller-establecimiento-seminario-lacan.md
  -> 02_wiki/conceptos/establecimiento-textual.md
  -> 03_outputs/drafts/yo-claudio-05-establecer-texto.md
```

For a fully public-domain sample that can be audited end to end, inspect this one:

```text
01_raw/books/epicteto-manual-5-george-long.md
  -> 02_wiki/fuentes/epicteto-manual-5.md
  -> 02_wiki/conceptos/disciplina-del-asentimiento.md
  -> 03_outputs/memos/what-stoic-assent-has-to-do-with-llm-knowledge-bases.md
```

Read either chain in order, or compare both.

You will see the method becoming more explicit at each step:

- `raw` keeps the capture immutable
- `fuente` extracts what can actually be defended from the source
- `concepto` promotes a reusable interpretive node
- `output` turns that chain into an argument or public-facing draft

## 4. Check the editorial contract

Each curated note declares:

- `fuentes`
- `confianza`
- `estado`
- a visible split between `Evidencia firme`, `Lectura abierta`, and `Hipótesis abierta`

That split is the core of the repo.

The point is not to automate note-taking. The point is to make judgement legible.

## 5. Read the review logic

If you want the human review step, continue with [docs/review-flow.md](docs/review-flow.md).
