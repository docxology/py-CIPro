import { mountMethodLab } from './method-lab.js'

const $ = (id) => document.getElementById(id)
const number = new Intl.NumberFormat('en-US')
const pageSize = 15
const binWidth = 20
const sortKeys = ['id', 'h11', 'h21', 'euler']
const pairKey = ({ h11, h21 }) => `${h11},${h21}`
const isHodgePlaceholder = ({ product, h11, h21 }) => product && h11 === 0 && h21 === 0
const binStart = ({ euler }) => Math.floor(euler / binWidth) * binWidth
const interval = (start) => `${start} to ${start + binWidth - 1}`
const choice = (value) => ['yes', 'no'].includes(value) ? value : 'all'
const integer = (text) => /^-?\d+$/.test(text || '') ? Number(text) : null
const isPair = (value) => /^\d{1,3},\d{1,3}$/.test(value || '')
const backendNames = { python: 'Python', wolfram: 'Wolfram', auto: 'Auto' }
const backendName = (backend) => backendNames[backend] ?? 'CIPro'

const state = {
  records: [], bins: [], domain: { h11: 10, h21: 10 }, source: null,
  view: [], query: '', favourable: 'all', product: 'all', pair: null, bin: null,
  recordId: null, record: null, page: 0, sort: 'id', direction: 1,
  kernelEnabled: false, kernelChecked: false, computing: false, backend: 'python', backends: [],
}
let plotPoints = []
let requestSerial = 0
let updateMethodBackend = () => {}

function element(tag, content, className) {
  const node = document.createElement(tag)
  if (content !== undefined) node.textContent = content
  if (className) node.className = className
  return node
}

