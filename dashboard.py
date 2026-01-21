import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math

# =========================
# ⚙️ KONFIGURASI
# =========================
st.set_page_config(page_title="Dashboard Darah 2025–2026", layout="wide", page_icon="💉")

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
    </style>
""", unsafe_allow_html=True)

# =========================
# 🧠 LINK DATA
# =========================
url_2025 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQsbaP26Ljsop1EwVXWEbgXrtf_K17_tK1TlFWWepUBF_eyt8Uhpnr5ua8JaYcsCQmz-JoZbwnbI-F/pub?gid=0&single=true&output=csv"
url_2026 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url, tahun):
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = [c.strip() for c in df.columns]
    df["Tahun"] = tahun
    if "Bulan" in df.columns:
        df["Periode"] = df["Bulan"].astype(str) + " " + df["Tahun"].astype(str)
    if "Tanggal Droping" in df.columns:
        df["Tanggal Droping"] = pd.to_datetime(df["Tanggal Droping"], errors="coerce")
    return df

df_2025 = load_data(url_2025, 2025)
df_2026 = load_data(url_2026, 2026)

# Gabungkan kedua data
df_all = pd.concat([df_2025, df_2026], ignore_index=True)

# =========================
# 📆 PILIH TAHUN
# =========================
tahun_pilihan = st.sidebar.multiselect("📆 Pilih Tahun:", [2025, 2026], default=[2025, 2026])

# Filter tahun
df = df_all[df_all["Tahun"].isin(tahun_pilihan)]

# =========================
# 🎛️ FILTER DATA
# =========================
jenis_list = df["Jenis Permintaan"].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", jenis_list, default=jenis_list)

rs_list = sorted(df["RS/Klinik Tujuan"].dropna().unique().tolist())
rs_filter = st.sidebar.multiselect("RS/Klinik Tujuan:", rs_list, default=rs_list)

bulan_list = sorted(df["Bulan"].dropna().unique().tolist())
bulan_filter = st.sidebar.multiselect("🗓️ Pilih Bulan:", bulan_list, default=bulan_list)

# Terapkan filter
df_filtered = df[
    df["Jenis Permintaan"].isin(jenis_filter)
    & df["RS/Klinik Tujuan"].isin(rs_filter)
    & df["Bulan"].isin(bulan_filter)
]

# =========================
# 🕒 HEADER
# =========================
st.title("💉 Dashboard Distribusi Darah 2025–2026")
st.markdown("#### Analisis Droping, Permintaan & Pemenuhan Multi-Tahun (Real-time dari Google Sheets)")
st.markdown("---")

# =========================
# 📈 CHART FUNCTION
# =========================
def chart_with_label(data, x, y, title, color):
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
            color="#111",
            fontSize=13,
            fontWeight="bold"
        )
        .encode(x=f"{x}:N", y=f"{y}:Q", text=f"{y}:Q")
    )
    return (base + text).interactive()

# =========================
# 📊 TREND GABUNGAN (2025 vs 2026)
# =========================
st.subheader("📈 Perbandingan Trend Bulanan 2025 vs 2026")

if "Jumlah" in df_filtered.columns and "Bulan" in df_filtered.columns:
    df_trend = (
        df_filtered.groupby(["Tahun", "Bulan"], as_index=False)["Jumlah"]
        .sum()
        .sort_values(["Tahun", "Bulan"])
    )

    chart = (
        alt.Chart(df_trend)
        .mark_line(point=True)
        .encode(
            x="Bulan:N",
            y="Jumlah:Q",
            color="Tahun:N",
            tooltip=["Tahun", "Bulan", "Jumlah"],
        )
        .properties(width=950, height=400, title="📊 Trend Bulanan Perbandingan 2025 vs 2026")
    )
    st.altair_chart(chart, use_container_width=True)

# =========================
# 📊 GRAFIK TAHUN TERPILIH
# =========================
st.subheader(f"📊 Analisis Berdasarkan Tahun yang Dipilih: {', '.join(map(str, tahun_pilihan))}")

if "RS/Klinik Tujuan" in df_filtered.columns:
    df_rs = df_filtered.groupby(["Tahun", "RS/Klinik Tujuan"])["Jumlah"].sum().reset_index()
    chart_rs = (
        alt.Chart(df_rs)
        .mark_bar()
        .encode(
            x="RS/Klinik Tujuan:N",
            y="Jumlah:Q",
            color="Tahun:N",
            tooltip=["Tahun", "RS/Klinik Tujuan", "Jumlah"]
        )
        .properties(width=950, height=400, title="🏥 Distribusi per RS/Klinik Tujuan (2025 vs 2026)")
    )
    st.altair_chart(chart_rs, use_container_width=True)

# =========================
# 📋 DATA TABLE
# =========================
st.subheader("📋 Data Terfilter")
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
st.caption("📊 Dashboard Perbandingan 2025–2026 | 🎨 Multi-Tema | Dibuat dengan ❤️ menggunakan Streamlit & Altair")
