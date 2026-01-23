import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import grey

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
# 📊 DATA SOURCE (DIPISAH)
# =========================
DATA_SOURCES = [
    {
        "label": "Data 2025",
        "tahun": 2025,
        "url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQsbaP26Ljsop1EwVXWEbgXrtf_K17_tK1TlFWWepUBF_eyt8Uhpnr5ua8JaYcsCQmz-JoZbwnbI-F/pub?gid=0&single=true&output=csv"
    },
    {
        "label": "Monitoring Pengimputan Nurmala Sari, A.Md.AK",
        "tahun": 2026,
        "url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"
    },
    {
        "label": "Data 2026",
        "tahun": 2026,
        "url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=0&single=true&output=csv"
    }
]

@st.cache_data(ttl=120)
def load_all_sources(sources):
    frames = []
    for src in sources:
        df = pd.read_csv(src["url"])
        df = df.iloc[:, :10]
        df.columns = df.columns.str.strip()
        df["Tahun"] = src["tahun"]
        df["Label Tahun"] = src["label"]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

df_all = load_all_sources(DATA_SOURCES)

# =========================
# 📆 FILTER
# =========================
label_opsi = df_all["Label Tahun"].unique().tolist()
label_pilih = st.sidebar.multiselect(
    "📆 Pilih Sumber Data",
    label_opsi,
    default=label_opsi
)
df = df_all[df_all["Label Tahun"].isin(label_pilih)]

bulan_list = sorted(df["Bulan"].dropna().unique())
bulan_filter = st.sidebar.multiselect("🗓️ Bulan", bulan_list, default=bulan_list)
df = df[df["Bulan"].isin(bulan_filter)]

# =========================
# 🧠 HELPER
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
    for jenis, col in zip(["Permintaan", "Pemenuhan"], [c1, c2]):
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
                    .mark_bar()
                    .encode(
                        x=alt.X("Kategori:N", sort="-y"),
                        y="Jumlah:Q",
                        tooltip=["Kategori", "Jumlah"]
                    )
                    .properties(
                        title=f"{jenis} per {judul}",
                        height=300
                    ),
                    use_container_width=True
                )
            )

# =========================
# 🧾 HEADER DASHBOARD
# =========================
st.title("💉 Dashboard Monitoring Droping & Non Droping")
st.markdown("---")

# =========================
# 🔀 DROPING / NON DROPING
# =========================
for jp in ["Droping", "Non Droping"]:
    st.markdown(f"## 🔹 {jp}")
    df_jp = df[df["Jenis Permintaan"] == jp]

    # Trend
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
                tooltip=["Label Tahun", "Bulan", "Jumlah"]
            )
            .properties(height=350),
            use_container_width=True
        )
    )

    st.markdown("### 📊 Permintaan vs Pemenuhan")
    side_by_side(df_jp, "Komponen", "Komponen")
    side_by_side(df_jp, "Golongan Darah", "Golongan Darah")
    side_by_side(df_jp, "Rhesus", "Rhesus")
    side_by_side(df_jp, "RS/Klinik Tujuan", "RS/Klinik")

    st.markdown("### 📋 Data Lengkap")
    st.dataframe(df_jp, use_container_width=True)

# =========================
# 🧾 PDF + WATERMARK
# =========================
st.markdown("---")
st.subheader("🧾 Download Laporan PDF")

def draw_watermark(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 40)
    canvas.setFillGray(0.85)
    canvas.translate(400, 200)
    canvas.rotate(30)
    canvas.drawCentredString(0, 0, "Distribusi Bidang Pelayanan Darah")
    canvas.restoreState()

def generate_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        alignment=1
    )

    elements = []

    # ===== COVER PAGE =====
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("UNIT DONOR DARAH (UDD)", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("PMI KOTA BANDA ACEH", title_style))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        "LAPORAN DISTRIBUSI & PELAYANAN DARAH",
        styles["Heading1"]
    ))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"Tanggal Cetak: {datetime.now().strftime('%d %B %Y')}",
        styles["Normal"]
    ))

    elements.append(PageBreak())

    # ===== ISI =====
    kolom_pdf = [
        "Label Tahun", "Bulan", "Jenis Permintaan",
        "Jenis Pengimputan", "Komponen",
        "Golongan Darah", "Rhesus", "Jumlah"
    ]

    table_data = [kolom_pdf] + df[kolom_pdf].values.tolist()
    elements.append(Table(table_data, repeatRows=1))

    doc.build(
        elements,
        onFirstPage=draw_watermark,
        onLaterPages=draw_watermark
    )

    buffer.seek(0)
    return buffer

pdf_buffer = generate_pdf(df)

st.download_button(
    "⬇️ Download PDF Resmi (Landscape + Watermark)",
    pdf_buffer,
    "laporan_udd_pmi_banda_aceh.pdf",
    "application/pdf"
)

st.caption(
    "📊 Dashboard Final | UDD PMI Kota Banda Aceh | Streamlit Gratis | Siap Produksi"
)
