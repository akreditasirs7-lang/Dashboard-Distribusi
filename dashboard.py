import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Droping vs Non Droping", layout="wide")
st.title("📊 Dashboard Droping vs Non Droping (Live dari Google Sheets)")

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"

@st.cache_data(ttl=120)
def load_data():
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    return df

if st.button("🔄 Refresh Data Sekarang"):
    st.cache_data.clear()

df = load_data()

st.sidebar.header("🔍 Filter Data")
jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Pilih Jenis Permintaan:", options=jenis_list, default=jenis_list)

df_filtered = df[df['Jenis Permintaan'].isin(jenis_filter)]

st.subheader("📋 Data Kolom A:J")
st.dataframe(df_filtered, use_container_width=True)

st.markdown("### 📈 Statistik & Grafik")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Jumlah per Jenis Permintaan")
    st.bar_chart(df_filtered['Jenis Permintaan'].value_counts())

with col2:
    if 'Golongan Darah' in df_filtered.columns:
        st.markdown("#### Distribusi Golongan Darah")
        st.bar_chart(df_filtered['Golongan Darah'].value_counts())

st.markdown("---")
st.caption("📡 Data otomatis diperbarui dari Google Sheets setiap 2 menit atau tekan tombol Refresh.")
