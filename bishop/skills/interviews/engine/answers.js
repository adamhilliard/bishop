// The answers file: everything a candidate has written in their decks, in one JSON file.
// It's what Export Answers writes, what Import Answers reads, and what build_deck.py --master
// embeds so an interview deck can show the candidate's master answers. The page loads this file
// first, so the engine can use ANSWERS_FILE. The shape is written up in references/answers-file.md.
//
//   toFile(raw)    this browser's rows -> the file
//   fromFile(f)    the file            -> rows for this browser
//   checkFile(f)   the problems with a file (an empty list when it is sound)
const ANSWERS_FILE = (() => {
  const FORMAT = 'bishop.interviews.answers';
  const VERSION = 1;

  // A saved row is "<question id>" or "<question id>--<part>". These parts are known; any other
  // part rides along under "extra" so nothing is lost.
  const PARTS = { sections: 'json', locked: 'flag' };
  const byId = (a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
  const sortKeys = (o) => Object.fromEntries(Object.keys(o).sort().map((k) => [k, o[k]]));

  // raw = { answers: [{deck, slide_id, text}], edits: [{deck, slide_id, field, before, after}] }
  function toFile(raw, { exported = new Date().toISOString() } = {}) {
    const decks = {};
    const deckOf = (slug) => (decks[slug] ||= { answers: {}, edits: [] });
    for (const a of raw.answers || []) {
      const i = a.slide_id.indexOf('--');
      const id = i < 0 ? a.slide_id : a.slide_id.slice(0, i),
        part = i < 0 ? 'text' : a.slide_id.slice(i + 2);
      const box = (deckOf(a.deck).answers[id] ||= {});
      const kind = PARTS[part];
      if (part === 'text') box.text = a.text;
      else if (kind === 'json') {
        try {
          box[part] = JSON.parse(a.text);
        } catch (e) {
          (box.extra ||= {})[part] = a.text;
        }
      } else if (kind === 'flag') box[part] = a.text === '1';
      else (box.extra ||= {})[part] = a.text;
    }
    for (const e of raw.edits || []) deckOf(e.deck).edits.push({ id: e.slide_id, field: e.field, before: e.before, after: e.after });
    for (const d of Object.values(decks)) {
      d.answers = sortKeys(Object.fromEntries(Object.entries(d.answers).map(([k, v]) => [k, sortKeys(v)])));
      d.edits.sort((a, b) => byId(a, b) || (a.field < b.field ? -1 : a.field > b.field ? 1 : 0));
    }
    return { format: FORMAT, version: VERSION, exported, decks: sortKeys(decks) };
  }

  function fromFile(f) {
    const problems = checkFile(f);
    if (problems.length) throw new Error('not a sound answers file:\n' + problems.join('\n'));
    const raw = { answers: [], edits: [] };
    for (const [slug, d] of Object.entries(f.decks)) {
      for (const [id, box] of Object.entries(d.answers || {})) {
        const row = (part, text) => raw.answers.push({ deck: slug, slide_id: part ? id + '--' + part : id, text });
        if (box.text != null) row('', box.text);
        for (const [part, kind] of Object.entries(PARTS)) {
          if (box[part] == null) continue;
          if (kind === 'json') row(part, JSON.stringify(box[part]));
          else if (box[part]) row(part, '1');
        }
        for (const [part, text] of Object.entries(box.extra || {})) row(part, text);
      }
      for (const e of d.edits || []) raw.edits.push({ deck: slug, slide_id: e.id, field: e.field, before: e.before, after: e.after });
    }
    return raw;
  }

  function checkFile(f) {
    const p = [];
    if (!f || typeof f !== 'object') return ['not an object'];
    if (f.format !== FORMAT) p.push(`format is "${f.format}", expected "${FORMAT}"`);
    if (f.version !== VERSION) p.push(`version is ${f.version}; this reads version ${VERSION}`);
    if (!f.decks || typeof f.decks !== 'object') p.push('decks must be an object keyed by deck slug');
    if (p.length) return p;
    for (const [slug, d] of Object.entries(f.decks)) {
      if (!/^[a-z0-9-]{1,60}$/.test(slug)) p.push(`deck "${slug}": slug must be lowercase letters, digits and dashes`);
      for (const [id, box] of Object.entries(d.answers || {}))
        if (box.sections != null && !Array.isArray(box.sections)) p.push(`deck ${slug}, ${id}: sections must be a list`);
    }
    return p;
  }

  return { toFile, fromFile, checkFile, FORMAT, VERSION };
})();
