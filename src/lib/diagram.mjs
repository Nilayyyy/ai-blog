// Renders a diagram spec (JSON written by the generator) as plain HTML. No client-side library,
// and untrusted text is always escaped, so a bad spec can never break the page.

const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const lim = (s, n) => String(s ?? '').replace(/\s+/g, ' ').trim().slice(0, n);
const arr = (x, max) => (Array.isArray(x) ? x.filter((i) => i && typeof i === 'object' && i.label).slice(0, max) : []);

// What the speaker button reads out instead of the boxes and arrows.
export function speechForDiagram(d) {
  const bits = [];
  if (d.title) bits.push(`Diagram: ${lim(d.title, 80)}.`);
  if (d.type === 'flow') {
    arr(d.steps, 5).forEach((s, i) => bits.push(`Step ${i + 1}: ${lim(s.label, 40)}. ${lim(s.detail, 100)}.`));
  } else if (d.type === 'stack') {
    arr(d.layers, 5).forEach((s, i) => bits.push(`Layer ${i + 1}: ${lim(s.label, 40)}. ${lim(s.detail, 100)}.`));
  } else if (d.type === 'compare') {
    for (const side of ['before', 'after']) {
      const s = d[side] || {};
      const pts = (Array.isArray(s.points) ? s.points : []).slice(0, 4).map((p) => lim(p, 70)).join('. ');
      bits.push(`${lim(s.heading || side, 30)}: ${pts}.`);
    }
  }
  if (d.caption) bits.push(lim(d.caption, 160));
  return bits.join(' ').replace(/\.\s*\./g, '.').replace(/\s+/g, ' ').trim();
}

export function renderDiagram(d) {
  if (!d || typeof d !== 'object') throw new Error('diagram must be an object');
  const title = lim(d.title, 80);
  const head = title ? `<figcaption class="diagram-title">${esc(title)}</figcaption>` : '';
  const caption = d.caption ? `<p class="diagram-caption">${esc(lim(d.caption, 160))}</p>` : '';
  let inner = '';

  if (d.type === 'flow') {
    const steps = arr(d.steps, 5);
    if (steps.length < 2) throw new Error('flow needs at least two steps');
    const items = steps
      .map(
        (s, i) =>
          `<li><span class="step-n" aria-hidden="true">${i + 1}</span><strong>${esc(lim(s.label, 40))}</strong><span class="step-detail">${esc(lim(s.detail, 100))}</span></li>`
      )
      .join('');
    inner = `<ol class="flow" style="--n:${steps.length}">${items}</ol>`;
  } else if (d.type === 'stack') {
    const layers = arr(d.layers, 5);
    if (layers.length < 2) throw new Error('stack needs at least two layers');
    const items = layers
      .map(
        (s, i) =>
          `<li style="--i:${i}"><strong>${esc(lim(s.label, 40))}</strong><span class="step-detail">${esc(lim(s.detail, 100))}</span></li>`
      )
      .join('');
    inner = `<ol class="stack">${items}</ol>`;
  } else if (d.type === 'compare') {
    const side = (key, cls) => {
      const s = d[key] || {};
      const pts = (Array.isArray(s.points) ? s.points : []).slice(0, 4).filter(Boolean);
      if (pts.length < 1) throw new Error('compare needs points');
      return `<div class="side ${cls}"><p class="side-title">${esc(lim(s.heading || key, 30))}</p><ul>${pts
        .map((p) => `<li>${esc(lim(p, 70))}</li>`)
        .join('')}</ul></div>`;
    };
    inner = `<div class="cmp">${side('before', 'before')}<span class="cmp-arrow" aria-hidden="true"></span>${side('after', 'after')}</div>`;
  } else {
    throw new Error(`unknown diagram type: ${d.type}`);
  }

  return `<figure class="diagram diagram-${d.type}" data-speech="${esc(speechForDiagram(d))}" role="group" aria-label="${esc(title || 'Diagram')}">${head}${inner}${caption}</figure>`;
}
