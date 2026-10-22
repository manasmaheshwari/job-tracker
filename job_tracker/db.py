"""SQLite storage and analytics for job applications."""
from __future__ import annotations

import sqlite3
from datetime import date

PIPELINE = ["Applied", "Screen", "Interview", "Offer", "Accepted"]
TERMINAL = ["Rejected", "Withdrawn"]
STAGES = PIPELINE + TERMINAL

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company TEXT NOT NULL, role TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'Unknown',
  stage TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stage_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id INTEGER NOT NULL REFERENCES applications(id),
  stage TEXT NOT NULL, entered_on TEXT NOT NULL
);
"""


def connect(path: str = "jobs.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_application(conn, company: str, role: str, source: str = "Unknown", applied_on: str | None = None) -> int:
    cur = conn.execute("INSERT INTO applications (company, role, source, stage) VALUES (?,?,?,?)",
                       (company, role, source, "Applied"))
    conn.execute("INSERT INTO stage_events (application_id, stage, entered_on) VALUES (?,?,?)",
                 (cur.lastrowid, "Applied", applied_on or date.today().isoformat()))
    conn.commit()
    return cur.lastrowid


def move(conn, app_id: int, stage: str, on: str | None = None) -> None:
    if stage not in STAGES:
        raise ValueError(f"unknown stage '{stage}'; choose from {', '.join(STAGES)}")
    row = conn.execute("SELECT stage FROM applications WHERE id=?", (app_id,)).fetchone()
    if row is None:
        raise ValueError(f"no application with id {app_id}")
    if row["stage"] in TERMINAL or row["stage"] == "Accepted":
        raise ValueError(f"application is already closed ({row['stage']})")
    when = on or date.today().isoformat()
    last = conn.execute("SELECT MAX(entered_on) m FROM stage_events WHERE application_id=?", (app_id,)).fetchone()["m"]
    if when < last:
        raise ValueError(f"date {when} is before the previous event ({last})")
    conn.execute("UPDATE applications SET stage=? WHERE id=?", (stage, app_id))
    conn.execute("INSERT INTO stage_events (application_id, stage, entered_on) VALUES (?,?,?)", (app_id, stage, when))
    conn.commit()


def list_applications(conn):
    return conn.execute("SELECT * FROM applications ORDER BY id").fetchall()


def _events_by_app(conn) -> dict[int, list[tuple[str, date]]]:
    out: dict[int, list] = {}
    for r in conn.execute("SELECT application_id, stage, entered_on FROM stage_events ORDER BY entered_on, id"):
        out.setdefault(r["application_id"], []).append((r["stage"], date.fromisoformat(r["entered_on"])))
    return out


def funnel(conn) -> list[dict]:
    """Applications that reached each pipeline stage, with conversion from the previous stage."""
    events = _events_by_app(conn)
    reached = {s: 0 for s in PIPELINE}
    for evs in events.values():
        top = max((PIPELINE.index(s) for s, _ in evs if s in PIPELINE), default=0)
        for s in PIPELINE[: top + 1]:
            reached[s] += 1
    rows, prev = [], None
    for s in PIPELINE:
        n = reached[s]
        rows.append({"stage": s, "count": n,
                     "conversion": None if prev is None else (n / prev if prev else 0.0)})
        prev = n
    return rows


def response_rate_by_source(conn) -> list[dict]:
    """Response = the application moved beyond 'Applied' (any reply, including a rejection)."""
    events = _events_by_app(conn)
    stats: dict[str, list[int]] = {}
    for a in conn.execute("SELECT id, source FROM applications"):
        s = stats.setdefault(a["source"], [0, 0])
        s[0] += 1
        if len(events.get(a["id"], [])) > 1:
            s[1] += 1
    return sorted(({"source": k, "applications": v[0], "responses": v[1], "rate": v[1] / v[0]}
                   for k, v in stats.items()), key=lambda r: (-r["rate"], r["source"]))


def avg_days_per_stage(conn) -> list[dict]:
    """Average days spent in each stage, from entering it until the next event (completed stays only)."""
    durations: dict[str, list[int]] = {}
    for evs in _events_by_app(conn).values():
        for (stage, start), (_, end) in zip(evs, evs[1:]):
            durations.setdefault(stage, []).append((end - start).days)
    return [{"stage": s, "avg_days": sum(durations[s]) / len(durations[s]), "samples": len(durations[s])}
            for s in PIPELINE if s in durations]
