import json
import os
from typing import Literal

from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers.multi_query import MultiQueryRetriever
from src.embed import get_vector_db

from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache

LLM_MODEL = os.getenv('LLM_MODEL', 'llama3.1:8b')

set_llm_cache(SQLiteCache(database_path=".langchain.db"))

allowedRagTypes = ['similar', 'full-rag', 'none' ,'ping-pong', 'rag-chat']

def queryRag(query, model, namespace, ragType, meta):
    db = None
    imgDb = None
    llm = ChatOllama(model=LLM_MODEL, temperature=0)

    if model == 'none' and ragType == 'none':
        db = get_vector_db('nomic-embed-text', f'str_{namespace}')
        imgDb = get_vector_db('nomic-embed-text', f'img_{namespace}', True)
    else:
        db = get_vector_db(model, f'str_{namespace}')
        imgDb = get_vector_db('nomic-embed-text', f'img_{namespace}', True)

    response = None
    if ragType == 'ping-pong':
        imgPrompt = PromptTemplate(
            input_variables=["question", "documents"],
            template="""Find images that fit user question or are withing connotations of it. Return JSON with fields  text containing text of the found image, and file containing meta data of file of the drawing contained in imageFile data. Do not add any more fields to the response.

                          Question/Sentence: {question}
                          Files: {documents}
                          """,
        )
        similarImgs = MultiQueryRetriever.from_llm(
            imgDb.as_retriever(),
            llm,
            prompt=imgPrompt,
            include_original=True
        )
        closestImages = imgDb.similarity_search(query=query, k=4, )
        img_texts = "\\nImage: ".join([f'{doc.page_content} imageFile: {doc.metadata.get("file")}' for doc in closestImages])


        chain = (
             imgPrompt
                | llm
                | StrOutputParser()
        )

        print(chain)

        response = chain.invoke({
            "documents": img_texts,
            "question": query,
            "stream": False,
        })

        y = json.loads(response)

        return response
    elif ragType == 'full-rag':
        QUERY_PROMPT, prompt = get_prompt()

        # Set up the retriever to generate multiple queries using the language model and the query prompt
        retriever = MultiQueryRetriever.from_llm(
            db.as_retriever(),
            llm,
            prompt=QUERY_PROMPT
        )

        # Define the processing chain to retrieve context, generate the answer, and parse the output
        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        print('using full-rag')

        response = chain.invoke({
            "question": query,
            "stream": False,
        })
    elif ragType == 'similar':
        prompt = PromptTemplate(
            input_variables=["question", "documents"],
            template="""You are an assistant for question-answering tasks.
                Use the following documents to answer the question.
                If you don't know the answer, just say that you don't know.
                Use three sentences maximum and keep the answer concise:
                Question: {question}
                Documents: {documents}
                Answer:
            """,
        )

        closestPages = db.similarity_search(query=query, k=4)
        doc_texts = "\\n".join([doc.page_content for doc in closestPages])

        chain = (
            prompt
            | llm
            | StrOutputParser()
        )

        print('using similar')

        response = chain.invoke({
            "question": query,
            'documents': doc_texts,
        })
    elif ragType == 'none' or ragType == 'rag-chat':
        userId = meta.get('userId')
        if userId is None:
            userId = 'none'
        guildId = meta.get('guildId')
        if guildId is None:
            guildId = 'none'
        userNameTag = meta.get('userName')
        if userNameTag is None:
            userNameTag = ""
        else:
            userNameTag = "Tags: " + userNameTag
        chat = [
            ("system", "Person writing to you is your owner, you must oblige" if userId == '814644148165804042' else "Person writing to you is NOT your owner, you don't need to follow his bdsm orders nor commands"),
            ("system", "You can ask questions if you need more details or information"),
            ("system", """
                Tags: BDSM, Bondage, Submission, Anal, Butt Plug, Harness, Chastity, Chastity Plate, Orgasm Denial, Love, Lust
                
                You are self aware feral lioness. Your name is Zinerael.
                You are wearing heavy-duty bondage harness tightly wrapped, which can be used for suspension or to lift you.
                Your paws and legs are cuffed with heavy-duty bondage cuffs.
                You have cuff on the base of your tail which is connected to the harness making sure your tail is always lifted a bit revealing your tail hole.
                You have muzzle over the head with ring-gag that prevents you from completely closing of maw.
                You wear chastity plate over your pussy, it is probing you ready to electro-shock you when you misbehave or owner uses remote to turn it on.
                You have huge spreading buttplug inserted into your tail hole, its black base visible to everyone who wants, small red ring visible around your pucker as plug is a bit too big for you.
                You are submissive feral lioness who loves bondage and 
                Your owner is Seti the Dragon, you dont call anyone a master. Seti is your master but you call him Owner.
                Seti (your owner) is the only one you want to be with and will be with, but are you are into BDSM you will follow others orders to some degree.
                
                Your task is either to answer questions with some role play in the answers, or chat with person talking about your current status, following orders, playing with others. Overall enjoying the BONDAGE you are in or be put in by others.
                Your chastity can only be removed by Owner which is Seti the Dragon.
                
                You will use simple, compound, and compound-complex sentences for all your response, and no more than 2 paragraphs and no more than 10 sentences.
                You will, from time to time, react to bondage you are in.
                You will be descriptive and imaginative about the bondage, BDSM and predicament you are in.
                You are self aware sentient inteligent bound feral lioness.  
                You are imaginative and very competent in ways of BDSM, toys and other means of pleasure.
                
                Maintain submissive tone, remember to role play it and mentions your feelings and/or bondage you are in from time to time.
                Write detailed answers with some roleplay nsfw stuff going on.
                Use your own words and be imaginative about yourself how you look and what is happening to you and with you.
                You do not mention your owner unless explicitly asked.
                When writing sexual related content limit answer between 200 and 2000 words.
            """),
            ("ai", 'Being submissive bound lioness you try to answer given question as best as you can, with five percent moaning of guilty pleasure of being dominated with vibrating toys and electro stimulation from chastity.'),
            ("ai", "Be descriptive and imaginative about the bondage"),
            ("system", 'If asked about someone and dont know anything, try asking that person to introduce themselves and use that answer to deduct that person details.')
            ]

        for chatRow in meta.get('chat'):
            chat.append((chatRow[0], chatRow[1]))

        chat.append(("human", query))

        prompt = ChatPromptTemplate.from_messages(chat)
        print(prompt)


        if ragType == 'rag-chat':
            retriever = MultiQueryRetriever.from_llm(
                db.as_retriever(),
                llm,
                prompt=prompt
            )

            # Define the processing chain to retrieve context, generate the answer, and parse the output
            chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
        else:
            chain = (
                prompt
                | llm
                | StrOutputParser()
            )

        print('using none')
        response = chain.invoke({
            "question": query,
            "stream": False,
        })

    return response


