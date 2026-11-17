const count = new Intl.NumberFormat("en-US");
const percent = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 });
const svgNamespace = "http://www.w3.org/2000/svg";

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function svgNode(tag, attributes, text) {
  const element = document.createElementNS(svgNamespace, tag);
  for (const [key, value] of Object.entries(attributes || {})) element.setAttribute(key, value);
  if (text !== undefined) element.textContent = text;
  return element;
}

function link(text, path, className) {
  const anchor = node("a", text, className);
  anchor.href = path;
  return anchor;
}

async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Request failed (HTTP ${response.status}).`);
  }
  return response.json();
}

function section(root, id, title, caption, filename) {
  const figure = node("figure", "", "card research-figure");
  figure.id = `research-${id}`;
  figure.setAttribute("aria-labelledby", `${figure.id}-heading`);
  const header = node("header", "", "research-figure-heading");
  const heading = node("h3", title);
  heading.id = `${figure.id}-heading`;
  const actions = node("div", "", "research-figure-links");
  const download = link("Download vector PDF", `/research/${filename}.pdf`, "text-button");
  download.download = `${filename}.pdf`;
  actions.append(download);
  const panels = node("div", "", "research-panels");
  header.append(heading, actions);
  figure.append(header, panels, node("figcaption", caption, "research-caption"));
  root.append(figure);
  return panels;
}

function panel(parent, title, description) {
  const section = node("section", "", "research-panel");
  const heading = node("h4", title);
  heading.id = `research-panel-${title.toLowerCase().replace(/[^a-z]+/g, "-")}`;
  section.setAttribute("aria-labelledby", heading.id);
  const graph = node("div", "", "research-graph");
  const details = node("div", "", "research-panel-controls");
  section.append(heading, node("p", description, "research-panel-description"), graph, details);
  parent.append(section);
  return { graph, details };
}

function field(id, label, rows, value, labelFor) {
  const wrapper = node("label", label, "research-field");
  wrapper.htmlFor = id;
  const select = node("select");
  select.id = id;
  for (const row of rows) {
    const option = node("option", labelFor(row));
    option.value = value(row);
    select.append(option);
  }
  wrapper.append(select);
  return { wrapper, select };
}

function graph(container, accessibleName, limits, options) {
  const width = 540;
  const height = 302;
  const left = options.left ?? 68;
  const right = 515;
  const top = 16;
  const bottom = 249;
  const xScale = options.xScale ?? (value => value);
  const yScale = options.yScale ?? (value => value);
  const scale = (value, min, max, start, stop, transform) =>
    start + (transform(value) - transform(min)) / (transform(max) - transform(min)) * (stop - start);
  const x = value => scale(value, limits[0], limits[1], left, right, xScale);
  const y = value => scale(value, limits[2], limits[3], bottom, top, yScale);
  const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": accessibleName });
  svg.classList.add("research-svg");
  const grid = svgNode("g", { class: "research-grid" });
  const texts = svgNode("g", { class: "research-ticks" });
  for (const value of options.xTicks) {
    if (options.verticalGrid) {
      grid.append(svgNode("line", { x1: x(value), x2: x(value), y1: top, y2: bottom }));
    }
    texts.append(svgNode("text", { x: x(value), y: bottom + 18, "text-anchor": "middle" },
      options.xFormat ? options.xFormat(value) : String(value)));
  }
  for (const value of options.yTicks) {
    grid.append(svgNode("line", { x1: left, x2: right, y1: y(value), y2: y(value) }));
    texts.append(svgNode("text", { x: left - 8, y: y(value) + 4, "text-anchor": "end" },
      options.yFormat ? options.yFormat(value) : String(value)));
  }
  const axes = svgNode("path", { d: `M ${left} ${top} V ${bottom} H ${right}`, class: "research-axes" });
  const labels = svgNode("g", { class: "research-axis-title" });
  labels.append(
    svgNode("text", { x: (left + right) / 2, y: 286, "text-anchor": "middle" }, options.xLabel),
    svgNode("text", { transform: `translate(20 ${(top + bottom) / 2}) rotate(-90)`,
      "text-anchor": "middle" }, options.yLabel),
  );
  const marks = svgNode("g");
  svg.append(grid, axes, texts, labels, marks);
  container.append(svg);
  return { svg, marks, x, y };
}

function point(chart, mark, value, label, choose) {
  mark.classList.add("research-mark");
  mark.dataset.choice = value;
  mark.append(svgNode("title", {}, label));
  mark.addEventListener("click", () => choose(String(value)));
  chart.marks.append(mark);
  return mark;
}

function legend(parent, items) {
  const list = node("ul", "", "research-legend");
  for (const [style, caption] of items) {
    const item = node("li");
    const swatch = node("span", "", `research-key research-key-${style}`);
    swatch.setAttribute("aria-hidden", "true");
    item.append(swatch, document.createTextNode(caption));
    list.append(item);
  }
  parent.append(list);
}

function choices(panel, chart, rows, { id, label, value, option, initial, summary, extra, changed }) {
  const { wrapper, select } = field(id, label, rows, value, option);
  const form = node("div", "", "research-fields");
  const report = node("p", "", "research-selection");
  report.setAttribute("aria-live", "polite");
  const selectedRows = new Map(rows.map(row => [String(value(row)), row]));
  let selectedMarks = [];
  function update() {
    const row = selectedRows.get(select.value);
    report.textContent = summary(row);
    for (const mark of selectedMarks) mark.classList.remove("is-selected");
    selectedMarks = [...chart.marks.querySelectorAll("[data-choice]")].filter(mark =>
      mark.dataset.choice === select.value);
    for (const mark of selectedMarks) mark.classList.add("is-selected");
    if (changed) changed(row);
  }
  function choose(newValue) {
    select.value = newValue;
    update();
  }
  form.append(wrapper, ...(extra || []));
  panel.details.append(form, report);
  select.addEventListener("change", update);
  return { choose, current: () => selectedRows.get(select.value), initialize: () => choose(String(initial)) };
}

function recordAction(panel, select, lookup, openRecords, singular = false) {
  const button = node("button", singular ? "Open source record" : "Open source records", "text-button");
  button.type = "button";
  const status = node("p", "", "research-status");
  status.setAttribute("role", "status");
  button.addEventListener("click", async () => {
    const { query, title } = lookup(select());
    button.disabled = true;
    status.classList.remove("error");
    status.textContent = "Looking up archive records…";
    try {
      const params = new URLSearchParams(query);
      const result = await request(`/api/research/records?${params}`);
      if (result.ids.length === 0) {
        status.textContent = "No archive records match this selection.";
      } else {
        await openRecords(result.ids, result.label || title, params);
        status.textContent = `Opened ${count.format(result.matched)} archive ${singular ? "record" : "records"}.`;
      }
    } catch (error) {
      status.textContent = error.message;
      status.classList.add("error");
    } finally {
      button.disabled = false;
    }
  });
  let actions = panel.details.querySelector(".research-actions");
  if (!actions) {
    actions = node("div", "", "research-actions");
    panel.details.append(actions);
  }
  actions.append(button);
  panel.details.append(status);
}

function atlas(root, data, openRecords) {
  const catalog = data.catalog;
  const figure = section(root, "atlas", "Hodge and Euler atlas",
    `The Hodge panel covers ${count.format(catalog.nonproduct_hodge_pairs)} pairs from ` +
    `${count.format(catalog.nonproduct_records)} non-product presentations. The Euler panel also includes ` +
    `${count.format(catalog.products)} product rows, all at χ = 0. The dashed line shows the archive median.`,
    "cicy3-atlas");
  const hodge = panel(figure, "Hodge pairs", "Select a point or choose a pair to inspect its presentations.");
  const pairs = catalog.hodge_pairs;
  const hodgeGraph = graph(hodge.graph, "Scatter plot of non-product Hodge pairs, sized by record count",
    [0, 20, 10, 110], { xTicks: [0, 5, 10, 15, 20], yTicks: [20, 40, 60, 80, 100],
      xLabel: "h¹·¹", yLabel: "h²·¹", verticalGrid: true });
  const hodgeKey = row => `${row.h11},${row.h21}`;
  const hodgeLabel = row => `(${row.h11}, ${row.h21}) · ${count.format(row.records)} records`;
  const selectedHodge = choices(hodge, hodgeGraph, pairs, {
    id: "research-hodge", label: "Hodge pair", value: hodgeKey, option: hodgeLabel,
    initial: hodgeKey(pairs[0]), summary: row => `${hodgeLabel(row)} in the non-product archive.`,
  });
  for (const row of [...pairs].reverse()) {
    const mark = svgNode("circle", {
      cx: hodgeGraph.x(row.h11), cy: hodgeGraph.y(row.h21), r: 3.4 + 1.35 * Math.log10(row.records),
      class: "research-dot", opacity: 0.60 + Math.log10(row.records) / 8,
    });
    point(hodgeGraph, mark, hodgeKey(row), hodgeLabel(row), selectedHodge.choose);
  }
  for (const [name, label] of [["quintic", "Quintic"], ["bicubic", "Bicubic"]]) {
    const fixture = data.fixtures[name];
    hodgeGraph.marks.append(svgNode("text", {
      x: hodgeGraph.x(fixture.h11) + 9, y: hodgeGraph.y(fixture.h21) - 4, class: "research-annotation",
    }, label));
  }
  selectedHodge.initialize();
  legend(hodge.graph, [["dot", "Larger markers indicate more presentations"]]);
  recordAction(hodge, selectedHodge.current, row => ({
    query: { figure: "atlas", h11: row.h11, h21: row.h21 }, title: `Hodge pair (${row.h11}, ${row.h21})`,
  }), openRecords);

  const euler = panel(figure, "Euler counts", "The archive contributes one count for each configuration ID.");
  const eulers = catalog.euler_counts;
  const total = row => row.nonproducts + row.products;
  const mode = eulers.reduce((largest, row) => total(row) > total(largest) ? row : largest);
  const eulerGraph = graph(euler.graph, "Stacked counts of archive rows by exact Euler characteristic",
    [-207, 7, 0, 700], { xTicks: [-200, -150, -100, -50, 0], yTicks: [0, 200, 400, 600],
      xLabel: "Euler characteristic χ", yLabel: "Archive records" });
  const groups = field("research-euler-population", "Population", ["all", "0", "1"],
    value => value, value => ({ all: "All rows", 0: "Non-products", 1: "Products" })[value]);
  const selectedEuler = choices(euler, eulerGraph, eulers, {
    id: "research-euler", label: "Euler characteristic", value: row => row.euler,
    option: row => `${row.euler} · ${count.format(total(row))} records`,
    initial: mode.euler, extra: [groups.wrapper],
    summary: row => `χ = ${row.euler} · ${count.format(row.nonproducts)} non-products and ${count.format(row.products)} products.`,
  });
  eulerGraph.marks.append(svgNode("line", {
    x1: eulerGraph.x(catalog.median_euler), x2: eulerGraph.x(catalog.median_euler),
    y1: eulerGraph.y(0), y2: eulerGraph.y(700), class: "research-reference-line",
  }));
  const barWidth = 3.2;
  for (const row of eulers) {
    const mark = svgNode("g");
    const position = eulerGraph.x(row.euler) - barWidth / 2;
    const base = eulerGraph.y(0);
    const nonproducts = eulerGraph.y(row.nonproducts);
    const top = eulerGraph.y(total(row));
    mark.append(svgNode("rect", { x: position - .35, y: Math.min(top, base - 8),
      width: barWidth + .7, height: base - Math.min(top, base - 8), class: "research-hit" }));
    mark.append(svgNode("rect", { x: position, y: nonproducts, width: barWidth,
      height: base - nonproducts, class: "research-fill" }));
    if (row.products) {
      mark.append(svgNode("rect", { x: position, y: top, width: barWidth,
        height: nonproducts - top, class: "research-warm" }));
    }
    point(eulerGraph, mark, row.euler, `χ = ${row.euler} · ${count.format(total(row))} records`, selectedEuler.choose);
  }
  selectedEuler.initialize();
  legend(euler.graph, [["fill", "Non-products"], ["warm", "Products"], ["line", "Median"]]);
  recordAction(euler, selectedEuler.current, row => {
    const population = groups.select.value;
    const query = { figure: "atlas", euler: row.euler };
    if (population !== "all") query.product = population;
    return { query, title: `χ = ${row.euler}${population === "all" ? "" : population === "1" ? " · products" : " · non-products"}` };
  }, openRecords);
}

function structure(root, data, openRecords) {
  const catalog = data.catalog;
  const figure = section(root, "structure", "Configuration shape and favorability",
    `Configuration dimensions count all ${count.format(catalog.records)} archive rows. Favorability uses the ` +
    `${count.format(catalog.nonproduct_records)} non-product rows and the archive's Favour flag.`, "cicy3-structure");
  const shape = panel(figure, "Configuration sizes", "A cell groups matrices by number of rows and columns.");
  const maximum = catalog.modal_shape;
  const shapes = catalog.shape_counts;
  const factorsMax = Math.max(...shapes.map(row => row.factors));
  const codimensionMax = Math.max(...shapes.map(row => row.codimension));
  const shapeGraph = graph(shape.graph, "Heatmap of configuration matrix sizes over all published records",
    [.5, factorsMax + .5, .5, codimensionMax + .5], {
      xTicks: [1, 3, 5, 7, 9, 11, factorsMax].filter((value, index, ticks) => ticks.indexOf(value) === index),
      yTicks: Array.from({ length: Math.ceil(codimensionMax / 2) }, (_, i) => 2 * i + 1),
      xLabel: "Ambient projective factors", yLabel: "Defining equations",
    },
  );
  const shapeKey = row => `${row.factors},${row.codimension}`;
  const shapeLabel = row => `${row.factors} × ${row.codimension} · ${count.format(row.records)} records`;
  const selectedShape = choices(shape, shapeGraph, shapes, {
    id: "research-shape", label: "Matrix shape", value: shapeKey, option: shapeLabel,
    initial: shapeKey(maximum), summary: row => `${shapeLabel(row)} in the archive.`,
  });
  const shapeWidth = shapeGraph.x(1.5) - shapeGraph.x(.5);
  const shapeHeight = shapeGraph.y(.5) - shapeGraph.y(1.5);
  for (const row of shapes) {
    const intensity = .22 + .78 * Math.log10(row.records) / Math.log10(maximum.records);
    const mark = svgNode("rect", { x: shapeGraph.x(row.factors) - shapeWidth / 2 + 1,
      y: shapeGraph.y(row.codimension) - shapeHeight / 2 + 1, width: shapeWidth - 2,
      height: shapeHeight - 2, rx: 2, class: "research-fill", opacity: intensity });
    point(shapeGraph, mark, shapeKey(row), shapeLabel(row), selectedShape.choose);
  }
  selectedShape.initialize();
  legend(shape.graph, [["fill", "Darker cells indicate more records (log scale)"]]);
  recordAction(shape, selectedShape.current, row => ({
    query: { figure: "structure", factors: row.factors, codimension: row.codimension },
    title: `Configuration shape ${row.factors} × ${row.codimension}`,
  }), openRecords);

  const favour = panel(figure, "Favorability by ambient factors", "Each share uses the non-product records in its factor group.");
  const rates = catalog.favourability;
  const favourGraph = graph(favour.graph, "Fraction of non-product records flagged favorable by ambient factors",
    [0, 1, .5, factorsMax + .5], {
      xTicks: [0, .25, .5, .75, 1], xFormat: percent.format, yTicks: rates.map(row => row.factors),
      xLabel: "Fraction with Favour flag", yLabel: "Ambient projective factors", verticalGrid: true,
    },
  );
  const favourLabel = row => `${row.factors} factors · ${percent.format(row.favourable / row.records)} favorable`;
  const groups = field("research-favourable-population", "Flag", ["all", "1", "0"],
    value => value, value => ({ all: "All non-products", 1: "Favorable", 0: "Unflagged" })[value]);
  const selectedRate = choices(favour, favourGraph, rates, {
    id: "research-factors", label: "Ambient factors", value: row => row.factors, option: favourLabel,
    initial: maximum.factors, extra: [groups.wrapper],
    summary: row => `${count.format(row.favourable)} of ${count.format(row.records)} non-products are flagged favorable ` +
      `(${percent.format(row.favourable / row.records)}).`,
  });
  const height = favourGraph.y(.5) - favourGraph.y(1.5) - 5;
  for (const row of rates) {
    const mark = svgNode("g");
    const top = favourGraph.y(row.factors) - height / 2;
    mark.append(
      svgNode("rect", { x: favourGraph.x(0), y: top, width: favourGraph.x(1) - favourGraph.x(0),
        height, rx: 3, class: "research-track" }),
      svgNode("rect", { x: favourGraph.x(0), y: top,
        width: favourGraph.x(row.favourable / row.records) - favourGraph.x(0),
        height, rx: 3, class: "research-fill" }),
    );
    point(favourGraph, mark, row.factors, favourLabel(row), selectedRate.choose);
  }
  selectedRate.initialize();
  legend(favour.graph, [["fill", "Flagged favorable"], ["track", "Remaining share"]]);
  recordAction(favour, selectedRate.current, row => {
    const flag = groups.select.value;
    const query = { figure: "structure", factors: row.factors };
    if (flag !== "all") query.favourable = flag;
    return { query, title: `${row.factors} ambient factors · ${flag === "all" ? "non-products" : flag === "1" ? "favorable" : "unflagged"}` };
  }, openRecords);
}

