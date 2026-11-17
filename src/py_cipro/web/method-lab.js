const kinds = { function: 'Function', property: 'Property', modification: 'Modification' }
const previewLimit = 24
const owns = (value, key) => Object.prototype.hasOwnProperty.call(value ?? {}, key)
const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value)
const isExpression = (value) => isObject(value) && owns(value, '$expression')
const isScalar = (value) => value === null || typeof value !== 'object' || isExpression(value) ||
  owns(value, '$rational') || owns(value, '$integer') || owns(value, '$complex')

function exactText(value) {
  if (isExpression(value)) return value.$expression
  if (owns(value, '$rational')) return value.$rational.map(exactText).join('/')
  if (owns(value, '$integer')) return String(value.$integer)
  if (owns(value, '$complex')) {
    const [real, imaginary] = value.$complex.map(exactText)
    return imaginary.startsWith('-') ? `${real} − ${imaginary.slice(1)}i` : `${real} + ${imaginary}i`
  }
  return String(value)
}

function numericValue(value) {
  let result
  if (typeof value === 'number') result = value
  else if (owns(value, '$rational')) result = Number(exactText(value.$rational[0])) / Number(exactText(value.$rational[1]))
  else if (owns(value, '$integer')) result = Number(value.$integer)
  return Number.isFinite(result) ? result : undefined
}

function matrixPreview(matrix, element) {
  const rows = matrix.slice(0, previewLimit).map((row) => row.slice(0, previewLimit))
  const largest = Math.max(1, ...rows.flat().map((value) => Math.abs(numericValue(value) ?? 0)))
  const table = element('table', undefined, 'result-matrix')
  table.append(element('caption', `${matrix.length} × ${matrix[0].length} matrix`, 'matrix-caption'))
  const head = element('thead')
  const columns = element('tr')
  for (const label of ['Row', ...rows[0].map((_, index) => index + 1)]) {
    const column = element('th', label)
    column.scope = 'col'
    columns.append(column)
  }
  head.append(columns)
  const body = element('tbody')
  for (const [index, row] of rows.entries()) {
    const line = element('tr')
    const number = element('th', index + 1)
    number.scope = 'row'
    line.append(number)
    for (const value of row) {
      const cell = element('td', exactText(value))
      const numeric = numericValue(value)
      if (numeric !== undefined) {
        cell.style.setProperty('--cell-strength', `${Math.round(Math.abs(numeric) / largest * 33)}%`)
        cell.classList.toggle('negative', numeric < 0)
      }
      line.append(cell)
    }
    body.append(line)
  }
  table.append(head, body)
  const scroll = element('div', undefined, 'table-scroll')
  scroll.setAttribute('aria-label', 'Result matrix')
  scroll.tabIndex = 0
  scroll.append(table)
  if (matrix.length > previewLimit || matrix[0].length > previewLimit) {
    scroll.append(element('p', 'Complete matrix in Exact result JSON.', 'result-cap'))
  }
  return scroll
}

function vectorPreview(vector, element) {
  const sample = vector.slice(0, previewLimit)
  const numeric = sample.map(numericValue)
  const largest = Math.max(1, ...numeric.map(Math.abs))
  const list = element('ol', undefined, 'result-vector')
  list.setAttribute('aria-label', 'Numeric result vector')
  for (const [index, value] of sample.entries()) {
    const bar = element('meter', undefined, numeric[index] < 0 ? 'negative' : 'positive')
    bar.max = largest
    bar.value = Math.abs(numeric[index])
    bar.setAttribute('aria-hidden', 'true')
    const item = element('li')
    item.append(element('span', index + 1), bar, element('code', exactText(value)))
    list.append(item)
  }
  return previewCaption(list, sample.length, vector.length, element)
}

function previewCaption(node, shown, total, element) {
  if (shown === total) return node
  const wrapper = element('div')
  wrapper.append(node, element('p', `Showing ${shown} of ${total}. Open Exact result JSON for all values.`, 'result-cap'))
  return wrapper
}

