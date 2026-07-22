export const meta = {
  name: 'sense-adjudicate',
  description: 'Adjudicate the residue of the H1455 sense-corpus join — assign each unassigned DCS attestation to a numbered PWG sense, gloss-grounded, out-of-set-guarded',
  whenToUse: 'Step 4 of build_sense_corpus_concordance.py — the bounded LLM tier over the residue that the deterministic locus + gloss-overlap tiers left unassigned. Paid + bounded; deferred by default in an unattended wave-1 run (residue parked to sense_review_queue.tsv). Dispatch only on an explicit operator opt-in.',
  phases: [{ title: 'Adjudicate', detail: 'one gloss-grounded judgment per residue attestation' }],
}

// -----------------------------------------------------------------------------
// Contract. This is the residue adjudicator named by IMPLEMENTATION step 4. It
// is a Claude Code Workflow script (model:'sonnet', Max-subscription runner —
// NO API key, per project_pwg_ru), NOT a standalone node program: it has no
// filesystem access, so its input arrives via `args`, prepared by
// build_sense_corpus_concordance.py --run-llm (which serialises the residue) and
// dispatched by an operator who has opted into orchestration.
//
// args: {
//   tau: 0.6,
//   items: [ {
//     headword: 'nAgadanta',
//     senses: [ { sense_id: '1a', gloss: 'Elephantenzahn, Elfenbein ...' },
//               { sense_id: '1b', gloss: 'Pflock in der Wand ...' }, ... ],
//     attestation: { lemma: 'nāgadanta', meaning: 'elephant\'s tusk; a peg ...',
//                    kwic: 'ādityaketur ... nāgadanta...' }
//   }, ... ]
// }
//
// Returns { adjudicated: [ { headword, lemma, sense_id, confidence, reason } ] }.
//
// HARD GUARD (IMPLEMENTATION step 4): the model may only return a sense_id drawn
// from the item's own `senses` list, or the sentinel '?' when none fits. Any
// out-of-set id is rejected and the row is forced to '?' with confidence 0 — a
// hallucinated sense never enters the dataset. Every returned row carries
// method='llm' downstream, so it stays auditable; confidence<tau lands in the
// review queue exactly like the deterministic tiers.
// -----------------------------------------------------------------------------

const items = (args && args.items) || []
const tau = (args && args.tau) || 0.6
if (!items.length) { log('sense-adjudicate: empty residue — nothing to do'); return { adjudicated: [] } }

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['sense_id', 'confidence', 'reason'],
  properties: {
    sense_id: { type: 'string', description: "one of the provided sense_id values, or '?' if none fits" },
    confidence: { type: 'number', minimum: 0, maximum: 1 },
    reason: { type: 'string', maxLength: 240 },
  },
}

function prompt(it) {
  const senses = it.senses.map(s => `  ${s.sense_id}: ${s.gloss}`).join('\n')
  const ids = it.senses.map(s => s.sense_id).join(', ')
  return [
    `Sanskrit lexicography — assign ONE corpus attestation of the headword «${it.headword}» to the correct numbered PWG sense.`,
    ``,
    `Numbered senses (German gloss, from Böhtlingk-Roth):`,
    senses,
    ``,
    `The attestation (DCS corpus):`,
    `  lemma: ${it.attestation.lemma}`,
    `  DCS meaning: ${it.attestation.meaning || '(none)'}`,
    `  KWIC: ${it.attestation.kwic || '(none)'}`,
    ``,
    `Return the single best sense_id (STRICTLY one of: ${ids}), a confidence in [0,1], and a one-line reason.`,
    `If no listed sense fits the attestation, return sense_id '?' with a low confidence. Never invent a sense_id outside the list.`,
  ].join('\n')
}

const results = await pipeline(
  items,
  (it, _orig, i) => agent(prompt(it), { label: `adj:${it.headword}#${i}`, phase: 'Adjudicate', schema: SCHEMA })
    .then(v => {
      const allowed = new Set(it.senses.map(s => s.sense_id))
      let sid = v && v.sense_id
      let conf = (v && typeof v.confidence === 'number') ? v.confidence : 0
      let reason = (v && v.reason) || ''
      if (!sid || (sid !== '?' && !allowed.has(sid))) {   // out-of-set guard
        reason = `out-of-set id ${JSON.stringify(sid)} rejected — forced '?'. ` + reason
        sid = '?'; conf = 0
      }
      return { headword: it.headword, lemma: it.attestation.lemma, sense_id: sid, confidence: conf, reason }
    })
    .catch(e => ({ headword: it.headword, lemma: it.attestation.lemma, sense_id: '?', confidence: 0, reason: 'agent error: ' + (e && e.message) }))
)

const adjudicated = results.filter(Boolean)
const assigned = adjudicated.filter(r => r.sense_id !== '?' && r.confidence >= tau).length
log(`sense-adjudicate: ${adjudicated.length} residue rows judged, ${assigned} assigned >= tau ${tau}, rest -> review queue`)
return { adjudicated, tau }
