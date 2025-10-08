
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date as dt_date
import os

# Use Tahoma font to ensure Thai text is displayed correctly in Matplotlib
# Fallback to a different font if Tahoma is not available
try:
    plt.rcParams['font.family'] = 'Tahoma'
    plt.rcParams['axes.unicode_minus'] = False # Fix for minus sign issue with Thai font
except:
    pass

# --- Configuration for Streamlit page ---
st.set_page_config(
    page_title="ระบบบันทึกรายรับรายจ่าย",
    page_icon="📊",
    layout="wide"
)

# --- Session State Management ---
if 'df' not in st.session_state:
    try:
        # Check if file exists and is not empty
        if os.path.exists("transactions.csv") and os.path.getsize("transactions.csv") > 0:
            # Read the CSV file with utf-8-sig encoding to handle BOM
            df = pd.read_csv("transactions.csv", encoding='utf-8-sig')
            df['วันที่'] = pd.to_datetime(df['วันที่'], errors='coerce')
            st.session_state.df = df
        else:
            # Create an empty DataFrame if the file is empty or doesn't exist
            st.session_state.df = pd.DataFrame(columns=["วันที่", "ประเภท", "หมวดหมู่", "รายละเอียด", "จำนวนเงิน"])
    except pd.errors.EmptyDataError:
        # Handle the case where the file exists but has no content
        st.session_state.df = pd.DataFrame(columns=["วันที่", "ประเภท", "หมวดหมู่", "รายละเอียด", "จำนวนเงิน"])
    except UnicodeDecodeError:
        # Fallback to a different encoding if utf-8-sig fails
        try:
            df = pd.read_csv("transactions.csv", encoding='TIS-620')
            df['วันที่'] = pd.to_datetime(df['วันที่'], errors='coerce')
            st.session_state.df = df
        except Exception:
            st.session_state.df = pd.DataFrame(columns=["วันที่", "ประเภท", "หมวดหมู่", "รายละเอียด", "จำนวนเงิน"])

# Set default transaction type if not in session state
if 'trans_type' not in st.session_state:
    st.session_state.trans_type = 'รายรับ'
if 'category' not in st.session_state:
    st.session_state.category = 'เงินรายวัน'
if 'description' not in st.session_state:
    st.session_state.description = ''
if 'amount' not in st.session_state:
    st.session_state.amount = 0.0
# Add a new state variable to control the success message display
if 'show_success_message' not in st.session_state:
    st.session_state.show_success_message = False

def update_category_options():
    """Update category options based on transaction type and reset the selected category."""
    if st.session_state.trans_type == 'รายรับ':
        st.session_state.category = 'เงินรายวัน'
    else:
        st.session_state.category = 'ค่าอาหาร'

# --- Main Application Title ---
st.title("📊 ระบบบันทึกรายรับรายจ่าย")
st.markdown("---")

# --- Form for data entry ---
st.subheader("บันทึกรายการใหม่")
col1, col2 = st.columns(2)
with col1:
    date = st.date_input("วันที่", value=dt_date.today(), format="DD/MM/YYYY", key="date")
with col2:
    trans_type = st.selectbox(
        "ประเภท",
        ["รายรับ", "รายจ่าย"],
        key="trans_type",
        on_change=update_category_options
    )

# Dynamic category options based on transaction type
if st.session_state.trans_type == "รายรับ":
    category_options = ["เงินรายวัน", "รายได้อื่นๆ"]
else:
    category_options = ["ค่าอาหาร", "ค่าเดินทาง", "ค่าใช้จ่ายอื่นๆ"]

category = st.selectbox(
    "หมวดหมู่",
    options=category_options,
    key="category"
)

description = st.text_input("รายละเอียด", key="description")
amount = st.number_input("จำนวนเงิน", min_value=0.0, step=1.0, format="%.2f", key="amount")

# Enable/disable the submit button based on user input
if description and amount > 0:
    disabled_state = False
else:
    disabled_state = True

with st.form("transaction_form"):
    st.write("กดปุ่มด้านล่างเพื่อบันทึกข้อมูล")
    submitted = st.form_submit_button("บันทึกข้อมูล", disabled=disabled_state)

    if submitted:
        # Create a new DataFrame row with the submitted data
        new_data = pd.DataFrame([[date, st.session_state.trans_type, st.session_state.category, st.session_state.description, st.session_state.amount]],
                                columns=["วันที่", "ประเภท", "หมวดหมู่", "รายละเอียด", "จำนวนเงิน"])

        # Concatenate with the existing DataFrame
        st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
        
        # Save the updated DataFrame to CSV with utf-8-sig encoding
        st.session_state.df.to_csv("transactions.csv", index=False, encoding='utf-8-sig')
        
        # Set the session state to show the success message on the next run
        st.session_state.show_success_message = True
        
        # Rerun the app to show updated data
        st.rerun()

