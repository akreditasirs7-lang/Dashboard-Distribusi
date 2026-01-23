st.markdown("---")
st.subheader("⬇️ Download Laporan Per Bulan")

# =========================
# PILIH BULAN & FORMAT
# =========================
bulan_opsi = sorted(df["Bulan"].dropna().unique())

bulan_pilih_download = st.selectbox(
    "📆 Pilih Bulan untuk Download",
    bulan_opsi
)

format_download = st.radio(
    "📄 Pilih Format File",
    ["PDF", "Excel"],
    horizontal=True
)

df_bulan = df[df["Bulan"] == bulan_pilih_download]

# =========================
# GENERATE PDF PER BULAN
# =========================
def generate_pdf_bulan(df_bulan, nama_bulan):
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

    # COVER
    elements.append(Spacer(1, 80))
    elements.append(Paragraph("UNIT DONOR DARAH (UDD)", title_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("PMI KOTA BANDA ACEH", title_style))
    elements.append(Spacer(1, 30))
    elements.append(
        Paragraph(
            f"LAPORAN DISTRIBUSI DARAH BULAN {nama_bulan.upper()}",
            styles["Heading1"]
        )
    )
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

    table_data = [kolom_pdf] + df_bulan[kolom_pdf].values.tolist()
    elements.append(Table(table_data, repeatRows=1))

    def watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 40)
        canvas.setFillGray(0.85)
        canvas.translate(400, 200)
        canvas.rotate(30)
        canvas.drawCentredString(0, 0, "Distribusi Bidang Pelayanan Darah")
        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=watermark,
        onLaterPages=watermark
    )

    buffer.seek(0)
    return buffer

# =========================
# GENERATE EXCEL PER BULAN
# =========================
def generate_excel_bulan(df_bulan):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_bulan.to_excel(
            writer,
            index=False,
            sheet_name=f"Bulan_{df_bulan['Bulan'].iloc[0]}"
        )
    buffer.seek(0)
    return buffer

# =========================
# TOMBOL DOWNLOAD
# =========================
if df_bulan.empty:
    st.warning("⚠️ Tidak ada data pada bulan ini.")
else:
    if format_download == "PDF":
        pdf_bulan = generate_pdf_bulan(df_bulan, bulan_pilih_download)
        st.download_button(
            label="⬇️ Download PDF Per Bulan",
            data=pdf_bulan,
            file_name=f"laporan_{bulan_pilih_download}_udd_pmi.pdf",
            mime="application/pdf"
        )
    else:
        excel_bulan = generate_excel_bulan(df_bulan)
        st.download_button(
            label="⬇️ Download Excel Per Bulan",
            data=excel_bulan,
            file_name=f"data_{bulan_pilih_download}_udd_pmi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
