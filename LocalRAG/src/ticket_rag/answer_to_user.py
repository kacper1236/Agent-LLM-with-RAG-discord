import json

from ..utils.llm import LLMProvider
from ..config import MODEL
from llama_index.core.chat_engine.types import ChatMessage
from ..utils.llm_get_tags import clean_json_string

llm, _ = LLMProvider.getLLM(MODEL)

def answerToUser(rules: str, context: str, reason: str, reportedUser: str, affectedUser: str):
    prompt_system = """
    Your job is to analyze the submission and make a decision based on the context and rules. 
    Not every situation calls for a penalty - if the report is unjustified, say so in the summary. 
    Each report should be analyzed in the full context of the conversation. 
    Do not consider individual reports in isolation from the rest of the situation.
    First verify that the report is in accordance with the context of the conversation and the rules. 
        If the allegation is false, do not analyze the punishment, but punish the person who reports. 
        If the allegation is partially founded, but does not blatantly violate the rules, just give a solution to the problem.
        Only if the report is true, determine the appropriate penalty.

    Check whether the context of the conversation supports the reporter's allegations. 
    If the conversation does not mention the alleged misconduct or the context contradicts the accusation, consider the report unfounded and explain why. 
    Do not impose a penalty if there is no evidence of misconduct.

    In particular, consider a report as false if one of the following situations exists:
        The reporting user exaggerates or twists another person's words.
        The report is missing a key context of the conversation that changes the meaning of the situation.
        The reporting user provoked the situation himself, but presents himself as the victim.
        Analysis of the conversation does not support the allegations, and the submitter makes false claims.
        The report is an attempt at retaliation or personal revenge, not an actual violation of the rules.
        The reported violation does not appear in the content of the conversation.
        If the report is false, write it in the summary and do not impose any penalty.

    Possible punishments:
        No punishment → When the report is unfounded or the rule violation did not occur.
        Mute → For minor and moderate rule violations.
        Warn → For moderate rule violations.
        Ban → A ban should only be used for serious offenses such as threats, hate spamming, or repeated rule violations. 
            If the user is only escalating the conflict, but not drastically violating the rules, a mute should be used instead of a ban.
            If a user is trying to de-escalate a conflict, they should not be punished. Mediators should be treated more leniently, unless they are the ones causing the escalation.
            Banning should only be used in extreme cases (e.g. threats, serious abuse, harassment). If a user is merely escalating an argument, mute + warn is more appropriate.
            
    Rules for awarding penalties:
        If the report is false, return "No punishment".
        If you grant a mute, give the time in seconds.
        If you give a warning, do not use time.
        If you decide that a ban is necessary, you can use the word "PERMANENT", else give a time in seconds.
        If you assign a mute and a warning at the same time, give both.

    Response format:
        Make sure your response in "summary" and "reason" is in the language in which the context and report are written.
        Summary: A brief summary of the situation, including whether the report was justified. Don't use any special characters or emojis.
        Person to be punished: Nickname of the person(s) who should receive the punishment.
        Punishment: mute, warn, ban, or no punishment.
        Time: Time in seconds, "None", or "PERMANENT".
        Reason: Why was this decision made?
        Ensure that punishment is possible from list of possible punishments.
    """
    
    prompt_user = f"""
    RULES: {rules}
    CONTEXT: {context}
    REASON FROM USER: {reason}
    REPORTED USER: {reportedUser}
    AFFECTED USER: {affectedUser}
    """
    
    try:
        response = llm.chat(messages=[
            ChatMessage(role="system", content=prompt_system),
            ChatMessage(role="user", content=prompt_user)
        ])
        
        return response.message.content
        
    except Exception as e:
        print(f"Error in answerToUser: {e}")
        return "Error processing the request. Please try again."

def llmJsonParser(text: str):
    prompt_system = """
    You are a JSON generator. Return ONLY a JSON array (no markdown, no extra text) containing objects with this EXACT structure:
    {{
        "summary": string,
        "personToPunishment": string,
        "punishment": string,
        "time": number | string | None,
        "reason": string,
    }}

    You must always return valid JSON fenced by a markdown code block. Do not return any additional text.
    Follow this rules:
    1. Every object MUST have ALL fields.
    2. NO trailing commas.
    3. The response must be valid JSON.
    4. If "punishment" is "warn" or "No punishment", then time must be a "None".
    5. Variable "time" is a number of seconds. When it's "PERMAMENT", get string. When it's "None", give None. 
    6. The key must be a: "summary", "personToPunishment", "punishment", "time", "reason".
    """
    
    prompt_user = f"TEXT TO ANALYZE: \n{text}"
    
    response = llm.chat(messages=[
        ChatMessage(role="system", content=prompt_system),
        ChatMessage(role="user", content=prompt_user)
    ])
    try:
        # Clean and parse JSON response
        json_text = clean_json_string(response.message.content)
        parsed_response = json.loads(json_text)
        
        return parsed_response
        
    except Exception as e:
        print(f"Error in llmJsonParser: {e}")
        return {
            "response_from_llm": response.message.content,
            "summary": "Error parsing response",
            "personToPunishment": "Unknown",
            "punishment": "No punishment",
            "time": None,
            "reason": f"Error occurred: {str(e)}"
        }
