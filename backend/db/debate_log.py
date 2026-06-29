"""Database storage for debate logs."""

import json
import logging
import sqlite3
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the SQLite database schema."""
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            dataset_name TEXT,
            max_params INTEGER,
            target_latency_ms REAL,
            max_iterations INTEGER,
            final_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debate_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            iteration INTEGER,
            agent TEXT,
            action TEXT,
            message TEXT,
            data_json TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_session(session_id: str, config: dict):
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO sessions (session_id, dataset_name, max_params, target_latency_ms, max_iterations, final_status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session_id, 
        config.get("dataset_name"), 
        config.get("max_params"), 
        config.get("target_latency_ms"), 
        config.get("max_iterations"), 
        "started"
    ))
    conn.commit()
    conn.close()

def save_log_entry(session_id: str, entry: dict):
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO debate_logs (session_id, iteration, agent, action, message, data_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        entry.get("iteration", 0),
        entry.get("agent", "system"),
        entry.get("action", "unknown"),
        entry.get("message", ""),
        json.dumps(entry.get("data", {})),
        entry.get("timestamp", "")
    ))
    conn.commit()
    conn.close()

def update_session_status(session_id: str, status: str):
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sessions SET final_status = ? WHERE session_id = ?
    ''', (status, session_id))
    conn.commit()
    conn.close()

def get_session_status(session_id: str) -> str:
    db_path = settings.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT final_status FROM sessions WHERE session_id = ?
    ''', (session_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""
