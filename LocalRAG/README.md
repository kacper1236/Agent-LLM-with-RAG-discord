# Local RAG with Python and Flask

This application is designed to handle queries using a language model and a vector database. It generates multiple versions of a user query to retrieve relevant documents and provides answers based on the retrieved context.

## Prerequisites

1. **Python 3**: Ensure you have Python 3.x installed. Tested in 3.10+, but I recommend 3.12.X
2. **Ollama**: This app requires Ollama to be installed and running locally. Follow the [Ollama installation guide](https://github.com/ollama/ollama/blob/main/README.md#quickstart) to set it up.
3. **CUDA**: This app require graphic card from NVIDIA. Follow the [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit-archive) to setup CUDA for version 12.8.0

## Setup

1. **Clone the repository**:
```bash
$ git clone https://github.com/your-repo/local-rag.git
$ cd local-rag
```

2. **Create a virtual environment**:
```bash
$ python -m venv venv
$ source venv/bin/activate

# For Windows user
# venv\Scripts\activate
```

3. **Install dependencies**:
```bash
$ pip install -r requirements.txt
```
After install, need to do is write in console command
```bash
$ playwright install
```
It gives a properly giving a pages, where they using JS for viewing. 

4. **Run Ollama**:
Ensure Ollama is installed and running locally. Refer to the [Ollama documentation](https://github.com/ollama/ollama/blob/main/README.md#quickstart) for setup instructions.
- Install llm models
```bash
$ ollama pull llama3.1:latest
```
- Install text embedding model
```bash
$ ollama pull nomic-embed-text
```
- Run Ollama
```bash
$ ollama serve
```

5. **Install apps on Windows**:
You need to install poppler-latest from [Poppler link](https://github.com/oschwartz10612/poppler-windows/releases)
and tesseract from [Tesseract link](https://github.com/UB-Mannheim/tesseract/wiki).

*Follow the instructions because RAG may don't work*

6. **Get Google Search JSON API**
You need to get api key and custom search engine id
Follow the instructions from [here](https://developers.google.com/custom-search/v1/overview)
Add to .env. Example is in .env.sample

## Running the App
```bash
$ python app.py
```

## Conclusion

This app leverages a language model and a vector database to provide enhanced query handling capabilities. Ensure Ollama is running locally and follow the setup instructions to get started.
