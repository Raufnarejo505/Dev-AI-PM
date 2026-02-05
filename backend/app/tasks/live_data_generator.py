"""
Background task to generate live dummy data for dashboard
This ensures live data is always available even if MQTT isn't working
"""
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
import random

from loguru import logger

from app.db.session import AsyncSessionLocal
from app.services import machine_service, sensor_service, sensor_data_service, prediction_service
from app.schemas.sensor_data import SensorDataIn
from app.schemas.prediction import PredictionCreate


async def generate_live_dummy_data():
    """Generate live dummy sensor data and predictions"""
    try:
        async with AsyncSessionLocal() as session:
            # Get existing machines
            from sqlalchemy import select
            from app.models.machine import Machine
            from app.models.sensor import Sensor
            
            result = await session.execute(select(Machine))
            machines = result.scalars().all()
            
            if not machines:
                logger.warning("No machines found, cannot generate dummy data")
                return
            
            # For each machine, get sensors and generate data
            for machine in machines:
                sensor_result = await session.execute(
                    select(Sensor).where(Sensor.machine_id == machine.id)
                )
                sensors = sensor_result.scalars().all()
                
                if not sensors:
                    logger.debug(f"No sensors found for machine {machine.name}")
                    continue
                
                # Generate data for each sensor
                for sensor in sensors:
                    # Generate realistic sensor value based on sensor type
                    base_value = 50.0
                    if "pressure" in sensor.sensor_type.lower():
                        base_value = random.uniform(100, 180)
                    elif "temperature" in sensor.sensor_type.lower():
                        base_value = random.uniform(60, 120)
                    elif "vibration" in sensor.sensor_type.lower():
                        base_value = random.uniform(1.5, 5.0)
                    elif "current" in sensor.sensor_type.lower():
                        base_value = random.uniform(10, 50)
                    elif "flow" in sensor.sensor_type.lower():
                        base_value = random.uniform(50, 150)
                    else:
                        base_value = random.uniform(20, 100)
                    
                    # Add some variation
                    value = base_value + random.uniform(-5, 5)
                    timestamp = datetime.now(timezone.utc)
                    
                    # Ingest sensor data
                    sensor_data_in = SensorDataIn(
                        sensor_id=sensor.id,
                        machine_id=machine.id,
                        timestamp=timestamp,
                        value=float(value),
                        status="normal",
                        metadata={"generated_by": "live_data_generator"}
                    )
                    
                    try:
                        sensor_data_record = await sensor_data_service.ingest_sensor_data(session, sensor_data_in)
                        logger.debug(f"Generated sensor_data: {sensor_data_record.id} for {machine.name}/{sensor.name}")
                        
                        # Generate prediction
                        # Random anomaly chance (5%)
                        is_anomaly = random.random() < 0.05
                        score = random.uniform(0.1, 0.9) if not is_anomaly else random.uniform(0.8, 1.0)
                        confidence = random.uniform(0.7, 0.99)
                        status = "critical" if score > 0.8 else ("warning" if score > 0.6 else "normal")
                        prediction_type = "normal" if not is_anomaly else random.choice(["anomaly", "drift", "spike"])
                        
                        pred_create = PredictionCreate(
                            machine_id=machine.id,
                            sensor_id=sensor.id,
                            timestamp=timestamp,
                            prediction=prediction_type,
                            status=status,
                            score=float(score),
                            confidence=float(confidence),
                            anomaly_type="gradual_drift" if is_anomaly else None,
                            model_version="live_generator_v1",
                            response_time_ms=float(random.uniform(10, 50)),
                            metadata={"generated_by": "live_data_generator"}
                        )
                        
                        prediction = await prediction_service.create_prediction(session, pred_create)
                        logger.debug(f"Generated prediction: {prediction.id} for {machine.name}/{sensor.name} (status: {status})")
                        
                    except Exception as e:
                        logger.error(f"Error generating data for {machine.name}/{sensor.name}: {e}")
                        continue
            
            await session.commit()
            logger.info(f"✅ Generated live dummy data for {len(machines)} machines")
            
    except Exception as e:
        logger.error(f"Error in generate_live_dummy_data: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def start_live_data_generator(interval_seconds: int = 5):
    """Start background task that generates live data every N seconds"""
    logger.info(f"Starting live data generator (interval: {interval_seconds}s)")
    
    while True:
        try:
            await generate_live_dummy_data()
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Live data generator cancelled")
            break
        except Exception as e:
            logger.error(f"Error in live data generator loop: {e}")
            await asyncio.sleep(interval_seconds)


