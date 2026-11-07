"""
Fetch level data from the Impossible Levels List (ILL) API,
decode tags and tiers dynamically, extract creators, and save everything to CSV + JSON.

Three modes:
    1) TOP N MODE      - grab the top N levels (e.g. top 100, top 2000)
    2) SPECIFIC MODE    - grab just ONE level by its exact rank (e.g. only rank #53)
    3) ALL MODE         - grab every single available level on the list

Requirements:
    pip install requests

Usage:
    python ILL_data_grabber.py                 # interactive menu, asks you which mode you want
    python ILL_data_grabber.py --top 100        # grabs the top 100 levels -> top_100_levels.csv/.json
    python ILL_data_grabber.py --rank 53        # grabs ONLY rank #53      -> level_53.csv/.json
    python ILL_data_grabber.py --all            # grabs EVERY available level -> ILL_data.json / ILL_data.csv
    python ILL_data_grabber.py --top 250 -o custom_name   # override output filename
"""

import argparse
import requests
import json
import csv
import time

API_BASE = "https://api.impossiblelevels.com/api"
PAGE_SIZE = 100

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ILL-data-fetch/2.0)",
    "Accept": "application/json",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch level data from the Impossible Levels List (ILL) API."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-t", "--top",
        type=int,
        default=None,
        help="Grab the top N levels (e.g. --top 100 grabs ranks 1-100).",
    )
    group.add_argument(
        "-r", "--rank",
        type=int,
        default=None,
        help="Grab ONLY the level at this exact rank (e.g. --rank 53 grabs only #53).",
    )
    group.add_argument(
        "-a", "--all",
        action="store_true",
        help="Grab EVERY single available level on the list -> ILL_data.json / ILL_data.csv",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Base filename (without extension) for output files. "
             "Defaults to 'top_<N>_levels' or 'level_<rank>' depending on mode.",
    )
    return parser.parse_args()


def get_mode_interactively():
    """Ask the user whether they want top-N mode, a single specific level, or ALL levels."""
    print("What would you like to grab?")
    print("  1) Top N levels (e.g. the top 100 hardest levels)")
    print("  2) One specific level by rank (e.g. only the #53 hardest level)")
    print("  3) EVERY single available level on the list")
    choice = input("Enter 1, 2, or 3 [default: 1]: ").strip()

    if choice == "2":
        while True:
            raw = input("Which rank would you like to grab? (e.g. 53): ").strip()
            try:
                rank = int(raw)
                if rank <= 0:
                    print("Rank must be a positive number.")
                    continue
                return None, rank, False
            except ValueError:
                print("Please enter a valid whole number.")
    elif choice == "3":
        return None, None, True
    else:
        raw = input("How many top levels would you like to grab? [default: 2000]: ").strip()
        if not raw:
            return 2000, None, False
        try:
            n = int(raw)
            if n <= 0:
                print("Value must be positive, using default of 2000.")
                return 2000, None, False
            return n, None, False
        except ValueError:
            print("Invalid number, using default of 2000.")
            return 2000, None, False


