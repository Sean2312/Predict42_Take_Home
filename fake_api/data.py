"""Deterministic generator for the fake case dataset.

Same seed on every start, so every candidate gets byte-identical data and
runs are reproducible.
"""

import random
from datetime import datetime, timedelta

SEED = 42
N_CASES = 4_300

CATEGORIES = [
    "Payment",
    "payment ",
    "PAYMENT",
    "Delivery",
    " delivery",
    "Product Quality",
    "product quality",
    "Other",
]
COUNTRIES = ["DE", "de", "Deutschland", "AT", "at", "CH"]
START = datetime(2026, 6, 1, 0, 0, 0)


def _fmt_created(dt: datetime, style: int) -> str:
    """Two date formats in the same field, like most real APIs."""
    if style == 0:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%d.%m.%Y %H:%M")


def _build_case(rng: random.Random, i: int) -> dict:
    created = START + timedelta(
        days=rng.randint(0, 89), hours=rng.randint(0, 23), minutes=rng.randint(0, 59)
    )
    handling = rng.randint(3, 900)
    closed = created + timedelta(minutes=handling)

    is_open = rng.random() < 0.18
    is_deleted = rng.random() < 0.03

    case = {
        "case_id": f"CS-{i:06d}",
        # leading zeros matter -- this is a code, not a number
        "store_no": f"{rng.randint(1, 3999):05d}",
        "created_at": _fmt_created(created, rng.randint(0, 1)),
        "last_modified": closed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "closed_at": None if is_open else closed.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "category": rng.choice(CATEGORIES),
        # priority arrives as a string, sometimes empty, sometimes missing
        "priority": rng.choice(["1", "2", "3", "3", "", None]),
        "status": "Open" if is_open else rng.choice(["Closed", "closed", "Resolved"]),
        # numbers as strings, plus some impossible values
        "handling_minutes": str(handling) if rng.random() > 0.04 else str(-handling),
        "customer": {
            "id": f"C{rng.randint(1000, 9999)}",
            "country": rng.choice(COUNTRIES),
            "email": None if rng.random() < 0.2 else f"cust{i}@example.invalid",
        },
        "comment": rng.choice(["", None, "Kunde erneut kontaktiert", "n/a", "  "]),
        "deleted": is_deleted,
    }
    if rng.random() < 0.06:
        # field simply absent instead of null
        case.pop("comment")
    return case


def build_dataset() -> list[dict]:
    """All cases, plus extra revisions of some of them.

    A case that was touched several times shows up several times with a
    different ``last_modified`` -- only the newest revision is the truth.
    """
    rng = random.Random(SEED)
    cases = [_build_case(rng, i) for i in range(1, N_CASES + 1)]

    revisions: list[dict] = []
    for case in cases:
        n_extra = rng.choices([0, 1, 2, 3], weights=[70, 20, 7, 3])[0]
        for _ in range(n_extra):
            older = dict(case)
            older["customer"] = dict(case["customer"])
            back = timedelta(hours=rng.randint(1, 240))
            older["last_modified"] = (
                datetime.strptime(case["last_modified"], "%Y-%m-%dT%H:%M:%SZ") - back
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            older["status"] = "In Progress"
            older["closed_at"] = None
            older["priority"] = rng.choice(["1", "2", "3"])
            revisions.append(older)

    everything = cases + revisions
    rng.shuffle(everything)
    return everything


DATASET = build_dataset()
