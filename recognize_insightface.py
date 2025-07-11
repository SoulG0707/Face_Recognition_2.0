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

def mark_attendance(student_id, action, emotion):
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
        if action == "check_in":
            cursor.execute(
                "SELECT id FROM attendance WHERE student_id = ? AND CONVERT(date, date) = ? AND in_time IS NOT NULL",
                (student_id, now.date())
            )
            if cursor.fetchone():
                print(f"MSSV {student_id} đã check-in hôm nay.")
                return f"MSSV {student_id} đã check-in."
            print(f"Thực hiện INSERT với MSSV: {student_id}, Emotion: {emotion}")
            cursor.execute(
                "INSERT INTO attendance (student_id, major, date, in_time, emotion) VALUES (?, ?, ?, ?, ?)",
                (student_id, major, now.date(), now.time(), emotion if emotion else "N/A")
            )
            conn.commit()
            print(f"Đã check-in: {name} (MSSV: {student_id}), Cảm xúc: {emotion if emotion else 'N/A'} - Ghi vào SQL thành công")
            return f"Đã check-in: {name} (MSSV: {student_id}), Cảm xúc: {emotion if emotion else 'N/A'}"
        elif action == "check_out":
            cursor.execute(
                "SELECT id, in_time FROM attendance WHERE student_id = ? AND CONVERT(date, date) = ? AND in_time IS NOT NULL AND out_time IS NULL",
                (student_id, now.date())
            )
            record = cursor.fetchone()
            if not record:
                print(f"MSSV {student_id} chưa check-in hôm nay hoặc đã check-out.")
                return f"MSSV {student_id} chưa check-in hoặc đã check-out."
            print(f"Thực hiện UPDATE cho MSSV: {student_id}")
            cursor.execute(
                "UPDATE attendance SET out_time = ? WHERE id = ?",
                (now.time(), record[0])
            )
            conn.commit()
            print(f"Đã check-out: {name} (MSSV: {student_id}) - Ghi vào SQL thành công")
            return f"Đã check-out: {name} (MSSV: {student_id})"
    except pyodbc.Error as e:
        print(f"Lỗi khi ghi vào SQL Server: {e}")
        return f"Lỗi ghi điểm danh: {str(e)}"
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
        self.time_label = QLabel(f"Thời gian: 10:27 11/07/2025")  # Đặt thời gian hiện tại
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 14px; color: #4B5563;")

        # Nút điều khiển
        self.start_btn = QPushButton("Bắt Đầu Điểm Danh")
        self.check_in_btn = QPushButton("Check-in")
        self.check_out_btn = QPushButton("Check-out")
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
        self.check_in_btn.clicked.connect(self.check_in)
        self.check_out_btn.clicked.connect(self.check_out)
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
        btn_layout.addWidget(self.check_in_btn)
        btn_layout.addWidget(self.check_out_btn)
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

    def start_recognition(self):
        global recognizing
        recognizing = True
        self.attendance_label.setText("Đang nhận diện...")
        self.name_label.setText("Họ tên: ---")
        self.id_label.setText("MSSV: ---")
        self.major_label.setText("Ngành: ---")

    def update_frame(self):
        global recognizing, seen, emotion_sequence
        if not recognizing:
            return
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
            print(f"Dự đoán: {student_id}, Độ tương đồng: {best_score:.2f}")  # Log nhận diện
            if best_score < 0.7:
                print(f"Khuôn mặt chưa đăng ký: Độ tương đồng {best_score:.2f} < 0.7")
                self.attendance_label.setText("Chưa đăng ký thông tin của người này")
                self.name_label.setText("Họ tên: ---")
                self.id_label.setText("MSSV: ---")
                self.major_label.setText("Ngành: ---")
                self.emotion_label.setText("Cảm xúc: Chưa nhận diện")
            elif best_score >= 0.7:
                try:
                    current_emotion = None
                    if lstm_model and len(emotion_sequence) == MAX_SEQ_LEN:
                        print(f"Đang sử dụng LSTM để dự đoán cảm xúc, độ dài sequence: {len(emotion_sequence)}")
                        input_tensor = torch.tensor(
                            [emotion_sequence], dtype=torch.float32)
                        output = lstm_model(input_tensor)
                        pred = torch.argmax(output, dim=1).item()
                        current_emotion = behavior_labels[int(pred)]
                        print(f"LSTM dự đoán: {current_emotion}")
                    else:
                        print(f"Đang sử dụng DeepFace để nhận diện cảm xúc trên ảnh {adjusted.shape}")
                        try:
                            analysis = DeepFace.analyze(
                                adjusted, actions=["emotion"], enforce_detection=False)
                            current_emotion = analysis[0]["dominant_emotion"]
                            print(f"DeepFace nhận diện: {current_emotion}")
                        except Exception as e:
                            print(f"Lỗi nhận diện cảm xúc với DeepFace: {e}")
                            current_emotion = "Không xác định"
                    vec = emotion_to_vector(current_emotion)
                    emotion_sequence.append(vec)
                    if len(emotion_sequence) > MAX_SEQ_LEN:
                        emotion_sequence.pop(0)
                    print(f"Cảm xúc hiện tại: {current_emotion}, Độ dài sequence: {len(emotion_sequence)}")
                    self.attendance_label.setText(f"Nhận diện: {student_id}")
                    cursor.execute(
                        "SELECT name, major FROM students WHERE student_id = ?", (student_id,))
                    result = cursor.fetchone()
                    if result:
                        name, major = result
                        self.name_label.setText(f"Họ tên: {name}")
                        self.id_label.setText(f"MSSV: {student_id}")
                        self.major_label.setText(f"Ngành: {major}")
                    self.emotion_label.setText(
                        f"Cảm xúc: {current_emotion if current_emotion else 'Không nhận diện'}")
                except Exception as e:
                    print(f"Lỗi tổng quát khi nhận diện: {e}")
                    self.emotion_label.setText("Cảm xúc: Lỗi")

    def check_in(self):
        global recognizing
        if not recognizing:
            self.attendance_label.setText("Vui lòng bắt đầu nhận diện trước!")
            return
        faces = app.get(adjust_image(cap.read()[1]))
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
            if best_score >= 0.7:
                # Lấy cảm xúc từ giao diện
                current_emotion = self.emotion_label.text().replace("Cảm xúc: ", "").strip()
                print(f"Chuẩn bị check-in cho MSSV: {student_id}, Cảm xúc lấy từ giao diện: {current_emotion}")
                msg = mark_attendance(student_id, "check_in", current_emotion)
                print(f"Kết quả check-in: {msg}")
                self.attendance_label.setText(msg)
                cursor.execute(
                    "SELECT name, major FROM students WHERE student_id = ?", (student_id,))
                result = cursor.fetchone()
                if result:
                    name, major = result
                    self.name_label.setText(f"Họ tên: {name}")
                    self.id_label.setText(f"MSSV: {student_id}")
                    self.major_label.setText(f"Ngành: {major}")
            else:
                self.attendance_label.setText("Khuôn mặt chưa đăng ký!")

    def check_out(self):
        global recognizing
        if not recognizing:
            self.attendance_label.setText("Vui lòng bắt đầu nhận diện trước!")
            return
        faces = app.get(adjust_image(cap.read()[1]))
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
            if best_score >= 0.7:
                print(f"Chuẩn bị check-out cho MSSV: {student_id}")
                msg = mark_attendance(student_id, "check_out", None)
                print(f"Kết quả check-out: {msg}")
                self.attendance_label.setText(msg)
                cursor.execute(
                    "SELECT name, major FROM students WHERE student_id = ?", (student_id,))
                result = cursor.fetchone()
                if result:
                    name, major = result
                    self.name_label.setText(f"Họ tên: {name}")
                    self.id_label.setText(f"MSSV: {student_id}")
                    self.major_label.setText(f"Ngành: {major}")
            else:
                self.attendance_label.setText("Khuôn mặt chưa đăng ký!")

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
        conn.close()  # Đóng kết nối SQL khi thoát
        self.close()

if __name__ == "__main__":
    app_gui = QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app_gui.exec_())