import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO
import math

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
        .sidebar-title {
            font-size: 18px;
            font-weight: 700;
            color: #9CDCFE;
        }
        table {
            color: white !important;
        }
        .pagination-btn {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 10px;
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
    if 'Tanggal Droping' in df.columns:
        df['Tanggal Droping'] = pd.to_datetime(df['Tanggal Droping'], errors='coerce')
    if 'Bulan' in df.columns and 'Tahun' in df.columns:
        df['Periode'] = df['Bulan'].astype(str) + " " + df['Tahun'].astype(str)
    return df

df = load_data()

# =========================
# 🧠 FILTER DATA
# =========================
st.sidebar.markdown('<p class="sidebar-title">🎛️ Filter Data</p>', unsafe_allow_html=True)

jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", jenis_list, default=jenis_list)

form_list = df['Jenis Pengimputan'].dropna().unique().tolist()
form_filter = st.sidebar.multiselect("Jenis Formulir:", form_list, default=form_list)

# Filter RS
rs_list = sorted(df['RS/Klinik Tujuan'].dropna().unique().tolist())
select_all = st.sidebar.checkbox("Pilih Semua RS/Klinik Tujuan", value=True)
if select_all:
    rs_filter = rs_list
else:
    rs_filter = st.sidebar.multiselect("Pilih RS/Klinik Tujuan:", rs_list, default=[])

# Filter Bulan
st.sidebar.markdown("---")
st.sidebar.markdown('<p class="sidebar-title">🗓️ Filter Menurut Bulan</p>', unsafe_allow_html=True)
bulan_list = sorted(df['Bulan'].dropna().unique().tolist())
bulan_filter = st.sidebar.multiselect("Pilih Bulan:", bulan_list, default=bulan_list)

# =========================
# 🧩 LOGIKA FILTER
# =========================
df_filtered = df.copy()
df_filtered = df_filtered[df_filtered['Jenis Permintaan'].isin(jenis_filter)]
df_filtered = df_filtered[df_filtered['Jenis Pengimputan'].isin(form_filter)]
df_filtered = df_filtered[df_filtered['RS/Klinik Tujuan'].isin(rs_filter)]
df_filtered = df_filtered[df_filtered['Bulan'].isin(bulan_filter)]

# =========================
# 🕒 INFO DATA TERAKHIR
# =========================
if 'Tanggal Droping' in df.columns:
    last_date = df['Tanggal Droping'].max()
    if pd.notnull(last_date):
        st.markdown(f"### 🕒 Data terakhir diinput: **{last_date.strftime('%d %B %Y')}**")

# =========================
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Distribusi & Pelayanan Darah 2026")
st.markdown("#### Analisis Droping, Permintaan & Pemenuhan | Real-time dari Google Sheets")
st.markdown("---")

# =========================
# 📦 DOWNLOAD DATA
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
    if len(df_trend) > 0:
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
    else:
        st.warning("Tidak ada data untuk ditampilkan.")

# =========================
# 🏥 DISTRIBUSI MENURUT RS/KLINIK TUJUAN
# =========================
st.subheader("🏥 Distribusi Menurut RS/Klinik Tujuan (Total Jumlah)")
if 'RS/Klinik Tujuan' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
    df_rs = df_filtered.groupby('RS/Klinik Tujuan')['Jumlah'].sum().reset_index()
    df_rs = df_rs.sort_values('Jumlah', ascending=False)
    chart_rs = (
        alt.Chart(df_rs)
        .mark_bar(color="#33FF99")
        .encode(
            x=alt.X('RS/Klinik Tujuan:N', sort='-y', title='RS/Klinik Tujuan'),
            y=alt.Y('Jumlah:Q', title='Total Jumlah'),
            tooltip=['RS/Klinik Tujuan', 'Jumlah']
        )
        .properties(width=950, height=400)
    )
    st.altair_chart(chart_rs, use_container_width=True)

# =========================
# 📋 DATA INPUT TERBARU (10 baris per halaman + tombol prev/next)
# =========================
st.subheader("📋 Data Input Terbaru (10 Baris per Halaman)")
page_size = 10
total_rows = len(df_filtered)
total_pages = math.ceil(total_rows / page_size)

if "page_number" not in st.session_state:
    st.session_state.page_number = 1

col_prev, col_next = st.columns([1, 1])
with col_prev:
    if st.button("⬅️ Previous"):
        if st.session_state.page_number > 1:
            st.session_state.page_number -= 1
with col_next:
    if st.button("Next ➡️"):
        if st.session_state.page_number < total_pages:
            st.session_state.page_number += 1

page_number = st.session_state.page_number
start_idx = (page_number - 1) * page_size
end_idx = start_idx + page_size

if total_rows > 0:
    st.dataframe(df_filtered.iloc[start_idx:end_idx], use_container_width=True, height=380)
    st.caption(f"📄 Halaman {page_number} dari {total_pages} | Menampilkan {start_idx+1}-{min(end_idx, total_rows)} dari {total_rows} baris.")
else:
    st.warning("⚠️ Tidak ada data sesuai filter yang dipilih.")

# =========================
# 🧾 FOOTER
# =========================
st.markdown("---")
st.caption("📡 Auto-refresh setiap 30 detik | Dark Mode Profesional | Dibuat dengan ❤️ menggunakan Streamlit & Altair")
