const auditPath = "/research/index-divisibility.json";
const dimension = value => String(value).replace(/\d/g, digit => "⁰¹²³⁴⁵⁶⁷⁸⁹"[digit]);
const tuple = values => `(${values.join(", ")})`;

function measure(node, label, value, className) {
  const pair = node("div", "", className);
  pair.append(node("dt", label), node("dd", String(value)));
  return pair;
}

function configuration(node, record) {
  const matrix = node("table", "", "index-divisibility-matrix");
  const rows = node("tbody");
  for (const [index, degrees] of record.configuration.entries()) {
    const row = node("tr");
    const factorDimension = record.ambient_dimensions[index];
    const factor = node("th", `ℙ${dimension(factorDimension)}`);
    factor.scope = "row";
    factor.setAttribute("aria-label", `Ambient factor ${index + 1}, projective dimension ${factorDimension}`);
    row.append(factor, ...degrees.map(degree => node("td", String(degree), degree === 0 ? "matrix-zero" : "matrix-nonzero")));
    rows.append(row);
  }
  matrix.append(node("caption", "Configuration degrees"), rows);
  return matrix;
}

function recordCard(record, openRecords, ui) {
  const { node, runAction, recordAction } = ui;
  const card = node("article", "", "index-divisibility-record");
  card.dataset.recordId = record.id;
  const heading = node("h5", `CICY3 record ${record.id}`);
  heading.id = `index-divisibility-record-${record.id}`;
  card.setAttribute("aria-labelledby", heading.id);
  const gcd = node("dl", "", "index-divisibility-gcd");
  gcd.append(measure(node, "Ambient index gcd dχ", record.index_divisor));

  const indices = node("div", "", "index-divisibility-hyperplanes");
  const hyperplaneValues = node("dl");
  for (const [i, value] of record.hyperplane_indices.entries()) {
    hyperplaneValues.append(measure(node, `χ(O(H${i + 1}))`, value, value % 2 ? "index-divisibility-odd" : ""));
  }
  indices.append(node("h6", "Archived hyperplane indices"), hyperplaneValues);
  const details = node("div", "", "research-panel-controls");
  runAction({ details }, () => record, row => ({ figure: "index-divisibility", record_id: row.id }), run => [
    `Backend: ${run.backend} · record #${run.record_id}`,
    `Ambient index gcd dχ = ${run.result.index_divisor}`,
    `Hyperplane indices · ${tuple(run.result.hyperplane_indices)}`,
  ]);
  recordAction({ details }, () => record, row => ({
    query: { figure: "index-divisibility", record_id: row.id },
    title: `Index divisibility · record #${row.id}`,
  }), openRecords, true);
  card.append(heading, gcd, configuration(node, record), indices, details);
  return card;
}

export function mountIndexDivisibility(parent, openRecords, ui) {
  const { node, request, count } = ui;
  const section = node("section", "", "index-divisibility");
  section.id = "research-index-divisibility";
  const heading = node("header", "", "refinement-heading");
  const caption = node("div");
  const title = node("h4", "Index-divisibility audit");
  title.id = "research-index-divisibility-title";
  section.setAttribute("aria-labelledby", title.id);
  caption.append(title, node("p", "Compare two records with the same Hodge numbers and cubic and Chern divisibilities. The index gcd measures divisibility across every integral class in the ambient divisor lattice.", "research-panel-description"));
  const download = node("a", "Download index-divisibility audit JSON", "text-button");
  download.href = auditPath;
  download.download = "index-divisibility.json";
  heading.append(caption, download);

  const status = node("p", "", "research-status");
  status.setAttribute("role", "status");
  const retry = node("button", "Retry index-divisibility audit", "text-button");
  retry.type = "button";
  section.append(heading, status, retry);
  parent.append(section);

  async function load() {
    retry.hidden = true;
    status.classList.remove("error");
    status.textContent = "Loading index-divisibility audit…";
    try {
      const { witness, summary } = await request(auditPath);
      const [first] = witness;
      const shared = node("dl", "", "index-divisibility-shared");
      shared.append(
        measure(node, "Shared Hodge numbers", tuple(first.hodge)),
        measure(node, "Euler characteristic χ", first.euler),
        measure(node, "Cubic and Chern gcds (d₁, d₂, d₃, dₚ)", tuple(first.signature)),
      );
      const comparison = node("div", "", "index-divisibility-comparison");
      comparison.append(...witness.map(record => recordCard(record, openRecords, ui)));
      const interpretation = node("p",
        `Adding the index gcd raises the number of distinct signatures from ${count.format(summary.signatures_before)} to ${count.format(summary.signatures_after)} across ${count.format(summary.records)} non-product records. ${count.format(summary.nonunit_records)} have an index gcd greater than one.`,
        "index-divisibility-interpretation");
      section.append(shared, comparison, interpretation);
      status.remove();
      retry.remove();
    } catch (error) {
      status.textContent = `Index-divisibility audit unavailable. ${error.message}`;
      status.classList.add("error");
      retry.hidden = false;
    }
  }

  retry.addEventListener("click", load);
  void load();
}
