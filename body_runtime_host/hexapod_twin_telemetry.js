// Read-only adapter for the Body's timestamped hardware contracts.
// A fresh RPC response does not make an old sensor sample fresh.
export function fresh(timestamp, now, maxAge = 3) {
  const value = Number(timestamp);
  return Number.isFinite(value) && value > 0 && now - value >= -1 && now - value <= maxAge;
}

export function radarTargets(status, now) {
  const sample = status?.available ? status.sample : null;
  if (!sample || sample.simulated || !fresh(sample.timestamp, now)) return [];
  const ld2450 = /^hlk_ld2450/i.test(String(sample.source || ''));
  if (!ld2450 && !/^body(?:_front)?$/i.test(String(sample.frame || ''))) return [];
  return (Array.isArray(sample.targets) ? sample.targets : []).flatMap((target, index) => {
    const position = target.position_m || target.position;
    if (!Array.isArray(position) || position.length < 2) return [];
    const forward = Number(position[ld2450 ? 1 : 0]);
    const left = Number(position[ld2450 ? 0 : 1]) * (ld2450 ? -1 : 1);
    const distance = Math.hypot(forward, left);
    if (!Number.isFinite(distance) || forward <= 0 || distance > 6) return [];
    return [{ id: String(target.target_id ?? target.id ?? index + 1), forward, left, distance,
      timestamp: Number(sample.timestamp), classification: 'unclassified' }];
  });
}

export function ultrasonicRanges(status, now) {
  const sample = status?.sample;
  if (!sample || sample.simulated || !fresh(sample.timestamp, now)) return {};
  const result = {};
  for (const item of Array.isArray(sample.sensors) ? sample.sensors : []) {
    const age = Number(item.age_ms);
    const distance = Number(item.distance_m);
    if (item.available && Number.isFinite(distance) && distance >= 0.02 && distance <= 4
        && (!Number.isFinite(age) || age <= 3000)) result[item.id] = distance;
  }
  return result;
}

export function tofRange(status, now) {
  const sample = status?.available ? status.sample : null;
  const distance = Number(sample?.distance_m);
  return sample && !sample.simulated && fresh(sample.timestamp, now)
    && Number.isFinite(distance) && distance > 0 && distance <= 4 ? distance : null;
}

export function batteryEstimate(status) {
  const estimate = status?.battery_estimate;
  const value = Number(estimate?.level_percent_est);
  return estimate?.direct_battery_measurement === false && Number.isFinite(value)
    ? { percent: Math.max(0, Math.min(100, value)), estimated: true,
      lowerBound: Boolean(estimate.counter_exceeds_usable_capacity) } : null;
}

export function commandLegs(status, now) {
  const state = status?.connected ? status.estimated_leg_state : null;
  if (!state || state.measured_feedback || !fresh(state.received_at, now, 5)) return null;
  const legs = Array.isArray(state.legs) ? state.legs : [];
  if (legs.length !== 6 || !legs.every(leg => Array.isArray(leg.joint_angles_deg)
      && leg.joint_angles_deg.length === 3 && leg.joint_angles_deg.every(value => Number.isFinite(Number(value))))) return null;
  return legs;
}
