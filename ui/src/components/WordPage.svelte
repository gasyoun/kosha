<script>
  // P5 word page in the SPA (H537, P5_ADVANCED_UI_DESIGN.md §3) — the interactive
  // twin of the static prerender (app/word_page.py). One headword, every
  // dictionary's entry on tabs (P5-1), a Gloss/Full/Adaptive view-mode toggle
  // (P5-2, persisted), and evidence / paradigm / scan disclosures (P3/P4).
  // Composes existing assets (getEntry, getParadigm, ParadigmTable) — see the
  // reuse ledger in P5_ADVANCED_UI_DESIGN.md §7; no data path is re-derived.
  import { getEntry, getParadigm } from '../lib/datasource.js';
  import { fromSlp1Out } from '../lib/translit.js';
  import { groupByDict, DICT_LABEL, loadViewMode, saveViewMode } from '../lib/query.js';
  import { glossOf } from '../lib/export.js';
  import ParadigmTable from './ParadigmTable.svelte';

  // onloaded({slp1, iast, deva, gloss, dicts}) fires once entries load, so the
  // app can record the session lookup for CSV/Anki export (P5 §6).
  let { slp1, out = 'deva', onloaded } = $props();

  let entries = $state(null);
  let loading = $state(false);
  let err = $state(null);
  let activeDict = $state(null);
  let view = $state(loadViewMode());

  // Paradigm is fetched lazily when its disclosure opens (P4), never inlined —
  // keeps the first paint light and matches the static page's JS-hydrated slot.
  let paradigm = $state(null);
  let paraLoading = $state(false);
  let paraErr = $state(null);
  let paraOpen = $state(false);

  const groups = $derived(entries ? groupByDict(entries) : []);
  const evidence = $derived(entries && entries.length ? entries[0].evidence : null);
  const band = $derived(evidence ? evidence.band : null);

  $effect(() => {
    const key = slp1;
    if (!key) { entries = null; return; }
    loading = true; err = null; entries = null; activeDict = null;
    paradigm = null; paraOpen = false; paraErr = null;
    getEntry(key)
      .then((r) => {
        entries = r;
        activeDict = groupByDict(r)[0]?.dict ?? null;
        if (r && r.length && onloaded) {
          onloaded({
            slp1: key,
            iast: fromSlp1Out(key, 'iast'),
            deva: fromSlp1Out(key, 'deva'),
            gloss: glossOf(r[0].rendered_html),
            dicts: groupByDict(r).map((g) => DICT_LABEL[g.dict] ?? g.dict).join(' '),
          });
        }
      })
      .catch((e) => { err = e.message; })
      .finally(() => { loading = false; });
  });

  function setView(v) { view = v; saveViewMode(v); }

  async function openParadigm() {
    paraOpen = !paraOpen;
    if (!paraOpen || paradigm || paraLoading) return;
    paraLoading = true; paraErr = null;
    try {
      paradigm = await getParadigm(slp1);
    } catch (e) {
      paraErr = e.status === 404
        ? 'No inflection table ingested for this headword.'
        : e.message;
    } finally {
      paraLoading = false;
    }
  }
</script>

