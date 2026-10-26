import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("Expense Tracker with Visuals")

CATEGORIES = ["Food", "Transport", "Rent", "Utilities", "Shopping", "Entertainment", "Health", "Other"]

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["date", "category", "amount", "note"])

# --- Input ---
st.subheader("Add Expense")
with st.form("add_expense", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    date = c1.date_input("Date")
    category = c2.selectbox("Category", CATEGORIES)
    amount = c3.number_input("Amount", min_value=0.0, step=10.0)
    note = c4.text_input("Note")
    submitted = st.form_submit_button("Add")
    if submitted and amount > 0:
        new_row = pd.DataFrame([{"date": date, "category": category, "amount": amount, "note": note}])
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)

st.subheader("Or Upload CSV")
st.caption("Columns required: date, category, amount, note (note optional)")
uploaded = st.file_uploader("Upload CSV", type="csv")
if uploaded is not None:
    df_upload = pd.read_csv(uploaded)
    df_upload["date"] = pd.to_datetime(df_upload["date"]).dt.date
    if "note" not in df_upload.columns:
        df_upload["note"] = ""
    st.session_state.expenses = pd.concat([st.session_state.expenses, df_upload], ignore_index=True)
    st.success(f"Loaded {len(df_upload)} rows")

df = st.session_state.expenses.copy()

if df.empty:
    st.info("No expenses yet. Add some above or upload a CSV.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["amount"] = df["amount"].astype(float)

# --- Table ---
st.subheader("All Expenses")
st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

# --- Budget alert ---
st.subheader("Budget")
budget = st.number_input("Monthly budget", min_value=0.0, value=10000.0, step=500.0)
current_month = pd.Timestamp.now().to_period("M")
month_total = df[df["date"].dt.to_period("M") == current_month]["amount"].sum()
pct = (month_total / budget * 100) if budget > 0 else 0
st.metric("Spent this month", f"₹{month_total:,.2f}", f"{pct:.1f}% of budget")
if pct >= 100:
    st.error("Over budget for this month.")
elif pct >= 80:
    st.warning("Approaching budget limit.")

# --- Visuals ---
st.subheader("Spending by Category")
by_category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
c1, c2 = st.columns(2)

with c1:
    fig1, ax1 = plt.subplots()
    ax1.pie(by_category, labels=by_category.index, autopct="%1.1f%%")
    ax1.set_title("Category Breakdown")
    st.pyplot(fig1)

with c2:
    fig2, ax2 = plt.subplots()
    by_category.plot(kind="bar", ax=ax2)
    ax2.set_ylabel("Amount")
    ax2.set_title("Spend by Category")
    st.pyplot(fig2)

st.subheader("Spending Over Time")
by_date = df.groupby(df["date"].dt.date)["amount"].sum()
fig3, ax3 = plt.subplots()
by_date.plot(kind="line", marker="o", ax=ax3)
ax3.set_ylabel("Amount")
ax3.set_title("Daily Spend")
st.pyplot(fig3)

# --- Export ---
st.subheader("Export")


def to_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name="Expenses", index=False)
        by_category.reset_index().to_excel(writer, sheet_name="By Category", index=False)
    return output.getvalue()


st.download_button(
    "Download Excel Report",
    data=to_excel(df),
    file_name="expense_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)