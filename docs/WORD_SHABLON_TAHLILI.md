# Word shabloni tahlili: `F:\uzbiznesss_site11\template.docx` (2026-11-10)

A4, kitob shaklida, 13 bet, 2759 so'z, makrossiz. Birinchi bet uchun alohida header (fon rasmi `image1.jpeg`, 320 KB),
qolgan betlarda "BIZNES-REJA / Bizplanai.uz" headeri va footerda bet raqami.
Eski sayt uni `modules/document_engine.py::create_word_document` bilan to'ldirgan: `{{kalit}}` almashtirish,
AI matnlari, "N-jadval" sarlavhasini qidirib jadval qo'yish, oxirida barcha ilovalar.
**Yangi backend bu shablonni ishlatmaydi**: `app/engine/word_generator.py` hujjatni noldan, boshqa tuzilmada yaratadi.

## Tuzilma
| Bet | Bo'lim | Ma'lumot manbai |
| --- | --- | --- |
| 1 | Muqova: «TASDIQLAYMAN», tashabbuskor, rahbar, sana, loyiha nomi, rasm | `tashabbuskor`, `fio`, `loyiha_nomi`, `business_image` |
| 2 | Mundarija (statik ro'yxat, bet raqamsiz) | — |
| 3 | Maxfiylik memorandumi + kredit shartlari | `tashabbuskor` x5, `kredit`, `muddat`, `imtiyoz`, `foiz` |
| 4 | 1. Tashabbuskor haqida (17 qatorli jadval) | `manzil`, `bank`, `stir`, `jshshir`, `faoliyat`, `mulk`, `fio`, `loyiha_qiymati`, `oz_mablag`, `kredit`, `muddat`, `imtiyoz`, `foiz` |
| 4-5 | 2. Loyiha maqsadi + "1-jadval. Loyiha qiymati" | `loyiha_nomi`, `tashabbuskor`, AI: `loyiha_maqsadi`; jadval: 1-ILOVA |
| 5-6 | 3.1 Bozor va marketing | `manzil`, `loyiha_nomi`, AI: `bozor_tahlili` |
| 7-8 | 3.2 SWOT: 4P jadvali (2-jadval), marketing matritsasi (3-jadval), SWOT matritsasi (4-jadval) | AI: `marketing_rejasi`, `risk_tahlili`, `swot_tahlili`; jadvallar **statik** |
| 9 | 4. Arxitektura va texnik talablar | AI: `texnik_tahlil` |
| 9 | 5. Ekologik aspekt | `manzil` |
| 9-10 | 6.1 Ish haqi + "5-jadval. Shtat jadvali" | `fio`; jadval: 5-ILOVA |
| 10 | 6.2 Daromad + "6-jadval. Daromad sxemasi", "7-jadval. Xarajatlar" | jadval: 6-ILOVA, 10-ILOVA, 11-ILOVA |
| 11 | 6.3 Kommunikatsiya + "8-jadval" | jadval: KOMMUNAL |
| 11 | 7. Xulosa | `xulosa` (NPV/ROI/IRR asosida) |
| 12-13 | 8. Moliyaviy hisob-kitoblar (ilovalar) | barcha 14 ilova, `extra_doc` |

24 xil placeholder, 47 marta. AI kalitlari (`loyiha_maqsadi`, `bozor_tahlili`, `marketing_rejasi`, `swot_tahlili`,
`risk_tahlili`, `texnik_tahlil`) yangi backenddagi `app/ai/prompts.py` bilan **aynan bir xil**.

## Texnik muammolar
1. 22 paragrafda placeholder bir nechta "run"ga bo'lingan (Word formatlash tufayli): oddiy almashtirish ishlamaydi,
   run'larni birlashtirib almashtirish kerak.
2. Jadvallar sarlavha matnini qidirib ("5-jadval" + "shtat") joylanadi: matn o'zgarsa jadval yo'qoladi.
   Ishonchliroq: sarlavha ostiga `{{jadval:5-ILOVA}}` kabi aniq belgi.
3. Bo'lim sarlavhalarining yarmi `Heading` emas, oddiy `Normal` uslubda (3.2, 4, 5, 6, 7, 8): avtomatik mundarija
   (bet raqamlari bilan) yasab bo'lmaydi.
4. `{{business_image}}` ikki joyda: muqovada va 6.2 bo'limida "7-jadval" ostida (ikkinchisi xato ko'rinadi).
   Yangi tizimda rasm yuklash yo'q.
5. Footerda ruscha "Дата отчета" qolgan.

## Mazmundagi xatolar
1. **1-bo'lim jadvalida foiz va imtiyoz almashib ketgan**: "Kredit foizi: `{{imtiyoz}}` %", "Imtiyozli davri: `{{foiz}}` oy".
   Raqamlash ham xato (1, 1, 2, 3 ...).