function drawPath(chart, rows, xFor, yFor, className) {
  chart.marks.append(svgNode("polyline", {
    points: rows.map(row => `${chart.x(xFor(row))},${chart.y(yFor(row))}`).join(" "),
    class: className,
  }));
}

function multiplicity(root, data, openRecords) {
  const catalog = data.catalog;
  const figure = section(root, "multiplicity", "Hodge-pair concentration and multiplicity",
    `The cumulative curve weights each non-product presentation once. The histogram weights each of the ` +
    `${count.format(catalog.nonproduct_hodge_pairs)} distinct non-product Hodge pairs once.`, "cicy3-multiplicity");
  const concentration = panel(figure, "Concentration by rank", "Hodge pairs are ranked by decreasing presentation count.");
  let cumulative = 0;
  const rows = catalog.hodge_pairs.map((row, i) => {
    cumulative += row.records;
    return { ...row, rank: i + 1, cumulative };
  });
  const population = catalog.nonproduct_records;
  const ranks = rows.length;
  const rankGraph = graph(concentration.graph, "Cumulative share of non-product records ranked by pair multiplicity",
    [1, ranks, 0, 1], {
      xScale: Math.log10, xTicks: [1, 5, 10, 25, 50, 100, ranks],
      yTicks: [0, .25, .5, .75, 1], yFormat: percent.format,
      xLabel: "Hodge-pair rank (log scale)", yLabel: "Cumulative share of records", verticalGrid: true,
    },
  );
  const rankLabel = row => `#${row.rank} · (${row.h11}, ${row.h21}) · ${count.format(row.records)} records`;
  const rankMode = field("research-rank-scope", "Scope", ["through", "rank"], value => value,
    value => value === "through" ? "All pairs through rank" : "Selected pair only");
  const selectedRank = choices(concentration, rankGraph, rows, {
    id: "research-rank", label: "Hodge-pair rank", value: row => row.rank, option: rankLabel,
    initial: catalog.pairs_to_half, extra: [rankMode.wrapper],
    summary: row => `Ranks 1–${row.rank} cover ${count.format(row.cumulative)} of ${count.format(population)} ` +
      `non-product records (${percent.format(row.cumulative / population)}). Pair (${row.h11}, ${row.h21}) has ` +
      `${count.format(row.records)} records.`,
  });
  drawPath(rankGraph, rows, row => row.rank, row => row.rank / ranks, "research-reference-line");
  drawPath(rankGraph, rows, row => row.rank, row => row.cumulative / population, "research-trace-line");
  for (const row of rows) {
    const mark = svgNode("circle", { cx: rankGraph.x(row.rank), cy: rankGraph.y(row.cumulative / population),
      r: row.rank === catalog.pairs_to_half ? 5 : 4, class: "research-rank-dot" });
    point(rankGraph, mark, row.rank, rankLabel(row), selectedRank.choose);
  }
  selectedRank.initialize();
  legend(concentration.graph, [["fill", "Observed share"], ["line", "Equal presentations per pair"]]);
  recordAction(concentration, selectedRank.current, row => {
    if (rankMode.select.value === "rank") {
      return { query: { figure: "multiplicity", rank: row.rank }, title: `Hodge-pair rank ${row.rank} · (${row.h11}, ${row.h21})` };
    }
    return { query: { figure: "multiplicity", through: row.rank }, title: `Top ${row.rank} ranked Hodge pairs` };
  }, openRecords);

  const distribution = panel(figure, "Multiplicity distribution", "Select a bar to inspect presentations in that frequency band.");
  const bins = catalog.multiplicity_bins.map((row, position) => ({ ...row, position }));
  const binKey = row => `${row.min},${row.max ?? ""}`;
  const binLabel = row => row.max === null ? `${row.min}+` : row.max === row.min ? String(row.min) : `${row.min}–${row.max}`;
  const binGraph = graph(distribution.graph, "Distinct non-product Hodge pairs grouped by presentation count",
    [-.6, bins.length - .4, 0, 80], {
      xTicks: bins.map(row => row.position), xFormat: n => binLabel(bins[n]),
      yTicks: [0, 20, 40, 60, 80], xLabel: "Presentations per Hodge pair", yLabel: "Distinct Hodge pairs",
    },
  );
  const selectedBin = choices(distribution, binGraph, bins, {
    id: "research-multiplicity-bin", label: "Presentation count per pair", value: binKey,
    option: row => `${binLabel(row)} · ${count.format(row.pairs)} pairs`,
    initial: binKey(bins[0]),
    summary: row => `${count.format(row.pairs)} distinct Hodge pairs in the ${binLabel(row)}-presentation band.`,
  });
  const barWidth = (binGraph.x(1) - binGraph.x(0)) * .73;
  for (const row of bins) {
    const x = binGraph.x(row.position);
    const y = binGraph.y(row.pairs);
    const mark = svgNode("g");
    mark.append(
      svgNode("rect", { x: x - barWidth / 2, y, width: barWidth, height: binGraph.y(0) - y,
        rx: 3, class: "research-fill" }),
      svgNode("text", { x, y: y - 7, "text-anchor": "middle", class: "research-annotation" }, row.pairs),
    );
    point(binGraph, mark, binKey(row), `${binLabel(row)} presentations · ${row.pairs} pairs`, selectedBin.choose);
  }
  selectedBin.initialize();
  recordAction(distribution, selectedBin.current, row => {
    const query = { figure: "multiplicity", min: row.min };
    if (row.max !== null) query.max = row.max;
    return { query, title: `Hodge pairs with ${binLabel(row)} presentations` };
  }, openRecords);
}

