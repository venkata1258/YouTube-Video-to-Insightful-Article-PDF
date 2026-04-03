import streamlit as st
import anthropic
import re
import io
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Video to Insightful Article & PDF",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 { font-size: 2.4rem; margin: 0; }
    .main-header p  { font-size: 1.1rem; opacity: 0.9; margin: 0.5rem 0 0; }

    .step-card {
        background: #f8f9ff;
        border-left: 4px solid #667eea;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .metric-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .article-output {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 2rem;
        line-height: 1.8;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .success-banner {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_transcript(video_id: str) -> tuple[str, list]:
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    full_text = " ".join(item["text"] for item in transcript_list)
    return full_text, transcript_list


def generate_article(transcript: str, tone: str, length: str, focus: str) -> str:
    client = anthropic.Anthropic()

    length_map = {"Short (~500 words)": "500", "Medium (~1000 words)": "1000", "Long (~1500 words)": "1500"}
    word_count = length_map.get(length, "1000")

    prompt = f"""You are an expert content writer. Transform the following YouTube video transcript into a well-structured, insightful article.

REQUIREMENTS:
- Tone: {tone}
- Target Length: approximately {word_count} words
- Focus: {focus}
- Structure: Include a compelling title (prefix with "TITLE: "), an introduction, 3-5 main sections with headings (prefix each with "HEADING: "), key insights, and a conclusion
- Make it engaging, informative, and valuable for readers who haven't watched the video
- Extract key insights, quotes, and actionable takeaways
- Use clear, flowing prose — not bullet points

TRANSCRIPT:
{transcript[:8000]}

Write the complete article now:"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def generate_pdf(article_text: str, video_url: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.9 * inch,
        leftMargin=0.9 * inch,
        topMargin=1 * inch,
        bottomMargin=0.9 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ArticleTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#4a3f8c"),
        spaceAfter=14,
        leading=28,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#667eea"),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "ArticleBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=17,
        spaceAfter=10,
        alignment=TA_JUSTIFY,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    story = []

    # Header block
    story.append(Paragraph("Generated Article", title_style))
    story.append(Paragraph(f"Source: {video_url}", meta_style))
    story.append(Paragraph("Generated by YouTube → Article AI", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#667eea"), spaceAfter=14))

    # Parse article text
    lines = article_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        if line.startswith("TITLE:"):
            text = line.replace("TITLE:", "").strip()
            story.append(Paragraph(text, title_style))
        elif line.startswith("HEADING:"):
            text = line.replace("HEADING:", "").strip()
            story.append(Paragraph(text, heading_style))
        elif line.startswith("#"):
            text = line.lstrip("#").strip()
            story.append(Paragraph(text, heading_style))
        else:
            story.append(Paragraph(line, body_style))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 6))
    story.append(Paragraph("AI-generated article • YouTube → Article converter", meta_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Article Settings")
    st.divider()

    tone = st.selectbox(
        "✍️ Writing Tone",
        ["Professional", "Casual & Friendly", "Academic", "Journalistic", "Inspirational"],
    )
    length = st.selectbox(
        "📏 Article Length",
        ["Short (~500 words)", "Medium (~1000 words)", "Long (~1500 words)"],
        index=1,
    )
    focus = st.selectbox(
        "🎯 Content Focus",
        [
            "Key Insights & Takeaways",
            "Step-by-Step Guide",
            "Summary & Overview",
            "Opinion & Analysis",
            "How-To Tutorial",
        ],
    )

    st.divider()
    st.markdown("### 📖 How it works")
    for i, step in enumerate(
        ["Paste a YouTube URL", "Claude extracts the transcript", "AI writes a full article", "Download as PDF"],
        1,
    ):
        st.markdown(f'<div class="step-card">**{i}.** {step}</div>', unsafe_allow_html=True)

    st.divider()
    st.caption("Powered by Claude AI + ReportLab")


# ─── Main UI ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎬 YouTube → Insightful Article</h1>
    <p>Transform any YouTube video into a well-crafted article and download it as PDF</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    video_url = st.text_input(
        "🔗 YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste any YouTube video URL with available captions/transcript",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 Generate Article", type="primary", use_container_width=True)

# ─── Generation Logic ─────────────────────────────────────────────────────────
if generate_btn:
    if not video_url:
        st.warning("⚠️ Please enter a YouTube URL first.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Could not extract video ID. Please check the URL.")
        else:
            # Step 1 – Transcript
            with st.status("📥 Fetching transcript...", expanded=True) as status:
                try:
                    st.write("Connecting to YouTube...")
                    transcript, raw = get_transcript(video_id)
                    word_count_transcript = len(transcript.split())
                    st.write(f"✅ Transcript fetched — {word_count_transcript:,} words")

                    # Step 2 – Article
                    status.update(label="✍️ Generating article with Claude AI...")
                    st.write(f"Writing a **{tone}** article ({length})…")
                    article = generate_article(transcript, tone, length, focus)
                    st.write("✅ Article generated!")

                    # Step 3 – PDF
                    status.update(label="📄 Creating PDF...")
                    st.write("Building formatted PDF…")
                    pdf_bytes = generate_pdf(article, video_url)
                    st.write("✅ PDF ready!")

                    status.update(label="🎉 All done!", state="complete")
                    st.session_state["article"] = article
                    st.session_state["pdf_bytes"] = pdf_bytes
                    st.session_state["video_url"] = video_url
                    st.session_state["transcript_words"] = word_count_transcript

                except Exception as e:
                    status.update(label="❌ Error occurred", state="error")
                    st.error(f"**Error:** {e}")
                    if "transcript" in str(e).lower() or "subtitles" in str(e).lower():
                        st.info("💡 This video may not have captions/subtitles enabled. Try another video.")

# ─── Output Display ───────────────────────────────────────────────────────────
if "article" in st.session_state:
    st.markdown('<div class="success-banner">✅ Article successfully generated!</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Metrics
    article_words = len(st.session_state["article"].split())
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-box"><h3>{st.session_state["transcript_words"]:,}</h3><p>Transcript Words</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><h3>{article_words:,}</h3><p>Article Words</p></div>', unsafe_allow_html=True)
    with m3:
        read_time = max(1, round(article_words / 200))
        st.markdown(f'<div class="metric-box"><h3>~{read_time} min</h3><p>Read Time</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📰 Article Preview", "📋 Raw Text"])

    with tab1:
        # Render article with some formatting
        rendered = st.session_state["article"]
        rendered_html = ""
        for line in rendered.split("\n"):
            line = line.strip()
            if not line:
                rendered_html += "<br>"
            elif line.startswith("TITLE:"):
                rendered_html += f'<h2 style="color:#4a3f8c">{line.replace("TITLE:","").strip()}</h2>'
            elif line.startswith("HEADING:") or line.startswith("##"):
                text = line.replace("HEADING:", "").replace("##", "").strip()
                rendered_html += f'<h3 style="color:#667eea;border-bottom:2px solid #eee;padding-bottom:4px">{text}</h3>'
            elif line.startswith("#"):
                rendered_html += f'<h2 style="color:#4a3f8c">{line.lstrip("#").strip()}</h2>'
            else:
                rendered_html += f'<p style="line-height:1.8;margin:0 0 10px">{line}</p>'

        st.markdown(f'<div class="article-output">{rendered_html}</div>', unsafe_allow_html=True)

    with tab2:
        st.text_area("Raw Article Text", st.session_state["article"], height=400)

    # Download buttons
    st.markdown("<br>", unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)

    with dl1:
        st.download_button(
            label="📄 Download as PDF",
            data=st.session_state["pdf_bytes"],
            file_name="youtube_article.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    with dl2:
        st.download_button(
            label="📝 Download as TXT",
            data=st.session_state["article"].encode("utf-8"),
            file_name="youtube_article.txt",
            mime="text/plain",
            use_container_width=True,
        )
