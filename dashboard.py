import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math

# =========================
# ⚙️ KONFIGURASI DASAR
# =========================
st.set_page_config(page_title="Dashboard Perbandingan Permintaan vs Pemenuhan 2025–2026", layout="wide", page_icon="💉")

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
        "permintaan_color": "#1E90FF",  # biru
        "pemenuhan_color": "#FF3030",  # merah
    },
    "Biru–Toska": {
        "background": "linear-gradient(135deg, #00b4db 0%, #0083b0 100%)",
        "text_color": "#f9f9f9",
        "title_color": "#e0ffff",
        "permintaan_color": "#00ffff",
        "pemenuhan_color": "#ffcc00",
    },
    "Dark Mode": {
        "background": "#0e1117",
        "text_color": "#fafafa",
        "title_color": "#58a6ff",
        "permintaan_color": "#1f77b4",
        "pemenuhan_color": "#d62728",
    },
    "Kuning–Oranye": {
        "background": "linear-gradient(135deg, #f9d423 0%, #ff4e50 100%)",
        "text_color": "#222",
        "title_color": "#fff3cd",
        "permintaan_color": "#ffa500",
        "pemenuhan_color": "#ff6347",
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
st.title("💉 Dashboard Batang Sejajar – Permintaan vs Pemenuhan (2025–2026)")
st.markdown("#### 📊 Batang sejajar kiri-kanan dalam satu grafik, warna berbeda")
st.markdown("---")

# =========================
# 📊 FUNGSI GRAFIK
# =========================
def dual_bar_chart(df, kategori, title, warna_kiri, warna_kanan):
    df_group = (
        df.groupby(["Jenis Pengimputan", kategori])["Jumlah"]
        .sum()
        .reset_index()
    )
    chart = (
        alt.Chart(df_group)
        .mark_bar()
        .encode(
            x=alt.X(f"{kategori}:N", sort='-y', title=kategori),
            y=alt.Y("Jumlah:Q", title="Total Jumlah"),
            color=alt.Color(
                "Jenis Pengimputan:N",
                scale=alt.Scale(domain=["Permintaan", "Pemenuhan"], range=[warna_kiri, warna_kanan]),
                title="Jenis"
            ),
            tooltip=[kategori, "Jenis Pengimputan", "Jumlah"]
        )
        .properties(title=title, width=900, height=400)
    )

    # Tambahkan label angka di atas batang
    text = (
        alt.Chart(df_group)
        .mark_text(
            align='center', baseline='bottom', dy=-5,
            color='white', fontSize=13, fontWeight='bold'
        )
        .encode(
            x=f"{kategori}:N",
            y="Jumlah:Q",
            detail="Jenis Pengimputan:N",
            text="Jumlah:Q"
        )
    )

    return (chart + text).configure_axis(labelColor=theme["text_color"], titleColor=theme["title_color"])

# =========================
# 🧪 PERBANDINGAN KOMPONEN
# =========================
if "Komponen" in df_filtered.columns:
    st.subheader("🧪 Perbandingan Komponen (Batang Sejajar)")
    st.altair_chart(
        dual_bar_chart(
            df_filtered, "Komponen",
            "🧪 Perbandingan Komponen – Permintaan vs Pemenuhan",
            theme["permintaan_color"], theme["pemenuhan_color"]
        ),
        use_container_width=True
    )

# =========================
# 🩸 PERBANDINGAN GOLONGAN DARAH
# =========================
if "Golongan Darah" in df_filtered.columns:
    st.subheader("🩸 Perbandingan Golongan Darah (Batang Sejajar)")
    st.altair_chart(
        dual_bar_chart(
            df_filtered, "Golongan Darah",
            "🩸 Perbandingan Golongan Darah – Permintaan vs Pemenuhan",
            theme["permintaan_color"], theme["pemenuhan_color"]
        ),
        use_container_width=True
    )

# =========================
# 🏥 PERBANDINGAN RS/KLINIK TUJUAN
# =========================
if "RS/Klinik Tujuan" in df_filtered.columns:
    st.subheader("🏥 Perbandingan RS/Klinik Tujuan (Top 15, Batang Sejajar)")
    df_top = df_filtered[df_filtered["RS/Klinik Tujuan"].isin(
        df_filtered["RS/Klinik Tujuan"].value_counts().head(15).index
    )]
    st.altair_chart(
        dual_bar_chart(
            df_top, "RS/Klinik Tujuan",
            "🏥 Perbandingan RS/Klinik Tujuan – Permintaan vs Pemenuhan",
            theme["permintaan_color"], theme["pemenuhan_color"]
        ),
        use_container_width=True
    )

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
    file_name="data_dualbar_2025_2026.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# 📋 DATA TABLE
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
st.caption("📊 Dashboard Batang Sejajar 2025–2026 | 💉 Permintaan vs Pemenuhan | Dibuat dengan ❤️ pakai Streamlit & Altair")
