from io import BytesIO, StringIO
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

def extract_text(file_name: str, file_bytes: bytes, file_type: str):
    try:
        logger.info(f"Text Extraction Started | File Name: {file_name} | File Type: {file_type}")
        
        extracted_text = ""
        if file_type == 'application/pdf':
            pdf_reader = PdfReader(BytesIO(file_bytes))
            logger.info(f"Extracting Text From PDF | File Name: {file_name} | No. of Pages: {len(pdf_reader.pages)}")
            extracted_text = '\n'.join([page.extract_text() for page in pdf_reader.pages])
        else:
            with StringIO(file_bytes.decode('utf-8')) as stringio:
                logger.info(f"Extracting Text From Plain File | File Name: {file_name} | Bytes Size: {len(file_bytes)}")
                extracted_text = stringio.read()
        
        if _is_null_empty_or_whitespace(extracted_text):
            raise Exception("No text was extracted from the file")
        
        logger.info(f"Text Extraction Ended | File Name: {file_name} | File Type: {file_type}")
        return extracted_text
    
    except Exception as ex:
        raise Exception(f"Unable to extract text | File name: {file_name} | File Type: {file_type} | Error: {ex}")

def _is_null_empty_or_whitespace(s: str):
    return not s or not s.strip()