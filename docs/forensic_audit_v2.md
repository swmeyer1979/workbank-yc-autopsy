# Forensic audit of all 21 v2-shuttered companies

Manual triangulation conducted 2026-04-24 after the 2-of-3 source automated verification labeled 21 companies as shuttered. Each company re-fetched with a current browser-grade User-Agent (Chrome 131, Mac), redirects followed, body-text length measured via BeautifulSoup, and YC `status` cross-referenced.

## Verdict table

| slug | YC status | curl status | text len | redirect destination | verdict |
|---|---|---|---|---|---|
| crouton | Active | 200 | 7 | — | Likely live (SPA shell, YC says Active) |
| supercontrast | Inactive | 200 | 13 | — | Dead (YC confirms; SPA shell only) |
| kanava-ai | Inactive | 200 | 9 | — | Dead (YC confirms; SPA shell) |
| invaria | Inactive | 200 | 0 | — | Dead (empty body) |
| **deepsilicon** | Inactive | 200 | 0 | → `sarai-tid.com` (parked/affiliate spam) | **Hard dead** (domain redirected to spam) |
| **lilac-labs** | Active | 200 | 21 | drive-thru.ai → lilaclabs.ai | **PIVOT** — live as Lilac Labs |
| riskangle | Inactive | 200 | 137 | — | Ambiguous (real content, YC Inactive) |
| **formula-insight** | Active | 200 | 264 | — | **Live** (false positive — YC Active, real content) |
| nuntius | Inactive | 200 | 44 | — | Dead (per YC, SPA shell) |
| **quary** | Inactive | 000 | — | DNS fail | **Hard dead** |
| **mango-health** | Inactive | 000 | — | DNS fail | **Hard dead** |
| dgi-apparel | Inactive | 200 | 89 | — | Dead (per YC) |
| engines | Inactive | 200 | 264 | — | Ambiguous (SPA, has content) |
| selera-medical | Inactive | 200 | 93 | — | Dead (per YC) |
| **celest** | Inactive | 200 | 2729 | — | **Likely live** (rich content despite YC Inactive) |
| toolify | Inactive | 200 | 0 | — | Dead (empty body) |
| **crmcopilot** | Inactive | **404** | — | — | **Hard dead** |
| **abel** | Inactive | 200 | 104 | tryabel.com → tryabel-com.l.ink (parked) | **Hard dead** (parked link-shortener) |
| **lumona** | Inactive | **404** | — | — | **Hard dead** |
| sublingual | Inactive | 200 | 81 | — | Dead (per YC, small SPA) |
| **strike** | Active | 200 | 30 | tradestrike.app → pluto.trade | **PIVOT** — live as Pluto |

## Tally

- Hard-confirmed dead: 7 (404, DNS fail, parked redirects)
- Probably dead (YC Inactive + tiny SPA shell, no contradicting signal): 7
- **Pivoted, live**: 2 (`lilac-labs`, `strike`)
- **Likely live false positive**: 3 (`crouton`, `formula-insight`, `celest`)
- Ambiguous: 2 (`riskangle`, `engines`)

True shutdown count: **7 (hard) to 14 (hard + probable)**. Misclassification rate at v2 = ~5/21 = 24%.

## Why even 2-of-3 verification still fails ~24% of the time

1. **Browser fetch can't render JS.** SPAs that hydrate content via JavaScript return small initial HTML to a non-browser fetcher. Body-text length thresholds misread these as dead.
2. **YC's `status` field lags reality.** Companies that pivoted, were quietly acquired, or rebranded onto a new domain may stay marked `Inactive` for weeks or months while the new entity is healthy.
3. **Wayback Machine null is non-random.** Companies with `robots.txt` blocking archive crawlers, or new domains that haven't been visited by the Wayback bot recently, return null Source C — leaving the label dependent on Source A + B alone.
4. **Domain rebrands defeat single-domain HTTP probes.** Two of our 21 v2-shuttered are confirmed pivots (`drive-thru.ai → lilaclabs.ai`; `tradestrike.app → pluto.trade`). Following the original YC-listed website to its current state requires manual resolution; automated pipelines will mis-label these as shuttered every time.

## Effect on the null finding

The paper's preregistered null result is robust to the verification grade. Cell counts are already 2–7 shutdowns per zone under v2 labels; reducing to a hard-confirmed count of 7 makes the per-zone counts even sparser and the Fisher contrasts more solidly null.

## Implication for replicators

If you're conducting startup-mortality research at any scale: a manual forensic audit of every flagged shutdown is a non-trivial cost. Plan for it. Single-source proxies fail at ~80%; 2-of-3 source verification fails at ~24%; 3-of-3 high-confidence agreement was 0% in our sample (all 21 were 2-of-3 low-confidence). True ground truth requires either domain-rebrand resolution + JS-rendering fetch + active company-search, or paid services with company-resolution like Crunchbase/PitchBook.