const cohomologyLabels = {
  h0_only: "H⁰ only", h3_only: "H³ only", acyclic: "Acyclic", unsupported: "Unsupported cohomology dimensions",
};

function bundleValues(dimensions, index) {
  const values = dimensions === null ? "Cohomology dimensions unsupported" :
    `(h⁰, h¹, h², h³) = (${dimensions.map(value => count.format(value)).join(", ")})`;
  return `${values} · index χ = ${count.format(index)}`;
}

function runAction(panel, selection, payloadFor) {
  const button = node("button", "Rerun in Python", "button run-button");
  button.type = "button";
  const actions = node("div", "", "research-actions");
  const result = node("div", "", "research-run-result");
  result.setAttribute("role", "status");
  actions.append(button);
  panel.details.append(actions, result);
  button.addEventListener("click", async () => {
    const source = selection();
    const payload = payloadFor(source);
    button.disabled = true;
    result.classList.remove("error");
    result.textContent = "Running the native Python methods…";
    try {
      const run = await request("/api/research/rerun", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      });
      if (source !== selection()) {
        result.textContent = "Selection changed. Rerun the current charge to see its result.";
        return;
      }
      const heading = run.matches_manuscript ? "Python result matches the manuscript" :
        "Python result differs from the manuscript";
      result.replaceChildren(
        node("strong", heading),
        node("p", bundleValues(run.dimensions, run.index)),
      );
      if (run.reason) result.append(node("p", run.reason));
      if (!run.matches_manuscript) result.classList.add("error");
    } catch (error) {
      result.textContent = error.message;
      result.classList.add("error");
    } finally {
      button.disabled = false;
    }
  });
  return () => {
    result.textContent = "";
    result.classList.remove("error");
  };
}

