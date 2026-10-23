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

let env;
const db = {
  admin: () => env.authenticatedContext('admin1').firestore(),
  teacher: () => env.authenticatedContext('t1').firestore(),
  otherTeacher: () => env.authenticatedContext('t2').firestore(),
  parent: () => env.authenticatedContext('p1').firestore(),
  anonymous: () => env.unauthenticatedContext().firestore(),
  edge: () => env.authenticatedContext('edge-c1', { role: 'edge', class_id: 'c1', camera_id: 'cam-1' }).firestore(),
  otherEdge: () => env.authenticatedContext('edge-c2', { role: 'edge', class_id: 'c2', camera_id: 'cam-2' }).firestore(),
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
        row_count: 2,
        column_count: 2,
        seat_map: { S01: { seat_id: 'S01', row: 1, column: 1, student_id: 'st1', status: 'occupied' } },
      },
      'session_rosters/s1': { class_id: 'c1', seats: { S01: 'st1' } },
      'sessions/s1': { class_id: 'c1', teacher_id: 't1', subject: 'Toan', status: 'scheduled' },
      'sessions/s2': { class_id: 'c2', teacher_id: 't2', subject: 'Van', status: 'running' },
      'session_results/s1': RESULT,
      'session_evaluations/s1_S1': { ...EVALUATION, seat_id: 'S1' },
      'sessions/s1/alerts/a1': ALERT,
      'edge_nodes/cam-1': HEARTBEAT,
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

describe('classes2/{c} and session rosters', () => {
  test('the edge node reads only its own class, parents never read seat maps', async () => {
    await assertSucceeds(getDoc(doc(db.edge(), 'classes2/c1')));
    await assertFails(getDoc(doc(db.otherEdge(), 'classes2/c1')));
    await assertFails(getDoc(doc(db.parent(), 'classes2/c1')));
    await assertFails(getDoc(doc(db.anonymous(), 'classes2/c1')));
    await assertSucceeds(getDoc(doc(db.otherTeacher(), 'classes2/c1')));
  });

  test('only the homeroom teacher or an admin changes the seat map, and nothing else', async () => {
    const seatMap = { S01: { seat_id: 'S01', row: 1, column: 1, student_id: 'st2', status: 'occupied' } };
    await assertSucceeds(updateDoc(doc(db.teacher(), 'classes2/c1'), { seat_map: seatMap, updated_at: NOW }));
    await assertFails(updateDoc(doc(db.teacher(), 'classes2/c1'), { class_name: '12A1' }));
    await assertFails(updateDoc(doc(db.otherTeacher(), 'classes2/c1'), { seat_map: seatMap }));
    await assertFails(updateDoc(doc(db.edge(), 'classes2/c1'), { seat_map: seatMap }));
    await assertSucceeds(updateDoc(doc(db.admin(), 'classes2/c1'), { seat_map: {} }));
  });

  test('the frozen roster of a session is for its teacher and admins only', async () => {
    await assertSucceeds(getDoc(doc(db.teacher(), 'session_rosters/s1')));
    await assertSucceeds(getDoc(doc(db.admin(), 'session_rosters/s1')));
    for (const as of [db.otherTeacher, db.parent, db.edge, db.anonymous]) {
      await assertFails(getDoc(doc(as(), 'session_rosters/s1')));
    }
    await assertFails(setDoc(doc(db.teacher(), 'session_rosters/s1'), { class_id: 'c1', seats: {} }));
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
