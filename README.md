# Rare Birds of New York

An auto-updating website that displays notable (rare) bird observations across New York State from the past 7 days.

**Live site:** [https://wongpeiting.github.io/ebird-ny-rare-birds/](https://wongpeiting.github.io/ebird-ny-rare-birds/)

## How It Works

1. A Python script fetches data from the [eBird API 2.0](https://documenter.getpostman.com/view/664302/S1ENwy59)
2. GitHub Actions runs the scraper daily at 6:00 AM UTC
3. The data is saved to `data/birds.json`
4. A static HTML page reads the JSON and displays the birds
5. GitHub Pages hosts the site for free

## Data Source

All bird observation data comes from [eBird](https://ebird.org), a citizen science project managed by the Cornell Lab of Ornithology. The "notable" observations endpoint returns species that are rare or unusual for the region.

## Project Structure

```
├── index.html                    # Main display page
├── data/
│   └── birds.json                # Auto-generated bird data
├── scripts/
│   └── scrape.py                 # eBird API scraper
├── .github/
│   └── workflows/
│       └── scrape.yml            # Daily automation
└── requirements.txt              # Python dependencies
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python scripts/scrape.py

# Open index.html in a browser
open index.html
```

## Manual Update

To trigger an update manually:
1. Go to the **Actions** tab in GitHub
2. Select **Scrape eBird Data**
3. Click **Run workflow**

## License

Data provided by eBird (https://ebird.org) and subject to their terms of use.
