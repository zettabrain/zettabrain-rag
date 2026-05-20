#!/usr/bin/env python3
"""
ZettaBrain download analytics
Pulls S3 access logs + PyPI stats and prints a unified report.

Usage:
  python3 scripts/analytics.py            # last 30 days
  python3 scripts/analytics.py --days 7   # last 7 days
  python3 scripts/analytics.py --sync     # re-sync logs from S3 before reporting
"""

import argparse
import gzip
import ipaddress
import json
import os
import re
import subprocess
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

LOG_BUCKETS = {
    "installer": {
        "bucket": "zettabrain-access-logs-west",
        "prefix": "s3-zettabrain-app/",
        "region": "us-west-2",
        "local":  Path("/tmp/zb-logs/app"),
        "filter": "install.sh",
    },
    "website": {
        "bucket": "zettabrain-access-logs",
        "prefix": "s3-zettabrain-io/",
        "region": "us-east-1",
        "local":  Path("/tmp/zb-logs/io"),
        "filter": None,
    },
}

PYPI_API = "https://pypistats.org/api/packages/zettabrain-rag"

COUNTRY_NAMES = {
    "US": "United States", "SG": "Singapore", "HK": "Hong Kong",
    "FR": "France", "JP": "Japan", "CN": "China", "DE": "Germany",
    "NO": "Norway", "KR": "South Korea", "RU": "Russia",
    "GB": "United Kingdom", "FI": "Finland", "CA": "Canada",
    "NL": "Netherlands", "IE": "Ireland", "SE": "Sweden",
    "ES": "Spain", "DK": "Denmark", "AT": "Austria", "EE": "Estonia",
    "AU": "Australia", "IN": "India", "BR": "Brazil", "IT": "Italy",
    "CH": "Switzerland", "PL": "Poland", "CZ": "Czech Republic",
    "UA": "Ukraine", "TR": "Turkey", "MX": "Mexico", "IL": "Israel",
    "TW": "Taiwan", "TH": "Thailand", "ID": "Indonesia", "VN": "Vietnam",
    "ZA": "South Africa", "AR": "Argentina", "PT": "Portugal",
    "BE": "Belgium", "HU": "Hungary", "RO": "Romania",
}


# ── S3 log sync ───────────────────────────────────────────────────────────────

def sync_logs(source: dict) -> None:
    source["local"].mkdir(parents=True, exist_ok=True)
    cmd = [
        "aws", "s3", "sync",
        f"s3://{source['bucket']}/{source['prefix']}",
        str(source["local"]),
        "--region", source["region"],
        "--quiet",
    ]
    subprocess.run(cmd, check=False)


# ── S3 log parser ─────────────────────────────────────────────────────────────
# S3 access log format (space-delimited, fields may be quoted):
# bucket-owner bucket time remote-ip requester request-id operation key
# request-uri status error bytes-sent object-size total-time turnaround-time
# referrer user-agent version-id host-id sig-version cipher auth-type
# host-header tls-version access-point-arn acl-required

_S3_LOG_RE = re.compile(
    r'\S+ \S+ \[.*?\] (\S+) \S+ \S+ (\S+) (\S+) "(\S+) (\S+) \S+" (\d+)'
)


def parse_s3_logs(local_dir: Path, path_filter: str | None, since: datetime) -> list[dict]:
    records = []
    for f in sorted(local_dir.glob("*")):
        try:
            opener = gzip.open if f.suffix == ".gz" else open
            with opener(f, "rt", errors="replace") as fh:
                for line in fh:
                    m = _S3_LOG_RE.match(line)
                    if not m:
                        continue
                    ip, operation, key, method, path, status = m.groups()
                    if int(status) not in (200, 206):
                        continue
                    if method != "GET":
                        continue
                    if path_filter and path_filter not in path:
                        continue
                    # Parse timestamp from line: [24/May/2026:12:00:00 +0000]
                    ts_m = re.search(r'\[(\d+/\w+/\d+:\d+:\d+:\d+) \+0000\]', line)
                    if not ts_m:
                        continue
                    ts = datetime.strptime(ts_m.group(1), "%d/%b/%Y:%H:%M:%S").replace(tzinfo=timezone.utc)
                    if ts < since:
                        continue
                    records.append({"ip": ip, "path": path, "ts": ts, "key": key})
        except Exception:
            continue
    return records


# ── Geo-IP lookup (ip-api.com — free, no key needed, 45 req/min) ──────────────

_geo_cache: dict[str, str] = {}


def ip_to_country(ip: str) -> str:
    if ip in _geo_cache:
        return _geo_cache[ip]
    try:
        # Skip private/loopback
        if ipaddress.ip_address(ip).is_private:
            _geo_cache[ip] = "Private"
            return "Private"
    except ValueError:
        pass
    try:
        url = f"http://ip-api.com/json/{ip}?fields=countryCode"
        with urllib.request.urlopen(url, timeout=3) as r:
            data = json.loads(r.read())
            country = data.get("countryCode", "Unknown")
    except Exception:
        country = "Unknown"
    _geo_cache[ip] = country
    return country