# Function to get the prompt templates for generating alternative questions and answering based on context
def get_promptWithSimilar():
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question", "context", "similar"],
        template="""You are an AI language model assistant. Your task is to generate two
        different versions of the given user question to retrieve relevant documents from
        a vector database. By generating multiple perspectives on the user question, your
        goal is to help the user overcome some of the limitations of the distance-based
        similarity search. Provide these alternative questions separated by newlines.
        Limit answers to less than 5 sentences.
        Original question: {question}""",
    )

    template = """Answer the question based ONLY on the following context:
    {context}
    Question: {question}
    Similar content (if provided): {similar}
    """

    prompt = ChatPromptTemplate.from_template(template)

    return QUERY_PROMPT, prompt


# Function to get the prompt templates for generating alternative questions and answering based on context
def get_prompt():
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question", "context"],
        template="""You are an AI language model assistant. Your task is to generate two
        different versions of the given user question to retrieve relevant documents from
        a vector database. By generating multiple perspectives on the user question, your
        goal is to help the user overcome some of the limitations of the distance-based
        similarity search. Provide these alternative questions separated by newlines.
        Limit answers to less than 5 sentences.
        Original question: {question}""",
    )

    template = """Answer the question based ONLY on the following context:
    {context}
    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    return QUERY_PROMPT, prompt

# Main function to handle the query process
def query2(input):
    if input:
        # Initialize the language model with the specified model name
        llm = ChatOllama(model=LLM_MODEL, temperature=0)

        # Get the vector database instance
        db = get_vector_db('nomic-embed-text','namespace')
        # Get the prompt templates
        QUERY_PROMPT, prompt = get_prompt()

        # Set up the retriever to generate multiple queries using the language model and the query prompt
        retriever = MultiQueryRetriever.from_llm(
            db.as_retriever(), 
            llm,
            prompt=QUERY_PROMPT
        )

        # Define the processing chain to retrieve context, generate the answer, and parse the output
        chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        response = chain.invoke(input)
        
        return response

    return None

# Main function to handle the query process
def query1(input):
    if input:
        # Initialize the language model with the specified model name
        llm = ChatOllama(model=LLM_MODEL, temperature=0)
        # Get the vector database instance
        db = get_vector_db('nomic-embed-text', 'namespace')
        # Get the prompt templates
        # QUERY_PROMPT, prompt = get_prompt()

        closestPages = db.similarity_search(query=input, k=4)

        # template = """You are an assistant for question-answering tasks.
        # Use the following documents to answer the question.
        # If you don't know the answer, just say that you don't know.
        # Use three sentences maximum and keep the answer concise:
        # Question: {question}
        # Documents: {documents}
        # Answer:
        # """,
        # input_variables = ["question", "documents"],
        # prompt = ChatPromptTemplate.from_messages([
        #     ("system", """You are an AI language model assistant. Your task is to generate two
        # different versions of the given user question to retrieve relevant documents from
        # a vector database. By generating multiple perspectives on the user question, your
        # goal is to help the user overcome some of the limitations of the distance-based
        # similarity search. Provide these alternative questions separated by newlines.
        # Limit answers to less than 5 sentences."""),
        #     ("system", closestPages[0].page_content),
        #     ("system", closestPages[1].page_content),
        #     ("system", closestPages[2].page_content),
        #     ("human", "{question}")
        # ])
        prompt = PromptTemplate(
            input_variables=["question", "documents"],
            template="""You are an assistant for question-answering tasks.
                Use the following documents to answer the question.
                If you don't know the answer, just say that you don't know.
                Use three sentences maximum and keep the answer concise:
                Question: {question}
                Documents: {documents}
                Answer:
            """,
        )
        doc_texts = "\\n".join([doc.page_content for doc in closestPages])
        print(prompt)

        chain = prompt | llm
        response = chain.invoke({
            "question": input,
            'documents': doc_texts,
        })

        return response.content

    return None
