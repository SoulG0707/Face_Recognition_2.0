import os
import pickle
import numpy as np
from insightface.app import FaceAnalysis
from PIL import Image
import cv2


def load_image(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        return np.array(img)
    except Exception as e:
        raise ValueError(f"Lỗi khi load ảnh: {e}")


def adjust_image(frame):
    # Điều chỉnh độ sáng và tương phản
    alpha = 1.2  # Tăng tương phản
    beta = 10    # Tăng độ sáng
    adjusted_frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    return adjusted_frame


def encode_faces(image_dir='./Images'):
    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=0, det_size=(800, 800))

    encoded_data = {}
    total = 0

    for dirpath, _, filenames in os.walk(image_dir):
        student_id = os.path.basename(dirpath)  # Lấy MSSV từ tên thư mục
        for fname in filenames:
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            image_path = os.path.join(dirpath, fname)
            try:
                img = load_image(image_path)
                adjusted_img = adjust_image(img)  # Điều chỉnh ảnh
                faces = app.get(adjusted_img)

                if not faces:
                    print(f"Không tìm thấy mặt: {fname}")
                    continue

                for face in faces:
                    emb = face.embedding
                    encoded_data.setdefault(student_id, []).append(emb)
                    total += 1

                print(f"{fname}: {len(faces)} mặt")

            except Exception as e:
                print(f"Lỗi {fname}: {e}")

    print(f"Tổng số embedding: {total}")
    return encoded_data


def save_data(data, filename='face_insight_model.dat'):
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f"Đã lưu: {filename}")


if __name__ == '__main__':
    data = encode_faces()
    save_data(data)
