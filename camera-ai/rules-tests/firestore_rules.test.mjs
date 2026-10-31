// Kiem tra config/firestore.rules tren Firestore emulator (`npm test`, can Java 21).
import { readFileSync } from 'node:fs';
import { after, before, beforeEach, describe, test } from 'node:test';
import { assertFails, assertSucceeds, initializeTestEnvironment } from '@firebase/rules-unit-testing';
import { collection, deleteDoc, doc, getDoc, getDocs, query, setDoc, setLogLevel, updateDoc, where } from 'firebase/firestore';

setLogLevel('error'); // assertFails mong doi PERMISSION_DENIED, khong in canh bao cho tung lan

const NOW = new Date('2026-10-02T00:30:00Z');
const RESULT = {
  session_id: 's1',
  camera_id: 'cam-1',
  captured_at: NOW,
  monitoring_status: 'running',
  result_map: { S1: { concentration: 80, interaction: 0, status: 'focused' } },
  expire_at: NOW,
};
const EVALUATION = {
  session_id: 's1',
  seat_id: 'S2',
  captured_at: NOW,
  concentration: 70,
  avg_concentration: 75,
  distraction: 1,
  observed_sec: 600,
  expire_at: NOW,
};
const ALERT = { session_id: 's1', seat_id: 'S1', type: 'head_drop', start_sec: 12.5, duration_sec: 6, expire_at: NOW };
const HEARTBEAT = {
  class_id: 'c1',
  online: true,
  status: 'monitoring',
  session_id: 's1',
  fps: 5,
  camera_ok: true,
  last_frame_at: NOW,
  updated_at: NOW,
};
const REGIONS = { class_id: 'c1', image_width: 1280, image_height: 720, seats: { S01: [100, 100, 300, 300] } };
const CAMERA_CONFIG = { class_id: 'c1', source: 'rtsp://admin:pw@10.0.0.5:554/stream1', updated_by: 'admin1' };

let env;
const db = {
  admin: () => env.authenticatedContext('admin1').firestore(),
  teacher: () => env.authenticatedContext('t1').firestore(),
  otherTeacher: () => env.authenticatedContext('t2').firestore(),
  parent: () => env.authenticatedContext('p1').firestore(),
  anonymous: () => env.unauthenticatedContext().firestore(),
  edge: () => env.authenticatedContext('edge-1', { role: 'edge', camera_id: 'cam-1' }).firestore(),
  otherEdge: () => env.authenticatedContext('edge-2', { role: 'edge', camera_id: 'cam-2' }).firestore(),
};

before(async () => {
  env = await initializeTestEnvironment({
    projectId: 'demo-camera-ai',
    firestore: { rules: readFileSync(new URL('../config/firestore.rules', import.meta.url), 'utf8') },
  });
});

after(() => env.cleanup());

