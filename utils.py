"""
Utility functions for the Travel Guide system
"""

import json
import os
import time
from typing import List, Dict

from groq import Groq
import requests
import os

def call_llm(prompt: str, estimated_tokens: int = 1000) -> str:
    """
    Call LLM using Groq API
    
    Args:
        prompt: The prompt to send to the LLM
        estimated_tokens: Estimated token count (for logging)
        
    Returns:
        The LLM's response as a string
    """
    client = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
    )
    
    # Choose model based on your needs
    # Options: llama-3.3-70b-versatile, llama-3.1-70b-versatile, mixtral-8x7b-32768
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    print(f"[LLM] Calling Groq {model}...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=0.7,
            max_tokens=4096,  # Adjust based on your needs
        )
        
        return chat_completion.choices[0].message.content or ""
        
    except Exception as e:
        error_str = str(e)
        
        # Handle rate limits gracefully
        if "rate_limit" in error_str.lower() or "429" in error_str:
            print(f"[LLM] Rate limit hit. Waiting 60s...")
            time.sleep(60)
            # Retry once
            try:
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    temperature=0.7,
                    max_tokens=4096,
                )
                return chat_completion.choices[0].message.content or ""
            except Exception as retry_error:
                print(f"[LLM ERROR] Retry failed: {retry_error}")
                raise
        
        print(f"[LLM ERROR] {e}")
        raise

# def call_llm(prompt: str) -> str:
#     """
#     Call LLM with the given prompt

#     Args:
#         prompt: The prompt to send to the LLM

#     Returns:
#         The LLM's response as a string
#     """
#     # Using Google Gemini as an example
#     # Users should replace with their preferred LLM
#     from google import genai

#     client = genai.Client(
#         api_key=os.getenv("GEMINI_API_KEY", ""),
#     )
#     model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

#     try:
#         response = client.models.generate_content(model=model, contents=[prompt])
#         return response.text or ""
#     except Exception as e:
#         print(f"Error calling LLM: {e}")
#         raise


# def call_llm(prompt: str) -> str:
#     """
#     Call LLM manually with the given prompt

#     Args:
#         prompt: The prompt to send to the prompt txt and user needs to put the response in response.txt

#     Returns:
#         The LLM's response as a string
#     """
#     # Users should use with their preferred LLM

#     try:
#         with open('prompt.txt', 'w', encoding='utf-8') as f:
#             f.write(prompt)

#         with open('response.txt', 'w', encoding='utf-8') as f:
#             pass

#         input()

#         with open('response.txt', 'r', encoding='utf-8') as f:
#             response = f.read()

#         return response
#     except Exception as e:
#         print(f"Error calling LLM: {e}")
#         raise

def search_web(query: str) -> List[Dict]:
    """
    Search the web for information using Serper.dev API
    
    Args:
        query: The search query
        
    Returns:
        List of search results with title, url, and snippet
    """
    print(f"[WEB SEARCH] Searching for: {query}")
    
    url = "https://google.serper.dev/search"
    
    # ✅ Keep as Python dict, don't use json.dumps()
    payload = {
        "q": query,
        "location": "India",
        "gl": "in",
        "num": 10
    }
    
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }
    
    try:
        # ✅ Use json=payload (requests will handle JSON encoding)
        response = requests.post(url, headers=headers, json=payload, timeout=50)
        response.raise_for_status()
        results = response.json()
        
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            }
            for r in results.get("organic", [])
        ]
        
    except requests.exceptions.HTTPError as e:
        print(f"[SEARCH ERROR] HTTP {e.response.status_code}: {e}")
        # Print response for debugging
        try:
            print(f"[SEARCH ERROR] Response: {e.response.text}")
        except:
            pass
        return []
    except Exception as e:
        print(f"[SEARCH ERROR] {e}")
        return []

def extract_yaml_str(response):
    if "```yaml" in response:
        return response.split("```yaml")[1].split("```")[0].strip()

    return response.strip()

if __name__ == "__main__":
    # Test the utility functions

    # Test LLM call
    print("Testing LLM call...")
    test_prompt = "What are the top 3 attractions in Paris?"
    try:
        resp = call_llm(test_prompt)
        print(f"Response: {resp}")
    except Exception as e:
        print(f"LLM test failed: {e}")

    # Test web search
    print("\nTesting web search...")
    res = search_web("best restaurants in Tokyo")
    print(f"Search results: {res}")
