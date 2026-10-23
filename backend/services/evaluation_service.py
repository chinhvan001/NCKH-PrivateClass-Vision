import logging
from firebase_admin import firestore

logger = logging.getLogger(__name__)

SESSION_RUNTIME_STATE = {}

class EvaluationService:

    @staticmethod
    def process_camera_capture(session_id: str, captures_data: list):

        db = firestore.client()
        
        session_ref = db.collection("sessions").document(session_id)
        session_doc = session_ref.get()
        if not session_doc.exists:
            return {"success": False, "error": "Session not found"}
        
        session_data = session_doc.to_dict() or {}
        if session_data.get("status") == "ended":
            return {"success": False, "error": "Session has already ended"}

        seat_snapshot = session_data.get("seat_snapshot", {})
        student_to_seat = {}
        for s_id, s_info in seat_snapshot.items():
            if isinstance(s_info, dict) and "student_id" in s_info:
                student_to_seat[s_info["student_id"]] = s_id

        if session_id not in SESSION_RUNTIME_STATE:
            SESSION_RUNTIME_STATE[session_id] = {}

        session_runtime = SESSION_RUNTIME_STATE[session_id]
        processed_results = []

        for item in captures_data:
            student_id = item.get("student_id")
            if not student_id:
                continue

            concentration = item.get("concentration")
            distraction = item.get("distraction")

            if concentration is None or distraction is None:
                logger.warning(f"Rejected capture for student {student_id}: missing concentration or distraction")
                continue

            try:
                conc_val = float(concentration)
                dist_val = float(distraction)
            except (ValueError, TypeError):
                logger.warning(f"Rejected capture for student {student_id}: non-numeric values")
                continue

            if not (0 <= conc_val <= 100) or not (0 <= dist_val <= 100):
                logger.warning(f"Rejected capture for student {student_id}: out of bounds")
                continue

            if abs((conc_val + dist_val) - 100.0) > 0.01:
                logger.warning(f"Rejected capture for student {student_id}: sum != 100")
                continue

            seat_id = student_to_seat.get(student_id, item.get("seat_id", "N/A"))

            if student_id not in session_runtime:
                session_runtime[student_id] = {
                    "concentration_sum": 0.0,
                    "capture_count": 0,
                    "seat_id": seat_id
                }

            student_state = session_runtime[student_id]
            student_state["concentration_sum"] += conc_val
            student_state["capture_count"] += 1

            count = student_state["capture_count"]
            current_avg_conc = student_state["concentration_sum"] / count

            if current_avg_conc >= 80.0:
                status_str = "Tập trung tốt"
            elif current_avg_conc >= 70.0:
                status_str = "Trung bình"
            else:
                status_str = "Cần chú ý"

            processed_results.append({
                "student_id": student_id,
                "seat_id": seat_id,
                "avg_concentration": round(current_avg_conc, 2),
                "status": status_str
            })

        return {
            "success": True,
            "session_id": session_id,
            "students": processed_results
        }

    @staticmethod
    def end_session(session_id: str):
        db = firestore.client()
        session_ref = db.collection("sessions").document(session_id)
        session_doc = session_ref.get()
        
        if not session_doc.exists:
            return {"success": False, "error": "Session not found"}

        session_runtime = SESSION_RUNTIME_STATE.get(session_id, {})
        final_results = []

        try:
            batch = db.batch()
            
            for student_id, state in session_runtime.items():
                capture_count = state.get("capture_count", 0)
                seat_id = state.get("seat_id", "")

                if capture_count > 0:
                    avg_conc = state["concentration_sum"] / capture_count
                else:
                    avg_conc = None

                if avg_conc is None:
                    status_str = "Chưa có dữ liệu"
                elif avg_conc >= 80.0:
                    status_str = "Tập trung tốt"
                elif avg_conc >= 70.0:
                    status_str = "Trung bình"
                else:
                    status_str = "Cần chú ý"

                result_doc_id = f"{session_id}_{student_id}"
                result_ref = db.collection("session_results").document(result_doc_id)
                
                result_data = {
                    "session_id": session_id,
                    "student_id": student_id,
                    "seat_id": seat_id,
                    "avg_concentration": round(avg_conc, 2) if avg_conc is not None else None,
                    "status": status_str,
                    "updated_at": firestore.SERVER_TIMESTAMP
                }
                
                batch.set(result_ref, result_data, merge=True)
                final_results.append(result_data)

            batch.update(session_ref, {"status": "ended", "ended_at": firestore.SERVER_TIMESTAMP})
            batch.commit()

            if session_id in SESSION_RUNTIME_STATE:
                del SESSION_RUNTIME_STATE[session_id]

            return {
                "success": True,
                "session_id": session_id,
                "results": final_results
            }

        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_classes_overview():
        db = firestore.client()
        try:
            sessions_ref = db.collection("sessions").stream()
        except Exception:
            return {"success": True, "data": []}
        
        classes_map = {}

        for doc in sessions_ref:
            session_data = doc.to_dict() or {}
            class_id = session_data.get("class_id")
            subject = session_data.get("subject", "Chưa xác định")
            aggregated_eval = session_data.get("aggregated_evaluation", {})

            if not class_id:
                continue

            class_name = "Lớp học"
            teacher_name = "Giáo viên"
            
            for col_name in ["classes2", "classes", "classrooms"]:
                try:
                    class_doc = db.collection(col_name).document(class_id).get()
                    if class_doc.exists:
                        c_data = class_doc.to_dict() or {}
                        class_name = c_data.get("name") or c_data.get("class_name") or class_name
                        teacher_name = c_data.get("teacher_name") or c_data.get("teacher") or teacher_name
                        break
                except Exception:
                    pass

            if class_id not in classes_map:
                classes_map[class_id] = {
                    "id": class_id,
                    "name": class_name,
                    "subject": subject,
                    "teacher": teacher_name,
                    "total_concentration": 0.0,
                    "record_count": 0
                }

            if isinstance(aggregated_eval, dict):
                for seat_id, captures in aggregated_eval.items():
                    if isinstance(captures, dict):
                        seat_concentrations = []
                        for key, val in captures.items():
                            if isinstance(val, dict) and "avg_concentration" in val:
                                try:
                                    seat_concentrations.append(float(val["avg_concentration"]))
                                except (ValueError, TypeError):
                                    pass
                            elif key == "avg_concentration" or key == "concentration":
                                try:
                                    seat_concentrations.append(float(captures[key]))
                                except (ValueError, TypeError):
                                    pass
                                break
                        
                        if seat_concentrations:
                            avg_seat_conc = sum(seat_concentrations) / len(seat_concentrations)
                            classes_map[class_id]["total_concentration"] += avg_seat_conc
                            classes_map[class_id]["record_count"] += 1

        result_list = []
        for c_id, val in classes_map.items():
            record_count = val.get("record_count", 0)
            total_conc = val.get("total_concentration", 0.0)
            avg_all = (total_conc / record_count) if record_count > 0 else 0.0
            
            if avg_all >= 80.0:
                status = "good"
            elif avg_all >= 70.0:
                status = "stable"
            else:
                status = "attention"

            result_list.append({
                "id": val.get("id", c_id),
                "name": val.get("name", "Lớp học"),
                "subject": val.get("subject", "Chưa xác định"),
                "teacher": val.get("teacher", "Giáo viên"),
                "students": record_count,
                "attention": round(avg_all, 1),
                "status": status
            })

        return {"success": True, "data": result_list}

    @staticmethod
    def get_class_details(class_id: str):
        db = firestore.client()
        
        class_name = "Chi tiết lớp học"
        subject = "Chưa rõ"
        teacher_name = "Chưa rõ"
        classroom = "Chưa rõ"
        seat_map = {}

        # 1. Lấy thông tin từ collection lớp học
        for col_name in ["classes2", "classes", "classrooms"]:
            try:
                class_doc = db.collection(col_name).document(class_id).get()
                if class_doc.exists:
                    c_data = class_doc.to_dict() or {}
                    class_name = c_data.get("class_name") or c_data.get("name") or class_name
                    subject = c_data.get("subject") or subject
                    
                    # Đổi phòng thành lấy trực tiếp từ class_name (ví dụ: "11B2")[cite: 29]
                    classroom = class_name
                    
                    # Tra cứu tên giáo viên từ teacher_id
                    teacher_id = c_data.get("teacher_id")
                    if teacher_id:
                        for t_col in ["teachers", "users"]:
                            t_doc = db.collection(t_col).document(teacher_id).get()
                            if t_doc.exists:
                                t_data = t_doc.to_dict() or {}
                                teacher_name = (
                                    t_data.get("full_name")
                                    or t_data.get("name")
                                    or t_data.get("display_name")
                                    or t_data.get("email")
                                    or teacher_name
                                )
                                break
                    
                    if teacher_name == "Chưa rõ":
                        teacher_name = c_data.get("teacher_name") or c_data.get("teacher") or teacher_name

                    seat_map = c_data.get("seat_map", {})
                    break
            except Exception:
                pass

        # 2. Truy vấn bổ sung từ collection sessions nếu thiếu thông tin môn học hoặc giáo viên
        try:
            sessions_ref = list(db.collection("sessions").where("class_id", "==", class_id).stream())
            if sessions_ref:
                for s_doc in sessions_ref:
                    s_data = s_doc.to_dict() or {}
                    if subject == "Chưa rõ" and s_data.get("subject"):
                        subject = s_data.get("subject")
                    
                    if teacher_name == "Chưa rõ":
                        s_teacher_id = s_data.get("teacher_id")
                        if s_teacher_id:
                            for t_col in ["teachers", "users"]:
                                t_doc = db.collection(t_col).document(s_teacher_id).get()
                                if t_doc.exists:
                                    t_data = t_doc.to_dict() or {}
                                    teacher_name = (
                                        t_data.get("full_name")
                                        or t_data.get("name")
                                        or t_data.get("display_name")
                                        or t_data.get("email")
                                        or teacher_name
                                    )
                                    break
                    if subject != "Chưa rõ" and teacher_name != "Chưa rõ":
                        break
        except Exception:
            pass

        try:
            sessions_ref = db.collection("sessions").where("class_id", "==", class_id).stream()
        except Exception:
            sessions_ref = []

        seat_evaluations = {}
        for session_doc in sessions_ref:
            s_data = session_doc.to_dict() or {}
            aggregated_eval = s_data.get("aggregated_evaluation", {})

            if not isinstance(aggregated_eval, dict):
                continue

            for seat_id, captures in aggregated_eval.items():
                if seat_id not in seat_evaluations:
                    seat_evaluations[seat_id] = []
                
                if isinstance(captures, dict):
                    has_sub_timestamps = any(isinstance(v, dict) and "concentration" in v for v in captures.values())
                    if has_sub_timestamps:
                        for ts, metrics in captures.items():
                            if isinstance(metrics, dict):
                                try:
                                    conc = float(metrics.get("concentration", metrics.get("avg_concentration", 0)))
                                    seat_evaluations[seat_id].append({"concentration": conc})
                                except (ValueError, TypeError):
                                    pass
                    else:
                        try:
                            conc = float(captures.get("concentration", captures.get("avg_concentration", 0)))
                            seat_evaluations[seat_id].append({"concentration": conc})
                        except (ValueError, TypeError):
                            pass

        students_report = []

        if seat_map and isinstance(seat_map, dict):
            for seat_id, seat_info in seat_map.items():
                if not isinstance(seat_info, dict):
                    continue
                
                student_id = seat_info.get("student_id")
                if not student_id:
                    continue
                
                student_display_name = f"Vị trí {seat_id}"
                for st_col in ["students", "students2"]:
                    try:
                        st_doc = db.collection(st_col).document(student_id).get()
                        if st_doc.exists:
                            st_data = st_doc.to_dict() or {}
                            student_display_name = st_data.get("name") or st_data.get("full_name") or student_display_name
                            break
                    except Exception:
                        pass

                metrics_list = seat_evaluations.get(seat_id, [])
                if metrics_list:
                    avg_conc = sum(m["concentration"] for m in metrics_list) / len(metrics_list)
                else:
                    avg_conc = 0.0

                if avg_conc >= 80.0:
                    status = "good"
                elif avg_conc >= 70.0:
                    status = "stable"
                else:
                    status = "attention"

                students_report.append({
                    "student_id": seat_id,
                    "name": student_display_name,
                    "attention_score": round(avg_conc, 1),
                    "status": status
                })

        return {
            "success": True,
            "data": {
                "name": class_name,
                "class_name": class_name,
                "subject": subject,
                "teacher": teacher_name,
                "classroom": classroom, # Sẽ mang giá trị của class_name (ví dụ: "11B2")
                "students": students_report
            }
        }