import os
import bs4
from datetime import datetime

from llama_index.core import Document
from werkzeug.utils import secure_filename
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .get_vector_db import get_vector_db

TEMP_FOLDER = os.getenv('TEMP_FOLDER', './_temp')
FILES_FOLDER = os.getenv('TEMP_FOLDER', './_files')

allowedPdfReaders = ['PyPDFLoader']

# Function to check if the uploaded file is allowed (only PDF files)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}
def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg'}
# Function to save the uploaded file to the temporary folder
def save_file(file, model, readerType, namespace):
    # Save the uploaded file with a secure filename and return the file path
    print("Loading file ... " + "__" + model + "__" + readerType + "__" + namespace + "__" + secure_filename(file.filename))
    ct = datetime.now()
    ts = ct.timestamp()
    filename = str(ts) + "__" + model + "__" + readerType + "__" + namespace + "__" + secure_filename(file.filename)
    file_path = os.path.join(TEMP_FOLDER, filename)
    file.save(file_path)

    return file_path

def splitTextAndImages(data:  list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4096, chunk_overlap=256)
    chunks = text_splitter.split_documents(data)
    return chunks

def load_and_split_data(file_path, pdfReader):
    loader = None
    data = None

    if pdfReader == 'PyPDFLoader':
        loader = PyPDFLoader(
            file_path=file_path,
        )

    try:
        if loader is not None:
            print("Loading data with loader:", pdfReader)
            data = loader.load()
            print(f"Loaded {len(data)} documents")
            for i, doc in enumerate(data[:3]):  # Show first 3 docs for debugging
                print(f"Document {i}: {len(doc.page_content)} chars")
        else:
            print(f"No loader found for pdfReader: {pdfReader}")
            return []
    except Exception as err:
        print(f"Error loading data: {err}")
        raise err

    if not data:
        print("No data loaded from file")
        return []

    chunks = splitTextAndImages(data)
    print(f"Split into {len(chunks)} chunks")

    return chunks

def embed(file, model, pdfReader, namespace, query=None):
    if not (file.filename != '' and file and allowed_file(file.filename)):
        return False

    file_path = save_file(file, model, pdfReader, namespace)
    chunks = load_and_split_data(file_path, pdfReader)
    if isinstance(chunks, str):
        return chunks
    if not chunks and chunks != False:
        return False

    if chunks != False:
        db = get_vector_db(model, f'str_{namespace}')
        db.add_documents(chunks, metadata={"type": "documents", "file": file})

    print("Loading file ... Chunks Added")
    os.remove(file_path)

    return True
