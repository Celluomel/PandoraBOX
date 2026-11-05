import test from 'node:test';
import assert from 'node:assert/strict';
import { radarTargets, ultrasonicRanges, tofRange, batteryEstimate, commandLegs } from '../../body_runtime_host/hexapod_twin_telemetry.js';

const now = 1000;

test('radar shows only fresh physical targets and keeps LD2450 coordinates', () => {
  const status = { available: true, sample: { timestamp: 999, source: 'hlk_ld2450_ventuno_bridge',
    frame: 'body', targets: [{ target_id: 2, position_m: [-0.4, 1.8, 0] }] } };
  assert.deepEqual(radarTargets(status, now).map(({ forward, left }) => [forward, left]), [[1.8, 0.4]]);
  assert.deepEqual(radarTargets({ ...status, sample: { ...status.sample, timestamp: 990 } }, now), []);
  assert.deepEqual(radarTargets({ ...status, sample: { ...status.sample, simulated: true } }, now), []);
});

test('ultrasonic rejects individual stale and no-echo channels', () => {
  const status = { sample: { timestamp: 999, sensors: [
    { id: 'front_left', available: true, distance_m: 0.76, age_ms: 100 },
    { id: 'front_right', available: true, distance_m: 0.5, age_ms: 4000 },
    { id: 'rear', available: false, distance_m: null, error: 'no_echo' },
  ] } };
  assert.deepEqual(ultrasonicRanges(status, now), { front_left: 0.76 });
  assert.deepEqual(ultrasonicRanges({ sample: { ...status.sample, timestamp: 990 } }, now), {});
});

test('ToF, battery, and FNHR pose retain their measurement limits', () => {
  assert.equal(tofRange({ available: false, sample: { timestamp: 999, distance_m: 1 } }, now), null);
  assert.equal(tofRange({ available: true, sample: { timestamp: 999, distance_m: 1 } }, now), 1);
  assert.deepEqual(batteryEstimate({ battery_estimate: { level_percent_est: 0,
    direct_battery_measurement: false, counter_exceeds_usable_capacity: true } }),
  { percent: 0, estimated: true, lowerBound: true });
  const legs = Array.from({ length: 6 }, (_, i) => ({ leg: i + 1, joint_angles_deg: [0, 1, 2] }));
  assert.equal(commandLegs({ connected: true, estimated_leg_state: { received_at: 999,
    measured_feedback: false, legs } }, now)?.length, 6);
  assert.equal(commandLegs({ connected: true, estimated_leg_state: { received_at: 990,
    measured_feedback: false, legs } }, now), null);
});
