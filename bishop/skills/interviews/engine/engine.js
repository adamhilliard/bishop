const CONTENT = JSON.parse(document.getElementById('deck-content').textContent);

const META = JSON.parse(document.getElementById('deck-meta').textContent);

const ORIGINAL_CONTENT = JSON.parse(JSON.stringify(CONTENT));
const DECK = META.deck || {};
// The master deck (deck.master) holds the questions every interview asks: the candidate's answers live on
// its questions, and each company deck shows them on the questions it links with "core".
const MASTER = !!DECK.master;
// The name in the top bar: the name the candidate gave their search at setup (build_deck.py fills it in).
const BRAND = DECK.site?.brand || 'Bishop';
const CORE_ANS = new Map();
const coreAnswers = () => (MASTER ? ANSWERS : CORE_ANS);
// The master deck sits next to this one, as core.html.
const coreLink = (qid) => location.pathname.replace(/[^/]*$/, MASTER_SLUG + '.html') + '#' + encodeURIComponent(qid);
// The deck's slug: META.deck.slug, else one made from its title.
const DECK_SLUG =
  DECK.slug ||
  String(DECK.title || 'deck')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
// The master deck's slug: the one company decks read answers from.
const MASTER_SLUG = DECK.site?.masterSlug || 'core';
// ---- Storage. Everything the candidate writes lives in this browser, in one answers file
// (answers.js, references/answers-file.md), with Export and Import to keep a copy or move it.
const STORE = (() => {
  const KEY = 'bishop-interviews:answers';
  let raw = null;
  const empty = () => ({ answers: [], edits: [] });
  function load() {
    if (raw) return raw;
    try {
      const saved = localStorage.getItem(KEY);
      if (saved) raw = JSON.parse(saved);
    } catch (e) {}
    // A deck can ship with the candidate's answers file: a script tag "master-data" holding it. It
    // wins when it's newer than this browser's copy (it came from a later export), never otherwise.
    const el = document.getElementById('master-data');
    if (el)
      try {
        const m = JSON.parse(el.textContent);
        if (!raw || !raw.savedAt || String(m.exported) > raw.savedAt)
          raw = { ...ANSWERS_FILE.fromFile(m), savedAt: String(m.exported) };
      } catch (e) {}
    return (raw ||= empty());
  }
  function save() {
    raw.savedAt = new Date().toISOString();
    localStorage.setItem(KEY, JSON.stringify(raw));
  }
  const strip = ({ deck, ...row }) => row;
  return {
    async answers(deck) {
      return load().answers.filter((a) => a.deck === deck).map(strip);
    },
    async saveAnswer(deck, id, text) {
      const r = load();
      r.answers = r.answers.filter((a) => !(a.deck === deck && a.slide_id === id));
      if (text) r.answers.push({ deck, slide_id: id, text });
      save();
    },
    async edits(deck) {
      return load().edits.filter((e) => e.deck === deck).map(strip);
    },
    async saveEdit(deck, { id, field, before, after }) {
      const r = load();
      r.edits = r.edits.filter((e) => !(e.deck === deck && e.slide_id === id && e.field === field));
      r.edits.push({ deck, slide_id: id, field, before, after });
      save();
    },
    async dropEdit(deck, { id, field }) {
      const r = load();
      r.edits = r.edits.filter((e) => !(e.deck === deck && e.slide_id === id && e.field === field));
      save();
    },
    // The whole set as one file, to keep or to move to another browser.
    exportFile() {
      const m = ANSWERS_FILE.toFile(load());
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(m, null, 2)], { type: 'application/json' }));
      a.download = 'Master_Answers.json';
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    },
    async importFile(file) {
      raw = ANSWERS_FILE.fromFile(JSON.parse(await file.text()));
      // An import is the newest copy there is; save() stamps it.
      save();
    },
  };
})();
// Saving fails in this browser only when it blocks saved data (a private window does).
const SAVED_WHERE = 'in this browser';
const TRY_AGAIN = 'Try again. If it keeps failing, this browser may be blocking saved data (a private window does).';
const TYPE_AGAIN = 'Type again. If it keeps failing, this browser may be blocking saved data (a private window does).';
const editTimers = new Map();
// Save one field in this browser a moment after typing stops. Back to the original text removes the saved edit.
function saveEdit(id, field, before, after) {
  const key = id + '::' + field;
  clearTimeout(editTimers.get(key));
  editTimers.set(
    key,
    setTimeout(async () => {
      editTimers.delete(key);
      try {
        if (after === before) await STORE.dropEdit(DECK_SLUG, { id, field, before, after });
        else await STORE.saveEdit(DECK_SLUG, { id, field, before, after });
        updateEditUI();
      } catch (e) {
        toast('That edit didn\u2019t save. ' + TYPE_AGAIN);
      }
    }, 700),
  );
}
// Saved edits apply over the built text, but only where the built text still matches what was edited.
function applySavedEdits(rows) {
  let n = 0;
  // Added questions first, so edits to them have something to land on.
  rows = [...(rows || [])].sort((a, b) => (b.field === '__added') - (a.field === '__added'));
  for (const row of rows) {
    if (row.field === '__added') {
      try {
        if (!byId.has(row.slide_id) && !DELETED.has(row.slide_id)) {
          insertSlide({ ...JSON.parse(row.after), id: row.slide_id, chain: row.slide_id });
          n++;
        }
      } catch (e) {}
      continue;
    }
    if (row.field === '__deleted') {
      if (row.after === '1' && removeSlide(row.slide_id)) n++;
      continue;
    }
    const obj = byId.get(row.slide_id),
      orig = originalById(row.slide_id);
    if (!obj || !orig) continue;
    const before = getPath(orig, row.field);
    if (before !== row.before) continue;
    setPath(obj, row.field, row.after);
    editChanges.set(row.slide_id + '::' + row.field, {
      id: row.slide_id,
      field: row.field,
      before,
      after: row.after,
    });
    n++;
  }
  return n;
}
const editChanges = new Map();
const $ = (s) => document.querySelector(s),
  esc = (s) =>
    String(s ?? '').replace(
      /[&<>"']/g,
      (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
    );
const sections = (() => {
    const declared = (META.sections || []).map((x) => ({ ...x }));
    const ids = new Set(declared.map((x) => x.id));
    const extra = [];
    for (const x of CONTENT) {
      if (!ids.has(x.section) && !extra.some((e) => e.id === x.section))
        extra.push({
          id: x.section,
          title: x.title || x.section,
          subtitle: '',
          color: DECK.theme?.accent || 'var(--signal)',
          hidden: true,
        });
    }
    return [...declared, ...extra];
  })(),
  byId = new Map(CONTENT.map((x) => [x.id, x])),
  sectionMap = new Map(sections.map((x) => [x.id, x]));
const state = {
  id: 'cover',
  purpose: 'study',
  globalMode: 1,
  overrides: new Map(),
  layers: new Map(),
  flags: new Set(),
  drill: false,
  preDrill: 'cover',
  timers: new Map(),
  flagFilter: false,
  editMode: false,
  lastId: null,
  asked: new Set(),
  views: new Map(),
};
// Each deck keeps its own flags, timings, ticks and place, so practicing one deck never marks another.
const PROGRESS_KEY = 'bishop-interviews:progress:' + DECK_SLUG;
function saveProgress() {
  try {
    localStorage.setItem(
      PROGRESS_KEY,
      JSON.stringify({
        views: [...state.views],
        asked: [...state.asked],
        flags: [...state.flags],
        timers: [...state.timers],
        overrides: [...state.overrides],
        globalMode: state.globalMode,
        purpose: state.purpose,
        id: state.id,
      }),
    );
  } catch (e) {}
}
function loadProgress() {
  try {
    const p = JSON.parse(localStorage.getItem(PROGRESS_KEY) || 'null');
    if (!p) return;
    state.flags = new Set(p.flags || []);
    state.asked = new Set(p.asked || []);
    state.views = new Map(p.views || []);
    state.timers = new Map(p.timers || []);
    state.overrides = new Map((p.overrides || []).filter(([, m]) => m === 1 || m === 2));
    state.globalMode = p.globalMode === 2 ? 2 : 1;
    state.purpose = p.purpose === 'test' ? 'test' : 'study';
    state.lastId = p.id || null;
  } catch (e) {}
}
let runningId = null,
  startedAt = 0,
  toastTimeout;
const current = () => byId.get(state.id),
  mode = () => state.overrides.get(state.id) || state.globalMode,
  layer = () => state.layers.get(state.id) || 0;
const target = () => current().target || 0;
function ordered() {
  const out = sections.flatMap(
    (s) => CONTENT.filter((x) => x.section === s.id).map((x) => x.id),
  );
  const seen = new Set(out);
  for (const x of CONTENT)
    if (!seen.has(x.id)) {
      out.push(x.id);
      seen.add(x.id);
    }
  return out;
}
function activeOrder() {
  const ids = ordered();
  return state.drill ? ids.filter((id) => state.flags.has(id)) : ids;
}
function toast(message) {
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => ($('#toast').hidden = true), 2800);
}
function getPath(obj, path) {
  return path.split('.').reduce((v, k) => (v == null ? undefined : v[k]), obj);
}
function setPath(obj, path, value) {
  const parts = path.split('.');
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) cur = cur[parts[i]];
  cur[parts.at(-1)] = value;
}
function originalById(id) {
  return ORIGINAL_CONTENT.find((x) => x.id === id);
}
function editAttrs(s, field, multiline = false) {
  return state.editMode
    ? ` contenteditable="true" spellcheck="true" data-edit-id="${s.id}" data-edit-field="${field}" data-edit-multiline="${multiline ? '1' : '0'}"`
    : '';
}
function normalizeEdit(el) {
  let value = el.innerText.replace(/\u00a0/g, ' ').replace(/\r/g, '');
  if (el.dataset.editMultiline === '1') value = value.replace(/\n{3,}/g, '\n\n').trim();
  else
    value = value
      .replace(/\n+/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();
  return value;
}

// ---- Practice: record yourself, play it back, read the transcript, and keep a typed answer.
// Takes (audio + transcript) stay in this browser, in IndexedDB, keyed by deck and slide. Transcripts
// come from the browser's speech recognition (Chrome sends that audio to Google to transcribe).
// Typed answers save in this browser with everything else (STORE), and travel in the answers file.
const TAKES = { db: null, ids: new Set(), urls: new Map() };
const ANSWERS = new Map();
const takeKey = (id) => (DECK_SLUG || 'local') + '|' + id;
function takesDB() {
  return (
    TAKES.db ||
    (TAKES.db = new Promise((ok, no) => {
      const r = indexedDB.open('bishop-interviews-takes', 1);
      r.onupgradeneeded = () => r.result.createObjectStore('takes');
      r.onsuccess = () => ok(r.result);
      r.onerror = () => no(r.error);
    }))
  );
}
async function takeOp(mode, fn) {
  const db = await takesDB();
  return new Promise((ok, no) => {
    const tx = db.transaction('takes', mode);
    const req = fn(tx.objectStore('takes'));
    tx.oncomplete = () => ok(req && req.result);
    tx.onerror = () => no(tx.error);
  });
}
const getTake = (id) => takeOp('readonly', (s) => s.get(takeKey(id)));
const putTake = (id, v) => takeOp('readwrite', (s) => s.put(v, takeKey(id)));
const deleteTake = (id) => takeOp('readwrite', (s) => s.delete(takeKey(id)));
function dropTakeURL(id) {
  const u = TAKES.urls.get(id);
  if (u) {
    URL.revokeObjectURL(u);
    TAKES.urls.delete(id);
  }
}
async function loadTakeIds() {
  try {
    const p = (DECK_SLUG || 'local') + '|';
    const keys = await takeOp('readonly', (s) => s.getAllKeys());
    TAKES.ids = new Set(
      keys
        .map(String)
        .filter((k) => k.startsWith(p))
        .map((k) => k.slice(p.length)),
    );
    render();
  } catch (e) {}
}
function loadAnswers() {
  STORE.answers(DECK_SLUG).then((rows) => {
    if (!rows) return;
    for (const a of rows) ANSWERS.set(a.slide_id, a.text);
    render();
  });
  // A company deck shows your master answers on the questions it links to the master deck.
  if (!MASTER && DECK_SLUG !== MASTER_SLUG)
    STORE.answers(MASTER_SLUG).then((rows) => {
      if (!rows) return;
      for (const a of rows) CORE_ANS.set(a.slide_id, a.text);
      render();
    });
}
async function saveAnswer(id, text) {
  text = String(text || '')
    .replace(/\r\n/g, '\n')
    .trim();
  try {
    await STORE.saveAnswer(DECK_SLUG, id, text);
    if (text) ANSWERS.set(id, text);
    else ANSWERS.delete(id);
    return true;
  } catch (e) {
    toast('That answer didn’t save. ' + TRY_AGAIN);
    return false;
  }
}

let rec = null;
const practiceSlide = (s) =>
  ['question', 'story'].includes(s.kind) && (sectionMap.get(s.section) || {}).role !== 'ask';
// Study: the answer is open to work on (STAR, open field, story picker). Test: it hides, you say it, the take records.
const studying = () => state.purpose === 'study';
const studyOpen = (s) => studying() && s.kind === 'question' && practiceSlide(s);
function setPurpose(p) {
  if (rec) stopRecord();
  pauseTimer();
  state.purpose = p;
  state.layers.clear();
  render();
  toast(p === 'study' ? 'Study: build your answers and tie your stories.' : 'Test: say it first, then reveal. ● records with a transcript.');
}
async function toggleRecord() {
  if (rec) {
    stopRecord();
    return;
  }
  const s = current();
  if (!practiceSlide(s) || studying()) return;
  if (!(navigator.mediaDevices && window.MediaRecorder)) {
    toggleTimer();
    toast('This browser can’t record. Timing only.');
    return;
  }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    toast('The microphone is blocked. Allow it in the address bar to record. Timing only for now.');
    toggleTimer();
    return;
  }
  const mime =
    ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find((m) => MediaRecorder.isTypeSupported(m)) || '';
  const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : {});
  const r = {
    id: s.id,
    recorder,
    stream,
    chunks: [],
    finalText: '',
    interim: '',
    started: performance.now(),
    mime: recorder.mimeType || mime || 'audio/webm',
  };
  recorder.ondataavailable = (e) => {
    if (e.data && e.data.size) r.chunks.push(e.data);
  };
  rec = r;
  recorder.start(1000);
  startSpeech(r);
  if (runningId !== s.id) toggleTimer();
  render();
}
function stopRecord() {
  const r = rec;
  if (!r) return;
  rec = null;
  stopSpeech(r);
  if (runningId === r.id) pauseTimer();
  r.recorder.onstop = async () => {
    r.stream.getTracks().forEach((t) => t.stop());
    const blob = new Blob(r.chunks, { type: r.mime });
    const take = {
      blob,
      transcript: (r.finalText + ' ' + r.interim).replace(/\s+/g, ' ').trim(),
      seconds: Math.round((performance.now() - r.started) / 1000),
      at: new Date().toISOString(),
    };
    try {
      await putTake(r.id, take);
      TAKES.ids.add(r.id);
      dropTakeURL(r.id);
    } catch (e) {
      toast('Couldn’t save that take in this browser.');
    }
    if (state.id === r.id) render();
  };
  r.recorder.stop();
  paintTimer();
}
function startSpeech(r) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  const sr = new SR();
  sr.continuous = true;
  sr.interimResults = true;
  sr.lang = 'en-US';
  sr.onresult = (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const x = e.results[i];
      if (x.isFinal) r.finalText += (r.finalText ? ' ' : '') + x[0].transcript.trim();
      else interim += x[0].transcript;
    }
    r.interim = interim;
    const el = $('#live-transcript');
    if (el && state.id === r.id) el.textContent = (r.finalText + ' ' + interim).trim() || 'Listening…';
  };
  sr.onend = () => {
    if (rec === r) {
      try {
        sr.start();
      } catch (e) {}
    }
  };
  sr.onerror = () => {};
  r.speech = sr;
  try {
    sr.start();
  } catch (e) {}
}
function stopSpeech(r) {
  if (r.speech) {
    r.speech.onend = null;
    try {
      r.speech.stop();
    } catch (e) {}
  }
}

