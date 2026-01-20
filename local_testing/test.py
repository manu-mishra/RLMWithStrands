#!/usr/bin/env python3
"""Test RLM experiments locally"""
import requests
import json
import time
import sys

def test_experiment(experiment="s-niah-50k"):
    """Test an experiment and poll for results"""
    url = "http://localhost:8080/invocations"
    
    print(f"🧪 Testing experiment: {experiment}\n")
    
    # Start experiment
    response = requests.post(url, json={"experiment": experiment})
    result = response.json()
    
    print("Response:")
    print(json.dumps(result, indent=2))
    print()
    
    # Check if async
    if "task_id" in result:
        task_id = result["task_id"]
        session_id = result.get("session_id")
        
        print(f"⏳ Async task started (task_id: {task_id})")
        print("Polling for results...\n")
        
        for i in range(1, 31):
            time.sleep(10)
            
            status_response = requests.post(
                url,
                json={"experiment": experiment, "check_status": True}
            )
            status = status_response.json()
            state = status.get("status")
            
            print(f"  [{i}] Status: {state}")
            
            if state in ["completed", "failed"]:
                print("\nFinal result:")
                print(json.dumps(status, indent=2))
                break

if __name__ == "__main__":
    experiment = sys.argv[1] if len(sys.argv) > 1 else "s-niah-50k"
    test_experiment(experiment)