async function loadJSON(path, init) {
  const response = await fetch(path, init)
  const body = await response.json()
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`)
  return body
}

function readView() {
  const params = new URLSearchParams(location.search)
  state.query = (params.get('q') || '').slice(0, 48)
  state.favourable = choice(params.get('fav'))
  state.product = choice(params.get('product'))
  state.pair = isPair(params.get('pair')) ? params.get('pair') : null
  const bin = integer(params.get('bin'))
  state.bin = state.bins.includes(bin) ? bin : null
  state.sort = sortKeys.includes(params.get('sort')) ? params.get('sort') : 'id'
  state.direction = params.get('dir') === 'desc' ? -1 : 1
  state.page = 0
  state.recordId = integer(params.get('id'))
  $('search').value = state.query
  $('favourability').value = state.favourable
  $('product').value = state.product
}

function writeView() {
  const url = new URL(location.href)
  url.search = ''
  if (state.query) url.searchParams.set('q', state.query)
  if (state.favourable !== 'all') url.searchParams.set('fav', state.favourable)
  if (state.product !== 'all') url.searchParams.set('product', state.product)
  if (state.pair) url.searchParams.set('pair', state.pair)
  if (state.bin !== null) url.searchParams.set('bin', state.bin)
  if (state.sort !== 'id') url.searchParams.set('sort', state.sort)
  if (state.direction < 0) url.searchParams.set('dir', 'desc')
  if (state.recordId !== null) url.searchParams.set('id', state.recordId)
  history.replaceState(null, '', url)
}

function filterRecords() {
  const query = state.query.trim()
  const id = integer(query.replace(/^#\s*/, ''))
  const parts = query.match(/^(\d{1,3})\s*[,/]\s*(\d{1,3})$/)
  const pair = parts ? `${Number(parts[1])},${Number(parts[2])}` : null
  return state.records.filter((record) => (
    (!query || record.id === id || (!isHodgePlaceholder(record) && pairKey(record) === pair)) &&
    (state.favourable === 'all' || record.favourable === (state.favourable === 'yes')) &&
    (state.product === 'all' || record.product === (state.product === 'yes'))
  ))
}

function hodgeGroups(records) {
  const groups = new Map()
  for (const record of records) {
    if (isHodgePlaceholder(record)) continue
    const key = pairKey(record)
    if (!groups.has(key)) groups.set(key, { key, h11: record.h11, h21: record.h21, count: 0 })
    groups.get(key).count += 1
  }
  return [...groups.values()]
}

function canvasContext(canvas) {
  const { width, height } = canvas.getBoundingClientRect()
  const scale = window.devicePixelRatio || 1
  canvas.width = Math.round(width * scale)
  canvas.height = Math.round(height * scale)
  const ctx = canvas.getContext('2d')
  ctx.setTransform(scale, 0, 0, scale, 0, 0)
  return { ctx, width, height }
}

function axes(ctx, left, top, right, bottom, xMax, yMax, colors) {
  ctx.font = '12px system-ui, sans-serif'
  ctx.fillStyle = colors.axes
  const drawGridLine = (x1, y1, x2, y2) => {
    ctx.strokeStyle = colors.grid
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.stroke()
  }
  ctx.textAlign = 'right'
  ctx.textBaseline = 'middle'
  for (let y = 0; y <= yMax; y += yMax / 5) {
    const screen = bottom - (y / yMax) * (bottom - top)
    drawGridLine(left, screen, right, screen)
    ctx.fillText(y, left - 7, screen)
  }
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  for (let x = 0; x <= xMax; x += xMax / 4) {
    const screen = left + (x / xMax) * (right - left)
    drawGridLine(screen, top, screen, bottom)
    ctx.fillText(x, screen, bottom + 6)
  }
  ctx.fillStyle = colors.axes
  ctx.font = '600 12px system-ui, sans-serif'
  ctx.fillText('h¹,¹', (left + right) / 2, bottom + 23)
  ctx.save()
  ctx.translate(13, (top + bottom) / 2)
  ctx.rotate(-Math.PI / 2)
  ctx.fillText('h²,¹', 0, 0)
  ctx.restore()
}

function drawScatter(groups) {
  const { ctx, width, height } = canvasContext($('scatter'))
  const left = 52, top = 12, right = width - 23, bottom = height - 44
  const xMax = state.domain.h11, yMax = state.domain.h21
  if (right < left) return
  const theme = getComputedStyle(document.documentElement)
  const colors = Object.fromEntries(['grid', 'axes', 'dot', 'selected'].map((name) => (
    [name, theme.getPropertyValue(`--plot-${name}`).trim()]
  )))
  axes(ctx, left, top, right, bottom, xMax, yMax, colors)
  plotPoints = groups.map((group) => ({
    ...group,
    x: left + (group.h11 / xMax) * (right - left),
    y: bottom - (group.h21 / yMax) * (bottom - top),
    radius: Math.min(9, 2 + Math.sqrt(group.count) * .27),
  })).sort((a, b) => b.count - a.count)
  const selected = state.view.find(({ id }) => id === state.recordId)
  const selectedKey = selected && pairKey(selected)
  for (const point of plotPoints) {
    ctx.fillStyle = point.key === state.pair ? colors.selected : colors.dot
    ctx.beginPath()
    ctx.arc(point.x, point.y, point.radius, 0, Math.PI * 2)
    ctx.fill()
  }
  const selectedPoint = plotPoints.find(({ key }) => key === selectedKey)
  if (selectedPoint) {
    ctx.beginPath()
    ctx.strokeStyle = colors.selected
    ctx.lineWidth = 1.5
    ctx.arc(selectedPoint.x, selectedPoint.y, selectedPoint.radius + 3, 0, Math.PI * 2)
    ctx.stroke()
  }
  if (plotPoints.length === 0) {
    ctx.fillStyle = colors.axes
    ctx.font = '14px system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('No Hodge pairs match these filters', (left + right) / 2, (top + bottom) / 2)
  }
  $('pair-count').textContent = `${number.format(plotPoints.length)} ${plotPoints.length === 1 ? 'pair' : 'pairs'}`
}

function drawHero() {
  const { ctx, width, height } = canvasContext($('hero-field'))
  const xMax = state.domain.h11, yMax = state.domain.h21
  ctx.lineWidth = 1
  ctx.strokeStyle = '#80bea529'
  for (let x = -height; x < width; x += 43) {
    ctx.beginPath()
    ctx.moveTo(x, height)
    ctx.lineTo(x + height, 0)
    ctx.stroke()
  }
  for (let y = 40; y < height; y += 43) {
    ctx.beginPath()
    ctx.moveTo(width * .12, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
  for (const group of hodgeGroups(state.records)) {
    const x = width * (.28 + group.h11 / xMax * .65)
    const y = height * (.79 - group.h21 / yMax * .68)
    ctx.fillStyle = '#68d3a976'
    ctx.beginPath()
    ctx.arc(x + (height * .5 - y) * .4, y, Math.min(5, 1 + Math.sqrt(group.count) * .14), 0, Math.PI * 2)
    ctx.fill()
  }
}

function hitPoint(event) {
  const rect = $('scatter').getBoundingClientRect()
  const x = event.clientX - rect.left, y = event.clientY - rect.top
  let nearest = null, minimum = Infinity
  for (const point of plotPoints) {
    const distance = Math.hypot(point.x - x, point.y - y)
    if (distance < minimum && distance <= point.radius + 7) {
      nearest = point
      minimum = distance
    }
  }
  return nearest
}

function renderHistogram(records) {
  const counts = new Map(state.bins.map((start) => [start, 0]))
  for (const record of records) counts.set(binStart(record), counts.get(binStart(record)) + 1)
  const tallest = Math.max(1, ...counts.values())
  const chart = $('histogram')
  const sameButtons = chart.children.length === state.bins.length
  if (!sameButtons) chart.replaceChildren()
  for (const [index, start] of state.bins.entries()) {
    const count = counts.get(start)
    const description = `${interval(start)}: ${number.format(count)} ${count === 1 ? 'configuration' : 'configurations'}`
    let bar = chart.children[index]
    if (!sameButtons) {
      bar = element('button', undefined, 'bar')
      bar.type = 'button'
      bar.append(element('span', undefined, 'bar-fill'))
      bar.addEventListener('click', () => changeFilter('bin', state.bin === start ? null : start))
      const describe = () => { $('histogram-info').textContent = bar.title }
      bar.addEventListener('focus', describe)
      bar.addEventListener('pointerenter', describe)
      chart.append(bar)
    }
    bar.firstChild.style.setProperty('--bar-height', `${(count / tallest) * 100}%`)
    bar.title = description
    bar.setAttribute('aria-label', description)
    bar.setAttribute('aria-pressed', String(state.bin === start))
    bar.dataset.empty = String(!count)
    bar.disabled = count === 0 && state.bin !== start
  }
  $('first-bin').textContent = state.bins[0]
  $('last-bin').textContent = state.bins.at(-1) + binWidth - 1
  $('histogram-info').textContent = state.bin === null
    ? 'Focus a bar to see its interval and count.'
    : `${interval(state.bin)} is selected.`
}

function renderChips() {
  const chips = $('chips')
  const values = [
    ['pair', state.pair && `Hodge (${state.pair.replace(',', ', ')})`],
    ['bin', state.bin !== null && `Euler ${interval(state.bin)}`],
  ]
  chips.replaceChildren()
  for (const [key, label] of values) {
    if (!label) continue
    const chip = element('button', `${label} ×`, 'chip')
    chip.type = 'button'
    chip.setAttribute('aria-label', `Remove ${label} filter`)
    chip.addEventListener('click', () => changeFilter(key, null))
    chips.append(chip)
  }
  $('reset').disabled = !(state.query || state.favourable !== 'all' || state.product !== 'all' || state.pair || state.bin !== null)
}

function renderTable() {
  const start = state.page * pageSize
  const shown = state.view.slice(start, start + pageSize)
  const body = $('table-body')
  body.replaceChildren()
  for (const record of shown) {
    const row = element('tr')
    const selected = record.id === state.recordId
    row.dataset.selected = String(selected)
    const id = element('button', `#${record.id}`, 'record-link')
    id.type = 'button'
    id.dataset.record = record.id
    if (selected) id.setAttribute('aria-current', 'true')
    const choose = () => { selectRecord(record.id); renderTable(); drawCurrentScatter() }
    row.addEventListener('click', choose)
    id.addEventListener('click', (event) => {
      event.stopPropagation()
      choose()
      body.querySelector(`[data-record="${record.id}"]`).focus({ preventScroll: true })
    })
    const first = element('td')
    first.append(id)
    const hodge = [record.h11, record.h21].map((value) => {
      const cell = element('td', isHodgePlaceholder(record) ? '—' : value)
      if (isHodgePlaceholder(record)) cell.setAttribute('aria-label', 'Archived Hodge placeholder')
      return cell
    })
    row.append(first, ...hodge, element('td', record.euler),
      element('td', record.favourable ? 'Yes' : 'No'), element('td', record.product ? 'Yes' : 'No'))
    body.append(row)
  }
  if (!shown.length) {
    const empty = element('td', 'No configurations match these filters.', 'empty-state')
    empty.colSpan = 6
    const row = element('tr')
    row.append(empty)
    body.append(row)
  }
  $('page-label').textContent = shown.length
    ? `${number.format(start + 1)}–${number.format(start + shown.length)} of ${number.format(state.view.length)}`
    : '0 configurations'
  $('previous').disabled = state.page === 0
  $('next').disabled = start + shown.length >= state.view.length
  for (const header of document.querySelectorAll('[data-column]')) {
    const order = header.dataset.column === state.sort ? (state.direction > 0 ? 'ascending' : 'descending') : 'none'
    header.setAttribute('aria-sort', order)
    header.querySelector('span').textContent = { ascending: '↑', descending: '↓', none: '↕' }[order]
  }
}