beforeEach(async () => {
  await env.clearFirestore();
  await env.withSecurityRulesDisabled(async (context) => {
    const seed = context.firestore();
    const docs = {
      'admins/admin1': { school_name: 'THPT Phan Chau Trinh' },
      'teachers/t1': { name: 'Teacher One' },
      'teachers/t2': { name: 'Teacher Two' },
      'parents/p1': { name: 'Parent One' },
      'students2/st1': { full_name: 'Student One', parent_id: 'p1' },
      'students2/st2': { full_name: 'Student Two', parent_id: 'p2' },
      'classes2/c1': {
        class_name: '11B2',
        teacher_id: 't1',
        camera_id: 'cam-1',
        row_count: 2,
        column_count: 2,
        seat_map: { S01: { seat_id: 'S01', row: 1, column: 1, student_id: 'st1', status: 'occupied' } },
      },
      'classes2/c2': { class_name: '11B3', teacher_id: 't2', camera_id: 'cam-2', row_count: 1, column_count: 1, seat_map: {} },
      'cameras/cam-1': { camera_name: 'cam-1', room_name: 'P201', ip_address: '10.0.0.5', rtsp_port: '554' },
      'sessions/s1/monitored_students/S01': { student_id: 'st1', row: 1, column: 1 },
      'sessions/s1': { class_id: 'c1', teacher_id: 't1', subject: 'Toan', status: 'scheduled' },
      'sessions/s2': { class_id: 'c2', teacher_id: 't2', subject: 'Van', status: 'running' },
      'session_results/s1': RESULT,
      'session_evaluations/s1_S1': { ...EVALUATION, seat_id: 'S1' },
      'sessions/s1/alerts/a1': ALERT,
      'edge_nodes/cam-1': HEARTBEAT,
      'seat_regions/cam-1': REGIONS,
      'camera_configs/cam-1': CAMERA_CONFIG,
      'students2/st1/reports/s1': { session_id: 's1', avg_concentration: 80, partial: false },
      'students2/st2/reports/s1': { session_id: 's1', avg_concentration: 60, partial: false },
    };
    for (const [path, data] of Object.entries(docs)) await setDoc(doc(seed, path), data);
  });
});

describe('sessions/{s}', () => {
  test('teachers read their own sessions through teacher_id queries, the edge node through class_id', async () => {
    await assertSucceeds(getDoc(doc(db.teacher(), 'sessions/s1')));
    await assertSucceeds(getDocs(query(collection(db.teacher(), 'sessions'), where('teacher_id', '==', 't1'))));
    await assertFails(getDocs(collection(db.teacher(), 'sessions')));
    await assertFails(getDoc(doc(db.otherTeacher(), 'sessions/s1')));
    await assertFails(getDoc(doc(db.parent(), 'sessions/s1')));
    await assertSucceeds(getDocs(query(collection(db.edge(), 'sessions'), where('class_id', '==', 'c1'))));
    await assertFails(getDoc(doc(db.edge(), 'sessions/s2')));
    await assertSucceeds(getDocs(collection(db.admin(), 'sessions')));
  });

  test('the teacher starts, pauses, resumes and ends a session, nothing else', async () => {
    const session = doc(db.teacher(), 'sessions/s1');
    await assertFails(updateDoc(session, { status: 'completed' }));
    await assertFails(updateDoc(session, { status: 'running', subject: 'Ly' }));
    await assertSucceeds(updateDoc(session, { status: 'running', started_at: NOW }));
    await assertSucceeds(updateDoc(session, { status: 'paused' }));
    await assertSucceeds(updateDoc(session, { status: 'running' }));
    await assertFails(updateDoc(session, { status: 'scheduled' }));
    await assertFails(updateDoc(session, { status: 'ended', ended_at: NOW }));
    await assertSucceeds(updateDoc(session, { status: 'completed', ended_at: NOW }));
  });

  test('clients never create or delete sessions, and only the session teacher updates them', async () => {
    await assertFails(setDoc(doc(db.teacher(), 'sessions/s3'), { class_id: 'c1', teacher_id: 't1', status: 'scheduled' }));
    await assertFails(deleteDoc(doc(db.teacher(), 'sessions/s1')));
    await assertFails(updateDoc(doc(db.otherTeacher(), 'sessions/s1'), { status: 'running' }));
    await assertFails(updateDoc(doc(db.edge(), 'sessions/s1'), { status: 'running' }));
  });
});

