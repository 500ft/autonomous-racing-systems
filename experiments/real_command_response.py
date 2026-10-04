"""Inspect one public development bag; fit command response on that same run.

No holdout evaluation, tire fitting, or vehicle calibration is performed here.
"""
import argparse
from collections import defaultdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np

# Units are conventions or embedded definitions, never calibration certificates.
UNITS = {
    'geometry_msgs/msg/Twist': 'ROS convention: linear m/s, angular rad/s; command mapping unverified',
    'geometry_msgs/msg/TwistStamped': 'Twist convention m/s and rad/s; accel-named topics overload Twist, units/differentiation unverified',
    'geometry_msgs/msg/PoseStamped': 'ROS convention: position m, unit quaternion xyzw',
    'tf2_msgs/msg/TFMessage': 'ROS convention: translation m, unit quaternion xyzw',
    'rosgraph_msgs/msg/Log': 'Text log; no physical units',
    'std_msgs/msg/Float64': 'Unitless message; topic-specific conversion/calibration not supplied',
    'std_msgs/msg/Bool': 'Boolean',
    'vesc_msgs/msg/VescStateStamped': 'Embedded definition: electrical rpm, V, A, deg C, Ah, Wh, tachometer counts; see vesc_message_definition.txt',
    'sensor_msgs/msg/LaserScan': 'Embedded ROS convention: ranges m, angles rad, timing s; intensity sensor-specific',
    'dynamic_reconfigure/msg/ConfigDescription': 'Parameter descriptions; units depend on parameter',
    'dynamic_reconfigure/msg/Config': 'Recorded laser settings: angles rad, time_offset s, cluster/skip counts',
    'diagnostic_msgs/msg/DiagnosticArray': 'Status codes and text key/value diagnostics; no uniform units',
    'nav_msgs/msg/Odometry': 'ROS convention: position m, twist m/s and rad/s; child frame empty',
    'visualization_msgs/msg/Marker': 'ROS convention: geometry m, quaternion xyzw; visualization, not calibration',
}
CAR = '/vrpn_client_node/Car_2_Tracking/'
CMD = '/cmd_vel'


def stats(values):
    a = np.asarray(values, dtype=float)
    return dict(zip(('min', 'p50', 'p95', 'max'), map(float, np.quantile(a, [0, .5, .95, 1])))) if len(a) else None


def timing(ns):
    a = np.asarray(ns, dtype=np.int64)
    d = np.diff(a) / 1e9
    positive = d[d > 0]
    return {
        'count': len(a), 'span_s': float((a[-1] - a[0]) / 1e9) if len(a) else 0,
        'mean_rate_hz': float((len(a)-1) * 1e9 / (a[-1]-a[0])) if len(a) > 1 and a[-1] > a[0] else None,
        'interval_s': stats(d), 'duplicate_intervals': int(np.sum(d == 0)),
        'backward_intervals': int(np.sum(d < 0)),
        'gap_rule': 'interval > 5 * median positive interval; descriptive, not an acceptance limit',
        'gap_threshold_s': float(5*np.median(positive)) if len(positive) else None,
        'gap_count': int(np.sum(d > 5*np.median(positive))) if len(positive) else 0,
    }


