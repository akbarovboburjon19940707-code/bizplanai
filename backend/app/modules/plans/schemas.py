from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Money = Field(default=None, ge=0, le=10**13)
Count = Field(default=None, ge=0, le=100_000)


class ProductIn(BaseModel):
    """Bitta mahsulot/xizmat qatori (Excel shablonidagi ProdPlan qatori)."""
    model_config = ConfigDict(extra="forbid")

    nomi: str = Field(min_length=1, max_length=200)
    hajm: float = Field(gt=0, le=10**12)  # yillik hajm, to'liq quvvatda
    narx: float = Field(gt=0, le=10**12)
    olchov: str | None = Field(default=None, max_length=30)
    xomashyo_narx: float | None = Money  # 1 birlik uchun tovar/xomashyo narxi


class PlanInput(BaseModel):
    """Moliyaviy yadro kirish maydonlari (nomlari yadrodagidek, frontend formasi bilan bir xil)."""
    model_config = ConfigDict(extra="forbid")

    faoliyat_turi: Literal["ishlab_chiqarish", "qishloq_xojaligi", "savdo", "xizmat"]
    loyiha_nomi: str = Field(min_length=2, max_length=200)
    faoliyat_turi_text: str | None = Field(default=None, max_length=200)
    tashabbuskor: str | None = Field(default=None, max_length=200)
    fio: str | None = Field(default=None, max_length=150)
    mulk: str | None = Field(default=None, max_length=50)
    stir: str | None = Field(default=None, pattern=r"^\d{9}$")
    jshshir: str | None = Field(default=None, pattern=r"^\d{14}$")  # qo'lda kiritiladi, faqat hujjatga yoziladi
    manzil: str | None = Field(default=None, max_length=300)
    bank: str | None = Field(default=None, max_length=150)
    soliq_turi: Literal["ytt", "mchj"] = "ytt"
    mahsulot: str | None = Field(default=None, max_length=200)
    olchov: str | None = Field(default=None, max_length=30)
    ro_sana: str | None = Field(default=None, max_length=20)

    loyiha_qiymati: float = Field(gt=0, le=10**13)
    oz_mablag: float | None = Money
    kredit: float | None = Money
    foiz: float | None = Field(default=None, ge=0, le=100)
    muddat: int | None = Field(default=None, ge=1, le=360)
    imtiyoz: int | None = Field(default=None, ge=0, le=120)
    kredit_turi: Literal["annuitet", "differensial"] = "differensial"
    aylanma_kapital: float | None = Money  # o'z mablag'idan
    sugurta: float | None = Money

    # Bitta mahsulot (eski usul) yoki mahsulotlar ro'yxati (6 tagacha)
    hajm: float | None = Field(default=None, gt=0, le=10**12)
    narx: float | None = Field(default=None, gt=0, le=10**12)
    mahsulotlar: list[ProductIn] | None = Field(default=None, min_length=1, max_length=6)
    xomashyo_narx: float | None = Money
    tovar_xaridi: float | None = Money
    tannarx_ulushi: float | None = Field(default=None, ge=0, le=100)  # tovar/xomashyo, tushumdan %; bo'sh: faoliyat turiga qarab
    urug_yem_narx: float | None = Money
    texnika_xarajat: float | None = Money
    yer_ijarasi: float | None = Money
    dokon_ijarasi: float | None = Money
    joy_ijarasi: float | None = Money
    transport_xarajat: float | None = Money
    elektr: float | None = Money
    gaz: float | None = Money
    suv: float | None = Money
    oqava: float | None = Money
    boshqa_kommunal: float | None = Money  # yillik summa

    # Ixtiyoriy sozlamalar (standart: Excel shabloni)
    quvvat: list[float] | None = Field(default=None, min_length=10, max_length=10)  # 10 yil, foizda (0-150)
    diskont: float | None = Field(default=None, ge=0, le=100)

    direktor: int | None = Count
    rahbar_oylik: float | None = Money
    xodim: int | None = Count
    ishchi_oylik: float | None = Money
    yangi_xodim: int | None = Count
    yangi_ishchi_oylik: float | None = Money

    @model_validator(mode="after")
    def _check(self):
        if not self.mahsulotlar and not (self.hajm and self.narx):
            raise ValueError("hajm va narx yoki mahsulotlar ro'yxati kerak")
        if self.quvvat and any(q < 0 or q > 150 for q in self.quvvat):
            raise ValueError("quvvat foizlari 0 dan 150 gacha bo'lishi kerak")
        return self

    # Muqova rasmi: POST /v1/plans/images natijasi yoki avtomatik (faoliyat turiga qarab)
    rasm_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}\.(jpg|png)$")
    rasm_avto: bool = True

    def engine_payload(self) -> dict:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class PlanCreateIn(BaseModel):
    input: PlanInput
    use_ai: bool = True


class PlanOut(BaseModel):
    id: str
    title: str
    activity_type: str
    status: str
    error: str | None
    quota_source: str
    ai_requested: bool
    ai_used: bool
    indicators: dict | None
    created_at: datetime
    finished_at: datetime | None


class PreviewOut(BaseModel):
    indicators: dict
    tables: list
    context: dict


class ImageOut(BaseModel):
    image_id: str


class DownloadOut(BaseModel):
    url: str
    expires_in: int
