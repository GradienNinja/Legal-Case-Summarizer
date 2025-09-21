from flask import Flask, request, jsonify, render_template
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import nltk
import pdfplumber

nltk.download('punkt')

app = Flask(__name__)

# ---------------- Models ----------------
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Optional premium tokens
VALID_TOKENS = ["TEST123", "EARLYBIRD"]

# ---------------- Helper Functions ----------------
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        return ""
    return text

def simple_issue_extractor(text, top_n=5):
    keywords = ['issue','held','holding','reason','liable','breach','negligence',
                'constitutional','appeal','convicted','sentence','dismissed',
                'contract','tort']
    sents = nltk.tokenize.sent_tokenize(text)
    scored = [(sum(k.lower() in s.lower() for k in keywords), s) 
              for s in sents if any(k.lower() in s.lower() for k in keywords)]
    scored.sort(reverse=True)
    issues = [s for sc,s in scored[:top_n]] or sents[:3]
    return issues

def summarize_case(text, max_len=180, min_len=40):
    text = text.strip()
    if len(text) < 50:
        return text
    paras = [p for p in text.split('\n') if p.strip()]
    chunks, current = [], ""
    for p in paras:
        if len(current)+len(p)<1000:
            current += p+"\n"
        else:
            chunks.append(current)
            current = p+"\n"
    if current: chunks.append(current)
    summaries=[]
    for c in chunks:
        try:
            s = summarizer(c,max_length=120,min_length=30,do_sample=False)[0]['summary_text']
        except:
            s = " ".join(nltk.tokenize.sent_tokenize(c)[:2])
        summaries.append(s)
    joined = " ".join(summaries)
    try:
        final = summarizer(joined,max_length=max_len,min_length=min_len,do_sample=False)[0]['summary_text']
    except:
        final = joined[:max_len*2]
    return final

def answer_question_from_text(text, question, top_k=3):
    sents = nltk.tokenize.sent_tokenize(text)
    if not sents: return "No text to search."
    sent_embeddings = embedder.encode(sents, convert_to_tensor=True)
    q_emb = embedder.encode(question, convert_to_tensor=True)
    hits = util.semantic_search(q_emb, sent_embeddings, top_k=top_k)[0]
    answers = [sents[h['corpus_id']] for h in hits]
    return "\n\n".join(answers)

# ---------------- Routes ----------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    text = request.form.get('case_text', '').strip()
    question = request.form.get('question', '').strip()
    token_input = request.form.get('token', '').strip()

    # Check file upload
    if 'case_file' in request.files and request.files['case_file'].filename != '':
        f = request.files['case_file']
        temp_path = f"/tmp/{f.filename}"
        f.save(temp_path)
        text_from_pdf = extract_text_from_pdf(temp_path)
        if text_from_pdf:
            text = text_from_pdf

    if not text:
        return jsonify({"summary": "⚠️ No text found.", "issues": "", "answer": ""})

    # Limit summary length for free users
    summary_length = 180
    if token_input in VALID_TOKENS:
        summary_length = 400

    summary = summarize_case(text, max_len=summary_length)
    issues = simple_issue_extractor(text)
    issues_text = "\n".join(f"• {i.strip()}" for i in issues)
    answer = answer_question_from_text(text, question) if question else ""

    return jsonify({"summary": summary, "issues": issues_text, "answer": answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
