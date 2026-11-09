"""Biznes-reja bo'limlari uchun promptlar (eski saytdagi ai_engine.py asosida qisqartirilgan)."""

SYSTEM = ("Siz O'zbekiston banklari kredit qo'mitasi uchun biznes-reja yozadigan tajribali iqtisodchisiz. "
          "Faqat o'zbek tilida, lotin alifbosida yozing. Sarlavha, raqamlash va markdown ishlatmang. "
          "Rasmiy, dalillarga asoslangan uslubda 400-600 so'z yozing. Berilmagan raqamlarni to'qimang.")

SECTIONS: list[tuple[str, str, str]] = [
    ("loyiha_maqsadi", "Loyihaning maqsadi va dolzarbligi",
     "loyihaning umumiy tavsifi, asosiy maqsadi, hududiy va ijtimoiy-iqtisodiy dolzarbligi, yaratiladigan ish o'rinlari"),
    ("bozor_tahlili", "Bozor tahlili",
     "mahsulot/xizmatga talab, maqsadli mijozlar, raqobat muhiti, narx siyosati va bozordagi o'rin"),
    ("marketing_rejasi", "Marketing rejasi",
     "sotish kanallari, reklama va targ'ibot, mijozlarni jalb qilish va ushlab qolish, sotuv hajmini oshirish bosqichlari"),
    ("swot_tahlili", "SWOT tahlili",
     "kuchli va zaif tomonlar, imkoniyatlar va tahdidlar; har biri loyihaning aniq sharoitiga bog'langan holda"),
    ("risk_tahlili", "Risklar va ularni boshqarish",
     "moliyaviy, bozor, operatsion va tashqi risklar hamda har biri uchun kamaytirish choralari"),
    ("texnik_tahlil", "Texnik va tashkiliy tahlil",
     "ishlab chiqarish yoki xizmat jarayoni, uskunalar, joylashuv, xodimlar tuzilmasi va ishga tushirish bosqichlari"),
]


def _money(v) -> str:
    try:
        return f"{float(v):,.0f}".replace(",", " ") + " so'm"
    except (TypeError, ValueError):
        return "—"


def build_prompt(topic: str, ctx: dict, ind: dict) -> str:
    return (
        f"Loyiha: «{ctx.get('loyiha_nomi') or 'Investitsiya loyihasi'}» "
        f"({ctx.get('faoliyat_turi_nomi') or ''}).\n"
        f"Tashabbuskor: {ctx.get('tashabbuskor') or '—'}. Joylashuv: {ctx.get('manzil') or 'O‘zbekiston'}.\n"
        f"Mahsulot: {ctx.get('mahsulot') or '—'}, yillik hajm {ctx.get('hajm') or '—'} {ctx.get('olchov') or ''}, "
        f"narx {_money(ctx.get('narx'))}.\n"
        f"Loyiha qiymati {_money(ind.get('loyiha_qiymati'))}, o'z mablag'i {_money(ind.get('oz_mablag'))}, "
        f"kredit {_money(ind.get('kredit'))} ({ctx.get('foiz') or '—'}% yillik, {ctx.get('muddat') or '—'} oy).\n"
        f"NPV {_money(ind.get('npv'))}, IRR {ind.get('irr', '—')}%, qoplash muddati {ind.get('payback', '—')} yil, "
        f"10 yillik sof foyda {_money(ind.get('jami_sof_foyda'))}.\n\n"
        f"Shu loyiha uchun quyidagini yoriting: {topic}."
    )
