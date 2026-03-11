"""
Child Safety Guardian AI — Streamlit Frontend
Calls the FastAPI backend to audit YouTube videos for child safety policy compliance.
"""

import streamlit as st
import requests

# ────────────────────────── Page Config ──────────────────────────
st.set_page_config(
    page_title="Child Safety Guardian AI",
    page_icon="🛡️",
    layout="wide",
)

# ────────────────────────── Custom CSS ──────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    .block-container { padding-top: 2rem; }

    /* ── Status badges ── */
    .badge-pass {
        display: inline-block;
        padding: 0.35em 1em;
        border-radius: 0.5em;
        font-weight: 700;
        font-size: 1.1rem;
        color: #fff;
        background: linear-gradient(135deg, #22c55e, #16a34a);
    }
    .badge-fail {
        display: inline-block;
        padding: 0.35em 1em;
        border-radius: 0.5em;
        font-weight: 700;
        font-size: 1.1rem;
        color: #fff;
        background: linear-gradient(135deg, #ef4444, #dc2626);
    }

    /* ── Severity pills ── */
    .severity-critical {
        display: inline-block;
        padding: 0.2em 0.7em;
        border-radius: 1em;
        font-weight: 600;
        font-size: 0.85rem;
        color: #fff;
        background: #dc2626;
    }
    .severity-warning {
        display: inline-block;
        padding: 0.2em 0.7em;
        border-radius: 1em;
        font-weight: 600;
        font-size: 0.85rem;
        color: #fff;
        background: #f59e0b;
    }

    /* ── Metric cards ── */
    .metric-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
    }
    .metric-card .label {
        font-size: 0.8rem;
        opacity: 0.6;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card .value {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 0.2rem;
    }

    /* ── Violation card ── */
    .violation-card {
        background: rgba(255,255,255,0.04);
        border-left: 4px solid #ef4444;
        border-radius: 0 0.5rem 0.5rem 0;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.65rem;
    }
    .violation-card.warning {
        border-left-color: #f59e0b;
    }

    /* ── Policy card ── */
    .policy-card {
        background: rgba(59, 130, 246, 0.08);
        border-left: 4px solid #3b82f6;
        border-radius: 0 0.5rem 0.5rem 0;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.65rem;
        font-size: 0.9rem;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────── Sidebar ──────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ Child Safety Guardian AI")
    st.caption("Automated video child safety auditing powered by AI.")
    st.divider()

    backend_url = st.text_input(
        "Backend URL",
        value="http://localhost:8000",
        help="Base URL of the running FastAPI backend.",
    )

    # Health check
    st.markdown("##### Backend Status")
    try:
        health = requests.get(f"{backend_url}/health", timeout=5)
        if health.status_code == 200:
            st.success("🟢  Connected", icon="✅")
        else:
            st.error(f"🔴  Unhealthy (HTTP {health.status_code})")
    except requests.ConnectionError:
        st.error("🔴  Cannot reach backend")
    except Exception as e:
        st.error(f"🔴  {e}")

    st.divider()
    st.markdown(
        "**How it works**\n"
        "1. Paste a YouTube URL\n"
        "2. Click **Run Audit**\n"
        "3. The pipeline downloads, indexes,\n"
        "   and audits the video against\n"
        "   YouTube child safety policy rules\n"
        "4. View the results below"
    )

# ────────────────────────── Main Area ──────────────────────────
st.title("🎬  Child Safety Policy Audit")
st.markdown("Paste a YouTube video URL below and run the child safety audit.")

col_input, col_btn = st.columns([4, 1], vertical_alignment="bottom")
with col_input:
    video_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
    )
with col_btn:
    run_clicked = st.button("🚀 Run Audit", type="primary", use_container_width=True)

# ────────────────────────── Video Preview ──────────────────────────
if video_url.strip():
    try:
        oembed_resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": video_url.strip(), "format": "json"},
            timeout=5,
        )
        if oembed_resp.status_code == 200:
            oembed = oembed_resp.json()
            prev_col1, prev_col2 = st.columns([1, 3])
            with prev_col1:
                st.image(oembed.get("thumbnail_url"), use_container_width=True)
            with prev_col2:
                st.markdown(f"**{oembed.get('title', 'Unknown Title')}**")
                st.caption(f"By {oembed.get('author_name', 'Unknown')}")
    except Exception:
        pass  # Silently ignore preview errors — non-critical

# ────────────────────────── Audit Execution ──────────────────────────
if run_clicked:
    if not video_url.strip():
        st.warning("Please enter a YouTube URL first.")
        st.stop()

    with st.spinner("🔄  Running child safety audit — this may take a few minutes…"):
        try:
            response = requests.post(
                f"{backend_url}/audit",
                json={"video_url": video_url.strip()},
                timeout=600,  # generous timeout for video processing
            )
            response.raise_for_status()
            data = response.json()
        except requests.ConnectionError:
            st.error("❌  Could not connect to the backend. Is it running?")
            st.stop()
        except requests.HTTPError as e:
            st.error(f"❌  Backend error: {e.response.text}")
            st.stop()
        except Exception as e:
            st.error(f"❌  Unexpected error: {e}")
            st.stop()

    # ────────────────────── Results ──────────────────────
    st.divider()
    st.subheader("📋  Audit Results")

    # ── Status + Metadata Row ──
    c1, c2, c3 = st.columns(3)

    status = data.get("status", "UNKNOWN")
    badge_class = "badge-pass" if status == "PASS" else "badge-fail"
    with c1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">Status</div>'
            f'<div class="value"><span class="{badge_class}">{status}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">Video ID</div>'
            f'<div class="value">{data.get("video_id", "—")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">Session ID</div>'
            f'<div class="value" style="font-size:0.85rem;">{data.get("session_id", "—")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Violations ──
    violations = data.get("compliance_results", [])

    st.markdown("#### ⚠️  Violations Detected" if violations else "#### ✅  No Violations Detected")

    if violations:
        for v in violations:
            severity = v.get("severity", "WARNING").upper()
            sev_class = "severity-critical" if severity == "CRITICAL" else "severity-warning"
            card_class = "violation-card" if severity == "CRITICAL" else "violation-card warning"
            st.markdown(
                f'<div class="{card_class}">'
                f'<span class="{sev_class}">{severity}</span> '
                f'&nbsp; <strong>{v.get("category", "General")}</strong>'
                f'<p style="margin:0.4em 0 0 0; opacity:0.85;">{v.get("description", "")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("The video passed all child safety policy checks. No violations were found.")

    # ── Policies Checked (RAG Context) — collapsible ──
    retrieved_policies = data.get("retrieved_policies", [])
    if retrieved_policies:
        with st.expander("📑  Policies Checked — click to expand", expanded=False):
            st.caption("The following child safety policy excerpts were retrieved from the knowledge base and used to evaluate this video:")
            for i, policy in enumerate(retrieved_policies, 1):
                st.markdown(
                    f'<div class="policy-card">'
                    f'<strong>Policy Excerpt {i}</strong>'
                    f'<p style="margin:0.4em 0 0 0;">{policy}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Final Report ──
    st.markdown("#### 📝  Final Report")
    st.markdown(data.get("final_report", "*No report generated.*"))
