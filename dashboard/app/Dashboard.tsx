"use client";

import { useEffect, useState, useMemo } from "react";
import { Company, Summary } from "./types";

const ZONE_COLORS: Record<string, string> = {
  Green: "#16a34a",
  Yellow: "#eab308",
  Red: "#dc2626",
  "Low-Priority": "#6b7280",
  Unknown: "#d1d5db",
};

const ZONE_PILL_CLASS: Record<string, string> = {
  Green: "zone-pill zone-pill-Green",
  Yellow: "zone-pill zone-pill-Yellow",
  Red: "zone-pill zone-pill-Red",
  "Low-Priority": "zone-pill zone-pill-LowPriority",
  Unknown: "zone-pill zone-pill-Unknown",
};

const ZONES = ["Green", "Yellow", "Red", "Low-Priority"];
const PAGE_SIZE = 50;

const HEADING = `Stanford's 4-zone framework applied to 1,223 YC companies (W24–F25).

The preregistered primary hypotheses are null.

But Red zone companies — "building automation workers don't want" —
shut down at 3.9% vs 9.0% elsewhere (Fisher p=0.016).

Stanford bundled Red + Low-Priority as "41% misaligned." Those two
zones move in opposite directions. The bundle hides the signal.`;

type SortKey = keyof Company;
type SortDir = "asc" | "desc";

function ycUrl(slug: string) {
  return `https://www.ycombinator.com/companies/${slug}`;
}

function fmt(v: number | null, decimals = 3) {
  if (v == null) return "—";
  return v.toFixed(decimals);
}

function pct(v: number | null) {
  if (v == null) return "—";
  return (v * 100).toFixed(1) + "%";
}