<div class="wp" data-view={view}>
  {#if loading}
    <p class="muted">loading word…</p>
  {:else if err}
    <p class="err">could not load: {err}</p>
  {:else if entries && entries.length}
    <header class="hw-strip">
      <span class="hw-deva">{fromSlp1Out(slp1, 'deva')}</span>
      <span class="hw-iast">{fromSlp1Out(slp1, 'iast')}</span>
      <span class="hw-key">[{slp1}]</span>
      {#if band != null}
        <span class="band b{band}" title={evidence.band_label}>band {band}</span>
      {/if}
      <span class="ndicts">{groups.length} dict{groups.length !== 1 ? 's' : ''}</span>
    </header>

    <div class="view-toggle" role="radiogroup" aria-label="Detail level">
      {#each [['gloss', 'Gloss'], ['full', 'Full'], ['adaptive', 'Adaptive']] as [v, label]}
        <button type="button" role="radio" aria-checked={view === v}
                class:on={view === v} onclick={() => setView(v)}>{label}</button>
      {/each}
    </div>

    <nav class="dict-tabs" role="tablist" aria-label="Dictionaries">
      {#each groups as g}
        <button type="button" class="tab" class:active={activeDict === g.dict}
                role="tab" aria-selected={activeDict === g.dict}
                onclick={() => (activeDict = g.dict)}>
          {DICT_LABEL[g.dict] ?? g.dict.toUpperCase()}<span class="tab-n">{g.entries.length}</span>
        </button>
      {/each}
    </nav>

    {#each groups as g}
      <section class="dict-panel" role="tabpanel" hidden={activeDict !== g.dict}>
        {#each g.entries as e, i}
          <article class="dict-entry" class:secondary={i > 0}>
            <div class="entry-head">
              <span class="hw">{e.headword}</span>
              {#if e.scan_url}<a class="scan" href={e.scan_url} target="_blank" rel="noopener">scan ↗</a>{/if}
            </div>
            <div class="rendered">{@html e.rendered_html}</div>
          </article>
        {/each}
      </section>
    {/each}

    {#if evidence}
      <details class="disclosure">
        <summary>Evidence</summary>
        <ul class="ev-list">
          <li><b>Frequency band {evidence.band}</b> — {evidence.band_label}</li>
          <li>{evidence.count_all == null ? 'no attestation data' : `${evidence.count_all} attestations in DCS`}</li>
          {#if evidence.first_era}<li>first attested: {evidence.first_era}</li>{/if}
        </ul>
        {#if evidence.example && evidence.example.sa}
          <blockquote class="example">{evidence.example.sa}
            {#if evidence.example.work}<cite> — {evidence.example.work}</cite>{/if}</blockquote>
        {/if}
      </details>
    {/if}

    <details class="disclosure" ontoggle={openParadigm}>
      <summary>Paradigm (all forms)</summary>
      {#if paraLoading}<p class="muted">loading paradigm…</p>
      {:else if paraErr}<p class="muted">{paraErr}</p>
      {:else if paradigm}
        {#each paradigm.models as model}<ParadigmTable {model} {out} />{/each}
      {/if}
    </details>
  {:else}
    <p class="muted">No dictionary entry for <span class="hw-key">[{slp1}]</span>.</p>
  {/if}
</div>

<style>
  .hw-strip { display: flex; gap: .7rem; align-items: baseline; flex-wrap: wrap;
    border-bottom: 1px solid var(--border); padding-bottom: .6rem; }
  .hw-deva { font-size: 2rem; }
  .hw-iast { font-size: 1.2rem; color: var(--muted); }
  .hw-key { font-family: monospace; font-size: .8rem; color: var(--muted); }
  .band { font-size: .65rem; font-weight: 700; padding: .12rem .45rem; border-radius: 4px;
    color: #fff; text-transform: uppercase; background: var(--accent); }
  .ndicts { font-size: .72rem; color: var(--muted); }
  .view-toggle { display: inline-flex; margin: .7rem 0 0; border: 1px solid var(--border);
    border-radius: 6px; overflow: hidden; }
  .view-toggle button { border: none; background: var(--page-bg); color: var(--muted);
    padding: .3rem .7rem; cursor: pointer; font-size: .8rem; }
  .view-toggle button.on { background: var(--head-bg); color: var(--fg); font-weight: 600; }
  .dict-tabs { display: flex; gap: .35rem; flex-wrap: wrap; margin: .9rem 0 0;
    border-bottom: 1px solid var(--border); }
  .tab { border: 1px solid var(--border); border-bottom: none; background: var(--card-bg);
    color: var(--fg); padding: .4rem .8rem; cursor: pointer; border-radius: 6px 6px 0 0; font-size: .9rem; }
  .tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  .tab-n { font-size: .65rem; opacity: .75; margin-left: .3rem; }
  .dict-panel { border: 1px solid var(--border); border-top: none; padding: .4rem 1rem;
    background: var(--card-bg); }
  .dict-entry { border-top: 1px solid var(--border); padding: .55rem 0; }
  .dict-entry:first-child { border-top: none; }
  .entry-head { display: flex; gap: .7rem; align-items: baseline; margin-bottom: .25rem; }
  .entry-head .hw { font-weight: 600; }
  .scan { font-size: .8rem; color: var(--accent); }
  .rendered { overflow-wrap: anywhere; line-height: 1.5; }
  /* Gloss hides all but the first entry; Adaptive does so only on a narrow
     viewport (mirrors the static page's CSS). */
  .wp[data-view=gloss] .dict-entry.secondary { display: none; }
  @media (max-width: 640px) { .wp[data-view=adaptive] .dict-entry.secondary { display: none; } }
  .disclosure { margin: .8rem 0 0; border: 1px solid var(--border); border-radius: 8px;
    background: var(--card-bg); padding: .3rem .8rem; }
  .disclosure summary { cursor: pointer; font-weight: 600; font-size: .9rem; padding: .3rem 0; }
  .ev-list { margin: .2rem 0 .4rem; padding-left: 1.1rem; font-size: .9rem; }
  .example { margin: .3rem 0; padding: .4rem .7rem; border-left: 3px solid var(--accent);
    background: var(--hit-bg); font-size: 1.05rem; }
  .muted { color: var(--muted); }
  .err { color: #c0392b; }
</style>
