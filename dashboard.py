import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# =========================
# ⚙️ KONFIGURASI
# =========================
st.set_page_config(page_title="Dashboard Distribusi Darah", layout="wide", page_icon="💉")

# =========================
# 🎨 PILIHAN TEMA
# =========================
st.sidebar.header("🎨 Pilih Tema Dashboard")
tema = st.sidebar.selectbox(
    "Mode Tampilan:",
    ["Merah–Ungu Soft", "Biru–Toska", "Dark Mode", "Kuning–Oranye"]
)

tema_style = {
    "Merah–Ungu Soft": {
        "background": "linear-gradient(135deg, #f8cdda 0%, #1d2b64 100%)",
        "text_color": "#fefefe",
        "title_color": "#ffe5ec",
        "bar_colors": ["#00c4ff", "#33FF99", "#FF7F50", "#4FC3F7", "#FF6B6B"]
    },
    "Biru–Toska": {
        "background": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)",
        "text_color": "#f9f9f9",
        "title_color": "#e0ffff",
        "bar_colors": ["#ffcc00", "#00ffff", "#ff6699", "#33ff99", "#ff9966"]
    },
    "Dark Mode": {
        "background": "#0e1117",
        "text_color": "#fafafa",
        "title_color": "#58a6ff",
        "bar_colors": ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#ff7f0e"]
    },
    "Kuning–Oranye": {
        "background": "linear-gradient(135deg, #f9d423 0%, #ff4e50 100%)",
        "text_color": "#222",
        "title_color": "#fff3cd",
        "bar_colors": ["#f5b700", "#ff8c00", "#f3722c", "#f94144", "#90be6d"]
    }
}

# Terapkan tema
theme = tema_style[tema]
st.markdown(f"""
    <style>
        html, body, [class*="css"] {{
            background: {theme['background']} !important;
            color: {theme['text_color']} !important;
        }}
        h1,h2,h3,h4 {{
            color: {theme['title_color']};
        }}
        .sidebar-title {{
            font-size: 18px;
            font-weight: 700;
            color: {theme['title_color']};
        }}
        .stButton>button {{
            background-color: #ffffff22 !important;
            color: {theme['text_color']} !important;
            font-weight: bold;
            border-radius: 8px;
        }}
        table {{
            color: {theme['text_color']} !important;
        }}
        .toggle-box {{
            background-color: rgba(255,255,255,0.1);
            border: 1px solid #ffffff33;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
    </style>
""", unsafe_allow_html=True)

# =========================
# 📊 LOAD DATA
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
# 🧠 FILTER
# =========================
st.sidebar.markdown('<p class="sidebar-title">🎛️ Filter Data</p>', unsafe_allow_html=True)

jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", jenis_list, default=jenis_list)

form_list = df['Jenis Pengimputan'].dropna().unique().tolist()
form_filter = st.sidebar.multiselect("Jenis Formulir:", form_list, default=form_list)

rs_list = sorted(df['RS/Klinik Tujuan'].dropna().unique().tolist())
select_all = st.sidebar.checkbox("Pilih Semua RS/Klinik Tujuan", value=True)
if select_all:
    rs_filter = rs_list
else:
    rs_filter = st.sidebar.multiselect("Pilih RS/Klinik Tujuan:", rs_list, default=[])

st.sidebar.markdown("---")
bulan_list = sorted(df['Bulan'].dropna().unique().tolist())
bulan_filter = st.sidebar.multiselect("🗓️ Pilih Bulan:", bulan_list, default=bulan_list)

# =========================
# FILTER LOGIKA
# =========================
df_filtered = df.copy()
df_filtered = df_filtered[
    df_filtered['Jenis Permintaan'].isin(jenis_filter)
    & df_filtered['Jenis Pengimputan'].isin(form_filter)
    & df_filtered['RS/Klinik Tujuan'].isin(rs_filter)
    & df_filtered['Bulan'].isin(bulan_filter)
]

# =========================
# HEADER
# =========================
if 'Tanggal Droping' in df.columns:
    last_date = df['Tanggal Droping'].max()
    if pd.notnull(last_date):
        st.markdown(f"### 🕒 Data terakhir diinput: **{last_date.strftime('%d %B %Y')}**")

st.title("💉 Dashboard Distribusi & Pelayanan Darah 2026")
st.markdown("#### Analisis Droping, Permintaan & Pemenuhan | Real-time dari Google Sheets")
st.markdown("---")

