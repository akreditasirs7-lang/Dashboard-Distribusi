import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# ⚙️ KONFIGURASI DASAR
# =========================
st.set_page_config(
    page_title="Dashboard Monitoring Pengimputan",
    layout="wide",
    page_icon="💉"
)

alt.data_transformers.disable_max_rows()

# =========================
# 🎨 TEMA
# =========================
st.sidebar.header("🎨 Tema")
tema = st.sidebar.selectbox(
    "Mode Tampilan:",
    ["Merah–Ungu Soft", "Biru–Toska", "Dark Mode", "Kuning–Oranye"]
)

tema_style = {
    "Merah–Ungu Soft": {"p": "#ff5f6d", "m": "#36cfc9"},
    "Biru–Toska": {"p": "#ffcc00", "m": "#00ffff"},
    "Dark Mode": {"p": "#ff7f0e", "m": "#1f77b4"},
    "Kuning–Oranye": {"p": "#ff8c00", "m": "#f3722c"},
}
theme = tema_style[tema]

# =========================
# 📊 DATA SOURCE
# =========================
urls = {
    2025: "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQsbaP26Ljsop1EwVXWEbgXrtf_K17_tK1TlFWWepUBF_eyt8Uhpnr5ua8JaYcsCQmz-JoZbwnbI-F/pub?gid=0&single=true&output=csv",
    2026: "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"
}

label_tahun = {
    2025: "Data 2025",
    2026: "Monitoring Pengimputan Nurmala Sari, A.Md.AK"
}

@st.cache_data(ttl=120)
def load_data(url, tahun):
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = df.columns.str.strip()
    df["Tahun"] = tahun
    df["Label Tahun"] = label_tahun[tahun]
    return df

df_all = pd.concat(
    [load_data(urls[2025], 2025), load_data(urls[2026], 2026)],
    ignore_index=True
)

# =========================
# 📆 FILTER TAHUN
# =========================
opsi_tahun = {
    "Data 2025": 2025,
    "Monitoring Pengimputan Nurmala Sari, A.Md.AK": 2026
}

label_pilih = st.sidebar.multiselect(
    "📆 Pilih Sumber Data",
    list(opsi_tahun.keys()),
    default=list(opsi_tahun.keys())
)

tahun_pilih = [opsi_tahun[l] for l in label_pilih]
df = df_all[df_all["Tahun"].isin(tahun_pilih)]

# =========================
# 🎛️ FILTER LAIN
# =========================
bulan_list = sorted(df["Bulan"].dropna().unique())
bulan_filter = st.sidebar.multiselect("Bulan", bulan_list, default=bulan_list)
df = df[df["Bulan"].isin(bulan_filter)]

# =========================
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Monitoring Permintaan vs Pemenuhan")
st.markdown("---")

# =========================
# 🧠 HELPER AUTO-HIDE
# =========================
def safe_chart(df, render_fn):
    if df.empty:
        st.info("ℹ️ Tidak ada data sesuai filter")
    else:
        render_fn()

# =========================
# 📊 SIDE-BY-SIDE CHART
# =========================
def side_by_side(df, kolom, judul):
    c1, c2 = st.columns(2)

    for jenis, col, warna in zip(
        ["Permintaan", "Pemenuhan"],
        [c1, c2],
        [theme["p"], theme["m"]]
    ):
        with col:
            data = (
                df[df["Jenis Pengimputan"] == jenis]
                .groupby(kolom, as_index=False)["Jumlah"]
                .sum()
                .rename(columns={kolom: "Kategori"})
            )

            safe_chart(
                data,
                lambda: st.altair_chart(
                    alt.Chart(data)
                    .mark_bar(color=warna)
                    .encode(
                        x=alt.X("Kategori:N", sort="-y"),
                        y="Jumlah:Q",
                        tooltip=["Kategori", "Jumlah"]
                    )
                    .properties(title=f"{jenis} per {judul}", height=300),
                    use_container_width=True
                )
            )

# =========================
# 📈 TREND BULANAN
# =========================
st.subheader("📈 Trend Bulanan")

trend = (
    df.groupby(["Label Tahun", "Bulan", "Jenis Pengimputan"], as_index=False)["Jumlah"]
    .sum()
)

safe_chart(
    trend,
    lambda: st.altair_chart(
        alt.Chart(trend)
        .mark_line(point=True)
        .encode(
            x="Bulan:N",
            y="Jumlah:Q",
            color="Label Tahun:N",
            strokeDash="Jenis Pengimputan:N",
            tooltip=["Label Tahun", "Jenis Pengimputan", "Bulan", "Jumlah"]
        )
        .properties(height=350),
        use_container_width=True
    )
)

# =========================
# 📊 SIDE BY SIDE CHARTS
# =========================
st.subheader("🧪 Komponen")
side_by_side(df, "Komponen", "Komponen")

st.subheader("🩸 Golongan Darah")
side_by_side(df, "Golongan Darah", "Golongan Darah")

st.subheader("🧬 Rhesus")
side_by_side(df, "Rhesus", "Rhesus")

st.subheader("🏥 RS / Klinik Tujuan")
side_by_side(df, "RS/Klinik Tujuan", "RS/Klinik")

# =========================
# 🧾 EXPORT PDF (GRATIS)
# =========================
st.subheader("🧾 Export Laporan PDF")

def generate_pdf(dataframe):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Laporan Monitoring Pengimputan Darah", styles["Title"]))
    elements.append(Spacer(1, 12))

    total_perm = dataframe[dataframe["Jenis Pengimputan"] == "Permintaan"]["Jumlah"].sum()
    total_pem = dataframe[dataframe["Jenis Pengimputan"] == "Pemenuhan"]["Jumlah"].sum()

    elements.append(Paragraph(f"Total Permintaan: {int(total_perm)}", styles["Normal"]))
    elements.append(Paragraph(f"Total Pemenuhan: {int(total_pem)}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    table_data = [list(dataframe.columns)] + dataframe.head(20).values.tolist()
    elements.append(Table(table_data))

    doc.build(elements)
    buffer.seek(0)
    return buffer

pdf = generate_pdf(df)

st.download_button(
    "⬇️ Download Laporan PDF",
    pdf,
    file_name="laporan_monitoring_pengimputan.pdf",
    mime="application/pdf"
)

st.caption("📊 Dashboard Lanjutan | Streamlit Gratis | Auto-Hide + Side-by-Side + PDF")
