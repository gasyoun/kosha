<script>
  import SearchBox from './components/SearchBox.svelte';
  import ParadigmTable from './components/ParadigmTable.svelte';
  import ReverseAnalyze from './components/ReverseAnalyze.svelte';
  import EntryView from './components/EntryView.svelte';
  import WordPage from './components/WordPage.svelte';
  import History from './components/History.svelte';
  import Stats from './components/Stats.svelte';
  import { getParadigm, API } from './lib/datasource.js';
  import { fromSlp1Out } from './lib/translit.js';
  import { wordHash, parseWordHash } from './lib/query.js';
  import { toCsv, toAnki, downloadFile } from './lib/export.js';

  let mode = $state('word');         // 'word' | 'forward' | 'reverse' | 'history' | 'stats'
  let out = $state('deva');          // Devanagari-default output (K2b-4)
  let forwardLemma = $state('');
  let paradigm = $state(null);
  let pLoading = $state(false);
  let pErr = $state(null);
  let entryLemma = $state('');       // in-app dictionary entry panel (K3-folded)
  let wordSlp1 = $state('');         // P5 word page (the /w/{slp1} in-app twin)
  let reverseSeed = $state('');      // sandhi: operator prefill for ReverseAnalyze
  let lookups = $state([]);          // P5 §6 session lookups, for CSV/Anki export

  // --- P5 hash routing (#/w/<slp1>) + operators -----------------------------
  function goWord(slp1) {
    if (!slp1) return;
    wordSlp1 = slp1; mode = 'word'; entryLemma = '';
    const h = wordHash(slp1);
    if (location.hash !== h) location.hash = h;   // triggers hashchange, but goWord is idempotent
  }
  function syncFromHash() {
    const slp1 = parseWordHash(location.hash);
    if (slp1) { wordSlp1 = slp1; mode = 'word'; }
  }
  function onCommand(kind, value) {
    if (kind === 'sandhi') { reverseSeed = value; mode = 'reverse'; }
    else if (kind === 'root') { goWord(value); }   // the root's own entry + paradigm (P5 §4)
  }
  function recordLookup(meta) {
    // de-dupe by slp1, most-recent-last
    lookups = [...lookups.filter((l) => l.slp1 !== meta.slp1), meta];
  }
  $effect(() => {
    syncFromHash();
    const on = () => syncFromHash();
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  });

  async function loadForward(slp1) {
    forwardLemma = slp1;
    pLoading = true; pErr = null; paradigm = null;
    try {
      paradigm = await getParadigm(slp1);
    } catch (e) {
      pErr = e.status === 404
        ? `No inflection paradigm for “${fromSlp1Out(slp1, 'iast')}”. It may be a headword with no ingested inflection table.`
        : e.message;
    } finally {
      pLoading = false;
    }
  }

  function showEntry(slp1) { entryLemma = slp1; }
  function showForms(slp1) { mode = 'forward'; entryLemma = ''; loadForward(slp1); }
  function selectFromHistory(slp1) { mode = 'forward'; entryLemma = ''; loadForward(slp1); }
</script>

