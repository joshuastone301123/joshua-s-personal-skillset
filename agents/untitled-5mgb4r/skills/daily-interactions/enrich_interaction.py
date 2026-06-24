#!/usr/bin/env python3
"""Resolve entities for an Interaction and (on apply) link them + write notes.

Two modes:
  --resolve : report which named entities already exist vs. are MISSING, per
              type. No writes. Use this to propose new records to the user.
  --apply   : create missing entities (only the types you pass), link ALL
              named entities to the interaction (merging with existing
              relations), and set the Interaction Notes. Prints the page URL.

Entity flags accept comma-separated names:
  --contacts "Erez Davids,Jess Park"   (Contacts DB, relation "Contact")
  --artists  "Oliver Heldens"          (Artists  DB, relation "Artist")
  --companies "Pacha NY"               (Companies DB, relation "Company")
  --venues   "House of Yes"            (Venues   DB, relation "Venue 1")
  --areas    "Brooklyn"                (Areas    DB, relation "Area")

Usage:
  # 1. propose
  uv run --env-file /workspace/.env --with requests enrich_interaction.py \
      --interaction <page_id> --resolve --contacts "Erez Davids,New Person" --venues "House of Yes"
  # 2. after user OK
  uv run --env-file /workspace/.env --with requests enrich_interaction.py \
      --interaction <page_id> --apply --create-missing \
      --contacts "Erez Davids,New Person" --venues "House of Yes" \
      --notes "Caught up about the Paris shoot; New Person runs lights."
"""
import os, sys, json, argparse
import requests

ACCOUNT = os.environ.get("NOTION_ACCOUNT_ID", "ea6c6c56-bf38-4c59-a67e-e1748b4031d9")
BASE = os.environ["PROXY_BASE_URL"]
TOK = os.environ["PROXY_TOKEN"]
HOST = "api.notion.com"
H = {"Authorization": f"Bearer {TOK}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}

# entity key -> (database_id, title_property, interaction_relation_property)
ENTITIES = {
    "contacts":  ("284384b2-b53f-8120-967d-ef2a691dd7e6", "Name",    "Contact"),
    "artists":   ("284384b2-b53f-810d-971a-fbd8a7d67f62", "Artist",  "Artist"),
    "companies": ("284384b2-b53f-814b-a60f-f55498c2dc34", "Company", "Company"),
    "venues":    ("284384b2-b53f-81c7-a254-f9c9780673cd", "Venue",   "Venue 1"),
    "areas":     ("284384b2-b53f-814e-a4e3-f6346ae1936c", "Area",    "Area"),
}


def post(path, body):
    return requests.post(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H, json=body)


def patch(path, body):
    return requests.patch(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H, json=body)


def get(path):
    return requests.get(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H)


def rt(arr):
    return "".join(x.get("plain_text", "") for x in arr)


def title_of(page):
    for k, v in page.get("properties", {}).items():
        if v.get("type") == "title":
            return rt(v["title"])
    return ""


def find_record(db_id, name):
    r = post(f"v1/databases/{db_id}/query", {
        "filter": {"property": TITLE_PROP_BY_DB[db_id], "title": {"contains": name.strip()}},
        "page_size": 5,
    }).json()
    results = r.get("results", [])
    for res in results:
        if title_of(res).lower() == name.strip().lower():
            return res["id"], title_of(res)
    if results:
        return results[0]["id"], title_of(results[0])
    return None, None


def create_record(db_id, title_prop, name):
    r = post("v1/pages", {
        "parent": {"type": "database_id", "database_id": db_id},
        "properties": {title_prop: {"title": [{"type": "text", "text": {"content": name.strip()}}]}},
    })
    r.raise_for_status()
    return r.json()["id"]


TITLE_PROP_BY_DB = {db: tp for (db, tp, _) in ENTITIES.values()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interaction", required=True)
    ap.add_argument("--resolve", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--create-missing", action="store_true")
    ap.add_argument("--notes", default="")
    for key in ENTITIES:
        ap.add_argument(f"--{key}", default="")
    args = ap.parse_args()

    requested = {key: [n.strip() for n in getattr(args, key).split(",") if n.strip()]
                 for key in ENTITIES}

    # Resolve each requested name against its DB.
    resolution = {}
    for key, names in requested.items():
        db_id, title_prop, rel_prop = ENTITIES[key]
        matched, missing = [], []
        for nm in names:
            rid, found = find_record(db_id, nm)
            if rid:
                matched.append({"input": nm, "id": rid, "name": found})
            else:
                missing.append(nm)
        resolution[key] = {"matched": matched, "missing": missing}

    if args.resolve and not args.apply:
        out = {key: {"matched": [m["name"] for m in v["matched"]], "missing": v["missing"]}
               for key, v in resolution.items() if requested[key]}
        print(json.dumps({"interaction": args.interaction, "resolution": out}, indent=2, ensure_ascii=False))
        return

    # --apply: create missing (if allowed), then link + set notes.
    created = {}
    for key, v in resolution.items():
        db_id, title_prop, rel_prop = ENTITIES[key]
        for nm in list(v["missing"]):
            if args.create_missing:
                rid = create_record(db_id, title_prop, nm)
                v["matched"].append({"input": nm, "id": rid, "name": nm})
                created.setdefault(key, []).append(nm)

    # Merge with existing relations on the interaction page.
    page = get(f"v1/pages/{args.interaction}").json()
    existing_props = page.get("properties", {})
    new_props = {}
    for key, v in resolution.items():
        if not requested[key]:
            continue
        _, _, rel_prop = ENTITIES[key]
        have = {x["id"] for x in (existing_props.get(rel_prop, {}).get("relation", []) or [])}
        for m in v["matched"]:
            have.add(m["id"])
        new_props[rel_prop] = {"relation": [{"id": i} for i in have]}

    r = patch(f"v1/pages/{args.interaction}", {"properties": new_props})
    if r.status_code != 200:
        print(json.dumps({"error": r.status_code, "body": r.text}))
        raise SystemExit(1)

    # Notes are written to the PAGE BODY (child blocks), not the
    # "Interaction Notes" property — that's where the user keeps notes.
    if args.notes:
        body = {"children": [
            {"object": "block", "type": "paragraph",
             "paragraph": {"rich_text": [{"type": "text",
                                          "text": {"content": args.notes[:1990]}}]}}
        ]}
        rb = requests.patch(f"{BASE}/{ACCOUNT}/{HOST}/v1/blocks/{args.interaction}/children",
                            headers=H, json=body)
        if rb.status_code != 200:
            print(json.dumps({"error": rb.status_code, "body": rb.text, "stage": "notes-append"}))
            raise SystemExit(1)

    print(json.dumps({"updated": True, "url": r.json().get("url"),
                      "created": created,
                      "linked": {k: [m["name"] for m in v["matched"]]
                                 for k, v in resolution.items() if requested[k]}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
