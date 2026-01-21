def chart_with_label(data, x, y, title, color):
    # Grafik batang utama
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

    # Label angka di atas batang — selalu kelihatan
    text = (
        alt.Chart(data)
        .mark_text(
            align="center",
            baseline="middle",
            dy=-10,             # jarak vertikal di atas batang
            color="#ffffff",    # warna teks putih
            fontSize=14,
            fontWeight="bold"
        )
        .encode(
            x=alt.X(f"{x}:N", sort='-y'),
            y=alt.Y(f"{y}:Q"),
            text=alt.Text(f"{y}:Q")
        )
    )

    # Tambah interaktivitas hover biar tooltips tetap aktif
    chart = (base + text).interactive()

    return chart
