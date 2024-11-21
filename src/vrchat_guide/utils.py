import json
import os
from collections import defaultdict

def extract_session_ids(metrics_dir='frontend/logs/metrics'):
    # Dictionary to store user_id -> session_ids mapping
    user_sessions = defaultdict(list)
    
    # Parse each metrics file
    for filename in os.listdir(metrics_dir):
        if filename.startswith('metrics_') and filename.endswith('.json'):
            filepath = os.path.join(metrics_dir, filename)
            with open(filepath, 'r') as f:
                try:
                    data = json.load(f)
                    user_id = data.get('user_id')
                    session_id = data.get('session_id')
                    if user_id and session_id:
                        user_sessions[user_id].append(session_id)
                except json.JSONDecodeError:
                    print(f"Error reading file: {filename}")
                    continue
    
    # Print results in a formatted way
    print("\nUser ID -> Session ID Mappings:")
    print("-" * 50)
    for user_id, sessions in user_sessions.items():
        print(f"\nUser ID: {user_id}")
        for session in sessions:
            print(f"  Session ID: {session}")
    
    return user_sessions

if __name__ == "__main__":
    sessions = extract_session_ids()