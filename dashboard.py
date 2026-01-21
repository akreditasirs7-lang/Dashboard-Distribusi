import streamlit as st
import pandas as pd
import altair as alt

# =========================
# 🎨 CONFIGURASI HALAMAN
# =========================
st.set_page_config(page_title="Dashboard Distribusi Darah", layout="wide", page_icon="💉")

# =========================
# 🌙 DARK MODE STYLING ELEGAN
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
# 🧠 FILTER BAR
# =========================
st.sidebar.header("🎛️ Filter Data")

# Jenis Distribusi
jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Jenis Distribusi:", jenis_list, default=jenis_list)

# Jenis Formulir
form_list = df['Jenis Pengimputan'].dropna().unique().tolist()
form_filter = st.sidebar.multiselect("Jenis Formulir:", form_list, default=form_list)

# RS/Klinik
if 'Droping RS/Klinik Tujuan' in df.columns:
    rs_list = df['Droping RS/Klinik Tujuan'].dropna().unique().tolist()
    rs_filter = st.sidebar.multiselect("RS/Klinik Tujuan:", rs_list, default=rs_list)
else:
    rs_filter = []

# Bulan
bulan_list = df['Bulan'].dropna().unique().tolist()
bulan_filter = st.sidebar.multiselect("Bulan:", bulan_list, default=bulan_list)

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

# =========================
# 🕒 INFORMASI DATA
# =========================
if 'Tanggal' in df.columns:
    last_date = df['Tanggal'].max()
    if pd.notnull(last_date):
        st.markdown(f"### 🕒 Data terakhir diinput: **{last_date.strftime('%d %B %Y')}**")

# =========================
# 🧾 JUDUL UTAMA
# =========================
st.title("💉 Dashboard Distribusi & Pelayanan Darah 2026")
st.markdown("#### Analisis Data Droping, Permintaan, dan Pemenuhan secara Real-Time dari Google Sheets")
st.markdown("---")

# =========================
# 📈 TREND BULANAN (SUM OF JUMLAH)
# =========================
st.subheader("📊 Trend Bulanan (SUM of Jumlah)")
if 'Bulan' in df_filtered.columns and 'Jumlah' in df_filtered.columns:
    df_trend = (
        df_filtered.groupby(['Periode'], as_index=False)['Jumlah'].sum()
        .sort_values('Periode')
    )
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
# 🧪 DISTRIBUSI KOMPONEN (WB, TC, PRC, DLL)
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
# ⚗️ POSITIF vs NEGATIF
# =========================
st.subheader("🩸 Negatif dan Positif per Golongan Darah")
if 'Rhesus' in df_filtered.columns and 'Golongan Darah' in df_filtered.columns:
    df_rh = df_filtered.groupby(['Golongan Darah', 'Rhesus'])['Jumlah'].sum().reset_index()
    chart_rh = (
        alt.Chart(df_rh)
        .mark_bar()
        .encode(
            x=alt.X('Golongan Darah:N'),
            y=alt.Y('Jumlah:Q'),
            color=alt.Color('Rhesus:N', scale=alt.Scale(scheme='redblue')),
            tooltip=['Golongan Darah', 'Rhesus', 'Jumlah']
        )
        .properties(width=950, height=300)
    )
    st.altair_chart(chart_rh, use_container_width=True)

# =========================
# 🏥 TABEL & GRAFIK RS/KLINIK TUJUAN
# =========================
st.subheader("🏥 Distribusi Berdasarkan RS/Klinik Tujuan")

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
