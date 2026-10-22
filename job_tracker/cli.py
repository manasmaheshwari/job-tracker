import argparse
import sys

from . import db, seed


def _print_stats(conn) -> None:
    print("Funnel (reached stage / conversion from previous)")
    for r in db.funnel(conn):
        conv = "" if r["conversion"] is None else f"  {r['conversion']:.0%}"
        print(f"  {r['stage']:<10} {r['count']:>3}{conv}")
    print("\nResponse rate by source")
    for r in db.response_rate_by_source(conn):
        print(f"  {r['source']:<14} {r['responses']}/{r['applications']}  {r['rate']:.0%}")
    print("\nAverage days per stage")
    for r in db.avg_days_per_stage(conn):
        print(f"  {r['stage']:<10} {r['avg_days']:.1f} days (n={r['samples']})")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jobtracker", description="Track job applications and analyse your funnel.")
    ap.add_argument("--db", default="jobs.db")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="log a new application")
    a.add_argument("company")
    a.add_argument("role")
    a.add_argument("--source", default="Unknown")
    a.add_argument("--date", help="applied date YYYY-MM-DD (default today)")
    m = sub.add_parser("move", help="move an application to a new stage")
    m.add_argument("id", type=int)
    m.add_argument("stage", choices=db.STAGES)
    m.add_argument("--date", help="YYYY-MM-DD (default today)")
    sub.add_parser("list", help="list applications")
    sub.add_parser("stats", help="funnel, response rate by source, avg days per stage")
    sub.add_parser("seed", help="load sample data into an empty database")
    args = ap.parse_args(argv)

    conn = db.connect(args.db)
    try:
        if args.cmd == "add":
            print(f"Added #{db.add_application(conn, args.company, args.role, args.source, args.date)}")
        elif args.cmd == "move":
            db.move(conn, args.id, args.stage, args.date)
            print(f"#{args.id} -> {args.stage}")
        elif args.cmd == "list":
            for r in db.list_applications(conn):
                print(f"#{r['id']:<3} {r['company']:<12} {r['role']:<18} {r['source']:<13} {r['stage']}")
        elif args.cmd == "seed":
            if db.list_applications(conn):
                raise ValueError("database is not empty; use a fresh --db file")
            print(f"Loaded {seed.load(conn)} sample applications")
        else:
            if not db.list_applications(conn):
                raise ValueError("no applications yet; add some or run `seed`")
            _print_stats(conn)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
