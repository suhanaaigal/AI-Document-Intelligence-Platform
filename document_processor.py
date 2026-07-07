from xml.parsers.expat import model
import pytesseract
from PIL import Image
import io
import pytesseract
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

import logging
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, services=None):
        """
        Initialize the DocumentProcessor with optional services (e.g., Vision API).
        
        Args:
            services (dict, optional): Dictionary of initialized services. Defaults to None.
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=1000
        )
        self.services = services

    def extract_text(self, pdf_files):
        """
        Extract text from a list of PDF files.
        
        Args:
            pdf_files (list): List of file paths or file-like objects for PDFs.
        
        Returns:
            str: Concatenated text from all PDFs.
        
        Raises:
            RuntimeError: If PDF extraction fails.
        """
        text = ""
        try:
            for pdf_file in pdf_files:
                pdf_reader = PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Document processing error: {str(e)}")

    def extract_text_from_image(self, image_bytes):
        try:
            image = Image.open(io.BytesIO(image_bytes))

            text = pytesseract.image_to_string(image)

            if text.strip():
                return text

            return "No text found in image."

        except Exception as e:
            return f"OCR processing failed: {str(e)}"
        
    def extract_image_text(self, image_bytes):
        return self.extract_text_from_image(image_bytes)
    # def analyze_image(self, image_bytes, analysis_type="full"):
    #     """
    #     Analyze image content using Google Vision API.
        
    #     Args:
    #         image_bytes (bytes): Binary image data.
    #         analysis_type (str, optional): Type of analysis. Defaults to "full".
        
    #     Returns:
    #         dict: Structured analysis results or error message.
    #     """
    #     try:
    #         if not self.services or 'vision' not in self.services:
    #             raise ValueError("Vision service not initialized")
            
    #         client = self.services['vision']
    #         image = vision.Image(content=image_bytes)
            
    #         features = [
    #             {"type_": vision.Feature.Type.LABEL_DETECTION},
    #             {"type_": vision.Feature.Type.OBJECT_LOCALIZATION},
    #             {"type_": vision.Feature.Type.IMAGE_PROPERTIES},
    #             {"type_": vision.Feature.Type.TEXT_DETECTION}
    #         ]
            
    #         request = vision.AnnotateImageRequest(
    #             image=image,
    #             features=features
    #         )
            
    #         response = client.annotate_image(request)
            
    #         if response.error.message:
    #             error_msg = f"Vision API Error: {response.error.message}"
    #             logger.error(error_msg)
    #             return {"error": error_msg}
                
    #         return self._parse_vision_response(response)
            
    #     except Exception as e:
    #         error_msg = f"Image analysis error: {str(e)}"
    #         logger.error(error_msg, exc_info=True)
    #         return {"error": error_msg}
        
    def analyze_image(self, image_bytes, analysis_type="full"):
        return {
            "text": self.extract_text_from_image(image_bytes)
        }
    def _parse_vision_response(self, response):
        """
        Parse Vision API response into structured data.
        
        Args:
            response: Vision API response object.
        
        Returns:
            dict: Structured analysis results.
        """
        result = {
            "text": "",
            "labels": [],
            "objects": [],
            "properties": {},
            "full_response": MessageToDict(response._pb)
        }
        
        # Extract text
        if response.text_annotations:
            result["text"] = response.text_annotations[0].description
            
        # Extract labels
        if response.label_annotations:
            result["labels"] = [{
                "description": label.description,
                "score": label.score
            } for label in response.label_annotations]
            
        # Extract objects
        if response.localized_object_annotations:
            result["objects"] = [{
                "name": obj.name,
                "score": obj.score,
                "bounding_poly": [(v.x, v.y) for v in obj.bounding_poly.normalized_vertices]
            } for obj in response.localized_object_annotations]
            
        # Extract image properties
        if response.image_properties_annotation:
            result["properties"] = {
                "dominant_colors": [{
                    "color": f"rgb({color.color.red}, {color.color.green}, {color.color.blue})",
                    "score": color.score,
                    "pixel_fraction": color.pixel_fraction
                } for color in response.image_properties_annotation.dominant_colors.colors]
            }
            
        return result

    def create_vector_store(self, text_chunks, embeddings, metadatas=None):
        """
        Create a FAISS vector store from text chunks.
        
        Args:
            text_chunks (list): List of text chunks.
            embeddings: Embedding model for vectorization.
            metadatas (list, optional): Metadata for each text chunk.
        
        Returns:
            FAISS: Vector store instance.
        
        Raises:
            RuntimeError: If vector store creation fails.
        """
        try:
            if metadatas:
                return FAISS.from_texts(text_chunks, embedding=embeddings, metadatas=metadatas)
            return FAISS.from_texts(text_chunks, embedding=embeddings)
        except Exception as e:
            logger.error(f"Vector store creation failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Indexing error: {str(e)}")

    def split_text(self, text):
        """
        Split text into manageable chunks.
        
        Args:
            text (str): Input text.
        
        Returns:
            list: List of text chunks.
        
        Raises:
            RuntimeError: If text splitting fails.
        """
        try:
            return self.text_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Text splitting error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Content processing failed: {str(e)}")




