def fetch_tiers():
    """Fetch tier bracket definitions dynamically from /api/Tiers"""
    r = requests.get(f"{API_BASE}/Tiers", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def get_tier(rank, tiers_data):
    """Determine the tier name dynamically based on rank"""
    for t in tiers_data:
        if t.get("start", 0) <= rank <= t.get("end", float('inf')):
            return t.get("name", "")
    return "Unknown"


def fetch_tags():
    """Fetch the tag id -> name mapping from /api/Tags"""
    r = requests.get(f"{API_BASE}/Tags", headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    return {t["id"]: t["name"] for t in data}


def fetch_levels_page(page, page_size=PAGE_SIZE):
    """Fetch one page of level details"""
    params = {"page": page, "pageSize": page_size}
    r = requests.get(f"{API_BASE}/Levels/details", headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def build_row(entry, tags, tiers_data):
    """Turn one raw API entry into (csv_row, enriched_json_entry)"""
    lv = entry.get("level", {})

    # 1. Process Tags
    tag_ids = entry.get("tagIds", [])
    tag_names = ", ".join(tags.get(tid, f"?{tid}") for tid in tag_ids)

    # 2. Process Records
    records = entry.get("records", [])
    best_record = None
    if records:
        # highest endDistance = best progress
        best_record = max(records, key=lambda r: r.get("endDistance", 0))

    # 3. Process Creators
    creators_list = entry.get("creators", [])
    if creators_list and isinstance(creators_list[0], dict):
        creators_str = ", ".join(c.get("name", str(c)) for c in creators_list)
    else:
        creators_str = ", ".join(str(c) for c in creators_list)

    # 4. Get dynamic tier
    tier_name = get_tier(lv.get("rank", 0), tiers_data)

    # --- CSV FORMAT (Flattened and Cleaned) ---
    row = {
        "Rank": lv.get("rank"),
        "Level Name": lv.get("name"),
        "Tier": tier_name,
        "Creators": creators_str,
        "Rating": lv.get("rating"),
        "TPS/FPS": lv.get("fps"),
        "Length (sec)": lv.get("levelLength"),
        "Level ID": lv.get("levelId"),
        "Uploader": lv.get("uploader"),
        "Date Published": lv.get("datePublished"),
        "Cleared?": "No (Uncleared)" if lv.get("uncleared") else "Yes",
        "WR Holder": best_record.get("player") if best_record else None,
        "Best %": best_record.get("endDistance") if best_record else None,
        "Showcase Link": lv.get("showcaseLink"),
        "Tags": tag_names,
    }

    # --- JSON FORMAT (Preserves absolutely all raw API information plus enriched items) ---
    enriched_entry = dict(entry)  # Copies the full original API dictionary
    enriched_entry["enrichedTier"] = tier_name
    enriched_entry["enrichedTags"] = tag_names
    enriched_entry["parsedCreators"] = creators_str

    return row, enriched_entry


def fetch_top_n(top_n, tags, tiers_data):
    """Fetch ranks 1..top_n"""
    pages_needed = (top_n + PAGE_SIZE - 1) // PAGE_SIZE  # ceiling division

    csv_rows = []
    json_rows = []

    for page in range(1, pages_needed + 1):
        print(f"Fetching page {page}/{pages_needed}...")
        payload = fetch_levels_page(page)
        entries = payload.get("data", [])

        if not entries:
            print("  -> No more data returned by API, stopping early.")
            break

        for entry in entries:
            lv = entry.get("level", {})
            rank = lv.get("rank")
            if rank is not None and rank > top_n:
                continue

            row, enriched_entry = build_row(entry, tags, tiers_data)
            csv_rows.append(row)
            json_rows.append(enriched_entry)

        time.sleep(0.3)  # be polite to the API

    return csv_rows[:top_n], json_rows[:top_n]


def fetch_all_levels(tags, tiers_data):
    """Fetch every single available level on the list, paging until the API has no more data."""
    csv_rows = []
    json_rows = []

    page = 1
    while True:
        print(f"Fetching page {page}...")
        payload = fetch_levels_page(page)
        entries = payload.get("data", [])

        if not entries:
            print("  -> No more data returned by API, stopping.")
            break

        for entry in entries:
            row, enriched_entry = build_row(entry, tags, tiers_data)
            csv_rows.append(row)
            json_rows.append(enriched_entry)

        if len(entries) < PAGE_SIZE:
            # Last page was a partial page, so there's nothing left to fetch.
            break

        page += 1
        time.sleep(0.3)  # be polite to the API

    return csv_rows, json_rows


def fetch_single_rank(rank, tags, tiers_data):
    """Fetch only the level at this exact rank"""
    page = (rank + PAGE_SIZE - 1) // PAGE_SIZE  # which page this rank falls on
    print(f"Fetching page {page} (contains rank #{rank})...")
    payload = fetch_levels_page(page)
    entries = payload.get("data", [])

    for entry in entries:
        lv = entry.get("level", {})
        if lv.get("rank") == rank:
            row, enriched_entry = build_row(entry, tags, tiers_data)
            return [row], [enriched_entry]

    print(f"  -> Rank #{rank} not found on page {page}.")
    return [], []


def main():
    args = parse_args()

    top_n = args.top
    rank = args.rank
    grab_all = args.all

    if top_n is None and rank is None and not grab_all:
        top_n, rank, grab_all = get_mode_interactively()

    if top_n is not None and top_n <= 0:
        print("Number of levels must be positive. Exiting.")
        return
    if rank is not None and rank <= 0:
        print("Rank must be positive. Exiting.")
        return

    # Determine output filenames
    if args.output:
        base_name = args.output
    elif grab_all:
        base_name = "ILL_data"
    elif rank is not None:
        base_name = f"level_{rank}"
    else:
        base_name = f"top_{top_n}_levels"

    json_filename = f"{base_name}.json"
    csv_filename = f"{base_name}.csv"

    if grab_all:
        print("Target: EVERY available level")
    elif rank is not None:
        print(f"Target: only rank #{rank}")
    else:
        print(f"Target: top {top_n} levels")

    print("Fetching tier definitions...")
    tiers_data = fetch_tiers()
    print(f"  -> {len(tiers_data)} tiers loaded")

    print("Fetching tag definitions...")
    tags = fetch_tags()
    print(f"  -> {len(tags)} tags loaded")

    if grab_all:
        all_csv_rows, all_json_rows = fetch_all_levels(tags, tiers_data)
    elif rank is not None:
        all_csv_rows, all_json_rows = fetch_single_rank(rank, tags, tiers_data)
    else:
        all_csv_rows, all_json_rows = fetch_top_n(top_n, tags, tiers_data)

    if not all_csv_rows:
        print("\nNo data was fetched, nothing to save.")
        return

    # Sort by rank just in case
    all_csv_rows.sort(key=lambda r: r.get("Rank", 0) if r.get("Rank") is not None else float('inf'))
    all_json_rows.sort(key=lambda r: r.get("level", {}).get("rank", 0) if r.get("level", {}).get("rank") is not None else float('inf'))

    # Save JSON
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(all_json_rows, f, indent=2, ensure_ascii=False)

    # Save CSV
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_csv_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_csv_rows)

    print(f"\nDone! Saved {len(all_csv_rows)} level(s) to {json_filename} and {csv_filename}")


if __name__ == "__main__":
    main()
