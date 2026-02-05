"""
Production Testing Script
Comprehensive testing of all backend endpoints and functionality
"""
import asyncio
import httpx
import json
from datetime import datetime, timezone
from uuid import uuid4

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test_production@example.com"
TEST_USER_PASSWORD = "Test123!@#"
access_token = None

async def test_authentication():
    """Test user authentication"""
    print("\n=== Testing Authentication ===")
    async with httpx.AsyncClient() as client:
        # Register test user
        try:
            register_response = await client.post(
                f"{BASE_URL}/users",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                    "full_name": "Production Test User",
                },
            )
            if register_response.status_code == 201:
                print("✅ User registration successful")
            elif register_response.status_code == 400:
                print("ℹ️  User already exists (continuing with login)")
            else:
                print(f"❌ Registration failed: {register_response.status_code}")
        except Exception as e:
            print(f"⚠️  Registration error: {e}")

        # Login
        login_response = await client.post(
            f"{BASE_URL}/users/login",
            data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if login_response.status_code == 200:
            global access_token
            access_token = login_response.json()["access_token"]
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return False

async def test_machines():
    """Test machine CRUD operations"""
    print("\n=== Testing Machines API ===")
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Create machine
        machine_data = {
            "name": f"Test-Machine-{uuid4().hex[:8]}",
            "status": "online",
            "location": "Test Building, Floor 1",
            "criticality": "high",
            "metadata": {"test": True, "created_at": datetime.now(timezone.utc).isoformat()}
        }
        
        create_response = await client.post(
            f"{BASE_URL}/machines",
            json=machine_data,
            headers=headers,
        )
        
        if create_response.status_code == 201:
            machine = create_response.json()
            machine_id = machine["id"]
            print(f"✅ Machine created: {machine['name']} (ID: {machine_id})")
            
            # Read machine
            get_response = await client.get(
                f"{BASE_URL}/machines/{machine_id}",
                headers=headers,
            )
            if get_response.status_code == 200:
                print("✅ Machine read successful")
            else:
                print(f"❌ Machine read failed: {get_response.status_code}")
            
            # List machines
            list_response = await client.get(
                f"{BASE_URL}/machines",
                headers=headers,
            )
            if list_response.status_code == 200:
                machines = list_response.json()
                print(f"✅ Listed {len(machines)} machines")
            else:
                print(f"❌ Machine list failed: {list_response.status_code}")
            
            # Update machine
            update_data = {"status": "maintenance", "location": "Updated Location"}
            update_response = await client.put(
                f"{BASE_URL}/machines/{machine_id}",
                json=update_data,
                headers=headers,
            )
            if update_response.status_code == 200:
                print("✅ Machine update successful")
            else:
                print(f"❌ Machine update failed: {update_response.status_code}")
            
            return machine_id
        else:
            print(f"❌ Machine creation failed: {create_response.status_code} - {create_response.text}")
            return None

async def test_sensors(machine_id):
    """Test sensor CRUD operations"""
    print("\n=== Testing Sensors API ===")
    if not machine_id:
        print("⚠️  Skipping sensor tests - no machine ID")
        return None
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Create sensor
        sensor_data = {
            "name": f"Test-Sensor-{uuid4().hex[:8]}",
            "machine_id": machine_id,
            "type": "pressure",
            "unit": "psi",
            "metadata": {"test": True}
        }
        
        create_response = await client.post(
            f"{BASE_URL}/sensors",
            json=sensor_data,
            headers=headers,
        )
        
        if create_response.status_code == 201:
            sensor = create_response.json()
            sensor_id = sensor["id"]
            print(f"✅ Sensor created: {sensor['name']} (ID: {sensor_id})")
            
            # List sensors
            list_response = await client.get(
                f"{BASE_URL}/sensors",
                headers=headers,
            )
            if list_response.status_code == 200:
                sensors = list_response.json()
                print(f"✅ Listed {len(sensors)} sensors")
            else:
                print(f"❌ Sensor list failed: {list_response.status_code}")
            
            return sensor_id
        else:
            print(f"❌ Sensor creation failed: {create_response.status_code} - {create_response.text}")
            return None

async def test_sensor_data(sensor_id, machine_id):
    """Test sensor data ingestion"""
    print("\n=== Testing Sensor Data Ingestion ===")
    if not sensor_id or not machine_id:
        print("⚠️  Skipping sensor data tests - missing IDs")
        return
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Ingest sensor data
        sensor_data_payload = {
            "sensor_id": sensor_id,
            "machine_id": machine_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": 145.5,
            "status": "normal",
            "metadata": {"test": True, "source": "production_test"}
        }
        
        ingest_response = await client.post(
            f"{BASE_URL}/sensor-data",
            json=sensor_data_payload,
            headers=headers,
        )
        
        if ingest_response.status_code == 201:
            data = ingest_response.json()
            print(f"✅ Sensor data ingested: ID {data['id']}, Value: {data['value']}")
        else:
            print(f"❌ Sensor data ingestion failed: {ingest_response.status_code} - {ingest_response.text}")

async def test_ai_service():
    """Test AI service predictions"""
    print("\n=== Testing AI Service ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check AI service health
        try:
            health_response = await client.get(f"{BASE_URL}/ai/status")
            if health_response.status_code == 200:
                ai_status = health_response.json()
                print(f"✅ AI Service Status: {ai_status.get('status', 'unknown')}")
                print(f"   Model Loaded: {ai_status.get('model_loaded', False)}")
                print(f"   Model Version: {ai_status.get('model_version', 'unknown')}")
            else:
                print(f"❌ AI service health check failed: {health_response.status_code}")
        except Exception as e:
            print(f"❌ AI service connection error: {e}")
        
        # Test prediction
        headers = {"Authorization": f"Bearer {access_token}"}
        prediction_payload = {
            "machine_id": str(uuid4()),
            "sensor_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "readings": {
                "pressure": 175.0,  # Above warning threshold (150)
                "temperature": 265.0,  # Above warning threshold (250)
            }
        }
        
        try:
            predict_response = await client.post(
                f"{BASE_URL}/ai/predict",
                json=prediction_payload,
                headers=headers,
                timeout=30.0,
            )
            
            if predict_response.status_code == 200:
                prediction = predict_response.json()
                print(f"✅ AI Prediction received:")
                print(f"   Status: {prediction.get('status', 'unknown')}")
                print(f"   Score: {prediction.get('score', 0):.4f}")
                print(f"   Confidence: {prediction.get('confidence', 0):.4f}")
                print(f"   Anomaly Type: {prediction.get('anomaly_type', 'unknown')}")
            else:
                print(f"❌ AI prediction failed: {predict_response.status_code} - {predict_response.text}")
        except Exception as e:
            print(f"❌ AI prediction error: {e}")

async def test_dashboard():
    """Test dashboard endpoints"""
    print("\n=== Testing Dashboard API ===")
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get overview
        overview_response = await client.get(
            f"{BASE_URL}/dashboard/overview",
            headers=headers,
        )
        if overview_response.status_code == 200:
            overview = overview_response.json()
            print("✅ Dashboard overview retrieved:")
            print(f"   Machines: {overview.get('machines', {}).get('total', 0)}")
            print(f"   Sensors: {overview.get('sensors', {}).get('total', 0)}")
            print(f"   Active Alarms: {overview.get('alarms', {}).get('active', 0)}")
        else:
            print(f"❌ Dashboard overview failed: {overview_response.status_code}")

async def test_predictions():
    """Test predictions endpoint"""
    print("\n=== Testing Predictions API ===")
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # List predictions
        list_response = await client.get(
            f"{BASE_URL}/predictions",
            headers=headers,
            params={"limit": 10},
        )
        if list_response.status_code == 200:
            predictions = list_response.json()
            print(f"✅ Retrieved {len(predictions)} predictions")
            if predictions:
                latest = predictions[0]
                print(f"   Latest: Status={latest.get('status')}, Score={latest.get('score', 0):.4f}")
        else:
            print(f"❌ Predictions list failed: {list_response.status_code}")

async def test_alarms():
    """Test alarms endpoint"""
    print("\n=== Testing Alarms API ===")
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # List alarms
        list_response = await client.get(
            f"{BASE_URL}/alarms",
            headers=headers,
            params={"status": "active"},
        )
        if list_response.status_code == 200:
            alarms = list_response.json()
            print(f"✅ Retrieved {len(alarms)} active alarms")
        else:
            print(f"❌ Alarms list failed: {list_response.status_code}")

async def test_mqtt_status():
    """Test MQTT status"""
    print("\n=== Testing MQTT Status ===")
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        status_response = await client.get(
            f"{BASE_URL}/mqtt/status",
            headers=headers,
        )
        if status_response.status_code == 200:
            mqtt_status = status_response.json()
            print(f"✅ MQTT Status: {mqtt_status.get('status', 'unknown')}")
            print(f"   Connected: {mqtt_status.get('connected', False)}")
            print(f"   Queue Size: {mqtt_status.get('queue_size', 0)}")
        else:
            print(f"❌ MQTT status failed: {status_response.status_code}")

async def test_reports():
    """Test reports generation"""
    print("\n=== Testing Reports API ===")
    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Generate report
        report_response = await client.post(
            f"{BASE_URL}/reports/generate",
            json={
                "start_date": (datetime.now(timezone.utc).replace(day=1)).isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat(),
                "format": "csv",
            },
            headers=headers,
        )
        if report_response.status_code == 200:
            report = report_response.json()
            print(f"✅ Report generated: {report.get('filename', 'unknown')}")
        else:
            print(f"❌ Report generation failed: {report_response.status_code} - {report_response.text}")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("PRODUCTION TESTING - COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    
    # Test authentication
    if not await test_authentication():
        print("\n❌ Authentication failed - cannot continue tests")
        return
    
    # Test core functionality
    machine_id = await test_machines()
    sensor_id = await test_sensors(machine_id)
    await test_sensor_data(sensor_id, machine_id)
    
    # Test AI service
    await test_ai_service()
    
    # Test dashboard and data endpoints
    await test_dashboard()
    await test_predictions()
    await test_alarms()
    
    # Test integrations
    await test_mqtt_status()
    
    # Test reporting
    await test_reports()
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