2. "Xizmat ko'rsatuvchi bank: ATB `{{bank}}` filiali": bank nomi "Hamkorbank ATB" bo'lsa "ATB Hamkorbank ATB filiali" chiqadi.
3. 2026 yil qattiq yozilgan (muqova sanasi, "Barcha narxlar 2026 yil holatiga").
4. 6.1: "asosiy shtatda 1 ta xodim ... qo'shimcha 2 ish o'rni" qattiq yozilgan, kiritilgan xodimlar soniga bog'lanmagan.
5. Matnlar ishlab chiqarishga moslangan ("O'zbekiston sanoat industriyasini rivojlantirish", "eksportga yo'naltirilgan",
   "100% xom ashyo mahalliy bozorda"): savdo, xizmat va qishloq xo'jaligi rejalarida noto'g'ri o'qiladi.
6. Statik jadvallar: marketing matritsasi ulushlari (0% / 90% / 10%), SWOT sanoqlari ("4 ta / 3 ta") har rejada bir xil.
7. Imlo: "rentabel1igini" (1 raqami), "iniatsiyator", "barqaror va barqaror", "maksimal darajada aylantiring",
   tutuq belgilari aralash (` ' ‘ ’), "6. moliya_xo`jalik_rejasi" va "Loyihaning_swot_tahlili" pastki chiziq bilan.
8. Bizda yo'q maydonlar: `jshshir`, pasport seriyasi, berilgan sana, IIB.

## Qarorlar (foydalanuvchi, 2026-11-10)
| Savol | Qaror |
| --- | --- |
| Asos | Word hujjati shu shablon asosida yaratiladi (hozirgi noldan yasovchi generator o'rniga) |
| Shablon xatolari | Tuzatilgan nusxa loyihaga qo'shiladi (`backend/app/engine/templates/`); F: diskdagi asl fayl o'zgarmaydi |
| Matnlar | 4 faoliyat turi uchun mos variant; AI yoqilsa AI matni qo'shiladi |
| Statik jadvallar va rasm | Faoliyat turi va kiritilgan ma'lumotdan to'ldiriladi; rasm bo'lmasa joyi olib tashlanadi |

## Amalga oshirish rejasi
1. Shablon nusxasi: foiz/imtiyoz, raqamlash, "ATB {{bank}} filiali", ruscha footer, 2026 -> `{{yil}}`, xodimlar soni ->
   `{{xodimlar_soni}}`/`{{yangi_ish_orni}}`, imlo, barcha bo'lim sarlavhalari `Heading` uslubiga, jadval joylari
   `{{jadval:N-ILOVA}}` belgilari bilan; ishlab chiqarishga xos paragraflar `{{matn:...}}` belgilariga.
2. Renderer (`word_generator.py` o'rniga): run'larni birlashtirib bir martalik almashtirish (foydalanuvchi matni qayta
   almashtirilmaydi), AI/standart matnlar paragraf bo'lib, jadvallar belgilangan joyga, 8-bo'limdan keyin 14 ilova.
3. Faoliyat turi bo'yicha matnlar va 4P, marketing matritsasi, SWOT jadvallari uchun ma'lumot lug'ati.
4. Testlar: hech bir `{{...}}` qolmasligi, har faoliyat turi uchun hujjat ochilishi, jadvallar joyida, foiz/imtiyoz to'g'ri.

## Amalga oshirildi (2026-11-10)
- `backend/scripts/build_word_template.py`: asl shablondan (`app/engine/templates/source/template_original.docx`)
  tuzatilgan `app/engine/templates/biznes_reja.docx` ni yasaydi; har bir o'zgartirish asl matnni tekshiradi.
  Shablonni o'zgartirish kerak bo'lsa: skriptni tahrirlab, qayta ishga tushiring.
- `app/engine/word_template.py`: renderer. AI matni bo'lsa shu, bo'lmasa faoliyat turiga mos standart matn.
  Matn ichidagi jadvallar: 1, 5, 6, 10-ilova va kommunal; 8-bo'limdan boshlab barcha 14 ilova albom (yotiq) varaqlarda,
  jadval sarlavhasi har betda takrorlanadi.
- `app/engine/word_texts.py`: 4 faoliyat turi uchun matnlar, 4P, marketing matritsasi segmentlari, risklar.
- Word'da tekshirildi: 4 faoliyat turining hammasi ochiladi, 19-20 bet.
- Muhim: bo'lim uzilishi uchun python-docx `sectPr.clone()` ishlatiladi (rsid atributlari bilan nusxa Word'da
  "fayl buzilgan" xatosini beradi).
- Muqova rasmi (2026-11-10): foydalanuvchi yuklaydi (`POST /v1/plans/images`, JPG/PNG, 5 MB) yoki avtomatik:
  AI loyiha nomidan inglizcha qidiruv so'zi tuzadi (AI yo'q bo'lsa faoliyat turi bo'yicha tayyor so'z), Pexels'dan
  rasm olinadi (`PEXELS_API_KEY`, bo'lmasa rasmsiz). Rasm docPr id barcha qismlar bo'yicha takrorlanmas qilinadi
  (header'dagi shakl bilan bir xil id bo'lsa Word faylni ochmaydi).
- JShShIR formada qo'lda kiritiladi (14 raqam). Pasport ma'lumotlari bo'sh chiziq bo'lib qoladi (qo'lda to'ldiriladi).
