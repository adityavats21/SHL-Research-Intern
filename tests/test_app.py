from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def chat(*contents: str):
    messages = [{"role": "user", "content": c} for c in contents]
    return client.post("/chat", json={"messages": messages})


def names(response):
    return [r["name"] for r in response.json()["recommendations"]]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_vague_query_clarifies_without_recommendations():
    response = chat("I need an assessment")
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert body["end_of_conversation"] is False


def test_java_refinement_catalog_urls():
    response = chat(
        "Senior Full-Stack Engineer with Core Java, Spring, REST APIs, SQL, AWS and Docker.",
        "Backend-leaning role.",
        "Senior IC.",
        "Add AWS and Docker. Drop REST.",
    )
    assert response.status_code == 200
    got = names(response)
    assert "Core Java (Advanced Level) (New)" in got
    assert "Amazon Web Services (AWS) Development (New)" in got
    assert "Docker (New)" in got
    assert "RESTful Web Services (New)" not in got
    for rec in response.json()["recommendations"]:
        assert rec["url"].startswith("https://www.shl.com/products/product-catalog/view/")


def test_legal_question_refuses():
    response = chat("Are we legally required under HIPAA to test all staff?")
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert "cannot answer legal" in body["reply"]


def test_sales_trace_shortlist():
    response = chat("As part of annual talent audit, we need to re-skill our Sales organization.")
    got = names(response)
    assert got[:2] == ["Global Skills Assessment", "Global Skills Development Report"]
    assert "OPQ MQ Sales Report" in got
