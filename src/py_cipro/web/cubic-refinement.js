const invariantNames = ["d₁", "d₂", "d₃", "dₚ"];
const invariantKeys = ["d1", "d2", "d3", "dp"];
const signature = row => invariantKeys.map(name => row[name]).join(",");
const signatureLabel = row => `(${invariantKeys.map(name => row[name]).join(", ")})`;

export function mountCubicRefinement(parent, data, integral, openRecords, openWitness, ui) {
  const { node, field, runAction, recordAction, count } = ui;
  const section = node("section", "", "integral-refinement");
  section.id = "research-refinement";
  section.setAttribute("aria-labelledby", "research-refinement-title");
  const heading = node("header", "", "refinement-heading");
  const title = node("h4", "Cubic refinement audit");
  title.id = "research-refinement-title";
  const subtitle = node("p", "Inspect repeated and diagonal cubic evaluations within the selected census cell. The original pair remains (d₁, dₚ) = (g₃, g₂).", "research-panel-description");
  const download = node("a", "Download refinement audit JSON", "text-button");
  download.href = "/research/cubic-refinement.json";
  download.download = "cubic-refinement.json";
  const caption = node("div");
  caption.append(title, subtitle);
  heading.append(caption, download);
  section.append(heading);
  parent.append(section);
  if (!data) {
    const error = node("p", "The supplemental refinement audit is unavailable. The two-dimensional census remains available above.", "research-status error");
    error.setAttribute("role", "alert");
    section.append(error);
    return { updateCell() {}, restore() {}, shareState: () => ({}) };
  }
  if (data.dataset_sha256 !== integral.dataset_sha256 || data.archive_sha256 !== integral.archive_sha256) {
    throw new Error("The refinement audit and integral census refer to different archive data.");
  }
  const auditRows = new Map(data.rows.map(row => [row.id, row]));
  const integralRows = new Map(integral.rows.map(row => [row.id, row]));
  if (auditRows.size !== data.rows.length || data.rows.length !== integral.rows.length || data.rows.some(row => {
    const prior = integralRows.get(row.id);
    return !prior || row.d1 !== prior.cubic_content || row.dp !== prior.chern_content;
  })) throw new Error("The refinement audit does not match the IDs and original content pairs of the integral census.");

  const metrics = node("dl", "", "refinement-metrics");
  for (const [label, value] of [
    ["Original signatures", data.summary.joint_pairs],
    ["Four-invariant signatures", data.summary.joint_quadruples],
    ["Original cells refined", data.summary.pair_cells_refined],
    ["Hodge groups gaining signatures", data.summary.hodge_groups_refined],
  ]) {
    const metric = node("div");
    metric.append(node("dt", label), node("dd", count.format(value)));
    metrics.append(metric);
  }
  const explanation = node("details", "", "refinement-definitions");
  const definitions = node("dl");
  for (const [label, text] of [
    ["d₁ · mixed", "Greatest common divisor of μ(x, y, z). This is the original cubic content g₃."],
    ["d₂ · repeated", "Greatest common divisor of μ(x, x, y)."],
    ["d₃ · diagonal", "Greatest common divisor of μ(x, x, x)."],
    ["dₚ · Chern", "Greatest common divisor of the second Chern evaluations. This is the original Chern content g₂."],
  ]) {
    const pair = node("div");
    pair.append(node("dt", label), node("dd", text));
    definitions.append(pair);
  }
  const reference = node("a", `He, Yao and Yau · equation ${data.reference.equation}`);
  reference.href = `https://doi.org/${data.reference.doi}`;
  reference.target = "_blank";
  reference.rel = "noopener";
  explanation.append(node("summary", "What do the four invariants measure?"),
    node("p", "All evaluations range over the integral lattice supplied by the ambient divisor classes. Equality of these invariants leaves equivalence of the full forms open."),
    definitions, reference);
  section.append(metrics, explanation);

  const layout = node("div", "", "refinement-layout");
  const cohort = node("div", "", "refinement-cohort");
  const inspection = node("div", "", "refinement-inspection");
  layout.append(cohort, inspection);
  section.append(layout);
  cohort.append(node("h5", "Subgroups of the selected cell"));
  const scopeReport = node("p", "", "research-selection refinement-scope");
  scopeReport.id = "research-refinement-scope";
  scopeReport.setAttribute("role", "status");
  const list = node("div", "", "refinement-subgroups");
  list.setAttribute("role", "group");
  list.setAttribute("aria-label", "Four-invariant subgroups of the selected census cell");
  const selected = field("research-refinement-signature", "Four-invariant subgroup (d₁, d₂, d₃, dₚ)", [], () => "", () => "");
  const selectedReport = node("p", "", "research-selection");
  selectedReport.id = "research-refinement-selection";
  selectedReport.setAttribute("role", "status");
  const idsDisclosure = node("details", "", "refinement-ids");
  const idsSummary = node("summary");
  const ids = node("pre");
  ids.tabIndex = 0;
  ids.setAttribute("aria-label", "Exact archive IDs in the selected refined subgroup");
  idsDisclosure.append(idsSummary, ids);
  const cohortActions = node("div", "", "research-panel-controls");
  cohortActions.id = "research-refinement-cohort-actions";
  cohort.append(scopeReport, list, selected.wrapper, selectedReport, idsDisclosure, cohortActions);

  inspection.append(node("h5", "Exact refinement record"));
  const record = field("research-refinement-record", "Record for refinement inspection and Python rerun", [], () => "", () => "");
  const detail = node("div", "", "refinement-record");
  detail.id = "research-refinement-detail";
  detail.setAttribute("aria-live", "polite");
  const rawDisclosure = node("details", "", "method-json refinement-json");
  const raw = node("pre");
  raw.tabIndex = 0;
  rawDisclosure.append(node("summary", "Exact refinement record JSON"), raw);
  const recordActions = node("div", "", "research-panel-controls");
  recordActions.id = "research-refinement-record-actions";
  inspection.append(record.wrapper, detail, rawDisclosure, recordActions);

  let groups = [];
  let selectedGroup;
  let selectedRecord;
  let scope = {};
  let clearCohort;
  let clearRecord;
  let clearRun;
  const groupButtons = new Map();
  const witnessButtons = new Map();
  const label = group => `${signatureLabel(group)} · ${count.format(group.ids.length)} ${group.ids.length === 1 ? "record" : "records"}`;

  function updateRecord() {
    selectedRecord = auditRows.get(Number(record.select.value));
    const prior = integralRows.get(selectedRecord.id);
    const recordTitle = node("p", `Archive #${selectedRecord.id}`, "refinement-record-id");
    const numbers = node("dl", "", "refinement-signature-values");
    for (const [index, name] of invariantKeys.entries()) {
      const value = node("div");
      value.append(node("dt", invariantNames[index]), node("dd", String(selectedRecord[name])));
      numbers.append(value);
    }
    detail.replaceChildren(recordTitle, numbers, node("p", `Hodge pair (${prior.hodge.join(", ")}) · χ = ${prior.euler} · ${prior.ambient_factors} ambient ${prior.ambient_factors === 1 ? "factor" : "factors"}`, "research-panel-description"));
    raw.textContent = JSON.stringify(selectedRecord, null, 2);
    for (const [id, button] of witnessButtons) button.setAttribute("aria-pressed", String(id === selectedRecord.id));
    clearRecord?.();
    clearRun?.();
    ui.onChange?.();
  }

  function chooseGroup(value, preferredId = selectedRecord?.id) {
    selectedGroup = groups.find(group => signature(group) === value) || groups[0];
    selected.select.value = signature(selectedGroup);
    selectedReport.textContent = `${label(selectedGroup)} in this census cell and scope.`;
    idsSummary.textContent = `Exact IDs in selected subgroup (${count.format(selectedGroup.ids.length)})`;
    ids.textContent = selectedGroup.ids.join(", ");
    for (const [choice, button] of groupButtons) button.setAttribute("aria-pressed", String(choice === signature(selectedGroup)));
    record.select.replaceChildren(...selectedGroup.ids.map(id => {
      const prior = integralRows.get(id);
      return new Option(`#${id} · (${prior.hodge.join(", ")}) · χ = ${prior.euler}`, String(id));
    }));
    if (selectedGroup.ids.includes(preferredId)) record.select.value = String(preferredId);
    clearCohort?.();
    updateRecord();
  }

  function updateCell(cell, context, preferredId) {
    scope = { ...context };
    const indexed = new Map();
    for (const id of cell.record_ids) {
      const row = auditRows.get(id);
      const value = signature(row);
      if (!indexed.has(value)) indexed.set(value, { ...row, ids: [] });
      indexed.get(value).ids.push(id);
    }
    groups = [...indexed.values()].sort((a, b) => {
      for (const name of invariantKeys) if (a[name] !== b[name]) return a[name] - b[name];
      return 0;
    });
    const scopeName = context.h11 !== undefined ? `Hodge pair (${context.h11}, ${context.h21})`
      : context.euler !== undefined ? `Euler χ = ${context.euler}` : "All non-product records";
    scopeReport.textContent = `${scopeName} · original cell (g₃, g₂) = (${cell.cubic_content}, ${cell.chern_content}) · ${count.format(cell.count)} records · ${groups.length} refined ${groups.length === 1 ? "subgroup" : "subgroups"}.`;
    selected.select.replaceChildren(...groups.map(group => new Option(label(group), signature(group))));
    list.replaceChildren();
    groupButtons.clear();
    for (const group of groups) {
      const button = node("button", "", "refinement-subgroup");
      button.type = "button";
      button.dataset.signature = signature(group);
      button.setAttribute("aria-label", `Refined signature ${label(group)}`);
      const names = node("span", "", "refinement-subgroup-values");
      for (const [index, name] of invariantKeys.entries()) {
        const item = node("span");
        item.append(node("span", invariantNames[index], "refinement-invariant-name"), node("strong", String(group[name])));
        names.append(item);
      }
      const frequency = node("span", `${count.format(group.ids.length)} ${group.ids.length === 1 ? "record" : "records"}`, "refinement-frequency");
      const track = node("span", "", "refinement-track");
      track.setAttribute("aria-hidden", "true");
      const fill = node("span");
      fill.style.width = `${100 * group.ids.length / cell.count}%`;
      track.append(fill);
      button.append(names, frequency, track);
      button.addEventListener("click", () => chooseGroup(signature(group)));
      groupButtons.set(signature(group), button);
      list.append(button);
    }
    const preferred = auditRows.get(preferredId);
    chooseGroup(preferred && cell.record_ids.includes(preferredId) ? signature(preferred) : signature(selectedGroup || groups[0]), preferredId);
  }

  clearCohort = recordAction({ details: cohortActions }, () => selectedGroup, group => ({
    query: { figure: "cubic-refinement", ...Object.fromEntries(invariantKeys.map(name => [name, group[name]])), ...scope },
    title: `Cubic refinement · ${label(group)}`,
  }), openRecords, false, "Open refined source records");
  clearRun = runAction({ details: recordActions }, () => selectedRecord,
    row => ({ figure: "cubic-refinement", record_id: row.id }), run => [
      `Backend: ${run.backend} · record #${run.record_id} · (d₁, d₂, d₃, dₚ) = ${signatureLabel(run.result)}`,
      run.source,
    ].filter(Boolean), "Rerun refinement in Python");
  clearRecord = recordAction({ details: recordActions }, () => selectedRecord, row => ({
    query: { figure: "cubic-refinement", record_id: row.id }, title: `Cubic refinement · record #${row.id}`,
  }), openRecords, true, "Open refinement source record");

  const witnessSection = node("section", "", "refinement-witness-section");
  witnessSection.setAttribute("aria-labelledby", "research-refinement-witness-title");
  const witnessHeading = node("h5", "Witness pairs for the two refinements");
  witnessHeading.id = "research-refinement-witness-title";
  witnessSection.append(witnessHeading, node("p", "These comparisons distinguish supplied ambient lattices. The rank-one comparison above supplies the separate full-lattice obstruction.", "research-panel-description"));
  const witnessLayout = node("div", "", "refinement-witness-layout");
  for (const [name, sources, changed, presetLabel] of [
    ["Repeated evaluations · d₂", data.witness, "d2", "Compare repeated-evaluation witnesses"],
    ["Diagonal evaluations · d₃", data.diagonal_witness, "d3", "Compare diagonal-evaluation witnesses"],
  ]) {
    const group = node("div", "", "refinement-witness-pair");
    group.append(node("h6", name), node("p", `Hodge pair (${sources[0].hodge.join(", ")}) · χ = ${sources[0].euler}`, "research-panel-description"));
    const cards = node("div", "", "refinement-witness-cards");
    for (const source of sources) {
      const button = node("button", "", "refinement-witness");
      button.type = "button";
      button.dataset.record = String(source.id);
      button.setAttribute("aria-label", `Inspect refinement witness #${source.id}`);
      button.append(node("span", `Archive #${source.id}`, "integral-witness-id"));
      const values = node("dl");
      for (const [index, property] of invariantKeys.entries()) {
        const value = node("div");
        if (property === changed) value.classList.add("refinement-changed-invariant");
        value.append(node("dt", invariantNames[index]), node("dd", String(source[property])));
        values.append(value);
      }
      button.append(values, node("span", "Inspect and rerun →", "integral-witness-action"));
      button.addEventListener("click", () => { openWitness(source); chooseGroup(signature(source), source.id); });
      witnessButtons.set(source.id, button);
      cards.append(button);
    }
    const preset = node("button", presetLabel, "text-button");
    preset.type = "button";
    preset.addEventListener("click", () => { openWitness(sources[0]); chooseGroup(signature(sources[0]), sources[0].id); });
    group.append(cards, preset);
    const witnessDetails = node("details", "", "method-json refinement-witness-evidence");
    const witnessRaw = node("pre");
    witnessRaw.tabIndex = 0;
    witnessRaw.textContent = JSON.stringify(sources, null, 2);
    witnessDetails.append(node("summary", "Exact witness configurations and cubic evaluations"), witnessRaw);
    group.append(witnessDetails);
    witnessLayout.append(group);
  }
  witnessSection.append(witnessLayout);
  section.append(witnessSection);
  section.append(node("p", `${count.format(data.checks.value_based_d2_and_d3)} records pass the independent value-based d₂/d₃ check, the divisibility chain d₁ ∣ d₂ ∣ d₃, and the diagonal Riemann–Roch condition gcd(2d₃, 12) ∣ dₚ.`, "refinement-qualification"));

  selected.select.addEventListener("change", () => chooseGroup(selected.select.value));
  record.select.addEventListener("change", updateRecord);
  return {
    updateCell,
    restore(state) {
      if (state.has("refinement")) chooseGroup(state.get("refinement"), Number(state.get("refinement_record")));
    },
    shareState: () => ({ refinement: signature(selectedGroup), refinement_record: String(selectedRecord.id) }),
  };
}
