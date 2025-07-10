import os, cv2, csv, glob
from deepface import DeepFace
import numpy as np

VIDEO_GLOB = "emotion_lstm/dataset/RAVDESS_VIDEO/Actor_01/*.mp4"
FRAME_DIR = "./emotion_lstm/dataset/frames"
CSV_PATH = "./emotion_lstm/dataset/emotion_sequences.csv"
MAX_FRAMES = 15

def emotion_to_vector(emotion):
    emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    vec = [0] * len(emotions)
    if emotion in emotions:
        vec[emotions.index(emotion)] = 1
    return vec

def parse_label(name):
    code = int(name.split("-")[2])
    label_map = {
        1: "neutral", 2: "calm", 3: "happy", 4: "sad",
        5: "angry", 6: "fear", 7: "disgust", 8: "surprise"
    }
    return label_map.get(code, "unknown")

os.makedirs(FRAME_DIR, exist_ok=True)

with open(CSV_PATH, "w", newline="") as f:
    writer = csv.writer(f)

    video_files = glob.glob(VIDEO_GLOB)
    if not video_files:
        print("❌ Không tìm thấy video nào.")
    else:
        print(f"🔍 Tìm thấy {len(video_files)} video.")

    for video_path in video_files:
        file = os.path.basename(video_path)
        name = file[:-4]
        label = parse_label(name)

        cap = cv2.VideoCapture(video_path)
        print(f"🎞️ Đang xử lý video: {file} → nhãn: {label}")

        emotion_seq = []
        frame_id = 0
        saved = 0

        sub_frame_dir = os.path.join(FRAME_DIR, name)
        os.makedirs(sub_frame_dir, exist_ok=True)

        while len(emotion_seq) < MAX_FRAMES:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_id % 3 == 0:
                try:
                    analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    dominant = analysis[0]['dominant_emotion']
                    vec = emotion_to_vector(dominant)
                    emotion_seq.append(vec)

                    # Hiển thị và lưu ảnh (tuỳ chọn)
                    cv2.putText(frame, dominant, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                    save_path = os.path.join(sub_frame_dir, f"{saved}.jpg")
                    cv2.imwrite(save_path, frame)
                    saved += 1
                    cv2.imshow("Frame", frame)
                    cv2.waitKey(1)

                    print(f"✅ Frame {frame_id}: {dominant}")
                except Exception as e:
                    print(f"⚠️ Frame {frame_id}: lỗi phân tích - {e}")

            frame_id += 1

        cap.release()

        if len(emotion_seq) == MAX_FRAMES:
            writer.writerow(np.array(emotion_seq).flatten().tolist() + [label])
            print(f"📦 Ghi chuỗi cảm xúc: {file}")
        else:
            print(f"❌ Bỏ qua {file} (chỉ có {len(emotion_seq)} frame hợp lệ)")

cv2.destroyAllWindows()
print("✅ Hoàn tất xử lý tất cả video.")
