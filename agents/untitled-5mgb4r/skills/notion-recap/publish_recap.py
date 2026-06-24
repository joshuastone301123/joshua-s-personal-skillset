#!/usr/bin/env python3
"""Publish a recap as a page in the Notion 'Recaps' database.

Converts a lightweight Markdown body into Notion blocks and creates the page
with Type / Period Start / Period End / count properties set.

Usage:
  uv run --env-file .env --with requests publish_recap.py \
      --title "Weekly Recap — Jun 15–21, 2026" \
      --type Weekly --start 2026-06-15 --end 2026-06-21 \
      --tasks 12 --interactions 5 \
      --body /tmp/recap.md

Supported Markdown: '# / ## / ###' headings, '- ' bullets, '1. ' numbered,
'> ' quotes, '---' dividers, '[ ] / [x]' todos, blank-line-separated paragraphs.
Inline **bold** and *italic* are rendered.
"""
import os, re, argparse, requests

ACCOUNT = os.environ.get("NOTION_ACCOUNT_ID", "ea6c6c56-bf38-4c59-a67e-e1748b4031d9")
BASE = os.environ["PROXY_BASE_URL"]
TOK = os.environ["PROXY_TOKEN"]
HOST = "api.notion.com"
H = {"Authorization": f"Bearer {TOK}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
RECAPS_DB = os.environ.get("RECAPS_DB_ID", "389384b2-b53f-8114-bb43-e72b1fc1cd1f")


def inline(text):
    """Parse **bold** and *italic* into Notion rich_text spans."""
    spans = []
    pos = 0
    pattern = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*")
    for m in pattern.finditer(text):
        if m.start() > pos:
            spans.append({"type": "text", "text": {"content": text[pos:m.start()]}})
        ann = {}
        if m.group(1) is not None:
            content = m.group(1); ann = {"bold": True}
        else:
            content = m.group(2); ann = {"italic": True}
        spans.append({"type": "text", "text": {"content": content}, "annotations": ann})
        pos = m.end()
    if pos < len(text):
        spans.append({"type": "text", "text": {"content": text[pos:]}})
    return spans or [{"type": "text", "text": {"content": ""}}]


def md_to_blocks(md):
    blocks = []
    lines = md.split("\n")
    para = []

    def flush_para():
        if para:
            blocks.append({"object": "block", "type": "paragraph",
                           "paragraph": {"rich_text": inline(" ".join(para).strip())}})
            para.clear()

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush_para(); continue
        if s == "---":
            flush_para(); blocks.append({"object": "block", "type": "divider", "divider": {}}); continue
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            flush_para()
            lvl = len(m.group(1)); key = f"heading_{lvl}"
            blocks.append({"object": "block", "type": key, key: {"rich_text": inline(m.group(2))}})
            continue
        m = re.match(r"^[-*]\s+\[([ xX])\]\s+(.*)$", s)
        if m:
            flush_para()
            blocks.append({"object": "block", "type": "to_do",
                           "to_do": {"rich_text": inline(m.group(2)), "checked": m.group(1).lower() == "x"}})
            continue
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            flush_para()
            blocks.append({"object": "block", "type": "bulleted_list_item",
                           "bulleted_list_item": {"rich_text": inline(m.group(1))}})
            continue
        m = re.match(r"^\d+\.\s+(.*)$", s)
        if m:
            flush_para()
            blocks.append({"object": "block", "type": "numbered_list_item",
                           "numbered_list_item": {"rich_text": inline(m.group(1))}})
            continue
        m = re.match(r"^>\s+(.*)$", s)
        if m:
            flush_para()
            blocks.append({"object": "block", "type": "quote",
                           "quote": {"rich_text": inline(m.group(1))}})
            continue
        para.append(s)
    flush_para()
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--type", choices=["Weekly", "Monthly"], required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--tasks", type=int, default=0)
    ap.add_argument("--interactions", type=int, default=0)
    ap.add_argument("--body", required=True, help="path to markdown file")
    args = ap.parse_args()

    with open(args.body) as f:
        md = f.read()
    blocks = md_to_blocks(md)

    props = {
        "Name": {"title": [{"type": "text", "text": {"content": args.title}}]},
        "Type": {"select": {"name": args.type}},
        "Period Start": {"date": {"start": args.start}},
        "Period End": {"date": {"start": args.end}},
        "Tasks Completed": {"number": args.tasks},
        "Interactions": {"number": args.interactions},
    }

    # Notion caps children at 100 per create call; chunk if needed.
    first, rest = blocks[:100], blocks[100:]
    body = {"parent": {"type": "database_id", "database_id": RECAPS_DB},
            "icon": {"type": "emoji", "emoji": "🗓️" if args.type == "Weekly" else "📅"},
            "properties": props, "children": first}
    r = requests.post(f"{BASE}/{ACCOUNT}/{HOST}/v1/pages", headers=H, json=body)
    if r.status_code != 200:
        print("ERROR", r.status_code, r.text); raise SystemExit(1)
    page = r.json(); pid = page["id"]
    for i in range(0, len(rest), 100):
        requests.patch(f"{BASE}/{ACCOUNT}/{HOST}/v1/blocks/{pid}/children",
                       headers=H, json={"children": rest[i:i + 100]})
    print("CREATED", page.get("url"))


if __name__ == "__main__":
    main()
