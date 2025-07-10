# emotion_lstm/train_lstm.py
import torch, csv
import torch.nn as nn
from sklearn.model_selection import train_test_split
import numpy as np

class EmotionLSTM(nn.Module):
    def __init__(self, input_size=7, hidden_size=64, output_size=8):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

# Load CSV
X, y = [], []
label_map = {'angry':0, 'disgust':1, 'fear':2, 'happy':3, 'sad':4, 'surprise':5, 'neutral':6, 'calm':7}

with open('./emotion_lstm/dataset/emotion_sequences.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        *features, label = row
        X.append(np.array(features, dtype=np.float32).reshape(15, 7))
        y.append(label_map[label])

X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = EmotionLSTM()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

EPOCHS = 20
for epoch in range(EPOCHS):
    model.train()
    inputs = torch.tensor(X_train)
    targets = torch.tensor(y_train)
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

# Lưu mô hình
torch.save(model, "./emotion_lstm/emotion_lstm.pth")
print("✅ Đã lưu mô hình.")
