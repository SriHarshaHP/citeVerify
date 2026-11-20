import json
import csv
import io
from app.schemas import VerificationReport

def export_json(report: VerificationReport) -> str:
    """Exports full report model as formatted JSON."""
    return report.model_dump_json(indent=2)

def export_csv(report: VerificationReport) -> str:
    """Exports claim-level findings as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Claim ID",
        "Page",
        "Section",
        "Claim Text",
        "Citation Markers",
        "Verdict",
        "Final Verdict",
        "Evidence Strength Score",
        "Score Band",
        "Evidence Tier",
        "Reference Status",
        "Atomic Subclaims Count",
        "Causality Overclaim",
        "Study Design",
        "Sample Size",
        "Flags",
        "Reason",
        "Verified Quote",
        "Quote Location",
        "Source Link",
        "Review Status",
        "Reviewer Note"
    ])

    for card in report.claim_cards:
        c = card.claim
        v = card.primary_verdict
        flags_str = "; ".join([f.value for f in v.flags])
        markers_str = ", ".join(c.citation_markers)
        ref_status = card.reference_verification.status.value if card.reference_verification else "N/A"
        atomic_count = len(c.atomic_subclaims)
        causality = "YES" if (card.causality_assessment and card.causality_assessment.is_causality_overclaim) else "NO"
        study_design = card.methodology_info.study_design if card.methodology_info else ""
        sample_size = card.methodology_info.sample_size or str(card.methodology_info.patient_count or "") if card.methodology_info else ""
        
        writer.writerow([
            c.id,
            c.page,
            c.section,
            c.verbatim_text,
            markers_str,
            v.label,
            card.final_verdict or v.label,
            f"{v.evidence_strength_score:.2f}",
            v.score_band.value,
            v.evidence_tier.value,
            ref_status,
            atomic_count,
            causality,
            study_design,
            sample_size,
            flags_str,
            v.reason,
            v.verified_evidence_quote or "",
            v.quote_location or "",
            v.source_link or "",
            card.reviewer_status,
            card.reviewer_note or ""
        ])

    return output.getvalue()

def export_corrected_bib(report: VerificationReport) -> str:
    """Exports verified and corrected references in BibTeX format."""
    entries = []
    seen = set()
    for card in report.claim_cards:
        if card.reference_verification:
            ref_ver = card.reference_verification
            key = ref_ver.reference_key or "ref"
            if key in seen:
                continue
            seen.add(key)
            title = ref_ver.verified_title or "Untitled"
            authors = " and ".join(ref_ver.verified_authors) if ref_ver.verified_authors else "Unknown"
            year = ref_ver.verified_year or ""
            doi = ref_ver.verified_doi or ref_ver.extracted_doi or ""
            journal = ref_ver.verified_journal or ""
            
            entry = f"@article{{{key},\n  author = {{{authors}}},\n  title = {{{{{title}}}}},\n  year = {{{year}}},\n  journal = {{{journal}}},\n  doi = {{{doi}}}\n}}"
            entries.append(entry)
            
    for ref in report.orphan_references:
        key = ref.key or "orphan"
        if key not in seen:
            seen.add(key)
            authors = " and ".join(ref.authors) if ref.authors else "Unknown"
            entry = f"@article{{{key},\n  author = {{{authors}}},\n  title = {{{{{ref.title or 'Untitled'}}}}},\n  year = {{{ref.year or ''}}},\n  doi = {{{ref.doi or ''}}}\n}}"
            entries.append(entry)
            
    return "\n\n".join(entries) if entries else "% No references found"

def export_standalone_html(report: VerificationReport) -> str:
    """
    Generates a self-contained, standalone, print-optimized HTML report with
    Academic Evidence Intelligence, Scorecard, and Methodology analysis.
    """
    cards_html = []
    verdict_colors = {
        "SUPPORTED": "#16a34a",
        "PARTIALLY_SUPPORTED": "#ca8a04",
        "UNSUPPORTED": "#dc2626",
        "CONTRADICTORY": "#991b1b",
        "POSSIBLY_OUTDATED": "#ea580c",
        "UNCITED": "#7c3aed",
        "AMBIGUOUS_CITATION": "#d97706",
        "UNVERIFIABLE": "#64748b",
        "OVERGENERALIZED": "#c026d3",
        "CAUSALITY_OVERCLAIM": "#e11d48",
        "SCOPE_MISMATCH": "#d97706",
        "CONTEXT_OMITTED": "#0284c7",
        "MISINTERPRETED": "#b91c1c"
    }

    for card in report.claim_cards:
        c = card.claim
        v = card.primary_verdict
        color = verdict_colors.get(card.final_verdict or v.label, "#475569")
        flags_badges = "".join([f'<span class="badge flag-badge">{f.value}</span>' for f in v.flags])
        
        # Subclaims HTML
        subclaims_html = ""
        if c.atomic_subclaims and len(c.atomic_subclaims) > 1:
            subclaim_items = "".join([
                f'<li style="margin-bottom: 4px;"><strong>{sub.subclaim_id}:</strong> {sub.text} <span class="badge" style="background:#e2e8f0; color:#334155; font-size:10px;">{sub.category}</span></li>'
                for sub in c.atomic_subclaims
            ])
            subclaims_html = f"""
            <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 10px; margin-bottom: 12px; font-size: 12px;">
                <strong style="color: #475569;">🔬 Decomposed Atomic Subclaims ({len(c.atomic_subclaims)}):</strong>
                <ul style="margin: 6px 0 0 16px; padding: 0;">{subclaim_items}</ul>
            </div>
            """

        # Reference Verification HTML
        ref_ver_html = ""
        if card.reference_verification:
            rv = card.reference_verification
            status_color = "#16a34a" if rv.status.value == "DOI_VERIFIED" else ("#ea580c" if "MISMATCH" in rv.status.value else "#dc2626")
            correction_html = ""
            if rv.suggested_correction:
                correction_html = f'<div style="margin-top: 4px; font-size: 11.5px; color: #b45309;"><strong>Suggested Fix:</strong> {rv.suggested_correction}</div>'
            
            ref_ver_html = f"""
            <div style="background: #f1f5f9; border-left: 3px solid {status_color}; padding: 8px 12px; border-radius: 4px; margin-bottom: 10px; font-size: 12px;">
                <div><strong>Bibliographic Verification:</strong> <span class="badge" style="background:{status_color}; color:white;">{rv.status.value}</span> ({rv.match_source})</div>
                {f'<div style="color:#64748b; font-size:11px;">Verified: {rv.verified_title} ({rv.verified_year}) • DOI: {rv.verified_doi}</div>' if rv.verified_title else ''}
                {correction_html}
            </div>
            """

        # Methodology & Stats HTML
        methodology_html = ""
        if card.methodology_info:
            mi = card.methodology_info
            lims = "; ".join(mi.explicit_author_limitations) if mi.explicit_author_limitations else "None explicitly cited in abstract"
            concerns = "; ".join(mi.methodological_concerns) if mi.methodological_concerns else "Standard academic design"
            methodology_html = f"""
            <div style="background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 6px; padding: 10px; margin-bottom: 10px; font-size: 12px; color: #581c87;">
                <div><strong>Study Methodology:</strong> {mi.study_design.replace('_', ' ').title()} • Sample: {mi.sample_size_str}</div>
                <div style="margin-top: 4px;"><strong>Author Limitations:</strong> {lims}</div>
                <div style="margin-top: 2px;"><strong>Methodological Concerns:</strong> {concerns}</div>
            </div>
            """

        # Causality Overclaim Banner
        causality_banner = ""
        if card.causality_assessment and card.causality_assessment.is_causality_overclaim:
            causality_banner = f"""
            <div style="background: #fff1f2; border: 1px solid #fda4af; color: #9f1239; padding: 8px 12px; border-radius: 6px; font-size: 12px; margin-bottom: 10px;">
                <strong>⚠️ Causality Overclaim Detected:</strong> Document asserts causal connection ("{', '.join(card.causality_assessment.detected_causal_verbs)}"), but cited source utilizes an observational or correlational methodology.
            </div>
            """

        quote_block = ""
        if v.verified_evidence_quote:
            quote_block = f"""
            <div class="evidence-box">
                <div class="evidence-header">
                    <strong>Verified Verbatim Evidence Quote:</strong>
                    <span class="location">{v.quote_location or 'Source excerpt'}</span>
                </div>
                <blockquote>“{v.verified_evidence_quote}”</blockquote>
            </div>
            """

        audit_rows = "".join([
            f"<tr><td>{a.timestamp[:19].replace('T', ' ')}</td><td>{a.actor.value}</td><td>{a.action.value}</td><td>{a.note or ''}</td></tr>"
            for a in card.audit_history
        ])

        audit_table = ""
        if audit_rows:
            audit_table = f"""
            <div class="audit-section">
                <h6>Review Audit Trail:</h6>
                <table class="audit-table">
                    <thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Note</th></tr></thead>
                    <tbody>{audit_rows}</tbody>
                </table>
            </div>
            """

        roll_up_banner = ""
        if card.roll_up_note:
            roll_up_banner = f'<div class="rollup-banner">ℹ️ {card.roll_up_note}</div>'

        retracted_banner = ""
        if "RETRACTED_SOURCE" in [f.value for f in v.flags]:
            retracted_banner = '<div class="retracted-banner">⚠️ CAUTION: Cited publication has been RETRACTED in scholarly databases.</div>'

        cards_html.append(f"""
        <div class="claim-card" style="border-left: 5px solid {color};">
            {retracted_banner}
            {causality_banner}
            {roll_up_banner}
            <div class="card-header">
                <div>
                    <span class="claim-id">{c.id}</span>
                    <span class="badge" style="background-color: {color}; color: white;">{card.final_verdict or v.label}</span>
                    <span class="badge tier-badge">Tier: {v.evidence_tier.value}</span>
                    <span class="badge score-badge">Evidence Strength: {v.evidence_strength_score:.2f} ({v.score_band.value})</span>
                    {f'<span class="badge" style="background:#fef08a; color:#854d0e;">Human: {card.reviewer_status.upper()}</span>' if card.reviewer_status != 'pending' else ''}
                </div>
                <div class="meta">Page {c.page} • {c.section}</div>
            </div>
            <div class="claim-statement">
                <strong>Document Claim:</strong>
                <p>"{c.verbatim_text}"</p>
                <div class="citations-tagged">Markers: {', '.join(c.citation_markers) if c.citation_markers else 'None (Uncited)'}</div>
            </div>
            {subclaims_html}
            {ref_ver_html}
            <div class="verdict-reason">
                <strong>Finding Reason:</strong> {v.reason}
            </div>
            {quote_block}
            {methodology_html}
            {f'<div class="scope-notes"><strong>Scope & Limitations:</strong> {v.scope_notes}</div>' if v.scope_notes else ''}
            <div class="flags-container">
                {flags_badges}
            </div>
            {f'<div class="source-link"><a href="{v.source_link}" target="_blank">🔗 Inspect Original Publication Source</a></div>' if v.source_link else ''}
            {audit_table}
        </div>
        """)

    summary_badges = "".join([
        f'<div class="summary-pill"><span class="count">{count}</span><span class="label">{label}</span></div>'
        for label, count in report.summary_counts.items()
    ])

    # Internal Contradictions Section
    contradictions_html = ""
    if report.internal_contradictions:
        c_items = "".join([
            f'<div style="margin-top:6px; font-size:12px;"><strong>Claims [{c.claim_id_1}] and [{c.claim_id_2}]:</strong> {c.explanation}</div>'
            for c in report.internal_contradictions
        ])
        contradictions_html = f"""
        <div style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 16px; margin-bottom: 25px;">
            <h4 style="margin: 0; color: #9f1239;">⚠️ Internal Document Contradictions Detected ({len(report.internal_contradictions)})</h4>
            <div style="color: #881337;">The document contains internal statements that conflict with each other independently of citations:</div>
            {c_items}
        </div>
        """

    # Scorecard Section
    scorecard_html = ""
    if report.scorecard:
        sc = report.scorecard
        scorecard_html = f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h4 style="margin: 0 0 12px 0; color: #0f172a;">📊 Document Research Integrity Scorecard</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <div style="font-size: 22px; font-weight: 700; color: #2563eb;">{sc.research_integrity_index:.1f}/100</div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Research Integrity Index</div>
                    <div style="font-size: 10.5px; color: #94a3b8; margin-top: 4px;">{sc.index_formula_description}</div>
                </div>
                <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <div style="font-size: 22px; font-weight: 700; color: #059669;">{sc.citation_coverage_pct:.1f}%</div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Citation Coverage</div>
                    <div style="font-size: 10.5px; color: #94a3b8; margin-top: 4px;">{sc.cited_claims_count} of {sc.total_claims} claims cited</div>
                </div>
                <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <div style="font-size: 22px; font-weight: 700; color: #7c3aed;">{sc.source_diversity_ratio:.2f}</div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Source Diversity Ratio</div>
                    <div style="font-size: 10.5px; color: #94a3b8; margin-top: 4px;">{sc.unique_sources_count} unique sources</div>
                </div>
                <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <div style="font-size: 22px; font-weight: 700; color: {'#dc2626' if sc.retracted_sources_count > 0 else '#16a34a'};">{sc.retracted_sources_count}</div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600;">Retracted Sources</div>
                    <div style="font-size: 10.5px; color: #94a3b8; margin-top: 4px;">Cross-verified OpenAlex/Crossref</div>
                </div>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CiteVerify Verification Report — {report.document_name}</title>
    <style>
        @page {{ size: A4; margin: 1.5cm; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5; margin: 0; padding: 20px; background: #f8fafc; }}
        .container {{ max-width: 950px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        h1 {{ margin: 0 0 5px 0; font-size: 26px; color: #0f172a; }}
        .tagline {{ color: #64748b; font-size: 14px; margin-bottom: 25px; }}
        .header-meta {{ display: flex; flex-wrap: wrap; gap: 15px; padding: 15px; background: #f1f5f9; border-radius: 6px; font-size: 13px; margin-bottom: 25px; }}
        .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }}
        .dash-card {{ padding: 15px; border-radius: 6px; background: #ffffff; border: 1px solid #e2e8f0; }}
        .dash-value {{ font-size: 28px; font-weight: 700; color: #2563eb; }}
        .dash-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
        .summary-bar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 25px; }}
        .summary-pill {{ display: flex; align-items: center; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 20px; padding: 4px 12px; font-size: 13px; }}
        .summary-pill .count {{ font-weight: 700; margin-right: 6px; color: #0f172a; }}
        .claim-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin-bottom: 20px; page-break-inside: avoid; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .claim-id {{ font-weight: 800; font-size: 15px; margin-right: 10px; color: #0f172a; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-right: 6px; }}
        .tier-badge {{ background: #e0f2fe; color: #0369a1; }}
        .score-badge {{ background: #f1f5f9; color: #334155; }}
        .flag-badge {{ background: #fee2e2; color: #991b1b; }}
        .claim-statement p {{ margin: 5px 0; font-size: 15px; font-style: italic; color: #0f172a; }}
        .citations-tagged {{ font-size: 12px; color: #64748b; margin-bottom: 10px; }}
        .verdict-reason {{ font-size: 14px; margin-bottom: 12px; color: #334155; }}
        .evidence-box {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 12px; margin-bottom: 12px; }}
        .evidence-header {{ font-size: 12px; color: #166534; display: flex; justify-content: space-between; margin-bottom: 6px; }}
        .evidence-box blockquote {{ margin: 0; font-size: 13.5px; color: #14532d; font-style: normal; }}
        .scope-notes {{ font-size: 12px; color: #64748b; margin-bottom: 10px; }}
        .source-link a {{ font-size: 12px; color: #2563eb; text-decoration: none; }}
        .retracted-banner {{ background: #fef2f2; border: 1px solid #f87171; color: #991b1b; padding: 8px 12px; border-radius: 4px; font-weight: 600; font-size: 12px; margin-bottom: 12px; }}
        .rollup-banner {{ background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; padding: 6px 10px; border-radius: 4px; font-size: 12px; margin-bottom: 10px; }}
        .audit-table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 6px; }}
        .audit-table th, .audit-table td {{ border: 1px solid #e2e8f0; padding: 4px 8px; text-align: left; }}
        .audit-table th {{ background: #f8fafc; color: #475569; }}
        .disclaimer-box {{ border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 40px; font-size: 12px; color: #64748b; }}
        @media print {{
            body {{ background: #ffffff; padding: 0; }}
            .container {{ box-shadow: none; padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <h1>CiteVerify Evidence-Backed Verification Report</h1>
                <div class="tagline">Your citation integrity copilot — verify what your sources actually say.</div>
            </div>
            <button class="no-print" onclick="window.print()" style="padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">🖨️ Print / Save as PDF</button>
        </div>

        <div class="header-meta">
            <div><strong>Document:</strong> {report.document_name}</div>
            <div><strong>Total Pages:</strong> {report.total_pages}</div>
            <div><strong>Citation Style:</strong> {report.citation_style.upper()}</div>
            <div><strong>Extracted Claims:</strong> {report.total_claims}</div>
            <div><strong>Generated:</strong> {report.created_at[:19].replace('T', ' ')} UTC</div>
        </div>

        {scorecard_html}
        {contradictions_html}

        <div class="dashboard">
            <div class="dash-card">
                <div class="dash-value">{report.citation_health_indicator:.1f}%</div>
                <div class="dash-label">Citation Health Index</div>
            </div>
            <div class="dash-card">
                <div class="dash-value" style="color: {'#dc2626' if report.items_needing_review_count > 0 else '#16a34a'};">{report.items_needing_review_count}</div>
                <div class="dash-label">Items In Review Queue</div>
            </div>
            <div class="dash-card">
                <div class="dash-value">{len(report.orphan_references)}</div>
                <div class="dash-label">Orphan References</div>
            </div>
            <div class="dash-card">
                <div class="dash-value">{len(report.uncited_claims)}</div>
                <div class="dash-label">Uncited Claims</div>
            </div>
        </div>

        <div class="summary-bar">
            {summary_badges}
        </div>

        <h3 style="margin-bottom: 15px; color: #0f172a;">Evaluated Claim Cards (Risk-Ordered)</h3>
        {''.join(cards_html)}

        <div class="disclaimer-box">
            <strong>Academic Integrity Notice & Copilot Disclaimer:</strong><br>
            CiteVerify is an integrity copilot designed to assist student researchers, peer reviewers, and supervisors.
            Findings are aids to human review, not final academic judgments. Quotes displayed are verified verbatim substrings.
            Where sources are restricted to abstracts, absence of evidence is not evidence of absence.
        </div>
    </div>
</body>
</html>
"""
    return html_content
