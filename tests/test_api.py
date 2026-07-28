"""
   -> TestClient is a fake HTTP client that FastAPI gives you for testing.
It lets you send fake requests to your app without actually starting a running server — no uvicorn, no real port, no network.
It just calls your app in-process, but behaves exactly like a real HTTP call would.
    
    -> Big picture for this file: these are integration tests — 
    they check that the whole chain works: HTTP request → FastAPI route → Pydantic validates the input → calls the utility function → wraps the result → sends back JSON.
    It's testing the wiring, not just the logic.
    
"""


from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app=app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    
def test_slugify_endpoint():
    resp = client.post("/string/slugify", json={"text": "Hello World!"})
    assert resp.status_code == 200
    assert resp.json() == {"result": "hello-world"}


def test_is_prime_endpoint():
    resp = client.post("/math/is-prime", json={"n": 7})
    assert resp.status_code == 200
    assert resp.json() == {"result": True}


def test_flatten_endpoint():
    resp = client.post("/json/flatten", json={"data": {"a": {"b": 1}}})
    assert resp.status_code == 200
    assert resp.json() == {"result": {"a.b": 1}}
