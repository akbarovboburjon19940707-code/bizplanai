"""Payme Merchant API (JSON-RPC 2.0). Hisob maydoni: account.order_id = payments.id. Summa tiyinda."""
import base64
import hmac
import time

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.models import PaymentEvent, PaymeTransaction
from app.modules.payments.service import lock_payment, mark_cancelled, mark_paid

router = APIRouter(prefix="/v1/payments/payme", tags=["payments-callbacks"])
TIMEOUT_MS = 43_200_000  # 12 soat


def _now_ms() -> int:
    return int(time.time() * 1000)


def _err(rpc_id, code: int, uz: str, data: str | None = None) -> dict:
    e = {"code": code, "message": {"uz": uz, "ru": uz, "en": uz}}
    if data:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": rpc_id, "error": e}


def _ok(rpc_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


def _authorized(header: str | None) -> bool:
    key = get_settings().payme_secret_key
    if not key or not header or not header.startswith("Basic "):
        return False
    try:
        login, _, password = base64.b64decode(header[6:]).decode().partition(":")
    except (ValueError, UnicodeDecodeError):
        return False
    return login == "Paycom" and hmac.compare_digest(password.encode(), key.encode())


async def _check_order(session, rpc_id, params):
    order_id = str((params.get("account") or {}).get("order_id") or "")
    p = await lock_payment(session, order_id) if order_id else None
    if not p or p.provider != "payme":
        return None, _err(rpc_id, -31050, "Buyurtma topilmadi", "order_id")
    if p.status != "pending":
        return None, _err(rpc_id, -31051, "Buyurtma allaqachon yopilgan", "order_id")
    if int(params.get("amount") or 0) != p.amount_tiyin:
        return None, _err(rpc_id, -31001, "Summa noto'g'ri")
    return p, None


def _tx_state(tx: PaymeTransaction) -> dict:
    return {"create_time": tx.create_time, "perform_time": tx.perform_time, "cancel_time": tx.cancel_time,
            "transaction": str(tx.id), "state": tx.state, "reason": tx.reason}


@router.post("")
async def rpc(request: Request, session: SessionDep):
    try:
        body = await request.json()
    except ValueError:
        return _err(None, -32700, "JSON xato")
    rpc_id, method, params = body.get("id"), body.get("method"), body.get("params") or {}
    if not _authorized(request.headers.get("authorization")):
        return _err(rpc_id, -32504, "Ruxsat yo'q")

    if method == "CheckPerformTransaction":
        p, err = await _check_order(session, rpc_id, params)
        return err or _ok(rpc_id, {"allow": True})

    if method == "CreateTransaction":
        payme_id = str(params.get("id") or "")
        tx = await session.scalar(select(PaymeTransaction).where(PaymeTransaction.payme_id == payme_id))
        if tx:
            if tx.state != 1:
                return _err(rpc_id, -31008, "Tranzaksiya holati noto'g'ri")
            if _now_ms() - tx.create_time > TIMEOUT_MS:
                tx.state, tx.reason, tx.cancel_time = -1, 4, _now_ms()
                await session.commit()
                return _err(rpc_id, -31008, "Tranzaksiya muddati o'tgan")
            return _ok(rpc_id, {"create_time": tx.create_time, "transaction": str(tx.id), "state": tx.state})
        p, err = await _check_order(session, rpc_id, params)
        if err:
            return err
        busy = await session.scalar(select(PaymeTransaction.id).where(
            PaymeTransaction.payment_id == p.id, PaymeTransaction.state == 1))
        if busy:
            return _err(rpc_id, -31050, "Buyurtma boshqa tranzaksiyada band", "order_id")
        tx = PaymeTransaction(payme_id=payme_id, payment_id=p.id, amount_tiyin=p.amount_tiyin, state=1,
                              paycom_time=int(params.get("time") or _now_ms()), create_time=_now_ms())
        session.add(tx)
        session.add(PaymentEvent(payment_id=p.id, source="payme", event="create", data={"payme_id": payme_id}))
        await session.commit()
        return _ok(rpc_id, {"create_time": tx.create_time, "transaction": str(tx.id), "state": tx.state})

    if method == "PerformTransaction":
        tx = await session.scalar(select(PaymeTransaction).where(PaymeTransaction.payme_id == str(params.get("id"))))
        if not tx:
            return _err(rpc_id, -31003, "Tranzaksiya topilmadi")
        p = await lock_payment(session, tx.payment_id)
        if tx.state == 1:
            if _now_ms() - tx.create_time > TIMEOUT_MS:
                tx.state, tx.reason, tx.cancel_time = -1, 4, _now_ms()
                await mark_cancelled(session, p, "payme", data={"reason": 4})
                await session.commit()
                return _err(rpc_id, -31008, "Tranzaksiya muddati o'tgan")
            tx.state, tx.perform_time = 2, _now_ms()
            await mark_paid(session, p, "payme", data={"payme_id": tx.payme_id})
            await session.commit()
        if tx.state == 2:
            return _ok(rpc_id, {"transaction": str(tx.id), "perform_time": tx.perform_time, "state": tx.state})
        return _err(rpc_id, -31008, "Bekor qilingan tranzaksiyani bajarib bo'lmaydi")

    if method == "CancelTransaction":
        tx = await session.scalar(select(PaymeTransaction).where(PaymeTransaction.payme_id == str(params.get("id"))))
        if not tx:
            return _err(rpc_id, -31003, "Tranzaksiya topilmadi")
        if tx.state in (1, 2):
            p = await lock_payment(session, tx.payment_id)
            tx.state = -1 if tx.state == 1 else -2
            tx.cancel_time, tx.reason = _now_ms(), int(params.get("reason") or 0) or None
            await mark_cancelled(session, p, "payme", data={"reason": tx.reason})
            await session.commit()
        return _ok(rpc_id, {"transaction": str(tx.id), "cancel_time": tx.cancel_time, "state": tx.state})

    if method == "CheckTransaction":
        tx = await session.scalar(select(PaymeTransaction).where(PaymeTransaction.payme_id == str(params.get("id"))))
        if not tx:
            return _err(rpc_id, -31003, "Tranzaksiya topilmadi")
        return _ok(rpc_id, _tx_state(tx))

    if method == "GetStatement":
        rows = await session.scalars(select(PaymeTransaction).where(
            PaymeTransaction.paycom_time >= int(params.get("from") or 0),
            PaymeTransaction.paycom_time <= int(params.get("to") or 0)).order_by(PaymeTransaction.paycom_time))
        return _ok(rpc_id, {"transactions": [
            {"id": t.payme_id, "time": t.paycom_time, "amount": t.amount_tiyin, "account": {"order_id": t.payment_id},
             **_tx_state(t)} for t in rows]})

    return _err(rpc_id, -32601, "Metod topilmadi")
