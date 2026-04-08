#!/usr/bin/env python3
"""
render_lineage_map.py — Renderiza un mapa HTML del lineage editorial.

Uso:
    python 04_ops/scripts/render_lineage_map.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_FILE = REPO_ROOT / "02_wiki" / "indices" / "graph.json"
OUTPUT_FILE = REPO_ROOT / "02_wiki" / "indices" / "lineage-map.html"


HTML_TEMPLATE = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ateneo-KB · Lineage Map</title>
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
      --accent: #003d9b;
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
      text-decoration: none;
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
    /* ── Hero bento ── */
    .hero {
      display: grid;
      grid-template-columns: 1fr 1fr;
      border-bottom: 1px solid var(--line);
    }
    .hero-main {
      padding: 48px 48px 44px 0;
      border-right: 1px dashed var(--line-dash);
    }
    .hero-main h1 {
      font-family: 'Merriweather', Georgia, serif;
      font-weight: 300;
      font-size: clamp(2.2rem, 3.4vw, 3.2rem);
      line-height: 1.08;
      letter-spacing: -0.03em;
      margin-bottom: 20px;
    }
    .hero-main h1 em {
      font-style: italic;
      font-weight: 400;
    }
    .hero-main p {
      font-family: 'Inter', sans-serif;
      font-size: 0.95rem;
      line-height: 1.7;
      color: var(--muted);
      max-width: 52ch;
    }
    .hero-stats {
      padding: 48px 0 44px 48px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0;
    }
    .stat {
      padding: 18px 0;
      border-bottom: 1px solid var(--line);
    }
    .stat:nth-child(odd) {
      padding-right: 24px;
      border-right: 1px solid var(--line);
    }
    .stat:nth-child(even) {
      padding-left: 24px;
    }
    .stat:nth-last-child(-n+2) {
      border-bottom: none;
    }
    .stat-value {
      font-family: 'Merriweather', Georgia, serif;
      font-size: 2rem;
      font-weight: 300;
      line-height: 1;
      margin-bottom: 6px;
    }
    .stat-label {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }
    /* ── Dark quote block ── */
    .quote-block {
      background: var(--dark);
      color: var(--dark-text);
      padding: 40px 48px;
      border-bottom: 1px solid var(--line);
    }
    .quote-block .section-tag {
      color: var(--dark-muted);
      border-left: 3px solid var(--firme);
      padding-left: 12px;
      margin-bottom: 20px;
    }
    .quote-block blockquote {
      font-family: 'Merriweather', Georgia, serif;
      font-style: italic;
      font-weight: 300;
      font-size: clamp(1.1rem, 1.8vw, 1.5rem);
      line-height: 1.55;
      max-width: 72ch;
    }
    /* ── Section tags ── */
    .section-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--muted);
    }
    /* ── Layout: controls + viewport + detail ── */
    .main-layout {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr) 300px;
      border-bottom: 1px solid var(--line);
    }
    .side-panel {
      padding: 28px 24px;
      position: sticky;
      top: 0;
      align-self: start;
    }
    .side-panel:first-child {
      border-right: 1px dashed var(--line-dash);
    }
    .side-panel:last-child {
      border-left: 1px dashed var(--line-dash);
    }
    .panel-section {
      padding: 18px 0;
      border-bottom: 1px solid var(--line);
    }
    .panel-section:last-child {
      border-bottom: none;
    }
    .panel-section h2 {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 14px;
    }
    .panel-section p {
      font-family: 'Merriweather', Georgia, serif;
      font-size: 0.88rem;
      line-height: 1.65;
      color: var(--muted);
    }
    .legend-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 5px 0;
      font-family: 'Inter', sans-serif;
      font-size: 0.82rem;
      color: var(--ink);
    }
    .legend-row .count {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: var(--muted);
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 10px;
      flex-shrink: 0;
    }
    label {
      display: block;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      font-weight: 500;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }
    input, select {
      width: 100%;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.6);
      color: var(--ink);
      padding: 10px 12px;
      font-family: 'Inter', sans-serif;
      font-size: 0.85rem;
      border-radius: 0;
      outline: none;
      transition: border-color 200ms;
    }
    input:focus, select:focus {
      border-color: var(--ink);
    }
    input + label {
      margin-top: 16px;
    }
    /* ── Viewport ── */
    .viewport {
      padding: 20px 16px;
      overflow: auto;
      min-height: 880px;
    }
    #board {
      width: 100%;
      height: 100%;
      display: block;
      min-height: 880px;
    }
    /* ── SVG styles ── */
    .stage-label {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9px;
      font-weight: 500;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      fill: var(--muted);
    }
    .stage-caption {
      font-family: 'Inter', sans-serif;
      font-size: 10px;
      fill: var(--muted);
    }
    .edge {
      fill: none;
      stroke: rgba(28, 28, 24, 0.10);
      stroke-linecap: round;
    }
    .edge.active {
      stroke: rgba(28, 28, 24, 0.45);
    }
    .node rect {
      rx: 3px;
      ry: 3px;
      stroke-width: 1;
      transition: stroke 160ms ease;
    }
    .node text {
      font-family: 'Inter', sans-serif;
      font-size: 11px;
      fill: var(--ink);
      pointer-events: none;
    }
    .node.is-match rect {
      stroke: var(--ink);
      stroke-width: 1.6;
    }
    .node.is-selected rect {
      stroke: var(--ink);
      stroke-width: 2;
    }
    /* ── Detail panel ── */
    .detail-title {
      font-family: 'Merriweather', Georgia, serif;
      font-size: 1.05rem;
      font-weight: 400;
      line-height: 1.3;
      margin-bottom: 8px;
    }
    .detail-path {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      color: var(--muted);
      word-break: break-all;
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 10px 0;
    }
    .pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      font-weight: 500;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 4px 10px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.5);
      color: var(--muted);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .detail-section {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--line);
    }
    .detail-section strong {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      font-weight: 500;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      display: block;
      margin-bottom: 8px;
    }
    .detail-section .list-row {
      font-family: 'Inter', sans-serif;
      font-size: 0.82rem;
      padding: 4px 0;
      color: var(--ink);
    }
    .empty {
      font-family: 'Merriweather', Georgia, serif;
      font-style: italic;
      font-size: 0.88rem;
      color: var(--muted);
    }
    /* ── Footer ── */
    .footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 20px 40px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }
    /* ── Responsive ── */
    @media (max-width: 1200px) {
      .hero { grid-template-columns: 1fr; }
      .hero-main { border-right: none; border-bottom: 1px dashed var(--line-dash); padding-right: 0; }
      .hero-stats { padding-left: 0; padding-top: 32px; }
      .main-layout { grid-template-columns: 1fr; }
      .side-panel { position: static; border-right: none !important; border-left: none !important; border-bottom: 1px solid var(--line); }
      .shell { padding: 0 20px 40px; }
      .navbar { padding: 18px 20px; }
      .quote-block { padding: 32px 20px; }
      .footer { padding: 20px; }
    }
  </style>
</head>
<body>
  <nav class="navbar">
    <div>
      <span class="navbar-brand">ATENEO</span>
      <span class="navbar-label">Lineage Map</span>
    </div>
    <span class="navbar-right">Ateneo-KB · Mapa de procedencia editorial</span>
  </nav>

  <div class="shell">
    <section class="hero">
      <div class="hero-main">
        <h1>Cadena editorial<br>desde <em>raw</em> hasta <em>output.</em></h1>
        <p>
          El mapa no muestra afinidades temáticas generales, sino relaciones de procedencia:
          qué fuente sube a qué nota, qué concepto se promueve a partir de qué fuente y qué
          pensamiento o draft cristaliza después.
        </p>
      </div>
      <div class="hero-stats" id="summary-grid"></div>
    </section>

    <div class="quote-block">
      <div class="section-tag">Lectura</div>
      <blockquote>
        "La pregunta no es solo qué notas están conectadas, sino de dónde sale cada una y
        hacia qué pieza termina cristalizando. El mapa sirve para defender la tesis de que
        Ateneo-KB no es un archivo que acumula cosas, sino una disciplina editorial que
        hace visible su genealogía."
      </blockquote>
    </div>

    <section class="main-layout">
      <aside class="side-panel">
        <div class="panel-section">
          <h2>Filtros</h2>
          <label for="search">Buscar nodo</label>
          <input id="search" type="search" placeholder="autor, concepto, raw...">
          <label for="confidence">Confianza</label>
          <select id="confidence">
            <option value="all">Todas</option>
            <option value="firme">Firme</option>
            <option value="media">Media</option>
            <option value="abierta">Abierta</option>
          </select>
        </div>
        <div class="panel-section">
          <h2>Etapas</h2>
          <div class="legend-row"><span><span class="dot" style="background:var(--raw)"></span>Raw</span><span class="count" id="count-raw"></span></div>
          <div class="legend-row"><span><span class="dot" style="background:var(--fuente)"></span>Fuente</span><span class="count" id="count-fuente"></span></div>
          <div class="legend-row"><span><span class="dot" style="background:var(--curado)"></span>Curado</span><span class="count" id="count-curado"></span></div>
          <div class="legend-row"><span><span class="dot" style="background:var(--output)"></span>Output</span><span class="count" id="count-output"></span></div>
        </div>
        <div class="panel-section">
          <h2>Confianza</h2>
          <div class="legend-row"><span><span class="dot" style="background:var(--firme)"></span>Firme</span></div>
          <div class="legend-row"><span><span class="dot" style="background:var(--media)"></span>Media</span></div>
          <div class="legend-row"><span><span class="dot" style="background:var(--abierta)"></span>Abierta</span></div>
          <div class="legend-row"><span><span class="dot" style="background:var(--raw)"></span>Raw / sin escala</span></div>
        </div>
      </aside>

      <main class="viewport">
        <svg id="board" viewBox="0 0 1360 980" preserveAspectRatio="xMidYMin meet"></svg>
      </main>

      <aside class="side-panel" id="detail-panel">
        <div class="panel-section" id="detail">
          <h2>Detalle</h2>
          <p class="empty">Selecciona un nodo para ver su tramo de lineage.</p>
        </div>
      </aside>
    </section>
  </div>

  <footer class="footer">
    <span>Ateneo-KB · Lineage Map generado automáticamente</span>
    <span>© 2026 Ateneo Editorial</span>
  </footer>

  <script>
    const DATA = __DATA__;
    const STAGES = ["raw", "fuente", "curado", "output"];
    const STAGE_LABELS = {
      raw: "01_RAW",
      fuente: "02_WIKI / FUENTES",
      curado: "02_WIKI / CURADO",
      output: "03_OUTPUTS"
    };
    const STAGE_COLORS = {
      raw: getComputedStyle(document.documentElement).getPropertyValue("--raw").trim(),
      fuente: getComputedStyle(document.documentElement).getPropertyValue("--fuente").trim(),
      curado: getComputedStyle(document.documentElement).getPropertyValue("--curado").trim(),
      output: getComputedStyle(document.documentElement).getPropertyValue("--output").trim()
    };
    const CONFIDENCE_COLORS = {
      firme: getComputedStyle(document.documentElement).getPropertyValue("--firme").trim(),
      media: getComputedStyle(document.documentElement).getPropertyValue("--media").trim(),
      abierta: getComputedStyle(document.documentElement).getPropertyValue("--abierta").trim()
    };

    const svg = document.getElementById("board");
    const detail = document.getElementById("detail");
    const searchInput = document.getElementById("search");
    const confidenceSelect = document.getElementById("confidence");
    const summaryGrid = document.getElementById("summary-grid");

    const graph = {
      nodes: DATA.nodes.map((node) => ({ ...node })),
      edges: DATA.edges.map((edge) => ({ ...edge }))
    };

    const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
    const adjacency = new Map();
    for (const node of graph.nodes) adjacency.set(node.id, new Set());
    for (const edge of graph.edges) {
      adjacency.get(edge.source)?.add(edge.target);
      adjacency.get(edge.target)?.add(edge.source);
    }

    let selectedId = null;

    function buildSummary() {
      const items = [
        ["Nodos en lineage", DATA.stats.nodes],
        ["Aristas de procedencia", DATA.stats.edges],
        ["Raw conectados", DATA.stats.raw_nodes],
        ["Outputs conectados", DATA.stats.output_nodes]
      ];
      summaryGrid.innerHTML = items
        .map(([label, value]) => `
          <div class="stat">
            <div class="stat-value">${value}</div>
            <div class="stat-label">${label}</div>
          </div>
        `)
        .join("");
    }

    function updateCounters(visibleNodes) {
      const counts = { raw: 0, fuente: 0, curado: 0, output: 0 };
      for (const node of visibleNodes) counts[node.stage] += 1;
      document.getElementById("count-raw").textContent = counts.raw;
      document.getElementById("count-fuente").textContent = counts.fuente;
      document.getElementById("count-curado").textContent = counts.curado;
      document.getElementById("count-output").textContent = counts.output;
    }

    function nodeMatches(node, term, confidence) {
      const confidenceMatch =
        confidence === "all" ||
        node.kind === "raw" ||
        (node.confianza || "").toLowerCase() === confidence;
      if (!confidenceMatch) return false;
      if (!term) return true;
      const haystack = `${node.label} ${node.path} ${node.tipo || ""}`.toLowerCase();
      return haystack.includes(term);
    }

    function deriveVisibleSet(term, confidence) {
      const matched = new Set(
        graph.nodes
          .filter((node) => nodeMatches(node, term, confidence))
          .map((node) => node.id)
      );
      if (!term) return matched;
      const expanded = new Set(matched);
      for (const nodeId of matched) {
        for (const neighbor of adjacency.get(nodeId) || []) {
          const node = nodeById.get(neighbor);
          if (node && nodeMatches(node, "", confidence)) expanded.add(neighbor);
        }
      }
      return expanded;
    }

    function stageFill(node) {
      if (node.kind === "raw") return STAGE_COLORS.raw;
      if (node.confianza && CONFIDENCE_COLORS[node.confianza]) return CONFIDENCE_COLORS[node.confianza];
      return STAGE_COLORS[node.stage] || "#bbb";
    }

    function truncate(value, max = 38) {
      return value.length > max ? `${value.slice(0, max - 1)}…` : value;
    }

    function buildLayout(nodesByStage) {
      const width = 1360;
      const xMap = { raw: 70, fuente: 390, curado: 710, output: 1030 };
      const boxWidth = 245;
      const boxHeight = 24;
      const stageTop = 120;
      const gap = 14;
      const counts = STAGES.map((stage) => (nodesByStage.get(stage) || []).length);
      const maxCount = Math.max(1, ...counts);
      const height = Math.max(980, stageTop + maxCount * (boxHeight + gap) + 120);
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.style.minHeight = `${height}px`;
      const positions = new Map();
      for (const stage of STAGES) {
        const nodes = nodesByStage.get(stage) || [];
        nodes.forEach((node, index) => {
          positions.set(node.id, {
            x: xMap[stage],
            y: stageTop + index * (boxHeight + gap),
            width: boxWidth,
            height: boxHeight
          });
        });
      }
      return { positions, width, height };
    }

    function neighborhood(selectedNodeId) {
      if (!selectedNodeId) return new Set();
      const active = new Set([selectedNodeId]);
      for (const neighbor of adjacency.get(selectedNodeId) || []) active.add(neighbor);
      return active;
    }

    function renderDetail(nodeId) {
      if (!nodeId || !nodeById.has(nodeId)) {
        detail.innerHTML = `
          <h2>Detalle</h2>
          <p class="empty">Selecciona un nodo para ver su tramo de lineage.</p>
        `;
        return;
      }
      const node = nodeById.get(nodeId);
      const upstream = graph.edges.filter((e) => e.target === nodeId).map((e) => nodeById.get(e.source));
      const downstream = graph.edges.filter((e) => e.source === nodeId).map((e) => nodeById.get(e.target));
      const pills = [
        `<span class="pill"><span class="dot" style="background:${STAGE_COLORS[node.stage]}"></span>${node.stage}</span>`
      ];
      if (node.tipo) pills.push(`<span class="pill">${node.tipo}</span>`);
      if (node.confianza) pills.push(`<span class="pill"><span class="dot" style="background:${CONFIDENCE_COLORS[node.confianza] || 'var(--muted)'}"></span>${node.confianza}</span>`);

      detail.innerHTML = `
        <h2>Detalle</h2>
        <h3 class="detail-title">${node.label}</h3>
        <div class="pill-row">${pills.join("")}</div>
        <p class="detail-path">${node.path}</p>
        <div class="detail-section">
          <strong>Recibe de (${upstream.length})</strong>
          ${upstream.length ? upstream.map((item) => `<div class="list-row">${item.label}</div>`).join("") : '<p class="empty">Sin upstream directo.</p>'}
        </div>
        <div class="detail-section">
          <strong>Deriva en (${downstream.length})</strong>
          ${downstream.length ? downstream.map((item) => `<div class="list-row">${item.label}</div>`).join("") : '<p class="empty">Sin downstream directo.</p>'}
        </div>
      `;
    }

    function render() {
      const term = searchInput.value.trim().toLowerCase();
      const confidence = confidenceSelect.value;
      const visibleIds = deriveVisibleSet(term, confidence);
      if (selectedId && !visibleIds.has(selectedId)) selectedId = null;
      const visibleNodes = graph.nodes.filter((node) => visibleIds.has(node.id));
      const nodesByStage = new Map(STAGES.map((stage) => [stage, []]));
      for (const node of visibleNodes) nodesByStage.get(node.stage).push(node);
      for (const stage of STAGES) {
        nodesByStage.get(stage).sort((a, b) => a.label.localeCompare(b.label, "es"));
      }
      updateCounters(visibleNodes);
      const { positions, width, height } = buildLayout(nodesByStage);
      const activeIds = neighborhood(selectedId);
      let html = "";
      STAGES.forEach((stage) => {
        const x = { raw: 70, fuente: 390, curado: 710, output: 1030 }[stage];
        html += `
          <text class="stage-label" x="${x}" y="58">${STAGE_LABELS[stage]}</text>
          <text class="stage-caption" x="${x}" y="78">${nodesByStage.get(stage).length} nodos visibles</text>
          <line x1="${x}" y1="92" x2="${x + 245}" y2="92" stroke="rgba(28,28,24,0.12)" />
        `;
      });
      for (const edge of graph.edges) {
        if (!visibleIds.has(edge.source) || !visibleIds.has(edge.target)) continue;
        const sp = positions.get(edge.source);
        const tp = positions.get(edge.target);
        if (!sp || !tp) continue;
        const x1 = sp.x + sp.width, y1 = sp.y + sp.height / 2;
        const x2 = tp.x, y2 = tp.y + tp.height / 2;
        const curve = Math.max(70, (x2 - x1) * 0.5);
        const active = selectedId && activeIds.has(edge.source) && activeIds.has(edge.target);
        html += `<path class="edge ${active ? "active" : ""}" d="M ${x1} ${y1} C ${x1 + curve} ${y1}, ${x2 - curve} ${y2}, ${x2} ${y2}" stroke-width="${active ? 2 : 1}" opacity="${active ? 0.9 : 0.7}" />`;
      }
      for (const node of visibleNodes) {
        const pos = positions.get(node.id);
        const selected = selectedId === node.id;
        const match = term && nodeMatches(node, term, "all");
        html += `
          <g class="node ${selected ? "is-selected" : ""} ${match ? "is-match" : ""}" data-node-id="${node.id}" style="cursor:pointer;">
            <rect x="${pos.x}" y="${pos.y}" width="${pos.width}" height="${pos.height}" fill="${stageFill(node)}" fill-opacity="${node.kind === "raw" ? 0.40 : 0.18}" stroke="${selected ? "rgba(28,28,24,0.9)" : "rgba(28,28,24,0.12)"}"></rect>
            <text x="${pos.x + 10}" y="${pos.y + 16}">${truncate(node.label)}</text>
          </g>
        `;
      }
      svg.innerHTML = html;
      svg.querySelectorAll("[data-node-id]").forEach((el) => {
        el.addEventListener("click", () => {
          selectedId = el.getAttribute("data-node-id");
          renderDetail(selectedId);
          render();
        });
      });
      renderDetail(selectedId);
    }

    searchInput.addEventListener("input", render);
    confidenceSelect.addEventListener("change", render);
    buildSummary();
    render();
  </script>
</body>
</html>
"""


def main() -> None:
    graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    lineage = graph.get("lineage")
    if not lineage:
        raise SystemExit("graph.json no contiene seccion lineage. Ejecuta wiki_graph.py primero.")

    html = HTML_TEMPLATE.replace(
        "__DATA__",
        json.dumps(lineage, ensure_ascii=False),
    )
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"lineage map renderizado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
