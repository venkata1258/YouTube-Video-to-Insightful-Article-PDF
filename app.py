import streamlit as st
from transcript import get_transcript
from article_generator import generate_article
from pdf_generator import generate_pdf

st.set_page_config(page_title="YouTube → Article Generator", layout="centered")

st.title("🎥 YouTube to Article & PDF Generator")

url = st.text_input("Enter YouTube Video URL")

if st.button("Generate"):

    if not url:
        st.warning("Please enter a YouTube URL")
    else:
        with st.spinner("Fetching transcript..."):

            transcript, title = get_transcript(url)

            if not transcript:
                st.error(title)
            else:
                st.success("Transcript fetched successfully ✅")

                with st.spinner("Generating article..."):
                    article = generate_article(transcript)

                st.subheader("📄 Generated Article")
                st.write(article)

                with st.spinner("Creating PDF..."):
                    pdf_file = generate_pdf(article, title)

                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF",
                        data=f,
                        file_name="youtube_article.pdf",
                        mime="application/pdf"
                    )