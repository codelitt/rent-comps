# /pull-comps - Institutional Comp Collection & Analysis

Collect comprehensive competitive property data with face rents, effective rents, concessions, and market positioning for investment underwriting.

## Arguments

- `<metro>` (optional) - Metro config name (e.g., `dallas_tx`, `austin_tx`). If not provided, will prompt for selection.
- `--refresh` (optional) - Force refresh even if recent data exists
- `--manual` (optional) - Skip automation, use web search only

## Instructions

Execute comprehensive comp data collection for institutional-quality analysis.

### Steps

1. If no metro argument provided, list available configs:
   ```bash
   ls agents/configs/*.yaml
   ```

2. Read the metro config to understand comp set:
   ```bash
   cat agents/configs/<metro>.yaml
   ```

3. Check for existing recent comp data:
   ```bash
   ls -t reports/{metro}/{property}/comps/comp_analysis_*.md | head -1
   ```

4. Attempt automated collection:
   ```bash
   uv run python etl/collect_comps_snapshot.py --config agents/configs/<metro>.yaml
   ```

5. If automated scraping fails (403 errors), use web search fallback:
   - Search each comp on Apartments.com
   - Check property websites for specials
   - Document all data sources

6. Validate collected data against prior snapshots

7. Generate comprehensive comp analysis report

8. Update tracking files for historical comparison

---

## Output Files

### Primary Outputs
- **JSON snapshot**: `data/public/processed/comps/{date}_{metro_slug}_comps_snapshot.json`
- **Markdown report**: `reports/{metro}/{property}/comps/comp_analysis_{date}.md`

### Tracking Files (Create/Update)
- `comps/tracking/rent_history.csv` - Monthly rent snapshots
- `comps/tracking/concession_history.csv` - Concession trends
- `comps/tracking/property_database.csv` - Owner/manager/renovation data

---

## Output Format

