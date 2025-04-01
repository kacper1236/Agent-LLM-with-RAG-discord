import os, re
from langchain_community.document_loaders import PlaywrightURLLoader

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')
set_llm_cache(SQLiteCache(database_path='.langchain.db'))
llm = ChatOllama(model = LLM_MODEL, temperature = 0.3, cache = False)

embedding = OllamaEmbeddings(model=LLM_MODEL)
db = Chroma(
        collection_name="llm_discordRules",
        persist_directory=CHROMA_PATH,
        embedding_function=embedding,
)

def getDiscordRules():
    collection = db.get(where = {'type': 'modifiedAt'})
    if collection is not None:
        if collection['metadatas'] == []:
            return ingestDiscordRules()
        elif collection['metadatas'][0]['modifiedAt']:
            return collection['documents'][0]
    return False

def ingestDiscordRules():
    
    urls = ["https://discord.com/guidelines"]

    loader = PlaywrightURLLoader(urls=urls, headless=True, remove_selectors=['.link-terms', '.link-terms > *', '.menu-numbers', '[data-animation="over-right"]', 'div.dropdown-language-name', '#onetrust-policy-text > *', '#onetrust-consent-sdk > *', '#locale-dropdown > *', '#locale-dropdown', '.locale-container', 'iframe', 'script', '* > .language', 'div.language', '.language > *', '.archived-link', '.footer-black > *', '.link-terms', '#localize-widget', '#localize-widget > *'])

    data = loader.load()

    d = data[0].page_content.split('\n\n')

    newModifiedAt = ""

    for i in d:
        if i.startswith("Last Updated:"):
            newModifiedAt = i.replace("Last Updated: ", "")
            break

    collection = db.get(where = {'type': 'modifiedAt'})
    if collection is not None:
        if collection['metadatas'] == []:
            pass
        elif collection['metadatas'][0]['modifiedAt'] == newModifiedAt:
            return collection['documents'][0]
    
    db.reset_collection()

    expPoint = r"\d+\. "
    expNawias = r"(.*)(\([^\)]+\))$"

    points = []
    started = False
    for line in d:
        du = re.match(expPoint, line)
        if line[0] == 'б': break
        if line == 'Follow the Law': continue
        if line == 'Respect Discord': continue
        if line == 'Respect Each Other': continue
        if line.startswith('For more information '): continue
        if du is not None:
            if (started == True):
                ma = re.match(expNawias, points[len(points)-1], re.MULTILINE)
                if ma is not None:
                    points[len(points)-1] = points[len(points)-1].replace(ma.group(2), '')
                points[len(points)-1] = points[len(points)-1].strip()

            started = True
            points.append(line + '\n')
        else:
            if started == True:
                if (line.startswith("If you see any")):
                    ma = re.match(expNawias, points[len(points) - 1], re.MULTILINE)
                    if ma is not None:
                        points[len(points) - 1] = points[len(points) - 1].replace(ma.group(2), '')
                    points[len(points) - 1] = points[len(points) - 1].strip()

                    break
                points[len(points)-1] = points[len(points)-1].strip() + line + '\n'
    i = 0
    for point in points:
        points[i] = point.strip();
        i = i +1

    content = '\n\n'.join(point for point in points)

    db.add_texts([content], [{'type': 'modifiedAt', "modifiedAt": newModifiedAt}])

    return content

def analyzeRules(rules:str):
    rulePrompt = PromptTemplate(
        input_variables = ['rules'],
        template = """
            You are master rules.
            Your job is to understand the rules in order to be a helpful person or group of people.
            Don't add any points to rules. Act only within the given rules.

            Here is your rules:
            {rules}

            Provide a structured understanding of these rules.
        """
    )

    chain = (
        rulePrompt
        | llm
        | StrOutputParser()
    )

    summary = chain.invoke({
        "rules": rules,
    })

    return summary
