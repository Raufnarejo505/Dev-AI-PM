import requests
import json
import random
import time

# Test the prediction endpoint directly
def test_prediction_endpoint():
    base_url = "http://localhost:8001"
    
    sensors = ["pressure", "temperature", "motor_current", "vibration"]
    
    for i in range(10):
        # Create test sensor data
        test_data = {
            "nozzle_id": f"factory1_plantA_line1_machine{i%2+1}",
            "timestamp": "2024-01-15T14:30:00Z",
            "sensors": {
                random.choice(sensors): random.uniform(100, 200)
            }
        }
        
        try:
            response = requests.post(f"{base_url}/predict", json=test_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Prediction {i+1}: {result['status']} (score: {result['anomaly_score']})")
                
                # If anomaly detected, print alert
                if result['status'] in ['WARN', 'ALARM']:
                    print(f"🚨 ALERT: {result['nozzle_id']} - {result['status']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        time.sleep(1)  # Wait 1 second between requests

if __name__ == "__main__":
    test_prediction_endpoint()