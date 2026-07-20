# Curation notes — beginner subhāṣita band (W-RU-b, H1279)

_Created: 19-07-2026 · Last updated: 19-07-2026_

Curated by Fable 5 (`claude-fable-5`) — the judgment step of [H1279](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1279-Fable_kosha_pedagogy-wave-ru-subhashita-reader_19.07.26.md). Every pick and every rejection below is logged: **no unlogged picks** (acceptance bar of [VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_PEDAGOGY_SURFACES.md) § W-RU-b).

## Candidate pool

The **250 lowest-difficulty** sayings of the 7,537 scored in [subhashita_difficulty.tsv](https://github.com/gasyoun/kosha/blob/main/data/subhashita/subhashita_difficulty.tsv) (difficulty 0.2841–0.4063; scorer: the W2a-reduced 2-axis variant, see [build_subhashita_difficulty.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_subhashita_difficulty.py)). Every pool member was read in full (IAST + Böhtlingk's German) and dispositioned.

## Acceptance criteria

- **C1 difficulty** — pool membership (250 lowest of 7,537).
- **C2 quotable** — a complete, memorable, self-contained thought; anthology classics preferred.
- **C3 vocabulary band fit** — high share of content lemmas inside the W1b vocab curriculum (`pct_w1b` in the difficulty TSV); soft preference, not a hard floor.
- **C4 metre resolved** — the two-tier classifier (vidyut-chandas strict vṛtta, else anuṣṭubh syllable heuristic) must name a metre; an empty tag would break the pack completeness gate. Hard gate.
- **C5 beginner content fit** — no crude misogyny, no erotica, no violence-without-frame, no proper-name mythology load as a learner's first contact with Sanskrit. Hard gate.
- **C6 translation present** — Böhtlingk's German translation must exist in F33 (the RU gloss layer, H1278, has not shipped; a card with no translation at all is not usable by the target learner). Hard gate.
- **C7 text sound** — the F33 JSONL text must be free of visible OCR/print corruption (the pack displays it verbatim). Hard gate.

**Result: 106 accepted · 144 rejected.**

## Reject-reason codes

| code | meaning | count |
|---|---|---:|
| R1 | text corrupt / OCR-damaged in the F33 source (typo, garbled word, broken sandhi) | 50 |
| R2 | content: misogynistic/demeaning — wrong first contact for a beginner deck | 15 |
| R3 | needs mythological / proper-name apparatus (epic vocatives, purāṇic allusions) | 10 |
| R4 | not self-contained (dialog fragment, fable-context-dependent, love-address) | 11 |
| R5 | duplicate / near-duplicate / thematic twin of an accepted saying (keep one) | 11 |
| R6 | metre unresolved by the two-tier classifier — an empty metre tag would fail the pack completeness check | 21 |
| R7 | erotic / anatomical content — not first-contact material | 11 |
| R8 | violent or ethically jarring without its frame | 4 |
| R9 | German translation absent in F33 (card would carry no translation layer; the RU layer, H1278, is not yet shipped) | 25 |
| R10 | quotability judgment: weaker or denser than band peers, or theme quota reached | 21 |

A known limitation, stated honestly: several **famous** sayings were rejected on C4/C6/C7 grounds (e.g. 5414 *sarve guṇāḥ kāñcanam āśrayanti*, 5104 the gold-test verse, 7739 the hope-chains verse, 5380 the mirror-and-blind verse, 6799 *santoṣas triṣu*). They are re-admission candidates once the F33 text is corrected upstream or the metre classifier learns mixed upajāti. R1 rows double as a to-fix list for the IndischeSprueche OCR layer.

## Accepted band (106 sayings, easiest first)

| # | num | difficulty | metre | pct_w1b | incipit | why |
|---:|---:|---:|---|---:|---|---|
| 1 | 3128 | 0.2841 | upagīti | 0.70 | dharmeṇa hanyate vyādhirdharmeṇa hanyate gra… | dharmeṇa anaphora drill; upagīti |
| 2 | 1249 | 0.2893 | anuṣṭubh | 1.00 | udyamena hi sidhyanti kāryāṇi na manorathaiḥ… | THE udyamena classic; sleeping lion / gazelles |
| 3 | 1727 | 0.2964 | anuṣṭubh | 0.70 | kiṃ kariṣyanti vaktāraḥ śrotā yatra na vidya… | speaker needs a hearer; washerman among naked monks |
| 4 | 3071 | 0.3076 | anuṣṭubh | 0.75 | dhaneṣu jīvitavyeṣu strīṣu bhojanavṛttiṣu… | insatiability; yātā yāsyanti yānti tense drill |
| 5 | 6168 | 0.3088 | anuṣṭubh | 0.89 | vibhave bhojane dāne tiṣṭhanti priyavādinaḥ… | fair-weather friends vs the good in misfortune |
| 6 | 6847 | 0.3103 | āryā | 0.83 | samāne śobhate prītī rājñi sevā ca śobhate… | friendship among equals; iḥ+r→ī r sandhi showcase |
| 7 | 291 | 0.3106 | anuṣṭubh | 0.89 | anityamiti jānanto na bhavanti bhavanti ca… | knowing success is uncertain; bhavanti wordplay |
| 8 | 133 | 0.3125 | anuṣṭubh | 0.88 | atithirbālakaścaiva rājā bhāryā tathaiva ca… | guest, child, king, wife: dehi dehi humour |
| 9 | 894 | 0.3141 | anuṣṭubh | 0.80 | ātmanānarthayuktena pāpe niviśate manaḥ… | harm turns the heart toward evil (MBh) |
| 10 | 4669 | 0.3247 | anuṣṭubh | 0.57 | madirāmadamatto hi kiṃ śṛṇoti ca paśyati… | wine-drunk still sees; power-drunk sees nothing |
| 11 | 1941 | 0.3259 | anuṣṭubh | 0.77 | ko 'rthaḥ putreṇa jātena yo na vidvānna dhār… | worthless son / dry cow rhetorical pair |
| 12 | 5395 | 0.3361 | anuṣṭubh | 0.75 | yasya vānnāni bhuñjīta gṛhe vāpyuṣitaṃ tathā… | gratitude to host: karmaṇā manasā vācā |
| 13 | 4166 | 0.3379 | anuṣṭubh | 0.60 | pūrṇaminduṃ yathā dṛṣṭvā nṛṇāṃ dṛṣṭiḥ prasīd… | full moon / Gaṅgā parallel structure |
| 14 | 3197 | 0.3386 | anuṣṭubh | 0.67 | na kāṣṭhe vidyate devo na pāṣāṇe na mṛnmaye… | god in the heart, not in wood or stone |
| 15 | 866 | 0.3418 | anuṣṭubh | 0.70 | āgamiṣyanti te bhāvā ye bhāvā mayi bhāvitāḥ… | MBh fatalism: the destined states will come |
| 16 | 4703 | 0.3431 | anuṣṭubh | 0.56 | mantrabhede hi ye doṣā bhavanti pṛthivīkṣitā… | leaked counsel cannot be mended (Pañcatantra) |
| 17 | 5878 | 0.3435 | anuṣṭubh | 0.75 | loke hi puruṣaḥ strī vā tathā tatkurute svay… | everyone earns what they hear — gender-even karma |
| 18 | 5209 | 0.3468 | toṭaka | 0.75 | yadi janmajarāmaraṇaṃ na bhave-/dyadi ceṣṭav… | Bhartṛhari vairāgya toṭaka: yadi janmajarāmaraṇaṃ |
| 19 | 6192 | 0.3482 | anuṣṭubh | 0.67 | viśanti sahasā mūḍhā ye 'vicārya dviṣadbalam… | rash attackers embrace sword-blades |
| 20 | 2320 | 0.3486 | anuṣṭubh | 0.70 | jaṅgamāni ca bhūtāni sthāvarāṇi ca ye narāḥ… | protect all beings like oneself |
| 21 | 584 | 0.3489 | udgīti | 0.77 | arthapatau bhūmipatau bāle vṛddhe tapo 'dhik… | whom the wise never contradict (udgīti list) |
| 22 | 435 | 0.3501 | anuṣṭubh | 0.62 | api śāstreṣu kuśalā lokācāravivarjitāḥ… | book-smart without lokācāra = laughing-stock |
| 23 | 2956 | 0.3538 | anuṣṭubh | 0.79 | deve tīrthe dvije mantre daivajñe bheṣaje gu… | yādṛśī bhāvanā tādṛśī siddhiḥ — faith shapes outcome |
| 24 | 6601 | 0.3564 | anuṣṭubh | 0.70 | ṣaṭkarṇo bhidyate mantraścatuṣkarṇo na bhidy… | counsel heard by six ears is betrayed |
| 25 | 3537 | 0.3567 | anuṣṭubh | 0.70 | nākāraṇaruṣāṃ saṅkhyā saṅkhyātāḥ kāraṇakrudh… | the five-or-six who never rage without cause |
| 26 | 6681 | 0.3585 | anuṣṭubh | 0.70 | sa jāto yena jātena yāti vaṃśaḥ samunnatim… | truly born is he who lifts his line |
| 27 | 7058 | 0.3591 | anuṣṭubh | 0.56 | sukule yojayetkanyāṃ putraṃ vidyāsu yojayet… | yojayet fourfold: daughter, son, enemy, friend |
| 28 | 2757 | 0.3592 | āryā | 0.67 | dānaṃ bhogo nāśastisro gatayo bhavanti vitta… | three fates of wealth: gift, enjoyment, loss |
| 29 | 1584 | 0.3596 | anuṣṭubh | 0.80 | kaviḥ karoti kāvyāni svādu jānāti paṇḍitaḥ… | poet makes, connoisseur tastes; husband knows, not father |
| 30 | 1714 | 0.3612 | anuṣṭubh | 0.71 | kāṣṭhapāṣāṇadhātūnāṃ kṛtvā bhāvena sevanam… | worship with faith — counterpart of accepted 3197 |
| 31 | 2434 | 0.3622 | anuṣṭubh | 0.67 | jīvitaṃ ca śarīreṇa jātyaiva saha jāyate… | life and body arise and perish together |
| 32 | 5201 | 0.3626 | anuṣṭubh | 0.75 | yadā satsaṅgarahito bhaviṣyasi bhaviṣyasi… | bhaviṣyasi bhaviṣyasi / patiṣyasi patiṣyasi yamaka gem |
| 33 | 2128 | 0.3638 | upagīti | 0.50 | guṇāḥ kurvanti dūtatvaṃ dūre 'pi vasatāṃ sat… | virtues are envoys: bees find the ketakī themselves |
| 34 | 2087 | 0.3650 | rathoddhatā | 0.50 | gamyate yadi mṛgendramandiraṃ labhyate karik… | lion's den pearl vs dog-house bones (rathoddhatā) |
| 35 | 7215 | 0.3650 | anuṣṭubh | 0.71 | strīṣu goṣu na śastrāṇi pātayedbrāhmaṇeṣu ca… | never strike women, cows, brahmins; the host's bread |
| 36 | 6674 | 0.3663 | anuṣṭubh | 0.70 | saṅgaḥ sarvātmanā tyājyaḥ sa cettyaktuṃ na ś… | satāṃ saṅgo hi bheṣajam — company of the good is medicine |
| 37 | 1952 | 0.3666 | anuṣṭubh | 0.71 | ko hi nāma kule jātaḥ sukhaleśena lobhitaḥ… | who would torment weak creatures for a scrap of comfort? |
| 38 | 5399 | 0.3669 | anuṣṭubh | 0.62 | yasya saṃsāriṇī prajñā dharmārthāvanuvartate… | the paṇḍita chooses artha over kāma |
| 39 | 2718 | 0.3684 | upagīti | 0.80 | darśane sparśane vāpi śravaṇe bhāṣaṇe 'pi vā… | definition of sneha: the heart melts |
| 40 | 7583 | 0.3686 | anuṣṭubh | 0.60 | paṭha putra kimālasyamapaṭhanbhāravāhakaḥ… | paṭha putra! learn, my son — meta-saying for learners |
| 41 | 1281 | 0.3690 | anuṣṭubh | 0.73 | upakāriṣu yaḥ sādhuḥ sādhutve tasya ko guṇaḥ… | true goodness: good to those who harm you |
| 42 | 1899 | 0.3699 | upagīti | 0.50 | ke khalu nayanavihīnāḥ paralokaṃ ye na paśya… | who are the truly blind and deaf? (upagīti Q&A) |
| 43 | 1990 | 0.3706 | anuṣṭubh | 0.67 | kva nu te 'dya pitā rājankva na te 'dya pitā… | memento mori: where is your father now, o king? |
| 44 | 975 | 0.3735 | āryā | 0.64 | ā maraṇādapi virutaṃ kurvāṇāḥ spardhayā saha… | crows cannot learn the peacock's cry (āryā) |
| 45 | 1277 | 0.3739 | anuṣṭubh | 0.44 | upakāraḥ kṛtajñeṣu pratikāreṇa yujyate… | ingratitude kills the hearts of the good |
| 46 | 3532 | 0.3748 | anuṣṭubh | 0.57 | nahyavijñātaśīlasya pradātavyaḥ pratiśrayaḥ… | bedbug and louse: vet your house-guests (Pañcatantra) |
| 47 | 2089 | 0.3765 | āryā | 0.92 | garjati śaradi na varṣati varṣati varṣāsu ni… | clouds: thunder without rain — talkers vs doers (āryā) |
| 48 | 2366 | 0.3769 | anuṣṭubh | 0.50 | jalena jāyate paṅkaṃ jalena pariśudhyati… | mud from water, cleansed by water; sin from mind |
| 49 | 1650 | 0.3780 | anuṣṭubh | 0.60 | kāma jānāmi te mūlaṃ saṅkalpātkila jāyase… | O desire, I know your root (MBh) |
| 50 | 4065 | 0.3783 | anuṣṭubh | 0.73 | pitācāryaḥ suhṛnmātā bhāryā putraḥ purohitaḥ… | a king may spare no one who strays from duty |
| 51 | 1653 | 0.3786 | anuṣṭubh | 0.71 | kāmaḥ sarvātmanā heyaḥ sa ceddhātuṃ na śakya… | the remedy for kāma: one's own wife (MBh ethic) |
| 52 | 2748 | 0.3790 | upagīti | 0.62 | dātṛtvaṃ priyavaktṛtvaṃ dhīratvamucitajñatā… | four inborn virtues no practice can teach |
| 53 | 3247 | 0.3791 | anuṣṭubh | 0.57 | na jāyate mriyate vā kvacitkiñcitkadācana… | nothing is born, nothing dies: brahma unfolds |
| 54 | 2084 | 0.3794 | anuṣṭubh | 0.92 | gandhena gāvaḥ paśyanti vedaiḥ paśyanti vai … | cows see by smell, kings by spies |
| 55 | 2057 | 0.3816 | anuṣṭubh | 1.00 | gaccha gacchasi cetkānta panthānaḥ santu te … | go, beloved — may your roads be kind (viraha gem, w1b 1.0) |
| 56 | 1420 | 0.3823 | anuṣṭubh | 0.46 | ekeṣāṃ vāci śukavadanyeṣāṃ hṛdi mūkavat… | parrot-tongue, mute-heart: where good sayings live |
| 57 | 3990 | 0.3826 | anuṣṭubh | 0.88 | parjanya iva bhūtānāmādhāraḥ pṛthivīpatiḥ… | the king as rain-cloud of the people |
| 58 | 2069 | 0.3840 | anuṣṭubh | 0.46 | gatirātmavatāṃ santaḥ santa eva satāṃ gatiḥ… | the good are everyone's refuge (chiasmus) |
| 59 | 3042 | 0.3842 | anuṣṭubh | 0.62 | dhanadhānyaprayogeṣu tathā vidyāgameṣu ca… | where shame must be dropped (Cāṇakya) |
| 60 | 3527 | 0.3845 | anuṣṭubh | 0.67 | nahīdṛśaṃ saṃvananaṃ triṣu lokeṣu vidyate… | nothing wins hearts like kindness |
| 61 | 3336 | 0.3848 | anuṣṭubh | 0.67 | na paśyati ca jātyandhaḥ kāmāndho naiva paśy… | four who cannot see: blind, lover, drunk-proud, beggar |
| 62 | 2389 | 0.3852 | anuṣṭubh | 0.70 | jātismarāṇi netrāṇi jānanti priyamapriyam… | eyes remember past lives — poetic conceit |
| 63 | 5361 | 0.3858 | anuṣṭubh | 0.62 | yasya kṛtyaṃ na jānanti mantraṃ vā mantritaṃ… | the paṇḍita: plans unknown, deeds known |
| 64 | 6414 | 0.3858 | anuṣṭubh | 0.62 | śaraṇaṃ kiṃ prapannāni viṣavanmārayanti vā… | the miser riddle: why hoard what kills like poison? |
| 65 | 5125 | 0.3867 | anuṣṭubh | 0.60 | yathā bījāṅkuraḥ sūkṣmaḥ paripuṣṭo 'bhirakṣi… | subjects are seedlings: tend them to fruit |
| 66 | 4901 | 0.3868 | anuṣṭubh | 0.67 | munerapi vanasthasya svāni karmāṇi kurvataḥ… | even a forest hermit has friends, neutrals, foes |
| 67 | 3205 | 0.3886 | anuṣṭubh | 0.67 | na kṛtasya ca kartuśca sakhyaṃ sandhīyate pu… | wronged and wrong-doer: friendship never heals |
| 68 | 5453 | 0.3893 | anuṣṭubh | 0.91 | yādṛgguṇena bhartrā strī saṃyujyeta yathāvid… | the river takes the sea's nature: yādṛś/tādṛś drill |
| 69 | 837 | 0.3895 | anuṣṭubh | 0.89 | aho bata vicitrāṇi caritāni mahātmanām… | they call Lakṣmī a straw — and bow under her weight |
| 70 | 3371 | 0.3912 | anuṣṭubh | 0.73 | na mātā śapate putraṃ na doṣaṃ labhate mahī… | mother, earth, sādhu, god: four who never harm |
| 71 | 4814 | 0.3916 | āryā | 0.46 | mānaṃ hitvā priyo bhavati krodhaṃ hitvā na ś… | give up pride, anger, desire, greed (āryā fourfold) |
| 72 | 5580 | 0.3925 | anuṣṭubh | 0.78 | ye sma kāle sumanasaḥ sarve vṛddhānupāsate… | honor the old: a lion-guarded forest |
| 73 | 2410 | 0.3926 | anuṣṭubh | 0.56 | jāyā vā syājjanitrī vā saṃbhavaḥ strīkṛto nṛ… | you owe women your existence, ingrates! |
| 74 | 7136 | 0.3927 | anuṣṭubh | 0.50 | suvyāhṛtāni dhīrāṇāṃ phalataḥ paricintya yaḥ… | ponder wise sayings → lasting fame (meta) |
| 75 | 6365 | 0.3928 | anuṣṭubh | 0.82 | śateṣu jāyate śūraḥ sahasreṣvapi paṇḍitaḥ… | a hero in hundreds; a giver maybe never |
| 76 | 1866 | 0.3938 | anuṣṭubh | 0.70 | kṛtasya karaṇaṃ nāsti mṛtasya maraṇaṃ tathā… | the done needs no doing — consolation triad |
| 77 | 4489 | 0.3942 | anuṣṭubh | 0.88 | bodhayanti na yācante bhikṣāhārā gṛhe gṛhe… | beggars do not beg — they remind |
| 78 | 485 | 0.3944 | anuṣṭubh | 0.62 | abhayaṃ sarvabhūtebhyo yo dadāti dayāparaḥ… | abhaya-dāna: the gift of safety to all beings |
| 79 | 471 | 0.3952 | anuṣṭubh | 0.91 | apriyasya prathamataḥ pariṇāme hitasya ca… | where hard truth is spoken and heard, Śrī steps in |
| 80 | 5577 | 0.3955 | anuṣṭubh | 0.75 | yeṣu kāryeṣu vidyeta sahasātiphalodayaḥ… | quick profit, later ruin: the wise decline |
| 81 | 2452 | 0.3956 | anuṣṭubh | 0.62 | jñānamantrasadācārairgauravaṃ bhajate guruḥ… | why the guru is honored; do not overstep his word |
| 82 | 1892 | 0.3960 | anuṣṭubh | 0.78 | kṛpaṇena samo dātā na kaścidbhuvi vidyate… | the miser: greatest donor — gives all, untouched |
| 83 | 2436 | 0.3963 | anuṣṭubh | 1.00 | jīvitāśā balavatī dhanāśā durbalā mama… | her answer: strong will to live, weak greed (pair of 2057) |
| 84 | 7508 | 0.3964 | vaṃśastha | 0.83 | krameṇa bhūmiḥ salilena bhidyate/krameṇa kār… | krameṇa fourfold: water splits the earth (vaṃśastha) |
| 85 | 1286 | 0.3966 | anuṣṭubh | 0.60 | upadeśo na dātavyo yādṛśe tādṛśe jane… | advice is not for everyone (Pañcatantra monkey) |
| 86 | 5370 | 0.3973 | anuṣṭubh | 0.88 | yasya tasya hi kāryasya phalitasya viśeṣataḥ… | time drinks the juice of delayed works |
| 87 | 2805 | 0.3975 | anuṣṭubh | 0.56 | divā paśyati nolūkaḥ kāko naktaṃ na paśyati… | owl by day, crow by night, the lover never |
| 88 | 4579 | 0.3977 | upagīti | 0.71 | bhāvaśuddhirmanuṣyaistu kartavyā sarvakarmas… | intention is everything: kissing wife vs daughter |
| 89 | 2763 | 0.3982 | indravajrā | 0.91 | dānena pāṇirna tu kaṅkaṇena snānena śuddhirn… | dānena pāṇiḥ — the hand adorned by giving (indravajrā) |
| 90 | 2178 | 0.3985 | anuṣṭubh | 0.62 | guruśuśrūṣayā vidyā puṣkalena dhanena vā… | three ways to knowledge — there is no fourth |
| 91 | 2978 | 0.3988 | āryā | 0.70 | daivavaśādupapanne sati vibhave yasya nāsti … | the rich fool: no enjoyment, no giving (āryā) |
| 92 | 5938 | 0.3989 | āryā | 0.40 | vapuḥ śīlaṃ kulaṃ vittaṃ vayo vidyā sanāthat… | seven things to check in a groom (āryā) |
| 93 | 2638 | 0.3996 | anuṣṭubh | 0.50 | trayaḥ sthānaṃ na muñcanti kākāḥ kāpuruṣā mṛ… | three never leave their post; three leave at insult |
| 94 | 2420 | 0.4008 | anuṣṭubh | 0.70 | jihvā dagdhā parastutyā hastau dagdhau prati… | burnt tongue, hands, heart: a life misspent |
| 95 | 5375 | 0.4017 | anuṣṭubh | 0.62 | yasya na jñāyate śīlaṃ na kulaṃ na ca saṃśra… | do not bond with the unknown — says Bṛhaspati |
| 96 | 1606 | 0.4018 | anuṣṭubh | 0.70 | kasya doṣaḥ kule nāsti vyādhinā ko na pīḍita… | whose family has no flaw? consolation questions |
| 97 | 5772 | 0.4022 | anuṣṭubh | 0.44 | rājyaṃ ca saṃpado bhogāḥ kule janma surūpatā… | the fruits of dharma (list) |
| 98 | 7126 | 0.4027 | āryāgīti | 0.50 | suramandiratarumūlanivāsaḥ śayyā bhūtalamaji… | renunciation: whom does it not make happy? (āryāgīti) |
| 99 | 2560 | 0.4032 | anuṣṭubh | 0.67 | tilamātrasukhārthaṃ hi kāmī tyajati sadvṛtta… | sesame-grain pleasure, Meru-sized pain |
| 100 | 3062 | 0.4037 | anuṣṭubh | 0.85 | dhanādhikeṣu khidyante ye 'tra mūrkhāḥ sukhā… | fools seek joy among the rich: fire for coolness |
| 101 | 4809 | 0.4038 | anuṣṭubh | 0.86 | mātrā svasrā duhitrā vā na viviktāsano bhave… | even the learned: never alone with mother, sister, daughter |
| 102 | 730 | 0.4046 | anuṣṭubh | 0.56 | aśvamedhasahasraṃ ca satyaṃ ca tulayā dhṛtam… | truth outweighs a thousand horse-sacrifices |
| 103 | 1657 | 0.4050 | anuṣṭubh | 1.00 | kāmābhibhūtaḥ krodhādvā yo mithyā pratipadya… | liars lose their allies (w1b 1.0) |
| 104 | 2133 | 0.4050 | anuṣṭubh | 0.50 | guṇānāmantaraṃ prāyastajjño jānāti netaraḥ… | the nose knows jasmine — connoisseurship |
| 105 | 4897 | 0.4051 | anuṣṭubh | 0.71 | muṇḍe muṇḍe matirbhinnā kuṇḍe kuṇḍe navaṃ pa… | muṇḍe muṇḍe matir bhinnā — every head its own mind |
| 106 | 954 | 0.4063 | anuṣṭubh | 0.64 | āpatsu mitraṃ jānīyādyuddhe śūramṛṇe śucim… | test the friend in misfortune, the hero in battle |

## Reject log (144 sayings, difficulty order — no unlogged picks)

| num | difficulty | code | note |
|---:|---:|---|---|
| 4180 | 0.2872 | R9 | no German translation in F33 (MBh pūrve vayasi yaḥ śāntaḥ) |
| 7451 | 0.3143 | R1 | kuṭila gatiḥ spacing/reading (canonical kuṭilā gatiḥ) |
| 7072 | 0.3200 | R3 | vocative Lakṣmaṇa, epic frame |
| 5759 | 0.3228 | R5+R1 | twin of accepted 2084; karṇabhyāṃ typo |
| 6646 | 0.3252 | R1 | obscure reading mā galāsīḥ |
| 3548 | 0.3259 | R5 | shares tasmād bhāvo refrain with accepted 3197; ritual vocab heavier |
| 6025 | 0.3276 | R1 | lakṣmīstayāgavanī corrupt (tyāgavatī?) |
| 5532 | 0.3308 | R1 | bārido typo (vārido) |
| 6078 | 0.3359 | R1+R2 | brāhnaṇe/dapā typos; gender-stereotype list |
| 4032 | 0.3399 | R6 | metre unresolved (30 syllables, defective pāda?) |
| 2765 | 0.3424 | R6 | metre unresolved (44 syllables, upajāti family not IDed) |
| 4609 | 0.3446 | R6 | metre unresolved (31 syllables) |
| 3283 | 0.3448 | R2 | viṣamāḥ sarvathā striyaḥ misogynist punchline |
| 4113 | 0.3479 | R8 | kill son/father/guru on the enemy side |
| 6074 | 0.3510 | R1 | yojena/satstripā corrupt |
| 4511 | 0.3519 | R3 | vocative Dhṛtarāṣṭra |
| 3389 | 0.3525 | R6 | metre unresolved (44 syllables) |
| 3717 | 0.3531 | R10 | kingly speech counsel, denser than band peers |
| 5414 | 0.3583 | R6 | famous sarve guṇāḥ kāñcanam āśrayanti, but upajāti not IDed — empty metre tag |
| 1483 | 0.3599 | R10 | political fortune-return, drier than peers |
| 5530 | 0.3613 | R1+R3 | itayāha corrupt; Nārada apparatus |
| 1789 | 0.3636 | R4 | love-address fragment (kalabhāṣiṇi) |
| 7116 | 0.3651 | R1+R6 | bhidyā corrupt; metre unresolved |
| 1748 | 0.3652 | R5 | twin of accepted 1941 |
| 6488 | 0.3653 | R1+R6 | rājaśvā corrupt; metre unresolved |
| 6278 | 0.3656 | R7+R8 | hell-torture of adulterers by iron women |
| 6565 | 0.3662 | R1 | dāyitā typo (dayitā) |
| 4996 | 0.3663 | R1 | yatnaḥ vriyate broken sandhi (kriyate?) |
| 2987 | 0.3664 | R1+R6 | first pāda garbled; 28 syllables |
| 6946 | 0.3672 | R10 | ascetic body-disgust — wrong register for first contact |
| 2255 | 0.3689 | R2 | rebirth-as-woman as karmic punishment trope |
| 7758 | 0.3693 | R9 | appendix saying, no translation in F33 |
| 6552 | 0.3711 | R3+R2 | vocative bhārata; women-as-property framing |
| 7517 | 0.3713 | R10 | obscure gaṇa-taking maxim; truncated translation |
| 561 | 0.3717 | R4+R7 | love-address lyric (manmathacūtamañjari) |
| 5493 | 0.3731 | R1 | yavanto/ajñitendriyam typos |
| 5104 | 0.3737 | R1 | tāpatāunaiḥ OCR corruption (tāpatāḍanaiḥ) in the gold-test verse |
| 3441 | 0.3741 | R2 | women made from women, no remedy against them |
| 7654 | 0.3751 | R5+R9 | duplicate of accepted 1281; no translation |
| 4358 | 0.3752 | R5 | twin of accepted 471 (rare speaker/hearer of hard truth) |
| 3857 | 0.3755 | R1+R6 | kṛtī 'pi odd; metre unresolved |
| 5688 | 0.3758 | R1 | natā jagaduttamāḥ suspicious reading |
| 7004 | 0.3762 | R6 | metre unresolved (31 syllables) |
| 4281 | 0.3763 | R10 | puṇya-reward conceit, weaker than peers |
| 4688 | 0.3763 | R1 | niśyayaṃ/prramāṇaṃ corrupt |
| 5526 | 0.3763 | R1 | rūrayātrāṃ corrupt (dūrayātrāṃ) |
| 4641 | 0.3770 | R2 | wandering woman perishes punchline |
| 4338 | 0.3771 | R10 | saṃsarga theme covered by accepted 6674; denser imagery |
| 5523 | 0.3775 | R9 | no German translation (fools and sages happy, middle suffers) |
| 6430 | 0.3777 | R1 | niyā typo (niśayā) in the moon/night gem |
| 5637 | 0.3778 | R1+R4 | parirakṣṇaṃ typo; love-address |
| 7210 | 0.3787 | R10+R2 | youth wasted staring at faces; heavy compound opener |
| 5400 | 0.3790 | R7 | virility/digestion health definition — adult register |
| 7553 | 0.3795 | R1+R6 | defective pāda (7 syllables); metre unresolved |
| 3275 | 0.3805 | R1 | yuvāpoyadhīyānas corrupt |
| 662 | 0.3806 | R5+R9 | twin of accepted 7215; no translation |
| 3237 | 0.3808 | R4 | parting-dialog fragment |
| 241 | 0.3814 | R4+R7 | love-longing address (subhru) |
| 1064 | 0.3814 | R9 | no German translation (enemies strike the careless) |
| 3557 | 0.3833 | R10 | daiva+pauruṣa knotty phrasing; translation garbled |
| 589 | 0.3840 | R10 | calculated affection, drier nīti |
| 2563 | 0.3840 | R6+R7+R9 | metre unresolved; anatomical; no translation |
| 6826 | 0.3846 | R1 | nṛpayeṣitām typo (nṛpayoṣitām) in the queens' lament |
| 2098 | 0.3848 | R10 | sun-disc piercing needs doctrinal apparatus |
| 2616 | 0.3850 | R1 | gṛhyajñānāṃ corrupt; translation truncated |
| 3276 | 0.3861 | R6 | clean twin of corrupt 3275, but metre unresolved (33 syllables) |
| 4984 | 0.3866 | R10 | toil-for-family-is-delusion, harsh ascetic take |
| 5517 | 0.3874 | R1 | svarje typo (svarge) in the anti-sacrifice zinger |
| 7835 | 0.3880 | R9 | appendix, no translation (ghana/dhana pun) |
| 263 | 0.3891 | R4 | bilasya vāṇī fable frame required |
| 1884 | 0.3891 | R10 | spy-craft metaphor stack; w1b 0.50 |
| 7739 | 0.3896 | R9 | appendix, no translation (the hope-chains verse — canonical elsewhere) |
| 4214 | 0.3898 | R1 | prajñcāṃs corrupt |
| 4125 | 0.3904 | R6 | metre unresolved (punar naro anaphora) |
| 7594 | 0.3905 | R1 | cakṣuhīno typo (cakṣurhīno) |
| 4565 | 0.3909 | R1+R10 | vībhrama corrupt; dense |
| 2658 | 0.3911 | R4 | love-address lotus-face conceit |
| 4269 | 0.3911 | R3 | vocative bhārata |
| 5618 | 0.3917 | R1+R9 | ścīddhartum corrupt; no translation |
| 2355 | 0.3920 | R1 | śīlaṃnivartanāya spacing artifact |
| 1215 | 0.3921 | R4+R7 | gopī and her two lovers fable |
| 6319 | 0.3925 | R3 | Rāma/Daśaratha names |
| 932 | 0.3929 | R9+R1 | no translation; ca apūrvāṇi hiatus |
| 5644 | 0.3940 | R1 | tenodayavyapī corrupt |
| 7798 | 0.3940 | R9+R4 | appendix riddle, no translation |
| 7522 | 0.3942 | R1 | ghaṭa bhindyāt corrupt (ghaṭaṃ) |
| 1447 | 0.3950 | R9 | no translation (kings collect the noble) |
| 3127 | 0.3954 | R5 | dharmeṇa anaphora twin of accepted 3128 |
| 2888 | 0.3957 | R10 | compound-heavy opener; relief-contrast theme covered |
| 2957 | 0.3958 | R6 | metre unresolved (31 syllables) |
| 7794 | 0.3958 | R9 | appendix, no translation (bedbug joke on the gods' beds) |
| 3951 | 0.3963 | R10 | sectarian exclusion edge |
| 2119 | 0.3965 | R1 | pṛccha hi mā construction anomalous |
| 5505 | 0.3966 | R1 | prāṇaparityāamūlyenāpi corrupt |
| 7635 | 0.3968 | R9 | appendix, no translation (give either way) |
| 267 | 0.3969 | R3+R4 | Somaśarman's father fable tag |
| 3885 | 0.3972 | R1+R9 | kathauañjaratīnāṃ corrupt; no translation |
| 5348 | 0.3973 | R6 | metre unresolved (he truly lives by whom many live) |
| 4359 | 0.3976 | R5 | twin of accepted 471 / 4358 family |
| 2386 | 0.3984 | R7 | kanakalatā/giridvaya anatomical riddle |
| 4773 | 0.3984 | R1+R9 | corrupt; no translation |
| 374 | 0.3988 | R1+R10 | parivadanasādhur reading odd |
| 7265 | 0.3997 | R7 | breasts riddle |
| 1021 | 0.3998 | R2 | pativratā ideal includes dying with the husband |
| 1839 | 0.4001 | R2+R3 | women's-fault essentialism; Nārada |
| 3684 | 0.4003 | R7 | payodhara pun |
| 4067 | 0.4003 | R2 | na strī svātantryam arhati (Manu) |
| 4964 | 0.4005 | R9 | no translation (soft cuts soft — a pity) |
| 5461 | 0.4007 | R10 | third viraha piece; theme quota (2057, 2436 kept) |
| 5168 | 0.4008 | R1+R6 | śaṛṅgaṃ typo; metre unresolved |
| 2078 | 0.4011 | R9+R10 | no translation; viraha quota |
| 4178 | 0.4013 | R1 | purve typo (pūrve) |
| 1256 | 0.4014 | R5 | twin of accepted 1249 (same lion/gazelle half) |
| 540 | 0.4015 | R4+R6 | riddle-complaint needs frame; metre unresolved |
| 3215 | 0.4015 | R1 | sidhyānti typo |
| 6564 | 0.4015 | R1 | sśruta- double-sibilant corruption |
| 2803 | 0.4018 | R10 | guest-refusal sin arithmetic, technical |
| 6799 | 0.4020 | R9 | no translation (santoṣas triṣu — a pity, canonical) |
| 5380 | 0.4024 | R1 | locanabhayāṃ/daryaṇaḥ corrupt (the mirror-and-blind gem) |
| 1488 | 0.4025 | R1 | kadā ca na spacing; nāsti āgate hiatus |
| 7561 | 0.4025 | R2 | river/woman fall pun; Greek-only translation |
| 2652 | 0.4028 | R5 | Gaṅgā theme twin of accepted 4166 |
| 884 | 0.4031 | R9 | no translation (the doctor is a father when sick) |
| 4060 | 0.4031 | R6 | sanmitra definition — vasantatilakā not IDed, empty tag |
| 2092 | 0.4032 | R8 | son dead in battle as the payoff of birth-pangs |
| 1156 | 0.4034 | R9 | no translation (wealth-anxiety ladder) |
| 2946 | 0.4034 | R2 | wife must always forgive the god-husband |
| 4566 | 0.4036 | R1+R10 | treaty jargon corrupt |
| 5387 | 0.4040 | R1 | sābhvī typo (sādhvī) |
| 7034 | 0.4041 | R9 | no translation (mind follows fate) |
| 2973 | 0.4043 | R6 | metre unresolved (30 syllables) |
| 3064 | 0.4043 | R1 | khilīkārāḥ grammar shaky |
| 3126 | 0.4044 | R5 | dharmeṇa anaphora — accepted 3128 kept |
| 3345 | 0.4044 | R9 | no translation |
| 6075 | 0.4044 | R7+R9 | erotic; Greek-only translation |
| 3584 | 0.4046 | R1+R3 | corrupt; Rāvaṇa apparatus |
| 4745 | 0.4047 | R3 | Kṛṣṇa/Kāliya myth |
| 41 | 0.4051 | R2 | man driven by women's words trope |
| 5305 | 0.4051 | R7 | waist/breasts conceit |
| 5536 | 0.4051 | R1 | vṛdhyā typo |
| 4120 | 0.4052 | R8 | kill the obstacle-maker, even a father |
| 808 | 0.4054 | R2 | women held in dependence day and night |
| 1582 | 0.4054 | R2 | witty but ends on the women-do-anything trope |
| 6305 | 0.4059 | R6+R10 | 60 syllables, unresolved, dense |

_Dr. Mārcis Gasūns_
