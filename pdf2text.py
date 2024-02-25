import io
import PyPDF2

def extract_pdf_text(pdf_data):
    """
    Extracts text from a given PDF byte data.

    Parameters:
        pdf_data (bytes): The byte data of the PDF to be read.

    Returns:
        str: The extracted text from the PDF.
    """
    # Initialize a string to hold all extracted text
    extracted_text = ""

    try:
        # Create a BytesIO object from the PDF data
        pdf_buffer = io.BytesIO(pdf_data)

        # Initialize PDF reader
        pdf_reader = PyPDF2.PdfReader(pdf_buffer)

        # Loop through all the pages and extract text
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text()

    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")
        return None

    return extracted_text
