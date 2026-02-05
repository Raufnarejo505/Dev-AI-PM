#!/usr/bin/env python3
"""
Test script to verify machine state detection logic
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime
from app.services.machine_state_service import MachineStateDetector, StateThresholds, SensorReading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_production_detection():
    """Test production state detection with dashboard values"""
    
    # Create test reading matching dashboard values
    reading = SensorReading(
        timestamp=datetime.now(),
        screw_rpm=85.3,      # Well above RPM_PROD (10.0)
        pressure_bar=29.6,  # Well above P_PROD (5.0)
        temp_zone_1=178.0,
        temp_zone_2=179.0,
        temp_zone_3=180.0,
        temp_zone_4=181.0
    )
    
    # Test state detection
    detector = MachineStateDetector('test-machine')
    result = detector.add_reading(reading)
    
    print("=" * 60)
    print("MACHINE STATE DETECTION TEST")
    print("=" * 60)
    print(f"Input Values:")
    print(f"  Screw RPM: {reading.screw_rpm} (threshold: >=10.0)")
    print(f"  Pressure: {reading.pressure_bar} bar (threshold: >=5.0)")
    print(f"  Temperature Zones: {reading.temp_zone_1}, {reading.temp_zone_2}, {reading.temp_zone_3}, {reading.temp_zone_4}")
    print()
    print(f"Detection Results:")
    print(f"  Detected State: {result.state}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Expected State: PRODUCTION")
    print()
    
    # Verify thresholds
    thresholds = detector.thresholds
    print(f"Thresholds Applied:")
    print(f"  RPM_ON: {thresholds.RPM_ON}")
    print(f"  RPM_PROD: {thresholds.RPM_PROD}")
    print(f"  P_ON: {thresholds.P_ON}")
    print(f"  P_PROD: {thresholds.P_PROD}")
    print(f"  T_MIN_ACTIVE: {thresholds.T_MIN_ACTIVE}")
    print()
    
    # Manual verification
    rpm_meets_prod = reading.screw_rpm >= thresholds.RPM_PROD
    pressure_meets_prod = reading.pressure_bar >= thresholds.P_PROD
    
    print(f"Manual Logic Verification:")
    print(f"  RPM >= RPM_PROD: {reading.screw_rpm} >= {thresholds.RPM_PROD} = {rpm_meets_prod}")
    print(f"  Pressure >= P_PROD: {reading.pressure_bar} >= {thresholds.P_PROD} = {pressure_meets_prod}")
    print(f"  Both criteria met: {rpm_meets_prod and pressure_meets_prod}")
    print()
    
    if result.state.value == "PRODUCTION":
        print("✅ SUCCESS: State correctly detected as PRODUCTION")
        return True
    else:
        print("❌ FAILURE: State should be PRODUCTION but detected as", result.state)
        return False

if __name__ == "__main__":
    success = test_production_detection()
    sys.exit(0 if success else 1)
