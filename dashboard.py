import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO

# =========================
# 🎨 KONFIGURASI HALAMAN
# =========================
st.set_page_config(page_title="Dashboard Distribusi Darah", layout="wide", page_icon="💉")

# =========================
# 🌙 DARK MODE STYLING
# =========================
st.markdown("""
    <style>
        html, body, [class*="css"] {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        h1,h2,h3,h4 {color:#58a6ff;}
        .stDataFrame {border-radius: 10px;}
        .sidebar-title {
            font-size: 18px;
            font-weight: 700;
            color: #9CDCFE;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# 📊 AMBIL DATA
# =========================
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = [c.strip() for c in df.columns]
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
    if 'Bulan' in df.columns and 'Tahun' in df.columns:
        df['Periode'] = df['Bulan'].astype(str) + " " + df['Tahun'].astype(str)
    return df

df = load_data()

# =========================
# 🧠 FILTER DATA
# =========================
st.sidebar.markdown('<p class="sidebar-title">🎛️ Filter Data</p>', unsafe_allow_html=True)

# Jenis Distribusi
jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", jenis_list, default=jenis_list)

# Jenis Formulir
form_list = df['Jenis Pengimputan'].dropna().unique().tolist()
form_filter = st.sidebar.multiselect("Jenis Formulir:", form_list, default=form_list)

# RS/Klinik Tujuan (UTAMA)
if 'Droping RS/Klinik Tujuan' in df.columns:
    rs_list = sorted(df['Droping RS/Klinik Tujuan'].dropna().unique().tolist())
    select_all = st.sidebar.checkbox("Pilih Semua RS/Klinik Tujuan", value=True)
    if select_all:
        rs_filter = rs_list
    else:
        rs_filter = st.sidebar.multiselect("Pilih RS/Klinik Tujuan:", rs_list, default=[])
else:
    rs_filter = []

# =========================
# 🧭 FILTER MENURUT BULAN
# =========================
st.sidebar.markdown("---")
st.sidebar.markdown('<p class="sidebar-title">🗓️ Filter Menurut Bulan</p>', unsafe_allow_html=True)

bulan_list = sorted(df['Bulan'].dropna().unique().tolist())
bulan_filter = st.sidebar.multiselect("Pilih Bulan:", bulan_list, default=bulan_list)

# =========================
# 🏥 FILTER MENURUT RS/KLINIK TUJUAN (langsung dari kolom D)
# =========================
st.sidebar.markdown("---")
st.sidebar.markdown('<p class="sidebar-title">🏥 Filter Menurut RS/Klinik Tujuan</p>', unsafe_allow_html=True)

# 🔥 Ambil langsung dari kolom D (Droping RS/Klinik Tujuan)
if 'Droping RS/Klinik Tujuan' in df.columns:
    rs_filter_extra = st.sidebar.multiselect(
        "Pilih RS/Klinik (Tambahan):",
        options=sorted(df['Droping RS/Klinik Tujuan'].dropna().unique().tolist()),
        default=[]
    )
else:
    rs_filter_extra = []

# =========================
# 🧩 LOGIKA FILTER
# =========================
df_filtered = df[
    (df['Jenis Permintaan'].isin(jenis_filter)) &
    (df['Jenis Pengimputan'].isin(form_filter))
]

# Gabungkan kedua filter RS (utama + tambahan)
if rs_filter or rs_filter_extra:
    combined_rs = list(set(rs_filter + rs_filter_extra))
    df_filtered = df_filtered[df_filtered['Droping RS/Klinik Tujuan'].isin(combined_rs)]

if bulan_filter:
    df_filtered = df_filtered[df_filtered['Bulan'].isin(bulan_filter)]

# =========================
# 🕒 INFO DATA TERAKHIR
# =========================
if 'Tanggal' in df.columns:
    last_date = df['Tanggal'].max()
    if pd.notnull(last_date):
        st.markdown(f"### 🕒 Data terakhir diinput: **{last_date.strftime('%d %B %Y')}**")

# =========================
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Distribusi & Pelayanan Darah 2026")
st.markdown("#### Analisis Droping, Permintaan & Pemenuhan | Real-time dari Google Sheets")
st.markdown("---")

# =========================
# 📥 DOWNLOAD DATA
# =========================
st.subheader("📦 Download Data Terfilter")
csv_buffer = StringIO()
df_filtered.to_csv(csv_buffer, index=False)
st.download_button(
    label="⬇️ Download Data (CSV)",
    data=csv_buffer.getvalue(),
    file_name="data_terfilter.csv",
    mime="text/csv"
)

# =========================
# 📈 TREND BULANAN (TOTAL)
# =========================
st.subheader("📊 Trend Bulanan (Total Jumlah)")
if 'Periode' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
    df_trend = df_filtered.groupby('Periode', as_index=False)['Jumlah'].sum().sort_values('Periode')
    chart_trend = (
        alt.Chart(df_trend)
        .mark_line(point=True, color='#00c4ff')
        .encode(
            x=alt.X('Periode:N', title='Periode (Bulan)'),
            y=alt.Y('Jumlah:Q', title='Total Jumlah'),
            tooltip=['Periode', 'Jumlah']
        )
        .properties(width=950, height=350)
    )
    st.altair_chart(chart_trend, use_container_width=True)

# =========================
# 🏥 TREND MENURUT RS/KLINIK TUJUAN
# =========================
st.subheader("🏥 Trend Bulanan Menurut RS/Klinik Tujuan")
if 'Periode' in df_filtered.columns and 'Droping RS/Klinik Tujuan' in df_filtered.columns:
    df_trend_rs = (
        df_filtered.groupby(['Periode', 'Droping RS/Klinik Tujuan'], as_index=False)['Jumlah'].sum()
    )
    top_rs = df_trend_rs.groupby('Droping RS/Klinik Tujuan')['Jumlah'].sum().nlargest(10).index
    df_trend_rs = df_trend_rs[df_trend_rs['Droping RS/Klinik Tujuan'].isin(top_rs)]

    chart_trend_rs = (
        alt.Chart(df_trend_rs)
        .mark_line(point=True)
        .encode(
            x=alt.X('Periode:N', title='Bulan'),
            y=alt.Y('Jumlah:Q', title='Jumlah'),
            color=alt.Color('Droping RS/Klinik Tujuan:N', title='RS/Klinik'),
            tooltip=['Periode', 'Droping RS/Klinik Tujuan', 'Jumlah']
        )
        .properties(width=950, height=400)
    )
    st.altair_chart(chart_trend_rs, use_container_width=True)

# =========================
# 🧾 FOOTER
# =========================
st.markdown("---")
st.caption("📡 Auto-refresh setiap 30 detik | Dark Mode Profesional | Dibuat dengan ❤️ menggunakan Streamlit & Altair")
