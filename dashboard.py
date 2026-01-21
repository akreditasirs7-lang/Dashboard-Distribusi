import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math

# =========================
# ⚙️ KONFIGURASI DASAR
# =========================
st.set_page_config(page_title="Dashboard Mirror Permintaan vs Pemenuhan 2025–2026", layout="wide", page_icon="💉")

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
    if "Tanggal Droping" in df.columns:
        df["Tanggal Droping"] = pd.to_datetime(df["Tanggal Droping"], errors="coerce")
    return df

df_2025 = load_data(urls[2025], 2025)
df_2026 = load_data(urls[2026], 2026)
df_all = pd.concat([df_2025, df_2026], ignore_index=True)

# =========================
# 📆 PILIH TAHUN
# =========================
tahun_pilihan = st.sidebar.multiselect("📆 Pilih Tahun:", [2025, 2026], default=[2025, 2026])
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

df_filtered = df[
    df["Jenis Permintaan"].isin(jenis_filter)
    & df["RS/Klinik Tujuan"].isin(rs_filter)
    & df["Bulan"].isin(bulan_filter)
]

# =========================
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Mirror Chart – Permintaan vs Pemenuhan (2025–2026)")
st.markdown("#### 📊 Perbandingan Kiri–Kanan dalam Satu Chart untuk Analisis yang Lebih Akurat")
st.markdown("---")

# =========================
# 📊 FUNGSI CHART MIRROR
# =========================
def mirror_chart(df, kategori, title, warna_kiri, warna_kanan):
    df_pivot = (
        df.groupby(["Jenis Pengimputan", kategori])["Jumlah"]
        .sum()
        .unstack(fill_value=0)
        .T
        .reset_index()
        .rename(columns={"index": kategori})
    )
    if "Permintaan" not in df_pivot.columns or "Pemenuhan" not in df_pivot.columns:
        return None

    df_pivot["Permintaan"] = -df_pivot["Permintaan"]  # nilai kiri negatif
    df_melt = df_pivot.melt(id_vars=[kategori], var_name="Jenis", value_name="Jumlah")

    chart = (
        alt.Chart(df_melt)
        .mark_bar()
        .encode(
            x=alt.X("Jumlah:Q", title="Jumlah (Kiri=Permintaan, Kanan=Pemenuhan)"),
            y=alt.Y(f"{kategori}:N", sort='-x', title=kategori),
            color=alt.Color(
                "Jenis:N",
                scale=alt.Scale(domain=["Permintaan", "Pemenuhan"], range=[warna_kiri, warna_kanan]),
            ),
            tooltip=[kategori, "Jenis", "Jumlah"]
        )
        .properties(width=950, height=500, title=title)
    )

    # Tambah garis tengah nol
    rule = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="white", strokeDash=[4, 4])
    return chart + rule

# =========================
# 📈 CHART: PER KOMPONEN
# =========================
if "Komponen" in df_filtered.columns:
    st.subheader("🧪 Mirror Chart: Permintaan vs Pemenuhan per Komponen")
    chart_komponen = mirror_chart(
        df_filtered, "Komponen",
        "🧪 Perbandingan Komponen (Mirror Chart)",
        theme["permintaan_color"], theme["pemenuhan_color"]
    )
    if chart_komponen:
        st.altair_chart(chart_komponen, use_container_width=True)

# =========================
# 🩸 CHART: PER GOLONGAN DARAH
# =========================
if "Golongan Darah" in df_filtered.columns:
    st.subheader("🩸 Mirror Chart: Permintaan vs Pemenuhan per Golongan Darah")
    chart_goldar = mirror_chart(
        df_filtered, "Golongan Darah",
        "🩸 Perbandingan Golongan Darah (Mirror Chart)",
        theme["permintaan_color"], theme["pemenuhan_color"]
    )
    if chart_goldar:
        st.altair_chart(chart_goldar, use_container_width=True)

# =========================
# 🏥 CHART: PER RS/KLINIK TUJUAN
# =========================
if "RS/Klinik Tujuan" in df_filtered.columns:
    st.subheader("🏥 Mirror Chart: Permintaan vs Pemenuhan per RS/Klinik Tujuan (Top 15)")
    df_filtered_top = df_filtered[df_filtered["RS/Klinik Tujuan"].isin(
        df_filtered["RS/Klinik Tujuan"].value_counts().head(15).index
    )]
    chart_rs = mirror_chart(
        df_filtered_top, "RS/Klinik Tujuan",
        "🏥 Perbandingan RS/Klinik Tujuan (Mirror Chart)",
        theme["permintaan_color"], theme["pemenuhan_color"]
    )
    if chart_rs:
        st.altair_chart(chart_rs, use_container_width=True)

# =========================
# 📥 DOWNLOAD DATA
# =========================
st.subheader("📦 Download Data Terfilter")
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_filtered.to_excel(writer, index=False, sheet_name="Data Terfilter")

st.download_button(
    label="⬇️ Download Data (Excel)",
    data=output.getvalue(),
    file_name="data_mirror_chart_2025_2026.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# 📋 TABEL DATA
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
    st.dataframe(df_filtered.iloc[start_idx:end_idx], use_container_width=True, height=380)
    st.caption(f"📄 Halaman {page_number} dari {total_pages} | Menampilkan {start_idx+1}-{min(end_idx, total_rows)} dari {total_rows} baris.")
else:
    st.warning("⚠️ Tidak ada data sesuai filter yang dipilih.")

st.markdown("---")
st.caption("📊 Dashboard Mirror Chart 2025–2026 | 💉 Jenis Permintaan vs Pemenuhan | Dibuat dengan ❤️ pakai Streamlit & Altair")
