import streamlit as st
import pandas as pd
import time
import altair as alt

# =========================
# 🎨 SETTING TAMPILAN
# =========================
st.set_page_config(page_title="Dashboard Droping vs Non Droping", layout="wide", page_icon="💉")

st.markdown("""
    <style>
        body {
            background-color: #f8f9fa;
        }
        .big-font {
            font-size:24px !important;
            font-weight:600;
            color:#2E86C1;
        }
        .metric-box {
            background-color: #E8F6F3;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            margin-bottom: 10px;
        }
        .stDataFrame {
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# 🩸 DATA GOOGLE SHEETS
# =========================
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"

@st.cache_data(ttl=30)  # refresh otomatis tiap 30 detik
def load_data():
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = [col.strip() for col in df.columns]
    # Gabungkan kolom Bulan dan Tahun jadi datetime (kalau ada)
    if 'Bulan' in df.columns and 'Tahun' in df.columns:
        df['Periode'] = df['Bulan'].astype(str) + " " + df['Tahun'].astype(str)
    return df

df = load_data()

# =========================
# 🎛️ SIDEBAR FILTERS
# =========================
st.sidebar.header("🎛️ Filter Data")

# Filter Jenis Permintaan
jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Pilih Jenis Permintaan:", options=jenis_list, default=jenis_list)

# Filter Jenis Pengimputan (Permintaan / Pemenuhan)
if 'Jenis Pengimputan' in df.columns:
    imput_list = df['Jenis Pengimputan'].dropna().unique().tolist()
    imput_filter = st.sidebar.multiselect("Pilih Jenis Pengimputan:", options=imput_list, default=imput_list)
else:
    imput_filter = []

# Filter RS/Klinik Tujuan
if 'Droping RS/Klinik Tujuan' in df.columns:
    tujuan_list = df['Droping RS/Klinik Tujuan'].dropna().unique().tolist()
    tujuan_filter = st.sidebar.multiselect("Pilih RS/Klinik Tujuan:", options=tujuan_list, default=tujuan_list)
else:
    tujuan_filter = []

# =========================
# 🧩 FILTER LOGIKA
# =========================
df_filtered = df[df['Jenis Permintaan'].isin(jenis_filter)]

if imput_filter:
    df_filtered = df_filtered[df_filtered['Jenis Pengimputan'].isin(imput_filter)]

if tujuan_filter:
    df_filtered = df_filtered[df_filtered['Droping RS/Klinik Tujuan'].isin(tujuan_filter)]

# =========================
# 📋 DATA TABEL
# =========================
st.title("💉 Dashboard Droping vs Non Droping - Data Distribusi 2026")
st.markdown("#### Analisis Real-time dari Google Sheets — Kolom A:J")
st.dataframe(df_filtered, use_container_width=True, height=400)

# =========================
# 🔢 STATISTIK UTAMA
# =========================
st.markdown("### 📈 Statistik Singkat")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric-box'><span class='big-font'>{len(df_filtered):,}</span><br>Jumlah Data</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-box'><span class='big-font'>{df_filtered['Jenis Permintaan'].value_counts().idxmax()}</span><br>Jenis Terbanyak</div>", unsafe_allow_html=True)
with col3:
    total_jumlah = df_filtered['Jumlah'].sum() if 'Jumlah' in df_filtered.columns else 0
    st.markdown(f"<div class='metric-box'><span class='big-font'>{int(total_jumlah):,}</span><br>Total Unit</div>", unsafe_allow_html=True)

# =========================
# 📊 VISUALISASI DATA
# =========================
st.markdown("### 📊 Visualisasi Data")

# Kolom 1 dan 2
col4, col5 = st.columns(2)
with col4:
    st.markdown("#### 🔸 Jumlah per Jenis Distribusi")
    st.bar_chart(df_filtered['Jenis Distribusi'].value_counts())

with col5:
    if 'Golongan Darah' in df_filtered.columns:
        st.markdown("#### 🩸 Distribusi Golongan Darah")
        st.bar_chart(df_filtered['Golongan Darah'].value_counts())

# Chart RS/Klinik
st.markdown("#### 🏥 Top 15 RS/Klinik Tujuan")
if 'Droping RS/Klinik Tujuan' in df_filtered.columns:
    tujuan_counts = df_filtered['Droping RS/Klinik Tujuan'].value_counts().head(15)
    st.bar_chart(tujuan_counts)

# =========================
# 📅 TREND BULANAN
# =========================
if 'Periode' in df_filtered.columns and 'Jenis Permintaan' in df_filtered.columns:
    st.markdown("### 📆 Tren Bulanan Droping vs Non Droping")
    df_trend = (
        df_filtered.groupby(['Periode', 'Jenis Permintaan'])
        .size()
        .reset_index(name='Jumlah')
        .sort_values('Periode')
    )
    chart = (
        alt.Chart(df_trend)
        .mark_line(point=True)
        .encode(
            x='Periode:N',
            y='Jumlah:Q',
            color='Jenis Permintaan:N',
            tooltip=['Periode', 'Jenis Permintaan', 'Jumlah']
        )
        .properties(width=900, height=400)
    )
    st.altair_chart(chart, use_container_width=True)

# =========================
# 🩸 PIE CHART KOMPONEN
# =========================
if 'Komponen' in df_filtered.columns:
    st.markdown("### 🧪 Komposisi Komponen Darah (Pie Chart)")
    df_pie = df_filtered['Komponen'].value_counts().reset_index()
    df_pie.columns = ['Komponen', 'Jumlah']
    pie_chart = (
        alt.Chart(df_pie)
        .mark_arc(innerRadius=60)
        .encode(
            theta='Jumlah:Q',
            color='Komponen:N',
            tooltip=['Komponen', 'Jumlah']
        )
        .properties(width=500, height=400)
    )
    st.altair_chart(pie_chart, use_container_width=True)

# =========================
# 🧾 FOOTER
# =========================
st.markdown("---")
st.caption("📡 Auto-refresh setiap 30 detik dari Google Sheets | Dibuat dengan ❤️ menggunakan Streamlit & Altair")

