"""
Test script for machine state detection functionality
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.machine_state_service import (
    MachineStateDetector, MachineStateEnum, StateThresholds, SensorReading
)


def test_state_scenarios():
    """Test various machine state scenarios"""
    
    print("🧪 Testing Machine State Detection Scenarios")
    print("=" * 50)
    
    # Initialize detector with default thresholds
    detector = MachineStateDetector("test-machine")
    
    test_cases = [
        {
            "name": "OFF State",
            "reading": SensorReading(
                timestamp=datetime.utcnow(),
                screw_rpm=0.0,
                pressure_bar=0.0,
                temp_zone_1=25.0,
                temp_zone_2=20.0,
                temp_zone_3=22.0,
                temp_zone_4=21.0
            ),
            "expected_state": MachineStateEnum.OFF
        },
        {
            "name": "HEATING State",
            "reading": SensorReading(
                timestamp=datetime.utcnow(),
                screw_rpm=0.0,
                pressure_bar=0.0,
                temp_zone_1=80.0,
                temp_zone_2=75.0,
                temp_zone_3=78.0,
                temp_zone_4=76.0
            ),
            "expected_state": MachineStateEnum.HEATING,
            "setup_heating": True  # Special setup for heating
        },
        {
            "name": "IDLE State",
            "reading": SensorReading(
                timestamp=datetime.utcnow(),
                screw_rpm=0.0,
                pressure_bar=0.0,
                temp_zone_1=180.0,
                temp_zone_2=175.0,
                temp_zone_3=178.0,
                temp_zone_4=176.0
            ),
            "expected_state": MachineStateEnum.IDLE
        },
        {
            "name": "PRODUCTION State (Primary)",
            "reading": SensorReading(
                timestamp=datetime.utcnow(),
                screw_rpm=20.0,
                pressure_bar=8.0,
                temp_zone_1=200.0,
                temp_zone_2=195.0,
                temp_zone_3=198.0,
                temp_zone_4=196.0
            ),
            "expected_state": MachineStateEnum.PRODUCTION
        },
        {
            "name": "PRODUCTION State (Fallback)",
            "reading": SensorReading(
                timestamp=datetime.utcnow(),
                screw_rpm=20.0,
                pressure_bar=3.0,  # Below P_PROD but above P_ON
                temp_zone_1=200.0,
                temp_zone_2=195.0,
                temp_zone_3=198.0,
                temp_zone_4=196.0,
                motor_load=0.2  # Above MOTOR_LOAD_MIN
            ),
            "expected_state": MachineStateEnum.PRODUCTION
        },
        {
            "name": "COOLING State",
            "reading": SensorReading(
                timestamp=datetime.utcnow(),
                screw_rpm=0.0,
                pressure_bar=0.0,
                temp_zone_1=100.0,
                temp_zone_2=95.0,
                temp_zone_3=98.0,
                temp_zone_4=96.0
            ),
            "expected_state": MachineStateEnum.COOLING,
            "setup_cooling": True  # Special setup for cooling
        },
        {
            "name": "SENSOR_FAULT State",
            "reading": SensorReading(
                timestamp=datetime.utcnow(),
                screw_rpm=20.0,
                pressure_bar=0.0,  # Fault: pressure 0 while RPM high
                temp_zone_1=-10.0,  # Fault: implausible temperature
                temp_zone_2=200.0,
                temp_zone_3=198.0,
                temp_zone_4=196.0
            ),
            "expected_state": MachineStateEnum.SENSOR_FAULT
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📋 Test Case {i+1}: {test_case['name']}")
        print("-" * 30)
        
        # Reset detector for clean test
        detector = MachineStateDetector("test-machine")
        
        # Special setup for heating/cooling states
        if test_case.get("setup_heating"):
            # Add some historical data to establish heating trend
            for j in range(10):
                past_time = datetime.utcnow() - timedelta(minutes=10-j)
                temp = 60 + j * 2  # Increasing temperature
                reading = SensorReading(
                    timestamp=past_time,
                    screw_rpm=0.0,
                    pressure_bar=0.0,
                    temp_zone_1=temp,
                    temp_zone_2=temp-5,
                    temp_zone_3=temp-2,
                    temp_zone_4=temp-4
                )
                detector.add_reading(reading)
        
        elif test_case.get("setup_cooling"):
            # Add some historical data to establish cooling trend
            for j in range(10):
                past_time = datetime.utcnow() - timedelta(minutes=10-j)
                temp = 150 - j * 5  # Decreasing temperature
                reading = SensorReading(
                    timestamp=past_time,
                    screw_rpm=0.0,
                    pressure_bar=0.0,
                    temp_zone_1=temp,
                    temp_zone_2=temp-5,
                    temp_zone_3=temp-2,
                    temp_zone_4=temp-4
                )
                detector.add_reading(reading)
        
        # Add multiple readings to stabilize state
        for j in range(5):
            reading = test_case["reading"]
            if j > 0:
                # Slight variations for subsequent readings
                reading = SensorReading(
                    timestamp=datetime.utcnow() + timedelta(seconds=j),
                    screw_rpm=reading.screw_rpm,
                    pressure_bar=reading.pressure_bar,
                    temp_zone_1=reading.temp_zone_1 + (j * 0.1),
                    temp_zone_2=reading.temp_zone_2 + (j * 0.1),
                    temp_zone_3=reading.temp_zone_3 + (j * 0.1),
                    temp_zone_4=reading.temp_zone_4 + (j * 0.1),
                    motor_load=reading.motor_load,
                    throughput_kg_h=reading.throughput_kg_h
                )
            
            state_info = detector.add_reading(reading)
        
        # Check final state
        actual_state = state_info.state
        expected_state = test_case["expected_state"]
        
        print(f"Expected: {expected_state.value}")
        print(f"Actual: {actual_state.value}")
        print(f"Confidence: {state_info.confidence:.2f}")
        print(f"Metrics:")
        print(f"  - Temp Avg: {state_info.metrics.temp_avg:.1f}°C")
        print(f"  - dTemp/dt: {state_info.metrics.d_temp_avg:.2f}°C/min")
        print(f"  - RPM Stable: {state_info.metrics.rpm_stable:.2f}")
        print(f"  - Pressure Stable: {state_info.metrics.pressure_stable:.2f}")
        
        if actual_state == expected_state:
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
            failed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 30)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        return False


def test_threshold_configuration():
    """Test custom threshold configuration"""
    
    print("\n🔧 Testing Custom Threshold Configuration")
    print("=" * 50)
    
    # Custom thresholds
    custom_thresholds = StateThresholds(
        RPM_ON=3.0,
        RPM_PROD=8.0,
        P_ON=1.5,
        P_PROD=4.0,
        T_MIN_ACTIVE=50.0
    )
    
    detector = MachineStateDetector("test-machine", custom_thresholds)
    
    # Test with values that would normally be PRODUCTION but should be IDLE with custom thresholds
    reading = SensorReading(
        timestamp=datetime.utcnow(),
        screw_rpm=10.0,  # Above default RPM_PROD but below custom RPM_PROD
        pressure_bar=6.0,  # Above default P_PROD but below custom P_PROD
        temp_zone_1=180.0,
        temp_zone_2=175.0,
        temp_zone_3=178.0,
        temp_zone_4=176.0
    )
    
    state_info = detector.add_reading(reading)
    
    print(f"Custom Thresholds Test:")
    print(f"RPM: {reading.screw_rpm} (Custom PROD: {custom_thresholds.RPM_PROD})")
    print(f"Pressure: {reading.pressure_bar} (Custom PROD: {custom_thresholds.P_PROD})")
    print(f"State: {state_info.state.value}")
    
    # With custom thresholds, this should be IDLE, not PRODUCTION
    if state_info.state == MachineStateEnum.IDLE:
        print("✅ Custom thresholds working correctly")
        return True
    else:
        print("❌ Custom thresholds not working as expected")
        return False


def test_hysteresis():
    """Test hysteresis/debounce behavior"""
    
    print("\n⏱️ Testing Hysteresis/Debounce Behavior")
    print("=" * 50)
    
    detector = MachineStateDetector("test-machine")
    
    # Start in OFF state
    off_reading = SensorReading(
        timestamp=datetime.utcnow(),
        screw_rpm=0.0,
        pressure_bar=0.0,
        temp_zone_1=25.0,
        temp_zone_2=20.0,
        temp_zone_3=22.0,
        temp_zone_4=21.0
    )
    
    state_info = detector.add_reading(off_reading)
    print(f"Initial state: {state_info.state.value}")
    
    # Quickly switch to PRODUCTION criteria
    prod_reading = SensorReading(
        timestamp=datetime.utcnow() + timedelta(seconds=1),
        screw_rpm=20.0,
        pressure_bar=8.0,
        temp_zone_1=200.0,
        temp_zone_2=195.0,
        temp_zone_3=198.0,
        temp_zone_4=196.0
    )
    
    state_info = detector.add_reading(prod_reading)
    print(f"After PRODUCTION criteria: {state_info.state.value}")
    
    # Should still be OFF due to hysteresis (need 90s for PRODUCTION)
    if state_info.state == MachineStateEnum.OFF:
        print("✅ Hysteresis working - state unchanged due to time requirement")
        return True
    else:
        print("❌ Hysteresis not working - state changed too quickly")
        return False


def main():
    """Run all tests"""
    print("🚀 Machine State Detection Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run all test functions
    results.append(test_state_scenarios())
    results.append(test_threshold_configuration())
    results.append(test_hysteresis())
    
    # Summary
    print(f"\n📋 Final Test Summary")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Test Suites Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All test suites passed!")
        print("\n✅ Machine State Detection is ready for deployment!")
        return 0
    else:
        print(f"⚠️ {total - passed} test suite(s) failed")
        print("\n❌ Please review and fix issues before deployment")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