function practiceHTML(s) {
  if (!practiceSlide(s) || studying()) return '';
  const live = rec && rec.id === s.id;
  return `<section class="practice">${live ? `<div class="take live"><div class="take-head"><span class="rec-dot"></span><b>Recording</b><span class="muted">Press ■ or T to stop.</span></div><p id="live-transcript" class="take-text">${esc((rec.finalText + ' ' + rec.interim).trim() || 'Listening…')}</p></div>` : ''}<div id="take-slot"></div></section>`;
}
async function hydrateTake(s) {
  const slot = $('#take-slot');
  if (!slot || !TAKES.ids.has(s.id)) return;
  let t;
  try {
    t = await getTake(s.id);
  } catch (e) {
    return;
  }
  if (!t || state.id !== s.id) return;
  let url = TAKES.urls.get(s.id);
  if (!url) {
    url = URL.createObjectURL(t.blob);
    TAKES.urls.set(s.id, url);
  }
  const when = new Date(t.at);
  slot.innerHTML = `<div class="take"><div class="take-head"><b>Your Last Take</b><span class="muted">${clock((t.seconds || 0) * 1000)} · ${esc(when.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }))} ${esc(when.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }))}</span><button data-action="take-delete" class="quiet">Delete Take</button></div><audio controls preload="metadata" src="${url}"></audio>${t.transcript ? `<details><summary>Transcript (${t.transcript.split(/\s+/).filter(Boolean).length} words)</summary><p class="take-text">${esc(t.transcript)}</p><div class="take-actions"><button data-action="take-use">Add as a Section</button></div></details>` : '<p class="muted tiny">No transcript for this take. Transcripts need Chrome or Edge.</p>'}</div>`;
}
function markTakes() {
  for (const el of document.querySelectorAll('#slide [data-go]'))
    el.classList.toggle('has-take', TAKES.ids.has(el.dataset.go));
}
async function practiceAction(a) {
  const s = current();
  if (a === 'take-delete') {
    try {
      await deleteTake(s.id);
    } catch (e) {}
    TAKES.ids.delete(s.id);
    dropTakeURL(s.id);
    render();
    toast('Take deleted.');
    return true;
  }
  if (a === 'take-use') {
    const take = await getTake(s.id).catch(() => null);
    if (!take || !take.transcript) return true;
    draftOf(s).push({ name: 'From My Take', text: take.transcript });
    touchDraft();
    queueSections(s, 0);
    render();
    toast(studying() ? 'Transcript added as a section.' : 'Transcript added as a section. Switch to Study to work on it.');
    return true;
  }
  return false;
}
// ---- Delete a question from its card (the small × in the corner).
const DELETED = new Set();
function removeSlide(id) {
  const s = byId.get(id);
  if (!s) return false;
  const gone = new Set([id]);
  for (let i = CONTENT.length - 1; i >= 0; i--) if (gone.has(CONTENT[i].id)) CONTENT.splice(i, 1);
  DELETED.add(id);
  // Gone from the lookup too, so the question's old link can't open it again.
  for (const g of gone) {
    byId.delete(g);
    state.flags.delete(g);
    state.asked.delete(g);
  }
  if (gone.has(state.id))
    state.id = (CONTENT.find((x) => x.kind === 'section' && x.section === s.section) || CONTENT[0]).id;
  return true;
}
// A deck's own question, deleted from its card: recorded as a deck edit (field "__deleted") and hidden.
async function deleteQuestion(id) {
  const s = byId.get(id);
  if (!s) return;
  if (!confirm(`Delete this question?\n\n“${s.title}”\n\nIt is removed from this deck ${SAVED_WHERE}.`)) return;
  try {
    await STORE.saveEdit(DECK_SLUG, { id, field: '__deleted', before: '', after: '1' });
    removeSlide(id);
    saveProgress();
    syncHash('replace');
    render();
    toast('Question deleted.');
  } catch (e) {
    toast('Couldn’t delete that question. ' + TRY_AGAIN);
  }
}
// A deck question added from the page, placed after the last item of its section. It joins the built
// copy too, so its own text edits apply like any other question's.
function insertSlide(x) {
  let at = -1;
  CONTENT.forEach((c, i) => {
    if (c.section === x.section) at = i;
  });
  CONTENT.splice(at < 0 ? CONTENT.length : at + 1, 0, x);
  byId.set(x.id, x);
  ORIGINAL_CONTENT.push(JSON.parse(JSON.stringify(x)));
}
// The Questions to Ask theme a card shows, from the code in its corner.
function themeOf(card) {
  const code = card && card.querySelector('.comp-code')?.textContent.trim();
  return code ? (DECK.askThemes || []).find((x) => x.code === code) || null : null;
}
// Adding a question (the master deck, in Study): under a section's cards, or in a Questions to Ask
// theme. It saves as a deck edit ("__added") in this browser.
function markAdds() {
  if (!MASTER || !studying()) return;
  const s = current();
  if (s.kind !== 'section') return;
  const add = (where) => `<button class="q-add quiet" data-add-q="${esc(where)}">+ Add Question</button>`;
  if ((sectionMap.get(s.section) || {}).role === 'ask')
    for (const card of document.querySelectorAll('#slide .comp-card:not(.ready-card)')) {
      if (card.querySelector(':scope > .q-add, :scope > .q-add-input')) continue;
      const t = themeOf(card);
      if (!t) continue;
      const foot = card.querySelector(':scope > .comp-foot');
      if (foot) foot.insertAdjacentHTML('beforebegin', add('theme:' + t.id));
      else card.insertAdjacentHTML('beforeend', add('theme:' + t.id));
    }
  const grid = document.querySelector('#slide .comp-grid');
  if (s.cards && grid && !grid.querySelector('.comp-card') && !document.querySelector('#slide .q-add-row'))
    grid.insertAdjacentHTML('afterend', `<div class="q-add-row">${add('sec:' + s.section)}</div>`);
}
async function addQuestion(where, title) {
  const i = where.indexOf(':'),
    kind = where.slice(0, i),
    id = where.slice(i + 1);
  try {
    const section = kind === 'sec' ? id : current().section,
      role = sectionMap.get(section)?.role;
    const slide = {
      kind: 'question',
      section,
      title,
      target: role === 'ask' ? 0 : 60,
      why: '',
      ...(role ? { origin: 'standard' } : {}),
      ...(kind === 'theme' ? { theme: id } : {}),
    };
    const newId = 'Q' + section + 'x' + Date.now().toString(36).slice(-6);
    await STORE.saveEdit(DECK_SLUG, { id: newId, field: '__added', before: '', after: JSON.stringify(slide) });
    insertSlide({ ...slide, id: newId, chain: newId });
    render();
    toast('Question added.');
  } catch (e) {
    toast('Couldn’t add that question. ' + TRY_AGAIN);
    render();
  }
}
document.addEventListener(
  'click',
  (e) => {
    const b = e.target.closest('[data-add-q]');
    if (!b) return;
    e.preventDefault();
    e.stopPropagation();
    const f = document.createElement('input');
    f.className = 'q-add-input';
    f.placeholder = 'New question';
    f.setAttribute('aria-label', 'New question');
    f.dataset.where = b.dataset.addQ;
    b.replaceWith(f);
    f.focus();
  },
  true,
);
document.addEventListener(
  'keydown',
  (e) => {
    const f = e.target.closest && e.target.closest('.q-add-input');
    if (!f) return;
    e.stopPropagation();
    if (e.key === 'Escape') {
      e.preventDefault();
      render();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const title = f.value.replace(/\s+/g, ' ').trim();
      if (!title || f.disabled) return;
      f.disabled = true;
      addQuestion(f.dataset.where, title);
    }
  },
  true,
);
document.addEventListener('focusout', (e) => {
  const f = e.target.closest && e.target.closest('.q-add-input');
  if (f && !f.disabled && !f.value.trim()) setTimeout(render, 0);
});
function markDeletes() {
  for (const el of document.querySelectorAll('#slide .comp-qs [data-go], #slide .q-card[data-go], #slide [data-asked].ask-row')) {
    if (el.closest('.ready-card')) continue;
    const id = el.dataset.go || el.dataset.asked || el.querySelector('[data-asked]')?.dataset.asked;
    const s = byId.get(id);
    if (!s || s.kind !== 'question' || el.querySelector(':scope > .q-del')) continue;
    el.classList.add('deletable');
    el.insertAdjacentHTML(
      'beforeend',
      `<span class="q-del" data-del="${esc(id)}" role="button" tabindex="0" aria-label="Delete question" title="Delete this question">×</span>`,
    );
  }
}
document.addEventListener(
  'click',
  (e) => {
    const d = e.target.closest('[data-del]');
    if (!d) return;
    e.preventDefault();
    e.stopPropagation();
    deleteQuestion(d.dataset.del);
  },
  true,
);
document.addEventListener(
  'keydown',
  (e) => {
    const d = e.target.closest && e.target.closest('[data-del]');
    if (d && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      e.stopPropagation();
      deleteQuestion(d.dataset.del);
    }
  },
  true,
);
// ---- The answer, in named sections. A question starts with one section, "Answer"; add more and
// name them (Situation, Task, Action and Result for a STAR, or anything else). The layout saves to the
// deck answer "<id>--sections".
const STAR_NAMES = ['Situation', 'Task', 'Action', 'Result'];
function sectionsOf(s) {
  try {
    const a = JSON.parse(ANSWERS.get(s.id + '--sections') || 'null');
    if (Array.isArray(a) && a.length) return a.map((x) => ({ name: String(x.name || ''), text: String(x.text || '') }));
  } catch (e) {}
  return [{ name: 'Answer', text: ANSWERS.get(s.id) || '' }];
}
// The sections being edited on the current slide, so typing, renaming and adding share one copy.
// Until the first edit it's rebuilt every time, so saved answers arriving after the first paint still show.
let secDraft = null;
function draftOf(s) {
  if (!(secDraft && secDraft.id === s.id && secDraft.touched)) secDraft = { id: s.id, secs: sectionsOf(s) };
  return secDraft.secs;
}
const touchDraft = () => secDraft && (secDraft.touched = true);
function sectionsHTML(s) {
  const secs = draftOf(s);
  const has = (n) => secs.some((x) => x.name.trim().toLowerCase() === n.toLowerCase());
  const locked = isLocked(s), ro = locked ? ' readonly' : '';
  const row = (x, i) =>
    `<div class="ans-sec"><input class="ans-sec-name" data-sec-name="${i}"${ro} value="${esc(x.name)}" placeholder="Name it" aria-label="Section name" spellcheck="false"><textarea data-sec-text="${i}"${ro} rows="1" spellcheck="true" aria-label="${esc(x.name || 'Section')}" placeholder="Say it the way you would out loud.">${esc(x.text)}</textarea>${secs.length > 1 && !locked ? `<button class="ans-sec-del" data-sec-del="${i}" aria-label="Remove ${esc(x.name || 'this section')}" title="Remove section">×</button>` : ''}</div>`;
  return `<div class="ans-sections${locked ? ' locked' : ''}">${verifyHTML(s)}${secs.map(row).join('')}<div class="ans-sec-add"${locked ? ' hidden' : ''}><button data-action="sec-add" class="quiet">+ Add Section</button>${STAR_NAMES.every(has) ? '' : '<button data-action="sec-star" class="quiet">+ Add STAR</button>'}</div></div>`;
}
// Lock In: an answer you're happy with. It saves in this browser (deck answer "<id>--locked"), turns
// read-only until you unlock it, and puts a check on the question's card so what's left stands out.
// A company deck question showing its master answer carries the master deck's lock too.
const isLocked = (q) =>
  ANSWERS.get(q.id + '--locked') === '1' ||
  (!MASTER && !!q.core && !hasOwnAnswer(q) && CORE_ANS.get(q.core + '--locked') === '1');
