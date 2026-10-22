"""Realistic sample data: (company, role, source, [(stage, date), ...])."""
SEED = [
    ("Razorpay", "Associate PM", "LinkedIn", [("Applied", "2026-08-03"), ("Screen", "2026-08-08"), ("Interview", "2026-08-18"), ("Offer", "2026-08-30")]),
    ("Swiggy", "APM", "Referral", [("Applied", "2026-08-05"), ("Screen", "2026-08-07"), ("Interview", "2026-08-14"), ("Rejected", "2026-08-25")]),
    ("CRED", "Product Analyst", "LinkedIn", [("Applied", "2026-08-06"), ("Rejected", "2026-08-20")]),
    ("Zepto", "Associate PM", "Careers page", [("Applied", "2026-08-10"), ("Screen", "2026-08-19")]),
    ("Meesho", "APM", "Referral", [("Applied", "2026-08-12"), ("Screen", "2026-08-14"), ("Interview", "2026-08-21"), ("Offer", "2026-09-02"), ("Accepted", "2026-09-05")]),
    ("Flipkart", "Product Manager", "LinkedIn", [("Applied", "2026-08-15")]),
    ("PhonePe", "Associate PM", "Job board", [("Applied", "2026-08-18"), ("Rejected", "2026-09-01")]),
    ("Groww", "Product Analyst", "Job board", [("Applied", "2026-08-20")]),
    ("Atlassian", "Associate PM", "Careers page", [("Applied", "2026-08-22"), ("Screen", "2026-09-01"), ("Rejected", "2026-09-10")]),
    ("Freshworks", "APM", "Referral", [("Applied", "2026-08-25"), ("Screen", "2026-08-28"), ("Interview", "2026-09-06")]),
    ("Zomato", "Associate PM", "LinkedIn", [("Applied", "2026-09-01")]),
    ("Paytm", "Product Associate", "Job board", [("Applied", "2026-09-03"), ("Withdrawn", "2026-09-12")]),
]


def load(conn) -> int:
    from .db import add_application, move
    for company, role, source, events in SEED:
        app_id = add_application(conn, company, role, source, events[0][1])
        for stage, day in events[1:]:
            move(conn, app_id, stage, day)
    return len(SEED)