describe('classes2/{c}, cameras and monitored students', () => {
  test('the edge node finds and reads only the class whose camera_id is its own, parents never read seat maps', async () => {
    await assertSucceeds(getDocs(query(collection(db.edge(), 'classes2'), where('camera_id', '==', 'cam-1'))));
    await assertFails(getDocs(collection(db.edge(), 'classes2')));
    await assertSucceeds(getDoc(doc(db.edge(), 'classes2/c1')));
    await assertFails(getDoc(doc(db.otherEdge(), 'classes2/c1')));
    await assertFails(getDoc(doc(db.parent(), 'classes2/c1')));
    await assertFails(getDoc(doc(db.anonymous(), 'classes2/c1')));
    await assertSucceeds(getDoc(doc(db.otherTeacher(), 'classes2/c1')));
  });

  test('a camera moved to another class on the web admin follows it without a new token', async () => {
    await env.withSecurityRulesDisabled(async (context) => {
      await updateDoc(doc(context.firestore(), 'classes2/c1'), { camera_id: 'cam-2' });
    });
    await assertSucceeds(getDocs(query(collection(db.otherEdge(), 'sessions'), where('class_id', '==', 'c1'))));
    await assertFails(getDocs(query(collection(db.edge(), 'sessions'), where('class_id', '==', 'c1'))));
  });

  test('staff read cameras, which never hold the RTSP URL; nobody writes them from a client', async () => {
    await assertSucceeds(getDoc(doc(db.teacher(), 'cameras/cam-1')));
    await assertSucceeds(getDoc(doc(db.admin(), 'cameras/cam-1')));
    await assertFails(getDoc(doc(db.parent(), 'cameras/cam-1')));
    await assertFails(getDoc(doc(db.anonymous(), 'cameras/cam-1')));
    await assertFails(setDoc(doc(db.admin(), 'cameras/cam-2'), { camera_name: 'cam-2', room_name: 'P202' }));
  });

  test('only the homeroom teacher or an admin changes the seat map, and nothing else', async () => {
    const seatMap = { S01: { seat_id: 'S01', row: 1, column: 1, student_id: 'st2', status: 'occupied' } };
    await assertSucceeds(updateDoc(doc(db.teacher(), 'classes2/c1'), { seat_map: seatMap, updated_at: NOW }));
    await assertFails(updateDoc(doc(db.teacher(), 'classes2/c1'), { class_name: '12A1' }));
    await assertFails(updateDoc(doc(db.otherTeacher(), 'classes2/c1'), { seat_map: seatMap }));
    await assertFails(updateDoc(doc(db.edge(), 'classes2/c1'), { seat_map: seatMap }));
    await assertSucceeds(updateDoc(doc(db.admin(), 'classes2/c1'), { seat_map: {} }));
  });

  test('the monitored students of a session are for its teacher and admins only', async () => {
    const seat = 'sessions/s1/monitored_students/S01';
    await assertSucceeds(getDoc(doc(db.teacher(), seat)));
    await assertSucceeds(getDocs(collection(db.admin(), 'sessions/s1/monitored_students')));
    for (const as of [db.otherTeacher, db.parent, db.edge, db.anonymous]) {
      await assertFails(getDoc(doc(as(), seat)));
    }
    await assertFails(setDoc(doc(db.teacher(), seat), { student_id: 'st2', row: 1, column: 1 }));
  });
});

