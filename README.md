
# Hệ Thống Điểm Danh và Nhận Diện Cảm Xúc Bằng AI

## 📝 Mô tả

Đây là một hệ thống điểm danh tự động sử dụng nhận diện khuôn mặt và phân tích cảm xúc, được xây dựng bằng các thư viện AI như `InsightFace`, `DeepFace`, `PyQt5`. Hệ thống cho phép:

- Đăng ký khuôn mặt sinh viên qua video.
- Lưu trữ và huấn luyện mô hình nhận diện từ ảnh.
- Nhận diện khuôn mặt và ghi nhận thông tin điểm danh vào cơ sở dữ liệu SQL Server.
- Phân tích cảm xúc sinh viên trong quá trình nhận diện.

---

## 💻 Yêu cầu hệ thống

- Hệ điều hành: Windows (kiểm tra trên Windows 10/11)
- Python: >= 3.8
- Thư viện cần cài:
  - opencv-python
  - insightface
  - deepface
  - torch
  - pyodbc
  - PyQt5
  - pillow
  - numpy

---

## ⚙️ Cài đặt

### 1. Cài đặt Python

Tải và cài đặt từ: https://www.python.org/downloads/

### 2. Cài đặt thư viện Python

Mở terminal và chạy:

```bash
pip install opencv-python insightface deepface torch pyodbc PyQt5 pillow numpy
```

**Lưu ý:** Cài thêm **ODBC Driver 17 for SQL Server** để kết nối với CSDL.

---

## 🗃️ Chuẩn bị cơ sở dữ liệu

Tạo cơ sở dữ liệu `attendance_db` trên SQL Server, ví dụ `NOCNOC\SQLEXPRESS`.

### Bảng `students`

| Cột        | Kiểu dữ liệu |
|------------|---------------|
| student_id | VARCHAR       |
| name       | VARCHAR       |
| major      | VARCHAR       |

### Bảng `attendance`

| Cột       | Kiểu dữ liệu |
|-----------|---------------|
| id        | INT IDENTITY  |
| student_id| VARCHAR       |
| major     | VARCHAR       |
| date      | DATE          |
| time      | TIME          |
| emotion   | VARCHAR       |

---

## 🖼️ Chuẩn bị dữ liệu ảnh

- Tạo thư mục `./Images`
- Mỗi thư mục con có tên là `student_id`, ví dụ: `./Images/22205600`

---

## 📁 Cấu trúc dự án

| File | Mô tả |
|------|-------|
| `train_insightface.py` | Huấn luyện mô hình nhận diện từ ảnh trong `./Images` |
| `register_by_video.py` | Đăng ký khuôn mặt qua camera và lưu ảnh |
| `recognize_insightface.py` | Giao diện điểm danh và phân tích cảm xúc với PyQt5 |

---

## 🚀 Hướng dẫn sử dụng

### 1. Đăng ký khuôn mặt

```bash
python register_by_video.py
```

- Nhập `student_id` khi được yêu cầu.
- Đặt khuôn mặt trước camera.
- Hệ thống sẽ lưu tối đa 50 ảnh.
- Nhấn `Q` để kết thúc.

### 2. Huấn luyện mô hình

```bash
python train_insightface.py
```

- Mô hình được lưu vào `face_insight_model.dat`.

### 3. Nhận diện & điểm danh

```bash
python recognize_insightface.py
```

- Giao diện mở ra.
- Nhấn `Bắt Đầu Điểm Danh` để bắt đầu.
- Hệ thống sẽ:
  - Hiển thị camera.
  - Hiển thị tên, MSSV, ngành.
  - Phân tích cảm xúc và ghi CSDL.
- Nhấn `Dừng` hoặc `Thoát` khi cần.

---

## ⚙️ Cấu hình

- **SQL Server**: Sửa chuỗi kết nối trong `recognize_insightface.py`
- **Ảnh**: Đảm bảo `./Images` tồn tại và đúng cấu trúc thư mục

---

## 🔍 Ghi chú

- Đảm bảo camera hoạt động.
- Có thể thử `cv2.VideoCapture(1)` nếu `0` không được.
- File `emotion_lstm/emotion_lstm.pth` dùng để phân tích cảm xúc bằng LSTM (nếu không có sẽ dùng DeepFace mặc định).

---

## 📄 Giấy phép

Dự án phát hành theo Giấy phép MIT – Tự do sử dụng, sửa đổi và phân phối.

---

## 📬 Liên hệ

Mọi thắc mắc vui lòng liên hệ: **[your_email@example.com]** (thay bằng email thật).
