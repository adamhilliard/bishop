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
  const questions = () => ordered().filter((id) => byId.get(id)?.kind === 'question');
  // Nothing the candidate reads says "master": the page, its title, the top bar, labels and tips.
  const noMaster = (where) => {
    const texts = [document.title, $1('#brand-sub').textContent, $1('#slide').innerText, $1('#help').textContent];
    for (const el of $all('[aria-label], [title]')) texts.push(el.getAttribute('aria-label') || '', el.getAttribute('title') || '');
    const hit = texts.find((t) => /master/i.test(t));
    assert(!hit, where + ' says "master": ' + String(hit).slice(0, 120));
  };
  // A stand-in recorder, so a take records without a microphone; counts whether speech recognition starts.
  async function fakeTake() {
    const real = { md: Object.getOwnPropertyDescriptor(Navigator.prototype, 'mediaDevices'), MR: window.MediaRecorder, speech: startSpeech };
    let speechStarts = 0;
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia: async () => ({ getTracks: () => [] }) } });
    window.MediaRecorder = class {
      static isTypeSupported() {
        return true;
      }
      constructor() {
        this.mimeType = 'audio/webm';
      }
      start() {
        this.ondataavailable && this.ondataavailable({ data: new Blob(['take'], { type: 'audio/webm' }) });
      }
      stop() {
        this.onstop && this.onstop();
      }
    };
    startSpeech = () => speechStarts++;
    await toggleRecord();
    const live = !!rec,
      liveTranscript = !!$1('#live-transcript');
    stopRecord();
    await wait(200);
    delete navigator.mediaDevices;
    if (real.md) Object.defineProperty(Navigator.prototype, 'mediaDevices', real.md);
    window.MediaRecorder = real.MR;
    startSpeech = real.speech;
    return { live, liveTranscript, speechStarts };
  }
  // A stand-in for the browser's speech recognition: it hears one phrase.
  class FakeSpeech {
    start() {
      setTimeout(() => this.onresult && this.onresult({ resultIndex: 0, results: [Object.assign([{ transcript: 'spoken from the mic' }], { isFinal: true })] }), 10);
    }
    stop() {
      this.onend && this.onend();
    }
  }
  const withSpeech = async (fn) => {
    const real = window.SpeechRecognition;
    window.SpeechRecognition = FakeSpeech;
    try {
      return await fn();
    } finally {
      window.SpeechRecognition = real;
    }
  };
  async function printAllCheck(answerText, extra) {
    let printed = 0;
    const realPrint = window.print;
    window.print = () => printed++;
    location.hash = '#print-all';
    await wait(400);
    try {
      assert(printing(), 'the print view did not open');
      const shown = $all('#print-all .pa-q').map((x) => x.dataset.printQ);
      assert(JSON.stringify(shown) === JSON.stringify(questions()), 'questions: ' + shown.join(',') + ' / deck: ' + questions().join(','));
      assert($1('#print-all').innerText.includes(answerText), 'no saved answer on the page');
      assert(printed === 1, 'print was called ' + printed + ' times');
      assert(getComputedStyle($1('.layout')).display === 'none', 'the deck still shows under the print view');
      if (extra) extra();
    } finally {
      $1('[data-print-close]').click();
      await wait(50);
      window.print = realPrint;
    }
    assert(!printing() && location.hash !== '#print-all', 'Close did not return to the deck');
    assert(!$all('a[href*="print-all"], [data-go="print-all"]').length, 'something on the page links to the print view');
  }

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
  await check('No Export or Import: answers live only in this browser', () => {
    assert(!$1('#local-export') && !$1('#local-import') && !$1('#master-data'), 'export, import or an embedded answers file is still on the page');
    assert(!/Export Answers|Import Answers/.test(document.body.innerText), 'the buttons still show');
    assert(typeof STORE.exportFile === 'undefined' && typeof STORE.importFile === 'undefined', 'STORE still exports or imports');
    assert(typeof ANSWERS_FILE === 'undefined', 'the answers-file code still ships');
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
    // ---- The core deck ----
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
    await check('Core labels: the deck says core, never master', async () => {
      assert($1('#brand-sub').textContent === 'Core deck', 'top bar: ' + $1('#brand-sub').textContent);
      assert(document.title.endsWith('Core Deck'), 'title: ' + document.title);
      setPurpose('study');
      for (const id of ordered()) {
        go(id);
        noMaster(id);
      }
      go('cover');
      assert($1('#slide h1').textContent === 'Your core deck', 'readiness: ' + $1('#slide h1').textContent);
    });
    await check('Recording: no setting means a take with a transcript', async () => {
      assert(DECK.record === undefined && recordMode() === 'transcript', 'record ' + DECK.record + ' -> ' + recordMode());
      setPurpose('test');
      assert($1('#toast').textContent === 'Test: say it or type it first, then reveal. ● records with a transcript.', 'toast: ' + $1('#toast').textContent);
      go('QR1');
      await wait(50);
      assert($1('#timer-btn').getAttribute('aria-label') === 'Record Your Answer' && $1('#timer-btn .rec-icon').textContent === '●', 'no record button');
      const t = await fakeTake();
      assert(t.live && t.speechStarts === 1 && t.liveTranscript, `recording ${t.live}, speech started ${t.speechStarts}, live transcript ${t.liveTranscript}`);
      // A saved take (IndexedDB, which a headless browser on a file page doesn't open) shows its transcript.
      const take = takeHTML({ transcript: 'I cut fix time by restaging parts.', seconds: 40, at: new Date().toISOString() }, 'blob:take');
      assert(take.includes('<audio') && take.includes('<details>') && take.includes('Transcript (7 words)'), 'the take has no transcript');
    });
    await check('Test: type it from memory, then compare on reveal', async () => {
      setPurpose('test');
      setGlobal(1);
      go('QA2');
      await wait(50);
      const box = $1('#recall-box');
      assert(box && $1('label[for="recall-box"]').textContent === 'Type it from memory', 'no Type it from memory box');
      assert(box.closest('.response') && getComputedStyle(box).resize === 'none', 'the box is not styled like the answer boxes');
      type(box, 'I want to run a whole service line from memory.');
      go('QA1');
      go('QA2');
      await wait(50);
      assert($1('#recall-box').value.includes('from memory'), 'the attempt did not stay with the slide');
      reveal();
      await wait(50);
      const attempt = $1('#slide .attempt'),
        answer = $1('#slide .own-part');
      assert(attempt && attempt.innerText.includes('from memory'), 'what was typed is not shown after the reveal');
      assert(answer && attempt.compareDocumentPosition(answer) & Node.DOCUMENT_POSITION_FOLLOWING, 'the attempt is not above the saved answer');
      assert(!$1('#recall-box'), 'the box still shows after the reveal');
      assert(!JSON.stringify(localStorage).includes('from memory'), 'the attempt was saved');
    });
    await check('Study: Speak shows only with a transcript and speech recognition', async () => {
      setPurpose('study');
      go('QR1');
      await wait(50);
      assert(!!$1('[data-dictate]') === !!SPEECH(), `Speak button ${!!$1('[data-dictate]')}, speech recognition ${!!SPEECH()}`);
      await withSpeech(async () => {
        render();
        const boxes = $all('#slide [data-sec-text]').length;
        assert(boxes && $all('#slide [data-dictate]').length === boxes, 'one Speak button per answer box');
      });
    });
    await check('Study: Speak adds what you say and saves it', async () => {
      await withSpeech(async () => {
        render();
        type($1('[data-sec-text="0"]'), 'I rebuilt parts staging.');
        $1('[data-dictate="0"]').click();
        await wait(60);
        const box = $1('[data-sec-text="0"]');
        assert(box.value === 'I rebuilt parts staging. spoken from the mic', 'box: ' + box.value);
        assert($1('[data-dictate="0"]').getAttribute('aria-pressed') === 'true', 'button does not show it is listening');
        await wait(1200);
        assert(saved().answers.some((a) => a.slide_id === 'QR1--sections' && a.text.includes('spoken from the mic')), 'not saved');
        $1('[data-dictate="0"]').click();
        assert(!dict, 'Stop did not stop');
      });
    });
    await check('#print-all lists every question with its answer, then prints', async () => {
      await printAllCheck('bigger operating role');
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
    await check('A linked question shows the core answer, read from this browser', async () => {
      setPurpose('study');
      go('QA1');
      await wait(50);
      assert($1('#slide').innerText.includes('forty technicians'), 'core answer not shown');
      assert(($1('#slide a.jd-link') || {}).getAttribute?.('href')?.endsWith('core.html#QA1'), 'edit link wrong');
      assert(isLocked(byId.get('QA1')), 'core lock not carried');
      assert($1('#slide').innerText.includes('Your core answer.'), 'not labeled as the core answer');
      assert($1('#slide a.jd-link').textContent === 'Edit in the core deck ↗', 'link: ' + $1('#slide a.jd-link').textContent);
    });
    await check('Core labels: the deck says core, never master', async () => {
      setPurpose('study');
      for (const id of ordered()) {
        go(id);
        noMaster(id);
      }
      setPurpose('test');
      go('QA1');
      reveal();
      noMaster('QA1 revealed');
      setPurpose('study');
    });
    await check('"From the job description" tags a question from the posting', () => {
      go('SE');
      const tag = $1('#slide .pill.origin-jd');
      assert(tag && tag.textContent === 'From the job description', 'tag: ' + (tag && tag.textContent));
    });
    await check('Write One for This Interview starts from the core answer', async () => {
      setPurpose('study');
      go('QA1');
      await wait(50);
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
    await check('Recording audio: a take plays back, with no transcript anywhere', async () => {
      assert(recordMode() === 'audio', 'record ' + DECK.record);
      setPurpose('test');
      assert($1('#toast').textContent === 'Test: say it or type it first, then reveal. ● records you.', 'toast: ' + $1('#toast').textContent);
      assert(!/transcript/i.test($1('#help').textContent), 'the controls panel mentions a transcript');
      go('QA20');
      await wait(50);
      assert($1('#timer-btn').getAttribute('aria-label') === 'Record Your Answer', 'no record button');
      const t = await fakeTake();
      assert(t.live && t.speechStarts === 0 && !t.liveTranscript, `recording ${t.live}, speech started ${t.speechStarts}, live transcript ${t.liveTranscript}`);
      assert(!/transcript/i.test($1('#slide').innerText), 'a transcript area shows on the slide');
      // A saved take (IndexedDB, which a headless browser on a file page doesn't open) plays back, and
      // shows no transcript even when one was saved before the setting changed.
      const take = takeHTML({ transcript: 'Words from an older take.', seconds: 40, at: new Date().toISOString() }, 'blob:take');
      assert(take.includes('<audio'), 'the take does not play back');
      assert(!/transcript|<details/i.test(take), 'the take shows a transcript area');
    });
    await check('Recording audio: no Speak button in Study', async () => {
      await withSpeech(async () => {
        setPurpose('study');
        go('QA20');
        await wait(50);
        assert($1('#slide [data-sec-text]') && !$1('[data-dictate]'), 'a Speak button shows');
      });
    });
    await check('Recording off: no record button, no timer, and nothing about recording', async () => {
      DECK.record = 'off';
      applyDeckChrome();
      try {
        setPurpose('test');
        assert($1('#toast').textContent === 'Test: say it or type it first, then reveal.', 'toast: ' + $1('#toast').textContent);
        go('QA20');
        await wait(100);
        assert($1('#timer').hidden, 'the timer still shows');
        assert(!$1('#take-slot') && !$1('#slide .practice'), 'the take area still shows');
        assert(!/record/i.test($1('#help').textContent), 'the controls panel mentions recording');
        assert(!$all('[aria-label], [title]').some((el) => /record/i.test((el.getAttribute('aria-label') || '') + (el.getAttribute('title') || ''))), 'a label mentions recording');
        assert($1('#help-record-key').hidden, 'the controls panel still lists T');
        await toggleRecord();
        assert(!rec && runningId !== 'QA20', 'T started something');
        await withSpeech(async () => {
          setPurpose('study');
          await wait(50);
          assert(!$1('[data-dictate]'), 'a Speak button shows');
        });
      } finally {
        DECK.record = 'audio';
        applyDeckChrome();
      }
    });
    await check('#print-all shows the core answer where the deck has none of its own', async () => {
      await printAllCheck('I hold on to work too long', () => {
        const qe1 = $1('#print-all [data-print-q="QE1"]');
        assert(qe1.textContent.includes('Your core answer'), 'QE1 is not labeled as the core answer');
        const qa1 = $1('#print-all [data-print-q="QA1"]');
        assert(!qa1.textContent.includes('Your core answer'), 'QA1 has its own answer, but shows the core one');
        assert($1('#print-all [data-print-q="QE20"] .pa-empty'), 'an unanswered question does not say so');
      });
    });
  }

  const pre = document.createElement('pre');
  pre.id = 'test-results';
  pre.textContent = JSON.stringify(results);
  document.body.appendChild(pre);
  document.title = 'TESTS-DONE';
})();
