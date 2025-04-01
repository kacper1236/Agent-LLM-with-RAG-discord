import os
import bs4
from datetime import datetime

from llama_index.core import Document
from werkzeug.utils import secure_filename
from langchain_community.document_loaders import TextLoader, UnstructuredPDFLoader, PyPDFLoader, WebBaseLoader, PyMuPDFLoader
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .get_vector_db import get_vector_db
from unstructured.cleaners.core import clean_extra_whitespace

TEMP_FOLDER = os.getenv('TEMP_FOLDER', './_temp')
FILES_FOLDER = os.getenv('TEMP_FOLDER', './_files')

allowedPdfReaders = ['TextLoader', 'UnstructuredFileLoader', 'PyPDFLoader', 'UnstructuredPDFLoader', 'WebBaseLoader', 'PyMuPDFLoader']

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
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4096, chunk_overlap=256)  # maybe that should be also configurable
    chunks = text_splitter.split_documents(data)

    return chunks

def load_and_split_data(file_path, pdfReader):
    loader = None

    if pdfReader == 'PyPDFLoader':
        loader =  PyPDFLoader(
            file_path=file_path,
            show_progress=True,
        )
    elif pdfReader == 'WebBaseLoader':
        loader = WebBaseLoader(
            web_path=file_path,
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
            #         class_=("post-content", "post-title", "post-header")
                ),
                show_progress=True,
            ),
        )
    elif pdfReader == 'UnstructuredFileLoader':
        loader = UnstructuredLoader(
            file_path=file_path,
            mode = "elements",
            unstructured_kwargs=dict(
                show_progress=True,
                use_multithreading=True,
            ),
            strategy = "fast",
            post_processors=[clean_extra_whitespace],
        )
        data = loader.load()
    elif pdfReader == 'TextLoader':
        loader = TextLoader(
            file_path=file_path,
            encoding="utf-8",
        )
    elif pdfReader == 'PyMuPDFLoader':
        loader = PyMuPDFLoader(
            file_path=file_path,
            extract_images=True,
            show_progress=True,
        )
    else:
        loader = UnstructuredPDFLoader(file_path=file_path)

    print("Loading file ... Started")

    data = None
    try:
        if data == None:
            print("Nowa data")
            data = loader.load()
    except Exception as err :
        print(err)
        raise err

    chunks = splitTextAndImages(data, file_path)

    print(14)
    print("Loading file ... Finished")


    print("Loading file ... Splited")

    return chunks

def embed(file, model, pdfReader, namespace, query = None):
    if not (file.filename != '' and file and allowed_file(file.filename)):
        return False

    file_path = save_file(file, model, pdfReader, namespace)
    chunks = load_and_split_data(file_path, pdfReader, query)
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
