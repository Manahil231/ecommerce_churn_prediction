import re
import sqlite3
from pathlib import Path

import altair as alt
import joblib
import pandas as pd
import streamlit as st

# =====================================================================
# 1) Settings: paths, colors and page setup
# =====================================================================
BASE_DIR = Path(__file__).parent                 # folder where app.py lives
DB_PATH = BASE_DIR / "ecommerce_hackathon.db"
CHURN_MODEL_PATH = BASE_DIR / "churn_model.pkl"
SENTIMENT_MODEL_PATH = BASE_DIR / "sentiment_model.pkl"

ORANGE = "#FF6B35"
NAVY = "#1F2A44"
GREEN = "#2E9E6B"
RED = "#D64545"
AMBER = "#F2A93B"

st.set_page_config(page_title="AI Powered E-Commerce Customer Intelligence System", page_icon="🛍️", layout="wide")

# =====================================================================
# 2) Design (CSS): banner, cards, badges
# =====================================================================
st.markdown(
    """
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1250px;}
.hero {
    background: linear-gradient(120deg, #FF6B35 0%, #F7931E 60%, #FFB347 100%);
    color: white; padding: 28px 34px; border-radius: 18px; margin-bottom: 22px;
    box-shadow: 0 8px 22px rgba(255,107,53,0.25);
}
.hero h1 {margin: 0; font-size: 1.9rem; color: white; line-height: 1.25;}
.hero p {margin: 6px 0 0 0; font-size: 1.05rem; opacity: 0.95; color: white;}
.kpi {
    background: #FFFFFF; border-left: 6px solid #FF6B35; border-radius: 14px;
    padding: 16px 18px; box-shadow: 0 3px 12px rgba(31,42,68,0.08); height: 100%;
}
.kpi .label {font-size: 0.82rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.04em;}
.kpi .value {font-size: 1.55rem; font-weight: 700; color: #1F2A44; margin-top: 2px; white-space: nowrap;}
.kpi .label {white-space: nowrap;}
.grid5 {display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px;}
.kpi .icon {font-size: 1.3rem; float: right;}
.pcard {
    background: #FFFFFF; border: 1px solid #FFE0D1; border-radius: 16px; padding: 16px;
    box-shadow: 0 3px 10px rgba(31,42,68,0.06); height: 100%;
}
.pcard .rank {background: #FF6B35; color: white; border-radius: 50%; width: 28px; height: 28px;
    display: inline-block; text-align: center; line-height: 28px; font-weight: 700;}
.pcard .name {font-weight: 700; color: #1F2A44; margin: 10px 0 4px 0; min-height: 44px;}
.pcard .cat {display: inline-block; background: #FFF3EC; color: #C2410C; border-radius: 999px;
    padding: 2px 10px; font-size: 0.78rem;}
.pcard .rev {font-size: 1.15rem; font-weight: 700; color: #FF6B35; margin-top: 8px;}
.section-title {font-size: 1.25rem; font-weight: 700; color: #1F2A44; margin: 26px 0 10px 0;
    border-bottom: 3px solid #FF6B35; display: inline-block; padding-bottom: 2px;}
.verdict {border-radius: 16px; padding: 20px 24px; color: white; margin-bottom: 14px;}
.verdict h2 {margin: 0; color: white;}
.verdict p {margin: 4px 0 0 0; color: white; opacity: 0.95;}
.note {background: #FFF3EC; border-left: 5px solid #FF6B35; border-radius: 10px; padding: 12px 16px;
    color: #1F2A44; font-size: 0.92rem;}
.footer {text-align: center; color: #9CA3AF; font-size: 0.85rem; margin-top: 40px;}
</style>
""",
    unsafe_allow_html=True,
)


# =====================================================================
# 3) Helper functions
# =====================================================================
def money(value):
    """Shorten big numbers: 865628304 -> Rs 865.6M"""
    if value >= 1_000_000_000:
        return "Rs " + format(value / 1_000_000_000, ".2f") + "B"
    if value >= 1_000_000:
        return "Rs " + format(value / 1_000_000, ".1f") + "M"
    if value >= 1_000:
        return "Rs " + format(value / 1_000, ".1f") + "K"
    return "Rs " + format(value, ".0f")


def kpi_card(icon, label, value):
    return (
        '<div class="kpi"><span class="icon">' + icon + '</span><div class="label">' + label
        + '</div><div class="value">' + value + "</div></div>"
    )