// On a card it's a padlock in the lower-right corner; the card's border also closes around it.
const LOCK_SVG =
  '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><rect x="3" y="7" width="10" height="7.5" rx="1.5" fill="currentColor"/><path d="M5.25 7V5a2.75 2.75 0 0 1 5.5 0v2" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';
// An unlocked card shows the padlock open, so locked and not-yet-locked read apart at a glance.
const OPEN_LOCK_SVG =
  '<svg viewBox="-1.5 0 17.5 16" width="15.3" height="14" aria-hidden="true"><rect x="3" y="7" width="10" height="7.5" rx="1.5" fill="currentColor"/><path d="M5.25 7V4.5a2.75 2.75 0 0 0 -5.5 0V5.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';
const lockMark = (q) =>
  isLocked(q)
    ? `<span class="lock-mark on" title="Locked in" role="img" aria-label="Locked in">${LOCK_SVG}</span>`
    : `<span class="lock-mark" title="Not locked in yet" role="img" aria-label="Not locked in">${OPEN_LOCK_SVG}</span>`;
function lockHTML(s) {
  const on = isLocked(s);
  return `<button class="lock-btn${on ? ' on' : ''}" data-lock aria-pressed="${on}" title="${on ? 'Unlock to keep working on it' : 'Mark this answer as done'}">${on ? '✓ Locked In' : 'Lock In'}</button>`;
}
document.addEventListener('click', async (e) => {
  const btn = e.target.closest && e.target.closest('[data-lock]');
  if (!btn) return;
  const s = current(), on = isLocked(s);
  if (await saveAnswer(s.id + '--locked', on ? '' : '1')) {
    render();
    toast(on ? 'Unlocked.' : 'Locked in.');
  }
});
function secStatusHTML(s) {
  return `<span class="sec-status" id="sec-status" role="status">Saves as you type, ${SAVED_WHERE}.</span>${lockHTML(s)}`;
}
// The opening of a question's answer: its first section with words in it, first paragraph only.
function answerPreview(q) {
  for (const x of sectionsOf(q)) {
    const text = String(x.text || '').trim();
    if (text) return text.split(/\n\s*\n/)[0].replace(/\s+/g, ' ');
  }
  return '';
}
const previewHTML = (q) => {
  if (!studying()) return '';
  const p = answerPreview(q);
  return p ? `<span class="rc-preview" title="${esc(p)}">${esc(p)}</span>` : '';
};
// What still needs checking on this answer: the deck's note on the question (verify). Editing the answer
// counts as verifying it: the note clears (a deck edit, so its text can come back).
function verifyHTML(s) {
  return s.verify ? `<p class="verify-line study-verify"><b>Verify</b> ${esc(s.verify)}</p>` : '';
}
function markVerified(s) {
  if (!s.verify) return;
  const before = getPath(originalById(s.id) || {}, 'verify');
  s.verify = '';
  editChanges.set(s.id + '::verify', { id: s.id, field: 'verify', before, after: '' });
  saveEdit(s.id, 'verify', before, '');
  // Take the note off the page without re-rendering, so typing isn't interrupted.
  document.querySelectorAll('#slide .study-verify, #slide .question-meta .pill.verify').forEach((x) => x.remove());
  toast('Marked verified.');
}
const secStatus = (t) => {
  const el = $('#sec-status');
  if (el) el.textContent = t;
};
const secTimers = new Map();
// Save the section list: names, order and text.
function queueSections(s, wait = 800) {
  const secs = draftOf(s);
  clearTimeout(secTimers.get(s.id));
  secStatus('Saving…');
  secTimers.set(
    s.id,
    setTimeout(async () => {
      secTimers.delete(s.id);
      const ok = await saveAnswer(s.id + '--sections', JSON.stringify(secs.map((x) => ({ name: x.name, text: x.text }))));
      if (ok && s.verify) markVerified(s);
      secStatus(ok ? 'Saved.' : 'Didn’t save. ' + TYPE_AGAIN);
    }, wait),
  );
}
document.addEventListener('input', (e) => {
  const el = e.target.closest && e.target.closest('[data-sec-text],[data-sec-name]');
  if (!el) return;
  const s = current(),
    secs = draftOf(s);
  const x = secs[Number(el.dataset.secText ?? el.dataset.secName)];
  if (!x) return;
  touchDraft();
  const val = el.value.replace(/\r\n/g, '\n');
  if (el.dataset.secName != null) x.name = val;
  else x.text = val;
  queueSections(s);
});
function editSections(fn, focusLast) {
  const s = current();
  fn(draftOf(s));
  touchDraft();
  queueSections(s, 0);
  render();
  if (focusLast) [...document.querySelectorAll('.ans-sec-name')].pop()?.focus();
}
function sectionAction(a) {
  if (a === 'sec-add') editSections((secs) => secs.push({ name: '', text: '' }), true);
  if (a === 'sec-star')
    editSections((secs) => {
      for (const n of STAR_NAMES)
        if (!secs.some((x) => x.name.trim().toLowerCase() === n.toLowerCase())) secs.push({ name: n, text: '' });
    });
}
document.addEventListener('click', (e) => {
  const d = e.target.closest && e.target.closest('[data-sec-del]');
  if (!d) return;
  const s = current(),
    x = draftOf(s)[Number(d.dataset.secDel)];
  if (!x) return;
  if (x.text.trim() && !confirm(`Remove “${x.name || 'this section'}” and its text?`)) return;
  editSections((secs) => secs.splice(Number(d.dataset.secDel), 1));
});
function loadEdits() {
  STORE.edits(DECK_SLUG).then((rows) => {
    if (rows && applySavedEdits(rows)) render();
    updateEditUI();
  });
}