function renderRecord(record) {
  $('record-title').textContent = `Configuration #${record.id}`
  $('record-source').textContent = `${state.source.dataset} · archived record`
  const metrics = element('dl', undefined, 'record-metrics')
  const labels = ['h¹,¹', 'h²,¹', 'Euler']
  const hodge = isHodgePlaceholder(record) ? ['—', '—'] : [record.h11, record.h21]
  for (const [index, value] of [...hodge, record.euler].entries()) {
    const item = element('div')
    item.append(element('dt', labels[index]), element('dd', value))
    metrics.append(item)
  }
  const tags = element('div', undefined, 'record-tags')
  tags.append(element('span', record.favourable ? 'Favourable' : 'Non-favourable', 'record-tag'),
    element('span', record.product ? 'Product' : 'Non-product', 'record-tag'))
  const matrix = element('table', undefined, 'matrix')
  matrix.append(element('caption', 'Configuration matrix', 'matrix-caption'))
  const head = element('thead'), labelsRow = element('tr')
  const ambient = element('th', 'Ambient factor')
  ambient.scope = 'col'
  labelsRow.append(ambient)
  for (let index = 0; index < record.configuration[0].length; index += 1) {
    const label = element('th', `Eq. ${index + 1}`)
    label.scope = 'col'
    labelsRow.append(label)
  }
  head.append(labelsRow)
  const body = element('tbody')
  for (const [index, row] of record.configuration.entries()) {
    const tr = element('tr'), projective = element('th')
    projective.scope = 'row'
    projective.append('ℙ', element('sup', record.ambient_dimensions[index]))
    tr.append(projective, ...row.map((value) => element('td', value)))
    body.append(tr)
  }
  matrix.append(head, body)
  const scroll = element('div', undefined, 'table-scroll')
  scroll.tabIndex = 0
  scroll.setAttribute('aria-label', 'Configuration matrix')
  scroll.append(matrix)
  $('record-body').replaceChildren(metrics, tags, scroll,
    element('p', 'Each column gives the multidegree of one defining equation.', 'config-note'))
  if (isHodgePlaceholder(record)) {
    $('record-body').append(element('p', 'The archived Hodge pair (0, 0) is a product-record placeholder.', 'config-note'))
  }
  $('export').disabled = false
}