```markdown
# Comp Analysis: [Subject Property Name]

**Subject Property:** [Name]
**Address:** [Full Address]
**Submarket:** [Submarket Name]
**Pull Date:** [YYYY-MM-DD]
**Data Sources:** Apartments.com, Property Websites, CoStar
**Comp Set:** [X] properties within [X] mile radius

---

## Executive Summary

### Subject Property Overview

| Floorplan | Beds/Baths | Units | Avg SF | Market Rent | $/SF |
|-----------|:----------:|------:|-------:|------------:|-----:|
| [Code] | [X]BR/[X]BA | [X] | [XXX] | $[X,XXX] | $[X.XX] |
| **Total/Avg** | - | **[XXX]** | **[XXX]** | **$[X,XXX]** | **$[X.XX]** |

### Market Position Snapshot

| Metric | Subject | Comp Average | Premium/(Discount) |
|--------|--------:|-------------:|-------------------:|
| Studio Face Rent | $[XXX] | $[XXX] | +/-[X.X]% |
| Studio Effective Rent | $[XXX] | $[XXX] | +/-[X.X]% |
| 1BR Face Rent | $[X,XXX] | $[X,XXX] | +/-[X.X]% |
| 1BR Effective Rent | $[X,XXX] | $[X,XXX] | +/-[X.X]% |
| 2BR Face Rent | $[X,XXX] | $[X,XXX] | +/-[X.X]% |
| 2BR Effective Rent | $[X,XXX] | $[X,XXX] | +/-[X.X]% |
| Avg $/SF | $[X.XX] | $[X.XX] | +/-[X.X]% |

### Key Findings
1. **[Finding 1]:** [Brief insight]
2. **[Finding 2]:** [Brief insight]
3. **[Finding 3]:** [Brief insight]

---

## 1. Competitive Set Summary

| # | Property | Address | Units | Year | Distance | Studio | 1BR | 2BR | $/SF | Specials |
|:-:|----------|---------|------:|-----:|:--------:|-------:|----:|----:|-----:|:---------|
| 1 | [Name] | [Addr] | [X] | [YYYY] | [X.X mi] | $[XXX] | $[X,XXX] | $[X,XXX] | $[X.XX] | [Brief] |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **Avg** | - | - | **[X,XXX]** | **[YYYY]** | **[X.X mi]** | **$[XXX]** | **$[X,XXX]** | **$[X,XXX]** | **$[X.XX]** | - |

---

## 2. Detailed Comp Profiles

### 1. [Property Name]

**Address:** [Full Street Address, City, State ZIP]
**Year Built:** [YYYY] | **Units:** [XXX] | **Stories:** [X] | **Distance:** [X.X] mi from subject

| Unit Type | Beds/Baths | Sq Ft | Face Rent | Effective Rent | $/SF |
|-----------|:----------:|------:|----------:|---------------:|-----:|
| [Name] | [X]BR/[X]BA | [XXX] | $[X,XXX] | $[XXX] | $[X.XX] |
| [Name] | [X]BR/[X]BA | [XXX] | $[X,XXX] | $[XXX] | $[X.XX] |

**Current Specials:** [Detailed concession description or "None advertised"]
- Concession Value: [X weeks/months free = $X,XXX value]
- Effective Rent Impact: -[X.X]% from face rent

**Property Notes:**
- [Condition/renovation status]
- [Key amenities or differentiators]
- [Competitive positioning observations]

**Ownership:** [Owner Name] | **Manager:** [Management Company]
**Source:** [Apartments.com](URL) | [Property Website](URL)

---

[Repeat for each comp property]

---

## 3. Summary Statistics by Unit Type

### Studio Comparison

| Property | Distance | Units | Avg SF | Face Rent | Effective Rent | Face $/SF | Eff $/SF | Specials |
|----------|:--------:|------:|-------:|----------:|---------------:|----------:|---------:|:---------|
| **[Subject]** | - | [X] | [XXX] | $[XXX] | $[XXX] | $[X.XX] | $[X.XX] | None |
| [Comp 1] | [X.X mi] | [X] | [XXX] | $[XXX] | $[XXX] | $[X.XX] | $[X.XX] | [Type] |
| [Comp 2] | [X.X mi] | [X] | [XXX] | $[XXX] | $[XXX] | $[X.XX] | $[X.XX] | [Type] |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **Comp Average** | **[X.X mi]** | - | **[XXX]** | **$[XXX]** | **$[XXX]** | **$[X.XX]** | **$[X.XX]** | - |

**Subject vs. Comp Average:**
- Face Rent: +/-$[XX] (+/-[X.X]%)
- Effective Rent: +/-$[XX] (+/-[X.X]%)
- $/SF Premium: +/-$[X.XX] (+/-[X.X]%)

### 1-Bedroom Comparison

| Property | Distance | Units | Avg SF | Face Rent | Effective Rent | Face $/SF | Eff $/SF | Specials |
|----------|:--------:|------:|-------:|----------:|---------------:|----------:|---------:|:---------|
| **[Subject]** | - | [X] | [XXX] | $[X,XXX] | $[X,XXX] | $[X.XX] | $[X.XX] | None |
| [Comp 1] | [X.X mi] | [X] | [XXX] | $[X,XXX] | $[XXX] | $[X.XX] | $[X.XX] | [Type] |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **Comp Average** | **[X.X mi]** | - | **[XXX]** | **$[X,XXX]** | **$[XXX]** | **$[X.XX]** | **$[X.XX]** | - |

**Subject vs. Comp Average:**
- Face Rent: +/-$[XXX] (+/-[X.X]%)
- Effective Rent: +/-$[XXX] (+/-[X.X]%)
- $/SF Premium: +/-$[X.XX] (+/-[X.X]%)

### 2-Bedroom Comparison

[Same format as above]

---

## 4. Concession Analysis

### Current Concession Environment

| Property | Concession Type | Value | Months Free | Eff. Rent Discount | Lease Req |
|----------|:----------------|------:|------------:|-------------------:|:----------|
| [Subject] | None | $0 | 0 | 0% | - |
| [Comp 1] | [X] weeks free | $[X,XXX] | [X.X] | -[X.X]% | [X] mo |
| [Comp 2] | [X] month free | $[X,XXX] | [X.X] | -[X.X]% | [X] mo |
| ... | ... | ... | ... | ... | ... |
| **Market Avg** | - | **$[X,XXX]** | **[X.X]** | **-[X.X]%** | - |

### Concession Trend (vs. Prior Pull)

| Property | Prior Concession | Current Concession | Change |
|----------|:-----------------|:-------------------|:-------|
| [Comp 1] | [Prior] | [Current] | Increased / Decreased / Stable |
| [Comp 2] | [Prior] | [Current] | Increased / Decreased / Stable |

**Market Direction:** [Concessions increasing/decreasing/stable]

---

## 5. Occupancy & Availability Proxy

| Property | Total Units | Units Available | Availability % | Occupancy Est. | Trend |
|----------|------------:|----------------:|---------------:|---------------:|:-----:|
| [Subject] | [XXX] | [XX] | [X.X]% | [XX.X]% | - |
| [Comp 1] | [XXX] | [XX] | [X.X]% | [XX.X]% | - |
| [Comp 2] | [XXX] | [XX] | [X.X]% | [XX.X]% | - |
| ... | ... | ... | ... | ... | ... |
| **Submarket Avg** | **[X,XXX]** | **[XXX]** | **[X.X]%** | **[XX.X]%** | - |

*Note: Occupancy estimated as 100% minus availability percentage. Actual occupancy may differ.*

---

## 6. Owner & Management Analysis

| Property | Owner | Owner Type | Management Co. | Strategy |
|----------|:------|:-----------|:---------------|:---------|
| [Subject] | [Name] | [Institutional/Private] | [Mgmt Co] | [Value-add/Core/Core+] |
| [Comp 1] | [Name] | [Type] | [Mgmt Co] | [Strategy] |
| [Comp 2] | [Name] | [Type] | [Mgmt Co] | [Strategy] |

### Ownership Implications
- [Insight on competitive behavior based on ownership]
- [Insight on pricing strategy based on owner type]

---

## 7. Property Condition & Renovation Status

| Property | Year Built | Renovation Status | Reno Year | Condition | Interior Finishes |
|----------|:----------:|:------------------|:---------:|:---------:|:------------------|
| [Subject] | [YYYY] | [Original/Partial/Full] | [YYYY] | [A/B/C] | [Brief description] |
| [Comp 1] | [YYYY] | [Status] | [YYYY] | [Rating] | [Description] |
| [Comp 2] | [YYYY] | [Status] | [YYYY] | [Rating] | [Description] |

### Renovation Impact on Rents
- Renovated comps command +$[XX]-$[XXX] premium
- Subject renovation opportunity: [Yes/No] - potential +$[XXX] uplift

---

## 8. Market Positioning Analysis

### Competitive Tier Segmentation

```
PREMIUM TIER (Studios >$[X,XXX], 1BR >$[X,XXX])
+--------------------------------------------------+
| [Property 1] ($[X,XXX]) - [Positioning note]     |
| [Property 2] ($[X,XXX]) - [Positioning note]     |
+--------------------------------------------------+

