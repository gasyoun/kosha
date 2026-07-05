<script>
  import { fromSlp1Out } from '../lib/translit.js';

  // props: one paradigm model (nominal or verb), the output script, and the
  // form the user searched by (highlighted if it appears in the grid).
  let { model, out = 'deva', highlight = null } = $props();

  const CASE_LABEL = {
    nom: 'Nominative', acc: 'Accusative', instr: 'Instrumental',
    dat: 'Dative', abl: 'Ablative', gen: 'Genitive', loc: 'Locative',
    voc: 'Vocative',
  };
  const NUM_LABEL = { sg: 'Singular', du: 'Dual', pl: 'Plural' };
  const PERS_LABEL = { '1': '1st', '2': '2nd', '3': '3rd' };
  const VOICE_LABEL = { active: 'Parasmaipada', middle: 'Ātmanepada', passive: 'Passive' };
  const TENSE_LABEL = {
    pre: 'Present', ipf: 'Imperfect', opt: 'Optative', ipv: 'Imperative',
  };

  function render(forms) {
    if (!forms || !forms.length) return '';
    return forms.map((f) => fromSlp1Out(f, out)).join(' / ');
  }
  function isHit(forms) {
    return highlight && forms && forms.includes(highlight);
  }
</script>

<div class="paradigm">
  <h4>
    <span class="model">{model.model}</span>
    {#if model.gender}<span class="tag">{model.gender}</span>{/if}
    <span class="tag">{model.type}</span>
  </h4>

  <div class="grid-scroll">
    {#if model.type === 'verb'}
      {#each Object.entries(model.vcells) as [voice, tenses]}
        {#each Object.entries(tenses) as [tense, persons]}
          <table>
            <caption>{VOICE_LABEL[voice] ?? voice} · {TENSE_LABEL[tense] ?? tense}</caption>
            <thead>
              <tr><th></th>{#each model.numbers as n}<th>{NUM_LABEL[n] ?? n}</th>{/each}</tr>
            </thead>
            <tbody>
              {#each Object.entries(persons) as [person, byNum]}
                <tr>
                  <th class="rowhead">{PERS_LABEL[person] ?? person}</th>
                  {#each model.numbers as n}
                    <td class:hit={isHit(byNum[n])}>{render(byNum[n])}</td>
                  {/each}
                </tr>
              {/each}
            </tbody>
          </table>
        {/each}
      {/each}
    {:else}
      <table>
        <thead>
          <tr><th></th>{#each model.numbers as n}<th>{NUM_LABEL[n] ?? n}</th>{/each}</tr>
        </thead>
        <tbody>
          {#each model.cases as c}
            <tr>
              <th class="rowhead">{CASE_LABEL[c] ?? c}</th>
              {#each model.numbers as n}
                <td class:hit={isHit(model.cells[c]?.[n])}>{render(model.cells[c]?.[n])}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>

<style>
  .paradigm { margin: 0 0 1.5rem; }
  h4 { margin: 0 0 .4rem; font-size: 1rem; display: flex; gap: .5rem; align-items: baseline; }
  .model { font-family: monospace; color: var(--accent); }
  .tag {
    font-size: .7rem; font-weight: 500; padding: .05rem .4rem; border-radius: 4px;
    background: var(--tag-bg); color: var(--tag-fg); text-transform: uppercase;
    letter-spacing: .03em;
  }
  /* Mobile: the grid scrolls inside its own container — never forces the body
     to scroll horizontally (H183 exit check). */
  .grid-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  table { border-collapse: collapse; margin: 0 0 1rem; min-width: max-content; }
  caption { text-align: left; font-size: .8rem; color: var(--muted); padding: .2rem 0; }
  th, td {
    border: 1px solid var(--border); padding: .35rem .7rem; text-align: left;
    white-space: nowrap; font-size: 1.05rem;
  }
  thead th, .rowhead {
    font-size: .78rem; font-weight: 600; color: var(--muted);
    background: var(--head-bg); text-transform: none;
  }
  .rowhead { text-align: right; }
  td.hit { background: var(--hit-bg); font-weight: 700; }
</style>
