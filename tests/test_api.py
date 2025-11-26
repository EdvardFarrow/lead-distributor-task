import pytest

@pytest.mark.asyncio
async def test_full_flow(client):
    # Создаем оператора "Alice"
    resp = await client.post("/operators/", json={"name": "Alice", "max_load": 5})
    assert resp.status_code == 200
    alice_id = resp.json()["id"]

    # Создаем источник "Telegram Bot"
    resp = await client.post("/sources/", json={"name": "Telegram Bot"})
    assert resp.status_code == 200
    source_id = resp.json()["id"]

    # Настраиваем вес (Alice работает на Telegram Bot с весом 100)
    config_data = [{"operator_id": alice_id, "weight": 100}]
    resp = await client.post(f"/sources/{source_id}/config", json=config_data)
    assert resp.status_code == 200

    # Приходит Лид (ID: user123)
    lead_payload = {
        "external_lead_id": "user123",
        "source_id": source_id,
        "message": "Hello"
    }
    resp = await client.post("/interactions/", json=lead_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["operator_id"] == alice_id  
    assert data["status"] == "open"

    # Проверяем статистику (нагрузка Алисы должна стать 1)
    resp = await client.get("/stats/")
    stats = resp.json()
    alice_stats = next(s for s in stats if s["operator"] == "Alice")
    assert alice_stats["current_load"] == 1