function renderKernelState() {
  $('kernel-inputs').disabled = !state.kernelEnabled || !state.record || state.computing
  updateMethodBackend()
  $('kernel-dot').classList.toggle('ready', state.kernelEnabled)
  $('kernel-status').textContent = !state.kernelChecked ? 'Checking backends' : state.kernelEnabled ? `${backendName(state.backend)} selected` : 'Archive mode'
  if (state.computing) return
  const status = $('kernel-help')
  status.classList.remove('error')
  if (!state.kernelChecked) status.textContent = 'Checking compute backends.'
  else if (!state.kernelEnabled) status.textContent = 'Calculation is unavailable. The catalogue remains available.'
  else if (!state.record) status.textContent = 'Choose a record to calculate its properties.'
  else if (state.backend === 'wolfram') status.textContent = 'Wolfram uses an activated local kernel.'
  else if (state.backend === 'auto') status.textContent = 'Auto tries Python first and uses a local Wolfram kernel for unsupported inputs.'
  else status.textContent = 'Python calculates these properties locally.'
}

function renderPropertyComparison(output, record, response) {
  const configuration = record.configuration
  const ambient = record.ambient_dimensions
  const reference = {
    CIDim: [ambient.reduce((total, value) => total + value, 0) - configuration[0].length, 'Configuration dimensions'],
    CY: [configuration.every((row, index) => row.reduce((total, value) => total + value, 0) === ambient[index] + 1), 'Configuration row sums'],
    Euler: [record.euler, 'Archived Euler'],
  }
  const table = element('table', undefined, 'compute-table')
  const head = element('thead')
  const heading = element('tr')
  for (const label of ['Property', 'Reference', backendName(response.backend)]) {
    const cell = element('th', label)
    cell.scope = 'col'
    heading.append(cell)
  }
  head.append(heading)
  const body = element('tbody')
  for (const [key, value] of Object.entries(response.properties)) {
    const row = element('tr')
    const label = element('th', key)
    label.scope = 'row'
    const [expected, note] = reference[key] ?? [null, 'Reference unavailable']
    const baseline = element('td', expected === null ? '—' : String(expected))
    baseline.append(element('small', note))
    const calculated = element('td', String(value), 'compute-comparison')
    if (expected !== null) {
      calculated.classList.toggle('differs', value !== expected)
      calculated.append(element('small', value === expected ? 'Matches reference' : 'Differs from reference'))
    }
    row.append(label, baseline, calculated)
    body.append(row)
  }
  table.append(head, body)
  output.replaceChildren(element('p', `Source: ${response.source}`, 'compute-source'), table)
  output.hidden = false
}

