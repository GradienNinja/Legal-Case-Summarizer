import streamlit as st
from transformers import pipeline
from PyPDF2 import PdfReader
import docx

# Load summarizer once (cached)
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_summarizer()

st.set_page_config(page_title="Legal Case Summarizer", layout="wide")

st.title("⚖️ Legal Case Summarizer")
st.markdown(
    "This tool provides automated summaries for educational purposes "
    "and does not replace professional legal advice."
)

# Tabs
tabs = st.tabs(["Civil Cases", "Criminal Cases", "Other Cases"])

for tab, case_type in zip(tabs, ["Civil", "Criminal", "Other"]):
    with tab:
        st.header(f"{case_type} Cases Summarizer")
        uploaded_file = st.file_uploader(
            f"Upload your {case_type.lower()} case", type=["txt", "pdf", "docx"], key=case_type
        )
        num_sentences = st.slider(
            "Number of summary sentences", 1, 10, 5, key=f"slider_{case_type}"
        )

        if uploaded_file:
            # Extract text depending on file type
            if uploaded_file.name.endswith(".txt"):
                text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.name.endswith(".pdf"):
                reader = PdfReader(uploaded_file)
                text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif uploaded_file.name.endswith(".docx"):
                doc = docx.Document(uploaded_file)
                text = " ".join([para.text for para in doc.paragraphs])
            else:
                st.error("Unsupported file format.")
                text = ""

            if text:
                st.subheader("📑 Extracted Text")
                st.text_area("Preview", text[:2000] + ("..." if len(text) > 2000 else ""), height=200)

                # Summarize
                st.subheader("⚡ Summary")
                try:
                    summary = summarizer(
                        text,
                        max_length=150,
                        min_length=40,
                        do_sample=False
                    )
                    st.success(summary[0]['summary_text'])
                except Exception as e:
                    st.error(f"Error during summarization: {e}")
