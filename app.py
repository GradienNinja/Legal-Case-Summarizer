import streamlit as st
from summarize import summarize_text, highlight_keywords
import PyPDF2
import docx
import os

# Page configuration
st.set_page_config(page_title="Legal Case Summarizer", layout="wide", initial_sidebar_state="expanded")

# Sidebar branding & settings
logo_path = "assets/logo.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=150)
else:
    st.sidebar.markdown("### ⚖️ Legal Case Summarizer")

dark_mode = st.sidebar.checkbox("Dark Mode")

# CSS for dark mode
if dark_mode:
    st.markdown("""
        <style>
        .css-1d391kg {background-color: #1E1E1E;}
        .css-18ni7ap {color: #ffffff;}
        </style>
    """, unsafe_allow_html=True)

# Tabs for case types
tabs = st.tabs(["Civil Cases", "Criminal Cases", "Other Cases"])
tab_titles = ["Civil Cases", "Criminal Cases", "Other Cases"]

for i, tab in enumerate(tabs):
    with tab:
        st.subheader(f"📁 {tab_titles[i]} Summarizer")
        uploaded_file = st.file_uploader(
            f"Upload your legal case ({tab_titles[i]})",
            type=["txt", "pdf", "docx"],
            key=i
        )
        sent_count = st.slider(
            "Number of summary sentences",
            min_value=3,
            max_value=15,
            value=5,
            key=f"slider{i}"
        )

        if uploaded_file:
            text = ""
            # PDF support
            if uploaded_file.type == "application/pdf":
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    text += page.extract_text()
            # DOCX support
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            # TXT support
            else:
                text = uploaded_file.read().decode("utf-8")

            # Summarization
            summary = summarize_text(text, sentences_count=sent_count)
            highlighted_summary = highlight_keywords(summary)

            st.subheader("📄 Summary")
            st.markdown(highlighted_summary)

            # Download button
            st.download_button(
                label="Download Summary as TXT",
                data=summary,
                file_name="legal_case_summary.txt",
                mime="text/plain"
            )

# Footer disclaimer
st.markdown("---")
st.write("⚠️ Disclaimer: This tool provides automated summaries for educational purposes and does not replace professional legal advice.")