export default function Dashboard() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [batch, setBatch] = useState("All");
  const [zone, setZone] = useState("All");
  const [status, setStatus] = useState("All");
  const [aiOnly, setAiOnly] = useState(false);

  // Sort
  const [sortKey, setSortKey] = useState<SortKey>("zone_alignment_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  // Pagination
  const [page, setPage] = useState(1);

  useEffect(() => {
    Promise.all([
      fetch("/data/companies.json").then((r) => r.json()),
      fetch("/data/summary.json").then((r) => r.json()),
    ]).then(([cos, sum]) => {
      setCompanies(cos);
      setSummary(sum);
      setLoading(false);
    });
  }, []);

  const filtered = useMemo(() => {
    let rows = companies;
    if (batch !== "All") rows = rows.filter((c) => c.batch === batch);
    if (zone !== "All") rows = rows.filter((c) => c.zone_category === zone);
    if (status === "site-live") rows = rows.filter((c) => c.site_live && !c.shuttered);
    if (status === "shuttered") rows = rows.filter((c) => c.shuttered);
    if (aiOnly) rows = rows.filter((c) => c.is_ai);
    return rows;
  }, [companies, batch, zone, status, aiOnly]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortKey] as number | string | boolean | null;
      const bv = b[sortKey] as number | string | boolean | null;
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      let cmp = 0;
      if (typeof av === "string" && typeof bv === "string") {
        cmp = av.localeCompare(bv);
      } else {
        cmp = (av as number) < (bv as number) ? -1 : (av as number) > (bv as number) ? 1 : 0;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const pageRows = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
    setPage(1);
  }

  function handleFilterChange() {
    setPage(1);
  }

  // Summary stats on filtered set
  const stats = useMemo(() => {
    const n = filtered.length;
    const live = filtered.filter((c) => c.site_live && !c.shuttered).length;
    const shut = filtered.filter((c) => c.shuttered).length;
    const drifts = filtered
      .map((c) => c.description_drift_cosine)
      .filter((v): v is number => v != null);
    const meanDrift = drifts.length > 0 ? drifts.reduce((a, b) => a + b, 0) / drifts.length : null;
    const zoneCounts: Record<string, number> = {};
    for (const c of filtered) {
      const z = c.zone_category || "Unknown";
      zoneCounts[z] = (zoneCounts[z] || 0) + 1;
    }
    return { n, live, shut, meanDrift, zoneCounts };
  }, [filtered]);

  const batches = summary?.batches ?? [];

  if (loading) {
    return (
      <div className="container" style={{ padding: "60px 20px", color: "var(--text-muted)" }}>
        Loading…
      </div>
    );
  }

  const SortTh = ({
    label,
    col,
  }: {
    label: string;
    col: SortKey;
  }) => (
    <th
      className={sortKey === col ? "active" : ""}
      onClick={() => handleSort(col)}
    >
      {label}
      <span className="sort-icon">
        {sortKey === col ? (sortDir === "asc" ? " ▲" : " ▼") : " ⇅"}
      </span>
    </th>
  );

  return (
    <div className="container">
      {/* Hero */}
      <div className="hero">
        <h1>YC × WORKBank Postmortem</h1>
        <div className="finding">{HEADING}</div>
      </div>

      {/* Filters */}
      <div
        className="filters"
        onChange={handleFilterChange}
      >
        <select value={batch} onChange={(e) => { setBatch(e.target.value); setPage(1); }}>
          <option value="All">All batches</option>
          {batches.map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>

        <select value={zone} onChange={(e) => { setZone(e.target.value); setPage(1); }}>
          <option value="All">All zones</option>
          {ZONES.map((z) => (
            <option key={z} value={z}>{z}</option>
          ))}
        </select>

        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="All">All statuses</option>
          <option value="site-live">Site live</option>
          <option value="shuttered">Shuttered</option>
        </select>

        <label>
          <input
            type="checkbox"
            checked={aiOnly}
            onChange={(e) => { setAiOnly(e.target.checked); setPage(1); }}
          />
          AI only
        </label>
      </div>

      {/* Summary strip */}
      <div className="summary-strip">
        <div className="stat-card">
          <div className="stat-label">Companies</div>
          <div className="stat-value">{stats.n.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Site live</div>
          <div className="stat-value" style={{ color: "var(--green)" }}>
            {stats.n > 0 ? ((stats.live / stats.n) * 100).toFixed(1) : "—"}%
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Shuttered</div>
          <div className="stat-value" style={{ color: "var(--red)" }}>
            {stats.n > 0 ? ((stats.shut / stats.n) * 100).toFixed(1) : "—"}%
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Mean drift</div>
          <div className="stat-value">
            {stats.meanDrift != null ? stats.meanDrift.toFixed(3) : "—"}
          </div>
        </div>
        <ZoneBarCard counts={stats.zoneCounts} total={stats.n} />
      </div>

      {/* Table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <SortTh label="Name" col="name" />
              <SortTh label="Batch" col="batch" />
              <SortTh label="Zone" col="zone_category" />
              <SortTh label="Alignment" col="zone_alignment_score" />
              <SortTh label="Live" col="site_live" />
              <SortTh label="Drift" col="description_drift_cosine" />
              <SortTh label="Team" col="team_size" />
              <th>One-liner</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((c) => (
              <tr key={c.slug}>
                <td>
                  {c.website ? (
                    <a href={ycUrl(c.slug)} target="_blank" rel="noopener noreferrer">
                      {c.name || c.slug}
                    </a>
                  ) : (
                    <a href={ycUrl(c.slug)} target="_blank" rel="noopener noreferrer">
                      {c.name || c.slug}
                    </a>
                  )}
                </td>
                <td style={{ whiteSpace: "nowrap", color: "var(--text-muted)" }}>
                  {c.batch || "—"}
                </td>
                <td>
                  {c.zone_category ? (
                    <span className={ZONE_PILL_CLASS[c.zone_category] || "zone-pill zone-pill-Unknown"}>
                      {c.zone_category}
                    </span>
                  ) : "—"}
                </td>
                <td style={{ fontVariantNumeric: "tabular-nums" }}>
                  {pct(c.zone_alignment_score)}
                </td>
                <td>
                  {c.shuttered ? (
                    <span className="status-dead" title="Shuttered">✗</span>
                  ) : c.site_live ? (
                    <span className="status-live" title="Site live">✓</span>
                  ) : (
                    <span style={{ color: "var(--text-muted)" }} title="Unknown">—</span>
                  )}
                </td>
                <td style={{ fontVariantNumeric: "tabular-nums" }}>
                  {fmt(c.description_drift_cosine)}
                </td>
                <td>{c.team_size ?? "—"}</td>
                <td className="one-liner-cell">
                  <span
                    className="one-liner-text"
                    title={c.one_liner || ""}
                  >
                    {c.one_liner
                      ? c.one_liner.length > 80
                        ? c.one_liner.slice(0, 80) + "…"
                        : c.one_liner
                      : "—"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
          ← Prev
        </button>
        <span>
          Page {page} of {totalPages} &nbsp;·&nbsp; {sorted.length.toLocaleString()} companies
        </span>
        <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
          Next →
        </button>
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-links">
          <a href="https://github.com/samm-meyer/yc-workbank-postmortem-2026" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
          <a href="/findings/">Findings</a>
          <a href="https://github.com/samm-meyer/yc-workbank-postmortem-2026/commit/HEAD" target="_blank" rel="noopener noreferrer">
            Preregistration commit
          </a>
        </div>
        <div className="citation">
          Meyer, S. (2026). <em>Stanford WORKBank Framework on YC Data: A Preregistered Test.</em>{" "}
          yc-workbank-postmortem-2026.
        </div>
      </footer>
    </div>
  );
}

function ZoneBarCard({ counts, total }: { counts: Record<string, number>; total: number }) {
  const ZONE_ORDER = ["Green", "Yellow", "Red", "Low-Priority", "Unknown"];
  return (
    <div className="zone-bar-card">
      <div className="zone-bar-label">Zone distribution</div>
      <div className="zone-bar">
        {ZONE_ORDER.map((z) => {
          const n = counts[z] || 0;
          const w = total > 0 ? (n / total) * 100 : 0;
          if (w < 1) return null;
          return (
            <div
              key={z}
              className="zone-bar-segment"
              style={{ width: `${w}%`, background: ZONE_COLORS[z] }}
              title={`${z}: ${n} (${w.toFixed(1)}%)`}
            />
          );
        })}
      </div>
      <div className="zone-bar-legend">
        {ZONE_ORDER.filter((z) => (counts[z] || 0) > 0).map((z) => (
          <div key={z} className="zone-bar-legend-item">
            <div className="zone-dot" style={{ background: ZONE_COLORS[z] }} />
            {z} ({counts[z] || 0})
          </div>
        ))}
      </div>
    </div>
  );
}
