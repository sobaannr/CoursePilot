from fastapi.testclient import TestClient
from coursepilot.api import app

client=TestClient(app)

def test_health_and_catalogue():
    assert client.get("/health").json()["status"]=="ok"
    assert len(client.get("/courses").json()["courses"])==74

def test_recommend():
    r=client.post("/recommend",json={"query":"personalized recommendation", "interests":{"recommender systems":5}})
    assert r.status_code==200
    assert r.json()["recommendations"][0]["code"]=="CS4053"

def test_invalid_requests():
    for body in [{"k":0},{"k":1.5},{"method":"fake"},{"completed":["FAKE"]},{"interests":{"machine learning":-1}},{"extra":True}]:
        assert client.post("/recommend",json=body).status_code==422
