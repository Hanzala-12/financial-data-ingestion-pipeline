🧠 Sentiment Pipeline TODO (Two-Layer Strategy)
🎯 Objective

Build a modular Python sentiment classification pipeline for financial text using:

Layer A: VADER (Reddit/Twitter)
Layer B: FinBERT (News headlines)
📦 Setup & Dependencies
 Install required libraries:
pandas
numpy
vaderSentiment
transformers
pyarrow (for parquet)
tqdm
 Initialize project structure:
project/
│── data/
│   ├── raw/
│   └── processed/
│── src/
│   ├── sentiment/
│   │   ├── vader_model.py
│   │   ├── finbert_model.py
│   │   ├── processor.py
│   │   ├── aggregator.py
│   │   └── utils.py
│── TODO.md
🧩 Layer A — VADER (Social Media)
 Create vader_model.py
 Initialize VADER analyzer
 Implement function:
def classify_vader(text: str) -> tuple[str, float]:
 Logic:
compound > 0.05 → positive
compound < -0.05 → negative
otherwise → neutral
 Return (label, score)
🧩 Layer B — FinBERT (News Headlines)
 Create finbert_model.py
 Load model using HuggingFace:
pipeline("text-classification", model="ProsusAI/finbert")
 Implement function:
def classify_finbert(text: str) -> tuple[str, float]:
 Output:
label: positive | negative | neutral
score: probability mapped to confidence
 ⚠️ Do NOT fine-tune model
🔄 Data Processing Pipeline
 Create processor.py
 Implement:
def process_parquet(file_path: str) -> pd.DataFrame:
 Steps:
Load parquet file
Detect source column:
news → FinBERT
reddit/twitter → VADER
Apply appropriate model
Add columns:
label
score
Ensure columns exist:
timestamp
ticker
source
⏱️ Time-Series Aggregation
 Create aggregator.py
 Implement:
def aggregate_sentiment(df: pd.DataFrame) -> pd.DataFrame:
 Apply hourly grouping:
df["hour"] = df["timestamp"].dt.floor("H")
 Aggregate:
pos_count
neg_count
neu_count
mean_score
text_count
 Compute:
net_sentiment = (pos_count - neg_count) / (text_count + 1e-6)
📊 Final Output
 Ensure output columns:
hour
ticker
net_sentiment
mean_score
pos_count
neg_count
text_count
 Save file:
data/processed/sentiment_hourly.parquet
🧪 Testing
 Unit test each module:
VADER classifier
FinBERT classifier
Processing function
Aggregation logic
 Validate:
No missing timestamps
Correct label distribution
No division errors
🚀 Optional Improvements (Later)
 Batch inference for FinBERT (performance)
 Logging + error handling
 Config file for thresholds
 Parallel processing for large datasets
🧠 Agent Instructions
Follow modular design (no monolithic scripts)
Each function must be independently testable
Avoid hardcoding paths (use config or constants)
Keep pipeline reproducible and clean