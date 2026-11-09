from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Money = Field(default=None, ge=0, le=10**13)
Count = Field(default=None, ge=0, le=100_000)


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
    kredit_turi: Literal["annuitet", "differensial"] = "annuitet"

    hajm: float = Field(gt=0, le=10**12)
    narx: float = Field(gt=0, le=10**12)
    xomashyo_narx: float | None = Money
    tovar_xaridi: float | None = Money
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

    direktor: int | None = Count
    rahbar_oylik: float | None = Money
    xodim: int | None = Count
    ishchi_oylik: float | None = Money
    yangi_xodim: int | None = Count
    yangi_ishchi_oylik: float | None = Money

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


class DownloadOut(BaseModel):
    url: str
    expires_in: int
