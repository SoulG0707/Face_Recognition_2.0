import cv2
import sys
import pickle
import numpy as np
from datetime import datetime
from insightface.app import FaceAnalysis
from deepface import DeepFace
import torch
import pyodbc

from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QGroupBox
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QTimer

# Load embeddings
with open("face_insight_model.dat", "rb") as f:
    known_faces = pickle.load(f)
print("Số sinh viên đã đăng ký:", len(known_faces))

# Setup InsightFace
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

# Kết nối SQL Server với xử lý lỗi
try:
    conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=NOCNOC\SQLEXPRESS;"
        r"DATABASE=attendance_db;"
        r"Trusted_Connection=yes;"
    )
    cursor = conn.cursor()
    print("Kết nối SQL Server thành công!")
except pyodbc.Error as e:
    print(f"Lỗi kết nối SQL Server: {e}")
    sys.exit(1)

# Trạng thái
running = True
recognizing = False
seen = set()
emotion_sequence = []
MAX_SEQ_LEN = 15

# Load LSTM
try:
    lstm_model = torch.load("emotion_lstm/emotion_lstm.pth")
    lstm_model.eval()
    behavior_labels = ["angry", "disgust", "fear",
                       "happy", "sad", "surprise", "neutral", "calm"]
except Exception:
    lstm_model = None

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Lỗi: Không thể mở camera. Hãy kiểm tra kết nối camera!")
    sys.exit()

def adjust_image(frame):
    return cv2.convertScaleAbs(frame, alpha=1.2, beta=10)

def emotion_to_vector(emotion):
    emotions = ["angry", "disgust", "fear",
                "happy", "sad", "surprise", "neutral"]
    vec = [0] * len(emotions)
    if emotion in emotions:
        vec[emotions.index(emotion)] = 1
    return vec

def mark_attendance(student_id, emotion):
    try:
        cursor.execute(
            "SELECT student_id, major, name FROM students WHERE student_id = ?",
            (student_id,)
        )
        result = cursor.fetchone()
        if not result:
            print(f"MSSV {student_id} không tồn tại trong bảng students.")
            return "Không tìm thấy MSSV"

        student_id, major, name = result
        now = datetime.now()
        cursor.execute(
            "SELECT id FROM attendance WHERE student_id = ? AND CONVERT(date, date) = ?",
            (student_id, now.date())
        )
        if cursor.fetchone():
            print(f"MSSV {student_id} đã điểm danh hôm nay.")
            return f"MSSV {student_id} đã điểm danh."

        cursor.execute(
            "INSERT INTO attendance (student_id, major, date, time, emotion) VALUES (?, ?, ?, ?, ?)",
            (student_id, major, now.date(), now.time(), emotion)
        )
        conn.commit()  # Đảm bảo commit sau mỗi lần chèn
        print(f"Đã ghi điểm danh: {name} (MSSV: {student_id}), Cảm xúc: {emotion}")
        return f"Đã ghi: {name} (MSSV: {student_id}), Cảm xúc: {emotion}"
    except pyodbc.Error as e:
        print(f"Lỗi khi ghi vào SQL Server: {e}")
        return "Lỗi ghi điểm danh"
    except Exception as e:
        print(f"Lỗi không xác định khi ghi điểm danh: {e}")
        return "Lỗi ghi điểm danh"

