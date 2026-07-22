#!/usr/bin/env python
r"""Wave-2 (H1459) step 1 — the DCS text→genre map, on Renou's classification of
Sanskrit literature (MG-decided genre source, 22-07-2026).

The 219 WordSem-tagged DCS texts, bucketed into Renou-aligned genres, with two coarse
flags that drive the de-biasing:
  is_sastra           — a learned treatise (technical or scholastic), vs. Vedic/literary text
  is_technical_sastra — an empirical/scientific śāstra (rasaśāstra, āyurveda, jyotiṣa,
                        artha/kāma/dhanur/kṛṣi) — the genres whose specialist vocabulary most
                        skews sense frequency (rasa=mercury). This is the flag the "non-śāstra"
                        reweight zeroes.

Robustness: the FINE genre is best-effort, but the COARSE flags are what the reweight uses,
and they are unmistakable — every Rasa* text, every medical saṃhitā/nighaṇṭu/commentary is
is_technical_sastra regardless of which fine bucket it lands in.

Output: data/frequency/dcs_text_genre.tsv (text_name, genre, is_sastra, is_technical_sastra,
confidence). Provenance: Renou, *L'Inde classique* / *Histoire de la littérature sanskrite*
genre taxonomy; assignment curated by Opus 4.8 (claude-opus-4-8) against the text titles.

  python build_dcs_text_genre.py            # -> dcs_text_genre.tsv (reads dcs_full.sqlite text list)
"""
import argparse
import csv
import os
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DCS = os.path.normpath(os.path.join(
    HERE, '..', '..', '..', 'VisualDCS', 'src', 'DCS-data-2026', 'dcs_full.sqlite'))
OUT_TSV = os.path.join(HERE, 'dcs_text_genre.tsv')

# genre -> (is_sastra, is_technical_sastra)
GENRE_FLAGS = {
    'veda':          (False, False),   # saṃhitā / brāhmaṇa / āraṇyaka / upaniṣad / vedic-sūtra / vedāṅga
    'epic':          (False, False),
    'purana':        (False, False),
    'kavya':         (False, False),   # court poetry, śatakas, dūta/saṃdeśa poems
    'katha':         (False, False),   # narrative, fable, avadāna
    'nataka':        (False, False),   # drama
    'stotra_bhakti': (False, False),   # hymns / devotional
    'dharmasastra':  (True,  False),   # smṛti + dharmasūtra
    'darsana':       (True,  False),   # philosophy
    'vyakarana':     (True,  False),   # grammar + nirukta
    'kosa':          (True,  False),   # (non-medical) lexicon / thesaurus
    'alamkara':      (True,  False),   # poetics theory
    'tantra_yoga':   (True,  False),   # tantra / āgama / haṭhayoga (esoteric technical, not empirical-science)
    'ayurveda':      (True,  True),    # medicine + medical nighaṇṭus + medical commentaries
    'rasasastra':    (True,  True),    # alchemy / iatrochemistry
    'jyotisa':       (True,  True),    # astronomy / astrology
    'arthasastra':   (True,  True),    # artha / kāma / dhanur / śyainika / kṛṣi — applied technical śāstra
}

