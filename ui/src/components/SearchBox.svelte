<script>
  import { toSlp1Auto, detectScheme, fromSlp1Out } from '../lib/translit.js';
  import { prefixSuggest } from '../lib/autocomplete.js';
  import { loadLemmaIndex } from '../lib/datasource.js';
  import { parseQuery } from '../lib/query.js';

  // onselect(slp1) fires when a suggestion is chosen or bare Enter is pressed.
  // oncommand(kind, value) fires for the P5 operators `root:`/`sandhi:` — the
  // raw text is inspected BEFORE transliteration so the operator prefix is not
  // mangled (P5 §4). Callers that don't pass oncommand keep the old behaviour.
  let { onselect, oncommand, placeholder = 'rāma · राम · rAma · root:BU · sandhi:tattvamasi' } = $props();

  // Returns true if the raw text was an operator and was dispatched.
  function dispatchOperator() {
    const q = parseQuery(text);
    if ((q.kind === 'root' || q.kind === 'sandhi') && oncommand) {
      open = false;
      oncommand(q.kind, q.value);
      return true;
    }
    return false;
  }

  let text = $state('');
  let suggestions = $state([]);
  let open = $state(false);
  let active = $state(-1);
  let index = null;
  let timer;

  const scheme = $derived(text ? detectScheme(text) : null);
  const slp1 = $derived.by(() => {
    if (!text.trim()) return '';
    try { return toSlp1Auto(text.trim(), 'auto'); } catch { return ''; }
  });
  // Live transliteration preview of whatever was typed, normalised to SLP1
  // then shown in the other two scripts (K2b-4 auto-detect).
  const preview = $derived.by(() => {
    if (!slp1) return null;
    return { iast: fromSlp1Out(slp1, 'iast'), deva: fromSlp1Out(slp1, 'deva') };
  });

  async function ensureIndex() {
    if (!index) index = await loadLemmaIndex();
    return index;
  }

  function onInput() {
    clearTimeout(timer);
    timer = setTimeout(refresh, 120); // debounce; 323k index stays responsive
  }

  async function refresh() {
    const q = slp1;
    if (!q) { suggestions = []; open = false; return; }
    await ensureIndex();
    suggestions = prefixSuggest(index, q, 20);
    active = -1;
    open = suggestions.length > 0;
  }

  function choose(s) {
    text = s.iast;
    open = false;
    onselect?.(s.slp1);
  }

  function onKey(e) {
    if (!open) {
      if (e.key === 'Enter') {
        if (dispatchOperator()) return;
        if (slp1) onselect?.(slp1);
      }
      return;
    }
    if (e.key === 'ArrowDown') { active = Math.min(active + 1, suggestions.length - 1); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { active = Math.max(active - 1, 0); e.preventDefault(); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      if (active >= 0) choose(suggestions[active]);
      else if (dispatchOperator()) return;
      else if (slp1) { open = false; onselect?.(slp1); }
    } else if (e.key === 'Escape') { open = false; }
  }
</script>

<div class="box">
  <input
    type="text"
    bind:value={text}
    oninput={onInput}
    onkeydown={onKey}
    onfocus={() => { if (suggestions.length) open = true; }}
    {placeholder}
    autocomplete="off"
    autocapitalize="off"
    spellcheck="false"
    aria-label="Sanskrit input (Devanagari, IAST or SLP1 — auto-detected)"
  />

  {#if preview && scheme}
    <div class="preview">
      <span class="badge">{scheme.toUpperCase()}</span>
      <span class="deva">{preview.deva}</span>
      <span class="iast">{preview.iast}</span>
      <span class="slp1">{slp1}</span>
    </div>
  {/if}

  {#if open}
    <ul class="suggest" role="listbox">
      {#each suggestions as s, i}
        <li
          role="option"
          aria-selected={i === active}
          class:active={i === active}
          onmousedown={() => choose(s)}
        >
          <span class="s-deva">{fromSlp1Out(s.slp1, 'deva')}</span>
          <span class="s-iast">{s.iast}</span>
          <span class="s-dicts">{s.dicts}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .box { position: relative; }
  input {
    width: 100%; box-sizing: border-box; font-size: 1.3rem; padding: .6rem .8rem;
    border: 2px solid var(--border); border-radius: 8px; background: var(--field-bg);
    color: var(--fg);
  }
  input:focus { outline: none; border-color: var(--accent); }
  .preview {
    display: flex; gap: .7rem; align-items: baseline; flex-wrap: wrap;
    margin: .4rem .2rem; font-size: .95rem;
  }
  .badge {
    font-size: .65rem; font-weight: 700; background: var(--tag-bg); color: var(--tag-fg);
    padding: .1rem .4rem; border-radius: 4px;
  }
  .preview .deva { font-size: 1.15rem; }
  .preview .iast { color: var(--muted); }
  .preview .slp1 { font-family: monospace; color: var(--muted); font-size: .85rem; }
  .suggest {
    position: absolute; z-index: 10; left: 0; right: 0; margin: .2rem 0 0; padding: 0;
    list-style: none; max-height: 20rem; overflow-y: auto; background: var(--field-bg);
    border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.18);
  }
  .suggest li {
    display: flex; gap: .7rem; align-items: baseline; padding: .4rem .7rem; cursor: pointer;
  }
  .suggest li.active, .suggest li:hover { background: var(--hit-bg); }
  .s-deva { font-size: 1.1rem; min-width: 6rem; }
  .s-iast { color: var(--muted); flex: 1; }
  .s-dicts { font-size: .7rem; color: var(--muted); font-family: monospace; }
</style>