function cohomology(root, data, openRecords) {
  const { quintic, bicubic } = data.cohomology;
  const figure = section(root, "cohomology", "Exact line-bundle calculations",
    `Native Python agrees with the independent quintic calculation at all ${quintic.cohomology_matches} plotted charges ` +
    `and the bicubic index at all ${bicubic.index_matches} charge pairs. ${bicubic.unsupported} bicubic pairs have an index ` +
    "and fall outside the native cohomology dimension method's domain.", "line-bundle-cohomology");
  const quinticPanel = panel(figure, "Quintic dimensions and index", "Select an integer charge to replay the manuscript calculation.");
  const signedLog = value => Math.sign(value) * Math.log10(1 + Math.abs(value));
  const max = Math.max(...quintic.rows.map(row => Math.abs(row.index)));
  const [kMin, kMax] = quintic.charge_range;
  const quinticGraph = graph(quinticPanel.graph, "Quintic h⁰, negative h³ and index on a symmetric logarithmic scale",
    [kMin - .35, kMax + .35, -max * 1.16, max * 1.16], {
      xTicks: [kMin, -5, 0, 5, kMax], yTicks: [-max, -100, -10, -1, 0, 1, 10, 100, max], yScale: signedLog,
      xLabel: "Integer charge k", yLabel: "Signed dimension / index (symlog)", verticalGrid: true,
    });
  drawPath(quinticGraph, quintic.rows, row => row.k, row => row.index, "research-reference-line");
  let clearQuintic;
  const selectedQuintic = choices(quinticPanel, quinticGraph, quintic.rows, {
    id: "research-quintic-charge", label: "Quintic charge k", value: row => row.k,
    option: row => `k = ${row.k}`, initial: 0,
    summary: row => `Manuscript · ${bundleValues(row.dimensions, row.index)}`,
    changed: () => clearQuintic?.(),
  });
  for (const row of quintic.rows) {
    const x = quinticGraph.x(row.k);
    const mark = svgNode("g");
    const y0 = quinticGraph.y(row.dimensions[0]);
    const y3 = quinticGraph.y(-row.dimensions[3]);
    mark.append(svgNode("rect", { x: x - 9, y: quinticGraph.y(max * 1.16),
      width: 18, height: quinticGraph.y(-max * 1.16) - quinticGraph.y(max * 1.16), class: "research-hit" }));
    if (row.dimensions[0]) mark.append(svgNode("circle", { cx: x, cy: y0, r: 5, class: "research-dot" }));
    if (row.dimensions[3]) mark.append(svgNode("path", {
      d: `M ${x} ${y3 - 5} L ${x + 5} ${y3 + 5} H ${x - 5} Z`, class: "research-coh3",
    }));
    point(quinticGraph, mark, row.k, `k = ${row.k} · ${bundleValues(row.dimensions, row.index)}`, selectedQuintic.choose);
  }
  selectedQuintic.initialize();
  legend(quinticPanel.graph, [["dot", "h⁰"], ["triangle", "−h³"], ["line", "Index χ"]]);
  clearQuintic = runAction(quinticPanel, selectedQuintic.current,
    row => ({ figure: "cohomology", geometry: "quintic", k: row.k }));
  recordAction(quinticPanel, selectedQuintic.current, () => ({
    query: { figure: "cohomology", geometry: "quintic" }, title: `Quintic · archive record ${quintic.record}`,
  }), openRecords, true);

  const bicubicPanel = panel(figure, "Bicubic charge grid", "Select a charge pair to compute its index and available dimensions.");
  const [aMin, aMax] = bicubic.charge_range_per_axis;
  const limits = [aMin - .5, aMax + .5, aMin - .5, aMax + .5];
  const ticks = [aMin, -4, 0, 4, aMax];
  const bicubicGraph = graph(bicubicPanel.graph, "Bicubic charge lattice colored by native cohomology outcome",
    limits, { xTicks: ticks, yTicks: ticks, xLabel: "Bicubic charge a", yLabel: "Bicubic charge b", verticalGrid: true });
  const rows = new Map(bicubic.rows.map(row => [`${row.a},${row.b}`, row]));
  const charges = Array.from({ length: aMax - aMin + 1 }, (_, i) => aMin + i);
  const a = field("research-bicubic-a", "Bicubic charge a", charges, value => value, value => String(value));
  const b = field("research-bicubic-b", "Bicubic charge b", charges, value => value, value => String(value));
  const fields = node("div", "", "research-fields");
  fields.append(a.wrapper, b.wrapper);
  const summary = node("p", "", "research-selection");
  summary.setAttribute("aria-live", "polite");
  bicubicPanel.details.append(fields, summary);
  const current = () => rows.get(`${a.select.value},${b.select.value}`);
  const marks = new Map();
  let selectedMark;
  let clearBicubic;
  function updateBicubic() {
    const row = current();
    selectedMark?.classList.remove("is-selected");
    selectedMark = marks.get(`${row.a},${row.b}`);
    selectedMark.classList.add("is-selected");
    summary.textContent = `Manuscript · ${bundleValues(row.dimensions, row.index)}`;
    clearBicubic?.();
  }
  for (const row of bicubic.rows) {
    const x = bicubicGraph.x(row.a);
    const y = bicubicGraph.y(row.b);
    const key = `${row.a},${row.b}`;
    const mark = svgNode("g");
    mark.append(svgNode("rect", { x: x - 11, y: y - 6.4, width: 22, height: 12.8, class: "research-hit" }));
    const dimension = row.dimensions ? Math.max(...row.dimensions) : 0;
    const r = 2.75 + Math.log10(Math.max(1, dimension)) * .65;
    if (row.status === "h0_only") mark.append(svgNode("circle", { cx: x, cy: y, r, class: "research-dot" }));
    if (row.status === "h3_only") mark.append(svgNode("path", {
      d: `M ${x} ${y - r} L ${x + r} ${y + r} H ${x - r} Z`, class: "research-coh3",
    }));
    if (row.status === "acyclic") mark.append(svgNode("rect", {
      x: x - 3.5, y: y - 3.5, width: 7, height: 7, class: "research-coh-empty",
    }));
    if (row.status === "unsupported") mark.append(svgNode("path", {
      d: `M ${x - 2.8} ${y - 2.8} l 5.6 5.6 m 0 -5.6 l -5.6 5.6`, class: "research-coh-unsupported",
    }));
    marks.set(key, point(bicubicGraph, mark, key,
      `(${row.a}, ${row.b}) · ${cohomologyLabels[row.status]} · index χ = ${row.index}`, () => {
        a.select.value = row.a;
        b.select.value = row.b;
        updateBicubic();
      }));
  }
  a.select.addEventListener("change", updateBicubic);
  b.select.addEventListener("change", updateBicubic);
  a.select.value = "1";
  b.select.value = "0";
  updateBicubic();
  legend(bicubicPanel.graph, [["dot", "H⁰ only"], ["triangle", "H³ only"], ["empty", "Acyclic"],
    ["cross", "Unsupported dimensions"]]);
  clearBicubic = runAction(bicubicPanel, current,
    row => ({ figure: "cohomology", geometry: "bicubic", a: row.a, b: row.b }));
  recordAction(bicubicPanel, current, () => ({
    query: { figure: "cohomology", geometry: "bicubic" }, title: `Bicubic · archive record ${bicubic.record}`,
  }), openRecords, true);
}

