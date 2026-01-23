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
# 📆 FILTER SIDEBAR
# =========================
label_opsi = df_all["Label Tahun"].unique().tolist()
label_pilih = st.sidebar.multiselect(
    "📆 Pilih Sumber Data",
    label_opsi,
    default=label_opsi
)
df = df_all[df_all["Label Tahun"].isin(label_pilih)]

bulan_opsi = sorted(df["Bulan"].dropna().unique())
bulan_filter = st.sidebar.multiselect(
    "🗓️ Pilih Bulan (Tampilan)",
    bulan_opsi,
    default=bulan_opsi
)
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
# 📊 SIDE BY SIDE
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
# 🔀 DROPING / NON DROPING
# =========================
for jp in ["Droping", "Non Droping"]:
    st.markdown(f"## 🔹 {jp}")
    df_jp = df[df["Jenis Permintaan"] == jp]

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
# 🧾 GENERATE PDF (FULL / BULAN)
# =========================
def watermark(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 40)
    canvas.setFillGray(0.85)
    canvas.translate(400, 200)
    canvas.rotate(30)
    canvas.drawCentredString(0, 0, "Distribusi Bidang Pelayanan Darah")
    canvas.restoreState()

def generate_pdf(df, judul):
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
        "CoverTitle", parent=styles["Title"], alignment=1
    )

    elements = []
    elements.append(Spacer(1, 80))
    elements.append(Paragraph("UNIT DONOR DARAH (UDD)", title_style))
    elements.append(Paragraph("PMI KOTA BANDA ACEH", title_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(judul, styles["Heading1"]))
    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            f"Tanggal Cetak: {datetime.now().strftime('%d %B %Y')}",
            styles["Normal"]
        )
    )
    elements.append(PageBreak())

    kolom_pdf = [
        "Label Tahun", "Bulan", "Jenis Permintaan",
        "Jenis Pengimputan", "Komponen",
        "Golongan Darah", "Rhesus", "Jumlah"
    ]

    table_data = [kolom_pdf] + df[kolom_pdf].values.tolist()
    elements.append(Table(table_data, repeatRows=1))

    doc.build(elements, onFirstPage=watermark, onLaterPages=watermark)
    buffer.seek(0)
    return buffer

# =========================
# 🧾 DOWNLOAD FULL
# =========================
st.markdown("---")
st.subheader("⬇️ Download Laporan Lengkap")

pdf_full = generate_pdf(df, "LAPORAN DISTRIBUSI & PELAYANAN DARAH")

st.download_button(
    "⬇️ Download PDF Lengkap (Landscape)",
    pdf_full,
    "laporan_udd_pmi_banda_aceh.pdf",
    "application/pdf"
)

excel_full = BytesIO()
with pd.ExcelWriter(excel_full, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Data Lengkap")

st.download_button(
    "⬇️ Download Excel Lengkap",
    excel_full.getvalue(),
    "data_monitoring_lengkap.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# 🧾 DOWNLOAD PER BULAN
# =========================
st.markdown("---")
st.subheader("⬇️ Download Laporan Per Bulan")

bulan_pilih = st.selectbox("📆 Pilih Bulan", bulan_opsi)
format_file = st.radio("📄 Format File", ["PDF", "Excel"], horizontal=True)

df_bulan = df[df["Bulan"] == bulan_pilih]

if df_bulan.empty:
    st.warning("⚠️ Tidak ada data pada bulan ini.")
else:
    if format_file == "PDF":
        pdf_bulan = generate_pdf(
            df_bulan, f"LAPORAN BULAN {bulan_pilih.upper()}"
        )
        st.download_button(
            "⬇️ Download PDF Per Bulan",
            pdf_bulan,
            f"laporan_{bulan_pilih}_udd_pmi.pdf",
            "application/pdf"
        )
    else:
        excel_bulan = BytesIO()
        with pd.ExcelWriter(excel_bulan, engine="xlsxwriter") as writer:
            df_bulan.to_excel(writer, index=False, sheet_name=f"Bulan_{bulan_pilih}")
        st.download_button(
            "⬇️ Download Excel Per Bulan",
            excel_bulan.getvalue(),
            f"data_{bulan_pilih}_udd_pmi.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.caption(
    "📊 Dashboard Final | UDD PMI Kota Banda Aceh | Streamlit Gratis | Stabil"
)
