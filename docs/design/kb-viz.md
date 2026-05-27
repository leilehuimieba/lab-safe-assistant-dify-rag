# KB Visualization Design

## Layout
- Left sidebar (280px): global stats panel (total, called, coverage%, counters)
- Main area: full-width visualization canvas
- Top bar: breadcrumb nav (全景 > {category} > {subcategory})
- Bottom-right: legend + toggle controls

## Color Scheme (Dark Monitoring Dashboard)
- Background: `#0f172a` (slate-900)
- Card bg: `#1e293b` (slate-800)
- Primary accent: `#06b6d4` (cyan-500)
- Called (safe): `#10b981` (emerald-500)
- Uncalled (alert): `#ef4444` (red-500)
- Border glow: `rgba(6, 182, 212, 0.3)` cyan glow
- Text primary: `#f1f5f9` (slate-100)
- Text secondary: `#94a3b8` (slate-400)

## API Contract

### GET /api/kb/summary
```json
{
  "total_entries": 3009,
  "total_categories": 58,
  "called_entries": 0,
  "coverage_rate": 0.0,
  "categories": [
    {
      "name": "string",
      "count": 0,
      "called_count": 0,
      "coverage_rate": 0.0,
      "subcategories": [
        {"name": "string", "count": 0, "called_count": 0, "coverage_rate": 0.0}
      ]
    }
  ]
}
```

### GET /api/kb/entries?category=&subcategory=&offset=0&limit=50
```json
{
  "total": 3009,
  "offset": 0,
  "limit": 50,
  "entries": [
    {
      "id": "KB-1001",
      "title": "string",
      "category": "string",
      "subcategory": "string",
      "risk_level": "2",
      "called": false,
      "call_count": 0,
      "source_org": "string"
    }
  ]
}
```

## Three-Layer Drill-Down
1. **L1 Bubble Chart**: ECharts scatter, x=index, y=count, size=count, color=coverage_rate. Click bubble -> drill to L2.
2. **L2 Sunburst**: ECharts sunburst, inner=category, outer=subcategory, area=count, color=coverage_rate. Click segment -> drill to L3.
3. **L3 Virtual List**: react-window FixedSizeList, 80px/item. Click item -> detail drawer with full KB fields.

## Call Tracking
- Binary state: citation.kb_id recorded in chat response = "called"
- Persist to `.cache/kb_usage.json`
- Load on startup