def world_to_tracking(q, v):
    """R(q).T @ v, quaternion xyzw; q maps tracking-frame vectors to world."""
    q = np.asarray(q, dtype=float)
    norms = np.linalg.norm(q, axis=-1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError('Zero orientation quaternion')
    q = q / norms
    # Inverse unit quaternion rotates world vector into tracking axes.
    xyz = -q[..., :3]
    t = 2*np.cross(xyz, v)
    return v + q[..., 3:] * t + np.cross(xyz, t)


def hold(t, values, query, max_age):
    """Causal zero-order hold, never extrapolate outside coverage or long gaps."""
    t = np.asarray(t)
    if np.any(np.diff(t) <= 0):
        raise ValueError('Hold timestamps must be strictly increasing')
    i = np.searchsorted(t, query, side='right') - 1
    j = np.clip(i, 0, len(t)-1)
    valid = (i >= 0) & (query <= t[-1]) & (query-t[j] <= max_age)
    return np.asarray(values)[j], valid


def fit_response(ct, command, t, measured, lags, max_age):
    xs, masks = zip(*(hold(ct, command, t-lag, max_age) for lag in lags))
    keep = np.logical_and.reduce(masks) & np.isfinite(measured)
    if np.sum(keep) < 3:
        raise ValueError('Insufficient common samples')
    y = measured[keep]
    profile = []
    for lag, x in zip(lags, xs):
        design = np.column_stack((x[keep], np.ones(len(y))))
        if np.linalg.matrix_rank(design) < 2:
            raise ValueError('No command excitation for gain and offset')
        gain, offset = np.linalg.lstsq(design, y, rcond=None)[0]
        residual = y-design @ np.array([gain, offset])
        profile.append({'lag_s': float(lag), 'gain': float(gain), 'offset_m_s': float(offset),
                        'rmse_m_s': float(np.sqrt(np.mean(residual**2))),
                        'mae_m_s': float(np.mean(abs(residual)))})
    best = min(profile, key=lambda row: row['rmse_m_s'])
    selected = int(np.argmin([p['rmse_m_s'] for p in profile]))
    prediction = best['gain'] * xs[selected][keep] + best['offset_m_s']
    summary = {'sample_count': len(y), 'fit_interval_s': [float(t[keep][0]), float(t[keep][-1])],
               'mean_baseline_rmse_m_s': float(np.std(y)),
               'identity_command_rmse_m_s': float(np.sqrt(np.mean((y-xs[0][keep])**2))),
               'no_delay_affine': profile[0], 'delay_affine': best,
               'optimum_at_search_boundary': selected in (0, len(profile)-1),
               'scoring': 'same-run development residuals; serially correlated samples; no held-out claim'}
    return summary, profile, keep, xs[0][keep], prediction


def inspect(bag):
    from rosbags.highlevel import AnyReader
    rows = defaultdict(list)
    ts, headers, offsets = (defaultdict(list) for _ in range(3))
    frames, children, types = (defaultdict(set) for _ in range(3))
    definitions, settings = {}, {}
    with AnyReader([bag]) as reader:
        start = reader.start_time
        for c in reader.connections:
            types[c.topic].add(c.msgtype)
            if c.topic == '/sensors/core':
                definitions['vesc'] = c.msgdef.data
        for c, ns, raw in reader.messages():
            topic = c.topic
            ts[topic].append(ns)
            m = reader.deserialize(raw, c.msgtype)
            t = (ns-start)/1e9
            if hasattr(m, 'header'):
                h = m.header.stamp.sec*10**9+m.header.stamp.nanosec
                headers[topic].append(h)
                offsets[topic].append((h-ns)/1e9)
                frames[topic].add(m.header.frame_id)
            if hasattr(m, 'child_frame_id'):
                children[topic].add(m.child_frame_id)
            if topic == '/tf':
                for transform in m.transforms:
                    frames[topic].add(transform.header.frame_id)
                    children[topic].add(transform.child_frame_id)
            if topic == CMD:
                rows[topic].append([t, m.linear.x, m.linear.y, m.linear.z, m.angular.x, m.angular.y, m.angular.z])
            elif topic == CAR+'pose':
                q = m.pose.orientation
                rows[topic].append([t, (h-start)/1e9, q.x, q.y, q.z, q.w])
            elif topic in (CAR+'twist', CAR+'accel'):
                v, w = m.twist.linear, m.twist.angular
                rows[topic].append([t, (h-start)/1e9, v.x, v.y, v.z, w.x, w.y, w.z])
            elif topic in ('/commands/servo/position', '/sensors/servo_position_command', '/commands/motor/speed', '/emergency_flag'):
                rows[topic].append([t, float(m.data)])
            elif topic == '/sensors/core':
                s = m.state
                rows[topic].append([t, s.speed, s.voltage_input, s.current_motor, s.fault_code])
            elif topic == '/urg_node/parameter_updates':
                settings = {item.name: item.value for group in (m.bools, m.ints, m.strs, m.doubles) for item in group}
    inventory = {k: {'types': sorted(types[k]), 'bag_time': timing(v),
                     'header_time': timing(headers[k]), 'header_minus_bag_s': stats(offsets[k]),
                     'frames': sorted(frames[k]), 'child_frames': sorted(children[k]),
                     'units': [UNITS[typ] for typ in sorted(types[k])],
                     'calibration': 'No calibration certificate provided in source README; laser settings reported separately'}
                 for k, v in sorted(ts.items())}
    return inventory, {k: np.asarray(v) for k, v in rows.items()}, settings, definitions


def analyze(bag, output, provenance):
    source = json.loads(provenance.read_text())
    digest = hashlib.sha256(bag.read_bytes()).hexdigest()
    if digest != source['development_bag']['sha256']:
        raise ValueError('This study only accepts the pinned development bag')
    inventory, rows, settings, definitions = inspect(bag)
    pose, twist, cmd = rows[CAR+'pose'], rows[CAR+'twist'], rows[CMD]
    # Match orientation to twist on their shared header clock; no clock-offset fit.
    q, valid = hold(pose[:, 1], pose[:, 2:], twist[:, 1], .05)
    body = world_to_tracking(q, twist[:, 2:5])
    t, forward = twist[valid, 0], body[valid, 0]
    lags = np.arange(101)/100
    result, profile, keep, command, prediction = fit_response(cmd[:, 0], cmd[:, 1], t, forward, lags, .05)
    emergency, known = hold(rows['/emergency_flag'][:, 0], rows['/emergency_flag'][:, 1], t[keep], .05)
    result['emergency_flag_fraction'] = float(emergency[known].mean())
    result['emergency_flag_unknown_count'] = int(np.sum(~known))
    selected = np.flatnonzero(valid)[np.flatnonzero(keep)[len(command)//2]]
    vesc = rows['/sensors/core']
    result.update({
        'source_file': 'source.json', 'bag_sha256_verified': digest,
        'environment': {'python': platform.python_version(), 'packages': {name: importlib.metadata.version(name) for name in ('numpy', 'rosbags', 'matplotlib')}},
        'method': {'target': 'Vicon tracking-frame forward velocity, assuming tracking x follows vehicle forward',
                   'time': 'bag recording time for command-response; shared header time for pose/twist rotation',
                   'orientation': 'most recent pose at twist header time; normalized quaternion; maximum age 0.05 s',
                   'command': '/cmd_vel.linear.x; SI m/s assumed from ROS conventions and dataset README',
                   'delay_search': '0 to 1 s inclusive at 0.01 s; causal command hold; maximum age 0.05 s',
                   'comparison': 'All lag candidates and baselines use identical samples valid at every lag',
                   'selection': 'Smallest bag by metadata size, before inspecting motion; development only',
                   'gates': 'None; exploratory estimation only'},
        'excluded_twists_without_recent_pose': int(np.sum(~valid)),
        'excluded_response_samples': int(np.sum(~keep)),
        'excitation': {'command_forward_m_s': stats(cmd[:, 1]), 'command_angular_z_raw': stats(cmd[:, 6]),
                       'vicon_world_angular_z_raw': stats(twist[:, 7]), 'tracking_forward_m_s': stats(body[valid, 0]),
                       'tracking_lateral_m_s': stats(body[valid, 1])},
        'servo_command_echo': {'same_sequence_after_initial_value': bool(np.array_equal(rows['/commands/servo/position'][:, 1], rows['/sensors/servo_position_command'][1:, 1]))},
        'vesc_health': {'voltage_input_V': stats(vesc[:, 2]), 'speed_electrical_rpm': stats(vesc[:, 1]),
                        'fault_codes': sorted(map(int, set(vesc[:, 4]))),
                        'fault_codes_outside_embedded_enum': int(np.sum(~np.isin(vesc[:, 4], np.arange(7))))},
        'laser_settings': settings,
        'owner_frame_exercise': {'quaternion_xyzw': q[selected].tolist(), 'world_velocity_m_s': twist[selected, 2:5].tolist(),
                                 'tracking_velocity_m_s': body[selected].tolist()},
        'limits': ['No measured steering angle or IMU message found; servo topics are commands.',
                   'VESC telemetry fails basic plausibility checks; no electrical-RPM to road-speed calibration supplied.',
                   'Vicon scale, tracking-to-car alignment, lever arm, differentiation and clock synchronization are uncalibrated here.',
                   'Fitted delay includes transport, recording, tracking processing, controller and drivetrain response.',
                   'Command response includes emergency intervention; emergency and steering activity can confound a scalar fit.',
                   'No tire parameters, final holdouts, owner-car measurements or structural load limits are established.']})
    output.mkdir(parents=True, exist_ok=True)
    for name, content in [('result.json', result), ('inventory.json', inventory), ('delay_profile.json', profile)]:
        (output/name).write_text(json.dumps(content, indent=2, allow_nan=False)+'\n')
    (output/'vesc_message_definition.txt').write_text('\n'.join(line.rstrip() for line in definitions['vesc'].splitlines())+'\n')
    # Motion only: no world positions, scans, waypoints or session logs exported.
    np.savetxt(output/'comparison.csv', np.column_stack((t[keep], command, forward[keep], prediction)),
               delimiter=',', header='elapsed_s,command_forward_m_s,tracking_forward_m_s,delay_affine_m_s', comments='', fmt='%.9g')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), constrained_layout=True)
    for a, label in [(command, 'Command'), (forward[keep], 'Vicon in tracking axes'), (prediction, 'Delay + affine fit')]:
        # Break lines at missing intervals instead of drawing across exclusions.
        gaps = np.flatnonzero(np.diff(t[keep]) > .05)+1
        axes[0].plot(np.insert(t[keep], gaps, np.nan), np.insert(a, gaps, np.nan), label=label, linewidth=.8)
    axes[0].set(xlabel='Bag elapsed time (s)', ylabel='Forward velocity (m/s)', title='Public development run: fitted and scored on the same run')
    axes[0].legend(loc='upper right', fontsize=8)
    axes[1].plot(lags, [p['rmse_m_s'] for p in profile])
    axes[1].axhline(result['no_delay_affine']['rmse_m_s'], linestyle='--', color='gray', label='No-delay affine baseline')
    axes[1].set(xlabel='Apparent delay on recording clock (s)', ylabel='Development RMSE (m/s)')
    axes[1].legend()
    fig.savefig(output/'comparison.png', dpi=140)
    plt.close(fig)
    print(json.dumps({k: result[k] for k in ('sample_count', 'no_delay_affine', 'delay_affine', 'emergency_flag_fraction')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bag', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=Path('runs/real_command_response/source.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    analyze(args.bag, args.output, args.source)
