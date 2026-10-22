# job-tracker

A tiny CLI (Python + SQLite, no dependencies) that tracks job applications through stages and tells you what is actually working: where your funnel leaks, which sources get replies, and how long each stage takes.

## The product problem

A job search is a pipeline, but most people run it from a messy spreadsheet and gut feel. They cannot answer the questions that would change their behaviour: *Do referrals really convert better than cold applies? Am I failing at screening or at interviews? How long should I wait before following up?* This tool treats each application as a sequence of dated stage events so those answers fall out of simple queries.

## Quickstart

```bash
pip install -e ".[dev]"
jobtracker --db jobs.db seed                       # optional sample data
jobtracker add "Notion" "Associate PM" --source Referral
jobtracker move 13 Screen --date 2026-10-01
jobtracker list
jobtracker stats
pytest
```

Sample `stats` output (seed data):

```
Funnel (reached stage / conversion from previous)
  Applied     12
  Screen       6  50%
  Interview    4  67%
  Offer        2  50%
  Accepted     1  50%
```

## Concepts

- **Stages:** Applied > Screen > Interview > Offer > Accepted, plus terminal Rejected / Withdrawn.
- **Funnel:** applications that ever reached each stage, with stage-to-stage conversion.
- **Response rate:** share of applications that moved beyond Applied (a rejection counts as a response), grouped by source.
- **Average days per stage:** mean time from entering a stage to the next event, over completed stays only (open applications are not guessed at).
- Events are append-only and date-validated, so history is never rewritten.

## Structure

```
job_tracker/db.py     schema, add/move, funnel / response / timing analytics
job_tracker/seed.py   sample applications
job_tracker/cli.py    `jobtracker` command
tests/                analytics and CLI tests (temp SQLite DBs)
```

## Roadmap

- Follow-up reminders based on average days per stage
- Notes, contacts and salary fields
- CSV import/export
- Small web dashboard (FastAPI) with funnel chart
- Cohort views by week applied

## License

MIT