const figures = [
  ["atlas", "Hodge and Euler atlas", atlas],
  ["multiplicity", "Hodge-pair multiplicity", multiplicity],
  ["structure", "Configuration structure", structure],
  ["cohomology", "Line-bundle calculations", cohomology],
];

function intro(root) {
  const cover = node("header", "", "research-cover");
  const text = node("div", "", "research-cover-copy");
  const header = node("h2", "CIPro research manuscript");
  header.id = "research-heading";
  root.setAttribute("aria-labelledby", header.id);
  const title = node("p", "", "research-paper-title");
  const actions = node("div", "", "research-cover-actions");
  const manuscript = link("Open manuscript PDF", "/research/manuscript.pdf", "button hero-button");
  manuscript.target = "_blank";
  manuscript.rel = "noopener";
  const figuresLink = link("Explore the figures", "#research-figures", "button secondary-hero");
  actions.append(manuscript, figuresLink);
  text.append(header, title,
    node("p", "Inspect the four figures, trace each selection to the archive, and rerun exact calculations with Python."),
    actions);
  const provenance = node("dl", "", "research-provenance");
  provenance.hidden = true;
  cover.append(text, provenance);
  root.append(cover);
  return { title, provenance };
}

function showProvenance(display, data) {
  if (data.manuscript_title) display.title.textContent = data.manuscript_title;
  for (const [label, value] of [
    ["Rendered manuscript", data.manuscript_pages && `${data.manuscript_pages} pages`],
    ["Source revision", data.source_commit?.slice(0, 12)],
    ["Template version", data.template_version],
    ["Archive member SHA-256", data.dataset_sha256?.slice(0, 12)],
  ]) {
    if (!value) continue;
    const pair = node("div");
    pair.append(node("dt", label), node("dd", value));
    display.provenance.append(pair);
  }
  display.provenance.hidden = !display.provenance.children.length;
}

