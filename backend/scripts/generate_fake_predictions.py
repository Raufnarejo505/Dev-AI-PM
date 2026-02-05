"""
Quick script to generate fake predictions for testing dashboard
"""
import asyncio
import sys
from datetime import datetime, timedelta
from uuid import uuid4
import random

sys.path.append('/app')

from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from app.models.sensor import Sensor
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate
from app.services import prediction_service, machine_service, sensor_service
from sqlalchemy import select

async def generate_fake_predictions():
    async with AsyncSessionLocal() as session:
        # Get or create machines
        machines_result = await session.execute(select(Machine))
        machines = machines_result.scalars().all()
        
        if not machines:
            print("No machines found. Creating test machines...")
            from app.schemas.machine import MachineCreate
            machines = []
            for i in range(3):
                machine = await machine_service.create_machine(
                    session,
                    MachineCreate(
                        name=f"Machine-{i+1}",
                        status="online",
                        location=f"Building {chr(65+i)}, Floor {i+1}",
                    )
                )
                machines.append(machine)
            await session.commit()
        
        # Get or create sensors
        sensors_result = await session.execute(select(Sensor))
        sensors = sensors_result.scalars().all()
        
        if not sensors:
            print("No sensors found. Creating test sensors...")
            from app.schemas.sensor import SensorCreate
            sensors = []
            for machine in machines[:2]:  # Create sensors for first 2 machines
                for sensor_name in ["temperature", "pressure", "vibration"]:
                    sensor = await sensor_service.create_sensor(
                        session,
                        SensorCreate(
                            name=sensor_name,
                            sensor_type=sensor_name,
                            unit="°C" if sensor_name == "temperature" else "psi" if sensor_name == "pressure" else "mm/s",
                            machine_id=machine.id,
                            min_threshold=0,
                            max_threshold=100,
                        )
                    )
                    sensors.append(sensor)
            await session.commit()
        
        # Generate 400+ predictions
        print(f"Generating predictions for {len(machines)} machines and {len(sensors)} sensors...")
        
        predictions_to_create = 400
        anomalies_count = 0
        created_count = 0
        
        for i in range(predictions_to_create):
            machine = random.choice(machines)
            machine_sensors = [s for s in sensors if s.machine_id == machine.id]
            if not machine_sensors:
                continue
            sensor = random.choice(machine_sensors)
            
            # Create timestamp (last 24 hours)
            hours_ago = random.uniform(0, 24)
            timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
            
            # Force first 60 to be anomalies, then 15% chance
            is_anomaly = i < 60 or random.random() < 0.15
            if is_anomaly:
                status = random.choice(["warning", "critical"])
                score = random.uniform(0.7, 1.0)
                prediction_type = random.choice(["anomaly", "failure_risk", "degradation"])
                anomalies_count += 1
            else:
                status = "normal"
                score = random.uniform(0.0, 0.3)
                prediction_type = "normal"
            
            confidence = random.uniform(0.6, 0.95)
            
            pred_create = PredictionCreate(
                machine_id=machine.id,
                sensor_id=sensor.id,
                timestamp=timestamp,
                prediction=prediction_type,
                status=status,
                score=float(score),
                confidence=float(confidence),
                anomaly_type=prediction_type if is_anomaly else None,
                model_version="1.0.0",
                response_time_ms=random.uniform(10, 50),
            )
            
            try:
                await prediction_service.create_prediction(session, pred_create)
                created_count += 1
                if created_count % 50 == 0:
                    await session.commit()
                    print(f"Created {created_count} predictions... ({anomalies_count} anomalies so far)")
            except Exception as e:
                print(f"Error creating prediction {i+1}: {e}")
                await session.rollback()
        
        await session.commit()
        print(f"\n✅ Generated {created_count} predictions")
        print(f"✅ {anomalies_count} anomalies created")
        print(f"✅ {created_count - anomalies_count} normal predictions created")

if __name__ == "__main__":
    asyncio.run(generate_fake_predictions())

