import streamlit as st
from transformers import pipeline
from PyPDF2 import PdfReader
import docx
from io import BytesIO
from PIL import Image
import pytesseract

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

def extract_pdf_text(file):
    reader = PdfReader(file)
    pages_text = [page.extract_text() for page in reader.pages if page.extract_text()]
    text = " ".join(pages_text)
    
    # If no text found, try OCR
    if not text.strip():
        st.warning("No text found in PDF, trying OCR...")
        file.seek(0)
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(file.read())
        text = " ".join([pytesseract.image_to_string(img) for img in images])
    return text

def extract_docx_text(file):
    doc = docx.Document(file)
    return " ".join([para.text for para in doc.paragraphs])

def chunk_text(text, max_length=1000):
    """Split text into chunks to fit summarizer token limits."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_length):
        chunks.append(" ".join(words[i:i+max_length]))
    return chunks

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
            text = ""
            if uploaded_file.name.endswith(".txt"):
                text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.name.endswith(".pdf"):
                text = extract_pdf_text(uploaded_file)
            elif uploaded_file.name.endswith(".docx"):
                text = extract_docx_text(uploaded_file)

            if not text.strip():
                st.error("No text could be extracted from this file. It may be empty or unsupported format.")
            else:
                st.subheader("📑 Extracted Text")
                st.text_area("Preview", text[:2000] + ("..." if len(text) > 2000 else ""), height=200)

                # Summarize in chunks
                st.subheader("⚡ Summary")
                try:
                    chunks = chunk_text(text, max_length=1000)
                    summaries = []
                    for chunk in chunks:
                        summary = summarizer(
                            chunk,
                            max_length=150,
                            min_length=40,
                            do_sample=False
                        )
                        summaries.append(summary[0]['summary_text'])
                    final_summary = " ".join(summaries)
                    st.success(final_summary)
                except Exception as e:
                    st.error(f"Error during summarization: {e}")
