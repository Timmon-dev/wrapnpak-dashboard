import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Wrap n Pak Smart Dashboard")

file = st.file_uploader("Upload Excel File", type=["xlsx"])
date_input = st.text_input("Enter Date (YYYY-MM-DD)")

sku_map = {
    10264594: 'Ch.',
    10258817: 'TTR',
    10273819: 'BR',
    10258800: 'Baking'
}

if file and date_input:
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    df['Order Date'] = pd.to_datetime(df['Order Date']).dt.date
    selected_date = pd.to_datetime(date_input).date()

    df_day = df[df['Order Date'] == selected_date]

    # ===== Overall Metrics =====
    total_orders = df_day['Order Id'].nunique()
    total_quantity = df_day['Quantity'].sum()

    col1, col2 = st.columns(2)
    col1.metric("Total Orders", total_orders)
    col2.metric("Total Quantity", total_quantity)

    # ===== SKU Summary =====
    df_sku = df[df['Item Id'].isin(sku_map.keys())]

    df_sku_day = df_sku[df_sku['Order Date'] == selected_date]

    sku_summary = df_sku_day.groupby('Item Id').agg(
        Orders=('Order Id', pd.Series.nunique),
        Quantity=('Quantity', 'sum')
    ).reset_index()

    sku_summary['SKU'] = sku_summary['Item Id'].map(sku_map)

    st.subheader("🔍 SKU Summary")
    st.dataframe(sku_summary, use_container_width=True)

    # ===== City Full List =====
    all_cities = df['Customer City'].dropna().unique()

    city_day = df_day.groupby('Customer City').agg(
        Orders=('Order Id', pd.Series.nunique),
        Quantity=('Quantity', 'sum')
    ).reset_index()

    city_full = pd.DataFrame({'Customer City': all_cities})
    city_full = city_full.merge(city_day, on='Customer City', how='left').fillna(0)

    # ===== Averages =====
    city_days = df.groupby('Customer City')['Order Date'].nunique().reset_index()
    city_days.columns = ['Customer City', 'Days']

    city_total = df.groupby('Customer City').agg(
        Total_Orders=('Order Id', pd.Series.nunique),
        Total_Quantity=('Quantity', 'sum')
    ).reset_index()

    city_avg = city_total.merge(city_days, on='Customer City')

    city_avg['Avg Orders/Day'] = city_avg['Total_Orders'] / city_avg['Days']
    city_avg['Avg Qty/Day'] = city_avg['Total_Quantity'] / city_avg['Days']

    city_full = city_full.merge(
        city_avg[['Customer City', 'Avg Orders/Day', 'Avg Qty/Day']],
        on='Customer City',
        how='left'
    )

    st.subheader("🌆 Full City Table")
    st.dataframe(city_full.sort_values(by="Orders", ascending=False), use_container_width=True)

    # ===== Top Cities =====
    st.subheader("🔥 Top Cities (by Orders)")
    st.dataframe(city_full.sort_values(by="Orders", ascending=False).head(10))

    # ===== Download =====
    csv = city_full.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇ Download City Report",
        csv,
        "city_report.csv",
        "text/csv"
    )