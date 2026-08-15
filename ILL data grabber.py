"""
Fetch the top 2000 levels from the Impossible Levels List (ILL) API,
decode tags and tiers dynamically, extract creators, and save everything to CSV + JSON.

Requirements:
    pip install requests

Usage:
    python fetch_ill_top2000.py
"""

import requests
import json
import csv
import time

API_BASE = "https://api.impossiblelevels.com/api"
PAGE_SIZE = 100
TOP_N = 2000
PAGES_NEEDED = TOP_N // PAGE_SIZE  # 20 pages to cover ranks 1-2000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ILL-data-fetch/2.0)",
    "Accept": "application/json",
}

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

def fetch_levels_page(page):
    """Fetch one page of level details"""
    params = {"page": page, "pageSize": PAGE_SIZE}
    r = requests.get(f"{API_BASE}/Levels/details", headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def main():
    print("Fetching tier definitions...")
    tiers_data = fetch_tiers()
    print(f"  -> {len(tiers_data)} tiers loaded")

    print("Fetching tag definitions...")
    tags = fetch_tags()
    print(f"  -> {len(tags)} tags loaded")

    all_csv_rows = []
    all_json_rows = []

    for page in range(1, PAGES_NEEDED + 1):
        print(f"Fetching page {page}/{PAGES_NEEDED}...")
        payload = fetch_levels_page(page)
        entries = payload.get("data", [])

        for entry in entries:
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
            all_csv_rows.append(row)

            # --- JSON FORMAT (Preserves absolutely all raw API information plus enriched items) ---
            enriched_entry = dict(entry)  # Copies the full original API dictionary
            enriched_entry["enrichedTier"] = tier_name
            enriched_entry["enrichedTags"] = tag_names
            enriched_entry["parsedCreators"] = creators_str
            all_json_rows.append(enriched_entry)

        time.sleep(0.3)  # be polite to the API

    # Sort by rank just in case
    all_csv_rows.sort(key=lambda r: r.get("Rank", 0) if r.get("Rank") is not None else float('inf'))
    all_json_rows.sort(key=lambda r: r.get("level", {}).get("rank", 0) if r.get("level", {}).get("rank") is not None else float('inf'))

    # Save JSON
    with open("ill_top2000.json", "w", encoding="utf-8") as f:
        json.dump(all_json_rows, f, indent=2, ensure_ascii=False)

    # Save CSV
    with open("ill_top2000.csv", "w", newline="", encoding="utf-8") as f:
        if all_csv_rows:
            writer = csv.DictWriter(f, fieldnames=all_csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_csv_rows)

    print(f"\nDone! Saved {len(all_csv_rows)} levels to ill_top2000.json and ill_top2000.csv")

if __name__ == "__main__":
    main()