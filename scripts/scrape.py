#!/usr/bin/env python3
"""
eBird Rare Bird Scraper for New York
Fetches notable/rare bird observations from the past 7 days.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

# Configuration
API_KEY = os.environ.get("EBIRD_API_KEY", "hkt4hkqma58m")
REGION_CODE = "US-NY"  # New York State
DAYS_BACK = 7

# eBird API endpoint for notable observations
BASE_URL = "https://api.ebird.org/v2"


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

    # Sort species by name and observations by date (newest first)
    result = sorted(species_data.values(), key=lambda x: x["comName"])
    for species in result:
        species["observations"] = sorted(
            species["observations"],
            key=lambda x: x["obsDt"],
            reverse=True
        )
        species["totalObservations"] = len(species["observations"])

    return result


def main():
    print(f"Fetching notable bird observations for {REGION_CODE}...")

    try:
        raw_observations = fetch_notable_observations()
        print(f"Retrieved {len(raw_observations)} raw observations")

        processed_data = process_observations(raw_observations)
        total_obs = sum(s["totalObservations"] for s in processed_data)
        print(f"Found {len(processed_data)} unique species with {total_obs} unique observations")

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