function shapePreview(value, element, depth = 0, budget = { remaining: 160 }) {
  budget.remaining -= 1
  if (depth >= 4 || budget.remaining < 0) return element('p', 'Open Exact result JSON to inspect the full value.', 'result-cap')
  if (isExpression(value)) {
    const code = element('code', exactText(value), 'result-expression')
    code.title = value.language ?? 'Symbolic expression'
    return code
  }
  if (isScalar(value)) return element('span', exactText(value), 'result-scalar')
  if (Array.isArray(value)) {
    if (!value.length) return element('span', 'Empty list', 'result-scalar')
    const columns = value[0]?.length
    if (columns && value.every((row) => Array.isArray(row) && row.length === columns && row.every(isScalar))) {
      budget.remaining -= Math.min(value.length, previewLimit) * Math.min(columns, previewLimit)
      return matrixPreview(value, element)
    }
    if (value.length > 1 && value.every((item) => numericValue(item) !== undefined)) {
      budget.remaining -= Math.min(value.length, previewLimit)
      return vectorPreview(value, element)
    }
    const list = element('ol', undefined, 'result-sequence')
    for (const item of value.slice(0, previewLimit)) {
      const row = element('li')
      row.append(shapePreview(item, element, depth + 1, budget))
      list.append(row)
      if (budget.remaining < 0) break
    }
    return previewCaption(list, list.children.length, value.length, element)
  }
  const entries = owns(value, '$association') ? value.$association : Object.entries(value)
  if (!entries.length) return element('span', 'Empty association', 'result-scalar')
  const result = element('dl', undefined, 'result-association')
  for (const [key, item] of entries.slice(0, previewLimit)) {
    const row = element('div')
    const data = element('dd')
    data.append(shapePreview(item, element, depth + 1, budget))
    const term = element('dt')
    term.append(isScalar(key) ? exactText(key) : shapePreview(key, element, depth + 1, budget))
    row.append(term, data)
    result.append(row)
    if (budget.remaining < 0) break
  }
  return previewCaption(result, result.children.length, entries.length, element)
}

function readInputs(argsInput, optionsInput) {
  const args = argsInput.value.trim()
  const options = optionsInput.value.trim()
  let parsedArgs, parsedOptions
  try {
    parsedArgs = JSON.parse(args)
  } catch {
    throw new Error('Arguments must be valid JSON.')
  }
  try {
    parsedOptions = JSON.parse(options)
  } catch {
    throw new Error('Options must be valid JSON.')
  }
  if (!Array.isArray(parsedArgs)) throw new Error('Arguments must be a JSON list.')
  if (!isObject(parsedOptions)) throw new Error('Options must be a JSON object.')
  return { args, options }
}

