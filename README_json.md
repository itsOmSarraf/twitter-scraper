# Twitter Scraper with JSON Input

This Twitter/X scraper accepts a username and an optional search query via JSON input. It outputs scraped tweets to a JSON file.

## Requirements

- Python 3.6+
- Chrome browser installed

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/twitter-scraper.git
   cd twitter-scraper
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

You can use this scraper in three different ways:

### 1. Pass JSON directly at command line:

```bash
python twitter_json_scraper.py --json '{"username": "paraschopra", "search_query": "steal this idea"}'
```

### 2. Use a JSON configuration file:

Create a JSON file (e.g., `example_paraschopra.json`):

```json
{
	"username": "paraschopra",
	"search_query": "steal this idea",
	"max_scrolls": 100,
	"scroll_pause_time": 3.0
}
```

Then run:

```bash
python twitter_json_scraper.py --json-file example_paraschopra.json
```

This will scrape tweets from the URL: `https://x.com/search?q=from%3Aparaschopra%20steal%20this%20idea&src=typed_query`

### 3. Interactive mode:

Run the script without arguments and enter the JSON when prompted:

```bash
python twitter_json_scraper.py
```

When prompted, enter your JSON configuration.

## JSON Configuration Parameters

- `username` (required): The Twitter/X username to scrape (without @)
- `search_query` (optional): If provided, will search for tweets containing this query from the user
- `max_scrolls` (optional, default: 200): Number of times to scroll down the page
- `scroll_pause_time` (optional, default: 2.5): Time in seconds to pause between scrolls

## How It Works

When both username and search_query are provided, the script constructs a URL like:

```
https://x.com/search?q=from%3Ausername%20search_query&src=typed_query
```

This is equivalent to typing "from:username search_query" in Twitter's search box.

## Output

The script creates a JSON file in the current directory with a filename following this pattern:

- If no search query: `username_YYYYMMDD_HHMMSS.json`
- If search query provided: `username_search-query_YYYYMMDD_HHMMSS.json`

The JSON output contains an array of tweet objects, each with:

- `tweet_id`: The unique identifier of the tweet
- `timestamp`: The tweet's timestamp
- `text`: The tweet's content
- `replies`: Number of replies
- `retweets`: Number of retweets
- `likes`: Number of likes
- `url`: URL to the tweet

## Notes

- The scraper may require you to manually log in to Twitter in the browser window that opens.
- If you encounter a login wall, the script will pause for 45 seconds to allow you to log in.
- The script tries to avoid detection by using random scrolling and timing variations.
- Due to Twitter's dynamic nature, some tweet data may be missing or incomplete.
