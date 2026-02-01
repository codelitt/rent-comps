#!/usr/bin/env python3
"""
Collect rent comp snapshots for competitive analysis.

Usage:
    uv run python etl/collect_comps_snapshot.py --config agents/configs/dallas_tx.yaml
    uv run python etl/collect_comps_snapshot.py --config agents/configs/dallas_tx.yaml --manual
"""

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from rich.console import Console
from rich.table import Table

# Playwright is optional - only used if available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

console = Console()


@dataclass
class UnitType:
    """Represents a unit type/floor plan."""
    name: str
    beds: int
    baths: float
    sq_ft: int
    face_rent: float | None = None
    effective_rent: float | None = None
    units_available: int = 0


@dataclass
class Concession:
    """Represents a rental concession/special."""
    description: str
    type: str  # e.g., "weeks_free", "months_free", "flat_discount"
    value: float  # dollar value of concession
    months_free: float = 0.0
    lease_requirement_months: int = 12


@dataclass
class PropertyData:
    """Collected data for a single property."""
    name: str
    address: str
    distance_mi: float
    units: int
    year_built: int
    stories: int | None = None
    property_class: str = ""
    unit_types: list[UnitType] = field(default_factory=list)
    concessions: list[Concession] = field(default_factory=list)
    owner: str = ""
    management_company: str = ""
    data_source: str = ""
    collection_date: str = ""
    collection_status: str = "pending"  # pending, success, failed, manual_required
    error_message: str = ""


@dataclass
class CompSnapshot:
    """Full snapshot of comp data for a metro."""
    metro_slug: str
    metro_name: str
    subject: PropertyData
    comps: list[PropertyData]
    collection_date: str
    data_sources: list[str] = field(default_factory=list)


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate metro configuration."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    required_keys = ["metro", "subject", "comps"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Config missing required key: {key}")

    return config


def build_apartments_com_url(property_id: str) -> str:
    """Build apartments.com URL from property ID."""
    return f"https://www.apartments.com/{property_id}/"


def fetch_apartments_com(
    property_id: str,
    config: dict[str, Any]
) -> tuple[BeautifulSoup | None, str]:
    """
    Attempt to fetch property data from apartments.com using browser impersonation.

    Uses curl_cffi to impersonate browser TLS fingerprints, which bypasses
    most bot detection systems.

    Returns:
        Tuple of (parsed soup or None, error message if failed)
    """
    url = build_apartments_com_url(property_id)
    scraping_config = config.get("scraping", {})

    timeout = scraping_config.get("timeout_seconds", 30)
    max_retries = scraping_config.get("max_retries", 3)
    delay = scraping_config.get("request_delay_seconds", 2)

    # Browser impersonation options - curl_cffi can mimic TLS fingerprints
    # This is key to bypassing Cloudflare and similar bot detection
    impersonate_options = [
        "chrome120",  # Latest Chrome
        "chrome119",
        "safari17_0",
        "edge120",
    ]

    last_error = ""
    for browser in impersonate_options:
        for attempt in range(max_retries):
            try:
                time.sleep(delay)  # Be respectful

                # Use curl_cffi with browser impersonation
                response = curl_requests.get(
                    url,
                    impersonate=browser,
                    timeout=timeout,
                    allow_redirects=True,
                )

                if response.status_code == 403:
                    last_error = f"403 Forbidden with {browser}"
                    break  # Try next browser

                if response.status_code == 404:
                    return None, f"404 Not Found - property listing may have changed"

                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code}"
                    break

                console.print(f"  [green]Success with: {browser}[/]")
                return BeautifulSoup(response.text, "lxml"), ""

            except Exception as e:
                if attempt < max_retries - 1:
                    console.print(f"  [yellow]Error, retrying ({attempt + 1}/{max_retries})...[/]")
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    continue
                last_error = f"Error: {e}"
                break

    # Fallback to Playwright if available - can handle JavaScript challenges
    if PLAYWRIGHT_AVAILABLE:
        console.print("  [yellow]Trying Playwright (headless browser)...[/]")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                )
                page = context.new_page()

                # Navigate and wait for content to load
                page.goto(url, wait_until="networkidle", timeout=timeout * 1000)

                # Wait a bit for any JavaScript to execute
                page.wait_for_timeout(3000)

                # Get page content
                content = page.content()
                browser.close()

                if "Access Denied" in content or "blocked" in content.lower():
                    last_error = "Playwright: Access denied after JS execution"
                else:
                    console.print("  [green]Success with Playwright![/]")
                    return BeautifulSoup(content, "lxml"), ""
        except Exception as e:
            last_error = f"Playwright error: {e}"
    else:
        console.print("  [yellow]Playwright not available, trying httpx fallback...[/]")

    # Final fallback to httpx
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "lxml"), ""
            last_error = f"httpx fallback: HTTP {response.status_code}"
    except Exception as e:
        last_error = f"httpx fallback error: {e}"

    return None, last_error or "All methods failed"