function downloadResult(result, element) {
  const json = JSON.stringify(result, null, 2)
  const url = URL.createObjectURL(new Blob([`${json}\n`], { type: 'application/json' }))
  const link = element('a')
  link.href = url
  link.download = `cipro-${result.kind}-${result.name}.json`
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function mountMethodLab({ $, element, loadJSON, getBackend, getRecord, backendName }) {
  const list = $('method-list')
  const argsInput = $('method-args')
  const optionsInput = $('method-options')
  const status = $('method-status')
  const run = $('method-run')
  const exampleButton = $('method-example')
  const recordButton = $('method-record')
  const panel = $('method-result')
  let methods = []
  let selected = null
  let result = null
  let busy = false

  function showStatus(message, error = false) {
    status.textContent = message
    status.classList.toggle('error', error)
  }

  function updateControls() {
    const backend = getBackend()
    const runnable = selected?.runnable ?? selected?.native ?? false
    const available = backend && runnable && (selected.native || backend !== 'python')
    run.disabled = !available || busy
    argsInput.disabled = !runnable || busy
    optionsInput.disabled = argsInput.disabled
    exampleButton.disabled = !selected?.example || busy
    recordButton.hidden = selected?.kind !== 'property' || !selected?.native
    recordButton.disabled = !getRecord() || busy
    if (busy || !selected || result) return
    if (!runnable) showStatus('This operation is available through the Wolfram Language API.')
    else if (!available && backend === 'python') showStatus('Select Wolfram or Auto to run this method.')
    else if (backend === 'wolfram') showStatus('Wolfram uses an activated local kernel.')
    else if (backend === 'auto') showStatus('Auto tries Python first and uses a local Wolfram kernel for unsupported inputs.')
    else if (backend === 'python') showStatus('Python runs locally with the native CIPro implementation.')
    else showStatus('The dashboard is checking compute backends.')
  }

  function loadExample() {
    argsInput.value = JSON.stringify(selected?.example?.args ?? [], null, 2)
    optionsInput.value = JSON.stringify(selected?.example?.options ?? {}, null, 2)
  }

  function choose(method) {
    selected = method
    result = null
    panel.hidden = true
    list.querySelectorAll('button').forEach((button) => {
      button.setAttribute('aria-pressed', String(button.dataset.method === `${method.kind}:${method.name}`))
    })
    $('method-title').textContent = method.name
    $('method-description').textContent = kinds[method.kind] ?? method.kind
    $('method-badge').textContent = method.native ? 'Native Python' : 'Wolfram only'
    $('method-badge').hidden = false
    $('method-input-help').textContent = method.kind === 'function'
      ? 'List the positional arguments for this function.'
      : method.kind === 'property'
        ? 'Put the configuration association in a one-element arguments list.'
        : 'Put one configuration or a list of configurations in the arguments list.'
    loadExample()
    showStatus('')
    updateControls()
  }

  function renderList() {
    const query = $('method-query').value.trim().toLowerCase()
    const kind = $('method-kind').value
    const availability = $('method-availability').value
    const visible = methods.filter((method) => (
      method.name.toLowerCase().includes(query) && (kind === 'all' || kind === method.kind) &&
      (availability === 'all' || method.native === (availability === 'native'))
    ))
    const count = methods.filter((method) => method.native).length
    $('methods-coverage').textContent = `${visible.length} of ${methods.length} shown · ${count} native Python`
    list.replaceChildren()
    if (!visible.length) list.append(element('li', 'No matching methods.', 'empty-state'))
    for (const method of visible) {
      const item = element('li')
      const button = element('button', undefined, 'method-option')
      button.type = 'button'
      button.dataset.method = `${method.kind}:${method.name}`
      button.setAttribute('aria-pressed', String(selected === method))
      const label = element('span')
      label.append(element('strong', method.name), element('small', kinds[method.kind] ?? method.kind))
      button.append(label, element('span', method.native ? 'Python' : 'Wolfram', method.native ? 'method-tag' : 'method-tag wolfram-only'))
      button.addEventListener('click', () => choose(method))
      item.append(button)
      list.append(item)
    }
  }

  $('method-query').addEventListener('input', renderList)
  $('method-kind').addEventListener('change', renderList)
  $('method-availability').addEventListener('change', renderList)
  exampleButton.addEventListener('click', () => {
    if (!selected?.example) return
    loadExample()
    showStatus('Example loaded.')
  })
  recordButton.addEventListener('click', () => {
    const record = getRecord()
    if (!record || selected?.kind !== 'property') return
    argsInput.value = JSON.stringify([{ Conf: record.configuration, DimPs: record.ambient_dimensions }], null, 2)
    showStatus(`Loaded configuration #${record.id}.`)
  })
  $('method-export').addEventListener('click', () => {
    if (result) downloadResult(result, element)
  })
  $('method-form').addEventListener('submit', async (event) => {
    event.preventDefault()
    if (run.disabled || !selected) return
    let inputs
    try {
      inputs = readInputs(argsInput, optionsInput)
    } catch (error) {
      showStatus(error.message, true)
      return
    }
    const { kind, name } = selected
    const method = selected
    const backend = getBackend()
    const metadata = JSON.stringify({ backend, kind, name }).slice(0, -1)
    const body = `${metadata},"args":${inputs.args},"options":${inputs.options}}`
    busy = true
    result = null
    panel.hidden = true
    showStatus(`Running ${name} with ${backendName(backend)}…`)
    updateControls()
    try {
      const response = await loadJSON('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
      })
      if (selected !== method) return
      result = { kind, name, requested_backend: backend, ...response }
      $('method-result-source').textContent = `${name} · ${backendName(response.backend)} · ${response.source}`
      $('method-visual').replaceChildren(shapePreview(response.result, element))
      const diagnostics = [
        ...(response.messages ?? []).map((line) => `Message: ${line}`),
        ...(response.output ?? []).map((line) => `Output: ${line}`),
      ]
      $('method-log').textContent = diagnostics.join('\n')
      $('method-diagnostics').hidden = !diagnostics.length
      $('method-raw').textContent = JSON.stringify(result, null, 2)
      panel.hidden = false
      showStatus('')
    } catch (error) {
      if (selected === method) showStatus(error.message, true)
    } finally {
      busy = false
      const error = status.classList.contains('error') ? status.textContent : null
      updateControls()
      if (error && selected === method) showStatus(error, true)
    }
  })

  loadJSON('/api/methods').then((payload) => {
    if (!Array.isArray(payload.methods)) throw new Error('The method list was unavailable.')
    methods = payload.methods
    renderList()
    const initial = methods.find((method) => method.native && method.kind === 'property' && method.name === 'Euler') ??
      methods.find((method) => method.native)
    if (initial) choose(initial)
  }).catch((error) => {
    $('methods-coverage').textContent = 'Method list unavailable'
    list.replaceChildren(element('li', error.message, 'notice error'))
  })

  return updateControls
}
