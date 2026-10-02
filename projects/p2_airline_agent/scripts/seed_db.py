# Utility script to inspect or reset database seeds.
"""CLI script to display or verify mock database seeds."""

import json
from airline_agent.domain.database import get_all_bookings, reset_database


def main() -> None:
    """Print current seed data."""
    reset_database()
    bookings = get_all_bookings()
    print("--- Mock Airline Database Seed State ---")
    print(json.dumps(bookings, indent=2))
    print(f"\nTotal Records: {len(bookings)}")


if __name__ == "__main__":
    main()
