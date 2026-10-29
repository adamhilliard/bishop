// Flow checks for the outreach board, run inside the test candidate's built page by tests/run_all.py
// (headless Chrome or Edge, a fresh browser profile). Each check drives the page the way a user would
// and records pass or fail; the results land in <pre id="test-results"> as JSON, which the runner reads.
// window.__expect (set by the runner): { name: the name the top bar should show }.
// window.__export (set by the runner): the made-up export in tests/outreach/export: { connections,
// messages, zip (base64), zipName }.
(async () => {
  const results = [];
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const $1 = (s) => document.querySelector(s);
  const $all = (s) => [...document.querySelectorAll(s)];
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
  const same = (got, want, what) => assert(JSON.stringify(got) === JSON.stringify(want), what + ': got ' + JSON.stringify(got) + ', want ' + JSON.stringify(want));
  window.confirm = () => true;
  const expect = window.__expect || {};
  const X = window.__export || {};
  const EXPORT_DAY = Date.UTC(2026, 9, 12, 12);
  const csvFile = (text, name) => new File([text], name, { type: 'text/csv', lastModified: EXPORT_DAY });
  const zipFile = () => {
    const bin = atob(X.zip);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new File([bytes], X.zipName, { type: 'application/zip', lastModified: Date.UTC(2026, 9, 20, 12) });
  };
  // Hand files to the page's own file input, the way choosing them in the file picker does.
  async function pick(files) {
    const input = $1('#uplFile');
    assert(input, 'no file input on the page');
    const dt = new DataTransfer();
    files.forEach((f) => dt.items.add(f));
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
    for (let i = 0; i < 200 && (UPLBUSY || (!PENDING && !UPLERR)); i++) await wait(25);
    assert(!UPLERR, 'the page said: ' + UPLERR);
    assert(PENDING, 'the export never finished reading');
  }
  const useIt = async () => {
    const b = $1('[data-act=uplok]');
    assert(b, 'no Use This Export button');
    b.click();
    await wait(50);
  };
  const who = (name) => {
    const p = P.find((x) => x.name === name);
    assert(p, name + ' is not in the network');
    return p;
  };
  const homeOf = (k) => P.filter((p) => p.home === k).map((p) => p.name).sort();
  const regroup = async () => {
    readConfig();
    initNetwork();
    applyAccent(ACCENT);
    render();
    await wait(30);
  };
  // Every piece of text the user can read in the page as it stands, labels included.
  const visibleText = () => {
    const t = [document.title, document.body.innerText];
    for (const el of $all('[aria-label], [title], [placeholder]')) t.push(el.getAttribute('aria-label') || '', el.getAttribute('title') || '', el.getAttribute('placeholder') || '');
    return t.join('\n');
  };
  const dashSeen = [];
  const noteDashes = (where) => {
    const t = visibleText();
    if (/\u2014/.test(t)) dashSeen.push(where + ': ' + t.slice(Math.max(0, t.indexOf('\u2014') - 60), t.indexOf('\u2014') + 20));
  };
  await wait(200);

  // Expected homes under the test candidate's 3-year warm window (export dated 2026-10-12).
  const HOMES = {
    warm: ['Aisha Lindqvist', 'Ben Moreno', 'Dana Whitfield', 'Elena Brooks', 'Marcus Okafor', 'Priya Raman', 'Tom Achebe'],
    mentors: ['Diego Nakamura', 'Fiona Hughes'],
    search: ['Grace Patel', 'Hiro Kowalski', 'Imani Adeyemi'],
    recruiters: ['Luis Duarte', 'Maya Sato', 'Nikhil Bennett', 'Olivia Reyes'],
    exec: ['Carmen Castillo', 'Kara Novak', 'Rosa Mbeki', 'Tara Kim', 'Theo Ibarra', 'Uma Laurent'],
    robotics: ['Quinn Olsen', 'Victor Murphy', 'Wren Nguyen'],
    finance: ['Andre Rossi', 'Yusuf Osei', 'Zoe Park'],
    founders: ['Bianca Sullivan', 'Caleb Tanaka', 'Delia Underwood'],
    'globex-years': ['Eli Vasquez', 'Farah Walsh'],
    others: ['Gabe Yilmaz', 'Hana Zhou', 'Ivan Abbott', 'Jade Bauer', 'Jonah Fischer', 'Kofi Cho', 'Lena Dalton', 'Mateo Ellis', 'Mira Castellano', 'Pablo Haddad'],
  };
  const ORDER = ['motion', 'warm', 'mentors', 'search', 'recruiters', 'exec', 'robotics', 'finance', 'founders', 'globex-years', 'others'];

  await check('before any export, the page opens on the upload panel', async () => {
    assert(!HAS_NET, 'the page thinks it has an export');
    assert($1('#welcome'), 'no upload panel in the page');
    assert($1('#welcome #uplDrop') && $1('#welcome [data-act=uplpick]'), 'the upload panel has no drop box or Choose File button');
    assert($1('#welcome').textContent.includes('Upload Your LinkedIn Export'), 'the upload panel has no heading');
    assert($1('#tabs').hidden && !$all('#tabs a').length, 'group tabs show before any export');
    assert($1('#panel').hidden, 'a side panel is open');
    assert(!$1('.list') && !$1('.board'), 'a list or board shows before any export');
    assert(localStorage.getItem('bishop_outreach_network_v1') === null, 'contacts are stored before any upload');
    noteDashes('empty state');
  });

  await check('the top bar shows the name the user gave their Bishop', async () => {
    const name = expect.name || 'Bishop';
    same($1('#brandName').textContent, name, 'top bar name');
    assert(document.title === 'Outreach · ' + name, 'page title: ' + document.title);
  });

  await check('uploading the two CSVs reads the export in the page', async () => {
    await pick([csvFile(X.connections, 'Connections.csv'), csvFile(X.messages, 'messages.csv')]);
    same(PENDING.people.length, 43, 'connections read');
    same(PENDING.exported, '2026-10-12', 'export date (from the files)');
    assert(PENDING.hasMsgs, 'messages.csv not read');
    const preview = Object.fromEntries($all('#uplGroups li').map((li) => [li.dataset.k, +li.querySelector('b').textContent]));
    same(preview, Object.fromEntries(ORDER.slice(1).map((k) => [k, HOMES[k].length])), 'the preview counts');
    noteDashes('upload preview');
    await useIt();
    assert(HAS_NET && P.length === 43, 'the board did not load the export');
    assert(!$1('#welcome'), 'the upload panel still fills the page');
    const stored = JSON.parse(localStorage.getItem('bishop_outreach_network_v1'));
    assert(stored && stored.v === 1 && stored.people.length === 43, 'contacts not stored in the browser under bishop_outreach_network_v1');
    assert(!JSON.stringify(stored).includes('conference panel'), 'message text was stored');
  });

  await check('message counts: two-way, one-way, a group thread and a draft', async () => {
    same([who('Dana Whitfield').dir, who('Dana Whitfield').count], ['both', 6], 'Dana');
    same(who('Maya Sato').dir, 'you', 'Maya (you wrote)');
    same(who('Andre Rossi').dir, 'them', 'Andre (they wrote)');
    same([who('Kofi Cho').dir, who('Lena Dalton').dir], ['none', 'none'], 'a group thread counts for nobody');
    same(who('Hana Zhou').dir, 'none', 'a draft counts for nobody');
    same(who('Ben Moreno').lm, '2024-06-19', "Ben's last message");
  });

  await check('tabs: In Motion, the groups in the user order, Everyone Else last', async () => {
    same($all('#tabs a').map((a) => a.getAttribute('href').slice(2)), ORDER, 'tab order');
    same($all('#tabs a').map((a) => a.childNodes[a.childNodes.length - 2].textContent.trim()).slice(1),
      ['Warm', 'Mentors', 'In My Search', 'Recruiters', 'Executives', 'Robotics', 'Finance', 'Entrepreneurs', 'Globex Years', 'Everyone Else'], 'tab labels');
    assert(!$1('#tabs a[href="#/hr"]'), 'the dropped HR / People group has a tab');
  });

  await check('group counts, each group and each custom match type', async () => {
    for (const k of ORDER.slice(1)) same(homeOf(k), HOMES[k], k);
    const tabCounts = Object.fromEntries($all('#tabs a').map((a) => [a.getAttribute('href').slice(2), +a.querySelector('.c').textContent]));
    for (const k of ORDER.slice(1)) same(tabCounts[k], HOMES[k].length, 'tab count for ' + k);
    // The custom types, one each: a names file, the job search, a company list, title words, connected dates.
    same(who('Diego Nakamura').why, 'on your hand-picked list', 'names file');
    same(who('Imani Adeyemi').why, 'works at Umbrella Logistics, Inc., in your job search', 'job search, with a company suffix');
    same(who('Wren Nguyen').why, 'works at Ironfen Robotics', 'company list, with a suffix on the list side');
    same(who('Zoe Park').why, 'title has "controller"', 'title words');
    same(who('Farah Walsh').why, 'connected Jun 2021, inside your dates', 'connected dates, on the last day');
    same(who('Gabe Yilmaz').home, 'others', 'a day past the connected range');
    same(who('Luis Duarte').why, 'works at a search firm', 'recruiters by company');
    for (const k of ORDER.slice(1)) {
      location.hash = '#/' + k;
      render();
      await wait(10);
      same($all('main .row').length, HOMES[k].length, 'rows in ' + k);
      noteDashes(k + ' tab');
    }
  });

  await check('warm window: a two-way thread counts only when its last message is inside it', async () => {
    same(WARM_WINDOW, '3y', 'the built window');
    same(who('Carmen Castillo').home, 'exec', 'a 2021 thread under 3y');
    try {
      CONFIG.warmWindow = '1y';
      await regroup();
      same(homeOf('warm'), ['Aisha Lindqvist', 'Dana Whitfield', 'Elena Brooks', 'Marcus Okafor', 'Tom Achebe'], 'warm under 1y');
      same(who('Priya Raman').home, 'globex-years', 'Priya (last message Feb 2025) under 1y');
      same(who('Ben Moreno').home, 'search', 'Ben (last message Jun 2024) under 1y');
      CONFIG.warmWindow = 'any';
      await regroup();
      same(homeOf('warm'), [...HOMES.warm, 'Carmen Castillo'].sort(), 'warm under any');
      same(homeOf('exec').length, HOMES.exec.length - 1, 'executives under any');
    } finally {
      CONFIG.warmWindow = '3y';
      await regroup();
    }
    same(homeOf('warm'), HOMES.warm, 'warm back under 3y');
    same(who('Maya Sato').home, 'recruiters', 'one-way is never warm');
  });

  await check('tags and "why here" name the other groups and the rule that matched', async () => {
    same(who('Dana Whitfield').tags, ['mentors', 'globex-years'], "Dana's tags");
    same(who('Dana Whitfield').why, 'exchanged messages, the last in Sep 2026', "Dana's reason");
    same(who('Hiro Kowalski').tags, ['recruiters'], "Hiro's tags");
    same(who('Carmen Castillo').tags, ['finance'], "Carmen's tags");
    same(who('Carmen Castillo').why, 'title has "Chief"', "Carmen's reason");
    location.hash = '#/warm';
    render();
    await wait(10);
    const row = $1('main .row[data-id="' + who('Dana Whitfield').id + '"]');
    assert(row && row.querySelector('.tag.grp.g-mentors') && row.querySelector('.tag.grp.g-globex-years'), "Dana's row has no group tags");
    openPerson(who('Dana Whitfield').id);
    await wait(30);
    const line = $1('#whyHere').textContent;
    assert(line.startsWith('Why here: Warm, exchanged messages, the last in Sep 2026'), 'why here: ' + line);
    assert(line.includes('Also in Mentors Globex Years'), 'why here has no other groups: ' + line);
    noteDashes('person panel');
    closePanel();
    await wait(30);
  });

  await check('worked there: people at a past employer, and only then', async () => {
    same(P.filter((p) => p.co.past).map((p) => p.name).sort(), ['Ben Moreno', 'Jonah Fischer', 'Kara Novak'], 'at a past employer');
    location.hash = '#/others';
    render();
    await wait(10);
    const row = $1('main .row[data-id="' + who('Jonah Fischer').id + '"]');
    assert(row && /Worked There/.test(row.textContent), "Jonah's row doesn't say Worked There");
    openPerson(who('Kara Novak').id);
    await wait(30);
    assert($1('#whyHere').textContent.includes('You worked there'), 'why here: ' + $1('#whyHere').textContent);
    closePanel();
    await wait(30);
    const keep = CONFIG.pastEmployers;
    try {
      CONFIG.pastEmployers = [];
      await regroup();
      for (const k of ORDER) {
        location.hash = '#/' + k;
        render();
        await wait(5);
        assert(!/worked there|you worked for/i.test($1('main').innerText), 'with no past employers, ' + k + ' still says worked there');
      }
    } finally {
      CONFIG.pastEmployers = keep;
      await regroup();
    }
  });

  await check('Everyone Else: always there, last, holding whoever fits no group', async () => {
    location.hash = '#/others';
    render();
    await wait(10);
    assert($1('main .lede').textContent === 'Everyone who fits no other group.', 'lede: ' + $1('main .lede').textContent);
    same(who('Pablo Haddad').home, 'others', 'an HR title, with HR / People dropped');
    same(who('Pablo Haddad').why, 'no group matched', "Pablo's reason");
    const keep = CONFIG.groups;
    try {
      CONFIG.groups = [];
      await regroup();
      same($all('#tabs a').map((a) => a.getAttribute('href')), ['#/motion', '#/others'], 'tabs with no groups');
      same(P.filter((p) => p.home === 'others').length, 43, 'everyone in Everyone Else');
    } finally {
      CONFIG.groups = keep;
      await regroup();
    }
  });

  await check('uploading the zip reads the same export', async () => {
    const before = JSON.stringify(JSON.parse(localStorage.getItem('bishop_outreach_network_v1')).people);
    $1('[data-act=upload]').click();
    await wait(30);
    assert(!$1('#panel').hidden && $1('#panel #uplDrop'), 'Upload Export did not open the panel');
    noteDashes('upload panel');
    await pick([zipFile()]);
    same(PENDING.exported, '2026-10-12', 'export date (from the zip name)');
    same(JSON.stringify(PENDING.people), before, 'the zip and the CSVs read the same');
    await useIt();
    same(P.length, 43, 'people after the zip');
    assert(/Your stages and notes stayed/.test($1('#toast').textContent), 'toast: ' + $1('#toast').textContent);
  });

  await check('a stage change and Note It survive a re-upload of a changed export', async () => {
    const eli = who('Eli Vasquez').id,
      mateo = who('Mateo Ellis').id;
    openPerson(eli);
    await wait(30);
    $1('#panel [data-act=stage][data-to="Up Next"]').click();
    await wait(30);
    same(get(eli).stage, 'Up Next', 'stage after Up Next');
    closePanel();
    await wait(30);
    location.hash = '#/motion';
    render();
    await wait(20);
    const card = $1('main .card[data-id="' + eli + '"]');
    assert(card, 'Eli has no card in In Motion');
    const noteIt = [...card.querySelectorAll('button')].find((b) => b.textContent === 'Note It');
    assert(noteIt, 'the card has no Note It button');
    noteIt.click();
    await wait(80);
    $1('#lgText').value = 'Asked how their analytics team plans its quarter.';
    $1('[data-act=logadd]').click();
    await wait(30);
    const notes = $1('#notes');
    notes.value = 'Met at a product meetup.';
    notes.dispatchEvent(new Event('input', { bubbles: true }));
    await wait(600);
    closePanel();
    await wait(30);
    setStage([mateo], 'Archived', 'Mateo archived');
    // The changed export: Mateo left, Eli's title changed, and someone new connected.
    const lines = X.connections.split(/\r?\n/);
    const changed = lines
      .filter((l) => !l.startsWith('Mateo,Ellis,'))
      .map((l) => (l.startsWith('Eli,Vasquez,') ? l.replace(',Product Manager,', ',Senior Product Manager,') : l));
    changed.splice(changed.length - 1, 0, 'Noor,Fairweather,https://www.linkedin.com/in/noor-fairweather-77c1d0,,Brasswing Robotics,Robotics Technician,01 Oct 2026');
    $1('[data-act=upload]').click();
    await wait(30);
    await pick([csvFile(changed.join('\n'), 'Connections.csv'), csvFile(X.messages, 'messages.csv')]);
    await useIt();
    same(P.length, 43, 'people after the re-upload');
    assert(!PI[mateo], 'Mateo is still on the board after leaving the network');
    same(who('Noor Fairweather').home, 'robotics', 'the new connection');
    same(who('Eli Vasquez').title, 'Senior Product Manager', "Eli's new title");
    same(get(eli).stage, 'Up Next', "Eli's stage after the re-upload");
    assert((get(eli).log || []).some((e) => e.type === 'Email' && e.text === 'Asked how their analytics team plans its quarter.'), "Eli's Note It entry is gone");
    same(get(eli).notes, 'Met at a product meetup.', "Eli's notes");
    same(S.p[mateo] && S.p[mateo].stage, 'Archived', 'a board entry for someone who left is kept, in case they come back');
    location.hash = '#/motion';
    render();
    await wait(20);
    assert($1('main .card[data-id="' + eli + '"]'), 'Eli is not in In Motion after the re-upload');
    const board = JSON.parse(localStorage.getItem('bishop_outreach_board_v1'));
    same(board.v, 1, 'board store version');
    same(board.p[eli].stage, 'Up Next', 'the stored stage');
  });

  await check('the accent from setup colors the page, in both themes', async () => {
    same(ACCENT, '#4F6D9F', 'the accent the page read');
    const want = { light: tune(rgbOf(ACCENT), [255, 255, 255], [0, 0, 0], 0.12).accent, dark: tune(rgbOf(ACCENT), [21, 29, 46], [255, 255, 255], 0.2).accent };
    const root = document.documentElement;
    const keep = root.dataset.theme;
    try {
      for (const theme of ['light', 'dark']) {
        root.dataset.theme = theme;
        const got = getComputedStyle(root).getPropertyValue('--accent').trim();
        same(got, want[theme], theme + ' --accent');
        assert(!['#c2410c', '#ff8a4c'].includes(got), theme + ' accent is still the stock orange');
      }
    } finally {
      root.dataset.theme = keep;
    }
    // Slate blue sits on the Executives hue, so that group moves to a spare color.
    const exec = getComputedStyle(root).getPropertyValue('--g-exec').trim();
    assert(exec && exec !== '#3b6fd8', 'Executives kept the blue the accent sits on: ' + exec);
    const custom = getComputedStyle(root).getPropertyValue('--g-robotics').trim();
    assert(/^#[0-9a-f]{6}$/.test(custom), 'a custom group has no color: ' + custom);
  });

  await check('no em dash in any visible text', async () => {
    location.hash = '#/motion';
    render();
    await wait(10);
    noteDashes('In Motion');
    $1('[data-act=help]').click();
    await wait(30);
    noteDashes('help');
    closePanel();
    await wait(30);
    VIEW = 'company';
    location.hash = '#/exec';
    render();
    await wait(10);
    noteDashes('company view');
    VIEW = 'people';
    render();
    assert(!dashSeen.length, dashSeen.join(' | '));
  });

  await check('no script errors on the page', async () => {
    const errs = window.__errors || [];
    assert(!errs.length, errs.join(' | '));
  });

  const pre = document.createElement('pre');
  pre.id = 'test-results';
  pre.textContent = JSON.stringify(results);
  document.body.appendChild(pre);
  document.title = 'TESTS-DONE';
})();
