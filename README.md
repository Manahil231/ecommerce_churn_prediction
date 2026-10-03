# ShopIQ: E-Commerce Customer Intelligence

An end-to-end Data Science project built for the **Data Science Final Hackathon**. It starts from a raw SQLite database and ends with a deployed **Streamlit** app that has a sales dashboard, a customer churn predictor and a review sentiment analyzer.

**Live app:** LIVE_APP_LINK_HERE

---

## 1. Project summary

| Part | What was done |
|---|---|
| Database | `ecommerce_hackathon.db` (SQLite) with 4 related tables: customers (8,000), products (1,000), orders (65,000), reviews (26,000) |
| Task A | Inspected all tables, found data quality problems and cleaned them (every decision explained in the notebook) |
| Task B | 5 business questions answered with **SQL** (`queries.sql`) |
| Task C | 4 charts and 3 business insights |
| Task D | **Churn model** (Logistic Regression vs Random Forest) with no data leakage, plus one engineered feature (`tenure_days`) |
| Task E | **Neural network** (32 - 16 - 1) compared with the ML models, plus an overfitting / underfitting check |
| Task F | **Sentiment model** (TF-IDF + Logistic Regression) |
| Task G | **Streamlit app** with 3 pages (Dashboard, Churn Prediction, Sentiment Analysis) |

## 2. Data quality issues found and how they were handled

| Problem | Decision |
|---|---|
| City and category names written in different ways (case, extra spaces) | Cleaned with `strip` and `title` (44 cities became 13, 19 categories became 8) |
| Missing `age` (100), `brand` (20), `payment_method` (55), `delivery_days` (40) | Filled with median or "Unknown", rows kept |
| Invalid order dates (30) and quantity = 0 (45) | Removed (only 75 of 65,000 orders) |
| Negative unit price (35) | Replaced with the product's catalog price, not deleted |
| Reviews with empty text (90) or rating outside 1-5 (25) | Removed (they cannot give a sentiment label) |
| Reviews with invalid date (16) | Kept, because the sentiment model does not use the date |
| Shared emails (35) | Kept, they belong to different customers |

**Net revenue** = quantity x price x (1 - discount), counting only valid orders that were **not returned**.

## 3. Results

### Churn prediction (Task D and E)
Churn = a customer who bought before 31 May 2026 and made **no purchase** between 1 June and 31 August 2026. Features use only information up to 31 May (no data leakage). We used the **8 required features plus one engineered feature, `tenure_days`** (account age in days).

| Model | Accuracy | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| **Logistic Regression (final)** | 0.771 | 0.794 | 0.773 | 0.843 |
| Random Forest | 0.774 | 0.855 | 0.787 | 0.844 |
| Neural Network (32-16-1) | 0.778 | 0.858 | 0.791 | 0.841 |

- **Feature engineering helped the most:** adding `tenure_days` raised accuracy from 0.720 to 0.771 and ROC-AUC from 0.785 to 0.843. It shows how fast a customer buys (orders compared to the age of the account). Other extra features (recent orders, reviews, discount) added almost nothing.
- All three models perform almost the same, so the **simplest and most explainable model (Logistic Regression)** was selected.
- **Overfitting check:** Logistic Regression and the neural network fit well (train and test scores are close). Random Forest overfits slightly (train ROC-AUC 0.90, test 0.84).
- **Underfitting check:** more powerful models did not do better, so the limit comes from the data, not from the model.
- Most important features: `total_orders` (more orders = less churn) and `tenure_days` (an old account with few orders = more churn).

### Sentiment analysis (Task F)
Labels: rating 1-2 = Negative, 3 = Neutral, 4-5 = Positive. The model scores about **100%** on test data.

**Limitation:** the reviews look generated from templates (each sentence belongs to only one sentiment, and there are only about 4,485 unique reviews out of 25,885), so this score will not carry over to real-world reviews with sarcasm, spelling mistakes or mixed opinions. Duplicate sentences were removed before training to avoid leakage.

## 4. Three business insights

1. **The company depends too much on Electronics.** Electronics gives about 70% of the net revenue, and only two headphone products give about 20%. If supply or demand for these few products drops, more than half of the income can fall at once. The company should grow the other categories (Home & Kitchen, Fashion, Sports).
2. **Fashion has the highest return rate (about 11%)**, almost double the overall 6.7%. About 7.6% of the revenue goes back through returns. Better size charts and product photos can reduce returns and their handling cost.
3. **Karachi and Lahore are the biggest markets (about 44% of revenue) and revenue grows every month.** Faster delivery and marketing in these two cities will pay off the most. The small drop in August 2026 compared with July should be watched. For retention, customers with **few orders compared to the age of their account** are the most likely to churn, so they should receive win-back offers first.

## 5. Project structure

```
.
├── app.py                      # Streamlit app (3 pages)
├── ecommerce_hackathon.db      # SQLite database
├── churn_model.pkl             # saved churn pipeline
├── sentiment_model.pkl         # saved sentiment pipeline
├── queries.sql                 # the 5 required SQL queries
├── 01_cleaning_sql_eda.ipynb   # Task A, B, C
├── 02_churn_model.ipynb        # Task D, E
├── 03_sentiment_model.ipynb    # Task F
├── requirements.txt
└── .streamlit/config.toml      # app theme
```

## 6. How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The notebooks additionally need `matplotlib`, `seaborn`, `jupyter` and `tensorflow` (only for the neural network in `02_churn_model.ipynb`). The app itself does not need TensorFlow.

## 7. Tech stack

Python, SQLite, SQL, pandas, scikit-learn, TensorFlow/Keras, Altair, Streamlit.
