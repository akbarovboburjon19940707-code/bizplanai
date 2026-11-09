"""arq worker: `arq app.workers.settings.WorkerSettings`"""
import logging
from datetime import timedelta

from arq import cron
from sqlalchemy import update

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.redis import get_redis
from app.core.security import utcnow
from app.db.session import dispose_engine, sessionmaker
from app.models import CatalogProduct, Payment
from app.modules.plans.service import run_generation
from app.workers.queue import redis_settings

log = logging.getLogger(__name__)


async def generate_plan(ctx, plan_id: str) -> None:
    await run_generation(plan_id)


async def flush_views(ctx) -> None:
    r = get_redis()
    tmp = "catalog:views:flush"
    if not await r.exists("catalog:views"):
        return
    await r.rename("catalog:views", tmp)
    counts = await r.hgetall(tmp)
    async with sessionmaker()() as session:
        for pid, n in counts.items():
            await session.execute(update(CatalogProduct).where(CatalogProduct.id == pid)
                                  .values(views=CatalogProduct.views + int(n)))
        await session.commit()
    await r.delete(tmp)


async def cancel_stale_payments(ctx) -> None:
    cutoff = utcnow() - timedelta(hours=get_settings().pending_payment_ttl_hours)
    async with sessionmaker()() as session:
        res = await session.execute(update(Payment).where(Payment.status == "pending", Payment.created_at < cutoff)
                                    .values(status="cancelled", updated_at=utcnow()))
        await session.commit()
        if res.rowcount:
            log.info("eskirgan to'lovlar bekor qilindi: %s", res.rowcount)


async def startup(ctx) -> None:
    setup_logging(get_settings().log_level)


async def shutdown(ctx) -> None:
    await dispose_engine()


class WorkerSettings:
    functions = [generate_plan]
    cron_jobs = [
        cron(flush_views, minute=set(range(0, 60, 5))),
        cron(cancel_stale_payments, minute={7}),
    ]
    redis_settings = redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 8  # CPU ishi + AI kutish aralash; nusxa CPU soniga qarab sozlanadi
    job_timeout = 300
    max_tries = 3
