import pytest

from knowledge_worker.core.exceptions import TooManyRequestsError
from knowledge_worker.core.rate_limit import LoginRateLimiter
from tests.test_auth import auth_client, register  # noqa: F401  (fixture + helper)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def limiter(clock):
    return LoginRateLimiter(max_failures=3, max_failures_per_ip=5, window_seconds=60, clock=clock)


def fail(limiter, times, ip="1.1.1.1", email="a@example.com"):
    for _ in range(times):
        limiter.record_failure(ip, email)


class TestLimiter:
    def test_allows_until_the_limit(self, limiter):
        fail(limiter, 2)
        limiter.check("1.1.1.1", "a@example.com")  # third attempt is still allowed

    def test_blocks_at_the_limit_with_retry_after(self, limiter):
        fail(limiter, 3)
        with pytest.raises(TooManyRequestsError) as info:
            limiter.check("1.1.1.1", "a@example.com")
        assert info.value.status_code == 429
        assert info.value.details["retry_after_seconds"] == 60
        assert info.value.headers == {"Retry-After": "60"}

    def test_email_is_case_insensitive(self, limiter):
        fail(limiter, 3, email="A@Example.com ")
        with pytest.raises(TooManyRequestsError):
            limiter.check("1.1.1.1", "a@example.com")

    def test_window_slides(self, limiter, clock):
        fail(limiter, 3)
        clock.now += 59
        with pytest.raises(TooManyRequestsError):
            limiter.check("1.1.1.1", "a@example.com")
        clock.now += 1
        limiter.check("1.1.1.1", "a@example.com")

    def test_retry_after_counts_down_from_the_oldest_failure(self, limiter, clock):
        fail(limiter, 1)
        clock.now += 20
        fail(limiter, 2)
        with pytest.raises(TooManyRequestsError) as info:
            limiter.check("1.1.1.1", "a@example.com")
        assert info.value.details["retry_after_seconds"] == 40

    def test_another_ip_is_not_blocked_for_the_same_email(self, limiter):
        # A stranger can't lock the real user out by failing from somewhere else.
        fail(limiter, 3, ip="6.6.6.6")
        limiter.check("1.1.1.1", "a@example.com")

    def test_one_ip_trying_many_emails_is_blocked(self, limiter):
        for i in range(5):
            fail(limiter, 1, email=f"user{i}@example.com")
        with pytest.raises(TooManyRequestsError):
            limiter.check("1.1.1.1", "brand-new@example.com")

    def test_reset_clears_the_account_but_not_the_ip_budget(self, limiter):
        fail(limiter, 2, email="a@example.com")
        limiter.reset("1.1.1.1", "a@example.com")
        fail(limiter, 2, email="a@example.com")
        limiter.check("1.1.1.1", "a@example.com")  # account count restarted: 2 of 3
        fail(limiter, 1, email="b@example.com")
        with pytest.raises(TooManyRequestsError):
            limiter.check("1.1.1.1", "c@example.com")  # IP total is still 2 + 2 + 1 = 5


@pytest.fixture
def strict_client(auth_client, container):  # noqa: F811
    container.login_limiter.max_failures = 3
    return auth_client


def login(client, password, email="rahim@example.com"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


class TestLoginEndpoint:
    def test_blocks_after_repeated_failures_even_with_the_right_password(self, strict_client):
        register(strict_client)
        for _ in range(3):
            assert login(strict_client, "wrong-password").status_code == 401
        response = login(strict_client, "password123")
        assert response.status_code == 429
        body = response.json()
        assert body["error"] == "TooManyRequestsError"
        assert body["details"]["retry_after_seconds"] > 0
        assert int(response.headers["Retry-After"]) == body["details"]["retry_after_seconds"]

    def test_success_resets_the_count(self, strict_client):
        register(strict_client)
        for _ in range(2):
            login(strict_client, "wrong-password")
        assert login(strict_client, "password123").status_code == 200
        for _ in range(2):
            assert login(strict_client, "wrong-password").status_code == 401
        assert login(strict_client, "password123").status_code == 200

    def test_unknown_email_failures_are_limited_too(self, strict_client):
        for _ in range(3):
            assert login(strict_client, "x", email="nobody@example.com").status_code == 401
        assert login(strict_client, "x", email="nobody@example.com").status_code == 429
