"""Staging yuklama testi kaliti: IP rate limit'ni faqat to'g'ri, yetarli uzun kalit bilan o'tkazadi."""
import pytest

from app.core.config import Settings, get_settings

TOKEN = "k6-" + "x" * 40


@pytest.fixture
def loadtest_token(monkeypatch):
    def set_token(value: str):
        monkeypatch.setattr(get_settings(), "loadtest_token", value)
    yield set_token


async def _hit_register(client, headers, n=11):
    codes = []
    for i in range(n):
        r = await client.post("/v1/auth/register", json={"phone": f"+99893{i:07d}", "password": "parol12345"}, headers=headers)
        codes.append(r.status_code)
    return codes


async def test_without_token_rate_limit_applies(client, loadtest_token):
    loadtest_token(TOKEN)
    codes = await _hit_register(client, {})
    assert codes[-1] == 429 and codes.count(201) == 10


async def test_correct_token_bypasses_rate_limit(client, loadtest_token):
    loadtest_token(TOKEN)
    assert 429 not in await _hit_register(client, {"X-Loadtest-Token": TOKEN})


@pytest.mark.parametrize("configured,sent", [
    ("", ""),                       # o'chiq
    ("", "anything"),               # server kalitsiz: sarlavha hech narsa bermaydi
    (TOKEN, TOKEN[:-1] + "y"),      # noto'g'ri kalit
    ("short-token", "short-token"), # 32 belgidan qisqa kalit ishlamaydi
])
async def test_bypass_needs_a_configured_long_matching_token(client, loadtest_token, configured, sent):
    loadtest_token(configured)
    assert (await _hit_register(client, {"X-Loadtest-Token": sent} if sent else {}))[-1] == 429


def test_production_rejects_short_loadtest_token():
    base = dict(app_env="production", secret_key="s" * 40, database_url="postgresql://u:p@h/db", redis_url="redis://r",
                job_mode="queue", storage_backend="r2", cookie_secure=True)
    with pytest.raises(ValueError, match="LOADTEST_TOKEN"):
        Settings(**base, loadtest_token="short")
    assert Settings(**base, loadtest_token=TOKEN).loadtest_token == TOKEN
