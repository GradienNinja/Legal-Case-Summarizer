from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

# Add more keywords as needed
LEGAL_KEYWORDS = ["plaintiff", "defendant", "verdict", "court", "judge", "appeal", "lawsuit", "case"]

def summarize_text(text, sentences_count=5):
    """
    Summarizes the given text into 'sentences_count' sentences.
    """
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return ' '.join([str(sentence) for sentence in summary])

def highlight_keywords(text):
    """
    Highlights legal keywords in the text.
    """
    for kw in LEGAL_KEYWORDS:
        text = text.replace(kw, f"**{kw.upper()}**")
    return text
