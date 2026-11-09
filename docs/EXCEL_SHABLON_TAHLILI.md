# "Asosiy shablon npv 10 yillik.xls" tahlili (2026-11-10)

Manba: `G:\Asosiy shablon npv 10 yillik.xls` (makrossiz, 14 varaq). Python nusxasi Excel bilan 85 katakda
tiyinigacha mos keldi (NPV, IRR, foyda, tannarx, pul oqimi, zararsizlik, PI).

## Varaqlar va formulalar

| Varaq (ilova) | Mantiq |
| --- | --- |
| ProjCost (1) | Kredit -> asosiy vositalar (E4); o'z mablag' -> asosiy vositalar (D5); aylanma kapital (D8); sug'urta; "kredit olish xarajatlari" |
| Share of Costs (3) | Kredit olish xarajati = (kredit + kredit) x 1% (amalda kreditning 2%); o'z mablag' jami = asosiy + aylanma + moliyaviy |
| FinPlan (2) | O'z mablag' va kredit ulushi |
| Depreciate (4) | Barcha asosiy vositalar / 10, har yili teng (to'g'ri chiziqli). D5 dagi 15% ishlatilmaydi |
| Labour (5) | Rahbar, ishchi, yangi ishchi: soni x maosh x 12; ijtimoiy soliq 12%. Kommunal: elektr (yillik kVt x 900) + boshqa kommunal (yillik summa) |
| ProdPlan (6) | Hajm x koeffitsient x narx (6 tagacha mahsulot qatori). Quvvat: 75, 77, 80, 82, 85, 90, 92, 95, 100, 100% |
| Loans (8-9) | Oylik, 120 oy, 24 oy imtiyoz (faqat foiz), keyin asosiy qarz / 96 teng (differensial), foiz 18% qoldiqqa |
| Taxes (7) | Faqat "Yagona soliq to'lovi" = 12% x sotish tushumi |
| CostTotal (10) | Har xarajat: to'liq summa (100% quvvatda) va doimiy ulushi. Bevosita = tushumning 1% (80% doimiy); kommunal (70%); amortizatsiya (100%); ishchi ish haqi va ijtimoiy (0%, to'liq o'zgaruvchan); rahbar (100%); boshqa ma'muriy 0,2% (50%); texnik xizmat = amortizatsiyaning 1% (70%); marketing 0,2% (70%); kutilmagan 0,2% (50%). Zararsizlik = doimiy / (tushum - o'zgaruvchan) |
| CostSold (11) | Har yil: doimiy + o'zgaruvchan x quvvat. Tannarx = bevosita + ishchi + ijtimoiy + kommunal + amortizatsiya; davr xarajatlari = rahbar + ijtimoiy + kutilmagan + texnik + marketing + boshqa ma'muriy |
| ProfLoss (12) | Yalpi = tushum - tannarx; operatsion = yalpi - ma'muriy - marketing - boshqa; sof = operatsion - foiz - soliq |
| CashFlow (13) | Operatsion CF = yalpi - marketing - ma'muriy - boshqa + amortizatsiya; sof CF = operatsion - foiz - soliq; asosiy qarz alohida qatorda |
| npv1 (14) | NPV va IRR **operatsion CF** (foiz va soliqdan oldin) bo'yicha, 14%, boshlang'ich = loyiha qiymati. Natija sifatida **5-yil** NPV/IRR olinadi; PI = NPV(5 yil) / investitsiya; qoplash muddati "3 yil" matn sifatida qo'lda yozilgan |

## Excel ichidagi xatolar (tuzatish yoki saqlash: foydalanuvchi qarori)
1. `ProjCost!D13` aylanma kapital va moliyaviy xarajatlarni 2 marta qo'shadi (namunada +2 000 000).
2. `CashFlow!I22:M22` asosiy qarz 25 000 000 qo'lda yozilgan; kredit jadvali bo'yicha 12 500 000. Jami 162,5 mln qaytariladi (kredit 100 mln).
3. `ProjCost!G13` ulushlar yig'indisi 98,6% (100% emas); `FinPlan!E9` = -2 000 000 (moliyaviy xarajat moliyalashtirilmagan).
4. PI = NPV / investitsiya (odatda PV / investitsiya).
5. Qoplash muddati va DPP hisoblanmaydi, "3 yil" qo'lda yozilgan.
6. Ruscha eski bloklar (`#REF!`), `Loans 2` varag'i ishlatilmaydi.

## Hozirgi yadro (`app/engine/financial_engine.py`) bilan asosiy farqlar
| | Excel | Yadro |
| --- | --- | --- |
| Bevosita xarajat (tovar/xomashyo) | tushumning 1% | birlik narxi x hajm yoki tushumning 25-60% |
| Quvvat | 75 -> 100% | 50 -> 100% |
| Amortizatsiya | asosiy vositalar / 10 | 15% stavka |
| Soliq | 12% tushumdan | YTT 4% yoki MCHJ 12% + ijtimoiy soliq yana bir marta (ish haqida ham bor: ikki marta hisob) |
| NPV pul oqimi | operatsion CF (foiz, soliqdan oldin) | sof CF (foiz, soliq va asosiy qarzdan keyin) |
| NPV davri | 5 yil | 10 yil |
| Diskont | 14% | 13,5% |
| Xarajatlar | doimiy/o'zgaruvchan ulush bilan | har biri o'z koeffitsienti bilan |

Bir xil kirishda: Excel NPV(10) = 955,6 mln, IRR 125%; yadro NPV = -815,9 mln, IRR 0%.
Asosiy sabab: savdo uchun yadro tovar tannarxini tushumning 60% deb oladi, Excel 1%.

## Kodga o'tkazishda qabul qilingan qarorlar (foydalanuvchi, 2026-11-10)
| Savol | Qaror |
| --- | --- |
| Bevosita xarajat | `xomashyo_narx` (1 birlik) kiritilsa: birlik x hajm; aks holda `tannarx_ulushi` yoki faoliyat turiga qarab (savdo 75%, ishlab chiqarish 55%, qishloq xo'jaligi 40%, xizmat 15%). Har doim sotuvga to'liq proporsional. Shablondagi 1% (80% doimiy) real emas deb almashtirildi (foydalanuvchi: "o'zing bilib o'zgartir") |
| NPV/IRR oqimi | Sof pul oqimi: operatsion oqim minus soliq va kredit foizi (Excel'da ulardan oldin edi). Avval Excel usuli tanlangan, so'ng natija sof foyda bilan mos kelmagani uchun foydalanuvchi shunga o'zgartirdi. PP va DPP ham shu oqimdan |
| NPV davri | 10 yil (jadvalda har yil uchun NPV ham bor) |
| Excel xatolari | Tuzatildi (1, 2, 5); PI = PV / investitsiya (4) |
| Soliq | Tanlov qoladi: YTT 4% yoki MCHJ 12% (shablon = 12%) |
| Mahsulotlar | 6 tagacha (`mahsulotlar`) |
| Quvvat va diskont | Standart shablondagi, `quvvat` va `diskont` bilan o'zgartirsa bo'ladi |
| Kredit olish xarajati | Kreditning 2% (ataylab) |

O'zim qilgan mayda qarorlar (shablonda yo'q, eski formadan qolgan maydonlar):
- Kommunal: `elektr`, `gaz`, `suv`, `oqava` oylik miqdor x tarif (900, 1500, 3000, 2000) x 12 + `boshqa_kommunal`; 70% doimiy (shablon).
- Ijara (`dokon_ijarasi`, `joy_ijarasi` oylik, `yer_ijarasi` yillik): 100% doimiy, davr xarajatlarida alohida qator.
- `transport_xarajat` (oylik): 70% doimiy, davr xarajatlarida alohida qator.
- `urug_yem_narx`, `texnika_xarajat` (yillik): tannarxda alohida qator, to'liq o'zgaruvchan.
- Annuitet kredit tanlovi saqlandi (standart: differensial).
- O'z mablag'i: avval aylanma kapital, sug'urta va 2% kredit xarajati ayriladi, qolgani asosiy vositalarga.

Moslik testi: `backend/tests/test_template_model.py`: `tannarx_ulushi=1` bilan yillik sof foyda, tannarx, operatsion CF, NPV va zararsizlik Excel bilan 0,01 so'm aniqlikda; yagona farq 1% ning doimiy qismi (3,84 mln x (1 - quvvat)), testda aniq hisoblangan.
