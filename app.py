import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re

st.set_page_config(page_title="Conversational BI Dashboard", layout="wide", page_icon="📊")

st.title("🎯 Conversational AI for Instant BI Dashboards")
st.markdown("BMW Vehicle Inventory - Natural Language → Dashboard 🚀")

# Sidebar
with st.sidebar:
    st.header("🔑 Setup")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        st.success("✅ API Connected")
    else:
        st.warning("Please enter your Gemini API key")

# ================== FILE UPLOAD + DOUBLE ENCODING FIX ==================
uploaded_file = st.file_uploader("📂 Upload BMW Vehicle Inventory.csv", type=["csv"])

if uploaded_file:
    uploaded_file.seek(0)
    
    # DOUBLE ENCODING FIX (yeh error hamesha ke liye khatam karega)
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8', low_memory=False, on_bad_lines='skip')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='ISO-8859-1', low_memory=False, on_bad_lines='skip')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='cp1252', low_memory=False, on_bad_lines='skip')

    # ================== STRONG CLEANING (Data Dictionary ke hisaab se) ==================
    # Junk columns hatao
    real_cols = ['model', 'year', 'price', 'transmission', 'mileage', 'fuelType', 'tax', 'mpg', 'engineSize']
    df.columns = [re.sub(r'__.*__', '', str(col)).strip() for col in df.columns]
    
    # Column names clean
    df.columns = df.columns.str.lower().str.strip()
    rename_map = {'fueltype': 'fuelType', 'enginesize': 'engineSize'}
    df = df.rename(columns=rename_map)

    # Numeric columns fix
    numeric_cols = ['year', 'price', 'mileage', 'tax', 'mpg', 'engineSize']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Final cleanup
    df = df.dropna(axis=1, how='all')

    st.session_state.df = df
    st.success(f"✅ CSV CLEANED & LOADED! {len(df):,} rows | {len(df.columns)} columns")
    st.dataframe(df.head(5), use_container_width=True)

# Query
query = st.text_area("💬 Ask your business question", 
                     placeholder="Show distribution of fuel types in pie chart", 
                     height=120)

# Generate Dashboard
if st.button("🚀 Generate Dashboard", type="primary", use_container_width=True):
    if not api_key or "df" not in st.session_state or not query.strip():
        st.error("❌ API key, file aur question daalo!")
        st.stop()

    with st.spinner("🤖 Gemini analyzing BMW data..."):
        df = st.session_state.df.copy()
        
        metadata = f"""
        Total rows: {len(df)}
        Columns: {list(df.columns)}
        Sample:\n{df.head(3).to_string()}
        """

        system_prompt = f"""
You are an expert automotive data analyst.
Dataset (already cleaned):
{metadata}

User question: {query}

Generate ONLY valid Python code (no explanation).
Use df variable + plotly.express + streamlit.
Create 2-3 beautiful interactive charts + 3-4 business insights.
"""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(system_prompt)
        code = response.text.strip()

        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].strip()

        try:
            exec_globals = {"df": df, "st": st, "px": px, "pd": pd}
            exec(code, exec_globals)
            st.success("✅ Dashboard Generated Successfully!")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.code(response.text, language="python")

st.caption("🏆 Hackathon Prototype | BMW Dataset | Streamlit + Gemini")