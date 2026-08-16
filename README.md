# ILL Data Grabber

A Python script for pulling level data from the **Impossible Levels List (ILL)** API. Grab the top N hardest levels, or just one specific rank, and export the results to CSV and JSON.

## Features

- 📊 Grab the **top N levels** (e.g. top 100, top 2000)
- 🎯 Grab **one specific level** by exact rank (e.g. only rank #53)
- 🏷️ Automatically decodes tag IDs and tier brackets into readable names
- 👤 Extracts creator names, world record holder, and best clear %
- 📁 Auto-named output files based on what you requested
- 💾 Saves both a clean, flattened **CSV** and a full raw **JSON** with all API data

## Requirements

- Python 3.7+

## Installation

1. Download the .py file to a new folder named "ILL_data" or something

2. Install the dependency:
   ```bash
   pip install requests
   ```

## Usage

### Interactive mode

Just run the script with no arguments and it'll walk you through it:

```bash
python ILL_data_grabber.py
```

You'll be asked:
```
What would you like to grab?
  1) Top N levels (e.g. the top 100 hardest levels)
  2) One specific level by rank (e.g. only the #53 hardest level)
Enter 1 or 2 [default: 1]:
```

### Command-line mode

**Grab the top N levels:**
```bash
python ILL_data_grabber.py --top 100
```
Saves `top_100_levels.csv` and `top_100_levels.json`.

**Grab only one specific level by rank:**
```bash
python ILL_data_grabber.py --rank 53
```
Saves `level_53.csv` and `level_53.json` — this pulls **only** rank #53, not everything above it.

**Override the output filename:**
```bash
python ILL_data_grabber.py --top 250 -o my_custom_name
python ILL_data_grabber.py --rank 923 -o hardest_level_ever
```

### All options

| Flag | Short | Description |
|---|---|---|
| `--top N` | `-t` | Fetch the top N levels (ranks 1 through N) |
| `--rank N` | `-r` | Fetch only the single level at rank N |
| `--output NAME` | `-o` | Custom base filename for output files (no extension) |

`--top` and `--rank` are mutually exclusive — pick one mode per run.

## Output

### CSV columns

| Column | Description |
|---|---|
| Rank | Level's position on the list |
| Level Name | Name of the level |
| Tier | Difficulty tier bracket |
| Creators | Level creator(s) |
| Rating | Difficulty rating |
| TPS/FPS | Ticks/frames per second |
| Length (sec) | Level length in seconds |
| Level ID | Geometry Dash level ID |
| Uploader | Uploader's name |
| Date Published | Publish date |
| Cleared? | Whether the level has been cleared |
| WR Holder | Player with the best record |
| Best % | Best clear percentage |
| Showcase Link | Link to a showcase video |
| Tags | Comma-separated level tags |

### JSON

Contains the full, unmodified data returned by the API for each level, plus three enriched fields:
- `enrichedTier` — decoded tier name
- `enrichedTags` — decoded tag names
- `parsedCreators` — flattened creator names

## Notes

- The script is polite to the API and waits 0.3 seconds between page requests.
- Data comes from `api.impossiblelevels.com`.

## License

MIT
