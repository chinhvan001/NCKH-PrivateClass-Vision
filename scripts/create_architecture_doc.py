import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._element.get_or_add_tcPr()
    borders_xml = f'<w:tcBorders {nsdecls("w")}>'
    if top:
        borders_xml += f'<w:top w:val="{top.get("val", "single")}" w:sz="{top.get("sz", "4")}" w:space="0" w:color="{top.get("color", "CCCCCC")}"/>'
    else:
        borders_xml += '<w:top w:val="none"/>'
    if bottom:
        borders_xml += f'<w:bottom w:val="{bottom.get("val", "single")}" w:sz="{bottom.get("sz", "4")}" w:space="0" w:color="{bottom.get("color", "CCCCCC")}"/>'
    else:
        borders_xml += '<w:bottom w:val="none"/>'
    if left:
        borders_xml += f'<w:left w:val="{left.get("val", "single")}" w:sz="{left.get("sz", "4")}" w:space="0" w:color="{left.get("color", "CCCCCC")}"/>'
    else:
        borders_xml += '<w:left w:val="none"/>'
    if right:
        borders_xml += f'<w:right w:val="{right.get("val", "single")}" w:sz="{right.get("sz", "4")}" w:space="0" w:color="{right.get("color", "CCCCCC")}"/>'
    else:
        borders_xml += '<w:right w:val="none"/>'
    borders_xml += '</w:tcBorders>'
    tcPr.append(parse_xml(borders_xml))

def format_row(row, bg_hex, text_color, is_header=False, font_size=10):
    for cell in row.cells:
        set_cell_background(cell, bg_hex)
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            for run in p.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(font_size)
                run.font.color.rgb = text_color
                if is_header:
                    run.font.bold = True

def add_callout(doc, title, text, border_color="0F4C81", bg_color="F0F4F8"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)
    set_cell_borders(cell, left={"val": "single", "sz": "24", "color": border_color},
                           top={"val": "single", "sz": "4", "color": "D0D7DE"},
                           bottom={"val": "single", "sz": "4", "color": "D0D7DE"},
                           right={"val": "single", "sz": "4", "color": "D0D7DE"})
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    run_title = p.add_run(f"📌 {title}\n")
    run_title.font.name = 'Arial'
    run_title.font.bold = True
    run_title.font.size = Pt(10.5)
    run_title.font.color.rgb = RGBColor(15, 76, 129)
    
    run_text = p.add_run(text)
    run_text.font.name = 'Arial'
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = RGBColor(44, 62, 80)
    p2 = doc.add_paragraph()
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(6)

