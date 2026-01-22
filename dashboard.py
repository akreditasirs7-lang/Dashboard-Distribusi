import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from PIL import Image
import tempfile
import os

# =========================
# ⚙️ KONFIGURASI DASAR
# =========================
st.set_page_config(page_title="Dashboard Distribusi & Pelayanan Darah 2025–2026", layout="wide", page_icon="💉")

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
        "permintaan_color": "#ff5f6d",
        "pemenuhan_color": "#36cfc9",
    },
    "Biru–Toska": {
        "background": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)",
        "text_color": "#f9f9f9",
        "title_color": "#e0ffff",
        "permintaan_color": "#ffcc00",
        "pemenuhan_color": "#00ffff",
    },
    "Dark Mode": {
        "background": "#0e1117",
        "text_color": "#fafafa",
        "title_color": "#58a6ff",
        "permintaan_color": "#ff7f0e",
        "pemenuhan_color": "#1f77b4",
    },
    "Kuning–Oranye": {
        "background": "linear-gradient(135deg, #f9d423 0%, #ff4e50 100%)",
        "text_color": "#222",
        "title_color": "#fff3cd",
        "permintaan_color": "#ff8c00",
        "pemenuhan_color": "#f3722c",
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
# 📊 DATA SOURCES
# =========================
urls = {
    2025: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQsbaP26Ljsop1EwVXWEbgXrtf_K17_tK1TlFWWepUBF_eyt8Uhpnr5ua8JaYcsCQmz-JoZbwnbI-F/pub?gid=0&single=true&output=csv",
    2026: "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"
}

@st.cache_data(ttl=60)
def load_data(url, tahun):
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = [c.strip() for c in df.columns]
    df["Tahun"] = tahun
    if "Bulan" in df.columns:
        df["Periode"] = df["Bulan"].astype(str) + " " + df["Tahun"].astype(str)
    return df

df_all = pd.concat([load_data(urls[2025], 2025), load_data(urls[2026], 2026)], ignore_index=True)

# =========================
# 📆 FILTER
# =========================
tahun_pilihan = st.sidebar.multiselect("📆 Pilih Tahun:", [2025, 2026], default=[2025, 2026])
df = df_all[df_all["Tahun"].isin(tahun_pilihan)]

jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", df["Jenis Permintaan"].dropna().unique().tolist())
rs_filter = st.sidebar.multiselect("RS/Klinik Tujuan:", df["RS/Klinik Tujuan"].dropna().unique().tolist())
bulan_filter = st.sidebar.multiselect("🗓️ Pilih Bulan:", sorted(df["Bulan"].dropna().unique().tolist()))

df_filtered = df[
    df["Jenis Permintaan"].isin(jenis_filter)
    & df["RS/Klinik Tujuan"].isin(rs_filter)
    & df["Bulan"].isin(bulan_filter)
]

# =========================
# 📊 FUNGSI CHART
# =========================
def chart_bar(df, title, color):
    base = (
        alt.Chart(df)
        .mark_bar(color=color)
        .encode(
            x=alt.X("Kategori:N", sort='-y', title="Kategori"),
            y=alt.Y("Jumlah:Q", title="Total Jumlah", scale=alt.Scale(padding=25)),
            tooltip=["Kategori", "Jumlah"]
        )
        .properties(width=500, height=350, title=title)
    )
    text = (
        alt.Chart(df)
        .mark_text(align="center", baseline="bottom", dy=-5, color="white", fontWeight="bold")
        .encode(x="Kategori:N", y="Jumlah:Q", text="Jumlah:Q")
    )
    return base + text

# =========================
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Distribusi & Pelayanan Darah 2025–2026")

# =========================
# TOGGLE CHART
# =========================
st.sidebar.header("📊 Pilih Chart yang Ditampilkan")
show_trend = st.sidebar.checkbox("📈 Trend Bulanan", True)
show_rs = st.sidebar.checkbox("🏥 RS/Klinik Tujuan", True)
show_goldar = st.sidebar.checkbox("🩸 Golongan Darah", True)
show_rhesus = st.sidebar.checkbox("🧬 Rhesus", True)
show_komponen = st.sidebar.checkbox("🧪 Komponen", True)

chart_files = []

# =========================
# 📈 TREND BULANAN
# =========================
if show_trend:
    st.subheader("📈 Trend Bulanan Permintaan vs Pemenuhan (Side-by-Side)")
    col1, col2 = st.columns(2)
    for jenis, col, warna in zip(["Permintaan", "Pemenuhan"], [col1, col2],
                                 [theme['permintaan_color'], theme['pemenuhan_color']]):
        with col:
            df_trend = (
                df_filtered[df_filtered["Jenis Pengimputan"] == jenis]
                .groupby(["Tahun", "Bulan"], as_index=False)["Jumlah"]
                .sum()
            )
            if not df_trend.empty:
                chart = (
                    alt.Chart(df_trend)
                    .mark_line(point=True, color=warna)
                    .encode(x="Bulan:N", y="Jumlah:Q", color="Tahun:N")
                    .properties(title=f"Trend Bulanan {jenis}")
                )
                st.altair_chart(chart, use_container_width=True)
                # Simpan chart ke file sementara
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                chart.save(temp.name)
                chart_files.append((f"Trend Bulanan {jenis}", temp.name))

# =========================
# FUNGSI TAMBAH CHART KATEGORI
# =========================
def add_chart(df_filtered, kategori, title_prefix):
    col1, col2 = st.columns(2)
    for jenis, col, warna in zip(["Permintaan", "Pemenuhan"], [col1, col2],
                                 [theme['permintaan_color'], theme['pemenuhan_color']]):
        with col:
            df_cat = (
                df_filtered[df_filtered["Jenis Pengimputan"] == jenis]
                .groupby(kategori, as_index=False)["Jumlah"]
                .sum()
                .rename(columns={kategori: "Kategori"})
            )
            if not df_cat.empty:
                chart = chart_bar(df_cat, f"{jenis} per {title_prefix}", warna)
                st.altair_chart(chart, use_container_width=True)
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                chart.save(temp.name)
                chart_files.append((f"{jenis} per {title_prefix}", temp.name))

# =========================
# CHART TAMBAHAN
# =========================
if show_rs:
    st.subheader("🏥 Distribusi RS/Klinik Tujuan")
    add_chart(df_filtered, "RS/Klinik Tujuan", "RS/Klinik Tujuan")

if show_goldar:
    st.subheader("🩸 Golongan Darah")
    add_chart(df_filtered, "Golongan Darah", "Golongan Darah")

if show_rhesus:
    st.subheader("🧬 Rhesus")
    add_chart(df_filtered, "Rhesus", "Rhesus")

if show_komponen:
    st.subheader("🧪 Komponen")
    add_chart(df_filtered, "Komponen", "Komponen")

# =========================
# 📄 DOWNLOAD PDF (DENGAN SEMUA CHART)
# =========================
if st.button("📄 Download PDF (Termasuk Semua Chart)"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 1.5*cm, "📊 Laporan Dashboard Distribusi & Pelayanan Darah")
    y = height - 3.0*cm
    for title, img_path in chart_files:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, title)
        y -= 0.5*cm
        img = Image.open(img_path)
        img_width = 20*cm
        img_height = 8*cm
        if y - img_height < 2*cm:
            c.showPage()
            y = height - 2.5*cm
        c.drawImage(img_path, 2*cm, y - img_height, width=img_width, height=img_height)
        y -= img_height + 1*cm
    c.save()

    st.download_button(
        label="⬇️ Simpan PDF (Lengkap)",
        data=buffer.getvalue(),
        file_name="Laporan_Dashboard_Darah_Lengkap.pdf",
        mime="application/pdf"
    )

# =========================
# DOWNLOAD EXCEL
# =========================
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_filtered.to_excel(writer, index=False, sheet_name="Data Terfilter")

st.download_button(
    label="⬇️ Download Data (Excel)",
    data=output.getvalue(),
    file_name="Data_Dashboard_Darah_2025_2026.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# TABEL
# =========================
st.subheader("📋 Data Input (10 Baris per Halaman)")
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
    st.dataframe(df_filtered.iloc[start_idx:end_idx], use_container_width=True)
else:
    st.warning("⚠️ Tidak ada data sesuai filter yang dipilih.")