# ── PyPI stats ────────────────────────────────────────────────────────────────

def fetch_pypi() -> dict:
    try:
        with urllib.request.urlopen(f"{PYPI_API}/recent", timeout=5) as r:
            recent = json.loads(r.read())["data"]
        with urllib.request.urlopen(f"{PYPI_API}/system", timeout=5) as r:
            by_os_raw = json.loads(r.read())["data"]
        by_os: dict[str, int] = {}
        for row in by_os_raw:
            cat = row["category"] or "Unknown"
            by_os[cat] = by_os.get(cat, 0) + row["downloads"]
        return {"recent": recent, "by_os": by_os}
    except Exception as e:
        return {"error": str(e)}


# ── Formatting helpers ────────────────────────────────────────────────────────

def bar(n: int, total: int, width: int = 30) -> str:
    filled = int(n / total * width) if total else 0
    return "█" * filled + "░" * (width - filled)


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--sync", action="store_true", help="Re-sync logs from S3")
    ap.add_argument("--geo", action="store_true", help="Resolve IPs to countries (slow, rate-limited)")
    args = ap.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    print(f"\nZettaBrain Analytics  —  last {args.days} days  ({since.date()} → today)")

    # ── PyPI ──────────────────────────────────────────────────────────────────
    section("PyPI  (pip install zettabrain-rag)")
    pypi = fetch_pypi()
    if "error" in pypi:
        print(f"  [error: {pypi['error']}]")
    else:
        r = pypi["recent"]
        print(f"  Last 24 h : {r['last_day']:>8,}")
        print(f"  Last 7 d  : {r['last_week']:>8,}")
        print(f"  Last 30 d : {r['last_month']:>8,}")
        print()
        total_os = sum(pypi["by_os"].values())
        for os_name, n in sorted(pypi["by_os"].items(), key=lambda x: -x[1]):
            label = os_name if os_name != "null" else "CI / bots"
            print(f"  {label:<12} {n:>7,}  {bar(n, total_os, 20)}")

    # ── S3 installer logs ─────────────────────────────────────────────────────
    section("install.sh downloads  (S3 access logs)")
    src = LOG_BUCKETS["installer"]
    if args.sync:
        print("  Syncing logs from S3…")
        sync_logs(src)

    if not src["local"].exists() or not any(src["local"].iterdir()):
        print("  No logs yet — run with --sync or wait for first downloads.")
    else:
        records = parse_s3_logs(src["local"], src["filter"], since)
        unique_ips = {r["ip"] for r in records}
        print(f"  Total GET 200 hits : {len(records):,}")
        print(f"  Unique IPs         : {len(unique_ips):,}")

        if args.geo and unique_ips:
            print(f"\n  Resolving {len(unique_ips)} IPs to countries (may take a moment)…")
            country_hits: Counter = Counter()
            for r in records:
                cc = ip_to_country(r["ip"])
                country_hits[cc] += 1
            top = country_hits.most_common(15)
            total_hits = sum(country_hits.values())
            print()
            for cc, n in top:
                name = COUNTRY_NAMES.get(cc, cc)
                print(f"  {name:<22} {n:>5,}  {bar(n, total_hits, 25)}")

        # Daily trend
        daily: dict[str, int] = defaultdict(int)
        for r in records:
            daily[r["ts"].strftime("%Y-%m-%d")] += 1
        if daily:
            print("\n  Daily trend:")
            peak = max(daily.values())
            for day in sorted(daily)[-14:]:
                print(f"    {day}  {daily[day]:>4}  {bar(daily[day], peak, 20)}")

    # ── S3 website logs ───────────────────────────────────────────────────────
    section("zettabrain.io  (hero GIF, sample data, docs)")
    src_io = LOG_BUCKETS["website"]
    if args.sync:
        sync_logs(src_io)

    if not src_io["local"].exists() or not any(src_io["local"].iterdir()):
        print("  No logs yet — run with --sync or wait for activity.")
    else:
        records_io = parse_s3_logs(src_io["local"], None, since)
        unique_ips_io = {r["ip"] for r in records_io}
        path_hits: Counter = Counter(r["path"] for r in records_io)
        print(f"  Total GET 200 hits : {len(records_io):,}")
        print(f"  Unique IPs         : {len(unique_ips_io):,}")
        if path_hits:
            print("\n  Top paths:")
            total_paths = sum(path_hits.values())
            for path, n in path_hits.most_common(10):
                print(f"    {n:>5,}  {path}")

    print()


if __name__ == "__main__":
    main()
