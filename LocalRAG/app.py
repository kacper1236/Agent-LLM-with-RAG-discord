import os
from dotenv import load_dotenv

from src.new_embeddings import doEmbeddings

from src.ticketRag.delete_documents import deleteDocuments
from src.ticketRag.analyze_rules import ingestDiscordRules, analyzeRules, getDiscordRules
from src.ticketRag.save_to_database import saveToDatabase
from src.ticketRag.answer_to_user import llmJsonParser, answerToUser
from src.searchFromInternet.search import searchToUser

load_dotenv()

from flask import Flask, request, jsonify
from src.embed import allowedPdfReaders, embed
from unnecessary.query import queryRag, allowedRagTypes, query1, query2
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

@app.route('/embed2', methods=['GET'])
def get__route_embed2():
    return jsonify({
        'embeddings': allowedEmbeddingsModels,
    })

@app.route('/embed2', methods=['POST'])
def post__route_embed2():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    

    data = request.form

    model = data['model']
    if model not in allowedEmbeddingsModels:
        return jsonify({"error": "No embedding model", "allowed": allowedEmbeddingsModels}), 400

    pdfReader = data['pdfReader']
    if pdfReader not in allowedPdfReaders:
        return jsonify({"error": "No pdfReader", "allowed": allowedPdfReaders}), 400


    namespace = data['namespace']
    if namespace == "":
        return jsonify({"error": "No namespace"}), 400


    embedded = doEmbeddings(file, model, pdfReader, namespace)
    print(embedded)

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
    if model not in allowedEmbeddingsModels:
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

@app.route('/query', methods=['POST'])
def routeQuery():
    data = request.get_json()

    model = data['model']

    if model not in allowedEmbeddingsModels:
        if model == 'none' and data['ragType'] == 'none':
            model = "nomic-embed-text"
        else:
            return jsonify({"error": "No embedding model", "allowed": allowedEmbeddingsModels}), 400

    namespace = data['namespace']
    if namespace == "":
        return jsonify({"error": "No namespace"}), 400

    ragType = data['ragType']
    if ragType not in allowedRagTypes:
        return jsonify({"error": "No ragType", "allowed": allowedRagTypes}), 400

    meta = data['meta']

    response = queryRag(data.get('query'), model, namespace, ragType, meta)

    if response:
        return jsonify({"message": response}), 200

    return jsonify({"error": "Something went wrong"}), 400

@app.route('/chat', methods = ['POST'])
def routeChat():
    try:
        data = request.get_json()
    except:
        data = request.form

    query:str = data['query']
    if query == "":
        return jsonify({'message': 'No query specified'}), 400
    
    max_iterations:int = data['max_iterations']

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
    #add serverRules

    answer = answerToUser(discordRules, context, reason, reportedUser, affectedUser)

    jsonAnswer = llmJsonParser(answer)

    if jsonAnswer:
        return jsonify(jsonAnswer)
    
    return jsonify({'message': 'Something went wrong'}), 400

    #need to end

@app.route('/set_server_rules', methods = ['POST'])
def setServerRules():
    data = request.get_json()
    if data.get('serverId') is None:
        return jsonify({'message': 'No server ID provided'}), 400
    if data.get("rules") is None:
        return jsonify({'message': 'No rules provided'}), 400
    if data.get("namespace") is None:
        return jsonify({'message': "No namespace defined"}), 400
    if data.get("document") is None:
        return jsonify({'message': 'No document specified'}), 400

    if deleteDocuments(data.get('document'), data.get('namespace')) is True:
        summary = analyzeRules(data.get('rules'))
        #przewalenie całego regulaminu
        response = saveToDatabase(summary, data.get('namespace'))
        if response:
            return jsonify({"message": "Rules updated successfully"}), 200
        return jsonify({"message": "Rules not updated successfully"}), 400
    else:
       return jsonify({'message': 'Rules doesn\'t exist'}), 400

@app.route('/add_server_rules', methods = ['POST'])
def addServerRules():
    data = request.get_json()
    if data.get('serverId') is None:
        return jsonify({'message': 'No server ID provided'}), 400
    if data.get('rules') is None:
        return jsonify({'message'})
    
    #need to end

@app.route('/query1', methods=['POST'])
def route_query1():
    data = request.get_json()
    response = query1(data.get('query'))

    if response:
        return jsonify({"message": response}), 200

    return jsonify({"error": "Something went wrong"}), 400

@app.route('/query2', methods=['POST'])
def route_query2():
    data = request.get_json()
    response = query2(data.get('query'))

    if response:
        return jsonify({"message": response}), 200

    return jsonify({"error": "Something went wrong"}), 400

@app.route('/delete', methods=['DELETE'])
def route_delete():
    db = get_vector_db()
    db.delete_collection()

    return jsonify({"message": "Collection deleted successfully"}), 200

@app.route('/test', methods = ['POST'])
def test():
    a = ingestDiscordRules()
    return jsonify({'message': a}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)

