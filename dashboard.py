import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math

# =========================
# ⚙️ KONFIGURASI DASAR
# =========================
st.set_page_config(
    page_title="Dashboard Perbandingan Permintaan vs Pemenuhan",
    layout="wide",
    page_icon="💉"
)

# =========================
# 📱 DETEKSI MOBILE (AUTO COLLAPSE)
# =========================
is_mobile = st.session_state.get("is_mobile", False)
st.session_state.is_mobile = st.sidebar.toggle(
    "📱 Mode Mobile",
    value=is_mobile,
    help="Aktifkan jika dibuka dari HP"
)

# =========================
# 🎨 PILIHAN TEMA
# =========================
st.sidebar.header("🎨 Tema")
tema = st.sidebar.selectbox(
    "Mode Tampilan",
    ["Merah–Ungu Soft", "Biru–Toska", "Dark Mode", "Kuning–Oranye"]
)

tema_style = {
    "Merah–Ungu Soft": {
        "background": "linear-gradient(135deg, #f8cdda 0%, #1d2b64 100%)",
        "text": "#ffffff",
        "title": "#ffe5ec",
        "p": "#ff5f6d",
        "m": "#36cfc9",
    },
    "Biru–Toska": {
        "background": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)",
        "text": "#ffffff",
        "title": "#e0ffff",
        "p": "#ffcc00",
        "m": "#00ffff",
    },
    "Dark Mode": {
        "background": "#0e1117",
        "text": "#fafafa",
        "title": "#58a6ff",
        "p": "#ff7f0e",
        "m": "#1f77b4",
    },
    "Kuning–Oranye": {
        "background": "linear-gradient(135deg, #f9d423 0%, #ff4e50 100%)",
        "text": "#222",
        "title": "#fff3cd",
        "p": "#ff8c00",
        "m": "#f3722c",
    }
}

theme = tema_style[tema]

st.markdown(
    f"""
    <style>
    html, body {{
        background: {theme['background']} !important;
        color: {theme['text']} !important;
    }}
    h1,h2,h3 {{
        color: {theme['title']} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# 📊 DATA SOURCE
# =========================
urls = {
    2025: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQsbaP26Ljsop1EwVXWEbgXrtf_K17_tK1TlFWWepUBF_eyt8Uhpnr5ua8JaYcsCQmz-JoZbwnbI-F/pub?output=csv",
    2026: "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?output=csv"
}

label_tahun = {
    2025: "Data 2025",
    2026: "Monitoring Pengimputan Nurmala Sari, A.Md.AK"
}

@st.cache_data(ttl=300)
def load_data(url, tahun):
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = df.columns.str.strip()
    df["Tahun"] = tahun
    df["Label Tahun"] = label_tahun[tahun]
    return df

df = pd.concat(
    [load_data(urls[2025], 2025), load_data(urls[2026], 2026)],
    ignore_index=True
)

# =========================
# 🎛️ FILTER
# =========================
st.sidebar.header("🎛️ Filter Data")

mode_view = st.sidebar.radio(
    "📊 Mode Tampilan",
    ["Chart + Table", "Chart Only", "Table Only"],
    horizontal=True
)

jenis = st.sidebar.multiselect(
    "Jenis Distribusi",
    df["Jenis Permintaan"].dropna().unique(),
    default=df["Jenis Permintaan"].dropna().unique()
)

df = df[df["Jenis Permintaan"].isin(jenis)]

# =========================
# 👁️ TOGGLE PER CHART
# =========================
st.sidebar.header("🔘 Chart Control")

show_trend = st.sidebar.checkbox("Trend Bulanan", value=not st.session_state.is_mobile)
show_komponen = st.sidebar.checkbox("Komponen", value=True)
show_goldar = st.sidebar.checkbox("Golongan Darah", value=True)
show_rs = st.sidebar.checkbox("RS/Klinik", value=False)

# =========================
# 📊 FUNGSI CHART (OPTIMIZED)
# =========================
alt.data_transformers.disable_max_rows()

def bar_chart(df, title, color):
    return (
        alt.Chart(df)
        .mark_bar(color=color)
        .encode(
            x=alt.X("Kategori:N", sort="-y"),
            y="Jumlah:Q",
            tooltip=["Kategori", "Jumlah"]
        )
        .properties(height=300, title=title)
    )

# =========================
# 📈 TREND BULANAN
# =========================
if mode_view != "Table Only" and show_trend:
    st.subheader("📈 Trend Bulanan")

    data_trend = (
        df.groupby(["Label Tahun", "Bulan", "Jenis Pengimputan"], as_index=False)
        ["Jumlah"].sum()
    )

    chart = (
        alt.Chart(data_trend)
        .mark_line(point=True)
        .encode(
            x="Bulan:N",
            y="Jumlah:Q",
            color="Label Tahun:N",
            tooltip=["Label Tahun", "Bulan", "Jumlah"]
        )
        .properties(height=320)
    )

    st.altair_chart(chart, use_container_width=True)

# =========================
# 🧪 KOMPONEN
# =========================
if mode_view != "Table Only" and show_komponen:
    st.subheader("🧪 Komponen")

    data = (
        df.groupby(["Komponen"], as_index=False)["Jumlah"].sum()
        .rename(columns={"Komponen": "Kategori"})
    )

    st.altair_chart(bar_chart(data, "Distribusi Komponen", theme["p"]), use_container_width=True)

# =========================
# 🩸 GOLONGAN DARAH
# =========================
if mode_view != "Table Only" and show_goldar:
    st.subheader("🩸 Golongan Darah")

    data = (
        df.groupby("Golongan Darah", as_index=False)["Jumlah"].sum()
        .rename(columns={"Golongan Darah": "Kategori"})
    )

    st.altair_chart(bar_chart(data, "Golongan Darah", theme["m"]), use_container_width=True)

# =========================
# 🏥 RS / KLINIK
# =========================
if mode_view != "Table Only" and show_rs:
    st.subheader("🏥 RS / Klinik Tujuan")

    data = (
        df.groupby("RS/Klinik Tujuan", as_index=False)["Jumlah"].sum()
        .rename(columns={"RS/Klinik Tujuan": "Kategori"})
        .sort_values("Jumlah", ascending=False)
        .head(10)
    )

    st.altair_chart(bar_chart(data, "Top 10 RS/Klinik", theme["p"]), use_container_width=True)

# =========================
# 📋 TABLE
# =========================
if mode_view != "Chart Only":
    st.subheader("📋 Data Tabel")

    page_size = 10
    total = len(df)
    pages = math.ceil(total / page_size)

    if "page" not in st.session_state:
        st.session_state.page = 1

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Prev") and st.session_state.page > 1:
            st.session_state.page -= 1
    with col2:
        if st.button("Next ➡️") and st.session_state.page < pages:
            st.session_state.page += 1

    start = (st.session_state.page - 1) * page_size
    end = start + page_size

    st.dataframe(df.iloc[start:end], use_container_width=True)
    st.caption(f"Halaman {st.session_state.page} / {pages}")

# =========================
# 📥 DOWNLOAD
# =========================
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False)

st.download_button(
    "⬇️ Download Excel",
    output.getvalue(),
    "dashboard_filtered.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("💉 Dashboard Streamlit | Optimized & Mobile Ready")
