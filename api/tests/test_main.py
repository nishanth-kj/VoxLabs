
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add api directory to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 1
    assert data["data"]["name"] == "VoxLabs API"

def test_get_emotions():
    response = client.get("/api/emotions")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 1
    assert "emotions" in data["data"]
    assert "neutral" in data["data"]["emotions"]

def test_get_voices():
    response = client.get("/api/voices")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 1
    assert isinstance(data["data"]["voices"], list)

def test_404_on_unknown_endpoint():
    response = client.get("/api/unknown")
    assert response.status_code == 404
