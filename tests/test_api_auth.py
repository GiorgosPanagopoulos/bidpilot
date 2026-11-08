"""Auth, roles and CORS at router level."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import jwt
import pytest

from app.core.security import ALGORITHM, create_access_token
from app.core.settings import settings
from tests.api_fixtures import PASSWORD, bearer


async def test_login_returns_token_with_company_claim(api, make_user):
    user, _ = await make_user("acme", "admin")

    res = await api.post("/auth/login", json={"email": user.email.upper(), "password": PASSWORD})

    assert res.status_code == 200
    body = res.json()
    claims = jwt.decode(body["access_token"], settings.secret_key, algorithms=[ALGORITHM])
    assert claims["company_id"] == "acme"
    assert claims["sub"] == user.id
    assert body["user"] == {
        "id": user.id,
        "email": user.email,
        "company_id": "acme",
        "role": "admin",
        "is_demo": False,
    }
    assert "hashed_password" not in body["user"]


@pytest.mark.parametrize(
    "email,password", [("member@acme.test", "wrong"), ("nobody@x.test", PASSWORD)]
)
async def test_login_rejects_bad_credentials_with_same_message(api, make_user, email, password):
    await make_user("acme")

    res = await api.post("/auth/login", json={"email": email, "password": password})

    assert res.status_code == 401
    assert res.json()["detail"] == "Incorrect email or password"


async def test_inactive_user_cannot_login_or_use_token(api, make_user):
    user, token = await make_user("acme", is_active=False)

    assert (
        await api.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    ).status_code == 403
    assert (await api.get("/auth/me", headers=bearer(token))).status_code == 403


async def test_me_requires_token(api, make_user):
    _, token = await make_user("acme")

    assert (await api.get("/auth/me")).status_code == 401
    assert (await api.get("/auth/me", headers=bearer("garbage"))).status_code == 401
    assert (await api.get("/auth/me", headers=bearer(token))).status_code == 200


async def test_token_signed_with_other_key_is_rejected(api, make_user):
    user, _ = await make_user("acme")
    forged = jwt.encode(
        {"sub": user.id, "company_id": "acme", "role": "admin", "exp": 4102444800},
        "another-secret-key-that-is-long-enough-123456",  # pragma: allowlist secret
        algorithm=ALGORITHM,
    )

    assert (await api.get("/auth/me", headers=bearer(forged))).status_code == 401


async def test_token_company_must_match_user(api, make_user):
    user, _ = await make_user("acme")
    tampered = create_access_token(user.id, "globex", user.role)

    assert (await api.get("/auth/me", headers=bearer(tampered))).status_code == 401


async def test_x_company_id_header_is_ignored(api, make_user):
    await make_user("acme")
    _, token_b = await make_user("globex")

    res = await api.get("/companies/acme", headers={**bearer(token_b), "X-Company-Id": "acme"})

    assert res.status_code == 404


async def test_all_data_endpoints_require_auth(api, fake_db):
    for method, path in [
        ("GET", "/tenders"),
        ("GET", "/awards"),
        ("GET", "/analytics/pricing"),
        ("GET", "/matches?company_id=acme"),
        ("GET", "/companies/acme"),
        ("GET", "/drafts/x"),
        ("POST", "/drafts/run"),
        ("POST", "/tenders/ingest"),
        ("POST", "/awards/ingest"),
    ]:
        res = await api.request(method, path)
        assert res.status_code == 401, f"{method} {path}"


@pytest.mark.parametrize(
    "path,target",
    [
        ("/tenders/ingest", "app.api.routers.tenders.ingest_pipeline"),
        ("/awards/ingest", "app.api.routers.awards.ingest_awards_pipeline"),
    ],
)
async def test_ingest_is_admin_only(api, make_user, path, target):
    _, admin = await make_user("acme", "admin")
    _, member = await make_user("acme", "member")
    _, viewer = await make_user("acme", "viewer")
    _, demo = await make_user("demo-co", "viewer", is_demo=True)

    with patch(target, new=AsyncMock(return_value=7)) as pipeline:
        for token in (member, viewer, demo):
            assert (await api.post(path, headers=bearer(token))).status_code == 403
        pipeline.assert_not_awaited()

        res = await api.post(path, headers=bearer(admin))

    assert res.status_code == 202
    assert res.json() == {"ingested": 7}


async def test_company_upsert_is_admin_only_and_pinned_to_own_company(api, make_user):
    _, admin = await make_user("acme", "admin")
    _, member = await make_user("acme", "member")
    body = {"id": "globex", "name": "Hijack"}

    assert (await api.post("/companies", json=body, headers=bearer(member))).status_code == 403

    res = await api.post("/companies", json=body, headers=bearer(admin))
    assert res.status_code == 201
    assert res.json()["id"] == "acme"


async def test_viewer_cannot_run_drafts(api, make_user):
    _, viewer = await make_user("acme", "viewer")

    res = await api.post(
        "/drafts/run", json={"company_id": "acme", "tender_id": "t1"}, headers=bearer(viewer)
    )

    assert res.status_code == 403


async def test_demo_login_issues_token_for_demo_user(api, make_user, monkeypatch):
    user, _ = await make_user("demo-co", "viewer", is_demo=True)
    monkeypatch.setattr(settings, "demo_email", user.email)

    res = await api.post("/auth/demo")

    assert res.status_code == 200
    assert res.json()["user"]["is_demo"] is True


async def test_demo_login_disabled_or_pointing_to_real_user(api, make_user, monkeypatch):
    user, _ = await make_user("acme", "admin")

    monkeypatch.setattr(settings, "demo_email", "")
    assert (await api.post("/auth/demo")).status_code == 404

    # Misconfiguration must not hand out a non-demo account.
    monkeypatch.setattr(settings, "demo_email", user.email)
    assert (await api.post("/auth/demo")).status_code == 404


async def test_cors_allows_configured_origin_only(api):
    preflight = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization",
    }

    ok = await api.options("/drafts/run", headers={"Origin": "http://localhost:5173", **preflight})
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"

    bad = await api.options("/drafts/run", headers={"Origin": "https://evil.example", **preflight})
    assert "access-control-allow-origin" not in bad.headers