describe('edge output', () => {
  test('session_results: the session teacher reads, only its class edge node writes the allowlist', async () => {
    await assertSucceeds(getDoc(doc(db.teacher(), 'session_results/s1')));
    await assertFails(getDoc(doc(db.otherTeacher(), 'session_results/s1')));
    await assertFails(getDoc(doc(db.parent(), 'session_results/s1')));
    await assertSucceeds(setDoc(doc(db.edge(), 'session_results/s1'), { ...RESULT, monitoring_status: 'completed' }));
    await assertFails(setDoc(doc(db.edge(), 'session_results/s1'), { ...RESULT, camera_id: 'cam-9' }));
    await assertFails(setDoc(doc(db.edge(), 'session_results/s1'), { ...RESULT, student_id: 'st1' }));
    await assertFails(setDoc(doc(db.otherEdge(), 'session_results/s1'), { ...RESULT, camera_id: 'cam-2' }));
    await assertFails(setDoc(doc(db.teacher(), 'session_results/s1'), RESULT));
  });

  test('session_evaluations: teachers query by session_id, the edge node writes {session}_{seat}', async () => {
    await assertSucceeds(getDoc(doc(db.teacher(), 'session_evaluations/s1_S1')));
    await assertSucceeds(getDocs(query(collection(db.teacher(), 'session_evaluations'), where('session_id', '==', 's1'))));
    await assertFails(getDocs(collection(db.teacher(), 'session_evaluations')));
    await assertFails(getDoc(doc(db.parent(), 'session_evaluations/s1_S1')));
    await assertSucceeds(setDoc(doc(db.edge(), 'session_evaluations/s1_S2'), EVALUATION));
    await assertFails(setDoc(doc(db.edge(), 'session_evaluations/s1_S9'), EVALUATION));
    await assertFails(setDoc(doc(db.edge(), 'session_evaluations/s1_S2'), { ...EVALUATION, student_id: 'st1' }));
    await assertFails(setDoc(doc(db.otherEdge(), 'session_evaluations/s1_S2'), EVALUATION));
  });

  test('session_windows: only the class edge node appends the allowlist, no client reads them', async () => {
    const window = {
      session_id: 's1',
      camera_id: 'cam-1',
      run: '0a1b2c3d',
      seq: 0,
      start_sec: 0,
      end_sec: 10,
      captured_at: NOW,
      monitoring_status: 'running',
      seats: { S01: { normal_sec: 9.5, slumping_sec: 0, head_drop_sec: 0, last_seen_sec: 9.5, last_state: 'normal', last_behaviour_sec: null, alerts: {} } },
      expire_at: NOW,
    };
    const path = 'session_windows/s1_0a1b2c3d_00000';
    await assertSucceeds(setDoc(doc(db.edge(), path), window));
    await assertFails(setDoc(doc(db.edge(), 'session_windows/s1_other_00000'), window));
    await assertFails(setDoc(doc(db.edge(), 'session_windows/s1_0a1b2c3d_00001'), { ...window, seq: 1, keypoints: [] }));
    await assertFails(setDoc(doc(db.otherEdge(), path.replace('00000', '00002')), { ...window, camera_id: 'cam-2' }));
    for (const reader of [db.admin(), db.teacher(), db.parent(), db.anonymous()]) {
      await assertFails(getDoc(doc(reader, path)));
    }
  });

  test('alerts: the edge node creates them, the session teacher only acknowledges or dismisses', async () => {
    await assertSucceeds(setDoc(doc(db.edge(), 'sessions/s1/alerts/a2'), ALERT));
    await assertFails(setDoc(doc(db.edge(), 'sessions/s1/alerts/a3'), { ...ALERT, type: 'phone_use' }));
    await assertFails(setDoc(doc(db.teacher(), 'sessions/s1/alerts/a4'), ALERT));
    const alert = doc(db.teacher(), 'sessions/s1/alerts/a1');
    await assertSucceeds(getDoc(alert));
    await assertSucceeds(updateDoc(alert, { status: 'acknowledged', handled_by: 't1', handled_at: NOW }));
    await assertSucceeds(updateDoc(alert, { status: 'dismissed', handled_by: 't1' }));
    await assertFails(updateDoc(alert, { status: 'acknowledged', handled_by: 't2' }));
    await assertFails(updateDoc(alert, { status: 'resolved', handled_by: 't1' }));
    await assertFails(updateDoc(alert, { duration_sec: 0, handled_by: 't1' }));
    await assertFails(getDoc(doc(db.parent(), 'sessions/s1/alerts/a1')));
  });

  test('edge_nodes: each edge node writes only its own heartbeat, staff read it', async () => {
    await assertSucceeds(setDoc(doc(db.edge(), 'edge_nodes/cam-1'), { ...HEARTBEAT, status: 'idle' }));
    await assertFails(setDoc(doc(db.edge(), 'edge_nodes/cam-2'), HEARTBEAT));
    await assertFails(setDoc(doc(db.edge(), 'edge_nodes/cam-1'), { ...HEARTBEAT, class_id: 'c2' }));
    await assertFails(setDoc(doc(db.teacher(), 'edge_nodes/cam-1'), HEARTBEAT));
    await assertSucceeds(getDoc(doc(db.teacher(), 'edge_nodes/cam-1')));
    await assertFails(getDoc(doc(db.parent(), 'edge_nodes/cam-1')));
  });
});

