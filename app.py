import io
import re
from collections import Counter

import pandas as pd
import spacy
import streamlit as st
from spacy import displacy

st.set_page_config(
    page_title="NEXUS NER | Text Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { color-scheme: dark; }
.stApp {
  background:
    radial-gradient(ellipse at 12% 5%, rgba(62, 95, 190, .24), transparent 36%),
    radial-gradient(ellipse at 88% 16%, rgba(157, 75, 210, .20), transparent 34%),
    linear-gradient(135deg, #080d1b 0%, #10152a 48%, #0b1020 100%);
  color: #eef2ff;
  font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
[data-testid="stSidebar"] {
  background: rgba(12, 18, 38, .82);
  border-right: 1px solid rgba(160, 174, 255, .14);
}
h1, h2, h3, .hero-title { font-family: 'Space Grotesk', sans-serif !important; }
.hero {
  padding: 28px 30px; border-radius: 24px;
  background: linear-gradient(120deg, rgba(79, 105, 220, .20), rgba(155, 83, 215, .12));
  border: 1px solid rgba(181, 194, 255, .23);
  box-shadow: 0 18px 60px rgba(0,0,0,.18);
  backdrop-filter: blur(18px); margin-bottom: 22px;
}
.hero-kicker { color: #aebcff; font-size: .78rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }
.hero-title { font-size: clamp(2rem, 4vw, 3.2rem); font-weight: 700; line-height: 1.08; margin: 10px 0; color: #f7f8ff; }
.hero-copy { color: #bac4e4; max-width: 780px; font-size: 1rem; }
.glass-card {
  background: rgba(20, 28, 54, .66); border: 1px solid rgba(165, 180, 252, .17);
  border-radius: 18px; padding: 18px 20px; backdrop-filter: blur(14px);
  box-shadow: 0 12px 32px rgba(0,0,0,.12); margin-bottom: 12px;
}
.metric-label { color: #a9b5d7; font-size: .82rem; }
.metric-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.9rem; font-weight: 700; color: #f5f6ff; }
.small-muted { color: #a9b5d7; font-size: .86rem; }
.section-title { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1.25rem; margin: 8px 0 12px; }
.stButton > button, .stDownloadButton > button {
  border-radius: 12px; border: 1px solid rgba(167, 180, 255, .3);
  background: linear-gradient(110deg, #5268e8, #8c52d7); color: white;
  font-weight: 700; min-height: 2.7rem; transition: .2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: #c3cbff; transform: translateY(-1px); color: white;
}
div[data-baseweb="tab-list"] { gap: 8px; }
button[data-baseweb="tab"] {
  background: rgba(28, 37, 68, .7); border-radius: 10px; padding: 10px 16px;
}
textarea, input { border-radius: 12px !important; }
hr { border-color: rgba(165,180,252,.15); }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------- Model ----------
@st.cache_resource(show_spinner="Loading the English NLP model...")
def load_nlp():
    return spacy.load("en_core_web_sm")

def extract_text(uploaded_file):
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()
    if name.endswith(".txt"):
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(raw))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(paragraphs)
    raise ValueError("Unsupported file format. Upload a TXT, PDF, or DOCX file.")

def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def html_escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#x27;"))

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🧠 NEXUS NER")
    st.caption("TEXT INTELLIGENCE STUDIO")
    st.markdown("---")
    st.markdown("### Analysis controls")
    show_person = st.checkbox("PERSON — People", value=True)
    show_org = st.checkbox("ORG — Organizations", value=True)
    show_gpe = st.checkbox("GPE — Countries / cities", value=True)
    show_loc = st.checkbox("LOC — Locations", value=True)
    show_date = st.checkbox("DATE — Dates / periods", value=True)
    show_money = st.checkbox("MONEY — Monetary values", value=True)
    show_percent = st.checkbox("PERCENT — Percentages", value=True)
    show_other = st.checkbox("Other entity types", value=True)
    st.markdown("---")
    st.caption("Powered by spaCy · en_core_web_sm")
    st.caption("Runs locally on your computer after setup.")

st.markdown("""
<div class="hero">
  <div class="hero-kicker">NLP WORKBENCH · PROJECT EDITION</div>
  <div class="hero-title">Named Entity Recognition</div>
  <div class="hero-copy">Turn unstructured text into structured knowledge. Extract people, organizations, places, dates and more — then inspect tokens, part-of-speech tags, and entity statistics in one workspace.</div>
</div>
""", unsafe_allow_html=True)

# Model availability check
try:
    nlp = load_nlp()
except OSError:
    st.error("The spaCy English model is not installed yet.")
    st.code("python -m spacy download en_core_web_sm", language="powershell")
    st.info("Run that command in your activated project environment, then restart Streamlit.")
    st.stop()

sample = (
    "Microsoft CEO Satya Nadella visited New Delhi on 15 January 2025. "
    "The company announced an investment of $3 billion in India and expects "
    "the project to create 2,500 jobs. Researchers from Chandigarh University "
    "will collaborate with teams in Bengaluru."
)

left, right = st.columns([1.55, 1], gap="large")
with left:
    st.markdown('<div class="section-title">01 / Input document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload a document (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"])
    if uploaded:
        try:
            default_text = extract_text(uploaded)
            st.success(f"Loaded: {uploaded.name}")
        except Exception as exc:
            st.error(f"Could not read this file: {exc}")
            default_text = sample
    else:
        default_text = sample

    input_text = st.text_area(
        "Paste or edit text",
        value=default_text,
        height=245,
        placeholder="Paste an article, report, email, or paragraph here...",
        help="English text works best with the default spaCy model."
    )
    analyze = st.button("✦ Analyze text", use_container_width=True)

with right:
    st.markdown('<div class="section-title">Quick guide</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card">
      <b>PERSON</b><div class="small-muted">People, including named individuals</div><br>
      <b>ORG</b><div class="small-muted">Companies, institutions, agencies</div><br>
      <b>GPE / LOC</b><div class="small-muted">Countries, cities, geographic places</div><br>
      <b>DATE / TIME</b><div class="small-muted">Dates, periods and times</div><br>
      <b>MONEY / PERCENT</b><div class="small-muted">Financial values and percentages</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="glass-card"><b>What you can explore</b><p class="small-muted">Entity highlighting · Entity counts · Token-level linguistic analysis · CSV export</p></div>', unsafe_allow_html=True)

if "analysis_run" not in st.session_state:
    st.session_state.analysis_run = False
if analyze:
    if not input_text.strip():
        st.warning("Please enter some text or upload a document before analyzing.")
        st.session_state.analysis_run = False
    elif len(input_text) > 1_000_000:
        st.error("This demo is limited to 1,000,000 characters per analysis. Please use a smaller document.")
        st.session_state.analysis_run = False
    else:
        with st.spinner("Analyzing text with spaCy..."):
            st.session_state.doc_text = input_text
            st.session_state.doc = nlp(input_text)
            st.session_state.analysis_run = True

if st.session_state.analysis_run:
    doc = st.session_state.doc
    text_value = st.session_state.doc_text
    all_ents = list(doc.ents)

    allowed = set()
    if show_person: allowed.add("PERSON")
    if show_org: allowed.add("ORG")
    if show_gpe: allowed.add("GPE")
    if show_loc: allowed.add("LOC")
    if show_date: allowed.update(["DATE", "TIME"])
    if show_money: allowed.add("MONEY")
    if show_percent: allowed.add("PERCENT")
    if show_other: allowed.update(["NORP", "FAC", "EVENT", "PRODUCT", "WORK_OF_ART", "LAW", "LANGUAGE", "QUANTITY", "ORDINAL", "CARDINAL"])

    visible_ents = [ent for ent in all_ents if ent.label_ in allowed]
    entity_types = Counter(ent.label_ for ent in visible_ents)
    token_count = sum(1 for t in doc if not t.is_space)
    word_count = sum(1 for t in doc if not t.is_space and t.is_alpha)
    sentence_count = sum(1 for _ in doc.sents)

    st.markdown("---")
    st.markdown('<div class="section-title">02 / Analysis overview</div>', unsafe_allow_html=True)
    metrics = st.columns(4)
    values = [
        ("Entities found", len(visible_ents)),
        ("Tokens", token_count),
        ("Words", word_count),
        ("Sentences", sentence_count),
    ]
    for col, (label, value) in zip(metrics, values):
        with col:
            st.markdown(f'<div class="glass-card"><div class="metric-label">{label}</div><div class="metric-value">{value:,}</div></div>', unsafe_allow_html=True)

    tab_entities, tab_tokens, tab_stats, tab_export = st.tabs([
        "✦ Entity explorer", "⌘ Token & POS analysis", "▥ Statistics", "⇩ Export"
    ])

    with tab_entities:
        st.markdown("### Highlighted text")
        if visible_ents:
            colors = {
                "PERSON": "#8b5cf6", "ORG": "#3b82f6", "GPE": "#14b8a6",
                "LOC": "#0d9488", "DATE": "#f59e0b", "TIME": "#f97316",
                "MONEY": "#ec4899", "PERCENT": "#e879f9", "NORP": "#64748b",
                "FAC": "#6366f1", "EVENT": "#d97706", "PRODUCT": "#0891b2",
                "WORK_OF_ART": "#be185d", "LAW": "#7c3aed", "LANGUAGE": "#475569",
                "QUANTITY": "#0284c7", "ORDINAL": "#9333ea", "CARDINAL": "#64748b"
            }
            html = displacy.render(doc, style="ent", options={"ents": sorted(allowed), "colors": colors})
            st.components.v1.html(
                f"""<div style="font-family:Arial,sans-serif;line-height:2.1;font-size:16px;
                color:#e8edff;background:rgba(15,22,45,.88);padding:20px;border-radius:14px;
                border:1px solid rgba(165,180,252,.18);">{html}</div>
                <style>mark.entity {{ padding:3px 6px;border-radius:5px;line-height:2.1; }}
                .entity .label {{font-size:10px;font-weight:700;margin-left:5px;opacity:.9;}}</style>""",
                height=260, scrolling=True
            )
            rows = [{"Text": e.text, "Label": e.label_, "Start": e.start_char, "End": e.end_char} for e in visible_ents]
            st.markdown("### Extracted entities")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No entities found for the currently selected categories. Try enabling more entity types.")

    with tab_tokens:
        st.markdown("### Token-level linguistic analysis")
        st.caption("POS = part of speech · Lemma = normalized dictionary form · Shape = word pattern")
        token_rows = []
        for i, token in enumerate(doc):
            if token.is_space:
                continue
            token_rows.append({
                "Index": i,
                "Token": token.text,
                "Lemma": token.lemma_,
                "POS": token.pos_,
                "Fine tag": token.tag_,
                "Dependency": token.dep_,
                "Entity label": token.ent_type_ or "—",
                "Stop word": "Yes" if token.is_stop else "No",
                "Alphabetic": "Yes" if token.is_alpha else "No",
            })
        token_df = pd.DataFrame(token_rows)
        pos_filter = st.multiselect("Filter by POS", sorted(token_df["POS"].unique()), default=[])
        if pos_filter:
            token_df = token_df[token_df["POS"].isin(pos_filter)]
        st.dataframe(token_df, use_container_width=True, hide_index=True, height=420)
        st.download_button("Download token analysis CSV", csv_bytes(token_df), "ner_token_analysis.csv", "text/csv")

    with tab_stats:
        st.markdown("### Entity category distribution")
        if entity_types:
            stats_df = pd.DataFrame(
                [{"Entity type": k, "Count": v} for k, v in entity_types.most_common()]
            )
            chart_col, table_col = st.columns([1.1, 1])
            with chart_col:
                st.bar_chart(stats_df.set_index("Entity type"), y="Count")
            with table_col:
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
            st.markdown("### Entity frequency")
            freq = Counter(ent.text for ent in visible_ents)
            freq_df = pd.DataFrame([{"Entity": k, "Occurrences": v} for k, v in freq.most_common()])
            st.dataframe(freq_df, use_container_width=True, hide_index=True)
        else:
            st.info("No entities to summarize for the selected categories.")

        st.markdown("### Document profile")
        profile = pd.DataFrame([
            {"Measure": "Characters", "Value": len(text_value)},
            {"Measure": "Tokens (including punctuation)", "Value": token_count},
            {"Measure": "Alphabetic words", "Value": word_count},
            {"Measure": "Sentences", "Value": sentence_count},
            {"Measure": "Unique entity strings", "Value": len(set(e.text for e in visible_ents))},
        ])
        st.dataframe(profile, use_container_width=True, hide_index=True)

    with tab_export:
        st.markdown("### Download your results")
        ent_df = pd.DataFrame([
            {"Entity": ent.text, "Label": ent.label_, "Description": spacy.explain(ent.label_) or "",
             "Start character": ent.start_char, "End character": ent.end_char}
            for ent in visible_ents
        ], columns=["Entity", "Label", "Description", "Start character", "End character"])
        st.download_button("⇩ Download entities CSV", csv_bytes(ent_df), "ner_entities.csv", "text/csv", use_container_width=True)
        st.download_button("⇩ Download full token analysis CSV", csv_bytes(pd.DataFrame(token_rows)), "ner_tokens.csv", "text/csv", use_container_width=True)
        st.download_button("⇩ Download analysis summary CSV", csv_bytes(pd.DataFrame([
            {"Metric": "Entities found", "Value": len(visible_ents)},
            {"Metric": "Tokens", "Value": token_count},
            {"Metric": "Words", "Value": word_count},
            {"Metric": "Sentences", "Value": sentence_count},
        ])), "ner_summary.csv", "text/csv", use_container_width=True)
        st.caption("CSV exports use UTF-8 with BOM for better compatibility with Excel.")

st.markdown("---")
st.markdown('<div class="small-muted" style="text-align:center;padding:10px 0 22px">NEXUS NER · Academic NLP Mini Project · Built with Python + spaCy + Streamlit</div>', unsafe_allow_html=True)
