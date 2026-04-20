import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# ---------------- DB ----------------
engine = create_engine("sqlite:///food_waste_management.db")

food = pd.read_sql("SELECT * FROM food_listings", engine)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide")

st.title("🍽️ Food Waste Management System")

# ---------------- SIDEBAR FILTERS (ONLY ONCE) ----------------
st.sidebar.header("🔍 Filters")

city_list = ["All"] + sorted(food['City'].dropna().unique().tolist())
food_type_list = ["All"] + sorted(food['Food_Type'].dropna().unique().tolist())
meal_type_list = ["All"] + sorted(food['Meal_Type'].dropna().unique().tolist())

city = st.sidebar.selectbox("City", city_list)
food_type = st.sidebar.selectbox("Food Type", food_type_list)
meal_type = st.sidebar.selectbox("Meal Type", meal_type_list)

# ---------------- FILTER DATA ----------------
filtered_data = food.copy()

if city != "All":
    filtered_data = filtered_data[filtered_data["City"] == city]

if food_type != "All":
    filtered_data = filtered_data[filtered_data["Food_Type"] == food_type]

if meal_type != "All":
    filtered_data = filtered_data[filtered_data["Meal_Type"] == meal_type]

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Add Data", "✏️ Update", "❌ Delete"])

# ======================================================
# TAB 1 - DASHBOARD
# ======================================================
with tab1:
    st.header("📊 Dashboard")

    k1, k2, k3, k4 = st.columns(4)

    total_food = filtered_data["Quantity"].sum()
    total_providers = filtered_data["Provider_ID"].nunique()
    total_claims = pd.read_sql("SELECT * FROM claims", engine).shape[0]

    with k1:
        st.metric("🍽️ Total Food", int(total_food))

    with k2:
        st.metric("🏪 Providers", total_providers)

    with k3:
        st.metric("📦 Total Claims", total_claims)

    with k4:
        st.metric("📊 Records", len(filtered_data))

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        q1 = filtered_data.groupby("City").size().reset_index(name="providers")
        if not q1.empty:
            fig1 = px.bar(q1, x="City", y="providers", title="Providers by City")
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        q3 = filtered_data.groupby("Food_Type")["Quantity"].sum().reset_index()
        if not q3.empty:
            fig2 = px.bar(q3, x="Food_Type", y="Quantity", title="Food by Type")
            st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        q6 = filtered_data.groupby("City").size().reset_index(name="listings")
        if not q6.empty:
            fig3 = px.bar(q6, x="City", y="listings", title="Listings by City")
            st.plotly_chart(fig3, use_container_width=True)

    with col4:
        q12 = filtered_data.groupby("Meal_Type").size().reset_index(name="total")
        if not q12.empty:
            fig4 = px.pie(q12, names="Meal_Type", values="total", title="Meal Type Demand")
            st.plotly_chart(fig4, use_container_width=True)

    st.subheader("📋 Filtered Data")
    st.dataframe(filtered_data, use_container_width=True)

# ======================================================
# TAB 2 - ADD
# ======================================================
with tab2:
    st.header("➕ Add Provider")

    name = st.text_input("Name")
    type_ = st.text_input("Type")
    address = st.text_input("Address")
    city_input = st.text_input("City")
    contact = st.text_input("Contact")

    if st.button("Add Provider"):
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO providers (Name, Type, Address, City, Contact)
                VALUES (:name, :type, :address, :city, :contact)
            """), {
                "name": name,
                "type": type_,
                "address": address,
                "city": city_input,
                "contact": contact
            })
            conn.commit()

        st.success("✅ Provider Added!")

# ======================================================
# TAB 3 - UPDATE
# ======================================================
with tab3:
    st.header("✏️ Update Data")

    option = st.selectbox("Select Update Type",
                          ["Claim Status", "Food Quantity", "Provider Name"])

    if option == "Claim Status":
        claim_id = st.number_input("Claim ID", min_value=1)
        status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])

        if st.button("Update Status"):
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE claims
                    SET Status = :status
                    WHERE Claim_ID = :id
                """), {"status": status, "id": claim_id})
                conn.commit()
            st.success("✅ Updated!")

    elif option == "Food Quantity":
        food_id = st.number_input("Food ID", min_value=1)
        qty = st.number_input("Quantity", min_value=0)

        if st.button("Update Quantity"):
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE food_listings
                    SET Quantity = :qty
                    WHERE Food_ID = :id
                """), {"qty": qty, "id": food_id})
                conn.commit()
            st.success("✅ Updated!")

    elif option == "Provider Name":
        provider_id = st.number_input("Provider ID", min_value=1)
        new_name = st.text_input("New Name")

        if st.button("Update Provider"):
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE providers
                    SET Name = :name
                    WHERE Provider_ID = :id
                """), {"name": new_name, "id": provider_id})
                conn.commit()
            st.success("✅ Updated!")

# ======================================================
# TAB 4 - DELETE
# ======================================================
with tab4:
    st.header("❌ Delete Claim")

    delete_id = st.number_input("Claim ID", min_value=1)

    if st.button("Delete"):
        with engine.connect() as conn:
            conn.execute(text("""
                DELETE FROM claims
                WHERE Claim_ID = :id
            """), {"id": delete_id})
            conn.commit()

        st.success("✅ Deleted!")
