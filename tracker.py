# tracker.py

import sqlite3
from typing import List, Dict

DB_FILE = "exposure_tracker.db"

def init_db():
    """Initializes local SQLite database tables."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                location TEXT,
                email TEXT,
                score INTEGER,
                status TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                category TEXT,
                source TEXT,
                title TEXT,
                url TEXT,
                opt_out_url TEXT,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (scan_id) REFERENCES scans(id)
            )
        """)
        conn.commit()

def save_scan_results(target: dict, score: int, status: str, findings: List[dict]) -> int:
    """Saves scan run and associated findings to local database."""
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scans (name, location, email, score, status) VALUES (?, ?, ?, ?, ?)",
            (target.get("name"), target.get("location"), target.get("email"), score, status)
        )
        scan_id = cursor.lastrowid
        
        for item in findings:
            cursor.execute(
                "INSERT INTO findings (scan_id, category, source, title, url, opt_out_url, status) VALUES (?, ?, ?, ?, ?, ?, 'Pending')",
                (scan_id, item.get("category"), item.get("source"), item.get("title"), item.get("url"), item.get("opt_out_url", "N/A"))
            )
        conn.commit()
        return scan_id

def update_finding_status(finding_id: int, new_status: str):
    """Updates status of a finding ('Pending' or 'Removed')."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE findings SET status = ? WHERE id = ?", (new_status, finding_id))
        conn.commit()

def get_latest_scan_findings() -> tuple:
    """Fetches findings from the most recent scan."""
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, score, status FROM scans ORDER BY id DESC LIMIT 1")
        scan = cursor.fetchone()
        if not scan:
            return None, 0, "No Scans Found", []
            
        scan_id, score, status = scan
        cursor.execute("SELECT id, category, source, title, url, opt_out_url, status FROM findings WHERE scan_id = ?", (scan_id,))
        rows = cursor.fetchall()
        
        findings = [
            {
                "id": r[0],
                "category": r[1],
                "source": r[2],
                "title": r[3],
                "url": r[4],
                "opt_out_url": r[5],
                "status": r[6]
            } for r in rows
        ]
        return scan_id, score, status, findings

def recalculate_active_score(scan_id: int) -> tuple:
    """Recalculates risk score considering only 'Pending' un-removed findings."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, status FROM findings WHERE scan_id = ?", (scan_id,))
        rows = cursor.fetchall()
        
    pending_brokers = sum(1 for r in rows if r[0] == "Data Broker" and r[1] == "Pending")
    pending_breaches = sum(1 for r in rows if r[0] == "Breach Leak" and r[1] == "Pending")
    pending_dorks = sum(1 for r in rows if r[0] in ["Paste Leak", "Document Leak"] and r[1] == "Pending")
    
    score = min((pending_brokers * 5) + (pending_breaches * 8) + (pending_dorks * 5), 100)
    
    if score == 0:
        status = "🟢 RAW (All items resolved or clean)"
    elif score < 30:
        status = "🟡 RARE (Low active risk)"
    elif score < 60:
        status = "🟠 MEDIUM WELL (Moderate active exposure)"
    else:
        status = "🔴 FULLY COOKED (High active exposure)"
        
    return score, status