MID-MARKET TIER (Studios $[XXX]-$[X,XXX], 1BR $[X,XXX]-$[X,XXX])
+--------------------------------------------------+
| * SUBJECT ($[XXX]/$[X,XXX]) - [Position in tier] |
| [Property 3] ($[XXX]) - [Positioning note]       |
| [Property 4] ($[XXX]) - [Positioning note]       |
+--------------------------------------------------+

VALUE TIER (Studios <$[XXX], 1BR <$[X,XXX])
+--------------------------------------------------+
| [Property 5] ($[XXX]) - [Positioning note]       |
| [Property 6] ($[XXX] face / $[XXX] eff) - Heavy  |
+--------------------------------------------------+
```

### Subject Positioning Summary
- **Face Rent Position:** [Premium/Mid-Market/Value] tier
- **Effective Rent Position:** [Premium/Mid-Market/Value] tier
- **Key Differentiators:** [List 2-3 factors]
- **Primary Competitive Threats:** [List 1-2 properties]

---

## 9. $/SF Analysis

### Rent per Square Foot Comparison

| Property | Unit Type | Sq Ft | Eff. Rent | $/SF | vs. Subject |
|----------|:----------|------:|----------:|-----:|------------:|
| **[Subject]** | Studio | [XXX] | $[XXX] | $[X.XX] | - |
| **[Subject]** | 1BR | [XXX] | $[X,XXX] | $[X.XX] | - |
| [Comp 1] | Studio | [XXX] | $[XXX] | $[X.XX] | +/-$[X.XX] |
| [Comp 1] | 1BR | [XXX] | $[XXX] | $[X.XX] | +/-$[X.XX] |
| ... | ... | ... | ... | ... | ... |

### Key $/SF Insights
- Subject studios: [Larger/Smaller] units at [higher/lower] $/SF
- Subject 1BRs: [X]% [premium/discount] vs effective rent average
- Opportunity: [Insight on pricing optimization]

*See `comps/generate_scatter_plot.py` for visualization*

---

## 10. Data Quality & Methodology

### Data Sources
| Source | Data Collected | As-Of Date | Confidence |
|--------|:---------------|:-----------|:----------:|
| Apartments.com | Rents, availability, specials | [Date] | High |
| Property websites | Floor plans, specials, amenities | [Date] | High |
| Web research | Owner/manager, renovations | [Date] | Medium |
| CoStar | Submarket metrics (if available) | [Date] | High |

### Methodology Notes
- **Face Rent:** Advertised asking rent before concessions
- **Effective Rent:** `Face Rent * (Lease Term - Free Months) / Lease Term`
- **$/SF:** Calculated using effective rent for true comparison
- **Distance:** Straight-line distance from subject property
- **Occupancy Est.:** `100% - (Available Units / Total Units)`

### Data Limitations
- [Note any properties with incomplete data]
- [Note any pricing that may be outdated]
- [Note any estimates or assumptions made]

### Update Schedule
- **Recommended frequency:** Monthly
- **Next scheduled pull:** [Date]
- **Prior pull date:** [Date] (see tracking files for comparison)

---

*Comp analysis generated: [Date] | Analyst: Market Study Agent*
*Tracking files updated: rent_history.csv, concession_history.csv, property_database.csv*
```

