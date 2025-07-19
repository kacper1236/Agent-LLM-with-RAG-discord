from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
import requests

from src.config import OPENAI_API_KEY

OpenAIModels: list[str] = []
OllamaModels: list[str] = []
isFilledOllama = False
isFilledOpenAI = False


class LLMProvider:

    def getLLM(model: str):
        """
        Factory function to create an LLM instance based on the provided model name.

        Args:
            model (str): The name of the model to use.

        Returns:
            LLM: An instance of the LLM class corresponding to the specified model.
        """
        if not isFilledOllama:
            LLMProvider.list_ollama_models()

        if not isFilledOpenAI:
            LLMProvider.list_openai_models()

        if model in OllamaModels or (model+':latest') in OllamaModels:
            if "embed" in model:
                return [OllamaEmbeddings(model=model), True]
            else:
                return [Ollama(model=model), True]
        elif model in OpenAIModels:
            if "embed" in model:
                return [OpenAIEmbeddings(model=model), False]
            else:
                return [OpenAI(model=model), False]
        else:
            raise ValueError(f"Model '{model}' is not supported. Available models: {OllamaModels + OpenAIModels}")

    @staticmethod
    def list_ollama_models():
        global OllamaModels
        global isFilledOllama

        try:
            response = requests.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            data = response.json()

            OllamaModels = [model["name"] for model in data.get("models", [])]
        except:
            pass
        isFilledOllama = True

        return OllamaModels

    @staticmethod
    def list_openai_models(api_base="https://api.openai.com/v1"):
        global OpenAIModels
        global isFilledOpenAI

        try:
            response = requests.get(
                f"{api_base}/models",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
            )
            response.raise_for_status()

            OpenAIModels = [model["id"] for model in response.json().get("data", [])]
        except:
            pass
        isFilledOpenAI = True

        return OpenAIModels