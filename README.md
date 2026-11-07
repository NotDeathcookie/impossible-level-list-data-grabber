# ILL Data Grabber

A Python command-line tool for retrieving level data from the
**Impossible Levels List (ILL)** API and exporting it to CSV and JSON.

The script supports three retrieval modes:

-   **Top N:** fetch levels ranked from #1 through the requested rank.
-   **Specific rank:** fetch only the level at one exact rank.
-   **All:** fetch every level currently returned by the API.

It also retrieves tier and tag definitions from the API, converts those
IDs and rank brackets into readable values, and extracts creator and
record information.

## Features

-   Fetch the top N levels (for example, the top 100 or top 2,000).
-   Fetch one exact rank without downloading all higher-ranked levels.
-   Fetch every available level returned by the API.
-   Resolve tier names dynamically using the API's tier definitions.
-   Convert tag IDs into readable tag names using the API's tag
    definitions.
-   Extract creator names and the best record returned for each level.
-   Export a flattened CSV and an enriched JSON file.
-   Choose a custom base filename for the output files.

## Requirements

-   Python 3.7 or newer
-   The `requests` package

## Installation

1.  Download `ILL_data_grabber.py` and place it in a folder of your
    choice.

2.  Open a terminal or command prompt in that folder.

3.  Install the dependency:

    ``` bash
    python -m pip install requests
    ```

## Usage

### Interactive mode

Run the script without arguments:

``` bash
python ILL_data_grabber.py
```

The script presents a menu:

``` text
What would you like to grab?
  1) Top N levels (e.g. the top 100 hardest levels)
  2) One specific level by rank (e.g. only the #53 hardest level)
  3) EVERY single available level on the list
Enter 1, 2, or 3 [default: 1]:
```

For Top N mode, the default amount is 2,000 if you leave the amount
blank.

### Command-line mode

#### Fetch the top N levels

``` bash
python ILL_data_grabber.py --top 100
```

Fetches ranks #1 through #100 and creates:

-   `top_100_levels.csv`
-   `top_100_levels.json`

Short form:

``` bash
python ILL_data_grabber.py -t 100
```

#### Fetch one exact rank

``` bash
python ILL_data_grabber.py --rank 53
```

Fetches only rank #53. It does **not** fetch every level from #1 through
#53.

Creates:

-   `level_53.csv`
-   `level_53.json`

Short form:

``` bash
python ILL_data_grabber.py -r 53
```

#### Fetch all available levels

``` bash
python ILL_data_grabber.py --all
```

Fetches pages until the API returns no data or a partial page, then
creates:

-   `ILL_data.csv`
-   `ILL_data.json`

Short form:

``` bash
python ILL_data_grabber.py -a
```

"All" means all levels the API makes available through the paginated
endpoint at the time of the run. It does not guarantee that the API
contains every level ever submitted to the ILL.

#### Choose a custom output filename

Use `--output` (or `-o`) to set the shared filename base. Do not include
`.csv` or `.json`; the script adds those extensions.

``` bash
python ILL_data_grabber.py --top 250 -o my_custom_name
python ILL_data_grabber.py --rank 923 -o hardest_level_ever
python ILL_data_grabber.py --all -o complete_ill_export
```

For example, the first command creates `my_custom_name.csv` and
`my_custom_name.json`.

## Command-line options

  -----------------------------------------------------------------------
  Option                  Short form              Description
  ----------------------- ----------------------- -----------------------
  `--top N`               `-t N`                  Fetch ranks #1 through
                                                  #N.

  `--rank N`              `-r N`                  Fetch only the level at
                                                  the exact rank N.

  `--all`                 `-a`                    Fetch all levels
                                                  available through the
                                                  API's paginated
                                                  endpoint.

  `--output NAME`         `-o NAME`               Set the base name for
                                                  both output files,
                                                  without an extension.
  -----------------------------------------------------------------------

Choose only one retrieval mode: `--top`, `--rank`, or `--all`. These
options are mutually exclusive.

Ranks and Top N values must be positive integers.

## Output

Each run creates two files in the current working directory:

-   A **CSV** file containing flattened, spreadsheet-friendly fields.
-   A **JSON** file retaining the API entry data and adding enriched
    fields.

### CSV columns

  -----------------------------------------------------------------------
  Column                              Description
  ----------------------------------- -----------------------------------
  `Rank`                              The level's rank on the list.

  `Level Name`                        The level name.

  `Tier`                              Tier name determined from the API's
                                      tier brackets and the level's rank.

  `Creators`                          Creator names joined into one
                                      string.

  `Rating`                            Rating value supplied by the API.

  `TPS/FPS`                           FPS value supplied by the API.

  `Length (sec)`                      Level length supplied by the API.

  `Level ID`                          Geometry Dash level ID.

  `Uploader`                          Uploader name supplied by the API.

  `Date Published`                    Publication date supplied by the
                                      API.

  `Cleared?`                          `No (Uncleared)` when the API's
                                      `uncleared` value is true;
                                      otherwise `Yes`.

  `WR Holder`                         Player associated with the record
                                      having the greatest `endDistance`,
                                      if a record is available.

  `Best %`                            That record's `endDistance` value.

  `Showcase Link`                     Showcase link supplied by the API.

  `Tags`                              Resolved tag names joined by
                                      commas.
  -----------------------------------------------------------------------

Some values may be blank if the API does not provide the corresponding
data.

### JSON fields

The JSON output preserves each original API entry and adds these fields
at the entry's top level:

-   `enrichedTier` --- the tier name resolved from the level's rank.
-   `enrichedTags` --- resolved tag names joined into a comma-separated
    string.
-   `parsedCreators` --- creator names flattened into a comma-separated
    string.

The original API data, including nested level and record information, is
retained.

## How it works

1.  Retrieves tier definitions from `/api/Tiers`.
2.  Retrieves tag definitions from `/api/Tags`.
3.  Requests level details from `/api/Levels/details` in pages of 100.
4.  Converts each entry into a CSV row and an enriched JSON entry.
5.  Sorts the collected results by rank and writes both output files.

For record data, the script selects the record with the highest
`endDistance` value. The CSV's `WR Holder` and `Best %` columns are
taken from that record.

The script waits 0.3 seconds between page requests in the Top N and All
modes.

## API

Data is retrieved from:

``` text
https://api.impossiblelevels.com/api
```

The script uses the ILL API's tier, tag, and paginated level-details
endpoints. API availability and the amount of data returned are outside
the script's control.

## Troubleshooting

-   **`ModuleNotFoundError: No module named 'requests'`** --- install
    the dependency with `python -m pip install requests`.
-   **No data was fetched** --- check your internet connection and
    whether the ILL API is reachable.
-   **A requested rank is not found** --- the API did not return that
    rank on the page requested by the script.

## License

MIT
