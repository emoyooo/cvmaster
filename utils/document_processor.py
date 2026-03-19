import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_file):
    """Извлекает текст из загруженного PDF-файла"""
    text = ""
    try:
        # Читаем байты из загруженного файла Streamlit
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None