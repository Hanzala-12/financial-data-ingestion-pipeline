Project: Binary Market Direction Prediction (PyTorch)
🔹 1. Data Preparation
 Load price_df and sentiment_ts
 Merge datasets on ["hour", "ticker"] → features
 Define feature columns:
 open, high, low, close, volume
 net_sentiment, mean_score, text_count
 returns_1h (pct_change)
 volatility_6h (rolling std)
 Handle missing values (fill or drop)
🔹 2. Build Sliding Window Dataset
 Set WINDOW = 24
 Loop over dataset to construct:
 X: shape (samples, 24, 10)
 y: binary label (1 if next return > 0 else 0)
 Convert X, y to NumPy arrays
 Split dataset (NO shuffle):
 70% Train
 15% Validation
 15% Test
🔹 3. PyTorch Dataset & DataLoader
 Create custom Dataset class
 Create DataLoader for:
 Train
 Validation
 Test
🔹 4. Define Models
Model 1 — Vanilla RNN
 nn.RNN(input_size=10, hidden_size=64, num_layers=2, dropout=0.1)
 Add Linear(64 → 1)
 Add Sigmoid
Model 2 — LSTM
 nn.LSTM(input_size=10, hidden_size=128, num_layers=2, dropout=0.2)
 Add Linear(128 → 1)
 Add Sigmoid
Model 3 — GRU
 nn.GRU(input_size=10, hidden_size=128, num_layers=2, dropout=0.2)
 Add Linear(128 → 1)
 Add Sigmoid
🔹 5. Training Setup (Shared for All Models)
 Loss: BCELoss
 Optimizer: Adam
 Epochs: 30
 Implement Early Stopping:
 Monitor val_f1
 Patience = 5
 Save best model
🔹 6. Training Loop (Reusable Function)
 Loop over epochs:
 Train phase:
 Forward pass
 Compute loss
 Backpropagation
 Optimizer step
 Validation phase:
 Compute val_accuracy
 Compute val_f1
 Apply early stopping logic
🔹 7. MLflow Tracking

For EACH model:

 Wrap training in mlflow.start_run()
 Log parameters:
 model name
 learning rate
 window size
 hidden size
 Log metrics per epoch:
 val_accuracy
 val_f1
 Log final model:
 mlflow.pytorch.log_model
 Log artifacts (e.g., test set)
🔹 8. Evaluation
 Use sklearn.metrics to compute:
 Accuracy
 F1-score
 Precision
 Recall
 AUC-ROC
 (Optional regression head):
 RMSE
 MAE
 MAPE
🔹 9. Final Comparison Table
 After training all models, print:
Model | Accuracy | F1 | RMSE (if available)
------------------------------------------
RNN   |   ...    | ...| ...
LSTM  |   ...    | ...| ...
GRU   |   ...    | ...| ...
🔹 10. Deliverables
 Trained models (saved)
 MLflow experiment logs
 Final comparison table
 Clean, reusable training pipeline