import pytest
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.agents.rpc import router, Agent, get_db, init_db

# Use an in-memory SQLite database for testing
TEST_DB = ":memory:"

def get_test_db():
    if not hasattr(get_test_db, "conn"):
        get_test_db.conn = sqlite3.connect(TEST_DB, check_same_thread=False)
        get_test_db.conn.row_factory = sqlite3.Row
    return get_test_db.conn

# Create a FastAPI app instance for testing
app = FastAPI()
app.include_router(router)

# Override the database dependency

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    print("Setting up test database...")  # Add this line
    conn = get_test_db()
    init_db(conn)
    yield conn

app.dependency_overrides[get_db] = get_test_db

def test_database_initialized(setup_database):
    conn = setup_database
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents';")
    result = cursor.fetchone()
    assert result is not None, "agents table not found in the database"


def test_create_agent(setup_database):
    response = client.post(
        "/create",
        json={
            "name": "Test Agent",
            "system_message": "Test message",
            "human_input_mode": "TERMINATE",
            "max_consecutive_auto_reply": 5,
            "code_execution_config": {"allow_code_execution": True},
            "llm_config": {"model": "gpt-3.5-turbo"},
            "description": "Test description"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Agent"
    assert "id" in data


def test_get_all_agents(setup_database):
    # Create a test agent
    client.post("/create", json={"name": "Test Agent"})

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "Test Agent"


def test_get_agent(setup_database):
    # Create a test agent
    create_response = client.post("/create", json={"name": "Test Agent"})
    agent_id = create_response.json()["id"]

    response = client.get(f"/{agent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["id"] == agent_id


def test_update_agent(setup_database):
    # Create a test agent
    create_response = client.post("/create", json={"name": "Test Agent"})
    agent_id = create_response.json()["id"]

    update_data = {
        "name": "Updated Agent",
        "system_message": "Updated message",
        "human_input_mode": "NEVER",
        "max_consecutive_auto_reply": 10,
        "code_execution_config": {"allow_code_execution": False},
        "llm_config": {"model": "gpt-4"},
        "description": "Updated description"
    }

    response = client.put(f"/{agent_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Agent"
    assert data["system_message"] == "Updated message"


def test_delete_agent(setup_database):
    # Create a test agent
    create_response = client.post("/create", json={"name": "Test Agent"})
    agent_id = create_response.json()["id"]

    response = client.delete(f"/{agent_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Agent deleted successfully"

    # Verify the agent is deleted
    get_response = client.get(f"/{agent_id}")
    assert get_response.status_code == 404


def test_mock_create_agent(setup_database):
    response = client.get("/mock/create")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Mock Agent"
    assert "id" in data