export async function initializeResearch({ openRecords }) {
  const root = document.querySelector("#research");
  if (!root) return;
  root.classList.add("research-workspace");
  root.replaceChildren();
  const display = intro(root);
  const provenance = request("/api/research/provenance").then(data => showProvenance(display, data)).catch(() => {});
  const jump = node("div", "", "research-jump");
  jump.id = "research-figures";
  const heading = node("h3", "Interactive manuscript figures");
  const links = node("div", "", "research-jump-links");
  for (const [id, title] of figures) links.append(link(title, `#research-${id}`, "text-button"));
  jump.append(heading, links);
  root.append(jump);
  const status = node("p", "Loading manuscript figure data…", "research-status");
  status.setAttribute("role", "status");
  root.append(status);
  try {
    const data = await request("/api/research");
    const rendered = document.createDocumentFragment();
    for (const [, , render] of figures) render(rendered, data, openRecords);
    root.append(rendered);
    status.remove();
    if (figures.some(([id]) => location.hash === `#research-${id}`)) {
      document.getElementById(location.hash.slice(1)).scrollIntoView();
    }
  } catch (error) {
    status.textContent = `Figure data unavailable. ${error.message}`;
    status.classList.add("error");
    const retry = node("button", "Retry figure data", "text-button");
    retry.type = "button";
    retry.addEventListener("click", () => initializeResearch({ openRecords }));
    root.append(retry);
  }
  await provenance;
}
