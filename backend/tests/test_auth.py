from fastapi.testclient import TestClient
from app.main import app
from app.auth import digest, ph
def test_password():
    h=ph.hash("long-test-password")
    assert ph.verify(h,"long-test-password")
    assert digest("token") != "token"
def test_origin():
    assert TestClient(app).post("/auth/logout").status_code==403
