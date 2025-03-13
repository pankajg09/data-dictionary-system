import sys
import os
import requests
import json
import time

def test_api():
    """Test API endpoints for analysis and query execution."""
    base_url = "http://localhost:3001"
    max_retries = 3
    retry_delay = 2  # seconds
    
    def make_request(method, endpoint, **kwargs):
        """Make a request with retries"""
        for attempt in range(max_retries):
            try:
                print(f"\nAttempting {method} request to {endpoint} (attempt {attempt + 1}/{max_retries})")
                response = requests.request(method, f"{base_url}{endpoint}", **kwargs)
                print(f"Response status code: {response.status_code}")
                print(f"Response headers: {response.headers}")
                if response.text:
                    try:
                        print(f"Response body: {json.dumps(response.json(), indent=2)}")
                    except json.JSONDecodeError:
                        print(f"Raw response: {response.text}")
                return response
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise
    
    try:
        # 1. Test root endpoint
        print("\nTesting root endpoint...")
        response = make_request("GET", "/")
        
        # 2. Test code analysis
        print("\nTesting code analysis endpoint...")
        test_code = """
class TestModel:
    def __init__(self):
        self.id = 0
        self.name = "test"
        """
        
        response = make_request(
            "POST",
            "/analyze",
            data={
                "code": test_code,
                "user_id": 1
            }
        )
        
        if response and response.status_code == 200:
            result = response.json()
            analysis_id = result.get('analysis_id')
            print(f"\nAnalysis created successfully with ID: {analysis_id}")
            
            # 3. Test query executions endpoint
            print("\nTesting query executions endpoint...")
            response = make_request("GET", "/query-executions", params={"user_id": 1})
            
            if response and response.status_code == 200:
                executions = response.json()
                print(f"\nFound {len(executions)} query executions:")
                for exe in executions:
                    print(f"- Execution {exe['id']}: {exe['execution_status']} ({exe['execution_duration']}ms)")
            
            # 4. Test user stats endpoint
            print("\nTesting user stats endpoint...")
            response = make_request("GET", "/user/1/query-stats")
            
            if response and response.status_code == 200:
                stats = response.json()
                print("\nUser statistics:")
                print(f"- Total queries: {stats['total_queries']}")
                print(f"- Successful queries: {stats['successful_queries']}")
                print(f"- Failed queries: {stats['failed_queries']}")
                print(f"- Average duration: {stats['average_duration_ms']}ms")
                
    except Exception as e:
        print(f"\nError during API testing: {str(e)}")
        raise

if __name__ == "__main__":
    print("Testing API endpoints...")
    test_api()
    print("\nAPI testing completed!") 