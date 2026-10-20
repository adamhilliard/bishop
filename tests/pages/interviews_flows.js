// Flow checks for the interviews deck, run inside a built deck page by tests/run_all.py (headless
// Chrome or Edge). Each check drives the page the way a candidate would and records pass or fail; the
// results land in <pre id="test-results"> as JSON, which the runner reads back.
// window.__expect (set by the runner): { name: the search name the top bar should show }.
(async () => {
  const results = [];
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const $1 = (s) => document.querySelector(s);
  const $all = (s) => [...document.querySelectorAll(s)];
  const type = (el, value) => {
    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  };
  const saved = () => JSON.parse(localStorage.getItem('bishop-interviews:answers') || '{"answers":[],"edits":[]}');
  async function check(name, fn) {
    try {
      const detail = await fn();
      results.push({ name, ok: true, detail: detail ?? '' });
    } catch (e) {
      results.push({ name, ok: false, detail: String((e && e.message) || e) });
    }
  }
  const assert = (cond, msg) => {
    if (!cond) throw new Error(msg);
  };
  window.confirm = () => true;
  await wait(300);
  const expect = window.__expect || {};

  // ---- Both decks ----
  await check('loads without script errors', () => {
    assert(!(window.__errors || []).length, 'errors: ' + (window.__errors || []).join(' | '));
  });
  await check('Bishop frame: robot, search name, favicon', () => {
    assert($1('.topbar .brandmark svg'), 'no robot in the top bar');
    assert($1('#brand-title').textContent === expect.name, `top bar says "${$1('#brand-title').textContent}", expected "${expect.name}"`);
    assert(($1('link[rel=icon]').getAttribute('href') || '').startsWith('data:image/svg+xml'), 'favicon is not the inline robot');
    const bg = getComputedStyle($1('.topbar')).backgroundColor;
    assert(bg === 'rgb(26, 41, 68)', 'top bar is ' + bg + ', not Bishop navy');
  });
  await check('no outside requests', () => {
    const ext = $all('link[href^="http"], script[src^="http"], img[src^="http"]');
    assert(!ext.length, ext.length + ' outside requests');
  });
  await check('progress is kept per deck', () => {
    assert(PROGRESS_KEY === 'bishop-interviews:progress:' + DECK_SLUG, 'progress key ' + PROGRESS_KEY);
  });
  await check('text size buttons work and are remembered', async () => {
    const before = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--script-size')) || 18;
    go(CONTENT.find((x) => x.kind === 'question').id);
    await wait(50);
    $1('[data-size="1"]').click();
    const after = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--script-size'));
    assert(after === before + 1, `size ${before} -> ${after}`);
    assert(localStorage.getItem('bishop-interviews:text-size') === String(after), 'size not saved');
  });

  if (MASTER) {
    // ---- The master deck ----
    await check('Study: an answer saves as you type', async () => {
      setPurpose('study');
      go('QA2');
      await wait(100);
      type($1('[data-sec-text="0"]'), 'I want a bigger operating role. My last team doubled. I want the whole service line.');
      await wait(1200);
      assert($1('#sec-status').textContent === 'Saved.', 'status: ' + $1('#sec-status').textContent);
      assert(saved().answers.some((a) => a.slide_id === 'QA2--sections' && a.text.includes('bigger operating role')), 'not in this browser');
    });
    await check('+ Add STAR adds the four parts', async () => {
      $1('[data-action="sec-star"]').click();
      await wait(50);
      const names = $all('.ans-sec-name').map((x) => x.value);
      assert(['Situation', 'Task', 'Action', 'Result'].every((n) => names.includes(n)), 'sections: ' + names.join(', '));
    });
    await check('Lock In locks the answer', async () => {
      $1('[data-lock]').click();
      await wait(100);
      assert(ANSWERS.get('QA2--locked') === '1', 'not locked');
      assert($1('[data-sec-text="0"]').readOnly, 'still editable');
    });
    await check('Readiness counts what is left', async () => {
      go('cover');
      await wait(50);
      const text = $1('#slide').innerText;
      assert(/To Write\s*4/.test(text), 'To Write: ' + (text.match(/To Write\s*\d+/) || ['?'])[0]);
      assert(/To Lock In\s*0/.test(text), 'To Lock In: ' + (text.match(/To Lock In\s*\d+/) || ['?'])[0]);
    });
    await check('Test: hidden first, then your answer', async () => {
      setPurpose('test');
      setGlobal(1);
      go('QA2');
      await wait(50);
      assert($1('#slide .concealed'), 'answer showed before reveal');
      document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
      await wait(50);
      assert(($1('#slide .own-part') || {}).innerText?.includes('bigger operating role'), 'reveal did not show the answer');
    });
    await check('Beats shows the first words of each part', async () => {
      setGlobal(2);
      reveal();
      await wait(50);
      const cues = $all('#slide .beats li');
      assert(cues.length >= 1, 'no cues');
      setGlobal(1);
    });
    await check('A question with no answer says so in Test', async () => {
      go('QE1');
      reveal();
      await wait(50);
      assert(($1('#slide .empty-message') || {}).textContent?.includes('No answer yet'), 'no empty message');
    });
    await check('Flags and the drill loop only flagged questions', async () => {
      go('QA2');
      flag();
      go('QR1');
      flag();
      drill();
      await wait(50);
      const order = activeOrder();
      assert(order.length === 2 && order.includes('QA2') && order.includes('QR1'), 'drill order: ' + order.join(','));
      drill();
      state.flags.clear();
      saveProgress();
    });
    await check('+ Add Question adds to a Questions to Ask theme', async () => {
      setPurpose('study');
      go('SF');
      await wait(50);
      const btn = $1('[data-add-q^="theme:"]');
      assert(btn, 'no add button on the theme cards');
      btn.click();
      await wait(20);
      const input = $1('.q-add-input');
      input.value = 'Who would I work with most?';
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      await wait(150);
      const added = CONTENT.find((x) => x.title === 'Who would I work with most?');
      assert(added && added.theme, 'question not added with its theme');
      assert(saved().edits.some((e) => e.field === '__added'), 'add not saved');
      window.__addedId = added.id;
    });
    await check('Delete removes a question', async () => {
      await deleteQuestion(window.__addedId);
      await wait(50);
      assert(!byId.has(window.__addedId), 'still there');
      assert(saved().edits.some((e) => e.field === '__deleted' && e.slide_id === window.__addedId), 'delete not saved');
    });
    await check('Export writes a sound answers file that reads back', () => {
      const raw = saved();
      const file = ANSWERS_FILE.toFile(raw);
      assert(file.format === 'bishop.interviews.answers' && file.version === 1, 'format ' + file.format);
      assert(!ANSWERS_FILE.checkFile(file).length, ANSWERS_FILE.checkFile(file).join('; '));
      const back = ANSWERS_FILE.fromFile(file);
      assert(back.answers.length === raw.answers.length, `answers ${raw.answers.length} -> ${back.answers.length}`);
    });
  } else {
    // ---- A company deck ----
    await check('Company color is the accent', () => {
      const brand = getComputedStyle(document.documentElement).getPropertyValue('--brand').trim();
      assert(brand.toLowerCase() === (DECK.theme?.accent || '').toLowerCase(), 'accent ' + brand);
    });
    await check('Cover: no numbers row or glyph; top risk shown', () => {
      go('cover');
      assert(!$1('#slide .stats') && !$1('#slide .compass'), 'stats or glyph still on the cover');
      assert($1('#slide').innerText.includes('Highest-risk question'), 'no top risk');
    });
    await check('Rounds: interview line and Questions for <name>', () => {
      assert($1('#side-meta').innerText.includes('Recruiter screen · Mon, Mar 4, 2030'), 'sidebar: ' + $1('#side-meta').innerText);
      assert($all('#section-nav button').some((b) => b.innerText.includes('Questions for Priya')), 'ask section not named for the round');
      assert($1('#side-meta').innerText.includes('Priya Shah, Recruiter'), "the round's interviewer isn't in the sidebar");
      go('cover');
      assert($1('#slide .hero-description').innerText.includes('Recruiter screen'), "the cover doesn't name the round");
      assert(!byId.has('QF21'), 'a hiring-manager-only question is in the screen round');
    });
    await check('A linked question shows the master answer', async () => {
      setPurpose('study');
      go('QA1');
      await wait(50);
      assert($1('#slide').innerText.includes('forty technicians'), 'master answer not shown');
      assert(($1('#slide a.jd-link') || {}).getAttribute?.('href')?.endsWith('core.html#QA1'), 'edit link wrong');
      assert(isLocked(byId.get('QA1')), "master lock not carried");
    });
    await check('Write One for This Interview starts from the master answer', async () => {
      $1('[data-fork-core]').click();
      await wait(100);
      assert(hasOwnAnswer(byId.get('QA1')), 'no company answer saved');
      assert(saved().answers.some((a) => a.deck === 'hooli' && a.slide_id === 'QA1--sections'), 'not saved under this deck');
    });
    await check('Writing an answer clears its verify note', async () => {
      go('QB1');
      await wait(50);
      assert($1('#slide .study-verify'), 'no verify line before');
      type($1('[data-sec-text="0"]'), 'Region two launched with nine techs; I hired the leads first.');
      await wait(1200);
      assert(!byId.get('QB1').verify, 'verify note still set');
    });
    await check('Mark Asked ticks and clears', async () => {
      toggleAsked('QF20');
      assert(state.asked.has('QF20'), 'not ticked');
      toggleAsked('QF20');
      assert(!state.asked.has('QF20'), 'not cleared');
    });
    await check('Notes from the call save', async () => {
      go('notes');
      await wait(50);
      const box = $1('[data-own-notes]');
      assert(box, 'no notes box');
      type(box, 'Priya said the second round is with Jordan next week.');
      await wait(900);
      assert(ANSWERS.get('notes--own')?.includes('Jordan'), 'notes not saved');
    });
    await check('Hub links each priority to its question', () => {
      go('hub');
      assert($all('#slide .priority-card [data-go="QB1"]').length === 1, 'no link to QB1');
    });
    await check('Import replaces what this browser holds', async () => {
      const file = ANSWERS_FILE.toFile({ answers: [{ deck: 'hooli', slide_id: 'QA20', text: 'Imported answer.' }], edits: [] });
      await STORE.importFile(new File([JSON.stringify(file)], 'Master_Answers.json', { type: 'application/json' }));
      assert(saved().answers.some((a) => a.slide_id === 'QA20' && a.text === 'Imported answer.'), 'import not saved');
    });
  }

  const pre = document.createElement('pre');
  pre.id = 'test-results';
  pre.textContent = JSON.stringify(results);
  document.body.appendChild(pre);
  document.title = 'TESTS-DONE';
})();
