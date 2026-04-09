# Review Flow

This repository is not designed around "the AI writes the wiki for you."

It is designed around a stricter contract:

`the agent proposes -> the human reviews -> the vault promotes`

The public sample already contains one clean humanities chain that shows this.

## Example chain

```text
01_raw/books/miller-establecimiento-seminario-lacan.md
  -> 02_wiki/fuentes/miller-establecimiento-seminario-lacan.md
  -> 02_wiki/conceptos/establecimiento-textual.md
  -> 03_outputs/drafts/yo-claudio-05-establecer-texto.md
```

This is not four copies of the same content. Each step does a different editorial job.

## Step 1. Raw capture stays immutable

`01_raw/books/miller-establecimiento-seminario-lacan.md`

This layer preserves the captured material as source matter. It is not rewritten, normalised, or upgraded into argument.

Why it matters:

- provenance stays auditable
- later notes can be challenged against the original material
- the system never pretends that a polished note is the source itself

## Step 2. A curated source note is proposed

`02_wiki/fuentes/miller-establecimiento-seminario-lacan.md`

This note extracts a defendable account of the source.

In the public sample, the source note already declares:

- `fuentes: 01_raw/books/miller-establecimiento-seminario-lacan.md`
- `confianza: firme`
- `estado: curado`

It also separates:

- `Evidencia firme`
- `Lectura abierta`
- `Hipótesis abierta`

That separation is the first review gate.

The question is not "is this interesting?" but "which parts are actually supported, and which parts are already interpretation?"

## Step 3. Human review decides what can be promoted

The human reviewer checks at least four things before promotion:

1. `Provenance`
   The note must point back to a raw source or another curated note.
2. `Confidence`
   The note must say whether the claim is `firme`, `media`, or `abierta`.
3. `Epistemic split`
   Evidence, reading, and hypothesis cannot be collapsed into one smooth paragraph.
4. `Promotion discipline`
   Only claims that survive review move upward into concepts or outputs.

This is the main difference from a generic second-brain workflow.

The human is not an afterthought checking style. The human governs what the system is allowed to treat as knowledge.

## Step 4. A concept is promoted

`02_wiki/conceptos/establecimiento-textual.md`

This note no longer just summarises Miller. It creates a reusable concept:

- what "establecimiento textual" means
- what evidence supports it
- how far the analogy with Ateneo-KB can travel
- what remains open

That is a promotion, not a paraphrase.

The concept note still stays accountable to the source note through `fuentes` and explicit evidence blocks.

## Step 5. An output becomes possible

`03_outputs/drafts/yo-claudio-05-establecer-texto.md`

Only after the prior review steps does the repo allow a public-facing draft to appear.

The output note is marked as:

- `tipo: pensamiento`
- `estado: draft`
- `confianza: abierta`

It openly says what is solid, what is interpretive, and what remains unresolved.

That means publication is not treated as proof.

## What this flow protects

- It protects raw material from being silently overwritten by polished summaries.
- It protects interpretation from disguising itself as evidence.
- It protects public outputs from looking more certain than the underlying chain allows.
- It protects the researcher from outsourcing judgement to fluency.

## What to inspect next

Run the scripts and then open:

- `../02_wiki/indices/lineage-map.html`
- `../02_wiki/indices/editorial-dashboard.html`

Those surfaces make the same contract visible at the level of the whole vault.

If you want to inspect the same flow in a fully public-domain chain, compare it with:

- `../01_raw/books/epicteto-manual-5-george-long.md`
- `../02_wiki/fuentes/epicteto-manual-5.md`
- `../02_wiki/conceptos/disciplina-del-asentimiento.md`
- `../03_outputs/memos/what-stoic-assent-has-to-do-with-llm-knowledge-bases.md`
