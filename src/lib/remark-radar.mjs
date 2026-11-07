// Markdown plugin for AI Dev Radar posts:
//  1. turns ```diagram code blocks (JSON) into rendered diagrams
//  2. tags the Situation / Task / Action / Result headings so they get their S, T, A, R badges
import { renderDiagram } from './diagram.mjs';

const STAR = { situation: 'S', task: 'T', action: 'A', result: 'R' };

const textOf = (n) => (typeof n.value === 'string' ? n.value : (n.children || []).map(textOf).join(''));

function walk(node, fn) {
  fn(node);
  (node.children || []).forEach((c) => walk(c, fn));
}

export default function remarkRadar() {
  return (tree) => {
    walk(tree, (node) => {
      if (node.type === 'code' && node.lang === 'diagram') {
        let html;
        try {
          html = renderDiagram(JSON.parse(node.value));
        } catch (e) {
          html = `<!-- diagram not rendered: ${String(e.message).replace(/--/g, '-')} -->`;
        }
        node.type = 'html';
        node.value = html;
        delete node.lang;
        delete node.meta;
        return;
      }
      if (node.type === 'heading' && node.depth === 2) {
        const word = textOf(node).trim().split(/[\s:\u2014\u2013-]/)[0].toLowerCase();
        if (STAR[word]) {
          node.data = { ...(node.data || {}), hProperties: { className: ['star'], 'data-star': STAR[word] } };
        }
      }
    });
  };
}
