import streamlit as st
import pandas as pd
from datetime import date

# 1. Hämta dagens datum
idag = date.today().strftime("%Y-%m-%d")

# 2. Skapa en rubrik med datumet
st.title(f"Dashboard för {idag}")

# 3. Skapa lite testdata
data = {
    'Namn': ['Alice', 'Bob', 'Charlie'],
    'Poäng': [10, 25, 30],
    'Status': ['Klar', 'Pågår', 'Klar']
}

df = pd.DataFrame(data)

# 4. Visa tabellen
st.subheader("Dagens deltagare")
st.write("Här är datan som laddades in i morse:")
st.dataframe(df)
