import os
from dotenv import load_dotenv

from src.new_embeddings import doEmbeddings

from src.ticket_rag.analyze_rules import getDiscordRules
from src.ticket_rag.answer_to_user import llmJsonParser, answerToUser
from src.search_from_internet.search import searchToUser

load_dotenv()

from flask import Flask, request, jsonify
from src.embed import allowedPdfReaders, embed
from src.get_vector_db import get_vector_db, allowedModels, embeddingSizes, allowedEmbeddingsModels

import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

import pytesseract
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH', 'C:\\Program Files\\Tesseract-OCR')

ollama_path = None
TEMP_FOLDER = os.getenv('TEMP_FOLDER', './_temp')
os.makedirs(TEMP_FOLDER, exist_ok=True)

app = Flask(__name__)

@app.route('/summarize_and_embed', methods=['GET'])
def get_summarize_and_embed():
    return jsonify({
        'embeddings': allowedEmbeddingsModels,
        'description': 'Endpoint do summaryzacji i embedowania dokumentów do lokalnej bazy danych'
    })

@app.route('/summarize_and_embed', methods=['POST'])
def post_summarize_and_embed():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    data = request.form

    model = data['model']
    if model not in allowedEmbeddingsModels and (model + ':latest') not in allowedEmbeddingsModels:
        return jsonify({"error": "No embedding model", "allowed": allowedEmbeddingsModels}), 400

    pdfReader = data['pdfReader']
    if pdfReader not in allowedPdfReaders:
        return jsonify({"error": "No pdfReader", "allowed": allowedPdfReaders}), 400

    namespace:str = os.getenv('NAMESPACE', 'user_files')

    embedded = doEmbeddings(file, model, pdfReader, namespace)
    #print(embedded)

    if isinstance(embedded, str):
        return jsonify({"error": embedded}), 400
    if embedded:
        return jsonify({"message": "File embedded successfully"}), 200

    return jsonify({"error": f"File embedded unsuccessfully or nothing returned\n Embedded: {embedded}"}), 400

@app.route('/embed', methods=['GET'])
def get__route_embed():
    return jsonify({
        'embeddings': allowedEmbeddingsModels,
        'sizes': embeddingSizes,
    })

@app.route('/embed', methods=['POST'])
def post__route_embed():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    data = request.form

    model = data['model']
    if model not in allowedEmbeddingsModels and (model + ':latest') not in allowedEmbeddingsModels:
        return jsonify({"error": "No embedding model", "allowed": allowedEmbeddingsModels}), 400

    pdfReader = data['pdfReader']
    if pdfReader not in allowedPdfReaders:
        return jsonify({"error": "No pdfReader", "allowed": allowedPdfReaders}), 400

    namespace = data['namespace']
    if namespace == "":
        return jsonify({"error": "No namespace"}), 400

    query = None
    if (pdfReader == 'Image'):
        query = data.get('query')

    print(file, model, pdfReader, namespace)
    embedded = embed(file, model, pdfReader, namespace, query)
    print(embedded)

    if isinstance(embedded, str):
        return jsonify({"error": embedded}), 400
    if embedded:
        return jsonify({"message": "File embedded successfully"}), 200

    return jsonify({"error": "File embedded unsuccessfully"}), 400

@app.route('/chat', methods = ['POST'])
def routeChat():
    try:
        data = request.get_json()
    except:
        data = request.form

    query:str = data['query']
    if query == "":
        return jsonify({'message': 'No query specified'}), 400
    
    max_iterations:int = data['max_iterations'] if data['max_iterations'] is not None else 10

    response = searchToUser(query, max_iterations)

    if response:
        return jsonify({'message': response}), 200
    return jsonify({'message': 'No search from internet'}), 400

@app.route('/report_user', methods = ['POST'])
def routeReportUser():
    try:
        data = request.get_json()
    except:
        data = request.form

    model = data['model']
    if model is None:
        return jsonify({'error': 'No model specified'}), 400
    elif model not in allowedModels:
        return jsonify({'error': f'Model not allowed\n Allowed models: {allowedModels}'}), 400
    
    context:str = data['context']

    if context == "":
        return jsonify({'error': 'No context specified'}), 400
    
    reason:str = data['reason']
    if reason == "":
        return jsonify({'error': 'No reason specified'}), 400

    reportedUser:str = data['reportedUser']
    if reportedUser == "":
        return jsonify({'error': 'No reported user specified'}), 400
    
    affectedUser:str = data['affectedUser']
    if affectedUser == "":
        return jsonify({'error': 'No affected user specified'}), 400
    
    if reportedUser == affectedUser:
        return jsonify({'error': 'Reported user and affected user are the same'}), 400

    discordRules = getDiscordRules()

    answer = answerToUser(discordRules, context, reason, reportedUser, affectedUser)

    jsonAnswer = llmJsonParser(answer)

    if jsonAnswer and jsonAnswer.get("response_from_llm"):
        return jsonify(jsonAnswer.get("response_from_llm"))

    if jsonAnswer:
        return jsonify(jsonAnswer)
    
    return jsonify({'message': 'Something went wrong'}), 400

@app.route('/delete', methods=['DELETE'])
def route_delete():
    db = get_vector_db()
    db.delete_collection()

    return jsonify({"message": "Collection deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)

