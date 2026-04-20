import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
import plotly.express as px

engine = create_engine("sqlite:///food_waste_management.db")

food = pd.read_sql("SELECT * FROM food_listings", engine)

q1 = pd.read_sql("""
SELECT City, COUNT(*) AS total_providers
FROM providers
GROUP BY City
""", engine)

q2 = pd.read_sql("""
SELECT City, COUNT(*) AS total_receivers
FROM receivers
GROUP BY City
""", engine)

q3 = pd.read_sql("""
SELECT p.Type, SUM(f.Quantity) AS total_food
FROM food_listings f
JOIN providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.Type
""", engine)

selected_city = st.sidebar.selectbox(
    "Select City for Contact Info",
    pd.read_sql("SELECT DISTINCT City FROM providers", engine)['City'],
    key="contact_city"
)

q4 = pd.read_sql(f"""
SELECT Name, Contact, Address
FROM providers
WHERE City = '{selected_city}'
""", engine)

q5 = pd.read_sql("""
SELECT SUM(Quantity) AS total_food
FROM food_listings
""", engine)

q6 = pd.read_sql("""
SELECT City, COUNT(*) AS listings
FROM food_listings
GROUP BY City
""", engine)

q7 = pd.read_sql("""
SELECT Food_Type, COUNT(*) AS total
FROM food_listings
GROUP BY Food_Type
""", engine)

q8 = pd.read_sql("""
SELECT Food_ID, COUNT(*) AS claims
FROM claims
GROUP BY Food_ID
""", engine)

q9 = pd.read_sql("""
SELECT p.Name, COUNT(*) AS successful_claims
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
JOIN providers p ON f.Provider_ID = p.Provider_ID
WHERE c.Status = 'Completed'
GROUP BY p.Name
""", engine)

q10 = pd.read_sql("""
SELECT Status,
COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims) AS percentage
FROM claims
GROUP BY Status
""", engine)

q11 = pd.read_sql("""
SELECT Receiver_ID, AVG(f.Quantity) AS avg_quantity
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
GROUP BY Receiver_ID
""", engine)

q12 = pd.read_sql("""
SELECT f.Meal_Type, COUNT(*) AS total
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
GROUP BY f.Meal_Type
""", engine)

q13 = pd.read_sql("""
SELECT p.Name, SUM(f.Quantity) AS total
FROM food_listings f
JOIN providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.Name
""", engine)

q14 = pd.read_sql("""
SELECT *
FROM food_listings
WHERE Expiry_Date < datetime('now')
""", engine)

q15 = pd.read_sql("""
SELECT c.Claim_ID, f.Food_Name, f.Expiry_Date, c.Timestamp
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
WHERE c.Timestamp > f.Expiry_Date
""", engine)

# ---------------- SINGLE FILTER SECTION (FIXED) ----------------
st.sidebar.header("🔍 Filters")

city_list = ["All"] + sorted(food['City'].dropna().unique().tolist())
food_type_list = ["All"] + sorted(food['Food_Type'].dropna().unique().tolist())
meal_type_list = ["All"] + sorted(food['Meal_Type'].dropna().unique().tolist())

city = st.sidebar.selectbox("City", city_list)
food_type = st.sidebar.selectbox("Food Type", food_type_list)
meal_type = st.sidebar.selectbox("Meal Type", meal_type_list)

filtered_data = food.copy()

if city != "All":
    filtered_data = filtered_data[filtered_data['City'] == city]

if food_type != "All":
    filtered_data = filtered_data[filtered_data['Food_Type'] == food_type]

if meal_type != "All":
    filtered_data = filtered_data[filtered_data['Meal_Type'] == meal_type]

# ---------------- APP TITLE ----------------
st.title("🍽️ Food Waste Management System")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "➕ Add Data",
    "✏️ Update",
    "❌ Delete"
])

# ================= DASHBOARD =================
with tab1:
    st.title("📊 Food Waste Management Dashboard")

    k1, k2, k3, k4 = st.columns(4)

    total_food = q5['total_food'][0]
    total_providers = len(pd.read_sql("SELECT * FROM providers", engine))
    total_claims = len(pd.read_sql("SELECT * FROM claims", engine))
    completed_pct = q10[q10['Status']=="Completed"]['percentage'].values

    with k1:
        st.metric("🍽️ Total Food", int(total_food))

    with k2:
        st.metric("🏪 Providers", total_providers)

    with k3:
        st.metric("📦 Total Claims", total_claims)

    with k4:
        st.metric("✅ Completed %",
                  f"{round(completed_pct[0],2)}%" if len(completed_pct)>0 else "0%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        q1_top = q1.sort_values(by="total_providers", ascending=True).tail(10)
        fig = px.bar(q1_top, x="City", y="total_providers",
                     title="Top 10 Cities by Providers")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(q3, x="Type", y="total_food", title="Food by Provider Type")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        q6_top = q6.sort_values(by="listings", ascending=False).head(10)
        fig3 = px.bar(q6_top, x="City", y="listings", title="Top Cities by Listings")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.pie(q12, names="Meal_Type", values="total", title="Meal Type Demand")
        st.plotly_chart(fig4, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        st.subheader("📋 Expired Food")
        st.dataframe(q14, use_container_width=True)

    with col6:
        st.subheader("⚠️ Claims After Expiry")
        st.dataframe(q15, use_container_width=True)

# ================= ADD =================
with tab2:
    st.header("➕ Add New Provider")

    name = st.text_input("Provider Name")
    type_ = st.text_input("Type (Restaurant/Grocery)")
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
        st.success("✅ Provider Added Successfully!")

# ================= UPDATE =================
with tab3:
    st.header("✏️ Update Data")

    option = st.selectbox(
        "What do you want to update?",
        ["Claim Status", "Food Quantity", "Provider Details"]
    )

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
            st.success("✅ Status Updated!")

    elif option == "Food Quantity":
        food_id = st.number_input("Food ID", min_value=1)
        quantity = st.number_input("New Quantity", min_value=0)

        if st.button("Update Quantity"):
            with engine.connect() as conn:
                conn.execute(text("""
                UPDATE food_listings
                SET Quantity = :qty
                WHERE Food_ID = :id
                """), {"qty": quantity, "id": food_id})
                conn.commit()
            st.success("✅ Quantity Updated!")

    elif option == "Provider Details":
        provider_id = st.number_input("Provider ID", min_value=1)
        name = st.text_input("New Name")

        if st.button("Update Provider"):
            with engine.connect() as conn:
                conn.execute(text("""
                UPDATE providers
                SET Name = :name
                WHERE Provider_ID = :id
                """), {"name": name, "id": provider_id})
                conn.commit()
            st.success("✅ Provider Updated!")

# ================= DELETE =================
with tab4:
    st.header("❌ Delete Claim")

    delete_id = st.number_input("Enter Claim ID to Delete", min_value=1)

    if st.button("Delete Claim"):
        with engine.connect() as conn:
            conn.execute(text("""
            DELETE FROM claims
            WHERE Claim_ID = :id
            """), {"id": delete_id})
            conn.commit()
        st.success("✅ Claim Deleted!")
