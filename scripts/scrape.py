#!/usr/bin/env python3
"""
eBird Rare Bird Scraper for New York
Fetches notable/rare bird observations from the past 7 days.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# Configuration
API_KEY = os.environ.get("EBIRD_API_KEY", "hkt4hkqma58m")
REGION_CODE = "US-NY"  # New York State
DAYS_BACK = 7

# eBird API endpoint for notable observations
BASE_URL = "https://api.ebird.org/v2"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def clean_bird_name(name):
    """Clean bird name for Wikipedia search."""
    import re
    # Remove subspecies/group designations in parentheses
    name = re.sub(r'\s*\([^)]*\)\s*', ' ', name).strip()
    # Remove "x" hybrid designations
    if ' x ' in name:
        name = name.split(' x ')[0].strip()
    return name


def fetch_bird_image(bird_name):
    """Fetch bird image URL from Wikipedia."""
    headers = {
        "User-Agent": "RareBirdsNY/1.0 (https://github.com/wongpeiting/ebird-ny-rare-birds)"
    }

    try:
        # Clean the bird name first
        clean_name = clean_bird_name(bird_name)

        # Search for the bird on Wikipedia
        params = {
            "action": "query",
            "titles": clean_name,
            "prop": "pageimages",
            "format": "json",
            "pithumbsize": 400,
            "redirects": 1,
        }
        response = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=5)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]

        # Try with " (bird)" suffix if not found
        params["titles"] = f"{clean_name} (bird)"
        response = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=5)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]

    except Exception:
        pass

    return None


def fetch_notable_observations():
    """Fetch recent notable (rare) bird observations in New York."""
    url = f"{BASE_URL}/data/obs/{REGION_CODE}/recent/notable"

    headers = {"X-eBirdApiToken": API_KEY}
    params = {
        "back": DAYS_BACK,
        "detail": "full",
        "hotspot": False,
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def process_observations(observations):
    """Process and deduplicate observations, grouping by species."""
    species_data = {}
    seen_obs = set()  # Track unique observations by (speciesCode, subId)

    for obs in observations:
        species_code = obs.get("speciesCode", "unknown")
        sub_id = obs.get("subId", "")

        # Deduplicate by species + checklist ID
        obs_key = (species_code, sub_id)
        if obs_key in seen_obs:
            continue
        seen_obs.add(obs_key)

        if species_code not in species_data:
            species_data[species_code] = {
                "comName": obs.get("comName", "Unknown"),
                "sciName": obs.get("sciName", ""),
                "speciesCode": species_code,
                "observations": [],
            }

        species_data[species_code]["observations"].append({
            "locName": obs.get("locName", "Unknown location"),
            "obsDt": obs.get("obsDt", ""),
            "howMany": obs.get("howMany", 1),
            "lat": obs.get("lat"),
            "lng": obs.get("lng"),
            "subId": sub_id,
            "userDisplayName": obs.get("userDisplayName", "Anonymous"),
        })

    # Calculate observation counts and sort by rarity (fewest observations = rarest)
    for species in species_data.values():
        species["observations"] = sorted(
            species["observations"],
            key=lambda x: x["obsDt"],
            reverse=True
        )
        species["totalObservations"] = len(species["observations"])

    # Sort by rarity: fewer observations = rarer = higher rank
    result = sorted(species_data.values(), key=lambda x: (x["totalObservations"], x["comName"]))

    # Add rarity rank
    for i, species in enumerate(result):
        species["rarityRank"] = i + 1

    return result


def main():
    print(f"Fetching notable bird observations for {REGION_CODE}...")

    try:
        raw_observations = fetch_notable_observations()
        print(f"Retrieved {len(raw_observations)} raw observations")

        processed_data = process_observations(raw_observations)
        total_obs = sum(s["totalObservations"] for s in processed_data)
        print(f"Found {len(processed_data)} unique species with {total_obs} unique observations")

        # Fetch images for top 30 rarest birds
        print("Fetching bird images from Wikipedia...")
        for i, species in enumerate(processed_data[:30]):
            img_url = fetch_bird_image(species["comName"])
            species["imageUrl"] = img_url
            if img_url:
                print(f"  [{i+1}] {species['comName']}: found image")
            else:
                print(f"  [{i+1}] {species['comName']}: no image")
            time.sleep(0.1)  # Be nice to Wikipedia API

        output = {
            "lastUpdated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "region": "New York",
            "regionCode": REGION_CODE,
            "daysBack": DAYS_BACK,
            "totalSpecies": len(processed_data),
            "totalObservations": total_obs,
            "species": processed_data,
        }

        # Ensure data directory exists
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)

        output_path = data_dir / "birds.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        raise


if __name__ == "__main__":
    main()