def generate_document():
    doc = Document()
    
    # Page setup - Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    PRIMARY_COLOR = RGBColor(15, 76, 129)     # Deep Navy Blue
    SECONDARY_COLOR = RGBColor(44, 62, 80)    # Slate Gray
    TEXT_COLOR = RGBColor(33, 37, 41)         # Off Black
    MUTED_COLOR = RGBColor(108, 117, 125)     # Muted Gray

    # Helper for styled headings
    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = PRIMARY_COLOR
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = SECONDARY_COLOR
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = PRIMARY_COLOR
        return p

    def add_p(text, bold_prefix=None, space_after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.2
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = 'Arial'
            r_pre.font.size = Pt(10)
            r_pre.font.bold = True
            r_pre.font.color.rgb = TEXT_COLOR
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(10)
        r.font.color.rgb = TEXT_COLOR
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = 'Arial'
            r_pre.font.size = Pt(10)
            r_pre.font.bold = True
            r_pre.font.color.rgb = TEXT_COLOR
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(10)
        r.font.color.rgb = TEXT_COLOR
        return p

    # ==========================
    # COVER / HEADER SECTION
    # ==========================
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst = p_inst.add_run("BỘ GIÁO DỤC VÀ ĐÀO TẠO — TRƯỜNG ĐẠI HỌC DUY TÂN (DTU)\nVIỆN ĐÀO TẠO VÀ NGHIÊN CỨU QUỐC TẾ (IS)")
    r_inst.font.name = 'Arial'
    r_inst.font.size = Pt(11)
    r_inst.font.bold = True
    r_inst.font.color.rgb = SECONDARY_COLOR

    p_doc_type = doc.add_paragraph()
    p_doc_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_doc_type.paragraph_format.space_before = Pt(30)
    p_doc_type.paragraph_format.space_after = Pt(6)
    r_doc_type = p_doc_type.add_run("TÀI LIỆU THIẾT KẾ KIẾN TRÚC HỆ THỐNG\n(SYSTEM ARCHITECTURE DESIGN DOCUMENT)")
    r_doc_type.font.name = 'Arial'
    r_doc_type.font.size = Pt(18)
    r_doc_type.font.bold = True
    r_doc_type.font.color.rgb = PRIMARY_COLOR

    p_proj_title = doc.add_paragraph()
    p_proj_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_proj_title.paragraph_format.space_before = Pt(6)
    p_proj_title.paragraph_format.space_after = Pt(30)
    r_proj_title = p_proj_title.add_run("ĐỀ TÀI: PRIVATECLASS VISION\nHỆ THỐNG GIÁM SÁT ĐỘ TẬP TRUNG LỚP HỌC THỜI GIAN THỰC\nBẢO VỆ TUYỆT ĐỐI QUYỀN RIÊNG TƯ (PRIVACY-BY-DESIGN)")
    r_proj_title.font.name = 'Arial'
    r_proj_title.font.size = Pt(13)
    r_proj_title.font.bold = True
    r_proj_title.font.color.rgb = SECONDARY_COLOR

    # Metadata Table
    meta_table = doc.add_table(rows=6, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    
    meta_data = [
        ("Mã dự án / Đề tài NCKH:", "PrivateClass Vision (C1SE.31-NCKH)"),
        ("Đơn vị thực hiện:", "Trường Đại học Duy Tân (DTU) - International School"),
        ("Giảng viên hướng dẫn:", "TS. Nguyễn Chiến Thắng"),
        ("Nhóm sinh viên thực hiện:", "Nguyễn Văn Chỉnh (Trưởng nhóm - Leader)\nTrần Công Danh\nNguyễn Phương Ngân\nNguyễn Thế Huy\nHoàng Tiến Đạt"),
        ("Phiên bản kiến trúc:", "Architecture Design Document v1.0 (Năm 2026)"),
        ("Trạng thái phê duyệt:", "Official Baseline Architecture Design")
    ]

    col_widths = [Inches(2.4), Inches(4.1)]
    for r_idx, (k, v) in enumerate(meta_data):
        row = meta_table.rows[r_idx]
        cell_k, cell_v = row.cells[0], row.cells[1]
        cell_k.width, cell_v.width = col_widths[0], col_widths[1]
        
        cell_k.text = k
        cell_v.text = v
        
        # Style
        bg_color = "F8F9FA" if r_idx % 2 == 0 else "FFFFFF"
        set_cell_background(cell_k, bg_color)
        set_cell_background(cell_v, bg_color)
        set_cell_margins(cell_k, top=100, bottom=100, left=140, right=140)
        set_cell_margins(cell_v, top=100, bottom=100, left=140, right=140)
        set_cell_borders(cell_k, top={"val": "single", "sz": "4", "color": "E2E8F0"},
                                 bottom={"val": "single", "sz": "4", "color": "E2E8F0"},
                                 left={"val": "single", "sz": "4", "color": "E2E8F0"},
                                 right={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_borders(cell_v, top={"val": "single", "sz": "4", "color": "E2E8F0"},
                                 bottom={"val": "single", "sz": "4", "color": "E2E8F0"},
                                 left={"val": "single", "sz": "4", "color": "E2E8F0"},
                                 right={"val": "single", "sz": "4", "color": "E2E8F0"})
        
        pk = cell_k.paragraphs[0]
        pk.runs[0].font.name = 'Arial'
        pk.runs[0].font.size = Pt(9.5)
        pk.runs[0].font.bold = True
        pk.runs[0].font.color.rgb = SECONDARY_COLOR
        
        pv = cell_v.paragraphs[0]
        for run in pv.runs:
            run.font.name = 'Arial'
            run.font.size = Pt(9.5)
            run.font.color.rgb = TEXT_COLOR

    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(20)
    doc.add_page_break()

    # ==========================
    # SECTION 1
    # ==========================
    add_h1("1. MỤC TIÊU VÀ NGUYÊN TẮC THIẾT KẾ KIẾN TRÚC")
    
    add_h2("1.1. Tổng quan dự án PrivateClass Vision")
    add_p(
        "PrivateClass Vision là hệ thống hỗ trợ ra quyết định sư phạm (Decision-Support System) "
        "dựa trên nền tảng Trí tuệ nhân tạo (AI) và Thị giác máy tính (Computer Vision), được thiết kế "
        "nhằm trợ giúp giảng viên và nhà quản lý giáo dục theo dõi trực quan mức độ tập trung, "
        "trạng thái nhận thức và hành vi học tập của sinh viên trong lớp học theo thời gian thực (Real-time). "
        "Trong bối cảnh các giảng đường đại học hiện đại có quy mô từ 40 đến 80 sinh viên, việc một giảng viên "
        "vừa truyền đạt kiến thức chuyên môn vừa bao quát từng cá nhân để phát hiện trạng thái mệt mỏi, ngủ gật, "
        "hoặc mất tập trung kéo dài là một áp lực rất lớn. Hệ thống giải quyết triệt để rào cản này bằng cách "
        "tự động hóa khâu quan sát định lượng, tạo ra bảng biểu đồ nhiệt (Heatmap) tập trung theo thời gian thực "
        "và cảnh báo tức thời khi chỉ số tập trung trung bình của lớp suy giảm đột ngột."
    )
    add_p(
        "Đồng thời, PrivateClass Vision xây dựng bức tranh tổng thể về hiệu quả giảng dạy xuyên suốt học kỳ, "
        "cung cấp báo cáo phân tích tương quan giữa mức độ chú ý của sinh viên với từng phương pháp giảng dạy, "
        "nội dung bài giảng hay các khung giờ học khác nhau trong ngày."
    )

    add_h2("1.2. Triết lý Bảo mật & Riêng tư Cốt lõi (Privacy-by-Design)")
    add_p(
        "Khác biệt căn bản và mang tính tiên quyết của PrivateClass Vision so với các hệ thống Camera giám sát "
        "truyền thống trên thị trường nằm ở cam kết bảo vệ quyền riêng tư tuyệt đối, tuân thủ nghiêm ngặt theo "
        "tiêu chuẩn GDPR (General Data Protection Regulation - Châu Âu) và khung an toàn NIST Privacy Framework."
    )

    add_callout(
        doc,
        "TUYÊN NGÔN BẢO VỆ QUYỀN RIÊNG TƯ (PRIVACY-BY-DESIGN)",
        "• KHÔNG nhận dạng khuôn mặt (Zero Facial Biometrics): Hệ thống loại bỏ hoàn toàn các mô hình Face Recognition. "
        "Tuyệt đối không trích xuất, không mã hóa (embeddings) và không lưu trữ bất kỳ đặc trưng sinh trắc học khuôn mặt nào.\n"
        "• Xử lý thị giác hoàn toàn tại biên (Local Edge Processing): Toàn bộ luồng video độ phân giải cao từ Camera IP (RTSP) "
        "được phân tích trực tiếp trên bộ nhớ RAM của trạm máy tính biên (Local Edge Workstation) đặt tại cơ sở đào tạo. "
        "Không có bất kỳ khung hình video thô (Raw Video Frame) nào bị truyền qua Internet hay đưa lên Cloud.\n"
        "• Trích xuất khung xương ẩn danh (Pose Skeleton Extraction): Hệ thống chỉ chuyển đổi hình ảnh thành các tọa độ khớp "
        "xương 2D/3D (Keypoints: đầu, cổ, vai, sống lưng) và tính toán vector góc gập cơ học để đánh giá tư thế.\n"
        "• Hủy dữ liệu thô tức thì (Zero Raw Retention): Các khung hình trong bộ nhớ đệm (RAM buffer) bị hủy hoàn toàn "
        "ngay sau chu kỳ suy luận (Inference cycle, < 50ms). Không ghi video ra ổ đĩa cục bộ hay Cloud Storage.\n"
        "• Định danh định vị thay vì sinh trắc học (Pseudonymous Seating Mapping): Sự liên kết giữa chỉ số hành vi và danh tính "
        "sinh viên được thực hiện gián tiếp thông qua ma trận sơ đồ chỗ ngồi (Seating Layout Grid) do giảng viên phê duyệt độc lập."
    )

    add_h2("1.3. Mục tiêu Kiến trúc Kỹ thuật (Architectural Goals)")
    add_bullet("Độ trễ thấp (Low-Latency Stream): ", "Hiệu năng thời gian thực: ")
    add_p("Xử lý luồng video 1080p với tốc độ khung hình tối thiểu 15–20 FPS trên máy trạm biên, độ trễ cảnh báo đẩy về giao diện giáo viên không quá 3 giây.")
    add_bullet("Cấu trúc 3 tầng tách biệt (Strict 3-Tier Separation): ", "Tính module hóa cao: ")
    add_p("Backend tuân thủ chặt chẽ mô hình Route — Service — Repository, bảo đảm khả năng mở rộng, bảo trì và kiểm thử độc lập.")
    add_bullet("Tối ưu hóa tài nguyên đám mây: ", "Tiết kiệm chi phí Firebase: ")
    add_p("Áp dụng cơ chế Cache RAM (TTL Cache) tại tầng Service và giảm thiểu số lần đọc Firestore lặp lại, tối ưu hạn ngạch tài nguyên Cloud.")
    add_bullet("Tính sẵn sàng và chịu lỗi: ", "Độ tin cậy cao: ")
    add_p("Hệ thống duy trì hoạt động cục bộ ngay cả khi mất kết nối Internet tạm thời; dữ liệu log được lưu đệm và đồng bộ bù khi kết nối được phục hồi.")

    # ==========================
    # SECTION 2
    # ==========================
    add_h1("2. KIẾN TRÚC TỔNG THỂ HỆ THỐNG (SYSTEM OVERVIEW ARCHITECTURE)")
    add_p(
        "PrivateClass Vision được xây dựng dựa trên mô hình Kiến trúc Lai Biên - Đám Mây (Hybrid Edge-Cloud System Architecture). "
        "Thiết kế này kết hợp tối ưu giữa sức mạnh xử lý song song trên phần cứng chuyên dụng tại biên (Edge GPU) "
        "và sự linh hoạt, bảo mật cao của nền tảng điện toán đám mây trung tâm (Google Cloud / Firebase Ecosystem)."
    )

    add_h2("2.1. Phân tầng Kiến trúc (4-Layer Architectural Stack)")
    
    layer_table = doc.add_table(rows=5, cols=3)
    layer_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    layer_table.autofit = False
    
    headers = ["Tầng Kiến Trúc (Layer)", "Công Nghệ & Thành Phần", "Nhiệm Vụ & Trách Nhiệm"]
    for i, h in enumerate(headers):
        layer_table.rows[0].cells[i].text = h
    format_row(layer_table.rows[0], "0F4C81", RGBColor(255, 255, 255), is_header=True)

    layers_data = [
        ("1. Perception & Edge Processing Layer\n(Tầng Thu Nhận & Xử Lý Biên)",
         "• Camera IP / RTSP Stream\n• FFmpeg / ffprobe Health Check\n• Edge GPU (NVIDIA Jetson / RTX Box)\n• YOLOv8-Pose / MediaPipe",
         "• Tiếp nhận luồng RTSP 1080p@30fps ổn định.\n• Kiểm tra trạng thái camera qua ffprobe.\n• Phát hiện người và trích xuất 17 điểm khớp xương (Body Keypoints).\n• Tiêu hủy khung hình thô ngay trên RAM buffer."),
        
        ("2. Behavioral AI & Analytics Layer\n(Tầng Phân Tích Hành Vi AI)",
         "• Python Spatial Geometry Engine\n• Time-series Sliding Window\n• Head Tilt & Torso Vector Rules\n• Seat Localization Algorithm",
         "• Tính toán góc nghiêng đầu, độ gập thân, cử động tay.\n• Phân loại trạng thái: Tập trung tốt, Trung bình, Cần chú ý (Gục bàn, lơ đãng).\n• Ánh xạ tọa độ không gian (Bounding Box) vào vị trí ghế ngồi (Seat Matrix)."),
        
        ("3. Central Backend & Cloud Layer\n(Tầng Nghiệp Vụ & Lưu Trữ Đám Mây)",
         "• Python Flask Framework (3-Tier)\n• Firebase Admin SDK & Cloud Firestore\n• Firebase Identity Toolkit / Auth\n• In-Memory TTL Cache Engine",
         "• Xác thực người dùng, kiểm soát RBAC (Admin, Teacher).\n• Quản lý danh mục: phòng học, camera, lớp học, học sinh.\n• Điều phối phiên giám sát (Session Lifecycle) và tổng hợp kết quả (Batch Commit).\n• Cung cấp RESTful API chuẩn mực."),
        
        ("4. Presentation & Application Layer\n(Tầng Giao Diện Ứng Dụng)",
         "• React 19, Vite, React Router v6\n• Lucide Icons, Custom Design System\n• Firebase Web SDK (Auth Client)\n• Flutter Mobile App (Giảng viên / Phụ huynh)",
         "• Web Portal: Quản trị hệ thống, cấu hình camera, quản lý sơ đồ lớp học, xem báo cáo tổng thể.\n• Mobile App: Giảng viên xem live heatmap sơ đồ chỗ ngồi, nhận thông báo đẩy tức thời khi lớp mất tập trung.")
    ]

    col_w_layer = [Inches(2.0), Inches(2.2), Inches(2.3)]
    for r_idx, (c0, c1, c2) in enumerate(layers_data):
        row = layer_table.rows[r_idx + 1]
        row.cells[0].text, row.cells[1].text, row.cells[2].text = c0, c1, c2
        for ci, w in enumerate(col_w_layer):
            row.cells[ci].width = w
        bg = "F8F9FA" if r_idx % 2 == 0 else "FFFFFF"
        format_row(row, bg, TEXT_COLOR, is_header=False, font_size=9)
        set_cell_borders(row.cells[0], top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_borders(row.cells[1], top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_borders(row.cells[2], top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})

    add_p("")
    add_h2("2.2. Luồng Dữ Liệu Xuyên Suốt (End-to-End Data Pipeline)")
    add_p(
        "Dữ liệu trong PrivateClass Vision luân chuyển qua 5 giai đoạn được kiểm soát nghiêm ngặt về bảo mật và độ trễ:"
    )
    add_bullet("Giai đoạn 1 — Ingestion: ", "RTSP Stream Ingestion: Camera IP truyền luồng video H.264/H.265 đến bộ đệm OpenCV VideoCapture trên máy Edge local qua mạng LAN trường học.")
    add_bullet("Giai đoạn 2 — Inference: ", "Skeleton Extraction & Purge: GPU chạy mô hình YOLOv8-Pose trong khoảng 25ms, trích xuất danh sách keypoints. Toàn bộ frame ảnh gốc được `del frame` khỏi RAM ngay lập tức.")
    add_bullet("Giai đoạn 3 — Spatial Mapping: ", "Mapping Ghế Ngồi Ẩn Danh: Dựa trên tọa độ tâm của người (Center Box), thuật toán Point-in-Polygon ánh xạ người đó vào mã ghế (ví dụ: S01, S02...).")
    add_bullet("Giai đoạn 4 — Cloud Sync: ", "JSON Telemetry Ingestion: Máy Edge đóng gói payload JSON ẩn danh (gồm `session_id`, `seat_id`, `concentration`, `distraction`) và gửi qua HTTPS POST tới Flask Backend.")
    add_bullet("Giai đoạn 5 — Aggregation & Alert: ", "Tích Lũy & Cảnh Báo: `EvaluationService` cập nhật trạng thái runtime `SESSION_RUNTIME_STATE`, tính toán điểm trung bình động và trả về trạng thái hiển thị cho UI.")

    # ==========================
    # SECTION 3
    # ==========================
    doc.add_page_break()
    add_h1("3. THIẾT KẾ CHI TIẾT CÁC PHÂN HỆ HỆ THỐNG")

    add_h2("3.1. Phân hệ Edge Processing & AI Computer Vision")
    add_p(
        "Phân hệ Biên chịu trách nhiệm phân tích thị giác nặng nhất nhưng được tối ưu hóa để vận hành mượt mà trên phần cứng cục bộ. "
        "Chi tiết cấu trúc thuật toán bao gồm:"
    )
    add_h3("A. Mô hình Trích xuất Khung xương (YOLOv8-Pose)")
    add_p(
        "Hệ thống sử dụng phiên bản YOLOv8n-pose (Nano) hoặc YOLOv8s-pose (Small) đã được lượng hóa (TensorRT / FP16). "
        "Mô hình nhận diện 17 điểm khớp xương chuẩn COCO Format: Mũi (0), Mắt (1,2), Tai (3,4), Vai (5,6), Khuỷu tay (7,8), Cổ tay (9,10), Hông (11,12)..."
    )
    add_h3("B. Thuật toán Đánh giá Tư thế & Góc nghiêng (Pose Geometric Analysis)")
    add_bullet("Góc gập đầu (Head Tilt Angle - θ_head): ", "Tính toán độ nghiêng của vector nối giữa Mắt/Mũi và Đốt sống cổ so với phương thẳng đứng.")
    add_p("    θ_head = arccos( (v_neck • v_up) / (|v_neck| * |v_up|) )\n"
          "    - Nếu θ_head > 45° kéo dài > 10 giây: Đánh dấu trạng thái Gục bàn / Buồn ngủ (Drowsy).")
    add_bullet("Độ xoay ngang đầu (Head Yaw/Orientation): ", "Đánh giá khoảng cách tỷ lệ giữa Mũi và 2 Tai.")
    add_p("    - Nếu một bên tai bị khuất hoặc tỷ lệ bất đối xứng vượt ngưỡng 75%: Đánh dấu trạng thái Quay dọc quay ngang / Mất tập trung (Distracted).")
    add_bullet("Độ vững của thân trên (Torso Posture Stability): ", "Đo dao động góc nghiêng giữa hai vai so với phương ngang.")
    add_p("    - Tư thế ngồi thẳng đứng chuẩn: Hai vai cân bằng, lưng tạo góc 80° - 100° so với mặt bàn.")

    add_h3("C. Cơ chế Kiểm tra Sức khỏe Camera (Camera Health Check via ffprobe)")
    add_p(
        "Để đảm bảo hệ thống không bị gián đoạn do mất tín hiệu RTSP, module `camera_routes.py` tích hợp tiện ích chạy ngầm "
        "`subprocess` gọi công cụ `ffprobe` nhằm thăm dò đường truyền RTSP với timeout 5 giây. Trạng thái kết nối (online/offline) "
        "được tự động cập nhật vào document phòng học trên Firestore."
    )

    add_h2("3.2. Phân hệ Central Backend (Flask 3-Tier Architecture)")
    add_p(
        "Toàn bộ mã nguồn Backend trong thư mục `backend/` được tái cấu trúc triệt để theo mô hình 3 tầng chuẩn công nghiệp (3-Tier Architecture):"
    )

    add_callout(
        doc,
        "CẤU TRÚC PHÂN TÁCH 3 TẦNG TRONG BACKEND FLASK",
        "1. Tầng Repository (backend/repositories/):\n"
        "   - Đảm nhiệm 100% việc kết nối và truy vấn Firestore Database hoặc Firebase Admin SDK.\n"
        "   - Các file: auth_repository.py, classroom_repository.py, class_repository.py, admin_repository.py, "
        "student_repository.py, session_repository.py, evaluation_repository.py, report_repository.py, dashboard_repository.py.\n"
        "2. Tầng Service (backend/services/):\n"
        "   - Đảm nhiệm toàn bộ business logic, validate dữ liệu, sắp xếp, tính toán thống kê và quản lý Cache RAM.\n"
        "   - Các file: auth_service.py, classroom_service.py, class_service.py, admin_service.py, "
        "student_service.py, session_service.py, evaluation_service.py, report_service.py, dashboard_service.py.\n"
        "3. Tầng Route / Controller (backend/routes/):\n"
        "   - Định nghĩa Flask Blueprints, kiểm tra token xác thực, trích xuất request parameters, ủy quyền xử lý cho Service và trả về JSON chuẩn RESTful.\n"
        "   - Các file: auth_routes.py, classroom_routes.py, class_routes.py, admin_routes.py, "
        "student_routes.py, session_routes.py, evaluation_routes.py, report_routes.py, dashboard_routes.py, camera_routes.py."
    )

    add_h3("Cơ chế Quản lý Phiên Giám sát Thời gian thực (Session Runtime State)")
    add_p(
        "Trong `backend/services/evaluation_service.py`, hệ thống duy trì cấu trúc bộ nhớ đệm `SESSION_RUNTIME_STATE = {}`. "
        "Khi luồng camera gửi dữ liệu đo độ tập trung liên tục (mỗi 1–3 giây), Backend không ghi từng bản ghi riêng rẽ vào Firestore "
        "(tránh hàng nghìn lượt ghi tốn kém). Thay vào đó, nó cộng dồn `concentration_sum` và đếm `capture_count` trên RAM. "
        "Chỉ khi phiên học kết thúc (`end_session`), Firestore Batch Commit mới được kích hoạt để lưu bản ghi tổng kết "
        "vào collection `session_results` một cách nguyên tử (Atomic Write)."
    )

    add_h2("3.3. Phân hệ Quản trị Web & Ứng dụng Người dùng (Frontend Layer)")
    add_p(
        "Giao diện người dùng được phân chia chuyên biệt theo vai trò người dùng (Role-Based Views):"
    )
    add_bullet("Admin Web Portal (React 19 + Vite): ", "Phục vụ ban giám hiệu và kỹ thuật viên quản trị hệ thống:")
    add_p("    • Quản lý tài khoản Admin & Giáo viên (Account Management): Phân quyền, kích hoạt/vô hiệu hóa, quản lý bộ môn.\n"
          "    • Quản lý Phòng học & Camera (Classroom & Camera): Khai báo địa chỉ IP, cổng RTSP, kích thước lưới phòng học (Hàng x Cột).\n"
          "    • Quản lý Lớp học & Sơ đồ Ghế (Class & Seating Map): Tự động sinh mã ghế (S01, S02...), gán học sinh vào từng vị trí ghế trực quan.\n"
          "    • Quản lý Học sinh & Hồ sơ (Student Management): Quản lý danh sách học sinh, thông tin liên lạc phụ huynh, chuyển trạng thái học tập.\n"
          "    • Báo cáo & Đánh giá (Evaluation & Reports): Theo dõi biểu đồ phân bố độ tập trung theo lớp, môn học, giáo viên và xuất báo cáo PDF/Excel.")
    add_bullet("Teacher & Parent Interfaces: ", "Giao diện theo dõi lớp học và báo cáo gia đình:")
    add_p("    • Giảng viên: Truy cập giao diện giám sát lớp học với bảng màu trực quan (Xanh: Tập trung tốt >=80%, Vàng: Trung bình 70-79%, Đỏ: Cần chú ý <70%).\n"
          "    • Phụ huynh: Chỉ nhận báo cáo tổng hợp hành vi và chuyên cần định kỳ của con em mình, không có quyền xem dữ liệu thời gian thực.")

    # ==========================
    # SECTION 4
    # ==========================
    doc.add_page_break()
    add_h1("4. THIẾT KẾ CƠ SỞ DỮ LIỆU & CẤU TRÚC THỰC THỂ (FIRESTORE SCHEMAS)")
    add_p(
        "PrivateClass Vision sử dụng Cloud Firestore — cơ sở dữ liệu tài liệu NoSQL phân tán (Distributed Document-Store) "
        "có độ trễ thấp và khả năng mở rộng quy mô linh hoạt. Cấu trúc Schema được thiết kế chuẩn xác bám sát thực tế triển khai trong mã nguồn:"
    )

    schema_table = doc.add_table(rows=8, cols=3)
    schema_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    schema_table.autofit = False

    s_headers = ["Collection Name", "Trường Dữ Liệu Chính (Document Fields)", "Mục Đích & Ràng Buộc Nghiệp Vụ"]
    for i, h in enumerate(s_headers):
        schema_table.rows[0].cells[i].text = h
    format_row(schema_table.rows[0], "0F4C81", RGBColor(255, 255, 255), is_header=True)

    schemas = [
        ("admins",
         "• email (string)\n• name (string)\n• phone_number (string)\n• school (string)\n• is_active (boolean)\n• created_at (timestamp)",
         "Lưu trữ danh sách quản trị viên có quyền truy cập toàn bộ portal. Document ID chính là Firebase UID."),
        
        ("teachers",
         "• uid (string | null)\n• email (string)\n• name (string)\n• phone_number (string)\n• subject (string)\n• is_active (boolean)\n• auth_provider (string)\n• auth_status (string)",
         "Danh mục tài khoản giáo viên bộ môn. Liên kết với Firebase Auth khi giáo viên kích hoạt đăng nhập lần đầu."),
        
        ("classrooms",
         "• classroom_name (string)\n• camera_name (string)\n• ip_address (string)\n• rtsp_port (string)\n• rtsp_url (string)\n• row_number (int)\n• column_number (int)\n• status (online/offline)",
         "Cấu hình thông số vật lý của phòng học và thông số kết nối Camera IP. Giới hạn số hàng x số cột bàn ghế."),
        
        ("classes2",
         "• class_name (string)\n• teacher_id (string)\n• school_year (string)\n• subject (string)\n• row_count (int)\n• column_count (int)\n• status (active/inactive)\n• seat_map (map of seats)\n• created_at, updated_at",
         "Thông tin lớp học chính khóa. Lưu ma trận sơ đồ chỗ ngồi (`seat_map`), trong đó mỗi ghế có `student_id`, `status` (empty/occupied)."),
        
        ("students2",
         "• student_code (string)\n• full_name (string)\n• birthday (string)\n• gender (string)\n• parent_name (string)\n• parent_phonenumber (string)\n• is_active (boolean/string)\n• notes (subcollection)",
         "Hồ sơ học sinh. Có subcollection `student_note` để giáo viên ghi chú hành vi cá biệt trong quá trình theo dõi."),
        
        ("sessions",
         "• class_id (string)\n• teacher_id (string)\n• room (string)\n• session_date (string)\n• shift (morning/afternoon)\n• period (int)\n• status (scheduled/running/ended)\n• seat_snapshot (map)\n• aggregated_evaluation (map)",
         "Lịch trình và trạng thái các buổi học thực tế. Lưu vết ảnh chụp vị trí chỗ ngồi (`seat_snapshot`) tại thời điểm lớp bắt đầu."),
        
        ("session_results",
         "• session_id (string)\n• student_id (string)\n• seat_id (string)\n• avg_concentration (float)\n• status (Tập trung tốt / Trung bình / Cần chú ý)\n• updated_at (timestamp)",
         "Kết quả tổng kết mức độ tập trung của từng học sinh sau khi phiên học kết thúc. Tạo bởi batch commit nguyên tử.")
    ]

    col_w_s = [Inches(1.6), Inches(2.5), Inches(2.4)]
    for r_idx, (c0, c1, c2) in enumerate(schemas):
        row = schema_table.rows[r_idx + 1]
        row.cells[0].text, row.cells[1].text, row.cells[2].text = c0, c1, c2
        for ci, w in enumerate(col_w_s):
            row.cells[ci].width = w
        bg = "F8F9FA" if r_idx % 2 == 0 else "FFFFFF"
        format_row(row, bg, TEXT_COLOR, is_header=False, font_size=8.5)
        set_cell_borders(row.cells[0], top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_borders(row.cells[1], top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_borders(row.cells[2], top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})

    add_p("")
    add_h2("4.2. Cơ chế Tối ưu hóa Bộ nhớ đệm (RAM / TTL Caching Strategy)")
    add_p(
        "Nhằm bảo vệ hạn ngạch Firestore Read Operations và tăng tốc độ phản hồi API cho người dùng, "
        "tầng Service áp dụng chiến lược Caching nội bộ với cơ chế Invalidation tức thì:"
    )
    add_bullet("Classroom Cache: ", "Cache danh sách phòng học trong 30 giây. Khi có thao tác POST, PUT hoặc DELETE phòng học, cache được xóa lập tức (`_invalidate_cache`).")
    add_bullet("Class & Teacher Relational Cache: ", "Khi lấy danh sách lớp học, hệ thống cache thông tin tên giáo viên (`_teacher_cache`) và học sinh (`_student_cache`) trong 60 giây, loại bỏ hoàn toàn việc gọi vòng lặp Firestore stream() N lần (giải quyết triệt để vấn đề N+1 Query).")
    add_bullet("Admin & Profile Cache: ", "Lưu tạm thông tin xác thực Admin trong 60 giây, giúp việc kiểm tra quyền trên mỗi HTTP Request diễn ra trong < 1ms.")

    # ==========================
    # SECTION 5
    # ==========================
    doc.add_page_break()
    add_h1("5. GIAO TIẾP VÀ TÍCH HỢP HỆ THỐNG (API & INTEGRATION)")

    add_h2("5.1. Danh mục API Endpoints Chính")
    
    api_table = doc.add_table(rows=11, cols=4)
    api_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    api_table.autofit = False

    api_headers = ["Phân Hệ", "HTTP & Endpoint", "Tham Số / Payload", "Mã Trả Về & Ý Nghĩa"]
    for i, h in enumerate(api_headers):
        api_table.rows[0].cells[i].text = h
    format_row(api_table.rows[0], "0F4C81", RGBColor(255, 255, 255), is_header=True)

    apis = [
        ("Auth", "POST /api/auth/google", "idToken (Firebase Token)", "200: Đăng nhập thành công\n401: Token lỗi\n403: Không có quyền Admin"),
        ("Auth", "POST /api/auth/email-password", "email, password", "200: Trả về idToken & user info\n400: Thiếu thông tin\n401: Sai mật khẩu"),
        ("Admin", "GET /api/admin/users", "Header: Bearer Token", "200: Danh sách giáo viên\n401: Unauthorized\n403: Bị vô hiệu hóa"),
        ("Admin", "POST /api/admin/teachers", "name, email, phone, subject, is_active", "201: Tạo giáo viên mới\n400: Validate lỗi\n409: Trùng email"),
        ("Classroom", "GET /api/admin/classrooms", "Header: Bearer Token", "200: Danh sách phòng học kèm camera và số hàng cột"),
        ("Classroom", "POST /api/admin/classrooms", "classroom_name, ip_address, rtsp_port, row, col", "201: Tạo phòng mới\n409: Trùng tên phòng"),
        ("Class", "GET /api/admin/classes", "status, teacher_id, school_year", "200: Danh sách lớp học kèm thống kê số ghế trống/có người"),
        ("Class", "PUT /api/admin/classes/<id>/seats/<sid>", "student_id", "200: Cập nhật học sinh vào vị trí ghế\n404: Không thấy ghế"),
        ("Evaluation", "POST /api/v1/evaluations/process-captures", "session_id, captures_data [student_id, concentration, distraction]", "200: Trả về trạng thái tập trung tích lũy của từng học sinh"),
        ("Evaluation", "POST /api/v1/evaluations/sessions/<id>/end", "session_id", "200: Kết thúc phiên học, batch commit kết quả vào Firestore")
    ]

    col_w_api = [Inches(1.1), Inches(2.2), Inches(1.8), Inches(1.4)]
    for r_idx, (c0, c1, c2, c3) in enumerate(apis):
        row = api_table.rows[r_idx + 1]
        row.cells[0].text, row.cells[1].text, row.cells[2].text, row.cells[3].text = c0, c1, c2, c3
        for ci, w in enumerate(col_w_api):
            row.cells[ci].width = w
        bg = "F8F9FA" if r_idx % 2 == 0 else "FFFFFF"
        format_row(row, bg, TEXT_COLOR, is_header=False, font_size=8)
        for cell in row.cells:
            set_cell_borders(cell, top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})

    add_p("")
    add_h2("5.2. Cơ chế Xác thực & Kiểm soát Truy cập (Security Middleware)")
    add_p(
        "Mọi yêu cầu gửi đến các Endpoint nhạy cảm đều phải đính kèm Firebase ID Token trong Authorization Header "
        "dưới dạng `Bearer <Token>`. Hàm `authorize_admin()` và `require_admin()` tại `utils/auth.py` giải mã token qua Firebase Admin SDK, "
        "đối chiếu trường `is_active` và phân quyền người dùng trước khi chuyển giao tác vụ xuống tầng Service."
    )

    # ==========================
    # SECTION 6
    # ==========================
    doc.add_page_break()
    add_h1("6. YÊU CẦU PHI CHỨC NĂNG & AN NINH HỆ THỐNG")

    add_h2("6.1. Hiệu năng & Khả năng Đáp ứng Thời gian thực (Performance)")
    add_bullet("Tần số xử lý tại Biên: ", "Đạt tối thiểu 15–20 FPS trên luồng RTSP 1080p, đáp ứng khả năng theo dõi đồng thời 40–60 sinh viên trong một góc nhìn camera.")
    add_bullet("Thời gian phản hồi API Backend: ", "Thời gian xử lý trung bình cho các request đọc danh sách đạt < 50ms nhờ có bộ đệm TTL Cache.")
    add_bullet("Độ trễ thông báo thời gian thực: ", "Từ thời điểm sinh viên có hành vi gục bàn/lơ đãng kéo dài đến khi hiển thị cảnh báo trên giao diện giáo viên không quá 3 giây.")

    add_h2("6.2. An toàn Thông tin & Tuân thủ Quyền riêng tư (Security & Compliance)")
    add_bullet("Mã hóa kênh truyền: ", "100% các kết nối ra ngoài mạng nội bộ đều bắt buộc sử dụng HTTPS với TLS 1.3.")
    add_bullet("Không lưu trữ dữ liệu nhạy cảm: ", "PrivateClass Vision tuân thủ nguyên tắc 'Data Minimization' — chỉ lưu trữ chỉ số số học ẩn danh (ví dụ: điểm tập trung 85.5%), không bao giờ lưu trữ ảnh chụp cá nhân hay video clip.")
    add_bullet("Chính sách lưu trữ và dọn dẹp dữ liệu (Data Retention): ", "Dữ liệu capture chi tiết được lưu tạm trên RAM và hủy khi kết thúc phiên. Báo cáo tổng hợp trong `session_results` được lưu trữ phục vụ thống kê học kỳ.")

    add_h2("6.3. Khả năng Mở rộng & Tính sẵn sàng (Scalability & Availability)")
    add_bullet("Mở rộng ngang tại Biên (Horizontal Edge Scaling): ", "Mỗi phòng học được trang bị một trạm xử lý biên độc lập. Khi nhà trường mở rộng thêm 50 hay 100 phòng học mới, năng lực xử lý thị giác máy tính tăng trưởng tuyến tính mà không gây nghẽn tại Cloud Backend.")
    add_bullet("Backend Không trạng thái (Stateless Backend Architecture): ", "Flask API được thiết kế để có thể dễ dàng đóng gói Docker và triển khai trên Google Cloud Run hoặc Kubernetes Cluster khi lượng truy cập tăng vọt.")

    # ==========================
    # SECTION 7
    # ==========================
    add_h1("7. TRIỂN KHAI & YÊU CẦU PHẦN CỨNG (DEPLOYMENT SPECIFICATIONS)")

    add_h2("7.1. Cấu hình Phần cứng Khuyến nghị")
    
    hw_table = doc.add_table(rows=4, cols=3)
    hw_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hw_table.autofit = False

    hw_headers = ["Thành Phần Phần Cứng", "Cấu Hình Tối Thiểu (Minimum)", "Cấu Hình Đề Xuất (Recommended)"]
    for i, h in enumerate(hw_headers):
        hw_table.rows[0].cells[i].text = h
    format_row(hw_table.rows[0], "0F4C81", RGBColor(255, 255, 255), is_header=True)

    hw_specs = [
        ("Camera IP Lớp học", "Độ phân giải Full HD (1080p), 15fps, giao thức RTSP chuẩn H.264, góc rộng 90°", "Camera IP Full HD 1080p@30fps, hỗ trợ WDR (chống ngược sáng), góc siêu rộng 110° - 120°"),
        ("Trạm Xử Lý Biên (Edge Box)", "CPU Intel Core i5 Gen 10 / AMD Ryzen 5, 16GB RAM, GPU NVIDIA GTX 1660 (6GB VRAM)", "NVIDIA Jetson Orin Nano / AGX Orin hoặc PC Intel Core i7, 32GB RAM, GPU RTX 3060 / 4060"),
        ("Hạ Tầng Mạng Trường Học", "Mạng LAN nội bộ cáp Cat6, băng thông 100 Mbps, kết nối switch ổn định", "Mạng Gigabit LAN (1000 Mbps), hỗ trợ cấp nguồn PoE cho Camera, đường truyền Internet cáp quang")
    ]

    col_w_hw = [Inches(1.8), Inches(2.3), Inches(2.4)]
    for r_idx, (c0, c1, c2) in enumerate(hw_specs):
        row = hw_table.rows[r_idx + 1]
        row.cells[0].text, row.cells[1].text, row.cells[2].text = c0, c1, c2
        for ci, w in enumerate(col_w_hw):
            row.cells[ci].width = w
        bg = "F8F9FA" if r_idx % 2 == 0 else "FFFFFF"
        format_row(row, bg, TEXT_COLOR, is_header=False, font_size=8.5)
        for cell in row.cells:
            set_cell_borders(cell, top={"val": "single", "sz": "4", "color": "E2E8F0"}, bottom={"val": "single", "sz": "4", "color": "E2E8F0"}, left={"val": "single", "sz": "4", "color": "E2E8F0"}, right={"val": "single", "sz": "4", "color": "E2E8F0"})

    add_p("")
    add_h2("7.2. Kết luận")
    add_p(
        "Tài liệu Thiết kế Kiến trúc (System Architecture Design Document v1.0) của dự án PrivateClass Vision "
        "đã định hình một giải pháp toàn diện, dung hòa xuất sắc giữa bài toán công nghệ thị giác máy tính hiện đại "
        "và đạo đức bảo vệ quyền riêng tư học đường. Với cấu trúc 3 tầng chuẩn mực tại Backend, bộ đệm thông minh bảo vệ Firebase "
        "và năng lực suy luận mạnh mẽ tại Edge, hệ thống sẵn sàng đáp ứng yêu cầu nghiên cứu khoa học cũng như "
        "khả năng ứng dụng thực tế tại các trường đại học và cơ sở giáo dục hiện đại."
    )

    output_path = os.path.abspath("Architecture_Design_Document_PrivateClass_Vision.docx")
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    generate_document()