---

## Tracking File Schemas

### rent_history.csv
```csv
date,property,address,unit_type,beds,baths,sq_ft,face_rent,effective_rent,rent_psf,units_available,mom_change,yoy_change,notes
```

### concession_history.csv
```csv
date,property,address,unit_type,face_rent,concession_type,concession_value,free_months,effective_rent,lease_requirement,notes
```

### property_database.csv
```csv
property,address,distance_mi,units,year_built,stories,owner,management_company,ownership_type,renovation_status,renovation_year,condition_rating,cap_rate_est,last_sale_date,last_sale_price,notes
```

---

## Comp Selection Criteria

When defining the comp set in metro configs, include properties that:

1. **Geographic Proximity:** Within 1-3 mile radius of subject (adjust for density)
2. **Unit Mix Similarity:** Offer similar bedroom types as subject
3. **Age/Vintage:** Within 10-15 years of subject (or similar renovation status)
4. **Class Comparability:** Same or adjacent property class (A, B, C)
5. **Unit Count:** Similar scale (+/-50% of subject unit count)
6. **Amenity Parity:** Comparable amenity package

### Minimum Comp Set
- **Urban/Suburban Dense:** 8-12 comps
- **Suburban:** 6-10 comps
- **Rural/Tertiary:** 4-6 comps (expand radius if needed)

---

## Integration with Other Skills

- **After pull-comps:** Run `/analyze-comps` for competitive positioning analysis
- **Cross-reference:** Use with `/rent-roll` to compare in-place vs market
- **Feed into:** `/forecast` for rent growth assumptions
- **Include in:** `/report` for investment committee materials

---

## Error Handling

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|:------|:---------|
| 403 Forbidden | Site blocking scraper | Use WebSearch fallback |
| Missing specials | Not prominently displayed | Check property website directly |
| Stale pricing | Listing not updated | Note in data limitations |
| Incomplete comp | New listing | Use available data, note gaps |

### Fallback Procedure
1. If automated scraping fails, use `WebSearch` for each comp
2. Search: `"[Property Name]" apartments.com [City]`
3. Visit property website for floor plans and specials
4. Document all sources in methodology section

---

## Notes

- Always calculate and report BOTH face rent and effective rent
- Concessions are critical - a $50 face rent difference may be $150 effective
- Track trends over time using history CSVs
- Owner/manager data helps predict competitive behavior
- Update property_database.csv with any new intel gathered
- Run scatter plot generator after each pull for visualization
