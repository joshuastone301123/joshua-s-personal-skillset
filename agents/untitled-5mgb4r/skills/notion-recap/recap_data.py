#!/usr/bin/env python3
"""Gather a weekly or monthly recap data digest from the JPOS Notion workspace.

Pulls completed Tasks and Interactions for a date range, resolves contacts,
and loads the live Goals / Intentions / Your People reference pages. Emits a
single JSON object on stdout that the agent uses to write the narrative recap.

Usage:
  uv run --env-file .env --with requests recap_data.py --period weekly
  uv run --env-file .env --with requests recap_data.py --period monthly
  uv run --env-file .env --with requests recap_data.py --period weekly --ref 2026-06-24
"""
import os, sys, json, argparse, datetime as dt
import requests

ACCOUNT = os.environ.get("NOTION_ACCOUNT_ID", "ea6c6c56-bf38-4c59-a67e-e1748b4031d9")
BASE = os.environ["PROXY_BASE_URL"]
TOK = os.environ["PROXY_TOKEN"]
HOST = "api.notion.com"
H = {"Authorization": f"Bearer {TOK}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}

TASKS_DB = "284384b2-b53f-8108-b609-f26cca6a95f9"
INTER_DB = "284384b2-b53f-815a-8d07-c312141c9e0b"
GOALS_PAGE = "2d7384b2-b53f-801b-8710-da9d3b588eab"        # I WILL 2026
INTENTIONS_PAGE = "2d7384b2-b53f-80df-91b3-ed07baec08c6"   # INTENTION SETTING 2026
PEOPLE_PAGE = "359384b2-b53f-8096-8a4d-e8abba34a259"       # Your People

# Google Calendar (via proxy). Routines, gym, etc. live here — not in Notion.
GCAL_ACCOUNTS = {
    "personal": "65b8a847-7bdc-4b91-9af4-4b92a8aade8b",  # josh.pollak365@gmail.com
    "work":     "a523bd49-60c4-46a9-b733-8dc835923d06",  # josh@joshuapollak.com
}


def post(path, body):
    return requests.post(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H, json=body)


def get(path):
    return requests.get(f"{BASE}/{ACCOUNT}/{HOST}/{path}", headers=H)


def rt(arr):
    return "".join(x.get("plain_text", "") for x in arr)


def query_all(db_id, body):
    results, cursor = [], None
    while True:
        b = dict(body)
        if cursor:
            b["start_cursor"] = cursor
        r = post(f"v1/databases/{db_id}/query", b).json()
        results.extend(r.get("results", []))
        if r.get("has_more"):
            cursor = r.get("next_cursor")
        else:
            break
    return results


def page_lines(pid):
    """Flatten a page's child blocks to plain-text lines (one level deep)."""
    out = []
    r = get(f"v1/blocks/{pid}/children?page_size=100").json()
    for b in r.get("results", []):
        t = b["type"]
        c = b.get(t, {})
        if isinstance(c, dict) and "rich_text" in c:
            txt = rt(c["rich_text"]).strip()
            if txt:
                out.append(txt)
    return out


def compute_range(period, ref):
    """Return (start_date, end_date, label) as date objects + display label.

    weekly  -> the prior Mon..Sun week relative to ref
    monthly -> the prior calendar month relative to ref
    """
    if period == "weekly":
        this_monday = ref - dt.timedelta(days=ref.weekday())
        start = this_monday - dt.timedelta(days=7)
        end = this_monday - dt.timedelta(days=1)
        label = f"{start.strftime('%b %-d')}–{end.strftime('%b %-d, %Y')}"
    else:
        first_this = ref.replace(day=1)
        end = first_this - dt.timedelta(days=1)
        start = end.replace(day=1)
        label = start.strftime("%B %Y")
    return start, end, label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", choices=["weekly", "monthly"], required=True)
    ap.add_argument("--ref", help="reference date YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    ref = dt.date.fromisoformat(args.ref) if args.ref else dt.date.today()
    start, end, label = compute_range(args.period, ref)
    start_iso, end_iso = start.isoformat(), end.isoformat()

    # --- Completed tasks in range (by Date) ---
    tasks = query_all(TASKS_DB, {
        "filter": {"and": [
            {"property": "Status", "status": {"equals": "Complete"}},
            {"property": "Date", "date": {"on_or_after": start_iso}},
            {"property": "Date", "date": {"on_or_before": end_iso + "T23:59:59"}},
        ]},
        "sorts": [{"property": "Date", "direction": "ascending"}],
    })

    # --- Interactions in range (by Date) ---
    inters = query_all(INTER_DB, {
        "filter": {"and": [
            {"property": "Date", "date": {"on_or_after": start_iso}},
            {"property": "Date", "date": {"on_or_before": end_iso + "T23:59:59"}},
        ]},
        "sorts": [{"property": "Date", "direction": "ascending"}],
    })

    # --- Resolve contact names referenced by interactions/tasks ---
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

    def sel(p, key):
        v = p.get(key, {})
        return (v.get("select") or {}).get("name")

    def date_of(p):
        return (p.get("Date", {}).get("date") or {}).get("start")

    task_rows = []
    for res in tasks:
        p = res["properties"]
        contacts = [name_for(c["id"]) for c in p.get("Contact", {}).get("relation", [])]
        task_rows.append({
            "title": rt(p["Tasks"]["title"]),
            "date": date_of(p),
            "category": sel(p, "Category"),
            "urgency": sel(p, "Urgency"),
            "importance": sel(p, "Importance"),
            "contacts": [c for c in contacts if c],
        })

    inter_rows = []
    people_seen = {}
    for res in inters:
        p = res["properties"]
        contacts = [name_for(c["id"]) for c in p.get("Contact", {}).get("relation", [])]
        contacts = [c for c in contacts if c]
        for c in contacts:
            people_seen[c] = people_seen.get(c, 0) + 1
        inter_rows.append({
            "title": rt(p["Information"]["title"]),
            "date": date_of(p),
            "type": sel(p, "Type"),
            "contacts": contacts,
            "notes": rt(p["Interaction Notes"]["rich_text"]),
        })

    # --- Google Calendar events in range (routines, gym, meetings, etc.) ---
    cal_events = {}
    cal_min = f"{start_iso}T00:00:00-04:00"
    cal_max = f"{(end + dt.timedelta(days=1)).isoformat()}T00:00:00-04:00"
    for label_, aid in GCAL_ACCOUNTS.items():
        url = f"{BASE}/{aid}/www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {"timeMin": cal_min, "timeMax": cal_max,
                  "singleEvents": "true", "orderBy": "startTime", "maxResults": "500"}
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {TOK}"}, params=params, timeout=30)
            items = r.json().get("items", []) if r.ok else []
        except Exception:
            items = []
        cal_events[label_] = [
            {
                "summary": it.get("summary"),
                "start": (it.get("start", {}).get("dateTime") or it.get("start", {}).get("date")),
                "end": (it.get("end", {}).get("dateTime") or it.get("end", {}).get("date")),
                "location": it.get("location"),
            }
            for it in items if it.get("status") != "cancelled"
        ]

    # --- Live reference pages ---
    goals = page_lines(GOALS_PAGE)
    intentions = page_lines(INTENTIONS_PAGE)
    people = page_lines(PEOPLE_PAGE)

    # Which "Your People" did they spend time with (by interaction contact match)?
    people_lower = {pp.lower(): pp for pp in people}
    your_people_seen = {}
    for nm, cnt in people_seen.items():
        if nm.lower() in people_lower:
            your_people_seen[nm] = cnt

    # Category tallies for tasks
    cat_counts = {}
    for t in task_rows:
        cat_counts[t["category"] or "Uncategorized"] = cat_counts.get(t["category"] or "Uncategorized", 0) + 1
    type_counts = {}
    for i in inter_rows:
        type_counts[i["type"] or "Untyped"] = type_counts.get(i["type"] or "Untyped", 0) + 1

    out = {
        "period": args.period,
        "label": label,
        "start": start_iso,
        "end": end_iso,
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "totals": {
            "tasks_completed": len(task_rows),
            "interactions": len(inter_rows),
            "task_categories": cat_counts,
            "interaction_types": type_counts,
        },
        "tasks_completed": task_rows,
        "interactions": inter_rows,
        "your_people_seen": your_people_seen,
        "all_people_in_interactions": people_seen,
        "calendar_events": cal_events,
        "reference": {
            "goals": goals,
            "intentions": intentions,
            "your_people": people,
        },
    }
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
