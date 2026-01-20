import streamlit as st
import pandas as pd
import altair as alt

# =========================
# 🎨 PAGE CONFIG
# =========================
st.set_page_config(page_title="Dashboard Droping vs Non Droping", layout="wide", page_icon="💉")
st.markdown("""
    <style>
        html, body, [class*="css"] {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        .big-font {
            font-size:26px !important;
            font-weight:700;
            color:#00c4ff;
        }
        .metric-box {
            background-color: #161b22;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            color: #e6e6e6;
            box-shadow: 0px 0px 10px rgba(0, 255, 255, 0.2);
        }
        h1, h2, h3, h4 {
            color: #58a6ff;
        }
        .stDataFrame {
            border-radius: 10px;
        }
        .css-1l269bu {
            background-color: #0e1117;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# 📊 DATA
# =========================
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9OLoy-V3cVOvhF-pgwGuMatwEUO9m8S2COzp2C9o44UbWTZG4-PEZOhqCV13GnO24yL_p1UNj5h_c/pub?gid=783347361&single=true&output=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(url)
    df = df.iloc[:, :10]
    df.columns = [col.strip() for col in df.columns]
    # Gabungkan Bulan + Tahun
    if 'Bulan' in df.columns and 'Tahun' in df.columns:
        df['Periode'] = df['Bulan'].astype(str) + " " + df['Tahun'].astype(str)
    # Ambil tanggal terakhir input (kolom Tanggal)
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
    return df

df = load_data()

# =========================
# 🧠 FILTER
# =========================
st.sidebar.header("🎛️ Filter Data")

jenis_list = df['Jenis Permintaan'].dropna().unique().tolist()
jenis_filter = st.sidebar.multiselect("Pilih Jenis Permintaan:", options=jenis_list, default=jenis_list)

if 'Jenis Pengimputan' in df.columns:
    imput_list = df['Jenis Pengimputan'].dropna().unique().tolist()
    imput_filter = st.sidebar.multiselect("Pilih Jenis Pengimputan:", options=imput_list, default=imput_list)
else:
    imput_filter = []

if 'Droping RS/Klinik Tujuan' in df.columns:
    tujuan_list = df['Droping RS/Klinik Tujuan'].dropna().unique().tolist()
    tujuan_filter = st.sidebar.multiselect("Pilih RS/Klinik Tujuan:", options=tujuan_list, default=tujuan_list)
else:
    tujuan_filter = []

# =========================
# 🧩 FILTER LOGIKA
# =========================
df_filtered = df[df['Jenis Permintaan'].isin(jenis_filter)]

if imput_filter:
    df_filtered = df_filtered[df_filtered['Jenis Pengimputan'].isin(imput_filter)]
if tujuan_filter:
    df_filtered = df_filtered[df_filtered['Droping RS/Klinik Tujuan'].isin(tujuan_filter)]

# =========================
# 🕒 TANGGAL TERAKHIR INPUT
# =========================
if 'Tanggal' in df.columns:
    last_date = df['Tanggal'].max()
    if pd.notnull(last_date):
        st.markdown(f"### 🕒 Data terakhir diinput: **{last_date.strftime('%d %B %Y')}**", unsafe_allow_html=True)

# =========================
# 📋 DATA TABEL
# =========================
st.title("💉 Dashboard Droping vs Non Droping - Dark Mode Edition")
st.markdown("#### Analisis Real-time dari Google Sheets (Kolom A:J)")
st.dataframe(df_filtered, use_container_width=True, height=400)

# =========================
# 🔢 STATISTIK UTAMA
# =========================
st.markdown("### 📈 Statistik Singkat")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric-box'><span class='big-font'>{len(df_filtered):,}</span><br>Jumlah Data</div>", unsafe_allow_html=True)
with col2:
    top_type = df_filtered['Jenis Permintaan'].value_counts().idxmax() if not df_filtered.empty else "-"
    st.markdown(f"<div class='metric-box'><span class='big-font'>{top_type}</span><br>Jenis Terbanyak</div>", unsafe_allow_html=True)
with col3:
    total_jumlah = df_filtered['Jumlah'].sum() if 'Jumlah' in df_filtered.columns else 0
    st.markdown(f"<div class='metric-box'><span class='big-font'>{int(total_jumlah):,}</span><br>Total Unit</div>", unsafe_allow_html=True)

# =========================
# 📊 VISUALISASI
# =========================
st.markdown("### 📊 Visualisasi Data")

col4, col5 = st.columns(2)
with col4:
    st.markdown("#### 🔸 Jumlah Distribusi")
    st.bar_chart(df_filtered['Jenis Permintaan'].value_counts())

with col5:
    if 'Golongan Darah' in df_filtered.columns:
        st.markdown("#### 🩸 Distribusi Golongan Darah")
        st.bar_chart(df_filtered['Golongan Darah'].value_counts())

# =========================
# 🏥 DUA CHART RS/KLINIK TUJUAN
# =========================
st.markdown("### 🏥 Analisis Berdasarkan RS/Klinik Tujuan")

if 'Droping RS/Klinik Tujuan' in df_filtered.columns:
    tujuan_counts = df_filtered['Droping RS/Klinik Tujuan'].value_counts().head(15)
    st.markdown("#### 📦 Jumlah Data per RS/Klinik Tujuan")
    st.bar_chart(tujuan_counts)

    if 'Jumlah' in df_filtered.columns:
        tujuan_sums = df_filtered.groupby('Droping RS/Klinik Tujuan')['Jumlah'].sum().nlargest(15)
        st.markdown("#### 💉 Total Unit (Jumlah) per RS/Klinik Tujuan")
        st.bar_chart(tujuan_sums)

# =========================
# 📆 TREN BULANAN PER RS/KLINIK TUJUAN
# =========================
if 'Periode' in df_filtered.columns and 'Droping RS/Klinik Tujuan' in df_filtered.columns:
    st.markdown("### 📆 Tren Bulanan per RS/Klinik Tujuan")
    df_trend_rs = (
        df_filtered.groupby(['Periode', 'Droping RS/Klinik Tujuan'])
        .size()
        .reset_index(name='Jumlah')
        .sort_values('Periode')
    )
    top_rs = df_trend_rs['Droping RS/Klinik Tujuan'].value_counts().head(8).index
    df_trend_rs = df_trend_rs[df_trend_rs['Droping RS/Klinik Tujuan'].isin(top_rs)]

    chart = (
        alt.Chart(df_trend_rs)
        .mark_line(point=True)
        .encode(
            x=alt.X('Periode:N', title="Bulan"),
            y=alt.Y('Jumlah:Q', title="Jumlah Droping"),
            color=alt.Color('Droping RS/Klinik Tujuan:N', title="RS/Klinik"),
            tooltip=['Periode', 'Droping RS/Klinik Tujuan', 'Jumlah']
        )
        .properties(width=950, height=450)
    )
    st.altair_chart(chart, use_container_width=True)

# =========================
# 🩸 PIE CHART KOMPONEN
# =========================
if 'Komponen' in df_filtered.columns:
    st.markdown("### 🧪 Komposisi Komponen Darah")
    df_pie = df_filtered['Komponen'].value_counts().reset_index()
    df_pie.columns = ['Komponen', 'Jumlah']
    pie_chart = (
        alt.Chart(df_pie)
        .mark_arc(innerRadius=60)
        .encode(
            theta='Jumlah:Q',
            color=alt.Color('Komponen:N', scale=alt.Scale(scheme='dark2')),
            tooltip=['Komponen', 'Jumlah']
        )
        .properties(width=500, height=400)
    )
    st.altair_chart(pie_chart, use_container_width=True)

# =========================
# 🧾 FOOTER
# =========================
st.markdown("---")
st.caption("📡 Auto-refresh setiap 30 detik | Dark Mode Elegan | Dibuat dengan ❤️ menggunakan Streamlit & Altair")