<main>
  <header>
    <h1>Sanskrit Inflection Lookup</h1>
    <p class="sub">
      Gasuns Sanskrit Dictionary · forward paradigms, reverse analysis, and
      dictionary cross-links over the Cologne inflection tables.
      {#if API}<span class="mode-badge live">live API</span>
      {:else}<span class="mode-badge">static</span>{/if}
    </p>
  </header>

  <nav class="tabs">
    <button class:active={mode === 'word'} onclick={() => (mode = 'word')}>Word page</button>
    <button class:active={mode === 'forward'} onclick={() => (mode = 'forward')}>Stem → paradigm</button>
    <button class:active={mode === 'reverse'} onclick={() => (mode = 'reverse')}>Analyse a form</button>
    {#if API}
      <button class:active={mode === 'history'} onclick={() => (mode = 'history')}>History</button>
      <button class:active={mode === 'stats'} onclick={() => (mode = 'stats')}>Stats</button>
    {/if}
    <span class="spacer"></span>
    <div class="script-toggle" role="radiogroup" aria-label="Output script">
      {#each [['deva', 'देव'], ['iast', 'IAST'], ['slp1', 'SLP1']] as [v, label]}
        <button class:on={out === v} onclick={() => (out = v)} role="radio" aria-checked={out === v}>{label}</button>
      {/each}
    </div>
  </nav>

  {#if mode === 'word'}
    <section>
      <SearchBox onselect={goWord} oncommand={onCommand} />
      {#if lookups.length}
        <div class="export-bar">
          <span>{lookups.length} word{lookups.length !== 1 ? 's' : ''} looked up this session</span>
          <button onclick={() => downloadFile('kosha-lookups.csv', toCsv(lookups), 'text/csv')}>Export CSV</button>
          <button onclick={() => downloadFile('kosha-lookups.txt', toAnki(lookups), 'text/plain')}>Export Anki</button>
          <button class="clear" onclick={() => (lookups = [])}>clear</button>
        </div>
      {/if}
      {#if wordSlp1}
        <WordPage slp1={wordSlp1} {out} onloaded={recordLookup} />
      {:else}
        <p class="muted">Search a headword to open its word page — every dictionary,
          its evidence, and its full paradigm on one address. Try
          <code>root:BU</code> or <code>sandhi:tattvamasi</code>.</p>
      {/if}
    </section>
  {:else if mode === 'forward'}
    <section>
      <SearchBox onselect={loadForward} />
      {#if pLoading}
        <p class="muted">loading paradigm…</p>
      {:else if pErr}
        <p class="err">{pErr}</p>
      {:else if paradigm}
        <div class="p-head">
          <h2>{fromSlp1Out(paradigm.lemma_slp1, out)} <span class="key">{paradigm.lemma_iast}</span></h2>
          {#if paradigm.has_entry}
            <button class="entry-link" onclick={() => showEntry(paradigm.lemma_slp1)}>dictionary entry →</button>
          {/if}
        </div>
        {#each paradigm.models as model}
          <ParadigmTable {model} {out} highlight={forwardLemma} />
        {/each}
      {/if}
    </section>
  {:else if mode === 'reverse'}
    <section>
      <ReverseAnalyze onlemma={showEntry} {out} seed={reverseSeed} />
    </section>
  {:else if mode === 'history'}
    <section>
      <History {out} onselect={selectFromHistory} />
    </section>
  {:else}
    <section>
      <Stats {out} />
    </section>
  {/if}

  {#if entryLemma}
    <section class="entry-panel">
      <div class="panel-bar">
        <span>Dictionary entry</span>
        <button class="close" onclick={() => (entryLemma = '')} aria-label="close entry">✕</button>
      </div>
      <EntryView slp1={entryLemma} {out} onforms={showForms} />
    </section>
  {/if}

  <footer>
    <p>
      Inflection data: Cologne <a href="https://github.com/sanskrit-lexicon/MWinflect" target="_blank" rel="noopener">csl-inflect</a>
      tables, ingested verbatim (cells surfaced as-is, including known upstream caveats).
      Part of <a href="https://github.com/gasyoun/kosha" target="_blank" rel="noopener">kosha</a>.
    </p>
  </footer>
</main>

<style>
  :global(:root) {
    --fg: #1a1a1a; --muted: #6b7280; --border: #d7d7db; --accent: #7b2d26;
    --field-bg: #fff; --card-bg: #fafafa; --head-bg: #f0f0f2; --hit-bg: #fdf3e7;
    --tag-bg: #ece7e0; --tag-fg: #7b2d26; --page-bg: #fff;
  }
  @media (prefers-color-scheme: dark) {
    :global(:root) {
      --fg: #e8e8ea; --muted: #9aa0a6; --border: #3a3a40; --accent: #e0a44a;
      --field-bg: #1d1d20; --card-bg: #202024; --head-bg: #26262b; --hit-bg: #3a3020;
      --tag-bg: #2c2c31; --tag-fg: #e0a44a; --page-bg: #161618;
    }
  }
  :global(body) { margin: 0; background: var(--page-bg); color: var(--fg);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  main { max-width: 60rem; margin: 0 auto; padding: 1.5rem 1rem 4rem; }
  header h1 { margin: 0 0 .3rem; font-size: 1.7rem; }
  .sub { margin: 0 0 1.2rem; color: var(--muted); font-size: .95rem; }
  .mode-badge { font-size: .65rem; font-weight: 700; padding: .1rem .45rem; border-radius: 4px;
    background: var(--tag-bg); color: var(--tag-fg); text-transform: uppercase; margin-left: .3rem; }
  .mode-badge.live { background: var(--accent); color: #fff; }
  .tabs { display: flex; gap: .4rem; align-items: center; margin-bottom: 1.2rem; flex-wrap: wrap;
    border-bottom: 1px solid var(--border); padding-bottom: .6rem; }
  .tabs > button {
    font-size: .95rem; padding: .4rem .9rem; border: 1px solid var(--border);
    background: var(--field-bg); color: var(--fg); border-radius: 6px; cursor: pointer;
  }
  .tabs > button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  .spacer { flex: 1; }
  .script-toggle { display: inline-flex; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
  .script-toggle button { border: none; background: var(--field-bg); color: var(--muted); padding: .35rem .7rem; cursor: pointer; font-size: .85rem; }
  .script-toggle button.on { background: var(--head-bg); color: var(--fg); font-weight: 600; }
  .p-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; flex-wrap: wrap; margin: 1.2rem 0 .8rem; }
  .p-head h2 { margin: 0; }
  .key { font-size: .9rem; color: var(--muted); font-weight: 400; }
  .entry-link { font-size: .85rem; padding: .3rem .7rem; border: 1px solid var(--accent); color: var(--accent); background: transparent; border-radius: 6px; cursor: pointer; }
  .entry-link:hover { background: var(--hit-bg); }
  .entry-panel { margin-top: 1.5rem; }
  .panel-bar { display: flex; justify-content: space-between; align-items: center; font-size: .8rem;
    text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin-bottom: .5rem; }
  .close { border: none; background: none; color: var(--muted); font-size: 1rem; cursor: pointer; }
  footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: .8rem; color: var(--muted); }
  footer a { color: var(--accent); }
  .muted { color: var(--muted); }
  .err { color: #c0392b; }
  .export-bar { display: flex; gap: .5rem; align-items: center; flex-wrap: wrap;
    margin: .8rem 0; font-size: .85rem; color: var(--muted); }
  .export-bar button { font-size: .8rem; padding: .3rem .7rem; border: 1px solid var(--accent);
    color: var(--accent); background: transparent; border-radius: 6px; cursor: pointer; }
  .export-bar button:hover { background: var(--hit-bg); }
  .export-bar button.clear { border-color: var(--border); color: var(--muted); }
  code { font-family: monospace; background: var(--tag-bg); color: var(--tag-fg);
    padding: .05rem .3rem; border-radius: 4px; font-size: .85em; }
</style>