async function selectRecord(id, { updateURL = true, reload = false } = {}) {
  if (state.record?.id === id && !reload) return
  const serial = ++requestSerial
  state.recordId = id
  state.record = null
  $('export').disabled = true
  $('compute-output').hidden = true
  renderKernelState()
  if (updateURL) writeView()
  if (id === null) {
    $('record-title').textContent = 'Configuration'
    $('record-source').textContent = 'No matching catalogue record'
    $('record-body').replaceChildren(element('p', 'Change filters to find a record.', 'empty-state'))
    return
  }
  $('record-title').textContent = `Configuration #${id}`
  $('record-source').textContent = 'Loading archived record…'
  $('record-body').replaceChildren(element('p', 'Loading degree matrix…', 'empty-state'))
  try {
    const record = await loadJSON(`/api/record?id=${id}`)
    if (serial !== requestSerial) return
    state.record = record
    renderRecord(record)
    renderKernelState()
  } catch (error) {
    if (serial !== requestSerial) return
    $('record-source').textContent = 'Archive request failed'
    $('record-body').replaceChildren(element('p', error.message, 'notice error'))
  }
}

function drawCurrentScatter() {
  const allowed = filterRecords().filter((record) => state.bin === null || binStart(record) === state.bin)
  drawScatter(hodgeGroups(allowed))
}

