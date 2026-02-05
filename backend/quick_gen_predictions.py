"""Quick script to generate predictions - run directly"""
import asyncio
import sys
from datetime import datetime, timedelta
import random

sys.path.append('/app')

from app.db.session import AsyncSessionLocal
from app.models.machine import Machine
from app.models.sensor import Sensor
from app.schemas.prediction import PredictionCreate
from app.services import prediction_service
from sqlalchemy import select

async def quick_gen():
    async with AsyncSessionLocal() as session:
        machines = (await session.execute(select(Machine))).scalars().all()[:5]
        if not machines:
            print("No machines found!")
            return
        
        sensors = (await session.execute(select(Sensor))).scalars().all()
        if not sensors:
            print("No sensors found - creating...")
            from app.schemas.sensor import SensorCreate
            from app.services import sensor_service
            for m in machines[:3]:
                for name in ["temperature", "pressure", "vibration"]:
                    s = await sensor_service.create_sensor(
                        session,
                        SensorCreate(name=name, sensor_type=name, machine_id=m.id, unit="C" if name=="temperature" else "psi" if name=="pressure" else "mm/s")
                    )
                    sensors.append(s)
            await session.commit()
            sensors = (await session.execute(select(Sensor))).scalars().all()
        
        anomalies = 0
        for i in range(400):
            m = random.choice(machines)
            machine_sensors = [s for s in sensors if s.machine_id == m.id]
            if not machine_sensors:
                machine_sensors = sensors[:1]
            s = random.choice(machine_sensors)
            
            is_anom = i < 60 or random.random() < 0.15
            if is_anom:
                anomalies += 1
            
            # Create prediction data dict without remaining_useful_life (model uses 'rul' column)
            pred_data = {
                "machine_id": m.id,
                "sensor_id": s.id,
                "timestamp": datetime.utcnow() - timedelta(hours=random.uniform(0, 24)),
                "prediction": "anomaly" if is_anom else "normal",
                "status": "warning" if is_anom else "normal",
                "score": float(random.uniform(0.7, 1.0) if is_anom else random.uniform(0, 0.3)),
                "confidence": float(random.uniform(0.6, 0.95)),
                "model_version": "1.0.0",
                "response_time_ms": float(random.uniform(10, 50)),
            }
            if is_anom:
                pred_data["anomaly_type"] = "anomaly"
            
            p = PredictionCreate(**pred_data)
            await prediction_service.create_prediction(session, p)
            if (i + 1) % 100 == 0:
                await session.commit()
                print(f"Created {i+1} predictions, {anomalies} anomalies so far")
        
        await session.commit()
        print(f"\n✅ Done: {400} predictions created, {anomalies} anomalies")

if __name__ == "__main__":
    asyncio.run(quick_gen())

