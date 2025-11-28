"""
Query the synced resumes
"""
import requests
import json

BASE_URL = "http://localhost:8000"

questions = [
    "What skills does the candidate have?",
    "What is the candidate's experience?",
    "What programming languages does the candidate know?",
    "Summarize the candidate's profile"
]

print("🔍 Querying synced resumes...\n")

for i, question in enumerate(questions, 1):
    print(f"Q{i}: {question}")
    
    response = requests.post(
        f"{BASE_URL}/chat/query",
        json={
            "question": question,
            "thread_id": f"resume_query_{i}"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get("answer", "No answer")
        print(f"A{i}: {answer}\n")
    else:
        print(f"Error: {response.status_code}\n")
