// P5 §6 study tooling — CSV / Anki export of a session's word lookups (H537).
//
// Pure serialisers (unit-tested without a DOM) + one small DOM download helper.
// A "session lookup" row is {slp1, iast, deva, gloss, dicts} — the words the
// reader opened this session, exportable to a spreadsheet (CSV) or an Anki deck
// (tab-separated: front = Devanagari + IAST, back = gloss).

function csvCell(v) {
  const s = v == null ? '' : String(v);
  // RFC-4180: quote if the cell holds a comma, quote, or newline; double inner quotes.
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function toCsv(rows) {
  const head = ['slp1', 'iast', 'devanagari', 'gloss', 'dicts'];
  const lines = [head.join(',')];
  for (const r of rows || []) {
    lines.push([r.slp1, r.iast, r.deva, r.gloss, r.dicts].map(csvCell).join(','));
  }
  return lines.join('\r\n');
}

export function toAnki(rows) {
  // Anki's default text importer is tab-separated, one note per line, fields in
  // column order (front, back). A literal tab/newline inside a field would break
  // the row, so collapse whitespace in each field. Front = देव / iast, back = gloss.
  const clean = (v) => (v == null ? '' : String(v).replace(/[\t\r\n]+/g, ' ').trim());
  const lines = [];
  for (const r of rows || []) {
    const front = `${clean(r.deva)} · ${clean(r.iast)}`;
    lines.push([front, clean(r.gloss)].join('\t'));
  }
  return lines.join('\n');
}

// Strip HTML tags + collapse whitespace to a short gloss for a lookup row.
export function glossOf(renderedHtml, limit = 120) {
  const text = (renderedHtml || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  return text.length > limit ? text.slice(0, limit - 1).trimEnd() + '…' : text;
}

export function downloadFile(filename, content, mime = 'text/plain') {
  // UTF-8 with a BOM for CSV so Excel opens Devanagari correctly; Anki reads
  // UTF-8 fine without one.
  const bom = mime.startsWith('text/csv') ? '﻿' : '';
  const blob = new Blob([bom + content], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
