import os
import argparse
import random

from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, help='Override for MODEL')
parser.add_argument('--embeddings', type=str, help='Override for EMBEDINGS MODEL')
parser.add_argument('--dir', type=str, help='Override for DIR_ID')
args = parser.parse_args()

OPENAI_API_KEY:str = os.getenv('OPENAI_API_KEY' ,'')
MODEL:str = args.model or os.getenv('model', 'llama3.1')
MODEL_EMBEDDINGS:str = args.embeddings or os.getenv('embeddings', 'nomic-embed-text')
DIR_ID: str = args.dir or os.getenv('DIR_ID', random.random())