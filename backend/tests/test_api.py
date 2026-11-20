
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["project"] == "MathGenius AI"
    assert data["status"] == "running"


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "math-engine-api"


def test_solve_linear_equation():
    response = client.post(
        "/api/solve",
        json={"problem": "3x+9=0"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["answer"] == ["-3"]
    assert data["verified"] is True


def test_solve_quadratic_equation():
    response = client.post(
        "/api/solve",
        json={"problem": "x^2+5x+6=0"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["answer"] == ["-3", "-2"]
    assert data["verified"] is True


def test_solve_complex_roots():
    response = client.post(
        "/api/solve",
        json={"problem": "x^2+4=0"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["answer"] == ["-2*I", "2*I"]
    assert data["verified"] is True
    assert len(data["steps"]) == len(data["step_formulas"])


def test_invalid_math_input():
    response = client.post(
        "/api/solve",
        json={"problem": "hello"}
    )

    assert response.status_code == 400


def test_empty_problem():
    response = client.post(
        "/api/solve",
        json={"problem": ""}
    )

    assert response.status_code == 422


def test_missing_problem():
    response = client.post(
        "/api/solve",
        json={}
    )

    assert response.status_code == 422


def test_problem_exceeds_maximum_length():
    response = client.post(
        "/api/solve",
        json={"problem": "1" * 201}
    )

    assert response.status_code == 422

def test_identity_equation_api():
    response = client.post(
        "/api/solve",
        json={"problem": "x-x=0"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["answer"] == ["All values of x"]
    assert data["verified"] is True
    assert "infinitely many" in data["message"].lower()
    assert len(data["steps"]) == len(data["step_formulas"])


def test_inconsistent_equation_api():
    response = client.post(
        "/api/solve",
        json={"problem": "x-x=5"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["answer"] == []
    assert data["verified"] is True
    assert "no solutions" in data["message"].lower()
    assert len(data["steps"]) == len(data["step_formulas"])


def test_unexpected_solver_error_returns_generic_500(monkeypatch):
    def raise_unexpected_error(problem):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(
        "backend.app.main.solve_math",
        raise_unexpected_error,
    )

    response = client.post(
        "/api/solve",
        json={"problem": "2+2"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "An internal error occurred while solving the problem."
    )
    assert "secret internal detail" not in response.text