describe('seat_regions/{camera_id}', () => {
  test('admins draw seat regions, only that camera\'s edge node reads them, extra fields are rejected', async () => {
    await assertSucceeds(setDoc(doc(db.admin(), 'seat_regions/cam-2'), { ...REGIONS, updated_by: 'admin1' }));
    await assertFails(setDoc(doc(db.admin(), 'seat_regions/cam-2'), { ...REGIONS, student_id: 'st1' }));
    await assertSucceeds(getDoc(doc(db.edge(), 'seat_regions/cam-1')));
    await assertFails(getDoc(doc(db.edge(), 'seat_regions/cam-2')));
    await assertFails(getDoc(doc(db.teacher(), 'seat_regions/cam-1')));
    await assertFails(setDoc(doc(db.edge(), 'seat_regions/cam-1'), REGIONS));
    await assertFails(deleteDoc(doc(db.teacher(), 'seat_regions/cam-1')));
    await assertSucceeds(deleteDoc(doc(db.admin(), 'seat_regions/cam-1')));
  });
});

describe('camera_configs/{camera_id}', () => {
  test('only that camera\'s edge node reads its class and RTSP URL; no client writes it, admins included', async () => {
    await assertSucceeds(getDoc(doc(db.edge(), 'camera_configs/cam-1')));
    await assertFails(getDoc(doc(db.otherEdge(), 'camera_configs/cam-1')));
    await assertFails(getDoc(doc(db.admin(), 'camera_configs/cam-1')));
    await assertFails(getDoc(doc(db.teacher(), 'camera_configs/cam-1')));
    await assertFails(getDoc(doc(db.parent(), 'camera_configs/cam-1')));
    await assertFails(setDoc(doc(db.admin(), 'camera_configs/cam-2'), CAMERA_CONFIG));
    await assertFails(setDoc(doc(db.edge(), 'camera_configs/cam-1'), CAMERA_CONFIG));
  });
});

describe('students2/{sid} and its reports', () => {
  test('a parent finds and reads only their own children, staff read every student, nobody writes from a client', async () => {
    await assertSucceeds(getDocs(query(collection(db.parent(), 'students2'), where('parent_id', '==', 'p1'))));
    await assertSucceeds(getDoc(doc(db.parent(), 'students2/st1')));
    await assertFails(getDoc(doc(db.parent(), 'students2/st2')));
    await assertFails(getDocs(collection(db.parent(), 'students2')));
    await assertSucceeds(getDoc(doc(db.teacher(), 'students2/st2')));
    await assertFails(getDoc(doc(db.edge(), 'students2/st1')));
    await assertFails(updateDoc(doc(db.parent(), 'students2/st1'), { full_name: 'X' }));
  });

  test('a parent reads only their own child\'s reports, and nobody writes them from a client', async () => {
    await assertSucceeds(getDoc(doc(db.parent(), 'students2/st1/reports/s1')));
    await assertSucceeds(getDocs(collection(db.parent(), 'students2/st1/reports')));
    await assertFails(getDoc(doc(db.parent(), 'students2/st2/reports/s1')));
    await assertFails(getDoc(doc(db.teacher(), 'students2/st1/reports/s1')));
    await assertSucceeds(getDoc(doc(db.admin(), 'students2/st1/reports/s1')));
    await assertFails(setDoc(doc(db.parent(), 'students2/st1/reports/s2'), { avg_concentration: 100 }));
  });
});