function renderView({ restorePage = false, reload = false } = {}) {
  const allowed = filterRecords()
  const histogram = allowed.filter((record) => state.pair === null || pairKey(record) === state.pair)
  state.view = histogram.filter((record) => state.bin === null || binStart(record) === state.bin)
  state.view.sort((a, b) => state.direction * (a[state.sort] - b[state.sort]) || a.id - b.id)
  const index = state.view.findIndex(({ id }) => id === state.recordId)
  if (restorePage && index !== -1) state.page = Math.floor(index / pageSize)
  if (index === -1) {
    const id = state.view[0]?.id ?? null
    selectRecord(id, { updateURL: false })
  } else if (reload || !state.record) selectRecord(state.recordId, { updateURL: false, reload })
  state.page = Math.min(state.page, Math.max(0, Math.ceil(state.view.length / pageSize) - 1))
  $('result-count').textContent = `${number.format(state.view.length)} of ${number.format(state.records.length)} configurations`
  renderChips()
  drawCurrentScatter()
  renderHistogram(histogram)
  renderTable()
  writeView()
}

function changeFilter(key, value) {
  state[key] = value
  state.page = 0
  renderView()
}

$('filters').addEventListener('submit', (event) => event.preventDefault())
$('search').addEventListener('input', (event) => changeFilter('query', event.target.value))
$('favourability').addEventListener('change', (event) => changeFilter('favourable', event.target.value))
$('product').addEventListener('change', (event) => changeFilter('product', event.target.value))
$('reset').addEventListener('click', () => {
  $('search').value = state.query = ''
  $('favourability').value = state.favourable = 'all'
  $('product').value = state.product = 'all'
  state.pair = state.bin = null
  state.page = 0
  renderView()
})
for (const button of document.querySelectorAll('[data-sort]')) {
  button.addEventListener('click', () => {
    const sort = button.dataset.sort
    state.direction = sort === state.sort ? -state.direction : 1
    state.sort = sort
    state.page = 0
    renderView()
  })
}
$('previous').addEventListener('click', () => { state.page -= 1; renderTable() })
$('next').addEventListener('click', () => { state.page += 1; renderTable() })
$('scatter').addEventListener('pointermove', (event) => {
  const point = hitPoint(event)
  const tooltip = $('scatter-tooltip')
  tooltip.hidden = !point
  $('scatter').style.cursor = point ? 'pointer' : 'default'
  if (!point) return
  tooltip.textContent = `(${point.h11}, ${point.h21}) · ${number.format(point.count)} ${point.count === 1 ? 'configuration' : 'configurations'}`
  tooltip.style.left = `${Math.min(point.x + 10, $('scatter').clientWidth - tooltip.clientWidth - 6)}px`
  tooltip.style.top = `${Math.max(point.y - 32, 0)}px`
})
$('scatter').addEventListener('pointerleave', () => { $('scatter-tooltip').hidden = true })
$('scatter').addEventListener('click', (event) => {
  const point = hitPoint(event)
  if (point) changeFilter('pair', state.pair === point.key ? null : point.key)
})
$('share').addEventListener('click', async () => {
  writeView()
  try {
    await navigator.clipboard.writeText(location.href)
    $('share-status').textContent = 'View link copied.'
  } catch {
    $('share-status').textContent = 'Copy the current URL from the address bar.'
  }
})
$('export').addEventListener('click', () => {
  if (!state.record) return
  const { dataset, release, sha256 } = state.source
  const data = JSON.stringify({ source: { dataset, release, sha256 }, record: state.record }, null, 2)
  const url = URL.createObjectURL(new Blob([`${data}\n`], { type: 'application/json' }))
  const link = element('a')
  link.href = url
  link.download = `${dataset}-${state.record.id}.json`
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
})
$('compute-form').addEventListener('submit', async (event) => {
  event.preventDefault()
  if (!state.record || !state.kernelEnabled || state.computing) return
  const form = new FormData(event.currentTarget)
  const properties = form.getAll('property')
  const status = $('kernel-help')
  status.classList.remove('error')
  if (!properties.length) {
    status.textContent = 'Choose at least one CIProp key.'
    return
  }
  const recordId = state.record.id
  const backend = state.backend
  const serial = requestSerial
  state.computing = true
  renderKernelState()
  status.textContent = `Calculating configuration #${recordId} with ${backendName(backend)}…`
  const output = $('compute-output')
  output.hidden = true
  try {
    const result = await loadJSON('/api/compute', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ record_id: recordId, properties, backend }),
    })
    if (serial !== requestSerial) return
    renderPropertyComparison(output, state.record, result)
    status.textContent = `Calculated configuration #${recordId} with ${backendName(result.backend)}.`
  } catch (error) {
    if (serial !== requestSerial) return
    status.classList.add('error')
    status.textContent = error.message
  } finally {
    state.computing = false
    $('kernel-inputs').disabled = !state.kernelEnabled || !state.record
    if (serial !== requestSerial) renderKernelState()
  }
})