# --- Display success message after rerun has completed ---
if st.session_state.show_success_message:
    st.success("บันทึกข้อมูลเรียบร้อย! ✅")
    st.balloons()
    # Reset the state so the message doesn't reappear on other interactions
    st.session_state.show_success_message = False

# --- Display separate income and expense tables and summary ---
st.markdown("---")
if not st.session_state.df.empty:
    income_df = st.session_state.df[st.session_state.df['ประเภท'] == 'รายรับ'].copy()
    expense_df = st.session_state.df[st.session_state.df['ประเภท'] == 'รายจ่าย'].copy()

    # Convert date format for display
    income_df['วันที่'] = pd.to_datetime(income_df['วันที่']).dt.strftime('%d/%m/%Y')
    expense_df['วันที่'] = pd.to_datetime(expense_df['วันที่']).dt.strftime('%d/%m/%Y')

    col_tables_1, col_tables_2 = st.columns(2)
    with col_tables_1:
        st.subheader("💰 ตารางรายรับ")
        if not income_df.empty:
            st.dataframe(income_df.style.format({'จำนวนเงิน': '{:,.2f} บาท'.format}), hide_index=True)
        else:
            st.info("ไม่มีข้อมูลรายรับในขณะนี้")

    with col_tables_2:
        st.subheader("💸 ตารางรายจ่าย")
        if not expense_df.empty:
            st.dataframe(expense_df.style.format({'จำนวนเงิน': '{:,.2f} บาท'.format}), hide_index=True)
        else:
            st.info("ไม่มีข้อมูลรายจ่ายในขณะนี้")
    
    st.markdown("---")
    # --- Summary calculation and display ---
    st.subheader("📊 สรุปยอดรวม")
    total_income = income_df['จำนวนเงิน'].sum() if not income_df.empty else 0
    total_expense = expense_df['จำนวนเงิน'].sum() if not expense_df.empty else 0
    balance = total_income - total_expense
    
    col_sum1, col_sum2, col_sum3 = st.columns(3)
    with col_sum1:
        st.metric(label="รวมรายรับ", value=f"{total_income:,.2f} บาท", delta_color="off")
    with col_sum2:
        st.metric(label="รวมรายจ่าย", value=f"{total_expense:,.2f} บาท", delta_color="off")
    with col_sum3:
        st.metric(label="คงเหลือ", value=f"{balance:,.2f} บาท", delta=f"{balance:,.2f}", delta_color="normal")


    # --- Display chart ---
    st.markdown("---")
    st.subheader("📈 กราฟรายรับ-รายจ่าย")
    if 'รายรับ' in st.session_state.df['ประเภท'].values or 'รายจ่าย' in st.session_state.df['ประเภท'].values:
        # Group by category and calculate sum of amount
        income_by_category = st.session_state.df[st.session_state.df['ประเภท'] == 'รายรับ'].groupby('หมวดหมู่')['จำนวนเงิน'].sum()
        expense_by_category = st.session_state.df[st.session_state.df['ประเภท'] == 'รายจ่าย'].groupby('หมวดหมู่')['จำนวนเงิน'].sum()
        
        all_categories = pd.concat([income_by_category, expense_by_category]).index.unique()
        
        income_values = [income_by_category.get(cat, 0) for cat in all_categories]
        expense_values = [expense_by_category.get(cat, 0) for cat in all_categories]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bar_width = 0.35
        x = range(len(all_categories))
        
        # Plot bars for income and expenses
        bars_income = ax.bar([i - bar_width/2 for i in x], income_values, bar_width, label='รายรับ', color='green')
        bars_expense = ax.bar([i + bar_width/2 for i in x], expense_values, bar_width, label='รายจ่าย', color='red')
        
        ax.set_ylabel("จำนวนเงิน (บาท)")
        ax.set_xlabel("หมวดหมู่")
        ax.set_xticks(x)
        ax.set_xticklabels(all_categories, rotation=45, ha='right')
        ax.legend()
        
        # Add labels with amount on top of the bars
        for bar in bars_income:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2., height, f'{height:,.0f}',
                        ha='center', va='bottom', fontsize=8)
                        
        for bar in bars_expense:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2., height, f'{height:,.0f}',
                        ha='center', va='bottom', fontsize=8)
                        
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("ไม่มีข้อมูลเพียงพอสำหรับสร้างกราฟ")