# =========================
# DOWNLOAD EXCEL
# =========================
st.subheader("📦 Download Data Terfilter")
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_filtered.to_excel(writer, index=False, sheet_name="Data Terfilter")

st.download_button(
    label="⬇️ Download Data (Excel)",
    data=output.getvalue(),
    file_name="data_terfilter.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# TOGGLE GRAFIK
# =========================
st.markdown('<div class="toggle-box">', unsafe_allow_html=True)
show_graphs = st.toggle("🧭 Tampilkan Semua Grafik", value=True)
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# CHART FUNCTION
# =========================
def chart_with_label(data, x, y, title, color):
    text_color = "#111" if color not in ["#1f77b4", "#2ca02c", "#d62728", "#9467bd"] else "#fff"

    base = (
        alt.Chart(data)
        .mark_bar(color=color)
        .encode(
            x=alt.X(f"{x}:N", sort='-y', title=x),
            y=alt.Y(f"{y}:Q", title="Total Jumlah"),
            tooltip=[x, y],
        )
        .properties(width=950, height=400, title=title)
    )

    text = (
        alt.Chart(data)
        .mark_text(
            align="center",
            baseline="bottom",
            dy=-8,
            color=text_color,
            fontSize=13,
            fontWeight="bold"
        )
        .encode(
            x=alt.X(f"{x}:N", sort='-y'),
            y=alt.Y(f"{y}:Q"),
            text=alt.Text(f"{y}:Q")
        )
    )

    return (base + text).interactive()

# =========================
# GRAFIK-GRAFIK
# =========================
if show_graphs:
    colors = theme["bar_colors"]
    if 'Periode' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
        df_trend = df_filtered.groupby('Periode', as_index=False)['Jumlah'].sum().sort_values('Periode')
        st.altair_chart(chart_with_label(df_trend, 'Periode', 'Jumlah', "📊 Trend Bulanan", colors[0]))

    if 'RS/Klinik Tujuan' in df_filtered.columns:
        df_rs = df_filtered.groupby('RS/Klinik Tujuan')['Jumlah'].sum().reset_index().sort_values('Jumlah', ascending=False)
        st.altair_chart(chart_with_label(df_rs, 'RS/Klinik Tujuan', 'Jumlah', "🏥 Distribusi Menurut RS/Klinik Tujuan", colors[1]))

    if 'Komponen' in df_filtered.columns:
        df_komp = df_filtered.groupby('Komponen')['Jumlah'].sum().reset_index()
        st.altair_chart(chart_with_label(df_komp, 'Komponen', 'Jumlah', "🧪 Distribusi Menurut Komponen", colors[2]))

    if 'Golongan Darah' in df_filtered.columns:
        df_goldar = df_filtered.groupby('Golongan Darah')['Jumlah'].sum().reset_index()
        st.altair_chart(chart_with_label(df_goldar, 'Golongan Darah', 'Jumlah', "🩸 Distribusi Menurut Golongan Darah", colors[3]))

    if 'Rhesus' in df_filtered.columns:
        df_rhesus = df_filtered.groupby('Rhesus')['Jumlah'].sum().reset_index()
        st.altair_chart(chart_with_label(df_rhesus, 'Rhesus', 'Jumlah', "🧬 Distribusi Rhesus (Positif vs Negatif)", colors[4]))

# =========================
# 📋 TABEL DATA
# =========================
st.subheader("📋 Data Input Terbaru (10 Baris per Halaman)")
page_size = 10
total_rows = len(df_filtered)
total_pages = math.ceil(total_rows / page_size)
if "page_number" not in st.session_state:
    st.session_state.page_number = 1

col_prev, col_next = st.columns(2)
with col_prev:
    if st.button("⬅️ Previous") and st.session_state.page_number > 1:
        st.session_state.page_number -= 1
with col_next:
    if st.button("Next ➡️") and st.session_state.page_number < total_pages:
        st.session_state.page_number += 1

page_number = st.session_state.page_number
start_idx = (page_number - 1) * page_size
end_idx = start_idx + page_size

if total_rows > 0:
    st.dataframe(df_filtered.iloc[start_idx:end_idx], use_container_width=True, height=380)
    st.caption(f"📄 Halaman {page_number} dari {total_pages} | Menampilkan {start_idx+1}-{min(end_idx, total_rows)} dari {total_rows} baris.")
else:
    st.warning("⚠️ Tidak ada data sesuai filter yang dipilih.")

st.markdown("---")
st.caption("🎨 Multi-Tema Dashboard | Real-time Google Sheets | Dibuat dengan ❤️ oleh kamu bro 😎")