window.addEventListener('popstate', () => {
  if (!state.source) return
  readView()
  renderView({ restorePage: true, reload: true })
})

const redraw = new ResizeObserver(() => {
  if (!state.source) return
  drawCurrentScatter()
  drawHero()
})
redraw.observe($('scatter'))
redraw.observe($('hero-field'))
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (state.source) drawCurrentScatter()
})

updateMethodBackend = mountMethodLab({
  $, element, loadJSON, backendName, getBackend: () => state.kernelEnabled ? state.backend : null,
  getRecord: () => state.record,
})
const backendControls = [...document.querySelectorAll('[data-backend-select]')]

function renderBackendControls() {
  for (const control of backendControls) {
    control.disabled = !state.kernelEnabled
    for (const option of control.options) option.disabled = !state.backends.includes(option.value)
    control.value = state.backend
  }
  renderKernelState()
}

for (const control of backendControls) {
  control.addEventListener('change', () => {
    if (!state.backends.includes(control.value)) return
    state.backend = control.value
    renderBackendControls()
  })
}

loadJSON('/api/kernel').then(({ enabled, default_backend, backends }) => {
  state.backends = Array.isArray(backends) ? backends.filter((name) => Object.hasOwn(backendNames, name)) : []
  state.kernelEnabled = enabled === true && state.backends.length > 0
  state.backend = state.backends.includes(default_backend) ? default_backend : state.backends[0] ?? 'python'
}).catch(() => {}).finally(() => {
  state.kernelChecked = true
  renderBackendControls()
})

loadJSON('/api/catalog').then(({ records, dataset, release, sha256 }) => {
  if (!records?.length) throw new Error('The released catalogue is empty.')
  state.source = { dataset, release, sha256 }
  state.records = records
  const h11 = Math.max(...records.map((record) => record.h11))
  const h21 = Math.max(...records.map((record) => record.h21))
  state.domain = { h11: Math.max(4, Math.ceil(h11 / 4) * 4), h21: Math.max(5, Math.ceil(h21 / 5) * 5) }
  const values = records.map(({ euler }) => euler)
  const minimum = Math.min(...values), maximum = Math.max(...values)
  const start = binStart({ euler: minimum }), end = binStart({ euler: maximum })
  state.bins = Array.from({ length: (end - start) / binWidth + 1 }, (_, i) => start + i * binWidth)
  $('release-label').textContent = `${dataset} · CIPro ${release}`
  $('total-records').textContent = number.format(records.length)
  $('total-hodge').textContent = number.format(hodgeGroups(records).length)
  const placeholders = records.filter(isHodgePlaceholder).length
  $('hodge-sentinel').textContent = `${number.format(placeholders)} product records use (0, 0) as a Hodge placeholder and are omitted from this plot.`
  $('hodge-sentinel').hidden = !placeholders
  $('total-euler').textContent = `${minimum} to ${maximum}`
  $('release-sha').textContent = sha256
  readView()
  renderView({ restorePage: true, reload: true })
  drawHero()
}).catch((error) => {
  $('result-count').textContent = 'Catalogue unavailable'
  $('catalogue-error').textContent = error.message
  $('catalogue-error').hidden = false
  $('page-label').textContent = 'Catalogue unavailable'
})
