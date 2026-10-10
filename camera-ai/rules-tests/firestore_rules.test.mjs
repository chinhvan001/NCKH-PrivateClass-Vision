// Kiem tra config/firestore.rules tren Firestore emulator (`npm test`, can Java 21).
import { readFileSync } from 'node:fs';
import { after, before, beforeEach, describe, test } from 'node:test';
import { assertFails, assertSucceeds, initializeTestEnvironment } from '@firebase/rules-unit-testing';
import { collection, deleteDoc, doc, getDoc, getDocs, query, setDoc, setLogLevel, updateDoc, where } from 'firebase/firestore';

setLogLevel('error'); // assertFails mong doi PERMISSION_DENIED, khong in canh bao cho tung lan

const GRID = {
  schema_version: 1,
  config_version: 1,
  camera_id: 'c1',
  classroom_id: 'c1',
  camera_angle_type: 'frontal',
  seats: [{ seat_id: 'A1', center_x: 120, center_y: 300 }],
  pose: {},
};

let env;
const db = {
  admin: () => env.authenticatedContext('admin1', { role: 'admin' }).firestore(),
  teacher: () => env.authenticatedContext('t1', { role: 'teacher' }).firestore(),
  otherTeacher: () => env.authenticatedContext('t2', { role: 'teacher' }).firestore(),
  parent: () => env.authenticatedContext('p1', { role: 'parent' }).firestore(),
  anonymous: () => env.unauthenticatedContext().firestore(),
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
    await setDoc(doc(seed, 'classrooms/c1'), { teacher_uids: ['t1'], rtsp_url: 'rtsp://admin:secret@10.0.0.5/stream' });
    await setDoc(doc(seed, 'classrooms/c2'), { teacher_uids: ['t2'] });
    await setDoc(doc(seed, 'classrooms/c1/camera_configs/c1'), GRID);
    await setDoc(doc(seed, 'classrooms/c1/edge_nodes/c1'), { online: true, status: 'idle' });
    await setDoc(doc(seed, 'sessions/s1'), { classroom_id: 'c1', status: 'scheduled', subject: 'Toan' });
    await setDoc(doc(seed, 'sessions/s2'), { classroom_id: 'c2', status: 'live', subject: 'Van' });
    await setDoc(doc(seed, 'sessions/s1/engagement/r1'), { seat_id: 'A1', observed_at_sec: 10 });
    await setDoc(doc(seed, 'sessions/s1/summaries/c1'), { session_id: 's1', status: 'running' });
    await setDoc(doc(seed, 'sessions/s1/alerts/a1'), {
      session_id: 's1',
      seat_id: 'A1',
      type: 'head_drop',
      start_sec: 5,
      duration_sec: 6,
    });
  });
});

describe('classrooms/{c}', () => {
  test('no client reads the classroom document, which holds the camera URL', async () => {
    for (const as of Object.values(db)) await assertFails(getDoc(doc(as(), 'classrooms/c1')));
  });
});

describe('classrooms/{c}/camera_configs/{cam}', () => {
  const path = 'classrooms/c1/camera_configs/c1';

  test('admin and the classroom teacher read the seat grid, nobody else', async () => {
    await assertSucceeds(getDoc(doc(db.admin(), path)));
    await assertSucceeds(getDoc(doc(db.teacher(), path)));
    for (const as of [db.otherTeacher, db.parent, db.anonymous]) await assertFails(getDoc(doc(as(), path)));
  });

  test('the classroom teacher writes allowlisted fields for this classroom only', async () => {
    await assertSucceeds(setDoc(doc(db.teacher(), path), { ...GRID, config_version: 2 }));
    await assertFails(setDoc(doc(db.teacher(), path), { ...GRID, rtsp_url: 'rtsp://cam' }));
    await assertFails(setDoc(doc(db.teacher(), path), { ...GRID, classroom_id: 'c2' }));
    await assertFails(setDoc(doc(db.otherTeacher(), path), GRID));
  });

  test('only admin deletes a seat grid', async () => {
    await assertFails(deleteDoc(doc(db.teacher(), path)));
    await assertSucceeds(deleteDoc(doc(db.admin(), path)));
  });
});

