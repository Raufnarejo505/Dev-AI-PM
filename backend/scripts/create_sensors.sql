-- Create sensors for Extruder-SQL machine
INSERT INTO sensor (id, name, machine_id, sensor_type, unit, min_threshold, max_threshold, warning_threshold, critical_threshold, metadata, created_at, updated_at)
VALUES 
  (gen_random_uuid(), 'ScrewSpeed_rpm', (SELECT id FROM machine WHERE name = 'Extruder-SQL'), 'rpm', 'rpm', 0, 500, 400, 450, '{"source": "seed"}'::jsonb, NOW(), NOW()),
  (gen_random_uuid(), 'Pressure_bar', (SELECT id FROM machine WHERE name = 'Extruder-SQL'), 'pressure', 'bar', 0, 200, 150, 180, '{"source": "seed"}'::jsonb, NOW(), NOW()),
  (gen_random_uuid(), 'Temperaturzonen Zone 1', (SELECT id FROM machine WHERE name = 'Extruder-SQL'), 'temperature', '°C', 0, 300, 250, 280, '{"source": "seed"}'::jsonb, NOW(), NOW()),
  (gen_random_uuid(), 'Temperaturzonen Zone 2', (SELECT id FROM machine WHERE name = 'Extruder-SQL'), 'temperature', '°C', 0, 300, 250, 280, '{"source": "seed"}'::jsonb, NOW(), NOW()),
  (gen_random_uuid(), 'Temperaturzonen Zone 3', (SELECT id FROM machine WHERE name = 'Extruder-SQL'), 'temperature', '°C', 0, 300, 250, 280, '{"source": "seed"}'::jsonb, NOW(), NOW()),
  (gen_random_uuid(), 'Temperaturzonen Zone 4', (SELECT id FROM machine WHERE name = 'Extruder-SQL'), 'temperature', '°C', 0, 300, 250, 280, '{"source": "seed"}'::jsonb, NOW(), NOW())
ON CONFLICT DO NOTHING;
