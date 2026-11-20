import pymupdf
from pathlib import Path

def create_demo_pdf():
    txt_path = Path(__file__).parent / "demo_doc.txt"
    pdf_path = Path(__file__).parent / "demo_doc.pdf"
    
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    pages = content.split("--- Page 2 ---")
    page1_text = pages[0].replace("--- Page 1 ---", "").strip()
    page2_text = pages[1].strip() if len(pages) > 1 else ""

    doc = pymupdf.open()

    for p_text in [page1_text, page2_text]:
        page = doc.new_page(width=595, height=842)  # A4 size
        rect = pymupdf.Rect(50, 50, 545, 792)
        page.insert_textbox(rect, p_text, fontsize=10.5, fontname="helv")

    doc.save(str(pdf_path))
    doc.close()
    print(f"Generated demo PDF at {pdf_path}")

if __name__ == "__main__":
    create_demo_pdf()
