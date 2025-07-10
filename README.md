Hệ Thống Điểm Danh và Nhận Diện Cảm Xúc Bằng AI
Mô tả
Đây là một hệ thống điểm danh tự động sử dụng nhận diện khuôn mặt và phân tích cảm xúc, được xây dựng dựa trên các thư viện AI như InsightFace, DeepFace và PyQt5. Hệ thống cho phép:

Đăng ký khuôn mặt sinh viên thông qua video.
Lưu trữ và huấn luyện mô hình nhận diện từ ảnh.
Nhận diện khuôn mặt và ghi nhận thông tin điểm danh vào cơ sở dữ liệu SQL Server.
Phân tích cảm xúc của sinh viên trong quá trình nhận diện.
Yêu cầu hệ thống
Hệ điều hành: Windows (đã kiểm tra trên Windows 10/11).
Python: Phiên bản 3.8 hoặc cao hơn.
Thư viện cần cài đặt:
opencv-python
insightface
deepface
torch
pyodbc
PyQt5
pillow
numpy
Cài đặt
Cài đặt Python:
Tải và cài đặt Python từ python.org nếu chưa có.
Cài đặt các thư viện:
Mở terminal và chạy lệnh sau để cài đặt các thư viện cần thiết:
bash

Thu gọn

Bọc lại

Chạy

Sao chép
pip install opencv-python insightface deepface torch pyodbc PyQt5 pillow numpy
Lưu ý: Đảm bảo có ODBC Driver 17 for SQL Server được cài đặt trên máy để kết nối với SQL Server.
Chuẩn bị cơ sở dữ liệu:
Tạo cơ sở dữ liệu attendance_db trên SQL Server (ví dụ: NOCNOC\SQLEXPRESS).
Tạo bảng students với các cột: student_id (VARCHAR), name (VARCHAR), major (VARCHAR).
Tạo bảng attendance với các cột: id (INT, IDENTITY), student_id (VARCHAR), major (VARCHAR), date (DATE), time (TIME), emotion (VARCHAR).
Chuẩn bị dữ liệu ảnh:
Tạo thư mục ./Images để lưu ảnh khuôn mặt của sinh viên.
Mỗi thư mục con trong ./Images mang tên là student_id (ví dụ: ./Images/22205600).
Cấu trúc dự án
train_insightface.py: Script huấn luyện mô hình nhận diện khuôn mặt từ ảnh trong thư mục ./Images và lưu vào file face_insight_model.dat.
register_by_video.py: Script đăng ký khuôn mặt sinh viên bằng video camera, lưu ảnh vào thư mục tương ứng với student_id.
recognize_insightface.py: Ứng dụng giao diện (UI) sử dụng PyQt5 để nhận diện khuôn mặt, phân tích cảm xúc và ghi điểm danh vào cơ sở dữ liệu.
Hướng dẫn sử dụng
1. Đăng ký khuôn mặt
Chạy file register_by_video.py.
Nhập student_id khi được yêu cầu.
Đặt khuôn mặt của sinh viên trước camera, hệ thống sẽ tự động chụp và lưu tối đa 50 ảnh.
Nhấn phím Q để kết thúc quá trình đăng ký.
2. Huấn luyện mô hình
Chạy file train_insightface.py để tạo và lưu mô hình nhận diện từ các ảnh đã đăng ký.
File face_insight_model.dat sẽ được tạo sau khi huấn luyện xong.
3. Nhận diện và điểm danh
Chạy file recognize_insightface.py để khởi động giao diện.
Nhấn "Bắt Đầu Điểm Danh" để bắt đầu nhận diện.
Hệ thống sẽ:
Hiển thị video từ camera.
Nhận diện khuôn mặt và cập nhật thông tin sinh viên (Họ tên, MSSV, Ngành).
Phân tích cảm xúc và ghi vào cơ sở dữ liệu.
Nhấn "Dừng" để tạm dừng, "Thoát" để đóng ứng dụng.
Cấu hình
Kết nối SQL Server: Chỉnh sửa chuỗi kết nối trong recognize_insightface.py nếu cần (ví dụ: đổi SERVER=NOCNOC\SQLEXPRESS).
Đường dẫn ảnh: Đảm bảo thư mục ./Images tồn tại và chứa ảnh theo cấu trúc student_id.
Ghi chú
Đảm bảo camera hoạt động đúng trước khi chạy.
Nếu gặp lỗi kết nối camera, kiểm tra quyền truy cập hoặc thử thay 0 bằng 1 trong cv2.VideoCapture(0).
File emotion_lstm/emotion_lstm.pth cần được cung cấp để phân tích cảm xúc bằng LSTM (nếu không có, hệ thống sẽ dùng DeepFace mặc định).
Giấy phép
Dự án này được phát hành dưới Giấy phép MIT. Bạn được tự do sử dụng, sửa đổi và phân phối mã nguồn.

Liên hệ
Nếu có câu hỏi hoặc cần hỗ trợ, vui lòng liên hệ qua email: [phamthiyenngoc77@gmail.com].