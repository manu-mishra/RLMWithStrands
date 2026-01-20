"""AgentCore client for benchmark invocations"""
import boto3
import json
import time
import requests
from .deploy import load_config

class BenchmarkClient:
    def __init__(self):
        self.config = load_config()
        self.target = self.config.get('target')
        
        if not self.target:
            raise ValueError("No deployment found. Please run Setup & Deploy first.")
        
        if self.target == 'agentcore':
            self.client = boto3.client('bedrock-agentcore', region_name='us-east-1')
            self.runtime_arn = self.config.get('runtime_arn')
        else:
            self.local_endpoint = self.config.get('local_endpoint')
    
    def invoke_experiment(self, experiment_id, model_config, session_id):
        """
        Invoke a benchmark experiment via AgentCore or local Docker (always async).
        
        Args:
            experiment_id: Experiment identifier (e.g., "oolong")
            model_config: Dict with "root" and "sub" model names
            session_id: Session ID for tracking
            
        Returns:
            Dict with experiment results
        """
        payload = {
            "experiment": experiment_id,
            "model_name": model_config["root"],
            "sub_model_name": model_config["sub"],
            "session_id": session_id  # Pass session_id to handler
        }
        
        start_time = time.time()
        
        try:
            # Start the task
            if self.target == 'local':
                response = requests.post(
                    self.local_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                result = response.json()
            else:
                response = self.client.invoke_agent_runtime(
                    agentRuntimeArn=self.runtime_arn,
                    runtimeSessionId=session_id,
                    payload=json.dumps(payload).encode(),
                    qualifier="DEFAULT"
                )
                
                content = []
                for chunk in response.get("response", []):
                    content.append(chunk.decode('utf-8'))
                result = json.loads(''.join(content))
            
            # Poll for completion (always async)
            if result.get("status") == "started":
                print(f"  Task started (ID: {result.get('task_id')}), polling for results...")
                result = self._poll_async_result(experiment_id, session_id, start_time)
            
            # Add elapsed time
            if "elapsed_seconds" not in result:
                result["elapsed_seconds"] = round(time.time() - start_time, 1)
            
            return result
            
        except Exception as e:
            return {
                "experiment": experiment_id,
                "error": str(e),
                "passed": False,
                "elapsed_seconds": round(time.time() - start_time, 1)
            }
    
    def _poll_async_result(self, experiment_id, session_id, start_time, poll_interval=10):
        """Poll for async task completion"""
        status_payload = {
            "experiment": experiment_id,
            "check_status": True,
            "session_id": session_id  # CRITICAL: Must pass session_id to retrieve result
        }
        
        while True:
            time.sleep(poll_interval)
            
            try:
                if self.target == 'local':
                    response = requests.post(
                        self.local_endpoint,
                        json=status_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    result = response.json()
                else:
                    response = self.client.invoke_agent_runtime(
                        agentRuntimeArn=self.runtime_arn,
                        runtimeSessionId=session_id,
                        payload=json.dumps(status_payload).encode(),
                        qualifier="DEFAULT"
                    )
                    
                    content = []
                    for chunk in response.get("response", []):
                        content.append(chunk.decode('utf-8'))
                    result = json.loads(''.join(content))
                
                # Check if completed
                if result.get("status") != "running":
                    result["elapsed_seconds"] = round(time.time() - start_time, 1)
                    return result
                    
                elapsed = round(time.time() - start_time, 1)
                print(f"  Still running... ({elapsed}s elapsed)")
                
            except Exception as e:
                return {
                    "experiment": experiment_id,
                    "error": f"Polling error: {str(e)}",
                    "passed": False,
                    "elapsed_seconds": round(time.time() - start_time, 1)
                }
