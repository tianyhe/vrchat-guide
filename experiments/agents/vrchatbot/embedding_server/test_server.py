import requests
import time

# Server details
embedding_server_url = "http://127.0.0.1:8608"

# Search only events
event_query_response = requests.post("http://localhost:8608/search", json={
    "query": "upcoming music events",
    "content_types": ["event"],
    "top_k": 5
})

# Search across all content
general_query_response = requests.post("http://localhost:8608/search", json={
    "query": "how to join vrchat events",
    "content_types": ["event", "guide", "general_info"],
    "top_k": 5
})

if __name__ == "__main__":
    print("Event query response:")
    print(event_query_response.json())
    print("\nGeneral query response:")
    print(general_query_response.json())