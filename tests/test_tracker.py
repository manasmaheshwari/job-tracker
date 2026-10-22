import pytest

from job_tracker import db, seed
from job_tracker.cli import main


@pytest.fixture
def conn(tmp_path):
    c = db.connect(str(tmp_path / "t.db"))
    yield c
    c.close()


def test_add_and_move(conn):
    i = db.add_application(conn, "Acme", "APM", "LinkedIn", "2026-01-01")
    db.move(conn, i, "Screen", "2026-01-05")
    assert db.list_applications(conn)[0]["stage"] == "Screen"


def test_move_validation(conn):
    i = db.add_application(conn, "Acme", "APM", "X", "2026-01-10")
    with pytest.raises(ValueError):
        db.move(conn, i, "Nonsense")
    with pytest.raises(ValueError):
        db.move(conn, 999, "Screen")
    with pytest.raises(ValueError):
        db.move(conn, i, "Screen", "2026-01-01")  # before applied date
    db.move(conn, i, "Rejected", "2026-01-12")
    with pytest.raises(ValueError):
        db.move(conn, i, "Screen", "2026-01-13")  # already closed


def test_funnel_counts_and_conversion(conn):
    a = db.add_application(conn, "A", "r", "s", "2026-01-01")
    b = db.add_application(conn, "B", "r", "s", "2026-01-01")
    db.add_application(conn, "C", "r", "s", "2026-01-01")
    db.move(conn, a, "Screen", "2026-01-02")
    db.move(conn, a, "Interview", "2026-01-03")
    db.move(conn, b, "Screen", "2026-01-02")
    db.move(conn, b, "Rejected", "2026-01-04")
    f = {r["stage"]: r for r in db.funnel(conn)}
    assert [f[s]["count"] for s in db.PIPELINE] == [3, 2, 1, 0, 0]
    assert f["Screen"]["conversion"] == pytest.approx(2 / 3)
    assert f["Offer"]["conversion"] == 0.0


def test_response_rate_by_source(conn):
    a = db.add_application(conn, "A", "r", "Referral", "2026-01-01")
    db.add_application(conn, "B", "r", "Referral", "2026-01-01")
    c = db.add_application(conn, "C", "r", "Board", "2026-01-01")
    db.move(conn, a, "Screen", "2026-01-03")
    db.move(conn, c, "Rejected", "2026-01-03")  # a rejection still counts as a response
    rates = {r["source"]: r for r in db.response_rate_by_source(conn)}
    assert rates["Referral"]["rate"] == 0.5
    assert rates["Board"]["rate"] == 1.0


def test_avg_days_per_stage(conn):
    a = db.add_application(conn, "A", "r", "s", "2026-01-01")
    b = db.add_application(conn, "B", "r", "s", "2026-01-01")
    db.move(conn, a, "Screen", "2026-01-05")   # Applied 4 days
    db.move(conn, b, "Screen", "2026-01-09")   # Applied 8 days
    db.move(conn, a, "Interview", "2026-01-15")  # Screen 10 days
    d = {r["stage"]: r for r in db.avg_days_per_stage(conn)}
    assert d["Applied"]["avg_days"] == 6 and d["Applied"]["samples"] == 2
    assert d["Screen"]["avg_days"] == 10


def test_seed_loads_and_stats_sane(conn):
    n = seed.load(conn)
    assert n == len(db.list_applications(conn)) == len(seed.SEED)
    f = db.funnel(conn)
    assert f[0]["count"] == n
    assert all(f[i]["count"] >= f[i + 1]["count"] for i in range(len(f) - 1))
    assert sum(r["applications"] for r in db.response_rate_by_source(conn)) == n


def test_cli_flow(tmp_path, capsys):
    path = str(tmp_path / "c.db")
    assert main(["--db", path, "stats"]) == 1  # empty
    assert main(["--db", path, "seed"]) == 0
    assert main(["--db", path, "seed"]) == 1  # not empty
    assert main(["--db", path, "add", "Notion", "APM", "--source", "Referral", "--date", "2026-09-20"]) == 0
    assert main(["--db", path, "move", "13", "Screen", "--date", "2026-09-25"]) == 0
    capsys.readouterr()
    assert main(["--db", path, "stats"]) == 0
    out = capsys.readouterr().out
    assert "Funnel" in out and "Response rate by source" in out and "Average days per stage" in out
