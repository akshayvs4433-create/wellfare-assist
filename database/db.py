"""
WelfareAssist - Privacy-Preserving SQLite Audit Storage
Stores only anonymous aggregate screening events. Zero personal identifiable data (PII).
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "welfareai.db")


def init_db(db_path: str = DB_PATH):
    """Initializes the SQLite schema."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                occupation TEXT,
                district TEXT,
                eligible_count INTEGER DEFAULT 0,
                more_info_count INTEGER DEFAULT 0,
                language TEXT DEFAULT 'en'
            )
        """)
        conn.commit()


def log_screening_event(
    occupation: Optional[str],
    district: Optional[str],
    eligible_count: int,
    more_info_count: int,
    language: str = "en",
    db_path: str = DB_PATH
) -> int:
    """Logs an anonymous screening event for hackathon demonstration audits."""
    init_db(db_path)
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO screening_audit 
            (timestamp, occupation, district, eligible_count, more_info_count, language)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (now, occupation or "unknown", district or "unknown", eligible_count, more_info_count, language))
        conn.commit()
        return cursor.lastrowid or 0


def get_screening_stats(db_path: str = DB_PATH) -> Dict[str, Any]:
    """Returns basic anonymous screening statistics."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(eligible_count) FROM screening_audit")
        row = cursor.fetchone()
        return {
            "total_screenings": row[0] or 0,
            "total_matches_found": row[1] or 0
        }

