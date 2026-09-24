"""Tests for the Profile & Preferences API (Phase 9).

Covers:
  - GET /api/profile (authenticated)
  - PATCH /api/profile (create + update + partial update)
  - GET /api/profile/preferences (authenticated)
  - PATCH /api/profile/preferences (create + update)
  - Unauthenticated access → 401
  - Cross-user isolation: user A cannot read user B's profile

Uses the shared in-memory SQLite test database defined in conftest.py.
"""

from tests.conftest import client


# ---------------------------------------------------------------------------
# Helper utilities (mirror test_auth.py pattern)
# ---------------------------------------------------------------------------

def _register(email, name="Test User", password="secret123"):
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )


def _login(email, password="secret123"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /api/profile — unauthenticated
# ---------------------------------------------------------------------------

def test_get_profile_requires_auth():
    resp = client.get("/api/profile")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/profile — authenticated, no profile yet
# ---------------------------------------------------------------------------

def test_get_profile_new_user_returns_defaults():
    _register("profile_new@example.com", name="New User")
    token = _login("profile_new@example.com")

    resp = client.get("/api/profile", headers=_headers(token))
    assert resp.status_code == 200

    data = resp.json()
    # Identity always present
    assert data["email"] == "profile_new@example.com"
    assert data["name"] == "New User"
    assert "user_id" in data
    # Editable fields are null until saved
    assert data["headline"] is None
    assert data["bio"] is None
    assert data["location"] is None
    assert data["country"] is None


# ---------------------------------------------------------------------------
# PATCH /api/profile — unauthenticated
# ---------------------------------------------------------------------------

def test_patch_profile_requires_auth():
    resp = client.patch("/api/profile", json={"headline": "Hi"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/profile — create profile
# ---------------------------------------------------------------------------

def test_patch_profile_creates_profile():
    _register("profile_create@example.com")
    token = _login("profile_create@example.com")

    payload = {
        "headline": "Senior Data Analyst",
        "bio": "10 years of experience in analytics.",
        "location": "London",
        "country": "United Kingdom",
    }
    resp = client.patch("/api/profile", json=payload, headers=_headers(token))
    assert resp.status_code == 200

    data = resp.json()
    assert data["headline"] == "Senior Data Analyst"
    assert data["bio"] == "10 years of experience in analytics."
    assert data["location"] == "London"
    assert data["country"] == "United Kingdom"
    assert data["profile_source"] == "manual"
    assert data["email"] == "profile_create@example.com"


# ---------------------------------------------------------------------------
# GET /api/profile — persists after PATCH
# ---------------------------------------------------------------------------

def test_get_profile_returns_saved_data():
    _register("profile_persist@example.com")
    token = _login("profile_persist@example.com")

    client.patch(
        "/api/profile",
        json={"headline": "ML Engineer", "location": "Berlin"},
        headers=_headers(token),
    )

    resp = client.get("/api/profile", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["headline"] == "ML Engineer"
    assert data["location"] == "Berlin"


# ---------------------------------------------------------------------------
# PATCH /api/profile — partial update (only update headline, bio stays)
# ---------------------------------------------------------------------------

def test_patch_profile_partial_update():
    _register("profile_partial@example.com")
    token = _login("profile_partial@example.com")

    # Set initial values
    client.patch(
        "/api/profile",
        json={"headline": "Junior Developer", "bio": "My bio"},
        headers=_headers(token),
    )

    # Update only headline — bio must remain
    resp = client.patch(
        "/api/profile",
        json={"headline": "Senior Developer"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["headline"] == "Senior Developer"
    assert data["bio"] == "My bio"  # unchanged


# ---------------------------------------------------------------------------
# GET /api/profile/preferences — unauthenticated
# ---------------------------------------------------------------------------

def test_get_preferences_requires_auth():
    resp = client.get("/api/profile/preferences")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/profile/preferences — authenticated, no preferences yet
# ---------------------------------------------------------------------------

def test_get_preferences_new_user_returns_defaults():
    _register("prefs_new@example.com")
    token = _login("prefs_new@example.com")

    resp = client.get("/api/profile/preferences", headers=_headers(token))
    assert resp.status_code == 200

    data = resp.json()
    assert "user_id" in data
    # List fields default to empty list
    assert data["preferred_roles"] == []
    assert data["preferred_skills"] == []
    assert data["preferred_work_modes"] == []
    assert data["preferred_employment_types"] == []
    assert data["preferred_industries"] == []
    # Scalars default to null
    assert data["salary_min"] is None
    assert data["salary_max"] is None
    assert data["career_level"] is None
    assert data["open_to_relocate"] is None


# ---------------------------------------------------------------------------
# PATCH /api/profile/preferences — unauthenticated
# ---------------------------------------------------------------------------

def test_patch_preferences_requires_auth():
    resp = client.patch("/api/profile/preferences", json={"career_level": "mid"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/profile/preferences — create preferences
# ---------------------------------------------------------------------------

def test_patch_preferences_creates_preferences():
    _register("prefs_create@example.com")
    token = _login("prefs_create@example.com")

    payload = {
        "preferred_roles": ["Data Analyst", "BI Developer"],
        "preferred_work_modes": ["remote", "hybrid"],
        "preferred_employment_types": ["full-time"],
        "career_level": "mid",
        "salary_min": 50000,
        "salary_max": 80000,
        "currency": "GBP",
        "open_to_relocate": True,
        "preferred_industries": ["Finance", "Tech"],
        "preferred_skills": ["Python", "SQL"],
    }
    resp = client.patch(
        "/api/profile/preferences", json=payload, headers=_headers(token)
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["preferred_roles"] == ["Data Analyst", "BI Developer"]
    assert data["preferred_work_modes"] == ["remote", "hybrid"]
    assert data["preferred_employment_types"] == ["full-time"]
    assert data["career_level"] == "mid"
    assert data["salary_min"] == 50000.0
    assert data["salary_max"] == 80000.0
    assert data["currency"] == "GBP"
    assert data["open_to_relocate"] is True
    assert data["preferred_industries"] == ["Finance", "Tech"]
    assert data["preferred_skills"] == ["Python", "SQL"]


# ---------------------------------------------------------------------------
# GET /api/profile/preferences — persists after PATCH
# ---------------------------------------------------------------------------

def test_get_preferences_returns_saved_data():
    _register("prefs_persist@example.com")
    token = _login("prefs_persist@example.com")

    client.patch(
        "/api/profile/preferences",
        json={"preferred_roles": ["Product Manager"], "career_level": "senior"},
        headers=_headers(token),
    )

    resp = client.get("/api/profile/preferences", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["preferred_roles"] == ["Product Manager"]
    assert data["career_level"] == "senior"


# ---------------------------------------------------------------------------
# PATCH /api/profile/preferences — partial update (list field)
# ---------------------------------------------------------------------------

def test_patch_preferences_partial_update():
    _register("prefs_partial@example.com")
    token = _login("prefs_partial@example.com")

    # Set initial values
    client.patch(
        "/api/profile/preferences",
        json={"preferred_roles": ["Developer"], "career_level": "junior"},
        headers=_headers(token),
    )

    # Update only career_level — preferred_roles must remain
    resp = client.patch(
        "/api/profile/preferences",
        json={"career_level": "mid"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["career_level"] == "mid"
    assert data["preferred_roles"] == ["Developer"]  # unchanged


# ---------------------------------------------------------------------------
# PATCH /api/profile/preferences — open_to_relocate False
# ---------------------------------------------------------------------------

def test_patch_preferences_open_to_relocate_false():
    _register("prefs_relocate@example.com")
    token = _login("prefs_relocate@example.com")

    resp = client.patch(
        "/api/profile/preferences",
        json={"open_to_relocate": False},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["open_to_relocate"] is False


# ---------------------------------------------------------------------------
# Cross-user isolation
# ---------------------------------------------------------------------------

def test_profile_scoped_to_current_user():
    """User A's profile data is NOT visible or overwritten by User B's actions."""
    _register("alice_profile@example.com", name="Alice")
    alice_token = _login("alice_profile@example.com")

    _register("bob_profile@example.com", name="Bob")
    bob_token = _login("bob_profile@example.com")

    # Alice sets her headline
    client.patch(
        "/api/profile",
        json={"headline": "Alice's Headline"},
        headers=_headers(alice_token),
    )

    # Bob sets his own headline
    client.patch(
        "/api/profile",
        json={"headline": "Bob's Headline"},
        headers=_headers(bob_token),
    )

    # Each user sees only their own data
    alice_profile = client.get("/api/profile", headers=_headers(alice_token)).json()
    bob_profile = client.get("/api/profile", headers=_headers(bob_token)).json()

    assert alice_profile["headline"] == "Alice's Headline"
    assert alice_profile["name"] == "Alice"

    assert bob_profile["headline"] == "Bob's Headline"
    assert bob_profile["name"] == "Bob"

    # user_ids are different
    assert alice_profile["user_id"] != bob_profile["user_id"]


def test_preferences_scoped_to_current_user():
    """User A's preferences do not affect User B's preferences."""
    _register("alice_prefs@example.com", name="Alice2")
    alice_token = _login("alice_prefs@example.com")

    _register("bob_prefs@example.com", name="Bob2")
    bob_token = _login("bob_prefs@example.com")

    client.patch(
        "/api/profile/preferences",
        json={"preferred_roles": ["Alice Role"]},
        headers=_headers(alice_token),
    )
    client.patch(
        "/api/profile/preferences",
        json={"preferred_roles": ["Bob Role"]},
        headers=_headers(bob_token),
    )

    alice_prefs = client.get(
        "/api/profile/preferences", headers=_headers(alice_token)
    ).json()
    bob_prefs = client.get(
        "/api/profile/preferences", headers=_headers(bob_token)
    ).json()

    assert alice_prefs["preferred_roles"] == ["Alice Role"]
    assert bob_prefs["preferred_roles"] == ["Bob Role"]