# Explicit assignment (curated). Titles as they appear in dcs_full.text.name.
EXPLICIT = {
    # --- epic ---
    'Rāmāyaṇa': 'epic', 'Mahābhārata': 'epic',
    # --- veda: saṃhitā / brāhmaṇa / āraṇyaka / upaniṣad / vedic sūtra / vedāṅga ---
    'Ṛgveda': 'veda', 'Atharvaveda (Paippalāda)': 'veda', 'Atharvaveda (Śaunaka)': 'veda',
    'Maitrāyaṇīsaṃhitā': 'veda', 'Taittirīyasaṃhitā': 'veda', 'Ṛgvedakhilāni': 'veda',
    'Aitareyabrāhmaṇa': 'veda', 'Pañcaviṃśabrāhmaṇa': 'veda', 'Jaiminīyabrāhmaṇa': 'veda',
    'Gopathabrāhmaṇa': 'veda', 'Śatapathabrāhmaṇa': 'veda', 'Śāṅkhāyanāraṇyaka': 'veda',
    'Bṛhadāraṇyakopaniṣad': 'veda', 'Śvetāśvataropaniṣad': 'veda', 'Nādabindūpaniṣat': 'veda',
    'Chāndogyopaniṣad': 'veda', 'Garbhopaniṣat': 'veda', "Śira'upaniṣad": 'veda',
    'Kaṭhopaniṣad': 'veda', 'Muṇḍakopaniṣad': 'veda', 'Brahmabindūpaniṣat': 'veda',
    'Amṛtabindūpaniṣat': 'veda', 'Aitareyopaniṣad': 'veda', 'Taittirīyopaniṣad': 'veda',
    'Kauṣītakyupaniṣad': 'veda',
    'Vaikhānasadharmasūtra': 'dharmasastra', 'Vārāhagṛhyasūtra': 'veda', 'Kauśikasūtra': 'veda',
    'Baudhāyanaśrautasūtra': 'veda', 'Āśvalāyanagṛhyasūtra': 'veda', 'Āpastambaśrautasūtra': 'veda',
    'Jaiminigṛhyasūtra': 'veda', 'Vaikhānasagṛhyasūtra': 'veda', 'Kāṭhakagṛhyasūtra': 'veda',
    'Baudhāyanagṛhyasūtra': 'veda', 'Āpastambagṛhyasūtra': 'veda', 'Śāṅkhāyanagṛhyasūtra': 'veda',
    'Hiraṇyakeśigṛhyasūtra': 'veda', 'Khādiragṛhyasūtra': 'veda', 'Gobhilagṛhyasūtra': 'veda',
    'Kāṭhakagṛhyasūtra': 'veda', 'Atharvaprāyaścittāni': 'veda',
    'Nirukta': 'vyakarana', 'Ṛgvedavedāṅgajyotiṣa': 'jyotisa',
    # --- purana ---
    'Matsyapurāṇa': 'purana', 'Liṅgapurāṇa': 'purana', 'Kūrmapurāṇa': 'purana',
    'Bhāgavatapurāṇa': 'purana', 'Viṣṇupurāṇa': 'purana', 'Garuḍapurāṇa': 'purana',
    'Skandapurāṇa': 'purana', 'Skandapurāṇa (Revākhaṇḍa)': 'purana', 'Śivapurāṇa': 'purana',
    'Agnipurāṇa': 'purana', 'Kālikāpurāṇa': 'purana', 'Gokarṇapurāṇasāraḥ': 'purana',
    'Varāhapurāṇa': 'purana', 'Narasiṃhapurāṇa': 'purana', 'Maṇimāhātmya': 'purana',
    # --- dharmasastra: smṛti + dharmasūtra ---
    'Manusmṛti': 'dharmasastra', 'Viṣṇusmṛti': 'dharmasastra', 'Yājñavalkyasmṛti': 'dharmasastra',
    'Parāśarasmṛtiṭīkā': 'dharmasastra', 'Nāradasmṛti': 'dharmasastra', 'Kātyāyanasmṛti': 'dharmasastra',
    'Gautamadharmasūtra': 'dharmasastra', 'Baudhāyanadharmasūtra': 'dharmasastra',
    'Parāśaradharmasaṃhitā': 'dharmasastra', 'Vṛddhayamasmṛti': 'dharmasastra',
    'Gṛhastharatnākara': 'dharmasastra', 'Haribhaktivilāsa': 'dharmasastra',
    # --- vyakarana / kosa ---
    'Aṣṭādhyāyī': 'vyakarana', 'Kāśikāvṛtti': 'vyakarana',
    'Amarakośa': 'kosa', 'Abhidhānacintāmaṇi': 'kosa', 'Trikāṇḍaśeṣa': 'kosa',
    'Nighaṇṭuśeṣa': 'kosa', 'Paramānandīyanāmamālā': 'kosa',
    # --- darsana (incl. Buddhist philosophy) ---
    'Sarvadarśanasaṃgraha': 'darsana', 'Nyāyasūtra': 'darsana', 'Nyāyabhāṣya': 'darsana',
    'Vaiśeṣikasūtra': 'darsana', 'Vaiśeṣikasūtravṛtti': 'darsana', 'Sāṃkhyakārikā': 'darsana',
    'Sāṃkhyakārikābhāṣya': 'darsana', 'Sāṃkhyatattvakaumudī': 'darsana', 'Tarkasaṃgraha': 'darsana',
    'Yogasūtra': 'darsana', 'Yogasūtrabhāṣya': 'darsana', 'Abhidharmakośa': 'darsana',
    'Pañcārthabhāṣya': 'darsana', 'Gaṇakārikā': 'darsana', 'Ratnaṭīkā': 'darsana',
    'Viṃśatikāvṛtti': 'darsana', 'Viṃśatikākārikā': 'darsana', 'Padārthacandrikā': 'darsana',
    # --- alamkara (poetics) + nataka ---
    'Kāvyālaṃkāra': 'alamkara', 'Kāvyālaṃkāravṛtti': 'alamkara', 'Kāvyādarśa': 'alamkara',
    'Nāṭyaśāstra': 'alamkara', 'Nāṭyaśāstravivṛti': 'alamkara', 'Rasikapriyā': 'alamkara',
    # --- kavya (court poetry, śatakas, dūta/saṃdeśa) ---
    'Kirātārjunīya': 'kavya', 'Ṛtusaṃhāra': 'kavya', 'Meghadūta': 'kavya',
    'Kumārasaṃbhava': 'kavya', 'Śatakatraya': 'kavya', 'Buddhacarita': 'kavya',
    'Saundarānanda': 'kavya', 'Gītagovinda': 'kavya', 'Amaruśataka': 'kavya',
    'Sūryaśataka': 'kavya', 'Sūryaśatakaṭīkā': 'kavya', 'Bhallaṭaśataka': 'kavya',
    'Āryāsaptaśatī': 'kavya', 'Caurapañcaśikā': 'kavya', 'Haṃsadūta': 'kavya',
    'Kokilasaṃdeśa': 'kavya', 'Haṃsasaṃdeśa': 'kavya', 'Bhadrabāhucarita': 'kavya',
    'Daśakumāracarita': 'kavya', 'Bodhicaryāvatāra': 'kavya', 'Smaradīpikā': 'kavya',
    'Narmamālā': 'kavya', 'Kādambarīsvīkaraṇasūtramañjarī': 'kavya',
    'Commentary on the Kādambarīsvīkaraṇasūtramañjarī': 'kavya',
    # --- katha (narrative / fable / avadāna) ---
    'Kathāsaritsāgara': 'katha', 'Bṛhatkathāślokasaṃgraha': 'katha', 'Bhāratamañjarī': 'katha',
    'Divyāvadāna': 'katha', 'Vetālapañcaviṃśatikā': 'katha', 'Avadānaśataka': 'katha',
    'Hitopadeśa': 'katha', 'Tantrākhyāyikā': 'katha', 'Śukasaptati': 'katha',
    'Lalitavistara': 'katha', 'Aṣṭasāhasrikā': 'katha', 'Saṅghabhedavastu': 'katha',
    'Śikṣāsamuccaya': 'katha', 'Laṅkāvatārasūtra': 'katha',
    # --- stotra / bhakti ---
    'Mukundamālā': 'stotra_bhakti', 'Acintyastava': 'stotra_bhakti', 'Bhairavastava': 'stotra_bhakti',
    'Aṣṭāvakragīta': 'stotra_bhakti',
    # --- arthasastra / applied technical ---
    'Arthaśāstra': 'arthasastra', 'Kāmasūtra': 'arthasastra', 'Śyainikaśāstra': 'arthasastra',
    'Dhanurveda': 'arthasastra', 'Kṛṣiparāśara': 'arthasastra', 'Ṭikanikayātrā': 'arthasastra',
    # --- jyotisa ---
    'Sūryasiddhānta': 'jyotisa',
    # --- ayurveda: saṃhitās, nighaṇṭus, commentaries ---
    'Suśrutasaṃhitā': 'ayurveda', 'Carakasaṃhitā': 'ayurveda', 'Aṣṭāṅgahṛdayasaṃhitā': 'ayurveda',
    'Aṣṭāṅgasaṃgraha': 'ayurveda', 'Bhāvaprakāśa': 'ayurveda', 'Śārṅgadharasaṃhitā': 'ayurveda',
    'Śārṅgadharasaṃhitādīpikā': 'ayurveda', 'Yogaratnākara': 'ayurveda', 'Nāḍīparīkṣā': 'ayurveda',
    'Rājanighaṇṭu': 'ayurveda', 'Kaiyadevanighaṇṭu': 'ayurveda', 'Dhanvantarinighaṇṭu': 'ayurveda',
    'Madanapālanighaṇṭu': 'ayurveda', 'Aṣṭāṅganighaṇṭu': 'ayurveda', 'Bījanighaṇṭu': 'ayurveda',
    'Āyurvedadīpikā': 'ayurveda', 'Gūḍhārthadīpikā': 'ayurveda', 'Sarvāṅgasundarā': 'ayurveda',
    'Indu (ad AHS)': 'ayurveda', 'Nibandhasaṃgraha': 'ayurveda', 'Ratnadīpikā': 'ayurveda',
    'Abhinavacintāmaṇi': 'ayurveda',
    'Ayurvedarasāyana': 'ayurveda', 'Nāḍīparīkṣā': 'ayurveda',
    # --- rasasastra: alchemy / iatrochemistry (all Rasa*; + gem/mineral parīkṣā) ---
    'Rasaratnākara': 'rasasastra', 'Rasārṇava': 'rasasastra', 'Rasaratnasamuccaya': 'rasasastra',
    'Rasendracūḍāmaṇi': 'rasasastra', 'Rasendracintāmaṇi': 'rasasastra', 'Rasaprakāśasudhākara': 'rasasastra',
    'Rasamañjarī': 'rasasastra', 'Rasahṛdayatantra': 'rasasastra', 'Rasādhyāya': 'rasasastra',
    'Rasaratnasamuccayaṭīkā': 'rasasastra', 'Rasendrasārasaṃgraha': 'rasasastra',
    'Rasaratnasamuccayabodhinī': 'rasasastra', 'Ānandakanda': 'rasasastra', 'Rasasaṃketakalikā': 'rasasastra',
    'Rasādhyāyaṭīkā': 'rasasastra', 'Rasakāmadhenu': 'rasasastra', 'Rasataraṅgiṇī': 'rasasastra',
    'Rasārṇavakalpa': 'rasasastra', 'Mugdhāvabodhinī': 'rasasastra',
    'Agastīyaratnaparīkṣā': 'rasasastra',
    # --- tantra / āgama / yoga ---
    'Sātvatatantra': 'tantra_yoga', 'Mātṛkābhedatantra': 'tantra_yoga', 'Tantrasāra': 'tantra_yoga',
    'Tantrāloka': 'tantra_yoga', 'Mṛgendratantra': 'tantra_yoga', 'Mṛgendraṭīkā': 'tantra_yoga',
    'Uḍḍāmareśvaratantra': 'tantra_yoga', 'Toḍalatantra': 'tantra_yoga', 'Mahācīnatantra': 'tantra_yoga',
    'Śāktavijñāna': 'tantra_yoga', 'Spandakārikā': 'tantra_yoga', 'Spandakārikānirṇaya': 'tantra_yoga',
    'Śivasūtra': 'tantra_yoga', 'Śivasūtravārtika': 'tantra_yoga', 'Vātūlanāthasūtravṛtti': 'tantra_yoga',
    'Pāśupatasūtra': 'tantra_yoga', 'Devīkālottarāgama': 'tantra_yoga', 'Paraśurāmakalpasūtra': 'tantra_yoga',
    'Haṭhayogapradīpikā': 'tantra_yoga', 'Gheraṇḍasaṃhitā': 'tantra_yoga', 'Gorakṣaśataka': 'tantra_yoga',
    'Kṛṣṇāmṛtamahārṇava': 'tantra_yoga', 'Amaraughaśāsana': 'tantra_yoga',
    'Janmamaraṇavicāra': 'tantra_yoga', 'Nāḍīparīkṣā': 'ayurveda',
}

