from tests.conftest import create_listing


def _payload(destination: str) -> dict:
    return {
        "destination": destination,
        "duration_days": 3,
        "budget_tier": "budget",
        "total_budget": 20000,
    }


def test_hybrid_does_not_trigger_web_when_db_is_sufficient(client, test_user, test_provider):
    create_listing(
        client,
        token=test_provider["token"],
        title="Fairy Hotel One",
        location="Fairy Meadows",
        price_per_night=2500,
        service_type="hotel",
        rooms_available=4,
    )
    create_listing(
        client,
        token=test_provider["token"],
        title="Fairy Hotel Two",
        location="Fairy Meadows",
        price_per_night=2800,
        service_type="hotel",
        rooms_available=4,
    )
    create_listing(
        client,
        token=test_provider["token"],
        title="Fairy Activity",
        location="Fairy Meadows",
        price_per_night=500,
        service_type="activity",
        rooms_available=10,
    )

    res = client.post("/trip-planner/suggest", headers=test_user["headers"], json=_payload("Fairy Meadows"))
    assert res.status_code == 200
    data = res.json()
    assert data["fallback_triggered"] is False
    assert data["web_suggestions"] == []


def test_hybrid_triggers_web_when_db_is_sparse(client, test_user, test_provider, monkeypatch):
    create_listing(
        client,
        token=test_provider["token"],
        title="Only Hotel",
        location="Fairy Meadows",
        price_per_night=2500,
        service_type="hotel",
        rooms_available=2,
    )

    async def fake_search(self, destination):  # noqa: ARG001
        return {
            "hotels": [{"name": "Hotel in Fairy Meadows", "description": "Budget stay Fairy Meadows", "external_url": "https://example.com/hotel"}],
            "restaurants": [],
            "activities": [{"name": "Things to do Fairy Meadows", "description": "Top attractions Fairy Meadows", "external_url": "https://example.com/activity"}],
            "transport": [],
            "guides": [],
        }

    monkeypatch.setattr("app.services.ai_trip_planner.web_search.WebSearchService.search", fake_search)
    res = client.post("/trip-planner/suggest", headers=test_user["headers"], json=_payload("Fairy Meadows"))
    assert res.status_code == 200
    data = res.json()
    assert data["fallback_triggered"] is True
    assert len(data["web_suggestions"]) >= 1


def test_hybrid_handles_web_failure_gracefully(client, test_user, test_provider, monkeypatch):
    create_listing(
        client,
        token=test_provider["token"],
        title="Only Hotel",
        location="Fairy Meadows",
        price_per_night=2500,
        service_type="hotel",
        rooms_available=2,
    )

    async def offline_search(self, destination):  # noqa: ARG001
        return {"hotels": [], "restaurants": [], "activities": [], "transport": [], "guides": []}

    monkeypatch.setattr("app.services.ai_trip_planner.web_search.WebSearchService.search", offline_search)
    res = client.post("/trip-planner/suggest", headers=test_user["headers"], json=_payload("Fairy Meadows"))
    assert res.status_code == 200
    data = res.json()
    assert data["fallback_triggered"] is True
    assert data["limited_results"] is True


def test_hybrid_corrects_typo_destination(client, test_user, monkeypatch):
    async def fake_search(self, destination):
        assert destination == "Fairy Meadows"
        return {"hotels": [], "restaurants": [], "activities": [], "transport": [], "guides": []}

    monkeypatch.setattr("app.services.ai_trip_planner.web_search.WebSearchService.search", fake_search)
    res = client.post("/trip-planner/suggest", headers=test_user["headers"], json=_payload("Fary Medows"))
    assert res.status_code == 200
    data = res.json()
    assert data["destination"] == "Fairy Meadows"
    assert data["destination_corrected_to"] == "Fairy Meadows"

