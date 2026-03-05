import html as _html
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from analyst.scorer import analyse_essay
from analyst.content_visualisation import (
    generate_wordcloud,
    build_knowledge_graph,
    render_graph,
)
from analyst.language_structure import (
    vocabulary_analysis,
    readability_score,
    argumentative_zoning,
    zoning_chart,
)
from analyst.grammar_analysis import grammar_suggestions, long_sentences
from analyst.sentiment_discourse import sentiment_analysis, discourse_analysis
from analyst.reflective_feedback import reflective_llm_feedback
from analyst.report_generator import (
    generate_report_markdown,
    generate_pdf_bytes,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Essay Analyst",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS (light / dark aware) ──────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { letter-spacing: -0.5px; }
    .stMetric label { font-size: 0.78rem !important; }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700;
    }
    div[data-testid="stProgress"] > div { border-radius: 6px; }

    /* ── Light-mode cards ────────────────────────────────────── */
    .strength-box {
        background: #E8F5E9;
        border-left: 3px solid #22C55E;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        color: #1B4332;
    }
    .weakness-box {
        background: #FFEBEE;
        border-left: 3px solid #EF4444;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        color: #4A1420;
    }
    .roadmap-card {
        background: #F5F5F5;
        border: 1px solid #DDD;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        color: #222;
    }

    /* ── Dark-mode overrides ──────────────────────────────────── */
    [data-theme="dark"] .strength-box,
    [data-testid="stAppViewContainer"][class*="dark"] .strength-box {
        background: #12281F; color: #D1FAE5;
    }
    [data-theme="dark"] .weakness-box,
    [data-testid="stAppViewContainer"][class*="dark"] .weakness-box {
        background: #28161B; color: #FEE2E2;
    }
    [data-theme="dark"] .roadmap-card,
    [data-testid="stAppViewContainer"][class*="dark"] .roadmap-card {
        background: #1A1D27; border-color: #2D3148; color: #F0F2F6;
    }

    @media (prefers-color-scheme: dark) {
        .strength-box { background: #12281F; color: #D1FAE5; }
        .weakness-box { background: #28161B; color: #FEE2E2; }
        .roadmap-card { background: #1A1D27; border-color: #2D3148; color: #F0F2F6; }
    }

    /* ── Part status badges ────────────────────────────────────── */
    .part-status {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        margin-left: 6px;
        vertical-align: middle;
    }
    .part-status.ready {
        background: #E3F2FD;
        color: #1565C0;
        border: 1px solid #90CAF9;
    }
    .part-status.done {
        background: #E8F5E9;
        color: #2E7D32;
        border: 1px solid #A5D6A7;
    }
    .part-status.error {
        background: #FFF3E0;
        color: #E65100;
        border: 1px solid #FFCC80;
    }
    [data-theme="dark"] .part-status.ready,
    @media (prefers-color-scheme: dark) { .part-status.ready {
        background: #0D47A1; color: #BBDEFB; border-color: #1565C0;
    }}
    [data-theme="dark"] .part-status.done,
    @media (prefers-color-scheme: dark) { .part-status.done {
        background: #1B5E20; color: #C8E6C9; border-color: #388E3C;
    }}
    [data-theme="dark"] .part-status.error,
    @media (prefers-color-scheme: dark) { .part-status.error {
        background: #BF360C; color: #FFE0B2; border-color: #E65100;
    }}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """HTML-escape user / LLM-provided text to prevent XSS."""
    return _html.escape(str(text))


def _score_colour(val: int) -> str:
    """Return a hex colour based on score: red → amber → green."""
    val = max(0, min(100, int(val)))
    if val >= 70:
        return "#22C55E"
    if val >= 50:
        return "#EAB308"
    return "#EF4444"


def _smart_truncate(text: str, limit: int) -> str:
    """Truncate only when *text* exceeds *limit* chars; add ellipsis at word boundary."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + " …"


def _part_header(part_num: int, title: str, state_key: str) -> None:
    """Render a Part header with a coloured status badge."""
    ran = st.session_state.get(state_key)
    if ran == "done":
        badge = '<span class="part-status done">✓ Complete</span>'
    elif ran == "error":
        badge = '<span class="part-status error">⚠ Error</span>'
    else:
        badge = '<span class="part-status ready">○ Ready</span>'
    st.markdown(
        f'Part {part_num} — {_esc(title)} {badge}',
        unsafe_allow_html=True,
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.title("📝 AI Essay Analyst")
st.caption("Research-grade academic feedback · RAG-assisted · Structured scoring")

with st.expander("ℹ️ How this works", expanded=False):
    st.markdown("""
    1. **Paste or browse your essay** in the left panel and configure your academic context.
    2. The engine retrieves relevant academic references **(RAG)** to ground the analysis.
    3. A structured scorecard, strengths/weaknesses, and a prioritised revision plan are returned.
    4. Re-run after revisions to **track improvement** across the session.
    5. Run **Extended Analysis** (Parts 1–6) for word clouds, grammar checks, sentiment analysis, and more.
    6. **Download your report** as Markdown, PDF, or plain text from the Overview tab.
    """)

st.divider()

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([0.44, 0.56], gap="large")

# ═════════════════════════════════════════════════════════════════════════════
# LEFT — Input & Settings
# ═════════════════════════════════════════════════════════════════════════════
with left:
    st.subheader("1  ·  Essay Input")

    m1, m2 = st.columns(2)
    level = m1.selectbox(
        "Academic level",
        ["Undergraduate", "Masters", "Doctoral / DBA"],
    )
    discipline = m2.selectbox(
        "Discipline",
        [
            "General",
            "Business & Management",
            "Computer Science",
            "Social Sciences",
            "Education",
            "Health Sciences",
            "Other",
        ],
    )

    rubric = st.selectbox(
        "Rubric profile",
        [
            "Critical Essay",
            "Research Paper",
            "Literature Review",
            "Research Proposal",
            "Reflective Account",
            "Case Study Analysis",
        ],
    )

    essay_text = st.text_area(
        "Paste essay text",
        height=300,
        placeholder="Paste your full essay or the section you want analysed…",
    )

    uploaded = st.file_uploader(
        "Or upload a plain-text file (.txt / .md) or a PDF",
        type=["txt", "md", "pdf"],
    )
    max_bytes = 1_000_000
    if uploaded:
        if uploaded.size > max_bytes:
            st.warning(f"Uploaded file exceeds {max_bytes // 1000} KB limit.")
        elif not essay_text:
            try:
                name = getattr(uploaded, "name", "") or ""
                lower_name = name.lower()
                data = uploaded.read()
                if lower_name.endswith(".pdf") or getattr(uploaded, "type", "") == "application/pdf":
                    try:
                        from analyst.pdf_utils import extract_pdf_text

                        _progress_bar = st.progress(0)

                        def _pdf_progress(page_idx: int, total: int) -> None:
                            _progress_bar.progress(int((page_idx + 1) / total * 100))

                        essay_text = extract_pdf_text(data, progress_callback=_pdf_progress)
                        _progress_bar.empty()
                    except Exception:
                        st.warning(
                            "Could not extract text from PDF. "
                            "Is it a scanned image PDF? OCR is required."
                        )
                        essay_text = ""
                else:
                    essay_text = data.decode("utf-8")
            except UnicodeDecodeError:
                st.warning("Uploaded file is not valid UTF-8 text.")
                essay_text = ""

    from analyst.input_validation import validate_essay, count_words

    word_count = count_words(essay_text)
    msg = ""
    if essay_text:
        ok, msg = validate_essay(essay_text)
    st.caption(f"Word count: **{word_count}** · Minimum required: 150 words")

    if msg:
        st.warning(msg)

    st.divider()
    st.subheader("2  ·  Analysis Settings")

    use_rag = st.toggle("Enable RAG (reference corpus retrieval)", value=True)
    max_refs = 7
    if use_rag:
        max_refs = st.slider("Max references to retrieve", 3, 15, 7)
        st.caption(
            "References are drawn from the indexed academic corpus in `/data/corpus/`."
        )

    ready = word_count >= 150 and not msg
    if not ready and not msg:
        st.warning("Please enter at least 150 words to enable analysis.")

    run = st.button(
        "▶  Run analysis",
        type="primary",
        disabled=not ready,
        use_container_width=True,
    )

# ═════════════════════════════════════════════════════════════════════════════
# RIGHT — Results
# ═════════════════════════════════════════════════════════════════════════════
with right:
    st.subheader("3  ·  Analysis Results")

    tabs = st.tabs(
        [
            "📊 Overview",
            "📋 Detailed Feedback",
            "🔍 Sources & RAG",
            "🕑 Session History",
            "🔎 Extended Analysis",
        ]
    )

    # ── Blank state — helpful guidance in every tab ───────────────────────────
    if "result" not in st.session_state and not run:
        with tabs[0]:
            st.info(
                "No analysis yet. Complete the essay input on the left "
                "and click **Run analysis**."
            )
        with tabs[1]:
            st.info(
                "Per-dimension strengths, weaknesses, and actions will appear here "
                "after you run an analysis."
            )
        with tabs[2]:
            st.info(
                "Retrieved RAG references will be listed here once you run an "
                "analysis with RAG enabled."
            )
        with tabs[3]:
            st.info(
                "Your session run history and score trends will appear here after "
                "one or more analysis runs."
            )
        with tabs[4]:
            st.info(
                "Extended analyses (word clouds, grammar checks, sentiment, etc.) "
                "will be available here after your essay text is loaded."
            )

    # ── Run analysis (with error handling) ────────────────────────────────────
    if run and ready:
        try:
            with st.spinner("Analysing essay… retrieving references and scoring…"):
                result = analyse_essay(
                    essay_text, level, discipline, rubric, use_rag, max_refs
                )
                st.session_state["result"] = result

                if "history" not in st.session_state:
                    st.session_state["history"] = []
                st.session_state["history"].append(
                    {
                        "Run #": len(st.session_state["history"]) + 1,
                        "Overall": result["scores"]["overall"],
                        "Band": result["band"],
                        "Level": level,
                        "Rubric": rubric,
                    }
                )
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")

    # ═════════════════════════════════════════════════════════════════════════
    # Display results (only when a result exists)
    # ═════════════════════════════════════════════════════════════════════════
    if "result" in st.session_state:
        r = st.session_state["result"]
        sc = r["scores"]

        # ── TAB 0: OVERVIEW ──────────────────────────────────────────────────
        with tabs[0]:
            st.markdown("##### 📊 Scorecard")
            c0, c1, c2, c3, c4 = st.columns(5)

            def _score_col(col, label, val):
                """Render a colour-coded metric + progress bar."""
                v = max(0, min(100, int(val)))
                col.metric(label, f"{v}/100")
                col.progress(v / 100)
                col.markdown(
                    f'<span style="color:{_score_colour(v)};font-size:1.4rem;">●</span>',
                    unsafe_allow_html=True,
                )

            _score_col(c0, "🎯 Overall", sc["overall"])
            _score_col(c1, "🏗️ Structure", sc["structure"])
            _score_col(c2, "💡 Argument", sc["argument_depth"])
            _score_col(c3, "📚 Evidence", sc["evidence_use"])
            _score_col(c4, "🔗 Coherence", sc["coherence"])

            band_icon = {
                "Distinction": "🟢",
                "Merit": "🔵",
                "Pass": "🟡",
                "Developing": "🔴",
            }.get(r["band"], "⚪")
            st.markdown(f"**Grade band:** {band_icon} {_esc(r['band'])}")

            # Radar chart — theme-transparent background
            cats = ["Structure", "Argument", "Evidence", "Coherence"]
            vals = [
                sc["structure"],
                sc["argument_depth"],
                sc["evidence_use"],
                sc["coherence"],
            ]
            r_vals = vals + [vals[0]]
            r_theta = cats + [cats[0]]

            fig = go.Figure(
                go.Scatterpolar(
                    r=r_vals,
                    theta=r_theta,
                    fill="toself",
                    fillcolor="rgba(75, 123, 229, 0.2)",
                    line=dict(color="rgba(75, 123, 229, 0.9)", width=2),
                )
            )
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(size=10),
                    ),
                    bgcolor="rgba(0,0,0,0)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Strengths & Weaknesses (with empty-state, XSS-safe)
            st.markdown("##### 💡 Strengths   &   ⚠️ Weaknesses")
            sw_l, sw_r = st.columns(2)

            with sw_l:
                st.caption("Strengths")
                strengths = r.get("strengths", [])
                if strengths:
                    for s in strengths:
                        st.markdown(
                            f'<div class="strength-box">'
                            f'<strong>{_esc(s["dimension"])}</strong><br>'
                            f'{_esc(s["point"])}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No specific strengths identified.")

            with sw_r:
                st.caption("Weaknesses")
                weaknesses = r.get("weaknesses", [])
                if weaknesses:
                    for w in weaknesses:
                        st.markdown(
                            f'<div class="weakness-box">'
                            f'<strong>{_esc(w["dimension"])}</strong><br>'
                            f'{_esc(w["point"])}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No specific weaknesses identified.")

            st.divider()

            # Revision Roadmap — sorted by priority, XSS-safe
            st.markdown("##### 🛠️ Revision Roadmap")
            roadmap = sorted(
                r.get("revision_roadmap", []),
                key=lambda x: x.get("priority", 99),
            )
            if roadmap:
                for item in roadmap:
                    imp_icon = {
                        "High": "🔴", "Medium": "🟡", "Low": "🟢"
                    }.get(item["impact"], "⚪")
                    eff_icon = {
                        "Quick fix": "⚡", "Moderate": "🔧", "Deep revision": "🏗️"
                    }.get(item["effort"], "")
                    st.markdown(
                        f'<div class="roadmap-card">'
                        f'<strong>#{_esc(str(item["priority"]))} · '
                        f'{_esc(item["dimension"])} — '
                        f'{_esc(item["title"])}</strong><br>'
                        f'{imp_icon} Impact: {_esc(item["impact"])} '
                        f'&nbsp;|&nbsp; '
                        f'{eff_icon} Effort: {_esc(item["effort"])}'
                        f'<br><br>{_esc(item["action"])}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No revision actions suggested.")

            st.divider()

            # Confidence — clamped to [0, 1]
            st.markdown("##### 🔬 Model Confidence")
            conf = max(0.0, min(1.0, float(r.get("confidence", 0.0))))
            cf1, cf2 = st.columns([1, 2])
            with cf1:
                st.metric("Confidence score", f"{int(conf * 100)}%")
                st.progress(conf)
            with cf2:
                st.caption("What affects this score")
                st.markdown(
                    _esc(r.get("confidence_notes", "No notes available."))
                )
                sources = r.get("rag_sources", [])
                if sources:
                    st.caption(
                        f"RAG: {len(sources)} reference(s) retrieved and used."
                    )

            st.divider()

            # ── Download Report (single PDF) ─────────────────────────────
            st.markdown("##### 📥 Download Report")
            report_md = generate_report_markdown(
                result=r,
                essay_text=essay_text,
                level=level,
                discipline=discipline,
                rubric=rubric,
                history=st.session_state.get("history"),
            )
            pdf_data = generate_pdf_bytes(report_md)
            if pdf_data:
                st.download_button(
                    label="📄 Download Summary Report (PDF)",
                    data=pdf_data,
                    file_name="essay_analysis_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.warning("PDF generation unavailable — please install fpdf2.")

        # ── TAB 1: DETAILED FEEDBACK (fuzzy dimension matching) ──────────────
        with tabs[1]:
            st.markdown("##### 📋 Per-Dimension Detail")

            _DIM_ALIASES = {
                "structure": [
                    "structure", "organisation", "organization", "layout",
                ],
                "argument_depth": [
                    "argument", "argument depth", "argumentation",
                    "critical thinking", "analysis",
                ],
                "evidence_use": [
                    "evidence", "evidence use", "sources",
                    "citations", "referencing",
                ],
                "coherence": [
                    "coherence", "flow", "clarity",
                    "transitions", "expression",
                ],
            }

            def _matches_dimension(item_dim: str, aliases: list) -> bool:
                d = item_dim.lower().strip()
                return any(alias in d or d in alias for alias in aliases)

            dim_display = {
                "structure": "Structure",
                "argument_depth": "Argument Depth",
                "evidence_use": "Evidence Use",
                "coherence": "Coherence",
            }
            for dim_key, dim_label in dim_display.items():
                aliases = _DIM_ALIASES[dim_key]
                with st.expander(f"{dim_label}  —  {sc[dim_key]}/100"):
                    s_list = [
                        s for s in r.get("strengths", [])
                        if _matches_dimension(s["dimension"], aliases)
                    ]
                    w_list = [
                        w for w in r.get("weaknesses", [])
                        if _matches_dimension(w["dimension"], aliases)
                    ]
                    a_list = [
                        a for a in r.get("revision_roadmap", [])
                        if _matches_dimension(a["dimension"], aliases)
                    ]
                    if s_list:
                        st.markdown("**✅ Strengths**")
                        for s in s_list:
                            st.markdown(f"- {_esc(s['point'])}")
                    if w_list:
                        st.markdown("**⚠️ Weaknesses**")
                        for w in w_list:
                            st.markdown(f"- {_esc(w['point'])}")
                    if a_list:
                        st.markdown("**🛠️ Suggested actions**")
                        for a in a_list:
                            st.markdown(f"- {_esc(a['action'])}")
                    if not s_list and not w_list and not a_list:
                        st.caption(
                            "No specific feedback mapped to this dimension."
                        )

        # ── TAB 2: SOURCES & RAG ─────────────────────────────────────────────
        with tabs[2]:
            st.markdown("##### 🔍 Retrieved References")
            rag_sources = r.get("rag_sources", [])
            if rag_sources:
                st.dataframe(
                    pd.DataFrame(rag_sources),
                    use_container_width=True,
                )
            else:
                st.info(
                    "No RAG sources retrieved. "
                    "Enable RAG in Analysis Settings and re-run."
                )

        # ── TAB 3: SESSION HISTORY (with trend chart) ────────────────────────
        with tabs[3]:
            st.markdown("##### 🕑 Session Run History")
            history = st.session_state.get("history", [])
            if history:
                df_hist = pd.DataFrame(history)
                st.dataframe(df_hist, use_container_width=True)

                if len(history) >= 2:
                    st.markdown("##### 📈 Score Trend")
                    fig_trend = go.Figure()
                    fig_trend.add_trace(
                        go.Scatter(
                            x=df_hist["Run #"],
                            y=df_hist["Overall"],
                            mode="lines+markers",
                            name="Overall Score",
                            line=dict(color="#4B7BE5", width=2),
                            marker=dict(size=8),
                        )
                    )
                    fig_trend.update_layout(
                        xaxis_title="Run",
                        yaxis_title="Overall Score",
                        yaxis=dict(range=[0, 100]),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=280,
                        margin=dict(t=10, b=30, l=40, r=10),
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info(
                    "No history yet. Run at least one analysis to start tracking."
                )

        # ── TAB 4: EXTENDED ANALYSIS ─────────────────────────────────────────
        with tabs[4]:
            st.markdown("##### 🔎 Extended Analysis")
            st.caption(
                "Each section below runs independently — expand the one you "
                "need and click its **Run** button."
            )

            # ──────────────────────────────────────────────────────────────────
            # Part 1 — Live LLM-prompted Feedback
            # ──────────────────────────────────────────────────────────────────
            with st.expander("Part 1 — LLM-prompted Feedback", expanded=st.session_state.get("p1_state") == "done"):
                _part_header(1, "LLM-prompted Feedback", "p1_state")
                st.caption(
                    "Uses the configured LLM (GPT-4o-mini) to generate "
                    "structured academic feedback on your essay covering: "
                    "Communication & Structure, Subject Knowledge & Sources, "
                    "Critical Analysis, and Conclusion."
                )
                st.info(
                    "**Disclaimer on Generative AI Output** — This content is "
                    "generated by AI. GenAI systems may produce errors, "
                    "omissions, or hallucinations. Critically evaluate all "
                    "output and consult authoritative sources."
                )

                _p1_label = "✓ Re-run LLM Feedback" if st.session_state.get("p1_state") == "done" else "▶ Run LLM Feedback"
                if st.button(_p1_label, key="btn_part1", type="primary" if st.session_state.get("p1_state") != "done" else "secondary"):
                    if not essay_text:
                        st.warning("Please paste or upload an essay first.")
                    else:
                        try:
                            with st.spinner("Generating LLM feedback…"):
                                fb = reflective_llm_feedback(essay_text)
                                st.session_state["p1_result"] = fb
                                st.session_state["p1_state"] = "done"
                                st.rerun()
                        except RuntimeError as exc:
                            st.session_state["p1_state"] = "error"
                            st.error(str(exc))
                        except Exception as exc:
                            st.session_state["p1_state"] = "error"
                            st.warning(f"LLM feedback failed: {exc}")

                if st.session_state.get("p1_state") == "done" and st.session_state.get("p1_result"):
                    st.markdown("##### LLM Analysis")
                    st.markdown(st.session_state["p1_result"])

            # ──────────────────────────────────────────────────────────────────
            # Part 2 — Content Visualisation
            # ──────────────────────────────────────────────────────────────────
            with st.expander("Part 2 — Content Visualisation", expanded=st.session_state.get("p2_state") == "done"):
                _part_header(2, "Content Visualisation", "p2_state")
                st.caption(
                    "Word cloud of most-used terms (stop words removed) and "
                    "a knowledge graph showing subject–verb–object relations."
                )

                _p2_label = "✓ Re-run Content Visualisation" if st.session_state.get("p2_state") == "done" else "▶ Run Content Visualisation"
                if st.button(_p2_label, key="btn_part2", type="primary" if st.session_state.get("p2_state") != "done" else "secondary"):
                    st.session_state["p2_state"] = "done"
                    st.session_state["part2_ran"] = True

                if st.session_state.get("part2_ran") and essay_text:
                    # Word cloud
                    st.markdown("##### Word Cloud")
                    try:
                        fig_wc = generate_wordcloud(essay_text)
                        st.pyplot(fig_wc)
                    except Exception as exc:
                        st.warning(f"Could not generate word cloud: {exc}")

                    st.divider()

                    # Knowledge graph
                    st.markdown("##### Knowledge Graph")
                    try:
                        G = build_knowledge_graph(essay_text)
                        html_file = render_graph(G)
                        import streamlit.components.v1 as components

                        with open(html_file, "r", encoding="utf-8") as f:
                            graph_html = f.read()

                        if st.checkbox(
                            "Show interactive graph (embeds HTML/JS)",
                            key="kg_checkbox",
                        ):
                            components.html(graph_html, height=700)
                        else:
                            st.info(
                                "Enable the checkbox above to view the "
                                "interactive knowledge graph."
                            )
                    except RuntimeError as exc:
                        st.warning(str(exc))
                    except Exception as exc:
                        st.warning(
                            f"Could not build knowledge graph: {exc}"
                        )
                elif st.session_state.get("part2_ran") and not essay_text:
                    st.warning("Please paste or upload an essay first.")

            # ──────────────────────────────────────────────────────────────────
            # Part 3 — Language & Structure
            # ──────────────────────────────────────────────────────────────────
            with st.expander("Part 3 — Language & Structure", expanded=st.session_state.get("p3_state") == "done"):
                _part_header(3, "Language & Structure", "p3_state")
                st.caption(
                    "Vocabulary distribution, Flesch readability score, and "
                    "argumentative-zoning breakdown."
                )

                _p3_label = "✓ Re-run Language Analysis" if st.session_state.get("p3_state") == "done" else "▶ Run Language Analysis"
                if st.button(_p3_label, key="btn_part3", type="primary" if st.session_state.get("p3_state") != "done" else "secondary"):
                    if not essay_text:
                        st.warning("Please paste or upload an essay first.")
                    else:
                        # Vocabulary
                        st.markdown("##### Vocabulary Usage")
                        try:
                            vocab = vocabulary_analysis(essay_text)
                            df_vocab = pd.DataFrame(
                                {
                                    "Metric": [
                                        "Unique Noun Words (%)",
                                        "Unique Function Words (%)",
                                        "Unique Content Words (%)",
                                        "Unique Transition Words (%)",
                                    ],
                                    "Your submission": [
                                        vocab["unique_noun_pct"],
                                        vocab["unique_function_pct"],
                                        vocab["unique_content_pct"],
                                        vocab["unique_transition_pct"],
                                    ],
                                    "Avg. benchmark": [
                                        41.79, 7.16, 34.89, 14.71,
                                    ],
                                }
                            )
                            st.dataframe(df_vocab, use_container_width=True)
                        except RuntimeError as exc:
                            st.warning(str(exc))

                        st.divider()

                        # Readability
                        st.markdown("##### Readability")
                        try:
                            rs = readability_score(essay_text)
                            st.metric("Flesch Reading Ease", rs)
                            st.caption("Target academic range: **15 – 40**")
                        except Exception as exc:
                            st.warning(f"Readability error: {exc}")

                        st.divider()

                        # Argumentative zoning
                        st.markdown("##### Argumentative Zoning")
                        try:
                            zones = argumentative_zoning(essay_text)
                            fig_z = zoning_chart(zones)
                            st.plotly_chart(fig_z, use_container_width=True)
                        except RuntimeError as exc:
                            st.warning(str(exc))
                        except Exception as exc:
                            st.warning(f"Zoning error: {exc}")
                        st.session_state["p3_state"] = "done"

            # ──────────────────────────────────────────────────────────────────
            # Part 4 — Grammar / Spelling & Sentence Length
            # ──────────────────────────────────────────────────────────────────
            with st.expander("Part 4 — Grammar / Spelling & Sentence Length", expanded=st.session_state.get("p4_state") == "done"):
                _part_header(4, "Grammar & Sentence Metrics", "p4_state")
                st.caption(
                    "LanguageTool grammar & spelling check, plus detection of "
                    "sentences exceeding 64 words."
                )

                _p4_label = "✓ Re-run Grammar Check" if st.session_state.get("p4_state") == "done" else "▶ Run Grammar Check"
                if st.button(_p4_label, key="btn_part4", type="primary" if st.session_state.get("p4_state") != "done" else "secondary"):
                    if not essay_text:
                        st.warning("Please paste or upload an essay first.")
                    else:
                        # Grammar
                        st.markdown("##### Grammar & Spelling Suggestions")
                        try:
                            errors = grammar_suggestions(essay_text)
                        except RuntimeError as exc:
                            st.error(str(exc))
                            errors = []

                        if errors:
                            for e in errors:
                                replacements = (
                                    ", ".join(
                                        f"**{_esc(rp)}**"
                                        for rp in (e.get("replacements") or [])
                                    )
                                    or "_none_"
                                )
                                st.markdown(
                                    f'> "…{_esc(e["text"])}…"\n\n'
                                    f'{_esc(e["message"])}\n\n'
                                    f'Suggested: {replacements}'
                                )
                                st.divider()
                        else:
                            st.success("No grammar issues detected.")

                        st.divider()

                        # Long sentences
                        st.markdown("##### Sentence Length")
                        try:
                            longs = long_sentences(essay_text)
                        except RuntimeError as exc:
                            st.error(str(exc))
                            longs = []

                        if longs:
                            st.warning(
                                "The following sentences exceed **64 words** "
                                "and may be difficult to read."
                            )
                            for s in longs:
                                st.markdown(
                                    f"**({s['length']} words)**\n\n"
                                    f"{_esc(s['sentence'])}"
                                )
                        else:
                            st.success(
                                "No excessively long sentences detected."
                            )
                        st.session_state["p4_state"] = "done"

            # ──────────────────────────────────────────────────────────────────
            # Part 5 — Sentiment & Discourse Analysis
            # ──────────────────────────────────────────────────────────────────
            with st.expander("Part 5 — Sentiment & Discourse Analysis", expanded=st.session_state.get("p5_state") == "done"):
                _part_header(5, "Sentiment & Discourse", "p5_state")
                st.caption(
                    "VADER sentiment scoring per sentence and discourse-"
                    "coherence scoring per paragraph."
                )

                _p5_label = "✓ Re-run Sentiment Analysis" if st.session_state.get("p5_state") == "done" else "▶ Run Sentiment Analysis"
                if st.button(_p5_label, key="btn_part5", type="primary" if st.session_state.get("p5_state") != "done" else "secondary"):
                    if not essay_text:
                        st.warning("Please paste or upload an essay first.")
                    else:
                        # Sentiment
                        st.markdown("##### Most Positive Sentences")
                        try:
                            pos, neg = sentiment_analysis(essay_text)
                            for p in pos:
                                st.markdown(
                                    f'> "{_smart_truncate(_esc(p["sentence"]), 150)}"\n\n'
                                    f'Score: **{p["score"]}**'
                                )

                            st.divider()
                            st.markdown("##### Most Negative Sentences")
                            for n in neg:
                                st.markdown(
                                    f'> "{_smart_truncate(_esc(n["sentence"]), 150)}"\n\n'
                                    f'Score: **{n["score"]}**'
                                )
                        except RuntimeError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            st.warning(f"Sentiment error: {exc}")

                        st.divider()

                        # Discourse
                        st.markdown("##### Discourse Coherence")
                        try:
                            high, low = discourse_analysis(essay_text)

                            st.markdown("###### Highest-scoring paragraphs")
                            for p in high:
                                st.markdown(
                                    f'> "{_smart_truncate(_esc(p["paragraph"]), 180)}"\n\n'
                                    f'Score: **{p["score"]}**'
                                )

                            st.markdown("###### Lowest-scoring paragraphs")
                            for p in low:
                                st.markdown(
                                    f'> "{_smart_truncate(_esc(p["paragraph"]), 180)}"\n\n'
                                    f'Score: **{p["score"]}**'
                                )
                        except Exception as exc:
                            st.warning(f"Discourse error: {exc}")
                        st.session_state["p5_state"] = "done"

            # ──────────────────────────────────────────────────────────────────
            # Part 6 — Reflective Piece Feedback (Driscoll)
            # ──────────────────────────────────────────────────────────────────
            with st.expander("Part 6 — Reflective Piece Feedback (Driscoll)", expanded=st.session_state.get("p6_state") == "done"):
                _part_header(6, "Reflective Piece Feedback", "p6_state")
                st.caption(
                    "Send your reflective writing to the LLM for analysis "
                    "using **Driscoll's model**: What? → So What? → Now What?"
                )
                st.info(
                    "**Disclaimer on Generative AI Output** — Generated by AI. "
                    "May contain errors or hallucinations. Evaluate critically "
                    "and consult authoritative sources."
                )

                _p6_label = "✓ Re-run Reflective Analysis" if st.session_state.get("p6_state") == "done" else "▶ Run Reflective Analysis"
                if st.button(_p6_label, key="btn_part6", type="primary" if st.session_state.get("p6_state") != "done" else "secondary"):
                    if not essay_text:
                        st.warning(
                            "Please paste or upload a reflective piece first."
                        )
                    else:
                        try:
                            with st.spinner("Analysing reflective piece…"):
                                feedback = reflective_llm_feedback(essay_text)
                                st.session_state["p6_result"] = feedback
                                st.session_state["p6_state"] = "done"
                                st.rerun()
                        except RuntimeError as exc:
                            st.session_state["p6_state"] = "error"
                            st.error(str(exc))
                        except Exception as exc:
                            st.session_state["p6_state"] = "error"
                            st.warning(f"Reflective analysis failed: {exc}")

                if st.session_state.get("p6_state") == "done" and st.session_state.get("p6_result"):
                    st.markdown("##### Reflective Analysis")
                    st.markdown(st.session_state["p6_result"])
