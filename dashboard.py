import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape

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
# 📆 FILTER TAHUN (LABEL)
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
# 🎛️ FILTER BULAN
# =========================
bulan_list = sorted(df["Bulan"].dropna().unique())
bulan_filter = st.sidebar.multiselect("🗓️ Bulan", bulan_list, default=bulan_list)
df = df[df["Bulan"].isin(bulan_filter)]

# =========================
# 🧠 HELPER AUTO-HIDE
# =========================
def safe_chart(data, fn):
    if data.empty:
        st.info("ℹ️ Tidak ada data sesuai filter")
    else:
        fn()

# =========================
# 📊 SIDE-BY-SIDE
# =========================
def side_by_side(df_src, kolom, judul):
    c1, c2 = st.columns(2)
    for jenis, col, warna in zip(
        ["Permintaan", "Pemenuhan"],
        [c1, c2],
        ["#ff5f6d", "#36cfc9"]
    ):
        with col:
            data = (
                df_src[df_src["Jenis Pengimputan"] == jenis]
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
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Monitoring Droping & Non Droping")
st.markdown("---")

# =========================
# 🔀 DROPING & NON DROPING
# =========================
for jp in ["Droping", "Non Droping"]:

    st.markdown(f"## 🔹 {jp}")

    df_jp = df[df["Jenis Permintaan"] == jp]

    # ===== TREND =====
    st.markdown("### 📈 Trend Bulanan")

    trend = (
        df_jp.groupby(
            ["Label Tahun", "Bulan", "Jenis Pengimputan"],
            as_index=False
        )["Jumlah"].sum()
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

    # ===== SIDE BY SIDE =====
    st.markdown("### 📊 Permintaan vs Pemenuhan")

    st.markdown("#### 🧪 Komponen")
    side_by_side(df_jp, "Komponen", "Komponen")

    st.markdown("#### 🩸 Golongan Darah")
    side_by_side(df_jp, "Golongan Darah", "Golongan Darah")

    st.markdown("#### 🧬 Rhesus")
    side_by_side(df_jp, "Rhesus", "Rhesus")

    st.markdown("#### 🏥 RS / Klinik Tujuan")
    side_by_side(df_jp, "RS/Klinik Tujuan", "RS/Klinik")

    # ===== TABEL LENGKAP =====
    st.markdown("### 📋 Data Lengkap")
    st.dataframe(df_jp, use_container_width=True)

# =========================
# 🧾 DOWNLOAD SECTION
# =========================
st.markdown("---")
st.subheader("🧾 Download Laporan")

# ===== PDF LANDSCAPE =====
def generate_pdf_landscape(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("LAPORAN MONITORING DROPING & NON DROPING", styles["Title"])
    )
    elements.append(Spacer(1, 12))

    for jp in ["Droping", "Non Droping"]:
        sub = df[df["Jenis Permintaan"] == jp]
        total = sub["Jumlah"].sum()
        elements.append(
            Paragraph(f"{jp} - Total Jumlah: {int(total)}", styles["Normal"])
        )

    elements.append(Spacer(1, 12))

    kolom_pdf = [
        "Label Tahun", "Bulan", "Jenis Permintaan",
        "Jenis Pengimputan", "Komponen",
        "Golongan Darah", "Rhesus", "Jumlah"
    ]

    data_pdf = df[kolom_pdf].copy()
    table_data = [data_pdf.columns.tolist()] + data_pdf.values.tolist()

    table = Table(table_data, repeatRows=1)
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

pdf_buffer = generate_pdf_landscape(df)

st.download_button(
    "⬇️ Download PDF (Landscape)",
    pdf_buffer,
    "laporan_monitoring_landscape.pdf",
    "application/pdf"
)

# ===== EXCEL DATA LENGKAP =====
excel_all = BytesIO()
with pd.ExcelWriter(excel_all, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Data Lengkap")

st.download_button(
    "⬇️ Download Excel (Data Lengkap)",
    excel_all.getvalue(),
    "data_monitoring_lengkap.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ===== EXCEL TERPISAH =====
excel_split = BytesIO()
with pd.ExcelWriter(excel_split, engine="xlsxwriter") as writer:
    df[df["Jenis Permintaan"] == "Droping"].to_excel(
        writer, index=False, sheet_name="Droping"
    )
    df[df["Jenis Permintaan"] == "Non Droping"].to_excel(
        writer, index=False, sheet_name="Non Droping"
    )

st.download_button(
    "⬇️ Download Excel (Droping & Non Droping)",
    excel_split.getvalue(),
    "data_monitoring_droping_non_droping.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("📊 Dashboard Final | Streamlit Gratis | Stabil & Siap Laporan")
