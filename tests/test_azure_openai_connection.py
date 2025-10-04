#!/usr/bin/env python3
"""
Test script for Azure OpenAI connectivity with hardcoded credentials.
This helps verify the endpoint and API key work before integrating into the main coach.
"""

import os
import json
from openai import AzureOpenAI

# Hardcoded credentials from config
endpoint = "https://iexigtsazurioneyeai.openai.azure.com/"
api_key = ""
deployment = "gpt-5"

print("🔧 Testing Azure OpenAI Connection")
print("=" * 50)
print(f"Endpoint: {endpoint}")
print(f"Deployment: {deployment}")
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print()

# Initialize Azure OpenAI client with API key authentication
try:
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2025-01-01-preview",  # Start with chat completions API
    )
    print("✅ Azure OpenAI client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Test with simple chat completion
chat_prompt = [
    {
        "role": "developer",
        "content": [
            {
                "type": "text",
                "text": "You are an AI assistant that helps people find information."
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text", 
                "text": "hello"
            }
        ]
    },
    {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Hi there! How can I help you today?"
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What can you do?"
            }
        ]
    },
    {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I can help with a lot of everyday and technical tasks. For example:\n- Answer questions and explain concepts clearly\n- Summarize, translate, rewrite, or improve the tone of text\n- Write and edit emails, resumes, essays, blog posts, and reports\n- Brainstorm ideas, outlines, titles, and prompts\n- Math help and step-by-step solutions\n- Programming help (debugging, code snippets, explanations) in Python, JS, SQL, etc.\n- Data and spreadsheets (formulas, cleaning, simple analysis)\n- Planning (trip itineraries, study plans, workouts, meal ideas, checklists)\n- Troubleshoot common tech issues and error messages\n- Analyze images (screenshots, photos, diagrams) to extract info or explain what's shown\n\nNotes:\n- I don't browse the live web; my knowledge is current through Oct 2024.\n- I can give general info, but not professional legal/medical/financial advice.\n\nTell me what you're trying to do (goal, audience, style, length, any constraints), or share text/image, and I'll jump in."
            }
        ]
    }
]

print("🚀 Testing Chat Completions API...")
try:
    completion = client.chat.completions.create(
        model=deployment,
        messages=chat_prompt,
        max_completion_tokens=1000,
        stop=None,
        stream=False
    )
    
    print("✅ Chat Completions API call successful!")
    print("\n📄 Response:")
    print(json.dumps(json.loads(completion.to_json()), indent=2))
    
except Exception as e:
    print(f"❌ Chat Completions API call failed: {e}")
    print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 50)

# Test phonetic coaching specific prompt
print("🎓 Testing Phonetic Coaching Prompt...")
phonetic_messages = [
    {
        "role": "system",  
        "content": "You are a pronunciation coach. Respond with JSON only. Provide phonetic options for words using [ipa:...] and [pron:...] markup tags."
    },
    {
        "role": "user",
        "content": """Generate phonetic coaching for "worcestershire" in JSON format:
{
    "general_text": "explanation",
    "options": [
        {"description": "brief", "phonetic": "[ipa:...]"},
        {"description": "brief", "phonetic": "[pron:...]"}
    ]
}"""
    }
]

try:
    phonetic_completion = client.chat.completions.create(
        model=deployment,
        messages=phonetic_messages,
        max_completion_tokens=4000,  # Much higher limit for GPT-5 reasoning
        temperature=1.0,  # GPT-5 only supports temperature=1.0
        response_format={"type": "json_object"}
    )
    
    print("✅ Phonetic coaching API call successful!")
    print("\n📝 Full Response JSON:")
    print(json.dumps(json.loads(phonetic_completion.to_json()), indent=2))
    
    response_content = phonetic_completion.choices[0].message.content
    print(f"\n📝 Response Content: '{response_content}'")
    print(f"Content length: {len(response_content) if response_content else 'None'}")
    
    # Try to parse JSON
    if response_content:
        try:
            parsed = json.loads(response_content)
            print("\n✅ JSON parsing successful!")
            print(f"General text: {parsed.get('general_text', 'N/A')}")
            print(f"Options count: {len(parsed.get('options', []))}")
            for i, option in enumerate(parsed.get('options', []), 1):
                print(f"  {i}. {option.get('phonetic', 'N/A')} - {option.get('description', 'N/A')}")
        except json.JSONDecodeError as je:
            print(f"❌ JSON parsing failed: {je}")
    else:
        print("❌ No content in response!")
        
except Exception as e:
    print(f"❌ Phonetic coaching API call failed: {e}")
    print(f"   Error type: {type(e).__name__}")

print("\n🏁 Test completed!")