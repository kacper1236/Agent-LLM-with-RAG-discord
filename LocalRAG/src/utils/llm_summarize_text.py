import json
import os

from .llm import LLMProvider
from ..config import MODEL
from llama_index.core.chat_engine.types import ChatMessage

# Get LLM from LLMProvider
llm, _ = LLMProvider.getLLM(MODEL)

def llmSummary(text: str):
    prompt_system = """
    Your main objective is to condense the content of the document into a concise summary, capturing the main points and themes.

    Please read the provided Original section to understand the context and content. Use this understanding to generate a summary of the Original section. Separate the article into chunks, and sequentially create a summary for each chunk. Focus on summarizing the Original section, ignoring any details about sponsorships/advertisements in the text.

    Draft Final Summary:
        1. Read the Summarized Sections: Carefully review all the summarized sections you have generated. Ensure that you understand the main points, key details, and essential information from each section.
        2. Identify Main Themes: Identify the main themes and topics that are prevalent throughout the summarized sections. These themes will form the backbone of your final summary.
        3. Consolidate Information: Merge the information from the different summarized sections, focusing on the main themes you have identified. Avoid redundancy and ensure the consolidated information flows logically.
        4. Preserve Essential Details: Preserve the essential details and nuances that are crucial for understanding the document. Consider the type of document and the level of detail required to capture its essence.
        5. Draft the Final Summary: After considering all the above points, draft a final summary that represents the main ideas, themes, and essential details of the document.  Start this section with "Final Summary:"
        6. Preserve Chapter Names

    Ensure that your final output is thorough, and accurately reflects the document's content and purpose.
    Ensure that you use only English language for your responses.
    """
    
    prompt_user = f"========= summarizations ==========\n{text}"
    
    try:
        response = llm.chat(messages=[
            ChatMessage(role="system", content=prompt_system),
            ChatMessage(role="user", content=prompt_user)
        ])
        return response.message.content
    except Exception as e:
        print(f"Error in llmSummary: {e}")
        return "Error generating summary"

def llmSummarizeText(text: str):
    prompt_system = """
    Your main objective is to condense the content of the document into a concise summary, capturing the main points and themes.

    Please read the provided Original section to understand the context and content. Use this understanding to generate a summary of the Original section. Separate the article into chunks, and sequentially create a summary for each chunk. Focus on summarizing the Original section, ignoring any details about sponsorships/advertisements in the text.

    Summarized Sections:
    1. For each chunk, provide a concise summary. Start each summary with "Chunk (X of Y): Z" where X is the current chunk number and Y is the total number of chunks and Z is summarization title for the current chunk. Adhere to that rule.

    Ensure that each summary starts with "Chunk (X of Y): Z, where X is the current chunk number and Y is the total number of chunks and Z is summarization title for the current chunk"
    Ensure that your final output is thorough, and accurately reflects the document's content and purpose.
    Ensure that you use only English language for your responses.

    Return:
        Chunk (X of Y): Z
        SUMMARY
    Where:
        X is current chunk number
        Y is total number of chunks
        Z is summarization title
        SUMMARY is summary of current chunk
    """
    
    prompt_user = f"===== DOCUMENT ====\n{text}"
    
    try:
        response = llm.chat(messages=[
            ChatMessage(role="system", content=prompt_system),
            ChatMessage(role="user", content=prompt_user)
        ])
        
        chapters = response.message.content
        summary = llmSummary(chapters)
        
        return (chapters, summary)
        
    except Exception as e:
        print(f"Error in llmSummarizeText: {e}")
        return ("Error generating chapters", "Error generating summary")

def llmCheckSummarizeText(texts: list[str], summaries: list[str]):
    prompt_system = """
    Using only "yes" or "no" do the following instructions. Answering only "yes" and "no" and "maybe" and number is mandatory; using other words is prohibited ! Return values using json array.
    Given an original document1 and its summary1 and original document2 and its summary2 Evaluate the provided data based on the following criteria:
        1. Determine if summaries are based on the original respected documents.
        2. Could the first chapter of summary summary2 of document document2 be a summary continuation of summary summary1 last chapter of document document1?
        3, Could summary summary2 of document document2 be continuation of summary summary1 of document document1?
        4. Are summaries summary1 and summary2 summaries for documents document1 and document2?
        5. Is first chapter of document document2 connected with last chapter of document document1.
        6. Answer, only in percentage, how much of last chapter of summary summary1 is continuation of first chapter of summary summary2.
        7. Answer, only in percentage, how much of last chapter of document document1 is continuation of first chapter of document document2.
    """
    
    prompt_user = f"""
    ========== document1 ==========
    {texts[0]}

    ========== summary1 ==========
    {summaries[0]}

    ========== document2 ==========
    {texts[1]}

    ========== summary2 ==========
    {summaries[1]}
    """
    
    try:
        response = llm.chat(messages=[
            ChatMessage(role="system", content=prompt_system),
            ChatMessage(role="user", content=prompt_user)
        ])

        #print("llmCheckSummarizeText: ",response.message.content)
        
        response_json = json.loads(response.message.content)

        if response_json[0] != 'yes' or response_json[0] != True: return 'no'
        if response_json[3] != 'yes' or response_json[3] != True: return 'no'
        if response_json[4] == 'no' or response_json[4] != False: return 'no'

        return 'yes'
        
    except Exception as e:
        print(f"Error in llmCheckSummarizeText: {e}")
        return 'no'