def parse_apartments_com(soup: BeautifulSoup, property_info: dict) -> PropertyData:
    """
    Parse apartments.com page for property data.

    Note: This is a basic parser - apartments.com frequently changes their HTML structure.
    This may need updates when the site changes.
    """
    prop = PropertyData(
        name=property_info.get("name", ""),
        address=property_info.get("address", ""),
        distance_mi=property_info.get("distance_mi", 0),
        units=property_info.get("units", 0),
        year_built=property_info.get("year_built", 0),
        stories=property_info.get("stories"),
        property_class=property_info.get("class", ""),
        data_source="apartments.com",
        collection_date=datetime.now().strftime("%Y-%m-%d"),
        collection_status="success",
    )

    # Try to find pricing table
    # Note: Apartments.com uses dynamic JavaScript rendering, so static parsing
    # often fails. This is a simplified example.
    pricing_tables = soup.find_all("div", class_="pricingGridItem")

    for table in pricing_tables:
        try:
            # Extract unit type info (structure varies)
            name_elem = table.find("span", class_="modelName")
            beds_elem = table.find("span", class_="detailsTextWrapper")
            rent_elem = table.find("span", class_="rentLabel")
            sqft_elem = table.find("span", class_="sqftLabel")

            if rent_elem:
                rent_text = rent_elem.get_text(strip=True)
                # Parse rent from text like "$1,500" or "$1,500 - $1,800"
                rent_text = rent_text.replace("$", "").replace(",", "")
                if " - " in rent_text:
                    # Take average of range
                    low, high = rent_text.split(" - ")
                    face_rent = (float(low) + float(high)) / 2
                else:
                    try:
                        face_rent = float(rent_text)
                    except ValueError:
                        face_rent = None

                unit = UnitType(
                    name=name_elem.get_text(strip=True) if name_elem else "Unknown",
                    beds=0,  # Would need more parsing
                    baths=1.0,
                    sq_ft=int(sqft_elem.get_text(strip=True).replace(",", "").split()[0]) if sqft_elem else 0,
                    face_rent=face_rent,
                    effective_rent=face_rent,  # Will adjust if concessions found
                )
                prop.unit_types.append(unit)
        except (AttributeError, ValueError):
            continue

    # Try to find specials/concessions
    specials = soup.find_all("div", class_="specials")
    for special in specials:
        text = special.get_text(strip=True).lower()
        if "free" in text or "off" in text or "special" in text:
            prop.concessions.append(Concession(
                description=special.get_text(strip=True),
                type="unknown",
                value=0,
            ))

    return prop


def collect_property_data(
    property_info: dict[str, Any],
    config: dict[str, Any],
    manual_mode: bool = False
) -> PropertyData:
    """Collect data for a single property."""

    if manual_mode:
        return PropertyData(
            name=property_info.get("name", ""),
            address=property_info.get("address", ""),
            distance_mi=property_info.get("distance_mi", 0),
            units=property_info.get("units", 0),
            year_built=property_info.get("year_built", 0),
            stories=property_info.get("stories"),
            property_class=property_info.get("class", ""),
            collection_date=datetime.now().strftime("%Y-%m-%d"),
            collection_status="manual_required",
            error_message="Manual mode - use web search to collect data",
        )

    # Try apartments.com first
    property_id = property_info.get("apartments_com_id")
    if property_id:
        console.print(f"  Fetching from apartments.com: {property_id}")
        soup, error = fetch_apartments_com(property_id, config)

        if soup:
            return parse_apartments_com(soup, property_info)
        else:
            console.print(f"  [yellow]Failed: {error}[/]")
            return PropertyData(
                name=property_info.get("name", ""),
                address=property_info.get("address", ""),
                distance_mi=property_info.get("distance_mi", 0),
                units=property_info.get("units", 0),
                year_built=property_info.get("year_built", 0),
                stories=property_info.get("stories"),
                property_class=property_info.get("class", ""),
                collection_date=datetime.now().strftime("%Y-%m-%d"),
                collection_status="failed",
                error_message=error,
            )

    return PropertyData(
        name=property_info.get("name", ""),
        address=property_info.get("address", ""),
        distance_mi=property_info.get("distance_mi", 0),
        units=property_info.get("units", 0),
        year_built=property_info.get("year_built", 0),
        stories=property_info.get("stories"),
        property_class=property_info.get("class", ""),
        collection_date=datetime.now().strftime("%Y-%m-%d"),
        collection_status="failed",
        error_message="No apartments.com ID configured",
    )


