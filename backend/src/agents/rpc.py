import sqlite3
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlite3 import Connection, Cursor

# Define the path for the database file
# This assumes that agents/rpc.py is two levels deep from the project root
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'database.db'))

# Database connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

# Database initialization
def init_db(conn: Connection) -> None:
    cursor: Cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            system_message TEXT,
            human_input_mode TEXT,
            max_consecutive_auto_reply INTEGER,
            code_execution_config TEXT,
            llm_config TEXT,
            description TEXT
        )
    ''')
    conn.commit()

# Initialize the database
conn = get_db_connection()
init_db(conn)
conn.close()

# Pydantic model for Agent
class Agent(BaseModel):
    id: Optional[int] = None
    name: str
    system_message: Optional[str] = "You are a helpful AI Assistant."
    human_input_mode: str = "TERMINATE"
    max_consecutive_auto_reply: Optional[int] = None
    code_execution_config: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

# FastAPI router
router = APIRouter()

# Dependency to get database connection
def get_db():
    print("real get_db called")
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# Helper function to convert a database row to an Agent object
def row_to_agent(row: sqlite3.Row) -> Agent:
    return Agent(
        id=row['id'],
        name=row['name'],
        system_message=row['system_message'],
        human_input_mode=row['human_input_mode'],
        max_consecutive_auto_reply=row['max_consecutive_auto_reply'],
        code_execution_config=eval(row['code_execution_config']) if row['code_execution_config'] else None,
        llm_config=eval(row['llm_config']) if row['llm_config'] else None,
        description=row['description']
    )

@router.get("/mock/create")
async def mock_create_agent(db: Connection = Depends(get_db)) -> Agent:
    print("inside create agent")

    mock_agent = Agent(
        name="Mock Agent",
        system_message="I am a mock agent for testing purposes.",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=5,
        code_execution_config={"allow_code_execution": True},
        llm_config={"model": "gpt-3.5-turbo"},
        description="A mock agent created for testing the API."
    )
    return await create_agent(mock_agent, db)


# Create an agent
@router.post("/create")
async def create_agent(agent: Agent, db: Connection = Depends(get_db)) -> Agent:
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO agents (name, system_message, human_input_mode, max_consecutive_auto_reply, 
                            code_execution_config, llm_config, description)
        VALUES (:name, :system_message, :human_input_mode, :max_consecutive_auto_reply, 
                :code_execution_config, :llm_config, :description)
    ''', {
        "name": agent.name,
        "system_message": agent.system_message,
        "human_input_mode": agent.human_input_mode,
        "max_consecutive_auto_reply": agent.max_consecutive_auto_reply,
        "code_execution_config": str(agent.code_execution_config),
        "llm_config": str(agent.llm_config),
        "description": agent.description
    })
    db.commit()
    agent.id = cursor.lastrowid
    return agent

# Create a mock agent for testing

# Get all agents
@router.get("/")
async def get_all_agents(db: Connection = Depends(get_db)) -> List[Agent]:
    cursor = db.cursor()
    cursor.execute('SELECT * FROM agents')
    agents = cursor.fetchall()
    return [row_to_agent(agent) for agent in agents]

# Get a specific agent
@router.get("/{agent_id}")
async def get_agent(agent_id: int, db: Connection = Depends(get_db)) -> Agent:
    cursor = db.cursor()
    cursor.execute('SELECT * FROM agents WHERE id = :agent_id', {"agent_id": agent_id})
    agent = cursor.fetchone()
    if agent:
        return row_to_agent(agent)
    raise HTTPException(status_code=404, detail="Agent not found")

# Update an agent
@router.put("/{agent_id}")
async def update_agent(agent_id: int, agent: Agent, db: Connection = Depends(get_db)) -> Agent:
    cursor = db.cursor()
    cursor.execute('''
        UPDATE agents 
        SET name=:name, system_message=:system_message, human_input_mode=:human_input_mode, 
            max_consecutive_auto_reply=:max_consecutive_auto_reply,
            code_execution_config=:code_execution_config, llm_config=:llm_config, description=:description
        WHERE id=:agent_id
    ''', {
        "name": agent.name,
        "system_message": agent.system_message,
        "human_input_mode": agent.human_input_mode,
        "max_consecutive_auto_reply": agent.max_consecutive_auto_reply,
        "code_execution_config": str(agent.code_execution_config),
        "llm_config": str(agent.llm_config),
        "description": agent.description,
        "agent_id": agent_id
    })
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.id = agent_id
    return agent

# Delete an agent
@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: Connection = Depends(get_db)) -> Dict[str, str]:
    cursor = db.cursor()
    cursor.execute('DELETE FROM agents WHERE id = :agent_id', {"agent_id": agent_id})
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}