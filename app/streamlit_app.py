import streamlit as st
import json
from pathlib import Path
from app.config import settings
from app.pipeline.orchestrator import run_verification_pipeline
from app.export.exporters import export_json, export_csv, export_standalone_html
from app.schemas import ReviewerActorEnum, ReviewerActionEnum
from app.core.audit import audit_manager

st.set_page_config(
    page_title="CiteVerify — Academic Citation Integrity Copilot",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ CiteVerify")
st.caption("Your citation integrity copilot — verify what your sources actually say. INNOVEDGE Hackathon 2026.")

# Sidebar
st.sidebar.header("Navigation & Actions")
offline_mode = st.sidebar.checkbox("Offline Demo Mode", value=settings.OFFLINE_DEMO)
settings.OFFLINE_DEMO = offline_mode

demo_clicked = st.sidebar.button("✨ Load Planted Demo Document (8 Cases)", use_container_width=True)
uploaded_file = st.sidebar.file_uploader("Upload Academic PDF or TXT", type=["pdf", "txt"])

if "report" not in st.session_state:
    st.session_state["report"] = None

# Progress indicator
progress_bar = st.empty()
status_text = st.empty()

def update_progress(stage, pct):
    progress_bar.progress(pct / 100.0)
    status_text.text(f"[{pct}%] {stage}")

if demo_clicked:
    demo_file = Path(__file__).parent / "demo" / "demo_doc.txt"
    with open(demo_file, "rb") as f:
        file_bytes = f.read()
    report = run_verification_pipeline(file_bytes, "demo_doc.txt", progress_callback=update_progress)
    st.session_state["report"] = report
    progress_bar.empty()
    status_text.empty()
    st.success("Planted demo document verified successfully!")

elif uploaded_file is not None:
    file_bytes = uploaded_file.read()
    report = run_verification_pipeline(file_bytes, uploaded_file.name, progress_callback=update_progress)
    st.session_state["report"] = report
    progress_bar.empty()
    status_text.empty()
    st.success(f"{uploaded_file.name} verified successfully!")

report = st.session_state.get("report")

if report:
    # Top Metrics
    st.markdown("### 📊 Citation Integrity Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Citation Health Index", f"{report.citation_health_indicator:.1f}%")
    col2.metric("Review Queue", report.items_needing_review_count)
    col3.metric("Orphan References", len(report.orphan_references))
    col4.metric("Uncited Claims", len(report.uncited_claims))

    st.info(f"**Citation Health Caveat:** {report.citation_health_caveat}")

    # Export Buttons
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button(
            "📥 Export JSON Report",
            data=export_json(report),
            file_name=f"citeverify_report_{report.document_name}.json",
            mime="application/json",
            use_container_width=True
        )
    with col_exp2:
        st.download_button(
            "📥 Export CSV Table",
            data=export_csv(report),
            file_name=f"citeverify_report_{report.document_name}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_exp3:
        st.download_button(
            "🖨️ Standalone Printable HTML Report",
            data=export_standalone_html(report),
            file_name=f"citeverify_report_{report.document_name}.html",
            mime="text/html",
            use_container_width=True
        )

    # Claim Cards
    st.markdown("---")
    st.markdown("### 📑 Evaluated Claim Cards (Risk-Ordered)")

    for card in report.claim_cards:
        c = card.claim
        v = card.primary_verdict

        color_emoji = {
            "SUPPORTED": "🟢",
            "PARTIALLY_SUPPORTED": "🟡",
            "UNSUPPORTED": "🔴",
            "CONTRADICTORY": "🛑",
            "POSSIBLY_OUTDATED": "🟠",
            "UNCITED": "🟣",
            "UNVERIFIABLE": "⚪"
        }.get(v.label, "⚪")

        with st.expander(f"{color_emoji} [{c.id}] {v.label} — Strength: {v.evidence_strength_score:.2f} ({v.score_band.value}) | Page {c.page}", expanded=True):
            if "RETRACTED_SOURCE" in [f.value for f in v.flags]:
                st.error("⚠️ RETRACTED SOURCE ALERT: The cited publication has been retracted in scholarly records!")

            if card.roll_up_note:
                st.info(f"ℹ️ {card.roll_up_note}")

            st.markdown(f"**Document Statement:** *\"{c.verbatim_text}\"*")
            st.markdown(f"**Citation Markers:** `{', '.join(c.citation_markers) if c.citation_markers else 'None (Uncited)'}`")
            st.markdown(f"**Finding Reason:** {v.reason}")

            if v.verified_evidence_quote:
                st.success(f"**Verified Verbatim Quote ({v.quote_location or 'Source'}):**\n\n> \"{v.verified_evidence_quote}\"")

            if v.scope_notes:
                st.warning(f"**Scope & Limitations:** {v.scope_notes}")

            if v.flags:
                st.markdown(f"**Flags:** `{'`, `'.join([f.value for f in v.flags])}`")

            if v.source_link:
                st.markdown(f"[🔗 Inspect Original Publication Source]({v.source_link})")

            # Reviewer panel
            st.markdown("##### ✍️ Human-in-the-Loop Review")
            r_col1, r_col2, r_col3 = st.columns([1, 1, 2])
            with r_col1:
                if st.button("Accept", key=f"acc_{c.id}"):
                    card.reviewer_status = "accepted"
                    audit_manager.record_entry(
                        claim_id=c.id,
                        pair_id=None,
                        actor=ReviewerActorEnum.REVIEWER,
                        action=ReviewerActionEnum.ACCEPTED,
                        note="Reviewer accepted automated finding via Streamlit."
                    )
                    st.rerun()

            with r_col2:
                new_v = st.selectbox("Override Verdict", ["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTORY", "POSSIBLY_OUTDATED", "UNVERIFIABLE"], key=f"ov_{c.id}")
                if st.button("Apply Override", key=f"btn_ov_{c.id}"):
                    card.primary_verdict.label = new_v
                    card.reviewer_status = "overridden"
                    audit_manager.record_entry(
                        claim_id=c.id,
                        pair_id=None,
                        actor=ReviewerActorEnum.REVIEWER,
                        action=ReviewerActionEnum.OVERRIDDEN,
                        note=f"Reviewer overrode verdict to {new_v}."
                    )
                    st.rerun()

            with r_col3:
                r_note = st.text_input("Annotation Note", key=f"note_{c.id}")
                if st.button("Save Note", key=f"btn_note_{c.id}"):
                    if r_note:
                        audit_manager.record_entry(
                            claim_id=c.id,
                            pair_id=None,
                            actor=ReviewerActorEnum.REVIEWER,
                            action=ReviewerActionEnum.NOTED,
                            note=r_note
                        )
                        st.rerun()

            # Audit History
            entries = audit_manager.get_entries_for_claim(c.id)
            if entries:
                with st.expander(f"Audit Trail ({len(entries)} entries)"):
                    for e in entries:
                        st.caption(f"**[{e.actor.value.upper()}]** `{e.action.value.upper()}` — {e.note or 'Entry recorded'} ({e.timestamp[:19]})")
else:
    st.info("👈 Click **'Load Planted Demo Document'** in the sidebar or upload a PDF/TXT document to begin verification.")
