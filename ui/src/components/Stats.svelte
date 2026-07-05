<script>
  import { API } from '../lib/datasource.js';
  import { fromSlp1Out } from '../lib/translit.js';
  import Chart from 'chart.js/auto';

  let { out = 'deva' } = $props();

  let summary = $state(null);
  let timeseries = $state(null);
  let top = $state(null);
  let err = $state(null);
  let canvasEl = $state(null);
  let chart = null;

  async function getJson(path) {
    const r = await fetch(`${API}${path}`);
    if (!r.ok) throw new Error(`fetch ${path} -> ${r.status}`);
    return r.json();
  }

  async function load() {
    if (!API) return;
    err = null;
    try {
      [summary, timeseries, top] = await Promise.all([
        getJson('/api/v1/stats/summary'),
        getJson('/api/v1/stats/timeseries?interval=day&days=30'),
        getJson('/api/v1/stats/top?limit=20'),
      ]);
    } catch (e) {
      err = e.message;
    }
  }

  $effect(() => { load(); });

  $effect(() => {
    if (!canvasEl || !timeseries) return;
    chart?.destroy();
    chart = new Chart(canvasEl, {
      type: 'line',
      data: {
        labels: timeseries.points.map((p) => p.day ?? p.week),
        datasets: [{
          label: 'searches / day',
          data: timeseries.points.map((p) => p.count),
          borderColor: '#7b2d26',
          backgroundColor: 'rgba(123,45,38,.15)',
          tension: .25,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    });
    return () => chart?.destroy();
  });
</script>

{#if API}
  <section class="stats">
    <h2>Search activity</h2>
    {#if err}
      <p class="err">could not load stats: {err}</p>
    {:else if !summary}
      <p class="muted">loading…</p>
    {:else}
      <div class="summary-row">
        <div class="stat-card"><span class="n">{summary.total_searches}</span><span class="l">total searches</span></div>
        <div class="stat-card"><span class="n">{summary.unique_visitors}</span><span class="l">unique visitors</span></div>
      </div>

      <div class="chart-wrap">
        <canvas bind:this={canvasEl}></canvas>
      </div>

      {#if top?.results?.length}
        <table class="top-table">
          <thead><tr><th>term</th><th>searches</th></tr></thead>
          <tbody>
            {#each top.results as t}
              <tr>
                <td>{fromSlp1Out(t.query_slp1, out)} <span class="key">{t.query_slp1}</span></td>
                <td>{t.count}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    {/if}
  </section>
{:else}
  <p class="muted">Aggregate stats require the live API — unavailable in this static build.</p>
{/if}

<style>
  h2 { margin: 0 0 .8rem; font-size: 1.2rem; }
  .summary-row { display: flex; gap: 1rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
  .stat-card { border: 1px solid var(--border); border-radius: 8px; padding: .7rem 1.2rem; background: var(--card-bg); display: flex; flex-direction: column; }
  .stat-card .n { font-size: 1.5rem; font-weight: 700; }
  .stat-card .l { font-size: .78rem; color: var(--muted); }
  .chart-wrap { max-width: 40rem; margin-bottom: 1.5rem; }
  .top-table { width: 100%; border-collapse: collapse; }
  .top-table th, .top-table td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid var(--border); }
  .top-table th { font-size: .78rem; text-transform: uppercase; color: var(--muted); }
  .key { font-family: monospace; font-size: .78rem; color: var(--muted); margin-left: .3rem; }
  .muted { color: var(--muted); }
  .err { color: #c0392b; }
</style>
