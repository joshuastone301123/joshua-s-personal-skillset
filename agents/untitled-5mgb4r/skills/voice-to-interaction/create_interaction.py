#!/usr/bin/env python3
"""Create (or preview) an entry in the Notion Interactions [JPOS] database.

Resolves person names against the Contacts [JPOS] database and links them via
the Contact relation. Use --dry-run to resolve contacts and preview the row
WITHOUT writing (for the confirm-before-save step); omit it to create the page.

Usage:
  uv run --env-file /workspace/.env --with requests create_interaction.py \
      --title "Coffee with Sophie" --type "Call / Meeting" \
      --date 2026-06-24 --contacts "Sophie Gurwitz,Ryan Sterne" \
      --notes "Talked about the layflat editor and Q3 bookings." --dry-run
"""
import os, sys, json, argparse, datetime as dt
import requests

ACCOUNT = os.environ.get("NOTION_ACCOUNT_ID", "ea6c6c56-bf38-4c59-a67e-e1748b4031d9")
BASE = os.environ["PROXY_BASE_URL"]
TOK = os.environ["PROXY_TOKEN"]
HOST = "api.notion.com"
H = {"Authorization": f"Bearer {TOK}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}

INTER_DB = "284384b2-b53f-815a-8d07-c312141c9e0b"
CONTACTS_DB = "284384b2-b53f-8120-967d-ef2a691dd7e6"
TYPES = ["Social Setting", "Call / Meeting", "Idea / Note", "Networking", "Shoot", "Event", "Date"]


def post(path, body):
    return requests.post(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H, json=body)


def rt(arr):
    return "".join(x.get("plain_text", "") for x in arr)


def find_contact(name):
    """Return (id, matched_name) for the best Contacts match, or (None, None)."""
    name = name.strip()
    if not name:
        return None, None
    r = post(f"v1/databases/{CONTACTS_DB}/query", {
        "filter": {"property": "Name", "title": {"contains": name}},
        "page_size": 5,
    }).json()
    results = r.get("results", [])
    # Prefer an exact (case-insensitive) match, else the first contains-hit.
    exact = None
    for res in results:
        nm = ""
        for k, v in res.get("properties", {}).items():
            if v.get("type") == "title":
                nm = rt(v["title"])
        if nm.lower() == name.lower():
            exact = (res["id"], nm)
            break
    if exact:
        return exact
    if results:
        first = results[0]
        nm = ""
        for k, v in first.get("properties", {}).items():
            if v.get("type") == "title":
                nm = rt(v["title"])
        return first["id"], nm
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--type", required=True)
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--contacts", default="", help="comma-separated names")
    ap.add_argument("--notes", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.type not in TYPES:
        print(json.dumps({"error": f"invalid type {args.type!r}. allowed: {TYPES}"}))
        raise SystemExit(1)
    date = args.date or dt.date.today().isoformat()

    matched, unmatched = [], []
    for nm in [c for c in args.contacts.split(",") if c.strip()]:
        cid, found = find_contact(nm)
        if cid:
            matched.append({"input": nm.strip(), "id": cid, "name": found})
        else:
            unmatched.append(nm.strip())

    preview = {
        "title": args.title, "type": args.type, "date": date,
        "notes": args.notes,
        "matched_contacts": [m["name"] for m in matched],
        "unmatched_contacts": unmatched,
    }

    if args.dry_run:
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return

    props = {
        "Information": {"title": [{"type": "text", "text": {"content": args.title}}]},
        "Type": {"select": {"name": args.type}},
        "Date": {"date": {"start": date}},
    }
    if matched:
        props["Contact"] = {"relation": [{"id": m["id"]} for m in matched]}
    if args.notes:
        note = args.notes
        if unmatched:
            note += f"\n\n[Unmatched names — not linked: {', '.join(unmatched)}]"
        props["Interaction Notes"] = {"rich_text": [{"type": "text", "text": {"content": note[:1900]}}]}

    r = post("v1/pages", {"parent": {"type": "database_id", "database_id": INTER_DB}, "properties": props})
    if r.status_code != 200:
        print(json.dumps({"error": r.status_code, "body": r.text}))
        raise SystemExit(1)
    page = r.json()
    print(json.dumps({"created": True, "url": page.get("url"),
                      "matched_contacts": [m["name"] for m in matched],
                      "unmatched_contacts": unmatched}, ensure_ascii=False))


if __name__ == "__main__":
    main()
