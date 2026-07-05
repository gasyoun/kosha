<script>
  import { toSlp1Auto, detectScheme, fromSlp1Out } from '../lib/translit.js';
  import { analyzeForm } from '../lib/datasource.js';

  // Paste-anything reverse box: wraps /api/v1/forms/{form}/analyze (or the
  // static reverse index). Shows each parse's provenance (`resolved_by`) so a
  // translator sees WHY a form resolved (H183 §4.5).
  let { onlemma, out = 'deva' } = $props();

  let text = $state('');
  let result = $state(null);
  let loading = $state(false);
  let err = $state(null);
  let lastForm = $state('');

  const scheme = $derived(text ? detectScheme(text) : null);

  async function run() {
    const raw = text.trim();
    if (!raw) return;
    let slp1;
    try { slp1 = toSlp1Auto(raw, 'auto'); } catch (e) { err = e.message; return; }
    loading = true; err = null; result = null; lastForm = slp1;
    try {
      result = await analyzeForm(slp1);
    } catch (e) {
      err = e.message;
    } finally {
      loading = false;
    }
  }

  function grammar(a) {
    const parts = [];
    if (a.case) parts.push(a.case);
    if (a.number) parts.push(a.number);
    if (a.person) parts.push(`${a.person}p`);
    if (a.tense) parts.push(a.tense);
    if (a.voice) parts.push(a.voice);
    return parts.join(' · ');
  }
</script>

<div class="reverse">
  <div class="row">
    <input
      type="text"
      bind:value={text}
      onkeydown={(e) => e.key === 'Enter' && run()}
      placeholder="dharmakṣetre · rāmeṇa · भगवान् · tattvamasi"
      autocomplete="off" autocapitalize="off" spellcheck="false"
      aria-label="Paste any Sanskrit form to analyse"
    />
    <button onclick={run}>Analyse</button>
  </div>
  {#if scheme}<div class="hint"><span class="badge">{scheme.toUpperCase()}</span> auto-detected</div>{/if}

  {#if loading}
    <p class="muted">analysing…</p>
  {:else if err}
    <p class="err">{err}</p>
  {:else if result}
    <div class="res">
      <div class="prov-line">
        <strong>{fromSlp1Out(lastForm, out)}</strong>
        <span class="key">{lastForm}</span>
        {#if result.resolved_by}
          <span class="prov">resolved by <code>{result.resolved_by}</code></span>
        {:else}
          <span class="prov miss">no analysis</span>
        {/if}
        {#if result.static}<span class="tag">static</span>{/if}
      </div>

      {#if result.analyses?.length}
        <table class="analyses">
          <thead><tr><th>lemma</th><th>model</th><th>parse</th><th>via</th></tr></thead>
          <tbody>
            {#each result.analyses as a}
              <tr>
                <td>
                  <button class="link" onclick={() => onlemma?.(a.canonical_slp1)}>
                    {fromSlp1Out(a.canonical_slp1, out)}
                  </button>
                </td>
                <td class="mono">{a.model}</td>
                <td>{grammar(a)}</td>
                <td class="mono small">{a.resolved_by}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}

      {#if result.forms_witnesses?.length}
        <div class="witnesses">
          <h5>Form witnesses (lemma-only)</h5>
          {#each result.forms_witnesses as w}
            <button class="link" onclick={() => onlemma?.(w.canonical_slp1)}>{fromSlp1Out(w.canonical_slp1, out)}</button>
            <span class="src">({w.source})</span>
          {/each}
        </div>
      {/if}

      {#if result.segments?.length}
        <div class="segments">
          <h5>Segmented (vidyut-cheda)</h5>
          {#each result.segments as s}
            <div class="seg">
              <span class="seg-form">{fromSlp1Out(s.text, out)}</span>
              {#each s.lemmas as l}
                <button class="link" onclick={() => onlemma?.(l.lemma_slp1)}>{fromSlp1Out(l.lemma_slp1, out)}</button>
              {/each}
            </div>
          {/each}
        </div>
      {/if}

      {#if result.lemmas?.length}
        <div class="lemmas">
          <h5>Lemmas</h5>
          {#each result.lemmas as l}
            <button class="chip" class:has={l.has_entry} onclick={() => onlemma?.(l.lemma_slp1)}>
              {fromSlp1Out(l.lemma_slp1, out)}
              {#if !l.has_entry}<span class="no-entry">no entry</span>{/if}
            </button>
          {/each}
        </div>
      {/if}

      {#if result.segmentation_available === false && !result.analyses?.length && !result.forms_witnesses?.length}
        <p class="muted">No exact match. Compound/sandhi segmentation needs the
          live API (set <code>window.KOSHA_API</code>) — vidyut segmentation
          cannot run in the static browser tier.</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .reverse { }
  .row { display: flex; gap: .5rem; }
  input {
    flex: 1; font-size: 1.15rem; padding: .55rem .8rem; border: 2px solid var(--border);
    border-radius: 8px; background: var(--field-bg); color: var(--fg); box-sizing: border-box;
  }
  input:focus { outline: none; border-color: var(--accent); }
  button { font-size: 1rem; padding: 0 1.1rem; border: none; border-radius: 8px; background: var(--accent); color: #fff; cursor: pointer; }
  .hint { margin: .35rem .2rem; font-size: .8rem; color: var(--muted); }
  .badge { font-size: .65rem; font-weight: 700; background: var(--tag-bg); color: var(--tag-fg); padding: .1rem .4rem; border-radius: 4px; }
  .res { margin-top: 1rem; }
  .prov-line { display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; margin-bottom: .6rem; }
  .prov-line strong { font-size: 1.3rem; }
  .key { font-family: monospace; font-size: .8rem; color: var(--muted); }
  .prov { font-size: .85rem; color: var(--muted); }
  .prov.miss { color: #c0392b; }
  .tag { font-size: .65rem; background: var(--tag-bg); color: var(--tag-fg); padding: .1rem .4rem; border-radius: 4px; text-transform: uppercase; }
  table.analyses { border-collapse: collapse; width: 100%; margin: .5rem 0; }
  .analyses th, .analyses td { border: 1px solid var(--border); padding: .35rem .6rem; text-align: left; font-size: .95rem; }
  .analyses thead th { font-size: .72rem; color: var(--muted); background: var(--head-bg); }
  .mono { font-family: monospace; }
  .small { font-size: .78rem; }
  .link { background: none; border: none; color: var(--accent); cursor: pointer; padding: 0; font-size: inherit; text-decoration: underline; }
  h5 { margin: 1rem 0 .3rem; font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
  .src { font-size: .8rem; color: var(--muted); margin-right: .6rem; }
  .seg { display: flex; gap: .5rem; align-items: baseline; margin: .2rem 0; flex-wrap: wrap; }
  .seg-form { font-weight: 600; }
  .chip { display: inline-flex; gap: .3rem; align-items: baseline; margin: .2rem .3rem .2rem 0; padding: .25rem .6rem; border: 1px solid var(--border); border-radius: 20px; background: var(--field-bg); color: var(--fg); cursor: pointer; }
  .chip.has { border-color: var(--accent); }
  .no-entry { font-size: .65rem; color: var(--muted); }
  .muted { color: var(--muted); }
  .err { color: #c0392b; }
</style>
