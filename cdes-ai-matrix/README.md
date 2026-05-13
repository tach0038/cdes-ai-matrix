# CDes AI Tools Matrix

A living database of AI tools relevant to College of Design disciplines at the University of Minnesota.

## Repository structure

```
cdes-ai-matrix/
├── .github/
│   └── workflows/
│       └── daily_refresh.yml   # Scheduled GitHub Actions job
├── scripts/
│   └── refresh_agent.py        # Claude-powered refresh agent
├── data/
│   ├── known_tools.json        # Current approved tool list (source of truth)
│   ├── pending_submissions.json # Agent suggestions + community submissions queue
│   └── run_log.json            # Log of daily agent runs
└── README.md
```

## How the daily refresh works

1. GitHub Actions triggers `refresh_agent.py` every morning at 6 AM UTC
2. The agent calls the Claude API with web search enabled
3. Claude searches for new or updated AI design tools from the past 30 days
4. Results land in `pending_submissions.json` with status `"pending"`
5. A human reviewer promotes approved items to `known_tools.json` and the master spreadsheet

## Setup instructions

See the GitHub walkthrough in the project documentation.

## Disciplines covered

Architecture · Interior Design · Landscape Architecture · Product Design ·
Graphic Design · Apparel Design · Retail Merchandising · Human Factors & Ergonomics · UX Design

## Maintainer

Milo Tacheny — CDes Strategic Initiatives, University of Minnesota
