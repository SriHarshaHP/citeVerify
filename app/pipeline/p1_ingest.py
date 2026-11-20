import re
from typing import List, Dict, Any, Tuple
import pymupdf  # PyMuPDF

class IngestResult:
    def __init__(
        self,
        full_text: str,
        pages: List[Dict[str, Any]],  # [{"page": int, "text": str}]
        abstract_text: str,
        body_text: str,
        references_text: str,
        citation_style: str,  # "numeric" or "author-year"
        total_pages: int
    ):
        self.full_text = full_text
        self.pages = pages
        self.abstract_text = abstract_text
        self.body_text = body_text
        self.references_text = references_text
        self.citation_style = citation_style
        self.total_pages = total_pages

def detect_citation_style(body_text: str) -> str:
    """Detects citation style: numeric ([1], [1, 2], [3-5]) vs author-year vs mixed."""
    numeric_count = len(re.findall(r'\[(?:[0-9]+(?:\s*[,-]\s*[0-9]+)*)\]', body_text))
    author_year_count = len(re.findall(r'\([A-Z][a-zA-Z\s]+(?:et al\.?)?,\s*(?:19|20)\d{2}[a-z]?[^()]*\)', body_text)) + len(re.findall(r'\b[A-Z][a-zA-Z\.\-]+\s+(?:et al\.?\s+)?\((?:19|20)\d{2}[a-z]?\)', body_text))

    if numeric_count > 0 and author_year_count > 0:
        return "mixed"
    elif numeric_count > 0:
        return "numeric"
    else:
        return "author-year"

def ingest_document(file_bytes: bytes, filename: str) -> IngestResult:
    """
    Ingests PDF or TXT document, extracts pages, splits abstract/body/references,
    and detects citation style.
    """
    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode("utf-8")

    is_pdf = filename.lower().endswith(".pdf")
    pages: List[Dict[str, Any]] = []

    if is_pdf:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)
        for i, page in enumerate(doc):
            p_text = page.get_text("text")
            pages.append({"page": i + 1, "text": p_text})
        doc.close()
    else:
        text = file_bytes.decode("utf-8", errors="replace")
        # Split txt into approximate pages if markers exist or treat as 1-2 pages
        page_chunks = re.split(r'(?:^|\n)--- Page (\d+) ---\r?\n?', text)
        if len(page_chunks) > 1:
            # Format: [preamble, page_num1, text1, page_num2, text2...]
            for i in range(1, len(page_chunks), 2):
                p_no = int(page_chunks[i])
                p_t = page_chunks[i+1].strip()
                if p_t:
                    pages.append({"page": p_no, "text": p_t})
            total_pages = len(pages)
        else:
            # Single page or synthetic page split by 3500 chars
            lines = text.split("\n")
            chunk_size = 50
            chunks = [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]
            total_pages = len(chunks) or 1
            for i, ch in enumerate(chunks):
                pages.append({"page": i + 1, "text": "\n".join(ch)})

    combined_full_text = "\n\n".join([f"--- Page {p['page']} ---\n{p['text']}" for p in pages])

    # Split References / Bibliography (using the last occurrence)
    ref_match = None
    ref_pattern = re.compile(
        r'\n\s*(?:[0-9]+\.?\s*)?(?:References|Bibliography|Works Cited|Literature Cited):?\s*\n',
        re.IGNORECASE
    )
    matches = list(ref_pattern.finditer(combined_full_text))
    if matches:
        last_match = matches[-1]
        pre_ref_text = combined_full_text[:last_match.start()]
        references_text = combined_full_text[last_match.end():].strip()
    else:
        pre_ref_text = combined_full_text
        references_text = ""

    # Split Abstract and Body
    abstract_pattern = re.compile(r'\bAbstract\b\s*[:\n]?', re.IGNORECASE)
    abs_match = abstract_pattern.search(pre_ref_text)

    if abs_match:
        post_abs = pre_ref_text[abs_match.end():]
        # Look for section 1 or main heading
        sec1_match = re.search(
            r'\n\s*(?:(?:[0-9]+\.?|[I|V|X]+\.?)\s+[A-Z][^\n]+|(?:Introduction|Background|Diagnostic performance|Methods|Methodology)\b)',
            post_abs,
            re.IGNORECASE
        )
        if sec1_match:
            abstract_text = post_abs[:sec1_match.start()].strip()
            body_text = post_abs[sec1_match.start():].strip()
        else:
            # First paragraph after Abstract
            para_break = re.search(r'\n\s*\n', post_abs)
            if para_break and para_break.start() > 20:
                abstract_text = post_abs[:para_break.start()].strip()
                body_text = post_abs[para_break.end():].strip()
            else:
                abstract_text = ""
                body_text = pre_ref_text
    else:
        abstract_text = ""
        body_text = pre_ref_text

    # Detect citation style
    citation_style = detect_citation_style(body_text)

    return IngestResult(
        full_text=combined_full_text,
        pages=pages,
        abstract_text=abstract_text,
        body_text=body_text,
        references_text=references_text,
        citation_style=citation_style,
        total_pages=total_pages
    )
