import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.config import settings
from app.schemas import AuditEntry, ReviewerActionEnum, ReviewerActorEnum

class AuditLogManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()

    def _get_connection(self):
        try:
            return sqlite3.connect(self.db_path)
        except (sqlite3.OperationalError, OSError):
            self.db_path = "/tmp/citeverify.db"
            try:
                return sqlite3.connect(self.db_path)
            except (sqlite3.OperationalError, OSError):
                return sqlite3.connect(":memory:")

    def _init_db(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    claim_id TEXT NOT NULL,
                    pair_id TEXT,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    before_value TEXT,
                    after_value TEXT,
                    note TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    def record_entry(
        self,
        claim_id: str,
        pair_id: Optional[str],
        actor: ReviewerActorEnum,
        action: ReviewerActionEnum,
        before_value: Optional[Dict[str, Any]] = None,
        after_value: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None
    ) -> AuditEntry:
        entry_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        entry = AuditEntry(
            id=entry_id,
            claim_id=claim_id,
            pair_id=pair_id,
            timestamp=now_iso,
            actor=actor,
            action=action,
            before_value=before_value,
            after_value=after_value,
            note=note
        )
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_log (id, claim_id, pair_id, timestamp, actor, action, before_value, after_value, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.id,
                entry.claim_id,
                entry.pair_id,
                entry.timestamp,
                entry.actor.value,
                entry.action.value,
                json.dumps(entry.before_value) if entry.before_value else None,
                json.dumps(entry.after_value) if entry.after_value else None,
                entry.note
            )
        )
        conn.commit()
        conn.close()
        return entry

    def get_entries_for_claim(self, claim_id: str) -> List[AuditEntry]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, claim_id, pair_id, timestamp, actor, action, before_value, after_value, note
            FROM audit_log
            WHERE claim_id = ?
            ORDER BY timestamp ASC
            """,
            (claim_id,)
        )
        rows = cur.fetchall()
        conn.close()
        entries = []
        for r in rows:
            entries.append(AuditEntry(
                id=r[0],
                claim_id=r[1],
                pair_id=r[2],
                timestamp=r[3],
                actor=ReviewerActorEnum(r[4]),
                action=ReviewerActionEnum(r[5]),
                before_value=json.loads(r[6]) if r[6] else None,
                after_value=json.loads(r[7]) if r[7] else None,
                note=r[8]
            ))
        return entries

    def get_all_entries(self) -> List[AuditEntry]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, claim_id, pair_id, timestamp, actor, action, before_value, after_value, note
            FROM audit_log
            ORDER BY timestamp ASC
            """
        )
        rows = cur.fetchall()
        conn.close()
        entries = []
        for r in rows:
            entries.append(AuditEntry(
                id=r[0],
                claim_id=r[1],
                pair_id=r[2],
                timestamp=r[3],
                actor=ReviewerActorEnum(r[4]),
                action=ReviewerActionEnum(r[5]),
                before_value=json.loads(r[6]) if r[6] else None,
                after_value=json.loads(r[7]) if r[7] else None,
                note=r[8]
            ))
        return entries

audit_manager = AuditLogManager()