class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ Thống Điểm Danh AI")
        self.setFixedSize(850, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #F8FAFC;
                font-family: 'Arial', sans-serif;
            }
            QLabel#TitleLabel {
                font-size: 26px;
                font-weight: bold;
                color: #1E3A8A;
                padding: 10px;
            }
            QLabel {
                font-size: 15px;
                color: #1F2937;
            }
            QPushButton {
                padding: 10px 20px;
                font-size: 15px;
                font-weight: 500;
                border-radius: 6px;
                background-color: #2563EB;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton#stopButton {
                background-color: #DC2626;
            }
            QPushButton#stopButton:hover {
                background-color: #B91C1C;
            }
            QPushButton#exitButton {
                background-color: #6B7280;
            }
            QPushButton#exitButton:hover {
                background-color: #4B5563;
            }
            QGroupBox {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 10px;
                font-size: 15px;
                font-weight: bold;
                color: #1E3A8A;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 10px;
            }
        """)

        # Tiêu đề
        title = QLabel("Hệ Thống Điểm Danh và Nhận Diện Cảm Xúc")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Khung video
        self.video_label = QLabel()
        self.video_label.setFixedSize(600, 400)
        self.video_label.setStyleSheet("border: 2px solid #E5E7EB; border-radius: 6px; background-color: #FFFFFF;")

        # Nhãn trạng thái
        self.attendance_label = QLabel("Chờ điểm danh...")
        self.emotion_label = QLabel("Cảm xúc: Chưa nhận diện")
        self.attendance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emotion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.attendance_label.setStyleSheet("font-size: 16px; color: #16A34A; font-weight: 500;")
        self.emotion_label.setStyleSheet("font-size: 15px; color: #1F2937;")

        # Nhóm thông tin sinh viên
        student_group = QGroupBox("Thông Tin Sinh Viên")
        student_layout = QVBoxLayout()
        self.name_label = QLabel("Họ tên: ---")
        self.id_label = QLabel("MSSV: ---")
        self.major_label = QLabel("Ngành: ---")
        for label in [self.name_label, self.id_label, self.major_label]:
            label.setStyleSheet("font-size: 14px; color: #1F2937;")
        student_layout.addWidget(self.name_label)
        student_layout.addWidget(self.id_label)
        student_layout.addWidget(self.major_label)
        student_group.setLayout(student_layout)

        # Nhãn thời gian
        self.time_label = QLabel(f"Thời gian: 09:21 11/07/2025") # Mặc định thời gian, sẽ cập nhật sau khi khởi động ứng dụng
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 14px; color: #4B5563;")

        # Nút điều khiển
        self.start_btn = QPushButton("Bắt Đầu Điểm Danh")
        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setObjectName("stopButton")
        self.exit_btn = QPushButton("Thoát")
        self.exit_btn.setObjectName("exitButton")

        # Timer cập nhật thời gian
        self.clock = QTimer()
        self.clock.timeout.connect(self.update_time)
        self.clock.start(1000)

        # Kết nối nút
        self.start_btn.clicked.connect(self.start_recognition)
        self.stop_btn.clicked.connect(self.stop_recognition)
        self.exit_btn.clicked.connect(self.close_app)

        # Bố cục chính
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Bố cục video và trạng thái
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_label, alignment=Qt.AlignmentFlag.AlignCenter)
        video_layout.addWidget(self.emotion_label)
        video_layout.addWidget(self.attendance_label)

        # Bố cục nút
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.exit_btn)

        # Thêm widgets vào bố cục chính
        main_layout.addWidget(title)
        main_layout.addLayout(video_layout)
        main_layout.addWidget(student_group)
        main_layout.addWidget(self.time_label)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_time(self):
        now = datetime.now().strftime("%H:%M %d/%m/%Y")
        self.time_label.setText(f"Thời gian: {now}")

    def update_frame(self):
        global recognizing, seen, emotion_sequence
        ret, frame = cap.read()
        if not ret:
            self.video_label.setText("Không thể truy cập camera!")
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        adjusted = adjust_image(rgb)
        h, w, ch = adjusted.shape
        img = QImage(adjusted.data, w, h, ch * w, QImage.Format_RGB888)
        scaled_img = img.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(QPixmap.fromImage(scaled_img))

        if recognizing:
            faces = app.get(adjusted)
            for face in faces:
                if not hasattr(face, "embedding"):
                    continue
                emb = face.embedding
                student_id = "Unknown"
                best_score = 0.0
                for known_id, emb_list in known_faces.items():
                    for known_emb in emb_list:
                        score = float(
                            np.dot(emb, known_emb) / (np.linalg.norm(emb) * np.linalg.norm(known_emb)))
                        if score > best_score:
                            best_score = score
                            student_id = known_id
                if best_score < 0.7:
                    self.attendance_label.setText("Chưa đăng ký thông tin của người này, vui lòng đăng ký trước.")
                    self.name_label.setText("Họ tên: ---")
                    self.id_label.setText("MSSV: ---")
                    self.major_label.setText("Ngành: ---")
                elif best_score >= 0.7:  
                    try:
                        if lstm_model and len(emotion_sequence) == MAX_SEQ_LEN:
                            input_tensor = torch.tensor(
                                [emotion_sequence], dtype=torch.float32)
                            output = lstm_model(input_tensor)
                            pred = torch.argmax(output, dim=1).item()
                            current_emotion = behavior_labels[int(pred)]
                        else:
                            analysis = DeepFace.analyze(
                                adjusted, actions=["emotion"], enforce_detection=False)
                            current_emotion = analysis[0]["dominant_emotion"]
                        vec = emotion_to_vector(current_emotion)
                        emotion_sequence.append(vec)
                        if len(emotion_sequence) > MAX_SEQ_LEN:
                            emotion_sequence.pop(0)
                        if student_id not in seen:
                            seen.add(student_id)
                            msg = mark_attendance(student_id, current_emotion)
                            self.attendance_label.setText(msg)
                            cursor.execute(
                                "SELECT name, major FROM students WHERE student_id = ?", (student_id,))
                            result = cursor.fetchone()
                            if result:
                                name, major = result
                                self.name_label.setText(f"Họ tên: {name}")
                                self.id_label.setText(f"MSSV: {student_id}")
                                self.major_label.setText(f"Ngành: {major}")
                        self.emotion_label.setText(
                            f"Cảm xúc: {current_emotion}")
                    except Exception as e:
                        print("Lỗi nhận diện cảm xúc:", str(e))
                        self.emotion_label.setText("Cảm xúc: Lỗi")

    def start_recognition(self):
        global recognizing, seen
        recognizing = True
        seen.clear()
        self.attendance_label.setText("Đang nhận diện...")
        self.name_label.setText("Họ tên: ---")
        self.id_label.setText("MSSV: ---")
        self.major_label.setText("Ngành: ---")

    def stop_recognition(self):
        global recognizing, emotion_sequence
        recognizing = False
        emotion_sequence.clear()
        self.attendance_label.setText("Đã dừng nhận diện")

    def close_app(self):
        global running
        running = False
        self.timer.stop()
        cap.release()
        conn.close()  
        self.close()

if __name__ == "__main__":
    app_gui = QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app_gui.exec_())