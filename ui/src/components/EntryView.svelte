<script>
  import { getEntry } from '../lib/datasource.js';
  import { fromSlp1Out } from '../lib/translit.js';

  // K3-folded cross-link target: the dictionary entries for a stem, rendered
  // in-app. `onforms(slp1)` wires the "show all forms" control back into the
  // paradigm UI — the two silos become one tool (H183 §4.7 / exit check).
  let { slp1, out = 'deva', onforms } = $props();

  let entries = $state(null);
  let loading = $state(false);
  let err = $state(null);

  $effect(() => {
    const key = slp1;
    if (!key) { entries = null; return; }
    loading = true; err = null; entries = null;
    getEntry(key)
      .then((r) => { entries = r; })
      .catch((e) => { err = e.message; })
      .finally(() => { loading = false; });
  });
</script>

<div class="entry">
  <div class="entry-head">
    <h3>{fromSlp1Out(slp1, out)} <span class="key">{slp1}</span></h3>
    <button class="forms-btn" onclick={() => onforms?.(slp1)}>show all forms →</button>
  </div>

  {#if loading}
    <p class="muted">loading entry…</p>
  {:else if err}
    <p class="err">could not load entry: {err}</p>
  {:else if entries && entries.length}
    {#each entries as e}
      <article class="dict-entry">
        <div class="dict-head">
          <span class="dict-code">{e.dict?.toUpperCase()}</span>
          {#if e.scan_url}<a href={e.scan_url} target="_blank" rel="noopener">scan ↗</a>{/if}
        </div>
        <div class="rendered">{@html e.rendered_html}</div>
      </article>
    {/each}
  {:else}
    <p class="muted">No dictionary entry for this stem (it is attested in the
      inflection tables but is not a dictionary headword).</p>
  {/if}
</div>

<style>
  .entry { border: 1px solid var(--border); border-radius: 8px; padding: 1rem; background: var(--card-bg); }
  .entry-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; flex-wrap: wrap; }
  h3 { margin: 0 0 .5rem; }
  .key { font-family: monospace; font-size: .8rem; color: var(--muted); }
  .forms-btn {
    font-size: .85rem; padding: .3rem .7rem; border: 1px solid var(--accent);
    color: var(--accent); background: transparent; border-radius: 6px; cursor: pointer;
  }
  .forms-btn:hover { background: var(--hit-bg); }
  .dict-entry { border-top: 1px solid var(--border); padding: .6rem 0; }
  .dict-head { display: flex; gap: .8rem; align-items: baseline; margin-bottom: .3rem; }
  .dict-code { font-size: .7rem; font-weight: 700; background: var(--tag-bg); color: var(--tag-fg); padding: .1rem .4rem; border-radius: 4px; }
  .rendered { line-height: 1.5; overflow-wrap: anywhere; }
  .muted { color: var(--muted); }
  .err { color: #c0392b; }
</style>
