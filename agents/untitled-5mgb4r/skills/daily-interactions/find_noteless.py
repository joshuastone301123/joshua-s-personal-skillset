#!/usr/bin/env python3
"""Find Interactions that already happened but have NO notes yet.

Covers today plus the trailing `--days` window (default 7) for stragglers.
Emits JSON the agent uses to text the user the end-of-day prompt.

Usage:
  uv run --env-file /workspace/.env --with requests find_noteless.py
  uv run --env-file /workspace/.env --with requests find_noteless.py --ref 2026-06-24 --days 7
"""
import os, sys, json, argparse, datetime as dt
import requests

ACCOUNT = os.environ.get("NOTION_ACCOUNT_ID", "ea6c6c56-bf38-4c59-a67e-e1748b4031d9")
BASE = os.environ["PROXY_BASE_URL"]
TOK = os.environ["PROXY_TOKEN"]
HOST = "api.notion.com"
H = {"Authorization": f"Bearer {TOK}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
INTER_DB = "284384b2-b53f-815a-8d07-c312141c9e0b"


def post(path, body):
    return requests.post(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H, json=body)


def get(path):
    return requests.get(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H)


def rt(arr):
    return "".join(x.get("plain_text", "") for x in arr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", help="reference date YYYY-MM-DD (default today)")
    ap.add_argument("--days", type=int, default=7, help="trailing window for stragglers")
    args = ap.parse_args()

    ref = dt.date.fromisoformat(args.ref) if args.ref else dt.date.today()
    window_start = (ref - dt.timedelta(days=args.days)).isoformat()
    end = ref.isoformat() + "T23:59:59"

    # NOTE: "has notes?" is determined by **page body content**, NOT the
    # Interaction Notes rich_text property. The user writes their notes in
    # the page body (child blocks). So we query the date window unfiltered
    # and then check each page's children for non-empty text content.
    res = post(f"v1/databases/{INTER_DB}/query", {
        "filter": {"and": [
            {"property": "Date", "date": {"on_or_after": window_start}},
            {"property": "Date", "date": {"on_or_before": end}},
        ]},
        "sorts": [{"property": "Date", "direction": "ascending"}],
        "page_size": 100,
    }).json()

    contact_cache = {}

    def name_for(cid):
        if cid in contact_cache:
            return contact_cache[cid]
        cp = get(f"v1/pages/{cid}").json()
        nm = ""
        for k, v in cp.get("properties", {}).items():
            if v.get("type") == "title":
                nm = rt(v["title"])
        contact_cache[cid] = nm
        return nm

    def has_body_notes(page_id):
        """True if the page has any meaningful content in its body.

        Counts as content:
        - Any non-empty text block (rich_text with non-whitespace content)
        - AI meeting-notes blocks (`transcription` block type from Notion AI)
        - Any media / structural block (image, file, to_do, etc.)
        - Nested children (Notion AI sometimes nests the actual notes)
        """
        children = get(f"v1/blocks/{page_id}/children?page_size=50").json()
        for b in children.get("results", []):
            t = b.get("type")
            # Notion AI meeting notes
            if t in ("transcription", "ai_block"):
                return True
            # Media / structural blocks always count
            if t in ("image", "file", "to_do", "bookmark", "embed", "video",
                     "audio", "table", "column_list", "synced_block",
                     "child_page", "child_database", "callout", "quote",
                     "toggle", "code"):
                return True
            # Text blocks: count if they have non-whitespace content
            c = b.get(t, {}) if t else {}
            if isinstance(c, dict) and c.get("rich_text"):
                if rt(c["rich_text"]).strip():
                    return True
            # Anything with nested children counts (notes sometimes nested)
            if b.get("has_children"):
                return True
        return False

    today, stragglers = [], []
    for r in res.get("results", []):
        if has_body_notes(r["id"]):
            continue
        p = r["properties"]
        d = (p.get("Date", {}).get("date") or {}).get("start")
        day = (d or "")[:10]
        existing = [name_for(c["id"]) for c in p.get("Contact", {}).get("relation", [])]
        item = {
            "id": r["id"],
            "title": rt(p["Information"]["title"]),
            "date": d,
            "type": (p.get("Type", {}).get("select") or {}).get("name"),
            "existing_contacts": [c for c in existing if c],
        }
        (today if day == ref.isoformat() else stragglers).append(item)

    print(json.dumps({"ref": ref.isoformat(), "today": today, "stragglers": stragglers,
                      "total": len(today) + len(stragglers)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
