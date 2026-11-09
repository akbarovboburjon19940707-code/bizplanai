"""Click SHOP API: Prepare (action=0) va Complete (action=1). Javob doim HTTP 200, xato 'error' maydonida."""
import hashlib
import hmac

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.models import ClickTransaction, PaymentEvent
from app.modules.payments.service import lock_payment, mark_cancelled, mark_paid

router = APIRouter(prefix="/v1/payments/click", tags=["payments-callbacks"])

ERR = {0: "Success", -1: "SIGN CHECK FAILED!", -2: "Incorrect parameter amount", -3: "Action not found",
       -4: "Already paid", -5: "User does not exist", -6: "Transaction does not exist", -8: "Error in request from click",
       -9: "Transaction cancelled"}


def _sign_ok(f: dict, action: str) -> bool:
    s = get_settings()
    prepare_id = f.get("merchant_prepare_id", "") if action == "1" else ""
    raw = (f"{f.get('click_trans_id', '')}{f.get('service_id', '')}{s.click_secret_key}{f.get('merchant_trans_id', '')}"
           f"{prepare_id}{f.get('amount', '')}{action}{f.get('sign_time', '')}")
    return hmac.compare_digest(hashlib.md5(raw.encode()).hexdigest(), (f.get("sign_string") or "").lower())


def _resp(f: dict, code: int, **extra) -> dict:
    return {"click_trans_id": f.get("click_trans_id"), "merchant_trans_id": f.get("merchant_trans_id"),
            "error": code, "error_note": ERR[code], **extra}


def _amount_ok(f: dict, amount_tiyin: int) -> bool:
    try:
        return round(float(f.get("amount", "")) * 100) == amount_tiyin
    except ValueError:
        return False


async def _common(session, f: dict, action: str):
    s = get_settings()
    if not s.click_secret_key:
        return None, _resp(f, -8)
    if not _sign_ok(f, action):
        return None, _resp(f, -1)
    if f.get("action") != action:
        return None, _resp(f, -3)
    if s.click_service_id and f.get("service_id") != s.click_service_id:
        return None, _resp(f, -8)
    p = await lock_payment(session, f.get("merchant_trans_id", ""))
    if not p or p.provider != "click":
        return None, _resp(f, -5)
    if not _amount_ok(f, p.amount_tiyin):
        return None, _resp(f, -2)
    session.add(PaymentEvent(payment_id=p.id, source="click", event=f"action_{action}",
                             data={k: v for k, v in f.items() if k != "sign_string"}))
    return p, None


@router.post("/prepare")
async def prepare(request: Request, session: SessionDep):
    f = dict(await request.form())
    p, err = await _common(session, f, "0")
    if err:
        await session.commit()
        return err
    if p.status == "paid":
        await session.commit()
        return _resp(f, -4)
    if p.status in ("cancelled", "rejected") or int(f.get("error") or 0) < 0:
        await session.commit()
        return _resp(f, -9)
    tx = await session.scalar(select(ClickTransaction).where(ClickTransaction.click_trans_id == str(f["click_trans_id"])))
    if tx is None:
        tx = ClickTransaction(payment_id=p.id, click_trans_id=str(f["click_trans_id"]))
        session.add(tx)
        await session.flush()
    await session.commit()
    return _resp(f, 0, merchant_prepare_id=tx.id)


@router.post("/complete")
async def complete(request: Request, session: SessionDep):
    f = dict(await request.form())
    p, err = await _common(session, f, "1")
    if err:
        await session.commit()
        return err
    try:
        tx = await session.get(ClickTransaction, int(f.get("merchant_prepare_id") or 0))
    except ValueError:
        tx = None
    if not tx or tx.payment_id != p.id or tx.click_trans_id != str(f.get("click_trans_id")):
        await session.commit()
        return _resp(f, -6)
    if int(f.get("error") or 0) < 0:
        tx.status = "cancelled"
        await mark_cancelled(session, p, "click", data={"click_error": f.get("error")})
        await session.commit()
        return _resp(f, -9)
    if tx.status == "cancelled" or p.status in ("cancelled", "rejected"):
        await session.commit()
        return _resp(f, -9)
    if p.status == "paid":
        await session.commit()
        return _resp(f, -4)
    await mark_paid(session, p, "click", data={"click_trans_id": tx.click_trans_id})
    tx.status = "completed"
    await session.commit()
    return _resp(f, 0, merchant_confirm_id=tx.id)