def collect_all_comps(config: dict[str, Any], manual_mode: bool = False) -> CompSnapshot:
    """Collect data for all properties in config."""
    metro = config["metro"]
    subject_config = config["subject"]
    comps_config = config["comps"]

    console.print(f"\n[bold]Collecting comps for {metro['name']}[/]")
    console.print(f"Subject: {subject_config['name']}")
    console.print(f"Comp set: {len(comps_config)} properties\n")

    # Collect subject property data
    console.print("[bold]Collecting subject property data...[/]")
    subject = collect_property_data(subject_config, config, manual_mode)

    # Collect comp data
    comps = []
    for i, comp_config in enumerate(comps_config, 1):
        console.print(f"[bold]({i}/{len(comps_config)}) {comp_config['name']}[/]")
        comp_data = collect_property_data(comp_config, config, manual_mode)
        comps.append(comp_data)

    # Build snapshot
    data_sources = set()
    for prop in [subject] + comps:
        if prop.data_source:
            data_sources.add(prop.data_source)

    return CompSnapshot(
        metro_slug=metro["slug"],
        metro_name=metro["name"],
        subject=subject,
        comps=comps,
        collection_date=datetime.now().strftime("%Y-%m-%d"),
        data_sources=list(data_sources),
    )


def save_json_snapshot(snapshot: CompSnapshot, output_dir: Path) -> Path:
    """Save snapshot as JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{snapshot.collection_date}_{snapshot.metro_slug}_comps_snapshot.json"
    filepath = output_dir / filename

    # Convert dataclasses to dicts for JSON serialization
    def to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [to_dict(item) for item in obj]
        else:
            return obj

    with open(filepath, "w") as f:
        json.dump(to_dict(snapshot), f, indent=2)

    return filepath


def generate_status_report(snapshot: CompSnapshot) -> None:
    """Print collection status summary."""
    console.print("\n[bold]Collection Status Summary[/]")

    table = Table(show_header=True)
    table.add_column("Property")
    table.add_column("Status")
    table.add_column("Unit Types")
    table.add_column("Notes")

    all_props = [("Subject", snapshot.subject)] + [(f"Comp {i+1}", c) for i, c in enumerate(snapshot.comps)]

    success_count = 0
    failed_count = 0
    manual_count = 0

    for label, prop in all_props:
        status = prop.collection_status
        if status == "success":
            status_display = "[green]Success[/]"
            success_count += 1
        elif status == "failed":
            status_display = "[red]Failed[/]"
            failed_count += 1
        else:
            status_display = "[yellow]Manual Required[/]"
            manual_count += 1

        units_display = str(len(prop.unit_types)) if prop.unit_types else "-"
        notes = prop.error_message[:50] if prop.error_message else ""

        table.add_row(
            f"{prop.name[:30]}",
            status_display,
            units_display,
            notes,
        )

    console.print(table)

    console.print(f"\n[bold]Summary:[/]")
    console.print(f"  Success: {success_count}")
    console.print(f"  Failed: {failed_count}")
    console.print(f"  Manual Required: {manual_count}")

    if failed_count > 0 or manual_count > 0:
        console.print("\n[yellow]Note: Use --manual flag and web search for failed properties.[/]")


def update_tracking_csvs(snapshot: CompSnapshot, tracking_dir: Path) -> None:
    """Update tracking CSV files with new data."""
    tracking_dir.mkdir(parents=True, exist_ok=True)

    # Update rent_history.csv
    rent_history_path = tracking_dir / "rent_history.csv"
    rent_history_exists = rent_history_path.exists()

    with open(rent_history_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not rent_history_exists:
            writer.writerow([
                "date", "property", "address", "unit_type", "beds", "baths",
                "sq_ft", "face_rent", "effective_rent", "rent_psf",
                "units_available", "mom_change", "yoy_change", "notes"
            ])

        for prop in [snapshot.subject] + snapshot.comps:
            for unit in prop.unit_types:
                psf = unit.effective_rent / unit.sq_ft if unit.sq_ft and unit.effective_rent else None
                writer.writerow([
                    snapshot.collection_date,
                    prop.name,
                    prop.address,
                    unit.name,
                    unit.beds,
                    unit.baths,
                    unit.sq_ft,
                    unit.face_rent,
                    unit.effective_rent,
                    f"{psf:.2f}" if psf else "",
                    unit.units_available,
                    "",  # mom_change - would need prior data
                    "",  # yoy_change - would need prior data
                    "",
                ])

    # Update concession_history.csv
    concession_path = tracking_dir / "concession_history.csv"
    concession_exists = concession_path.exists()

    with open(concession_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not concession_exists:
            writer.writerow([
                "date", "property", "address", "unit_type", "face_rent",
                "concession_type", "concession_value", "free_months",
                "effective_rent", "lease_requirement", "notes"
            ])

        for prop in [snapshot.subject] + snapshot.comps:
            for concession in prop.concessions:
                writer.writerow([
                    snapshot.collection_date,
                    prop.name,
                    prop.address,
                    "",  # unit_type
                    "",  # face_rent
                    concession.type,
                    concession.value,
                    concession.months_free,
                    "",  # effective_rent
                    concession.lease_requirement_months,
                    concession.description,
                ])

    # Update property_database.csv
    prop_db_path = tracking_dir / "property_database.csv"
    prop_db_exists = prop_db_path.exists()

    # For property database, we want to update/upsert, but for simplicity just append
    with open(prop_db_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not prop_db_exists:
            writer.writerow([
                "property", "address", "distance_mi", "units", "year_built",
                "stories", "owner", "management_company", "ownership_type",
                "renovation_status", "renovation_year", "condition_rating",
                "cap_rate_est", "last_sale_date", "last_sale_price", "notes"
            ])

        for prop in [snapshot.subject] + snapshot.comps:
            writer.writerow([
                prop.name,
                prop.address,
                prop.distance_mi,
                prop.units,
                prop.year_built,
                prop.stories or "",
                prop.owner,
                prop.management_company,
                "",  # ownership_type
                "",  # renovation_status
                "",  # renovation_year
                "",  # condition_rating
                "",  # cap_rate_est
                "",  # last_sale_date
                "",  # last_sale_price
                f"Last collected: {snapshot.collection_date}",
            ])

    console.print(f"\n[green]Updated tracking files in {tracking_dir}[/]")


def main():
    parser = argparse.ArgumentParser(description="Collect rent comp snapshots")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to metro config YAML file",
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Skip automation, mark all for manual collection",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/public/processed/comps"),
        help="Output directory for JSON snapshots",
    )
    parser.add_argument(
        "--tracking-dir",
        type=Path,
        default=Path("comps/tracking"),
        help="Directory for tracking CSV files",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error loading config: {e}[/]")
        sys.exit(1)

    # Collect data
    snapshot = collect_all_comps(config, manual_mode=args.manual)

    # Save outputs
    json_path = save_json_snapshot(snapshot, args.output_dir)
    console.print(f"\n[green]Saved JSON snapshot: {json_path}[/]")

    # Update tracking CSVs
    update_tracking_csvs(snapshot, args.tracking_dir)

    # Print status
    generate_status_report(snapshot)

    # Exit with error if any collections failed
    failed = sum(1 for c in snapshot.comps if c.collection_status == "failed")
    if snapshot.subject.collection_status == "failed":
        failed += 1

    if failed > 0:
        console.print(f"\n[yellow]Warning: {failed} properties failed automated collection.[/]")
        console.print("[yellow]Use web search fallback to complete data collection.[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
