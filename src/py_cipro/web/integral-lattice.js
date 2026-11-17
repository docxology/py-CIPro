const key = row => `${row.cubic_content},${row.chern_content}`;
const superscripts = { 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const superscript = value => String(value).replace(/\d/g, digit => superscripts[digit]);

export function renderIntegralLattice(root, data, openRecords, ui) {
  const { section, panel, field, node, svgNode, runAction, recordAction, count } = ui;
  const { summary, rows, witness } = data;
  const records = new Map(rows.map(row => [row.id, row]));
  const figure = section(root, "integral-invariants", "Integral lattice divisibility",
    `Cubic and Chern content group ${count.format(summary.records)} non-product presentations into ` +
    `${summary.joint_pairs} occupied cells. ${summary.split_hodge_groups} of ${summary.hodge_groups} Hodge groups ` +
    `and ${summary.split_euler_groups} of ${summary.euler_groups} Euler groups contain multiple content pairs. ` +
    "The census concerns the ambient divisor lattice. The two ample rank-one witnesses identify the full integral lattice by weak Lefschetz.",
    "integral-invariants", true);
  figure.classList.add("integral-panels");

  const census = panel(figure, "A · Exact joint census", "Filter the archive, then choose a cell or its entry in the list. Cell values count presentations; stronger color shows more records on a logarithmic scale.");
  const inspection = panel(figure, "B · Equal Hodge numbers, different integral content", "The two rank-one complete intersections share Hodge pair (1, 73) and χ = −144. Their cubic contents differ on the full integral lattice.");

  const scope = field("research-integral-scope", "Census scope", ["all", "hodge", "euler"], value => value,
    value => ({ all: "All non-product records", hodge: "One Hodge group", euler: "One Euler group" })[value]);
  const hodge = field("research-integral-hodge", "Hodge pair", data.hodge,
    row => row.hodge.join(","), row => `(${row.hodge.join(", ")}) · ${row.cells.length} ${row.cells.length === 1 ? "cell" : "cells"}`);
  const euler = field("research-integral-euler", "Euler characteristic χ", data.euler,
    row => row.euler, row => `${row.euler} · ${row.cells.length} ${row.cells.length === 1 ? "cell" : "cells"}`);
  const filters = node("div", "", "research-fields integral-filters");
  filters.append(scope.wrapper, hodge.wrapper, euler.wrapper);
  census.graph.before(filters);
  const scopeReport = node("p", "", "research-selection integral-scope-report");
  scopeReport.setAttribute("role", "status");
  filters.after(scopeReport);

  const cell = field("research-integral-cell", "Occupied cell · cubic g₃ and Chern g₂", [], () => "", () => "");
  const cellReport = node("p", "", "research-selection");
  cellReport.setAttribute("role", "status");
  census.details.append(cell.wrapper, cellReport);
  const presets = node("div", "", "research-actions integral-presets");
  const compare = node("button", "Compare the rank-one witnesses", "text-button");
  compare.type = "button";
  const modal = node("button", `Explore modal Hodge group (${summary.modal_hodge.join(", ")})`, "text-button");
  modal.type = "button";
  presets.append(compare, modal);
  census.details.append(presets);

  const xValues = [...new Set(data.joint.map(row => row.cubic_content))].sort((a, b) => a - b);
  const yValues = [...new Set(data.joint.map(row => row.chern_content))].sort((a, b) => a - b);
  const width = 580, height = 426, left = 60, top = 12, right = 562, bottom = 365;
  const cellWidth = (right - left) / xValues.length;
  const cellHeight = (bottom - top) / yValues.length;
  const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, role: "group",
    "aria-label": "Joint lattice content census. Choose a populated cell or use the occupied-cell list below.",
    "aria-describedby": "research-integral-map-note" });
  svg.classList.add("research-svg", "integral-map");
  const marks = svgNode("g");
  const ticks = svgNode("g", { class: "research-ticks" });
  for (const [index, value] of xValues.entries()) {
    ticks.append(svgNode("text", { x: left + (index + .5) * cellWidth, y: bottom + 18, "text-anchor": "middle" }, value));
  }
  for (const [index, value] of yValues.entries()) {
    ticks.append(svgNode("text", { x: left - 8, y: bottom - (index + .5) * cellHeight + 4, "text-anchor": "end" }, value));
  }
  const labels = svgNode("g", { class: "research-axis-title" });
  labels.append(
    svgNode("text", { x: (left + right) / 2, y: height - 11, "text-anchor": "middle" }, "Cubic content g₃ · occupied integer levels"),
    svgNode("text", { transform: `translate(17 ${(top + bottom) / 2}) rotate(-90)`, "text-anchor": "middle" }, "Chern content g₂"),
  );
  svg.append(marks, ticks, labels);
  census.graph.append(svg);
  census.graph.classList.add("integral-map-scroll");
  census.graph.tabIndex = 0;
  census.graph.setAttribute("role", "region");
  census.graph.setAttribute("aria-label", "Joint lattice census; scroll horizontally on small screens");
  const mapNote = node("p", "Empty cells contain zero records. Axes list observed integer levels at equal spacing. All values are available in the occupied-cell selector.", "integral-map-note");
  mapNote.id = "research-integral-map-note";
  census.graph.append(mapNote);

  const witnesses = node("div", "", "integral-witnesses");
  const witnessButtons = new Map();
  for (const source of witness) {
    const button = node("button", "", "integral-witness");
    button.type = "button";
    button.append(node("span", `Archive #${source.id}`, "integral-witness-id"),
      node("strong", `P${superscript(source.ambient_dimension)}[${source.degrees.join(", ")}]`, "integral-witness-geometry"));
    const values = node("dl");
    for (const [label, value] of [["Cubic g₃", source.cubic_content], ["Chern g₂", source.chern_content], ["Index χ(O(1))", source.hyperplane_indices[0]]]) {
      const pair = node("div");
      pair.append(node("dt", label), node("dd", String(value)));
      values.append(pair);
    }
    button.append(values, node("span", "Inspect this witness →", "integral-witness-action"));
    button.addEventListener("click", () => setPreset("hodge", source.hodge.join(","), source));
    witnesses.append(button);
    witnessButtons.set(source.id, button);
  }
  const interpretation = node("p", "For smooth successive ample cuts, weak Lefschetz identifies H²(X, ℤ) = ℤH in both examples. The different absolute cubic evaluations obstruct an isomorphism of their integral cohomology rings.", "integral-interpretation");
  inspection.graph.append(witnesses, interpretation);
  inspection.graph.classList.add("integral-comparison");

  const record = field("research-integral-record", "Record for exact inspection and Python rerun", [], () => "", () => "");
  const detail = node("div", "", "integral-record-detail");
  detail.setAttribute("aria-live", "polite");
  const exactDisclosure = node("details", "", "method-json integral-record-json");
  const exact = node("pre");
  exact.tabIndex = 0;
  exactDisclosure.append(node("summary", "Exact study record JSON"), exact);
  inspection.details.append(record.wrapper, detail, exactDisclosure);

  let selectedCells = data.joint;
  let selectedCell = null;
  let selectedRecord = null;
  let clearResult;
  const chartCells = new Map();
  const describeCell = row => `g₃ = ${row.cubic_content} · g₂ = ${row.chern_content} · ${count.format(row.count)} ${row.count === 1 ? "record" : "records"}`;
  const hodgeGroups = new Map(data.hodge.map(row => [row.hodge.join(","), row]));
  const eulerGroups = new Map(data.euler.map(row => [String(row.euler), row]));

  function currentScope() {
    if (scope.select.value === "hodge") return hodgeGroups.get(hodge.select.value).cells;
    if (scope.select.value === "euler") return eulerGroups.get(euler.select.value).cells;
    return data.joint;
  }

  function cellQuery(source) {
    const query = { figure: "integral-invariants", cubic_content: source.cubic_content, chern_content: source.chern_content };
    if (scope.select.value === "hodge") {
      [query.h11, query.h21] = hodge.select.value.split(",");
    } else if (scope.select.value === "euler") query.euler = euler.select.value;
    return { query, title: `Integral lattice · ${describeCell(source)}` };
  }

  function showRecord(preferredId) {
    const ids = selectedCell.record_ids;
    record.select.replaceChildren(...ids.map(id => {
      const source = records.get(id);
      return new Option(`#${id} · (${source.hodge.join(", ")}) · χ = ${source.euler}`, String(id));
    }));
    if (ids.includes(preferredId)) record.select.value = String(preferredId);
    updateRecord();
  }

  function updateRecord() {
    selectedRecord = records.get(Number(record.select.value));
    const source = selectedRecord;
    const heading = node("h5", `Archive record #${source.id}`);
    const values = node("dl", "", "integral-record-values");
    for (const [label, value] of [
      ["Hodge pair", `(${source.hodge.join(", ")})`], ["Euler χ", source.euler],
      ["Cubic content g₃", source.cubic_content], ["Chern content g₂", source.chern_content],
      ["Ambient factors", source.ambient_factors], ["Archive favorable flag", source.favourable ? "Yes" : "No"],
      ["Ordered Chern pairings Tᵢ", `(${source.c2.join(", ")})`],
      ["Hyperplane indices χ(O(Hᵢ))", `(${source.hyperplane_indices.join(", ")})`],
    ]) {
      const item = node("div");
      item.append(node("dt", label), node("dd", String(value)));
      if (String(value).length > 22 || label.startsWith("Ordered") || label.startsWith("Hyperplane")) item.classList.add("integral-value-wide");
      values.append(item);
    }
    detail.replaceChildren(heading, values);
    exact.textContent = JSON.stringify(source, null, 2);
    shareStatus.textContent = "";
    shareFallback.hidden = true;
    for (const [id, button] of witnessButtons) {
      button.classList.toggle("is-selected", id === source.id);
      button.setAttribute("aria-pressed", String(id === source.id));
    }
    clearResult?.();
  }

  function selectCell(newKey, preferredId) {
    selectedCell = selectedCells.find(row => key(row) === newKey) || selectedCells[0];
    cell.select.value = key(selectedCell);
    cellReport.textContent = `${describeCell(selectedCell)} in the selected scope.`;
    for (const [choice, mark] of chartCells) {
      const selected = choice === key(selectedCell);
      mark.classList.toggle("is-selected", selected);
      mark.setAttribute("aria-pressed", String(selected));
    }
    showRecord(preferredId);
  }

  function redraw(preferredKey = key(selectedCell || witness[0]), preferredId = selectedRecord?.id) {
    hodge.wrapper.hidden = scope.select.value !== "hodge";
    euler.wrapper.hidden = scope.select.value !== "euler";
    selectedCells = currentScope();
    const indexed = new Map(selectedCells.map(row => [key(row), row]));
    const scopeName = scope.select.value === "hodge" ? `Hodge pair (${hodge.select.value.replace(",", ", ")})`
      : scope.select.value === "euler" ? `Euler characteristic χ = ${euler.select.value}` : "All non-product configurations";
    scopeReport.textContent = `${scopeName} · ${count.format(selectedCells.reduce((sum, row) => sum + row.count, 0))} records · ${selectedCells.length} occupied ${selectedCells.length === 1 ? "cell" : "cells"}.`;
    cell.select.replaceChildren(...selectedCells.map(row => new Option(describeCell(row), key(row))));
    marks.replaceChildren();
    chartCells.clear();
    const maximum = Math.max(...selectedCells.map(row => row.count));
    for (const [yIndex, y] of yValues.entries()) {
      for (const [xIndex, x] of xValues.entries()) {
        const source = indexed.get(`${x},${y}`);
        const mark = svgNode("g");
        const rect = svgNode("rect", { x: left + xIndex * cellWidth + 1, y: bottom - (yIndex + 1) * cellHeight + 1,
          width: cellWidth - 2, height: cellHeight - 2, rx: 2,
          class: source ? "integral-cell" : "integral-empty" });
        mark.append(rect);
        if (source) {
          const intensity = Math.log1p(source.count) / Math.log1p(maximum);
          rect.style.fillOpacity = String(.16 + .84 * intensity);
          mark.classList.add("integral-cell-button");
          mark.setAttribute("role", "button");
          mark.setAttribute("tabindex", "0");
          mark.setAttribute("aria-label", describeCell(source));
          mark.append(svgNode("title", {}, describeCell(source)));
          const textClass = "integral-cell-count" + (intensity > .77 ? " integral-on-dark-cell" : "") +
            (intensity > .55 ? " integral-on-bright-cell" : "");
          mark.append(svgNode("text", { x: left + (xIndex + .5) * cellWidth, y: bottom - (yIndex + .5) * cellHeight + 3.7,
            class: textClass, "text-anchor": "middle" }, source.count));
          const choose = () => selectCell(key(source));
          mark.addEventListener("click", choose);
          mark.addEventListener("keydown", event => {
            if (event.key === "Enter" || event.key === " ") { event.preventDefault(); choose(); }
          });
          chartCells.set(key(source), mark);
        } else mark.setAttribute("aria-hidden", "true");
        marks.append(mark);
      }
    }
    selectCell(preferredKey, preferredId);
  }

  function setPreset(scopeName, group, source) {
    scope.select.value = scopeName;
    if (scopeName === "hodge") hodge.select.value = group;
    else if (scopeName === "euler") euler.select.value = group;
    redraw(source ? key(source) : undefined, source?.id);
  }

  clearResult = runAction(inspection, () => selectedRecord,
    row => ({ figure: "integral-invariants", record_id: row.id }), run => [
      `Backend: ${run.backend} · record #${run.record_id} · g₃ = ${run.result.cubic_content} · g₂ = ${run.result.chern_content}`,
      `Ordered Chern pairings · (${run.result.c2.join(", ")})`,
      `Hyperplane indices · (${run.result.hyperplane_indices.join(", ")})`,
      run.source,
    ].filter(Boolean));
  recordAction(census, () => selectedCell, cellQuery, openRecords);
  recordAction(inspection, () => selectedRecord, row => ({
    query: { figure: "integral-invariants", record_id: row.id }, title: `Integral lattice · record #${row.id}`,
  }), openRecords, true);

  const shareActions = node("div", "", "research-actions integral-share-actions");
  const share = node("button", "Copy figure view link", "text-button");
  share.type = "button";
  const shareStatus = node("p", "", "research-status integral-share-status");
  shareStatus.setAttribute("role", "status");
  const shareFallback = node("input", "", "integral-share-url");
  shareFallback.type = "url";
  shareFallback.readOnly = true;
  shareFallback.hidden = true;
  shareFallback.setAttribute("aria-label", "Figure view URL to copy");
  share.addEventListener("click", async () => {
    const state = new URLSearchParams({ scope: scope.select.value, cell: key(selectedCell), record: String(selectedRecord.id) });
    if (scope.select.value === "hodge") state.set("group", hodge.select.value);
    else if (scope.select.value === "euler") state.set("group", euler.select.value);
    const url = new URL(location.href);
    url.searchParams.set("lattice", String(state));
    url.hash = "research-integral-invariants";
    shareFallback.hidden = true;
    try {
      await navigator.clipboard.writeText(String(url));
      shareStatus.textContent = "Copied this scope, cell and source record.";
    } catch {
      shareFallback.value = String(url);
      shareFallback.hidden = false;
      shareFallback.focus();
      shareFallback.select();
      shareStatus.textContent = "Select and copy the figure view URL below.";
    }
  });
  shareActions.append(share);
  census.details.append(shareActions, shareStatus, shareFallback);

  scope.select.addEventListener("change", () => redraw());
  hodge.select.addEventListener("change", () => redraw());
  euler.select.addEventListener("change", () => redraw());
  cell.select.addEventListener("change", () => selectCell(cell.select.value));
  record.select.addEventListener("change", updateRecord);
  compare.addEventListener("click", () => setPreset("hodge", witness[0].hodge.join(","), witness[0]));
  modal.addEventListener("click", () => setPreset("hodge", summary.modal_hodge.join(",")));

  hodge.select.value = witness[0].hodge.join(",");
  euler.select.value = String(witness[0].euler);
  function restore() {
    const state = new URLSearchParams(new URLSearchParams(location.search).get("lattice") || "");
    scope.select.value = ["all", "hodge", "euler"].includes(state.get("scope")) ? state.get("scope") : "all";
    if (scope.select.value === "hodge" && hodgeGroups.has(state.get("group"))) hodge.select.value = state.get("group");
    if (scope.select.value === "euler" && eulerGroups.has(state.get("group"))) euler.select.value = state.get("group");
    redraw(state.get("cell") || key(witness[0]), Number(state.get("record") || witness[0].id));
  }
  window.addEventListener("popstate", restore);
  restore();
}
