import streamlit as st
import pandas as pd
import altair as alt
from io import StringIO

# =========================
# 🎨 CONFIGURASI HALAMAN
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
        .big-font {font-size:22px; font-weight:600; color:#00c4ff;}
        .metric-box {
            background-color: #161b22;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            color: #e6e6e6;
            box-shadow: 0px 0px 8px rgba(0, 255, 255, 0.2);
        }
        h1,h2,h3,h4 {color:#58a6ff;}
        .stDataFrame {border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# =========================
# 📊 AMBIL DATA
# =========================
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = [c.strip() for c in df.columns]
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
    if 'Bulan' in df.columns and 'Tahun' in df.columns:
        df['Periode'] = df['Bulan'].astype(str) + " " + df['Tahun'].astype(str)
    return df

df = load_data()

# =========================
# 🧠 FILTER UTAMA
# =========================
st.sidebar.header("🎛️ Filter Data Umum")

jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", jenis_list, default=jenis_list)

form_list = df['Jenis Pengimputan'].dropna().unique().tolist()
form_filter = st.sidebar.multiselect("Jenis Formulir:", form_list, default=form_list)

if 'Droping RS/Klinik Tujuan' in df.columns:
    rs_list = df['Droping RS/Klinik Tujuan'].dropna().unique().tolist()
    rs_filter = st.sidebar.multiselect("RS/Klinik Tujuan:", rs_list, default=rs_list)
else:
    rs_filter = []

bulan_list = df['Bulan'].dropna().unique().tolist()
bulan_filter = st.sidebar.multiselect("Bulan:", bulan_list, default=bulan_list)

# =========================
# 🏥 FILTER KHUSUS “RUMAH SAKIT FOKUS”
# =========================
st.sidebar.markdown("---")
st.sidebar.header("🏥 Filter Fokus Rumah Sakit / Klinik")
if 'Droping RS/Klinik Tujuan' in df.columns:
    rs_focus = st.sidebar.multiselect(
        "Pilih RS/Klinik Fokus:",
        options=sorted(df['Droping RS/Klinik Tujuan'].dropna().unique().tolist()),
        default=[]
    )
else:
    rs_focus = []

# =========================
# 🧩 FILTER DATA
# =========================
df_filtered = df[
    (df['Jenis Permintaan'].isin(jenis_filter)) &
    (df['Jenis Pengimputan'].isin(form_filter))
]

if rs_filter:
    df_filtered = df_filtered[df_filtered['Droping RS/Klinik Tujuan'].isin(rs_filter)]
if bulan_filter:
    df_filtered = df_filtered[df_filtered['Bulan'].isin(bulan_filter)]
if rs_focus:
    df_filtered = df_filtered[df_filtered['Droping RS/Klinik Tujuan'].isin(rs_focus)]

# =========================
# 🕒 INFO DATA TERAKHIR
# =========================
if 'Tanggal' in df.columns:
    last_date = df['Tanggal'].max()
    if pd.notnull(last_date):
        st.markdown(f"### 🕒 Data terakhir diinput: **{last_date.strftime('%d %B %Y')}**")

# =========================
# 🧾 HEADER
# =========================
st.title("💉 Dashboard Distribusi & Pelayanan Darah 2026")
st.markdown("#### Analisis Droping, Permintaan & Pemenuhan | Real-time dari Google Sheets")
st.markdown("---")

# =========================
# 📥 TOMBOL DOWNLOAD CSV
# =========================
st.subheader("📦 Download Data Terfilter")
from io import StringIO
csv_buffer = StringIO()
df_filtered.to_csv(csv_buffer, index=False)
st.download_button(
    label="⬇️ Download Data (CSV)",
    data=csv_buffer.getvalue(),
    file_name="data_terfilter.csv",
    mime="text/csv",
    help="Unduh data yang sudah difilter ke file CSV"
)

# =========================
# 📈 TREND BULANAN TOTAL
# =========================
st.subheader("📊 Trend Bulanan (Total Jumlah)")
if 'Periode' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
    df_trend = df_filtered.groupby('Periode', as_index=False)['Jumlah'].sum().sort_values('Periode')
    chart_trend = (
        alt.Chart(df_trend)
        .mark_line(point=True, color='#00c4ff')
        .encode(
            x=alt.X('Periode:N', title='Periode (Bulan)'),
            y=alt.Y('Jumlah:Q', title='Total Jumlah'),
            tooltip=['Periode', 'Jumlah']
        )
        .properties(width=950, height=350)
    )
    st.altair_chart(chart_trend, use_container_width=True)

# =========================
# 🏥 TREND MENURUT RS/KLINIK TUJUAN
# =========================
st.subheader("🏥 Trend Bulanan Menurut RS/Klinik Tujuan")
if 'Periode' in df_filtered.columns and 'Droping RS/Klinik Tujuan' in df_filtered.columns:
    df_trend_rs = (
        df_filtered.groupby(['Periode', 'Droping RS/Klinik Tujuan'], as_index=False)['Jumlah'].sum()
    )
    top_rs = df_trend_rs.groupby('Droping RS/Klinik Tujuan')['Jumlah'].sum().nlargest(10).index
    df_trend_rs = df_trend_rs[df_trend_rs['Droping RS/Klinik Tujuan'].isin(top_rs)]

    chart_trend_rs = (
        alt.Chart(df_trend_rs)
        .mark_line(point=True)
        .encode(
            x=alt.X('Periode:N', title='Bulan'),
            y=alt.Y('Jumlah:Q', title='Jumlah'),
            color=alt.Color('Droping RS/Klinik Tujuan:N', title='RS/Klinik'),
            tooltip=['Periode', 'Droping RS/Klinik Tujuan', 'Jumlah']
        )
        .properties(width=950, height=400)
    )
    st.altair_chart(chart_trend_rs, use_container_width=True)

# =========================
# 🧪 DISTRIBUSI KOMPONEN
# =========================
st.subheader("🧪 Distribusi Menurut Komponen")
if 'Komponen' in df_filtered.columns:
    df_komp = df_filtered.groupby('Komponen')['Jumlah'].sum().reset_index()
    chart_komp = (
        alt.Chart(df_komp)
        .mark_bar(color="#00FF80")
        .encode(
            x=alt.X('Komponen:N', title='Komponen'),
            y=alt.Y('Jumlah:Q', title='Jumlah'),
            tooltip=['Komponen', 'Jumlah']
        )
        .properties(width=950, height=300)
    )
    st.altair_chart(chart_komp, use_container_width=True)

# =========================
# 🏥 DISTRIBUSI MENURUT RS/KLINIK TUJUAN
# =========================
st.subheader("🏥 Distribusi Menurut RS/Klinik Tujuan (Total Jumlah)")
if 'Droping RS/Klinik Tujuan' in df_filtered.columns:
    df_dist_rs = df_filtered.groupby('Droping RS/Klinik Tujuan')['Jumlah'].sum().reset_index()
    df_dist_rs = df_dist_rs.sort_values('Jumlah', ascending=False).head(15)
    chart_dist_rs = (
        alt.Chart(df_dist_rs)
        .mark_bar(color="#33FF99")
        .encode(
            x=alt.X('Droping RS/Klinik Tujuan:N', sort='-y', title='RS/Klinik Tujuan'),
            y=alt.Y('Jumlah:Q', title='Total Jumlah'),
            tooltip=['Droping RS/Klinik Tujuan', 'Jumlah']
        )
        .properties(width=950, height=350)
    )
    st.altair_chart(chart_dist_rs, use_container_width=True)

# =========================
# ⚗️ RHESUS POSITIF/NEGATIF
# =========================
st.subheader("🩸 Negatif dan Positif per Golongan Darah")
if 'Rhesus' in df_filtered.columns and 'Golongan Darah' in df_filtered.columns:
    df_rh = df_filtered.groupby(['Golongan Darah', 'Rhesus'])['Jumlah'].sum().reset_index()
    chart_rh = (
        alt.Chart(df_rh)
        .mark_bar()
        .encode(
            x=alt.X('Golongan Darah:N', title='Golongan Darah'),
            y=alt.Y('Jumlah:Q', title='Jumlah'),
            color=alt.Color('Rhesus:N', scale=alt.Scale(scheme='redblue')),
            tooltip=['Golongan Darah', 'Rhesus', 'Jumlah']
        )
        .properties(width=950, height=300)
    )
    st.altair_chart(chart_rh, use_container_width=True)

# =========================
# 📋 TABEL & GRAFIK RS/KLINIK
# =========================
st.subheader("🏥 Tabel & Grafik RS/Klinik Tujuan (Top 20)")
if 'Droping RS/Klinik Tujuan' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
    df_rs = df_filtered.groupby('Droping RS/Klinik Tujuan')['Jumlah'].sum().reset_index()
    df_rs = df_rs.sort_values('Jumlah', ascending=False)

    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.dataframe(df_rs.head(20), use_container_width=True, height=400)
    with col2:
        chart_rs = (
            alt.Chart(df_rs.head(20))
            .mark_bar(color="#0096FF")
            .encode(
                x=alt.X('Jumlah:Q', title='Total Jumlah'),
                y=alt.Y('Droping RS/Klinik Tujuan:N', sort='-x', title='RS/Klinik'),
                tooltip=['Droping RS/Klinik Tujuan', 'Jumlah']
            )
            .properties(width=800, height=400)
        )
        st.altair_chart(chart_rs, use_container_width=True)

# =========================
# 🧾 FOOTER
# =========================
st.markdown("---")
st.caption("📡 Auto-refresh setiap 30 detik | Dark Mode Profesional | Dibuat dengan ❤️ menggunakan Streamlit & Altair")
