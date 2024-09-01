import csv
import json
import time
from typing import List, Dict, Any
import requests
from openai import OpenAI
from tqdm import tqdm
import os
from dotenv import load_dotenv
import time
from collections import deque

load_dotenv()

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Remove old calls
            while self.calls and now - self.calls[0] >= self.period:
                self.calls.popleft()
            
            # If we've reached the maximum number of calls, wait
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Make the call
            result = func(*args, **kwargs)
            self.calls.append(time.time())
            return result
        return wrapper

class OpenAIWrapper:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.total_tokens = 0
        self.rate_limiter = RateLimiter(max_calls=50, period=60)  # 50 calls per 60 seconds

    @RateLimiter(max_calls=50, period=60)
    def generate_content(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=functions,
                tool_choice="auto"
            )
            self.total_tokens += response.usage.total_tokens
            return response.choices[0].message
        except Exception as e:
            print(f"Error in OpenAI API call: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response content: {e.response.content}")
            return None

    def generate_content(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=functions,
                tool_choice="auto"
            )
            self.total_tokens += response.usage.total_tokens
            return response.choices[0].message
        except Exception as e:
            print(f"Error in OpenAI API call: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response content: {e.response.content}")
            return None

def fetch_webpage_content(url: str, max_retries: int = 3) -> str:
    for _ in range(max_retries):
        try:
            response = requests.get(f"https://r.jina.ai/{url}", timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            time.sleep(1)
    return ""

def process_row(row: Dict[str, str], openai_wrapper: OpenAIWrapper) -> Dict[str, str]:
    domain = row['domain']
    content = fetch_webpage_content(domain)
    
    messages = [
        {"role": "system", "content": "You are an AI assistant that analyzes company websites to extract 1) key AI features (be sure they are specifically AI-related) and 2) notable business function specific use cases for the products offered by the company."},
        {"role": "user", "content": f"Analyze the following website content and extract key AI features and notable use cases:\n\n{content}"}
    ]
    
    functions = [
    {
        "type": "function",
        "function": {
            "name": "extract_features_and_use_cases",
            "description": "Extract key AI features and notable use cases from website content",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_ai_features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of key AI features mentioned on the website"
                    },
                    "notable_use_cases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of notable use cases mentioned on the website"
                    }
                },
                "required": ["key_ai_features", "notable_use_cases"],
                "additionalProperties": False  # Add this line
            },
            "strict": True
        }
    }
]
    
    response = openai_wrapper.generate_content(messages, functions)
    
    # Add a small delay after each API call
    time.sleep(0.4)
    
    if response and response.tool_calls:
        extracted_data = json.loads(response.tool_calls[0].function.arguments)
        row['Key AI features'] = '; '.join(extracted_data['key_ai_features'])
        row['Notable use cases'] = '; '.join(extracted_data['notable_use_cases'])
    else:
        row['Key AI features'] = ''
        row['Notable use cases'] = ''
    
    return row

def main(input_file: str, output_file: str, openai_api_key: str):
    openai_wrapper = OpenAIWrapper(openai_api_key)
    
    with open(input_file, 'r', newline='') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['Key AI features', 'Notable use cases']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in tqdm(reader, desc="Processing rows"):
            processed_row = process_row(row, openai_wrapper)
            writer.writerow(processed_row)
    
    print(f"Total tokens used: {openai_wrapper.total_tokens}")
    print(f"Estimated cost: ${openai_wrapper.total_tokens / 1000 * 0.0006:.2f}")  # Assuming $0.0006 per 1K tokens

if __name__ == "__main__":
    main("input.csv", "output.csv", os.getenv("OPENAI_API_KEY"))
