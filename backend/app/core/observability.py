"""Sentry: API va worker uchun bitta joyda. SENTRY_DSN bo'sh bo'lsa hech narsa qilmaydi."""
from app.core.config import get_settings


def init_sentry(component: str) -> bool:
    s = get_settings()
    if not s.sentry_dsn:
        return False
    import sentry_sdk

    sentry_sdk.init(dsn=s.sentry_dsn, environment=s.app_env, traces_sample_rate=0.05, send_default_pii=False)
    sentry_sdk.set_tag("component", component)  # api | worker: xato qayerdan kelgani
    return True