function updateEditUI() {
  const copy = $('#copy-edits-btn'),
    count = $('#edit-count');
  document.body.classList.toggle('edit-mode', state.editMode);
  if (count) count.textContent = editChanges.size ? `(${editChanges.size})` : '';
  if (copy) copy.classList.toggle('has-edits', editChanges.size > 0);
}

const lines = (t) =>
  String(t || '')
    .split('\n')
    .filter(Boolean);
const ORIGIN_LABEL = {
  standard: 'Standard',
  jd: 'From the JD',
  recruiter: 'From the recruiter',
  research: 'From research',
  risk: 'From the risk list',
};
// The master deck holds standard questions only, so the tag would say the same thing on every card.
const originTag = (s) =>
  s.origin && !DECK.evergreen
    ?`<span class="pill origin origin-${esc(s.origin)}">${esc(ORIGIN_LABEL[s.origin] || s.origin)}</span>`
    : '';
// Your own answer, read-only: each named section and its text.
// A company deck question that asks what a master question asks names it ("core": "<id>"). Until you
// write a company-specific answer, it shows your master answer, edited in the master deck.
function coreSections(id) {
  if (!id) return [];
  try {
    const a = JSON.parse(coreAnswers().get(id + '--sections') || 'null');
    if (Array.isArray(a)) return a.filter((x) => String(x.text || '').trim()).map((x) => ({ name: String(x.name || ''), text: String(x.text) }));
  } catch (e) {}
  const typed = String(coreAnswers().get(id) || '').trim();
  return typed ? [{ name: 'Answer', text: typed }] : [];
}
const fromCore = (s) => (!MASTER && s.core && !hasOwnAnswer(s) ? coreSections(s.core) : []);
// A linked question's own version for this interview, started from the master answer. From then on
// it's this deck's answer, edited here.
document.addEventListener('click', async (e) => {
  if (!e.target.closest || !e.target.closest('[data-fork-core]')) return;
  const s = current(),
    secs = fromCore(s);
  if (!secs.length) return;
  if (await saveAnswer(s.id + '--sections', JSON.stringify(secs.map((x) => ({ name: x.name, text: x.text }))))) render();
});
function ownAnswerHTML(s, secs = sectionsOf(s)) {
  return secs
    .filter((x) => String(x.text || '').trim())
    .map((x) => `<div class="own-part">${x.name ? `<small>${esc(x.name)}</small>` : ''}<div class="script">${textHTML(x.text)}</div></div>`)
    .join('');
}
function textHTML(text) {
  return String(text || '')
    .split(/\n\s*\n/)
    .map((p) => '<p' + (p.includes('[VERIFY') ? ' class="verify-inline"' : '') + '>' + esc(p) + '</p>')
    .join('');
}
function cueHTML(beats) {
  return (
    '<ol class="beats">' +
    beats.map((b, i) => `<li><span class="beat-n">${i + 1}</span><span>${esc(b)}</span></li>`).join('') +
    '</ol>'
  );
}
function concealed() {
  return `<div class="concealed slim"><p class="conceal-lead">Hidden. Say yours first, then reveal (<kbd>Space</kbd>).</p></div>`;
}
function timing() {
  return `<div class="text-size" aria-label="Script text size"><button data-size="-1" aria-label="Smaller script text">A−</button><button data-size="1" aria-label="Larger script text">A+</button></div>`;
}
function cardBody(body, label, tools = '') {
  return `<section class="response"><div class="response-header">${label ? `<span class="response-label">${esc(label)}</span>` : ''}${tools}${timing()}</div>${body}</section>`;
}
// Whether you've written your own answer to a deck question (sections, or the older typed answer).
function hasOwnAnswer(s) {
  if (String(ANSWERS.get(s.id) || '').trim()) return true;
  try {
    const a = JSON.parse(ANSWERS.get(s.id + '--sections') || 'null');
    return Array.isArray(a) && a.some((x) => String(x.text || '').trim());
  } catch (e) {
    return false;
  }
}
// Recall cues from your own answer: a section's first words each, or a one-section answer's first sentences.
function ownCues(s, all = sectionsOf(s)) {
  const secs = all.filter((x) => String(x.text || '').trim());
  const firsts = secs.length > 1 ? secs.map((x) => x.text) : String(secs[0]?.text || '').split(/(?<=[.!?])\s+/);
  return firsts
    .map((x) => String(x).trim())
    .filter(Boolean)
    .slice(0, 6)
    .map((x) => x.split(/\s+/).slice(0, 8).join(' '));
}
function cuesFor(s) {
  if (hasOwnAnswer(s)) return ownCues(s);
  return ownCues(s, fromCore(s));
}
// Why they're asking, and what the deck knows about the question: where it came from, when it
// applies, a confirmed detail, and anything to check before the interview.
function contextHTML(s) {
  return `<details class="context"><summary>Why they’re asking${s.verify ? ' · verification note' : ''}</summary><div class="context-grid"><div><b>Why they’re asking</b><p>${esc(s.why)}</p></div>${s.source ? `<div><b>Source</b><p>${esc(s.source)}</p></div>` : ''}${s.when ? `<div><b>Use when</b><p>${esc(s.when)}</p></div>` : ''}${s.note ? `<div><b>Confirmed detail</b><p>${esc(s.note)}</p></div>` : ''}${s.verify ? `<div><b>Verify</b><p>${esc(s.verify)}</p></div>` : ''}</div></details>`;
}
// The master answer's footer on a linked question: say whose words these are, and where to change them.
const coreFoot = (s) =>
  `<span class="sec-status">Your master answer.</span>${studyOpen(s) ? '<button class="quiet" data-fork-core>Write One for This Interview</button>' : ''}<a class="jd-link" href="${esc(coreLink(s.core))}" target="_blank" rel="noopener">Edit in the master deck ↗</a>`;