# Regex fallbacks (only used when a title is not in EXPLICIT). First match wins.
PATTERNS = [
    (re.compile(r'[Rr]as(a|e|ā|endra)'), 'rasasastra'),
    (re.compile(r'nighaṇṭu'), 'ayurveda'),
    (re.compile(r'saṃhitā$'), 'ayurveda'),         # medical saṃhitā (Vedic ones are in EXPLICIT)
    (re.compile(r'purāṇa'), 'purana'),
    (re.compile(r'(upaniṣ|brāhmaṇa|āraṇyaka|saṃhitā.*veda)'), 'veda'),
    (re.compile(r'(gṛhyasūtra|śrautasūtra)'), 'veda'),
    (re.compile(r'(dharmasūtra|smṛti)'), 'dharmasastra'),
    (re.compile(r'(tantra|āgama)'), 'tantra_yoga'),
    (re.compile(r'(śataka|dūta|saṃdeśa|carita|kāvya)'), 'kavya'),
]


def classify(name):
    if name in EXPLICIT:
        return EXPLICIT[name], 'curated'
    for rx, g in PATTERNS:
        if rx.search(name):
            return g, 'pattern'
    return 'uncertain', 'unmatched'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dcs', default=DEFAULT_DCS)
    ap.add_argument('--out', default=OUT_TSV)
    args = ap.parse_args()

    con = sqlite3.connect(args.dcs)
    rows = con.execute("""SELECT tx.name, COUNT(*) AS ws
                          FROM token t JOIN sentence s ON t.sentence_id=s.id
                          JOIN chapter ch ON s.chapter_id=ch.chapter_id
                          JOIN text tx ON ch.text_id=tx.text_id
                          WHERE t.m_wordsem IS NOT NULL AND t.m_wordsem!=''
                          GROUP BY tx.text_id ORDER BY ws DESC""").fetchall()
    con.close()

    out, by_genre, tok_by_flag = [], {}, {'literary': 0, 'sastra': 0, 'technical': 0}
    uncertain, uncertain_tok = [], 0
    total_tok = sum(w for _n, w in rows)
    for name, ws in rows:
        genre, conf = classify(name)
        is_s, is_t = GENRE_FLAGS.get(genre, (False, False))
        out.append({'text_name': name, 'ws_tokens': ws, 'genre': genre,
                    'is_sastra': int(is_s), 'is_technical_sastra': int(is_t),
                    'confidence': conf})
        by_genre[genre] = by_genre.get(genre, 0) + ws
        if genre == 'uncertain':
            uncertain.append((name, ws)); uncertain_tok += ws
        if is_t:
            tok_by_flag['technical'] += ws
        if is_s:
            tok_by_flag['sastra'] += ws
        else:
            tok_by_flag['literary'] += ws

    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['text_name', 'ws_tokens', 'genre',
                                          'is_sastra', 'is_technical_sastra', 'confidence'],
                           delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(out)

    print(f"=== dcs_text_genre.tsv — {len(out)} texts, {total_tok:,} WordSem tokens ===")
    print("token mass by genre:")
    for g, t in sorted(by_genre.items(), key=lambda x: -x[1]):
        fs, ft = GENRE_FLAGS.get(g, (False, False))
        tag = ' [TECHNICAL]' if ft else (' [śāstra]' if fs else '')
        print(f"  {g:16} {t:>8,} ({t/total_tok:5.1%}){tag}")
    print(f"\ncoarse split (token mass):")
    print(f"  literary/vedic (non-śāstra): {tok_by_flag['literary']:,} ({tok_by_flag['literary']/total_tok:.1%})")
    print(f"  śāstra:                      {tok_by_flag['sastra']:,} ({tok_by_flag['sastra']/total_tok:.1%})")
    print(f"  …of which TECHNICAL śāstra:  {tok_by_flag['technical']:,} ({tok_by_flag['technical']/total_tok:.1%})")
    print(f"\nuncertain: {len(uncertain)} texts, {uncertain_tok:,} tokens ({uncertain_tok/total_tok:.1%})")
    for n, w in uncertain[:15]:
        print(f"    ? {n} ({w})")
    print(f"-> {args.out}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
