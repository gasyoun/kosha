<script>
  import { API } from '../lib/datasource.js';
  import { fromSlp1Out } from '../lib/translit.js';

  let { out = 'deva', onselect } = $props();

  let entries = $state(null);
  let loading = $state(false);
  let err = $state(null);
  let email = $state('');
  let linkStatus = $state(null); // null | 'sending' | 'sent' | 'error'

  async function load() {
    if (!API) return;
    loading = true; err = null;
    try {
      const r = await fetch(`${API}/api/v1/history?limit=50`, { credentials: 'include' });
      if (!r.ok) throw new Error(`fetch history -> ${r.status}`);
      const j = await r.json();
      entries = j.results;
    } catch (e) {
      err = e.message;
    } finally {
      loading = false;
    }
  }

  async function clearHistory() {
    if (!API) return;
    await fetch(`${API}/api/v1/history`, { method: 'DELETE', credentials: 'include' });
    entries = [];
  }

  async function requestLink(e) {
    e.preventDefault();
    if (!API || !email.trim()) return;
    linkStatus = 'sending';
    try {
      const r = await fetch(`${API}/api/v1/auth/request-link?email=${encodeURIComponent(email.trim())}`, {
        method: 'POST', credentials: 'include',
      });
      linkStatus = r.ok ? 'sent' : 'error';
    } catch {
      linkStatus = 'error';
    }
  }

  $effect(() => { load(); });
</script>

{#if API}
  <section class="history">
    <div class="hist-head">
      <h2>Your recent searches</h2>
      {#if entries?.length}
        <button class="clear-btn" onclick={clearHistory}>clear history</button>
      {/if}
    </div>

    {#if loading}
      <p class="muted">loading…</p>
    {:else if err}
      <p class="err">could not load history: {err}</p>
    {:else if entries && entries.length}
      <ul class="hist-list">
        {#each entries as h}
          <li>
            <button class="hist-item" onclick={() => onselect?.(h.query_slp1)}>
              {fromSlp1Out(h.query_slp1, out)} <span class="key">{h.query_slp1}</span>
            </button>
            <span class="hist-meta">{h.results_total} result{h.results_total === 1 ? '' : 's'} · {new Date(h.ts).toLocaleString()}</span>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="muted">No searches yet. Your recent lookups will appear here (kept in a browser cookie, no account needed).</p>
    {/if}

    <form class="link-form" onsubmit={requestLink}>
      <label for="hist-email">Sync history across devices (email a sign-in link):</label>
      <div class="link-row">
        <input id="hist-email" type="email" bind:value={email} placeholder="you@example.com" />
        <button type="submit" disabled={linkStatus === 'sending' || !email.trim()}>send link</button>
      </div>
      {#if linkStatus === 'sent'}<p class="muted">Link requested — check your email.</p>{/if}
      {#if linkStatus === 'error'}<p class="err">Could not request a link. Try again later.</p>{/if}
    </form>
  </section>
{:else}
  <p class="muted">Search history requires the live API — unavailable in this static build.</p>
{/if}

<style>
  .hist-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; flex-wrap: wrap; margin-bottom: .8rem; }
  h2 { margin: 0; font-size: 1.2rem; }
  .clear-btn { font-size: .85rem; padding: .3rem .7rem; border: 1px solid var(--border); color: var(--muted); background: transparent; border-radius: 6px; cursor: pointer; }
  .clear-btn:hover { background: var(--hit-bg); }
  .hist-list { list-style: none; margin: 0 0 1.5rem; padding: 0; border-top: 1px solid var(--border); }
  .hist-list li { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; padding: .5rem 0; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .hist-item { border: none; background: none; color: var(--fg); font: inherit; cursor: pointer; text-align: left; padding: 0; }
  .hist-item:hover { color: var(--accent); }
  .key { font-family: monospace; font-size: .8rem; color: var(--muted); margin-left: .3rem; }
  .hist-meta { font-size: .78rem; color: var(--muted); white-space: nowrap; }
  .link-form { border-top: 1px solid var(--border); padding-top: 1rem; }
  .link-form label { display: block; font-size: .85rem; color: var(--muted); margin-bottom: .4rem; }
  .link-row { display: flex; gap: .5rem; }
  .link-row input { flex: 1; padding: .4rem .6rem; border: 1px solid var(--border); border-radius: 6px; background: var(--field-bg); color: var(--fg); }
  .link-row button { padding: .4rem .9rem; border: 1px solid var(--accent); color: var(--accent); background: transparent; border-radius: 6px; cursor: pointer; }
  .link-row button:disabled { opacity: .5; cursor: default; }
  .muted { color: var(--muted); }
  .err { color: #c0392b; }
</style>
