import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# =========================
# 🎨 KONFIGURASI HALAMAN
# =========================
st.set_page_config(page_title="Dashboard Distribusi Darah", layout="wide", page_icon="💉")

# =========================
# 🌙 DARK MODE STYLING
# =========================
st.markdown("""
    <style>
        html, body, [class*="css"] {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        h1,h2,h3,h4 {color:#58a6ff;}
        .sidebar-title {
            font-size: 18px;
            font-weight: 700;
            color: #9CDCFE;
        }
        table { color: white !important; }
        .toggle-box {
            background-color: #1e1e1e;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# 📊 LOAD DATA
# =========================
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = [c.strip() for c in df.columns]
    if 'Tanggal Droping' in df.columns:
        df['Tanggal Droping'] = pd.to_datetime(df['Tanggal Droping'], errors='coerce')
    if 'Bulan' in df.columns and 'Tahun' in df.columns:
        df['Periode'] = df['Bulan'].astype(str) + " " + df['Tahun'].astype(str)
    return df

df = load_data()

# =========================
# 🧠 FILTER
# =========================
st.sidebar.markdown('<p class="sidebar-title">🎛️ Filter Data</p>', unsafe_allow_html=True)

jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", jenis_list, default=jenis_list)

form_list = df['Jenis Pengimputan'].dropna().unique().tolist()
form_filter = st.sidebar.multiselect("Jenis Formulir:", form_list, default=form_list)

rs_list = sorted(df['RS/Klinik Tujuan'].dropna().unique().tolist())
select_all = st.sidebar.checkbox("Pilih Semua RS/Klinik Tujuan", value=True)
if select_all:
    rs_filter = rs_list
else:
    rs_filter = st.sidebar.multiselect("Pilih RS/Klinik Tujuan:", rs_list, default=[])

st.sidebar.markdown("---")
st.sidebar.markdown('<p class="sidebar-title">🗓️ Filter Menurut Bulan</p>', unsafe_allow_html=True)
bulan_list = sorted(df['Bulan'].dropna().unique().tolist())
bulan_filter = st.sidebar.multiselect("Pilih Bulan:", bulan_list, default=bulan_list)

# =========================
# 🧩 FILTER LOGIKA
# =========================
df_filtered = df.copy()
df_filtered = df_filtered[df_filtered['Jenis Permintaan'].isin(jenis_filter)]
df_filtered = df_filtered[df_filtered['Jenis Pengimputan'].isin(form_filter)]
df_filtered = df_filtered[df_filtered['RS/Klinik Tujuan'].isin(rs_filter)]
df_filtered = df_filtered[df_filtered['Bulan'].isin(bulan_filter)]

# =========================
# 🕒 INFO TERAKHIR
# =========================
if 'Tanggal Droping' in df.columns:
    last_date = df['Tanggal Droping'].max()
    if pd.notnull(last_date):
        st.markdown(f"### 🕒 Data terakhir diinput: **{last_date.strftime('%d %B %Y')}**")

# =========================
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Distribusi & Pelayanan Darah 2026")
st.markdown("#### Analisis Droping, Permintaan & Pemenuhan | Real-time dari Google Sheets")
st.markdown("---")

# =========================
# 📥 DOWNLOAD DATA (EXCEL)
# =========================
st.subheader("📦 Download Data Terfilter")
output = BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    df_filtered.to_excel(writer, index=False, sheet_name="Data Terfilter")

st.download_button(
    label="⬇️ Download Data (Excel)",
    data=output.getvalue(),
    file_name="data_terfilter.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# 🧭 TOGGLE GRAFIK
# =========================
st.markdown('<div class="toggle-box">', unsafe_allow_html=True)
show_graphs = st.toggle("🧭 Tampilkan Semua Grafik", value=True)
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📊 GRAFIK-GRAFIK
# =========================
if show_graphs:
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

    # Tambahkan label di atas batang
    text = (
        alt.Chart(data)
        .mark_text(
            align="center",
            baseline="bottom",
            dy=-8,            # jarak dari batang
            color="white",    # warna label
            fontSize=14,      # ukuran teks
            fontWeight="bold" # tebal biar jelas
        )
        .encode(
            x=alt.X(f"{x}:N", sort='-y'),
            y=alt.Y(f"{y}:Q"),
            text=alt.Text(f"{y}:Q")
        )
    )

    return base + text

            .mark_bar(color=color)
            .encode(
                x=alt.X(f"{x}:N", sort='-y', title=x),
                y=alt.Y(f"{y}:Q", title="Total Jumlah"),
                tooltip=[x, y],
            )
            .properties(width=950, height=400, title=title)
        )
        text = chart.mark_text(align="center", baseline="bottom", dy=-5, color="white").encode(
            text=alt.Text(f"{y}:Q")
        )
        return chart + text

    # Grafik utama
    charts = []
    if 'Periode' in df_filtered.columns:
        df_trend = df_filtered.groupby('Periode', as_index=False)['Jumlah'].sum().sort_values('Periode')
        charts.append(("Trend Bulanan", chart_with_label(df_trend, 'Periode', 'Jumlah', "📊 Trend Bulanan", "#00c4ff")))

    if 'RS/Klinik Tujuan' in df_filtered.columns:
        df_rs = df_filtered.groupby('RS/Klinik Tujuan')['Jumlah'].sum().reset_index()
        df_rs = df_rs.sort_values('Jumlah', ascending=False)
        charts.append(("RS/Klinik Tujuan", chart_with_label(df_rs, 'RS/Klinik Tujuan', 'Jumlah', "🏥 Distribusi RS/Klinik", "#33FF99")))

    if 'Komponen' in df_filtered.columns:
        df_komp = df_filtered.groupby('Komponen')['Jumlah'].sum().reset_index()
        charts.append(("Komponen", chart_with_label(df_komp, 'Komponen', 'Jumlah', "🧪 Distribusi Komponen", "#FF7F50")))

    if 'Golongan Darah' in df_filtered.columns:
        df_goldar = df_filtered.groupby('Golongan Darah')['Jumlah'].sum().reset_index()
        charts.append(("Golongan Darah", chart_with_label(df_goldar, 'Golongan Darah', 'Jumlah', "🩸 Golongan Darah", "#4FC3F7")))

    if 'Rhesus' in df_filtered.columns:
        df_rhesus = df_filtered.groupby('Rhesus')['Jumlah'].sum().reset_index()
        charts.append(("Rhesus", chart_with_label(df_rhesus, 'Rhesus', 'Jumlah', "🧬 Rhesus", "#FF6B6B")))

    for title, chart in charts:
        st.altair_chart(chart, use_container_width=True)

# =========================
# 📤 EXPORT SEMUA GRAFIK KE PDF
# =========================
st.subheader("📤 Export Semua Grafik ke PDF")

if st.button("📄 Buat Laporan PDF"):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, 27*cm, "Laporan Dashboard Distribusi Darah 2026")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, 26.4*cm, f"Total Data: {len(df_filtered)} baris")
    c.drawString(2*cm, 26.0*cm, f"Terakhir Diperbarui: {pd.Timestamp.now().strftime('%d %B %Y, %H:%M')}")

    y = 25*cm
    for name, df_part in [("RS/Klinik Tujuan", df_filtered['RS/Klinik Tujuan'].value_counts().head(5)),
                          ("Komponen", df_filtered['Komponen'].value_counts().head(5)),
                          ("Golongan Darah", df_filtered['Golongan Darah'].value_counts().head(5)),
                          ("Rhesus", df_filtered['Rhesus'].value_counts().head(5))]:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, f"{name}")
        y -= 0.5*cm
        c.setFont("Helvetica", 10)
        for item, val in df_part.items():
            c.drawString(2.5*cm, y, f"• {item}: {val}")
            y -= 0.4*cm
        y -= 0.5*cm
        if y < 4*cm:
            c.showPage()
            y = 26*cm
    c.save()

    st.download_button(
        label="📥 Download Laporan PDF",
        data=pdf_buffer.getvalue(),
        file_name="Laporan_Dashboard_Darah.pdf",
        mime="application/pdf"
    )

# =========================
# 📋 DATA TABLE
# =========================
st.subheader("📋 Data Input Terbaru (10 Baris per Halaman)")
page_size = 10
total_rows = len(df_filtered)
total_pages = math.ceil(total_rows / page_size)

if "page_number" not in st.session_state:
    st.session_state.page_number = 1

col_prev, col_next = st.columns([1, 1])
with col_prev:
    if st.button("⬅️ Previous"):
        if st.session_state.page_number > 1:
            st.session_state.page_number -= 1
with col_next:
    if st.button("Next ➡️"):
        if st.session_state.page_number < total_pages:
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
st.caption("📡 Auto-refresh setiap 30 detik | Dark Mode Profesional | Dibuat dengan ❤️ menggunakan Streamlit & Altair")

