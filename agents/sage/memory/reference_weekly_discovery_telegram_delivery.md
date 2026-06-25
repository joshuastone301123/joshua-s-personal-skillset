---
name: reference-weekly-discovery-telegram-delivery
description: "After posting each weekly NYC dance-music discovery briefing to Notion, push a short teaser to Josh's Telegram in this exact bulleted format with section dividers."
metadata: 
  node_type: memory
  type: reference
  originSessionId: e9307264-6290-490b-9818-b668834734e2
---

After every weekly NYC dance-music discovery briefing is posted to Notion, send a Telegram teaser using the **Dance Music Discovery** integration (`mcp__chat__send_chat_message`, integration `cae11162-b522-4f29-aa33-ce95d9397963`).

**Locked format** (one bullet per line, blank line between bullets, `━━━━━━━━━━` divider between sections):

```
🔍 *Weekly Discovery — Month DD, YYYY*

━━━━━━━━━━

🎤 *Artists*

• [Artist 1](spotify-url) (City)

• [Artist 2](spotify-url) (City)

• [Artist 3](spotify-url) (City)

• [Artist 4](spotify-url) (City)

• [Artist 5](spotify-url) (City)

━━━━━━━━━━

🎵 *Songs*

• Artist — [Track](spotify-url)

• Artist — [Track](spotify-url)

• Artist — [Track](spotify-url)

• Artist — [Track](spotify-url)

• Artist — [Track](spotify-url)

━━━━━━━━━━

🏷️ *Labels*

• *Label 1* (City) — Two sentences. Two sentences.

• *Label 2* (City) — Two sentences. Two sentences.

━━━━━━━━━━

🎪 *Party*

• *Party Name* — City, years. Two sentences. Two sentences.

━━━━━━━━━━

→ [Full briefing in Notion](notion-page-url)

_Reply any time with feedback on a pick — saved to memory immediately._
```

**Rules:**
- Markdown V1 style: `*bold*`, `_italic_`, `[text](url)`. Don't escape `_` inside URLs.
- One bullet per line, blank line between every bullet (forces Telegram to render each on its own line — some clients collapse single-newline bullets).
- Artists section: name + city only, no descriptions. Name hyperlinks to Spotify artist URL.
- Songs section: `Artist — [Track Title](spotify-url)`. No descriptions. Track title hyperlinks to a Spotify track URL (or album URL if a single).
- Labels: 2 bullets, each 2 sentences. Bold label name, city in parens.
- Party: 1 bullet, 2 sentences. Bold party name, city + years after em-dash.
- Final line is the Notion page link, followed by the feedback invite in italics.

**Why:** Phone-first delivery — Josh wants to skim on Telegram and tap into Notion for the full briefing only when something catches his eye. Inline Spotify links let him preview artists/tracks straight from the teaser. Section dividers + line-per-bullet was the format he locked after iterating with me on June 25.

**How to apply:** Run this push as the final step of every Monday briefing compile, immediately after the Notion page is created and linked into the Dance Knowledge Hub. Feedback Josh sends back through Telegram (or directly in the Notion 💬 Feedback block) gets saved to memory immediately per [[feedback-weekly-discovery-format]].
