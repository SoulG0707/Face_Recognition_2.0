
# AI-Based Attendance and Emotion Recognition System

## Description

This is an automated attendance system that uses facial recognition and emotion analysis, built with AI libraries such as `InsightFace`, `DeepFace`, and `PyQt5`. The system allows:

- Student face registration via webcam video.
- Storing and training facial recognition models from images.
- Recognizing faces and logging attendance information into a SQL Server database.
- Analyzing student emotions during recognition.

---

## System Requirements

- Operating System: Windows (tested on Windows 10/11)
- Python: >= 3.8
- Required libraries:
  - opencv-python
  - insightface
  - deepface
  - torch
  - pyodbc
  - PyQt5
  - pillow
  - numpy

---

## Installation

### 1. Install Python

Download and install from: https://www.python.org/downloads/

### 2. Install required Python libraries

Open terminal and run:

```bash
pip install opencv-python insightface deepface torch pyodbc PyQt5 pillow numpy
```

**Note:** Ensure **ODBC Driver 17 for SQL Server** is installed for database connection.

---

## Prepare the Database

Create a database `attendance_db` on SQL Server (e.g., `NOCNOC\SQLEXPRESS`).

### Table `students`

| Column      | Data Type |
|-------------|------------|
| student_id  | VARCHAR    |
| name        | VARCHAR    |
| major       | VARCHAR    |

### Table `attendance`

| Column      | Data Type |
|-------------|------------|
| id          | INT IDENTITY |
| student_id  | VARCHAR       |
| major       | VARCHAR       |
| date        | DATE          |
| time        | TIME          |
| emotion     | VARCHAR       |

---

## Prepare Image Data

- Create folder `./Images`
- Each subfolder should be named as the `student_id`, e.g., `./Images/22205600`

---

## Project Structure

| File | Description |
|------|-------------|
| `train_insightface.py` | Train face recognition model from images in `./Images` |
| `register_by_video.py` | Register student face via webcam and save images |
| `recognize_insightface.py` | GUI application using PyQt5 for recognition and emotion logging |

---

## Usage Guide

### 1. Register Student Face

```bash
python register_by_video.py
```

- Enter `student_id` when prompted.
- Place student’s face in front of the camera.
- The system will automatically capture and save up to 50 images.
- Press `Q` to finish.

### 2. Train the Model

```bash
python train_insightface.py
```

- The model will be saved as `face_insight_model.dat`.

### 3. Run Recognition and Attendance

```bash
python recognize_insightface.py
```

- The GUI will appear.
- Click "Start Attendance" to begin.
- The system will:
  - Show live camera feed.
  - Display student info (name, ID, major).
  - Analyze emotion and save to database.
- Click "Pause" or "Exit" as needed.

---

## Configuration

- **SQL Server**: Edit connection string in `recognize_insightface.py`
- **Images**: Ensure `./Images` exists and has correct folder structure

---

## Notes

- Make sure the camera is functional.
- If `cv2.VideoCapture(0)` fails, try `cv2.VideoCapture(1)`.
- For emotion detection using LSTM, ensure `emotion_lstm/emotion_lstm.pth` exists (otherwise fallback to DeepFace).

---

## License

This project is released under the MIT License – free to use, modify, and distribute.

---

## 📬 Contact

For questions or support, please contact: **[phamthiyenngoc77@gmail.com]**