def clean_text(text):
    """Clean a review exactly the way it was cleaned when the model was trained."""
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@st.cache_data
def run_sql(query):
    """Run a SQL query on the database and return a table (the result is cached, so it stays fast)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


@st.cache_resource
def load_models():
    return joblib.load(CHURN_MODEL_PATH), joblib.load(SENTIMENT_MODEL_PATH)


# All cleaning rules in one place: invalid date, quantity 0, negative price, returned orders
SALES_CTE = """
WITH sales AS (
    SELECT o.order_id, o.customer_id, o.product_id,
           date(o.order_date) AS order_date,
           o.quantity,
           CASE WHEN o.unit_price > 0 THEN o.unit_price ELSE p.unit_price END AS price,
           o.discount
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    WHERE date(o.order_date) IS NOT NULL
      AND o.quantity > 0
      AND o.returned = 0
)
"""

# =====================================================================
# 4) Header (banner) and sidebar menu
# =====================================================================
st.markdown(
    '<div class="hero"><h1>🛍️ AI Powered E-Commerce Customer Intelligence System</h1>'
    "<p>Sales dashboard, customer churn prediction and review sentiment analysis in one place.</p></div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("## 🛍️ Customer Intelligence")
page = st.sidebar.radio(
    "Menu",
    ["📊 Dashboard", "🔮 Churn Prediction", "💬 Sentiment Analysis"],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: ecommerce_hackathon.db (SQLite)\n\n"
    "Models: Logistic Regression (churn) and TF-IDF + Logistic Regression (sentiment)."
)


# =====================================================================
# 5) Page 1: Dashboard (all numbers come from SQL)
# =====================================================================
def bar_chart(df, value_col, label_col, color, value_title, height=300):
    return (
        alt.Chart(df)
        .mark_bar(color=color, cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
        .encode(
            x=alt.X(value_col + ":Q", title=value_title),
            y=alt.Y(label_col + ":N", sort="-x", title=None),
            tooltip=[label_col, alt.Tooltip(value_col + ":Q", format=",.2f")],
        )
        .properties(height=height)
    )


def page_dashboard():
    # ---- SQL queries ----
    kpi = run_sql(SALES_CTE + "SELECT SUM(quantity*price*(1-discount)) AS revenue, COUNT(*) AS orders FROM sales")
    customers_total = run_sql("SELECT COUNT(*) AS n FROM customers")["n"][0]
    return_rate = run_sql(
        "SELECT AVG(returned)*100 AS rate FROM orders WHERE date(order_date) IS NOT NULL AND quantity > 0"
    )["rate"][0]

    monthly = run_sql(
        SALES_CTE
        + """SELECT strftime('%Y-%m', order_date) AS month,
                    SUM(quantity*price*(1-discount)) / 1000000.0 AS revenue_million
             FROM sales GROUP BY 1 ORDER BY 1"""
    )
    category = run_sql(
        SALES_CTE
        + """SELECT lower(trim(p.category)) AS category,
                    SUM(s.quantity*s.price*(1-s.discount)) / 1000000.0 AS revenue_million,
                    COUNT(*) AS orders, SUM(s.quantity) AS quantity
             FROM sales s JOIN products p ON s.product_id = p.product_id
             GROUP BY 1 ORDER BY 2 DESC"""
    )
    city = run_sql(
        SALES_CTE
        + """SELECT upper(substr(trim(c.city),1,1)) || lower(substr(trim(c.city),2)) AS city,
                    SUM(s.quantity*s.price*(1-s.discount)) / 1000000.0 AS revenue_million
             FROM sales s JOIN customers c ON s.customer_id = c.customer_id
             GROUP BY 1 ORDER BY 2 DESC"""
    )
    top_products = run_sql(
        SALES_CTE
        + """SELECT p.product_name, lower(trim(p.category)) AS category,
                    SUM(s.quantity*s.price*(1-s.discount)) AS revenue
             FROM sales s JOIN products p ON s.product_id = p.product_id
             GROUP BY p.product_id ORDER BY revenue DESC LIMIT 5"""
    )
    top_customers = run_sql(
        SALES_CTE
        + """SELECT c.customer_name AS Customer,
                    upper(substr(trim(c.city),1,1)) || lower(substr(trim(c.city),2)) AS City,
                    COUNT(*) AS Orders,
                    ROUND(SUM(s.quantity*s.price*(1-s.discount)), 0) AS Spending
             FROM sales s JOIN customers c ON s.customer_id = c.customer_id
             GROUP BY c.customer_id ORDER BY Spending DESC LIMIT 10"""
    )
    returns = run_sql(
        """SELECT lower(trim(p.category)) AS category, AVG(o.returned)*100 AS return_rate
           FROM orders o JOIN products p ON o.product_id = p.product_id
           WHERE date(o.order_date) IS NOT NULL AND o.quantity > 0
           GROUP BY 1 ORDER BY 2 DESC"""
    )

    # Make names look nice (karachi -> Karachi). Leave the product name as it is.
    category["category"] = category["category"].str.title()
    returns["category"] = returns["category"].str.title()
    top_products["category"] = top_products["category"].str.title()

    revenue = kpi["revenue"][0]
    orders_total = int(kpi["orders"][0])

    # ---- KPI cards ----
    cards = [
        kpi_card("💰", "Net Revenue", money(revenue)),
        kpi_card("🛒", "Total Orders", format(orders_total, ",")),
        kpi_card("👥", "Customers", format(int(customers_total), ",")),
        kpi_card("🧾", "Avg Order Value", money(revenue / orders_total)),
        kpi_card("↩️", "Return Rate", format(return_rate, ".1f") + "%"),
    ]
    st.markdown('<div class="grid5">' + "".join(cards) + "</div>", unsafe_allow_html=True)

    st.caption("Net revenue = quantity x price x (1 - discount), counting only clean orders that were not returned.")

    # ---- Monthly revenue ----
    st.markdown('<div class="section-title">📈 Monthly Net Revenue</div>', unsafe_allow_html=True)
    monthly["month"] = pd.to_datetime(monthly["month"] + "-01")
    area = (
        alt.Chart(monthly)
        .mark_area(color=ORANGE, opacity=0.25, line={"color": ORANGE, "strokeWidth": 2.5})
        .encode(
            x=alt.X("month:T", title=None),
            y=alt.Y("revenue_million:Q", title="Revenue (million Rs)"),
            tooltip=[alt.Tooltip("month:T", format="%b %Y"), alt.Tooltip("revenue_million:Q", format=",.2f")],
        )
        .properties(height=320)
    )
    st.altair_chart(area, width="stretch")

    # ---- Category and City ----
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section-title">🗂️ Revenue by Category</div>', unsafe_allow_html=True)
        st.altair_chart(bar_chart(category, "revenue_million", "category", ORANGE, "Revenue (million Rs)"),
                        width="stretch")
    with right:
        st.markdown('<div class="section-title">📍 Revenue by City</div>', unsafe_allow_html=True)
        st.altair_chart(bar_chart(city, "revenue_million", "city", NAVY, "Revenue (million Rs)", height=380),
                        width="stretch")

    # ---- Top 5 products (cards) ----
    st.markdown('<div class="section-title">🏆 Top 5 Products</div>', unsafe_allow_html=True)
    product_cards = ""
    for i, row in top_products.iterrows():
        product_cards += (
            '<div class="pcard"><span class="rank">' + str(i + 1) + '</span>'
            '<div class="name">' + row["product_name"] + '</div>'
            '<span class="cat">' + row["category"] + '</span>'
            '<div class="rev">' + money(row["revenue"]) + "</div></div>"
        )
    st.markdown('<div class="grid5">' + product_cards + "</div>", unsafe_allow_html=True)

    # ---- Return rate and Top customers ----
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section-title">↩️ Return Rate by Category (%)</div>', unsafe_allow_html=True)
        st.altair_chart(bar_chart(returns, "return_rate", "category", RED, "Return rate (%)"),
                        width="stretch")
    with right:
        st.markdown('<div class="section-title">👑 Top 10 Customers</div>', unsafe_allow_html=True)
        top_customers.index = top_customers.index + 1
        st.dataframe(top_customers, width="stretch", height=300)

    with st.expander("📋 Category table (revenue, orders, quantity)"):
        table = category.rename(columns={"category": "Category", "revenue_million": "Revenue (M Rs)",
                                         "orders": "Orders", "quantity": "Quantity sold"})
        st.dataframe(table.round(2), width="stretch", hide_index=True)


# =====================================================================
# 6) Page 2: Churn Prediction
# =====================================================================
def page_churn():
    churn_model, _ = load_models()

    st.markdown('<div class="section-title">🔮 Will this customer leave?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="note"><b>Churn</b> means the customer has not bought anything in the last 3 months. '
        "Enter the customer's past purchase details and the model will tell you how likely the customer is to leave.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        total_orders = st.number_input("Total orders (so far)", min_value=1, max_value=500, value=5, step=1)
        total_spending = st.number_input("Total spending (Rs)", min_value=0, max_value=5_000_000,
                                         value=60000, step=1000)
        days_since = st.slider("Days since the last order", 0, 1500, 60)
        return_rate = st.slider("Return rate (%)", 0, 100, 5)
    with col2:
        avg_delivery = st.slider("Average delivery days", 1.0, 10.0, 3.5, step=0.5)
        age = st.slider("Age", 18, 65, 30)
        membership = st.selectbox("Membership type", ["Standard", "Silver", "Gold", "Premium"])
        tenure = st.number_input("Account age (days since signup)", min_value=0, max_value=2000, value=365, step=30)
        st.write("")
        st.caption("Average order value is calculated automatically: total spending / total orders.")

    avg_order_value = total_spending / total_orders

    if st.button("🔮 Predict Churn", type="primary"):
        customer = pd.DataFrame([{
            "total_orders": total_orders,
            "total_spending": total_spending,
            "avg_order_value": avg_order_value,
            "days_since_last_order": days_since,
            "return_rate": return_rate / 100,
            "avg_delivery_days": avg_delivery,
            "age": age,
            "membership_type": membership,
            "tenure_days": tenure,
        }])
        probability = churn_model.predict_proba(customer)[0][1]
        will_churn = churn_model.predict(customer)[0] == 1

        if will_churn:
            st.markdown(
                '<div class="verdict" style="background:' + RED + ';"><h2>⚠️ High churn risk</h2>'
                "<p>This customer is likely to leave.</p></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="verdict" style="background:' + GREEN + ';"><h2>✅ Likely to stay</h2>'
                "<p>This customer will probably buy again.</p></div>",
                unsafe_allow_html=True,
            )

        m1, m2 = st.columns(2)
        m1.metric("Churn probability", format(probability * 100, ".1f") + "%")
        m2.metric("Stay probability", format((1 - probability) * 100, ".1f") + "%")
        st.progress(float(probability))

        st.markdown("**Suggested action:**")
        if will_churn:
            if days_since > 90:
                st.write("- No order for a long time: send a **win-back offer** or a discount coupon.")
            if tenure > 365 and total_orders <= 5:
                st.write("- **Old account with few orders:** this customer is losing interest, so a personal offer can help.")
            if total_orders <= 3:
                st.write("- New or low-activity customer: give **loyalty points** or free delivery.")
            st.write("- Re-engage the customer with an email or SMS.")
        else:
            st.write("- Keep this customer happy with a **loyalty reward**.")
            st.write("- Send new product recommendations.")

    st.caption("Note: the model looks only at orders, spending and days, so this is an estimate, not a certain answer.")


# =====================================================================
# 7) Page 3: Sentiment Analysis
# =====================================================================
EXAMPLES = {
    "😡 Negative": "Very disappointed, item stopped working quickly. Would not buy again.",
    "😐 Neutral": "Product is okay, quality matches the price. Not bad, not great.",
    "😍 Positive": "Excellent quality, highly recommended. Very happy with the purchase!",
}


def set_example(text):
    st.session_state["review_text"] = text


def page_sentiment():
    _, sentiment_model = load_models()

    st.markdown('<div class="section-title">💬 Review Sentiment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="note">Write a customer review and the model will tell you whether it is <b>Negative</b>, '
        "<b>Neutral</b> or <b>Positive</b>. (It works best on English reviews.)</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    st.write("Try an example:")
    cols = st.columns(3)
    for col, (label, text) in zip(cols, EXAMPLES.items()):
        col.button(label, on_click=set_example, args=(text,), width="stretch")

    review = st.text_area("Review text", key="review_text", height=130,
                          placeholder="Write a review here, for example: Great quality, fast delivery...")

    if st.button("💬 Analyze Sentiment", type="primary"):
        cleaned = clean_text(review)
        if cleaned == "":
            st.warning("Please write a review first (at least a few English words).")
            return

        label = sentiment_model.predict([cleaned])[0]
        probs = sentiment_model.predict_proba([cleaned])[0]
        classes = list(sentiment_model.classes_)

        style = {
            "Positive": (GREEN, "😍", "The customer is happy."),
            "Neutral": (AMBER, "😐", "The opinion is mixed."),
            "Negative": (RED, "😡", "The customer is unhappy and should get a reply."),
        }[label]
        st.markdown(
            '<div class="verdict" style="background:' + style[0] + ';"><h2>' + style[1] + " " + label
            + "</h2><p>" + style[2] + "</p></div>",
            unsafe_allow_html=True,
        )

        st.markdown("**Confidence:**")
        for name, p in sorted(zip(classes, probs), key=lambda x: -x[1]):
            st.write(name + ": " + format(p * 100, ".1f") + "%")
            st.progress(float(p))

    st.caption("Limitation: the model was trained on reviews that look template-generated, "
               "so it may do worse on real-world reviews (sarcasm, spelling mistakes, Roman Urdu).")


# =====================================================================
# 8) Choose the page and run it
# =====================================================================
if page == "📊 Dashboard":
    page_dashboard()
elif page == "🔮 Churn Prediction":
    page_churn()
else:
    page_sentiment()

st.markdown('<div class="footer">AI Powered E-Commerce Customer Intelligence System | Data Science Final Hackathon | Built with Streamlit</div>',
            unsafe_allow_html=True)
