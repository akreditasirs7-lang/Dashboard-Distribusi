import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

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
# 📆 FILTER LABEL TAHUN
# =========================
label_opsi = df_all["Label Tahun"].unique().tolist()

label_pilih = st.sidebar.multiselect(
    "📆 Pilih Sumber Data",
    label_opsi,
    default=label_opsi
)

df = df_all[df_all["Label Tahun"].isin(label_pilih)]

# =========================
# 🎛️ FILTER BULAN
# =========================
bulan_list = sorted(df["Bulan"].dropna().unique())
bulan_filter = st.sidebar.multiselect("🗓️ Bulan", bulan_list, default=bulan_list)
df = df[df["Bulan"].isin(bulan_filter)]

# =========================
# 🧠 AUTO-HIDE
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

    st.markdown("### 📋 Data Lengkap")
    st.dataframe(df_jp, use_container_width=True)

# =========================
# 🧾 DOWNLOAD (PDF + EXCEL)
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

    for label in df["Label Tahun"].unique():
        sub = df[df["Label Tahun"] == label]
        elements.append(
            Paragraph(f"{label} - Total Jumlah: {int(sub['Jumlah'].sum())}", styles["Normal"])
        )

    elements.append(Spacer(1, 12))

    kolom_pdf = [
        "Label Tahun", "Bulan", "Jenis Permintaan",
        "Jenis Pengimputan", "Komponen",
        "Golongan Darah", "Rhesus", "Jumlah"
    ]

    table_data = [kolom_pdf] + df[kolom_pdf].values.tolist()
    elements.append(Table(table_data, repeatRows=1))

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

# ===== EXCEL =====
excel_all = BytesIO()
with pd.ExcelWriter(excel_all, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Data Lengkap")

st.download_button(
    "⬇️ Download Excel (Data Lengkap)",
    excel_all.getvalue(),
    "data_monitoring_lengkap.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption("📊 Dashboard Final | PDF Landscape Aktif | Streamlit Gratis")