describe('classrooms/{c}/edge_nodes/{cam}', () => {
  test('admin and the classroom teacher read the heartbeat, no client writes it', async () => {
    const path = 'classrooms/c1/edge_nodes/c1';
    await assertSucceeds(getDoc(doc(db.admin(), path)));
    await assertSucceeds(getDoc(doc(db.teacher(), path)));
    await assertFails(getDoc(doc(db.parent(), path)));
    await assertFails(setDoc(doc(db.admin(), path), { online: false }));
  });
});

describe('sessions/{s}', () => {
  test('the classroom teacher reads its sessions, and queries must filter on classroom_id', async () => {
    await assertSucceeds(getDoc(doc(db.teacher(), 'sessions/s1')));
    await assertSucceeds(getDocs(query(collection(db.teacher(), 'sessions'), where('classroom_id', '==', 'c1'))));
    await assertFails(getDocs(collection(db.teacher(), 'sessions')));
    await assertFails(getDoc(doc(db.teacher(), 'sessions/s2')));
    await assertFails(getDoc(doc(db.parent(), 'sessions/s1')));
    await assertSucceeds(getDocs(collection(db.admin(), 'sessions')));
  });

  test('the teacher starts a scheduled session and ends a live one, nothing else', async () => {
    const session = doc(db.teacher(), 'sessions/s1');
    await assertFails(updateDoc(session, { status: 'completed' }));
    await assertFails(updateDoc(session, { status: 'live', subject: 'Ly' }));
    await assertSucceeds(updateDoc(session, { status: 'live' }));
    await assertFails(updateDoc(session, { status: 'scheduled' }));
    await assertSucceeds(updateDoc(session, { status: 'completed' }));
  });

  test('clients never create or delete sessions, and only the classroom teacher updates them', async () => {
    await assertFails(setDoc(doc(db.teacher(), 'sessions/s3'), { classroom_id: 'c1', status: 'scheduled' }));
    await assertFails(deleteDoc(doc(db.teacher(), 'sessions/s1')));
    await assertFails(updateDoc(doc(db.otherTeacher(), 'sessions/s1'), { status: 'live' }));
    await assertFails(updateDoc(doc(db.admin(), 'sessions/s1'), { status: 'live' }));
  });
});

describe('edge output under sessions/{s}', () => {
  test('the classroom teacher reads records and summaries, no client writes them', async () => {
    for (const path of ['sessions/s1/engagement/r1', 'sessions/s1/summaries/c1']) {
      await assertSucceeds(getDoc(doc(db.teacher(), path)));
      await assertSucceeds(getDoc(doc(db.admin(), path)));
      await assertFails(getDoc(doc(db.otherTeacher(), path)));
      await assertFails(getDoc(doc(db.parent(), path)));
      await assertFails(setDoc(doc(db.teacher(), path), { seat_id: 'A1' }));
    }
  });

  test('the classroom teacher only acknowledges or dismisses alerts', async () => {
    const alert = doc(db.teacher(), 'sessions/s1/alerts/a1');
    await assertSucceeds(getDoc(alert));
    await assertSucceeds(updateDoc(alert, { status: 'acknowledged' }));
    await assertSucceeds(updateDoc(alert, { status: 'dismissed' }));
    await assertFails(updateDoc(alert, { status: 'resolved' }));
    await assertFails(updateDoc(alert, { duration_sec: 0 }));
    await assertFails(setDoc(doc(db.teacher(), 'sessions/s1/alerts/a2'), { seat_id: 'A1' }));
    await assertFails(getDoc(doc(db.parent(), 'sessions/s1/alerts/a1')));
  });
});
