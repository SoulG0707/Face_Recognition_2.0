import cv2
import os
from insightface.app import FaceAnalysis

# Cấu hình
SAVE_DIR = "./Images"
FRAME_SKIP = 5         # Lưu mỗi 5 frame
MAX_IMAGES = 50        # Tối đa 50 ảnh mỗi người


def adjust_image(frame):
    alpha = 1.2
    beta = 10
    return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)


def register_from_video(student_id):
    save_path = os.path.join(SAVE_DIR, student_id)
    os.makedirs(save_path, exist_ok=True)

    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(800, 800))

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Không mở được camera.")
        return

    print("Bắt đầu thu thập ảnh. Nhấn Q để thoát.")
    count = 0
    frame_id = 0

    try:
        while count < MAX_IMAGES:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_id += 1
            if frame_id % FRAME_SKIP != 0:
                continue

            adjusted_frame = adjust_image(frame)

            # Hiển thị hướng dẫn
            h, w = adjusted_frame.shape[:2]
            cv2.putText(adjusted_frame, "Press Q to stop",
                        (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            faces = app.get(adjusted_frame)
            if faces:
                face = faces[0]
                box = face.bbox.astype(int)
                cv2.rectangle(
                    adjusted_frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

                filename = os.path.join(save_path, f"{count + 1}.jpg")
                cv2.imwrite(filename, adjusted_frame)
                print(f"Đã lưu: {filename}")
                count += 1

            try:
                cv2.imshow("Đăng ký khuôn mặt", adjusted_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except cv2.error:
                print("error")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"Đã thu thập {count} ảnh cho MSSV {student_id}")


if __name__ == '__main__':
    student_id = input("Nhập MSSV của sinh viên cần đăng ký: ")
    register_from_video(student_id)