function renderQuestion(s) {
  const sec = sectionMap.get(s.section) || {};
  // The master deck's questions to ask have nothing to rehearse: the wording is the answer, with Lock In
  // once it's final.
  const askMaster = MASTER && sec.role === 'ask';
  const core = fromCore(s);
  let body;
  if (core.length && (studyOpen(s) || (layer() && mode() !== 2))) body = ownAnswerHTML(s, core);
  else if (askMaster) body = '';
  else if (studyOpen(s)) body = sectionsHTML(s);
  else if (!layer()) body = concealed();
  else if (!hasOwnAnswer(s) && !core.length) body = '<div class="empty-message">No answer yet. Write one in Study.</div>';
  else if (mode() === 2) body = cueHTML(cuesFor(s));
  else body = ownAnswerHTML(s);
  const eyebrow = sec.questionLabel || 'Interview question';
  const label = !askMaster && layer() && !studyOpen(s) && mode() === 2 && (hasOwnAnswer(s) || core.length) ? 'Recall Cues' : '';
  const foot = askMaster ? `<span class="sec-status"></span>${lockHTML(s)}` : core.length ? coreFoot(s) : studyOpen(s) ? secStatusHTML(s) : '';
  return `<div class="question-head"><div class="question-meta"><span class="eyebrow">${esc(eyebrow)} / ${esc(s.id)}</span>${originTag(s)}${sec.role === 'ask' && !MASTER ? `<button class="pill ask-pill${state.asked.has(s.id) ? ' on' : ''}" data-asked="${s.id}">${state.asked.has(s.id) ? '✓ Asked' : 'Mark Asked'}</button>` : ''}${s.verify ? '<span class="pill verify">VERIFY</span>' : ''}</div><h1${editAttrs(s, 'title')}>${esc(s.title)}</h1></div><div style="height:12px"></div>${cardBody(body, label, foot)}${askMaster || layer() || studyOpen(s) ? contextHTML(s) : ''}`;
}
function renderShortlist(s) {
  return `<section class="top10-intro">${s.eyebrow ? `<div class="eyebrow">${esc(s.eyebrow)}</div>` : ''}<h1 style="margin-top:16px">${esc(s.title)}</h1>${s.intro ? `<p class="intro">${esc(s.intro)}</p>` : ''}${s.pacing ? `<div class="pill">${esc(s.pacing)}</div>` : ''}</section><ol class="top10-list">${s.questions.map((q, i) => `<li class="top10-card"><div class="eyebrow">${esc(q.topic)}</div><h2${editAttrs(s, 'questions.' + i + '.title')}>${esc(q.title)}</h2></li>`).join('')}</ol>`;
}
// The first page of the master deck: what still needs work, from this browser's answers and practice.
function renderReadiness(s) {
  const head = `<section class="section-page cards-page"><div class="eyebrow">Before your next interview</div><h1>${esc(s.title)}</h1>${s.subtitle ? `<p>${esc(s.subtitle)}</p>` : ''}</section>`;
  // What's left in the master set: questions with no answer yet, and answers not locked in.
  const practice = CONTENT.filter((x) => x.kind === 'question');
  const written = (q) => {
    if (String(ANSWERS.get(q.id) || '').trim()) return true;
    try {
      const a = JSON.parse(ANSWERS.get(q.id + '--sections') || 'null');
      return Array.isArray(a) && a.some((x) => String(x.text || '').trim());
    } catch (e) {
      return false;
    }
  };
  const toWrite = practice.filter((q) => !written(q) && sectionMap.get(q.section)?.role !== 'ask'),
    toLock = practice.filter((q) => written(q) && !isLocked(q));
  const where = (q) => [sectionMap.get(q.section)?.title, q.code].filter(Boolean).join(' · ');
  const qList = (qs) =>
    `<div class="ready-list">${qs.map((q) => `<button data-go="${q.id}"><span>${esc(q.title)}</span><small>${esc(where(q))}</small></button>`).join('')}</div>`;
  const flagged = CONTENT.filter((x) => state.flags.has(x.id));
  const askQs = CONTENT.filter((x) => x.kind === 'question' && sectionMap.get(x.section)?.role === 'ask'),
    asked = askQs.filter((q) => state.asked.has(q.id)).length;
  const card = (title, n, body, foot = '') =>
    `<article class="comp-card ready-card"><h3>${esc(title)} <span class="ready-n">${n}</span></h3>${body}${foot ? `<div class="comp-foot">${foot}</div>` : ''}</article>`;
  const none = (t) => `<p class="comp-test">${esc(t)}</p>`;
  const cards = [
    card('To Write', toWrite.length, toWrite.length ? qList(toWrite) : none('Every question has an answer.')),
    card('To Lock In', toLock.length, toLock.length ? qList(toLock) : none('Every answer is locked in.')),
    card(
      'Flagged answers',
      flagged.length,
      flagged.length
        ? `<div class="comp-qs">${flagged.map((x) => `<button data-go="${x.id}">${esc(x.title)}</button>`).join('')}</div>`
        : none('Nothing flagged. Press F on an answer that comes out wrong.'),
      flagged.length ? '<button data-action="drill" class="primary">Drill These <kbd>D</kbd></button>' : '',
    ),
    !MASTER && askQs.length
      ? card(
          'Questions to Ask',
          `${asked} of ${askQs.length}`,
          none(
            asked
              ? 'Ticked off in your last conversation. Clear them before the next one.'
              : 'Nothing ticked off yet.',
          ),
          asked ? '<button data-clear-asked="1">Clear Ticks</button>' : '',
        )
      : '',
  ].join('');
  return head + `<div class="comp-grid">${cards}</div>`;
}
function renderCover() {
  const c = DECK.cover || {};
  return `<section class="hero">${c.eyebrow ? `<div class="eyebrow">${esc(c.eyebrow)}</div>` : ''}<div class="hero-top"><div><h1>${esc(c.title || '')}${c.titleAccent ? `<span>${esc(c.titleAccent)}</span>` : ''}</h1><p class="hero-description">${(c.description || []).map(esc).join('<br>')}</p><div class="hero-actions">${(c.actions || []).map((a) => `<button class="${a.primary ? 'primary' : ''}" data-go="${esc(a.go)}">${esc(a.label)}${a.primary ? ' <span aria-hidden="true">↗</span>' : ''}</button>`).join('')}</div></div></div><div class="hero-line"></div><div class="cover-guides">${(c.guides || []).map((g, i) => `<div class="mini"><b>${String(i + 1).padStart(2, '0')} / ${esc(g.title)}</b><p>${esc(g.body)}</p></div>`).join('')}</div>${c.risk ? `<div class="cover-gate"><b>${esc(c.risk.title)}</b><p class="tiny muted" style="margin:7px 0 0">${esc(c.risk.body)}</p></div>` : ''}</section>`;
}
// A deck's own section as cards: one per question, with why they ask it and the target length.
const TICK =
  '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const askCount = (qs) => {
  if (MASTER) return `${qs.length} question${qs.length > 1 ? 's' : ''}`;
  const n = qs.filter((q) => state.asked.has(q.id)).length;
  return n ? `${n} of ${qs.length} asked` : `${qs.length} question${qs.length > 1 ? 's' : ''}`;
};
const askedTotal = (qs) => {
  if (MASTER) return '';
  const n = qs.filter((q) => state.asked.has(q.id)).length;
  return n ? ` · ${n} asked <button class="ask-clear" data-clear-asked="1">Clear</button>` : '';
};
function toggleAsked(id, b) {
  state.asked.has(id) ? state.asked.delete(id) : state.asked.add(id);
  saveProgress();
  const row = b && b.closest('.ask-row');
  if (!row) {
    render();
    return;
  }
  const on = state.asked.has(id);
  const tick = row.querySelector('.ask-check');
  row.classList.toggle('asked', on);
  tick.setAttribute('aria-checked', on);
  tick.innerHTML = on ? TICK : '';
  tick.title = on ? 'Asked. Click to clear.' : 'Mark as Asked';
  const s = byId.get(state.id),
    qs = CONTENT.filter((x) => x.section === s.section && x.kind === 'question'),
    card = row.closest('.comp-card');
  card.querySelector('.ask-count').textContent = askCount(
    qs.filter((q) => q.theme === CONTENT.find((x) => x.id === id).theme),
  );
  document.querySelector('.asked-total').innerHTML = askedTotal(qs);
}
function renderThemeCards(s, qs) {
  const themes = (DECK.askThemes || [])
    .map((t) => ({ ...t, qs: qs.filter((q) => q.theme === t.id) }))
    .filter((t) => t.qs.length);
  const cards = themes
    .map((t) => {
      const flagged = t.qs.filter((q) => state.flags.has(q.id)).length;
      return `<article class="comp-card"><h3>${esc(t.title)}</h3><p class="comp-test">${esc(t.testing)}</p><div class="comp-qs">${t.qs
        .map((q) => {
          const on = !MASTER && state.asked.has(q.id);
          return `<button class="ask-row${on ? ' asked' : ''}${MASTER ? ' no-tick' : ''}" data-go="${q.id}">${MASTER ? '' : `<span class="ask-check" data-asked="${q.id}" role="checkbox" aria-checked="${on}" aria-label="Asked" title="${on ? 'Asked. Click to clear.' : 'Mark as Asked'}">${on ? TICK : ''}</span>`}${MASTER ? lockMark(q) : ''}<span class="ask-q">${q.origin && q.origin !== 'standard' ? originTag(q) + ' ' : ''}${esc(q.title)}${q.when ? `<span class="q-when">Use when: ${esc(q.when)}</span>` : ''}</span></button>`;
        })
        .join(
          '',
        )}</div><div class="comp-foot"><span class="ask-count">${askCount(t.qs)}</span>${flagged ? `<span class="comp-flag">${flagged} flagged</span>` : ''}<span class="comp-code">${esc(t.code)}</span></div></article>`;
    })
    .join('');
  return `<section class="section-page cards-page"><div class="eyebrow">${themes.length} themes · ${qs.length} questions<span class="asked-total">${askedTotal(qs)}</span></div><h1>${esc(s.title)}</h1>${s.subtitle ? `<p>${esc(s.subtitle)}</p>` : ''}</section><div class="comp-grid">${cards}</div>`;
}
function renderQuestionCards(s) {
  const qs = CONTENT.filter((x) => x.section === s.section && x.kind === 'question');
  if (sectionMap.get(s.section)?.role === 'ask' && qs.some((q) => q.theme)) return renderThemeCards(s, qs);
  return `<section class="section-page cards-page"><div class="eyebrow">${qs.length} questions</div><h1>${esc(s.title)}</h1>${s.subtitle ? `<p>${esc(s.subtitle)}</p>` : ''}</section><div class="comp-grid">${qs.map((q) => `<button class="resume-card q-card ${state.flags.has(q.id) ? 'flagged' : ''}" data-go="${q.id}"><span class="rc-top">${originTag(q) || '<span></span>'}<span class="rc-status">${q.target ? clock(q.target * 1000) : ''}</span></span><b>${lockMark(q)}${esc(q.title)}</b>${previewHTML(q)}${q.when ? `<span class="rc-when">Use when: ${esc(q.when)}</span>` : ''}<span class="rc-foot">${q.verify ? '<span class="rc-verify">Verify</span>' : ''}</span></button>`).join('')}</div>`;
}
function renderSection(s) {
  if (s.cards) return renderQuestionCards(s);
  const sec = sectionMap.get(s.section) || {};
  const items = CONTENT.filter(
    (x) => x.section === s.section && x.kind === 'question',
  );
  return `<section class="section-page"><div class="section-letter">${esc(s.section)}</div><div class="eyebrow">${items.length} ${esc(sec.noun || 'core questions')}</div><h1>${esc(s.title)}</h1>${s.subtitle ? `<p>${esc(s.subtitle)}</p>` : ''}<div class="section-list">${items.map((x) => `<button data-go="${x.id}"><span>${esc(x.title)}</span><small>${x.target ? x.target + ' sec' : 'Recall'} ↗</small></button>`).join('')}</div></section>`;
}
function renderHub(s) {
  const h = DECK.hub || {};
  return `<div class="eyebrow">${esc(h.eyebrow || 'Their priorities')}</div><h1 style="margin-top:16px">${esc(h.title || s.title)}</h1>${h.intro ? `<p class="intro">${esc(h.intro)}</p>` : ''}<div class="priority-grid">${(s.priorities || []).map((p) => `<article class="priority-card"><div class="eyebrow">${esc(p.id)}</div><h3>${esc(p.title)}</h3>${p.quote ? `<blockquote>“${esc(p.quote)}”</blockquote>` : ''}<p>${esc(p.detail)}</p><div class="links">${(p.answers || []).map((id) => `<button data-go="${esc(id)}">${esc(id)} ↗</button>`).join('')}</div></article>`).join('')}</div>${h.caption ? `<div class="visual-caption" style="margin-top:22px">${esc(h.caption)}</div>` : ''}`;
}
// The notes you take on the call: one open box at the top of Interview Notes, saved in this browser as
// the deck answer "<notes id>--own" (as you type, like an answer).
let ownNotesTimer = null;
document.addEventListener('input', (e) => {
  const el = e.target.closest && e.target.closest('[data-own-notes]');
  if (!el) return;
  const id = el.dataset.ownNotes, val = el.value.replace(/\r\n/g, '\n');
  autosize(el);
  clearTimeout(ownNotesTimer);
  ownNotesTimer = setTimeout(async () => {
    const ok = await saveAnswer(id + '--own', val);
    const st = document.getElementById('own-notes-status');
    if (st) st.textContent = ok ? 'Saved.' : 'Not saved. ' + TYPE_AGAIN;
  }, 600);
});
function ownNotesHTML(s) {
  return `<div class="own-notes"><div class="own-notes-head"><b>Your notes from the call</b><span class="sec-status" id="own-notes-status" role="status">Saves as you type, ${SAVED_WHERE}.</span></div><textarea data-own-notes="${esc(s.id)}" rows="4" spellcheck="true" aria-label="Your notes from the call" placeholder="Type or paste your notes from the conversation here.">${esc(ANSWERS.get(s.id + '--own') || '')}</textarea></div>`;
}
function renderNotes(s) {
  return `<div class="eyebrow">${esc(s.eyebrow || 'Preparation notes, not spoken copy')}</div><h1 style="margin-top:17px">${esc(s.title)}</h1>${s.intro ? `<p class="intro">${esc(s.intro)}</p>` : ''}${ownNotesHTML(s)}${(s.cards || []).map((c, ci) => `<div class="evidence-card"><h3>${esc(c.title)}</h3>${(c.paragraphs || []).map((p, pi) => `<p${p.startsWith('VERIFY') ? ' class="verify-inline"' : ''}${editAttrs(s, 'cards.' + ci + '.paragraphs.' + pi, true)}>${esc(p)}</p>`).join('')}${(c.bullets || []).length ? `<ul>${c.bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}</div>`).join('')}${(s.links || []).length ? `<div class="chain-links">${s.links.map((l) => `<button data-go="${esc(l.id)}">${esc(l.label || l.id)} ↗</button>`).join('')}</div>` : ''}`;
}
function render() {
  // Study is the edit mode: the deck's own text is click-to-edit there, and only there.
  state.editMode = studying();
  const s = current();
  const sec = sectionMap.get(s.section) || { title: '', color: DECK.theme?.accent || 'var(--signal)' };
  const ids = activeOrder();
  const i = ids.indexOf(s.id);
  {
    const tab = $('#top10-tab'),
      sl = CONTENT.find((x) => x.kind === 'shortlist');
    tab.classList.toggle('active', !!sl && s.id === sl.id);
    tab.setAttribute('aria-pressed', String(!!sl && s.id === sl.id));
  }
  // A section page's own heading names the section, and the recall mode only matters on a question in Test.
  const onQuestion = s.kind === 'question';
  $('#section-label').textContent = onQuestion ? sec.title : '';
  $('#counter').textContent = String(i + 1).padStart(2, '0') + ' / ' + ids.length;
  $('#mode-label').hidden = !onQuestion || studying();
  $('#mode-label').textContent =
    ['', 'Answer', 'Beats'][mode()] + (state.overrides.has(s.id) ? ' · this slide' : '');
  $('#run-label').hidden = !state.drill;
  $('#run-label').textContent = 'Flagged drill';
  $('#footer-mode').textContent = studying() ? 'Study' : 'Test · ' + ['', 'Answer', 'Beats'][state.globalMode];
  $('#side-flags').textContent =
    state.flags.size + ' slide' + (state.flags.size === 1 ? '' : 's') + ' flagged';
  $('#section-nav').innerHTML = sections
    .filter((x) => !x.hidden)
    .map(
      (x, j) =>
        `<button data-section="${x.id}" class="${x.id === s.section ? 'active' : ''}" ${x.id === s.section ? 'aria-current="page"' : ''}><span class="nav-num">${String(j + 1).padStart(2, '0')}</span>${esc(x.title)}</button>`,
    )
    .join('');
  document.querySelectorAll('[data-purpose]').forEach((b) => {
    const on = b.dataset.purpose === state.purpose;
    b.classList.toggle('active', on);
    b.setAttribute('aria-pressed', String(on));
  });
  {
    // Out of sight in Study, but it keeps its space so Study / Test never moves.
    const mg = $('.mode-group');
    mg.classList.toggle('is-off', studying());
    mg.inert = studying();
  }
  document.body.classList.toggle('studying', studying());
  document.querySelectorAll('[data-global]').forEach((b) => {
    const on = Number(b.dataset.global) === state.globalMode;
    b.classList.toggle('active', on);
    b.setAttribute('aria-pressed', String(on));
  });
  const content = {
    readiness: renderReadiness,
    shortlist: renderShortlist,
    cover: renderCover,
    section: renderSection,
    question: renderQuestion,
    hub: renderHub,
    notes: renderNotes,
  };
  $('#slide').innerHTML = content[s.kind](s) + practiceHTML(s);
  $('#slide').dataset.slideId = s.id;
  $('#slide').dataset.kind = s.kind;
  $('#slide').dataset.layer = layer();
  $('#flag-btn').setAttribute('aria-pressed', String(state.flags.has(s.id)));
  $('#flag-btn').innerHTML = (state.flags.has(s.id) ? 'Flagged' : 'Flag') + ' <kbd>F</kbd>';
  $('#drill-btn').setAttribute('aria-pressed', String(state.drill));
  {
    // Progress, one segment per section (the Value Sort pattern): sections behind you are full, the
    // current one fills as you go, and only the current one carries a caption ("03 / 06 · Opening · 2 of 7").
    const secs = sections.filter((x) => !x.hidden),
      all = ordered(),
      at = secs.findIndex((x) => x.id === s.section),
      pad = (n) => String(n).padStart(2, '0');
    $('#steps').innerHTML = secs
      .map((x, j) => {
        const here = all.filter((id) => byId.get(id)?.section === x.id),
          k = here.indexOf(s.id);
        const fill = j < at ? 100 : j > at ? 0 : here.length ? ((k + 1) / here.length) * 100 : 100;
        const cap =
          j === at
            ? `${pad(j + 1)} / ${pad(secs.length)} · ${x.title}${here.length > 1 && k >= 0 ? ` · ${k + 1} of ${here.length}` : ''}`
            : '';
        return `<li data-state="${j < at ? 'done' : j === at ? 'current' : 'todo'}"${j >= secs.length / 2 ? ' data-end' : ''}${j === at ? ' aria-current="step"' : ''}><span class="lbl"><span>${esc(cap)}</span></span><span class="bar" title="${esc(x.title)}"><i style="width:${fill}%"></i></span></li>`;
      })
      .join('');
  }
  const max = maxLayer(s);
  $('#reveal-btn').disabled = !!max && layer() >= max;
  $('#reveal-btn').innerHTML =
    (max
      ? layer() >= max
        ? 'Revealed'
        : 'Reveal'
      : 'Continue') + ' <kbd>Space</kbd>';
  {
    const practice = s.kind === 'question';
    document.querySelector('.footer .tools').hidden = !practice;
    $('#timer').hidden = !practice || studying();
  }
  // Only a state worth knowing; the controls themselves live in ? (help).
  $('#footer-hint').textContent = state.drill ? 'Drill: arrows cycle flagged slides. D exits.' : '';
  $('[data-action="prev"]').disabled = !state.drill && i === 0;
  $('[data-action="next"]').disabled = !state.drill && i === ids.length - 1;
  $('#timer-btn').disabled = !target();
  paintTimer();
  updateEditUI();
  saveProgress();
  hydrateTake(s);
  markTakes();
  markDeletes();
  markAdds();
  sizeAnswerBoxes();
}
function maxLayer(s) {
  return !studyOpen(s) && s.kind === 'question' ? 1 : 0;
}
function pauseTimer() {
  if (runningId) {
    state.timers.set(runningId, (state.timers.get(runningId) || 0) + (performance.now() - startedAt));
    runningId = null;
    saveProgress();
  }
}
// The slide id lives in the URL hash, and every slide is a place: a jump (a link, a card, the nav)
// and a step (arrows, swipe, Space, a move within a drill) each add a history entry, so Back walks
// back through the slides. The entry also records whether a drill was on, so Back and Forward restore
// it. First load, and a slide deleted in place, only rewrite the current entry. Settings
// (Study/Test, Script/Beats, flags) are not steps.
// Section pages get readable links (#opening-resume-and-technical); questions keep their ids. Old links still resolve.
const slugify = (x) =>
  String(x || '')
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
const PAGE_KINDS = ['section', 'readiness', 'cover'];
function hashOf(id) {
  const s = byId.get(id);
  if (s && PAGE_KINDS.includes(s.kind)) {
    const k = slugify((sectionMap.get(s.section) || {}).title || s.title);
    if (k) return k;
  }
  return id;
}
function slideFromHash() {
  let h = '';
  try {
    h = decodeURIComponent(location.hash.slice(1));
  } catch (e) {}
  if (!h || byId.has(h)) return h;
  const alias = (DECK.hashAliases || {})[h];
  if (alias) return alias;
  const hit = CONTENT.find((s) => PAGE_KINDS.includes(s.kind) && hashOf(s.id) === h);
  return hit ? hit.id : h;
}
function syncHash(how) {
  if (how === 'none') return;
  const url = '#' + encodeURIComponent(hashOf(state.id));
  if (location.hash === url && !!history.state?.drill === state.drill) return;
  try {
    history[how === 'push' ? 'pushState' : 'replaceState']({ drill: state.drill }, '', url);
  } catch (e) {}
}
// Where you were on each page, so Back returns there.
const scrollSpots = new Map();
function go(id, { fromLink = true, history: how } = {}) {
  if (!byId.has(id)) return;
  if (state.drill && !state.flags.has(id) && fromLink) {
    state.drill = false;
    toast('Left flagged drill to open this slide.');
  }
  if (rec) stopRecord();
  pauseTimer();
  const moved = id !== state.id;
  const main = document.querySelector('main');
  if (moved) scrollSpots.set(state.id, { y: window.scrollY, m: main?.scrollTop || 0 });
  state.id = id;
  state.layers.delete(id);
  syncHash(how || (moved ? 'push' : 'replace'));
  render();
  // Back (and Forward) returns to where you were on that page; anything else starts at the top.
  const spot = how === 'none' && scrollSpots.get(id);
  const put = () => {
    window.scrollTo({ top: spot ? spot.y : 0, behavior: 'instant' });
    const m = document.querySelector('main');
    if (m) m.scrollTop = spot ? spot.m : 0;
  };
  put();
  if (spot) requestAnimationFrame(put);
}
function move(delta) {
  const ids = activeOrder();
  const i = ids.indexOf(state.id);
  let next = i + delta;
  if (state.drill) next = (next + ids.length) % ids.length;
  if (next < 0 || next >= ids.length) return;
  go(ids[next], { fromLink: false, history: 'push' });
}
function reveal() {
  const max = maxLayer(current());
  if (!max) {
    move(1);
    return;
  }
  if (layer() < max) {
    state.layers.set(state.id, layer() + 1);
    render();
  }
}
function setGlobal(m) {
  state.globalMode = m;
  state.overrides.clear();
  state.layers.clear();
  render();
  toast(
    ['', 'Answer: reveal your full answer.', 'Beats: recall from the first words of each part.'][
      m
    ],
  );
}
function flag() {
  const id = state.id;
  const old = activeOrder(),
    idx = old.indexOf(id);
  if (state.flags.has(id)) state.flags.delete(id);
  else state.flags.add(id);
  if (state.drill && !state.flags.has(id)) {
    if (!state.flags.size) {
      state.drill = false;
      go(state.preDrill, { history: 'replace' });
      toast('No flagged slides remain. Drill ended.');
      return;
    }
    const next = old
      .slice(idx + 1)
      .concat(old.slice(0, idx))
      .find((x) => state.flags.has(x));
    go(next || activeOrder()[0], { fromLink: false, history: 'replace' });
    return;
  }
  render();
}
function drill() {
  if (state.drill) {
    state.drill = false;
    go(state.preDrill, { history: 'push' });
    toast('Returned to the full deck.');
    return;
  }
  if (!state.flags.size) {
    toast('Flag a slide with F, then start a drill.');
    return;
  }
  state.preDrill = state.id;
  state.drill = true;
  go(state.flags.has(state.id) ? state.id : activeOrder()[0], { fromLink: false, history: 'push' });
  toast('Drilling ' + state.flags.size + ' flagged slides.');
}

function clock(ms) {
  const total = Math.floor(ms / 1000);
  return Math.floor(total / 60) + ':' + String(total % 60).padStart(2, '0');
}
function paintTimer() {
  const ms = (state.timers.get(state.id) || 0) + (runningId === state.id ? performance.now() - startedAt : 0);
  const t = target();
  $('#time').textContent = clock(ms);
  $('#target-time').textContent = t ? '/ ' + clock(t * 1000) : '/ recall';
  {
    const recording = !!(rec && rec.id === state.id);
    $('#timer-btn .rec-icon').textContent = recording ? '■' : runningId === state.id ? 'Ⅱ' : '●';
    $('#timer-btn').classList.toggle('recording', recording);
    $('#timer-btn').setAttribute(
      'aria-label',
      recording ? 'Stop Recording' : runningId === state.id ? 'Pause Timer' : 'Record Your Answer',
    );
  }
  $('#timer').classList.toggle('near', t > 0 && ms >= t * 800 && ms < t * 1000);
  $('#timer').classList.toggle('over', t > 0 && ms >= t * 1000);
}
function toggleTimer() {
  if (!target()) return;
  if (runningId === state.id) pauseTimer();
  else {
    pauseTimer();
    runningId = state.id;
    startedAt = performance.now();
  }
  paintTimer();
}

function action(name) {
  if (name === 'sec-add' || name === 'sec-star') {
    sectionAction(name);
    return;
  }
  if (['take-delete', 'take-use'].includes(name)) {
    practiceAction(name);
    return;
  }
  switch (name) {
    case 'prev':
      move(-1);
      break;
    case 'next':
      move(1);
      break;
    case 'reveal':
      reveal();
      break;
    case 'flag':
      flag();
      break;
    case 'drill':
      drill();
      break;
    case 'timer':
      toggleRecord();
      break;
    case 'reset-timer':
      pauseTimer();
      state.timers.set(state.id, 0);
      paintTimer();
      break;
    case 'help':
      $('#help').showModal();
      break;
  }
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  if (b.dataset.close) {
    $('#' + b.dataset.close).close();
    return;
  }
  const tick = e.target.closest('.ask-check[data-asked]');
  if (tick) {
    toggleAsked(tick.dataset.asked, tick);
    return;
  }
  if (b.dataset.asked) {
    toggleAsked(b.dataset.asked, b.closest('.ask-row') ? b : null);
    return;
  }
  if (b.dataset.clearAsked) {
    state.asked.clear();
    saveProgress();
    render();
    return;
  }
  if (b.dataset.go) {
    document.querySelectorAll('dialog[open]').forEach((d) => d.close());
    go(b.dataset.go);
    return;
  }
  if (b.dataset.section) {
    go(CONTENT.find((x) => x.section === b.dataset.section).id);
    return;
  }
  if (b.dataset.purpose) {
    setPurpose(b.dataset.purpose);
    return;
  }
  if (b.dataset.global) {
    setGlobal(Number(b.dataset.global));
    return;
  }
  if (b.dataset.action) {
    action(b.dataset.action);
    return;
  }
  if (b.dataset.size) {
    const size = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--script-size')) || 18;
    const next = Math.min(32, Math.max(14, size + Number(b.dataset.size)));
    document.documentElement.style.setProperty('--script-size', next + 'px');
    try {
      localStorage.setItem('bishop-interviews:text-size', String(next));
    } catch (e) {}
  }
});
document.addEventListener('input', (e) => {
  const el = e.target.closest?.('[data-edit-id]');
  if (!el || !state.editMode) return;
  const obj = byId.get(el.dataset.editId),
    orig = originalById(el.dataset.editId);
  if (!obj || !orig) return;
  const field = el.dataset.editField,
    value = normalizeEdit(el),
    before = getPath(orig, field);
  setPath(obj, field, value);
  const key = el.dataset.editId + '::' + field;
  if (value === before) editChanges.delete(key);
  else editChanges.set(key, { id: el.dataset.editId, field, before, after: value });
  saveEdit(el.dataset.editId, field, before, value);
});
document.addEventListener('keydown', (e) => {
  const el = e.target.closest?.('[data-edit-id]');
  if (!el || !state.editMode) return;
  if (el.dataset.editMultiline !== '1' && e.key === 'Enter') {
    e.preventDefault();
    el.blur();
  }
});
document.addEventListener('paste', (e) => {
  const el = e.target.closest?.('[data-edit-id]');
  if (!el || !state.editMode) return;
  e.preventDefault();
  const plain = (e.clipboardData || window.clipboardData).getData('text/plain');
  document.execCommand('insertText', false, plain);
});

document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const open = document.querySelector('dialog[open]');
  if (open) {
    if (e.key === 'Escape' || (e.key === '?' && open.id === 'help')) {
      e.preventDefault();
      open.close();
    }
    return;
  }
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName) || e.target.isContentEditable) return;
  const key = e.key.toLowerCase();
  const keys = {
    arrowleft: 'prev',
    arrowright: 'next',
    ' ': 'reveal',
    f: 'flag',
    d: 'drill',
    t: 'timer',
    '?': 'help',
  };
  if (['1', '2'].includes(key)) {
    e.preventDefault();
    setGlobal(Number(key));
    return;
  }
  if (keys[key]) {
    e.preventDefault();
    action(keys[key]);
  }
});
// Back and Forward restore the slide and drill the entry names, without adding an entry. A slide
// that no longer resolves (deleted, or from an earlier visit) falls back to the cover, or the first
// slide; a slide the drill no longer holds (unflagged since) shows in the full deck.
window.addEventListener('popstate', (e) => {
  document.querySelectorAll('dialog[open]').forEach((d) => d.close());
  let id = slideFromHash();
  const lost = !byId.has(id);
  if (lost) id = byId.has('cover') ? 'cover' : CONTENT[0].id;
  const drillOn = !!e.state?.drill && state.flags.has(id);
  if (id === state.id && drillOn === state.drill && !lost) return;
  state.drill = drillOn;
  // A lost slide rewrites the entry to the cover's address; nothing here adds an entry.
  go(id, { fromLink: false, history: lost ? 'replace' : 'none' });
});
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    pauseTimer();
    paintTimer();
  }
});
setInterval(paintTimer, 200);
function applyDeckChrome() {
  document.title = BRAND + ' · ' + (DECK.title || 'Interview study deck');
  // A company deck wears the company's brand color as its accent (META.deck.theme.accent), inside Bishop's
  // navy and orange frame. The master deck keeps Bishop orange. Text on a filled button turns dark when
  // the brand color is light.
  if (!DECK.evergreen && /^#[0-9a-f]{6}$/i.test(DECK.theme?.accent || '')) {
    const hex = DECK.theme.accent;
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    const light = 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.3;
    const root = document.documentElement;
    root.style.setProperty('--brand', hex);
    root.style.setProperty('--brand-ink', light ? '#111316' : '#ffffff');
    root.classList.add('branded');
  }
  if ($('#brand-title')) $('#brand-title').textContent = BRAND;
  if ($('#brand-sub')) $('#brand-sub').textContent = DECK.brandTitle || DECK.title || '';
  if ($('#side-meta'))
    $('#side-meta').innerHTML =
      (DECK.sidebar || []).map((l) => esc(l)).join('<br>') + ((DECK.sidebar || []).length ? '<br><br>' : '');
  const tab = $('#top10-tab'),
    sl = CONTENT.find((x) => x.kind === 'shortlist');
  if (sl) {
    tab.hidden = false;
    tab.dataset.go = sl.id;
    tab.textContent = DECK.shortlistTab || 'Shortlist';
  }
  const jd = DECK.jd || {};
  if (jd.href) {
    const a = $('#jd-link');
    a.href = jd.href;
    a.hidden = false;
    if (jd.label) a.firstChild.textContent = jd.label + ' ';
    if (jd.title) a.title = jd.title;
  } else if (jd.none) {
    $('#jd-none').textContent = jd.none;
    $('#jd-none').hidden = false;
  }
  // An archived deck says so in the top bar; it's kept for reference and no longer updated.
  if (DECK.archived) {
    $('#jd-none').textContent = 'Archived';
    $('#jd-none').hidden = false;
  }
}
// Swipe left or right on a phone to move between slides.
let touchStart = null;
document.addEventListener(
  'touchstart',
  (e) => {
    if (e.touches.length !== 1 || e.target.closest('[contenteditable="true"],input,textarea,select,dialog'))
      return;
    touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY, t: Date.now() };
  },
  { passive: true },
);
document.addEventListener(
  'touchend',
  (e) => {
    if (!touchStart) return;
    const dx = e.changedTouches[0].clientX - touchStart.x,
      dy = e.changedTouches[0].clientY - touchStart.y,
      quick = Date.now() - touchStart.t < 600;
    touchStart = null;
    if (quick && Math.abs(dx) > 70 && Math.abs(dy) < 45) move(dx < 0 ? 1 : -1);
  },
  { passive: true },
);
applyDeckChrome();
try {
  const z = parseInt(localStorage.getItem('bishop-interviews:text-size'));
  if (z >= 14 && z <= 32) document.documentElement.style.setProperty('--script-size', z + 'px');
} catch (e) {}
const autosize = (el) => {
  el.style.height = 'auto';
  el.style.height = el.scrollHeight + 2 + 'px';
};
function sizeAnswerBoxes() {
  document.querySelectorAll('.response textarea').forEach(autosize);
}
document.addEventListener('input', (e) => {
  if (e.target.matches && e.target.matches('.response textarea')) autosize(e.target);
});
window.addEventListener('resize', () => sizeAnswerBoxes());
loadEdits();
loadAnswers();
loadTakeIds();
loadProgress();
{
  const h = slideFromHash();
  if (h && byId.has(h)) state.id = h;
  // A deck with no cover slide (or a saved place that's gone) starts on its first slide.
  if (!byId.has(state.id)) state.id = CONTENT[0].id;
}
// A fresh open with no slide in the address returns to where the candidate left off.
if (state.id === 'cover' && !slideFromHash() && state.lastId && byId.has(state.lastId)) state.id = state.lastId;
syncHash('replace');
render();
updateEditUI();
// Everything lives in this browser: Export saves it all as one file, Import loads one (from another
// browser, or a backup) in its place.
$('.side-bottom').insertAdjacentHTML(
  'afterbegin',
  '<div class="local-store"><button id="local-export" class="quiet">Export Answers</button><button id="local-import" class="quiet">Import Answers</button><input type="file" id="local-import-file" accept="application/json,.json" hidden></div>',
);
$('#local-export').addEventListener('click', () => STORE.exportFile());
$('#local-import').addEventListener('click', () => $('#local-import-file').click());
$('#local-import-file').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (!confirm('Replace everything saved in this browser with ' + file.name + '?')) return;
  try {
    await STORE.importFile(file);
    location.reload();
  } catch (err) {
    toast('That file isn’t a saved answers file from these decks.');
  }
});
