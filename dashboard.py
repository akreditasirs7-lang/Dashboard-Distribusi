import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import math

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
        table {
            color: white !important;
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
# 🧩 LOGIKA FILTER
# =========================
df_filtered = df.copy()
df_filtered = df_filtered[df_filtered['Jenis Permintaan'].isin(jenis_filter)]
df_filtered = df_filtered[df_filtered['Jenis Pengimputan'].isin(form_filter)]
df_filtered = df_filtered[df_filtered['RS/Klinik Tujuan'].isin(rs_filter)]
df_filtered = df_filtered[df_filtered['Bulan'].isin(bulan_filter)]

# =========================
# 🕒 INFO DATA TERAKHIR
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
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_filtered.to_excel(writer, index=False, sheet_name='Data Terfilter')
    writer.save()
excel_data = output.getvalue()

st.download_button(
    label="⬇️ Download Data (Excel)",
    data=excel_data,
    file_name="data_terfilter.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# 🧭 TOGGLE GRAFIK
# =========================
show_graphs = st.toggle("🧭 Tampilkan Semua Grafik", value=True)

# =========================
# 📊 GRAFIK-GRAFIK
# =========================
if show_graphs:
    # ---- TREND BULANAN ----
    st.subheader("📊 Trend Bulanan (Total Jumlah)")
    if 'Periode' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
        df_trend = df_filtered.groupby('Periode', as_index=False)['Jumlah'].sum().sort_values('Periode')
        if len(df_trend) > 0:
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

    # ---- DISTRIBUSI RS/KLINIK ----
    st.subheader("🏥 Distribusi Menurut RS/Klinik Tujuan (Total Jumlah)")
    if 'RS/Klinik Tujuan' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
        df_rs = df_filtered.groupby('RS/Klinik Tujuan')['Jumlah'].sum().reset_index()
        df_rs = df_rs.sort_values('Jumlah', ascending=False)
        chart_rs = (
            alt.Chart(df_rs)
            .mark_bar(color="#33FF99")
            .encode(
                x=alt.X('RS/Klinik Tujuan:N', sort='-y', title='RS/Klinik Tujuan'),
                y=alt.Y('Jumlah:Q', title='Total Jumlah'),
                tooltip=['RS/Klinik Tujuan', 'Jumlah']
            )
            .properties(width=950, height=400)
        )
        st.altair_chart(chart_rs, use_container_width=True)

    # ---- DISTRIBUSI KOMPONEN ----
    st.subheader("🧪 Distribusi Menurut Komponen")
    if 'Komponen' in df_filtered.columns:
        df_komp = df_filtered.groupby('Komponen')['Jumlah'].sum().reset_index()
        chart_komp = (
            alt.Chart(df_komp)
            .mark_bar(color="#FF7F50")
            .encode(
                x=alt.X('Komponen:N', sort='-y', title='Komponen'),
                y=alt.Y('Jumlah:Q', title='Total Jumlah'),
                tooltip=['Komponen', 'Jumlah']
            )
            .properties(width=950, height=400)
        )
        text_komp = chart_komp.mark_text(
            align='center', baseline='bottom', dy=-5, color='white'
        ).encode(text=alt.Text('Jumlah:Q'))
        st.altair_chart(chart_komp + text_komp, use_container_width=True)

    # ---- DISTRIBUSI GOLONGAN DARAH ----
    st.subheader("🩸 Distribusi Menurut Golongan Darah")
    if 'Golongan Darah' in df_filtered.columns:
        df_goldar = df_filtered.groupby('Golongan Darah')['Jumlah'].sum().reset_index()
        chart_goldar = (
            alt.Chart(df_goldar)
            .mark_bar(color="#4FC3F7")
            .encode(
                x=alt.X('Golongan Darah:N', sort='-y', title='Golongan Darah'),
                y=alt.Y('Jumlah:Q', title='Total Jumlah'),
                tooltip=['Golongan Darah', 'Jumlah']
            )
            .properties(width=950, height=400)
        )
        text_goldar = chart_goldar.mark_text(
            align='center', baseline='bottom', dy=-5, color='white'
        ).encode(text=alt.Text('Jumlah:Q'))
        st.altair_chart(chart_goldar + text_goldar, use_container_width=True)

    # ---- DISTRIBUSI RHESUS ----
    st.subheader("🧬 Distribusi Rhesus (Positif vs Negatif)")
    if 'Rhesus' in df_filtered.columns:
        df_rhesus = df_filtered.groupby('Rhesus')['Jumlah'].sum().reset_index()
        chart_rhesus = (
            alt.Chart(df_rhesus)
            .mark_bar()
            .encode(
                x=alt.X('Rhesus:N', title='Rhesus'),
                y=alt.Y('Jumlah:Q', title='Total Jumlah'),
                color=alt.Color('Rhesus:N', scale=alt.Scale(domain=['Positif', 'Negatif'], range=['#FF6B6B', '#4FC3F7'])),
                tooltip=['Rhesus', 'Jumlah']
            )
            .properties(width=950, height=400)
        )
        text_rhesus = chart_rhesus.mark_text(
            align='center', baseline='bottom', dy=-5, color='white'
        ).encode(text=alt.Text('Jumlah:Q'))
        st.altair_chart(chart_rhesus + text_rhesus, use_container_width=True)

# =========================
# 📋 DATA INPUT TERBARU
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

# =========================
# 🧾 FOOTER
# =========================
st.markdown("---")
st.caption("📡 Auto-refresh setiap 30 detik | Dark Mode Profesional | Dibuat dengan ❤️ menggunakan Streamlit & Altair")
