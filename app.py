from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.graph_objs as go

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    try:
        df = pd.read_excel('data/dgkdetay.xlsx')
        df_tk = pd.read_excel('data/tkdetay.xlsx')
        df_dgk_sporcu = pd.read_excel('data/dgksporcu.xlsx')
    except Exception as e:
        return f"Dosyalar okunurken hata oluştu: {e}"

    klasmanlar = sorted(df['Klasman'].dropna().unique().tolist())
    klasmanlar.insert(0, 'Hepsi')

    secili_klasman = request.args.get('klasman', 'Hepsi')
    secili_sporcu = request.args.get('sporcu')

    if secili_klasman != 'Hepsi':
        df = df[df['Klasman'] == secili_klasman]

    sporcular = sorted(df['Sporcu'].dropna().unique().tolist())
    if not secili_sporcu and sporcular:
        secili_sporcu = sporcular[0]

    # Ortak içerik üretimi
    grafik_1, grafik_2, tablo_html, dgk_sira, tk_sira, dgk_tablo, tk_tablo = generate_content(
        df, df_tk, df_dgk_sporcu, secili_sporcu
    )

    return render_template(
        'index.html',
        klasmanlar=klasmanlar,
        secili_klasman=secili_klasman,
        sporcular=sporcular,
        secili_sporcu=secili_sporcu,
        grafik_1=grafik_1,
        grafik_2=grafik_2,
        tablo=tablo_html,
        dgk_sira=dgk_sira,
        tk_sira=tk_sira,
        dgk_tablo=dgk_tablo,
        tk_tablo=tk_tablo
    )

@app.route('/guncelle', methods=['POST'])
def guncelle():
    secili_klasman = request.form.get('klasman', 'Hepsi')
    secili_sporcu = request.form.get('sporcu')

    try:
        df = pd.read_excel('data/dgkdetay.xlsx')
        df_tk = pd.read_excel('data/tkdetay.xlsx')
        df_dgk_sporcu = pd.read_excel('data/dgksporcu.xlsx')
    except Exception as e:
        return jsonify({'error': f"Veri okunamadı: {e}"}), 500

    if secili_klasman != 'Hepsi':
        df = df[df['Klasman'] == secili_klasman]

    sporcular = sorted(df['Sporcu'].dropna().unique().tolist())
    if not secili_sporcu and sporcular:
        secili_sporcu = sporcular[0]

    grafik_1, grafik_2, tablo_html, dgk_sira, tk_sira, dgk_tablo, tk_tablo = generate_content(
        df, df_tk, df_dgk_sporcu, secili_sporcu
    )

    # İçerik parçacığını render et
    icerik_html = render_template(
        'parca_icerik.html',
        grafik_1=grafik_1,
        grafik_2=grafik_2,
        tablo=tablo_html,
        dgk_sira=dgk_sira,
        tk_sira=tk_sira,
        dgk_tablo=dgk_tablo,
        tk_tablo=tk_tablo
    )

    return jsonify({
        'icerik_html': icerik_html,
        'sporcular': sporcular,
        'secili_sporcu': secili_sporcu
    })

def generate_content(df, df_tk, df_dgk_sporcu, secili_sporcu):
    grafik_1 = grafik_2 = ""
    tablo_html = ""
    dgk_sira = "Yok"
    tk_sira = "Yok"
    dgk_tablo = tk_tablo = ""

    if secili_sporcu:
        df_sporcu = df[df['Sporcu'] == secili_sporcu].copy()
        for col in ['Genel Ortalama', 'Etap Puanı', 'En Yüksek Seri 1', 'En Yüksek Ortalama']:
            df_sporcu[col] = pd.to_numeric(df_sporcu[col], errors='coerce')

        if not df_sporcu.empty:
            klasman = df_sporcu['Klasman'].iloc[0]
            if klasman != "A Kategori" and 'DGK Sıra' in df_sporcu.columns:
                dgk_sira = df_sporcu['DGK Sıra'].iloc[0]

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df_sporcu['Turnuva'],
            y=df_sporcu['Genel Ortalama'],
            mode='lines+markers',
            name='Genel Ortalama'
        ))
        fig1.update_layout(
            title='Genel Ortalama Gelişimi',
            xaxis_title='Turnuva',
            yaxis_title='Genel Ortalama',
            xaxis=dict(
                tickfont=dict(size=9),
                tickangle=-90,
                automargin=True,
                tickmode='array',
                tickvals=df_sporcu['Turnuva'],
                ticktext=df_sporcu['Turnuva'],
            ),
            yaxis=dict(tickfont=dict(size=9)),
            autosize=False,
            width=900,
            margin=dict(l=60, r=20, t=50, b=150),
            height=300
        )
        grafik_1 = fig1.to_html(full_html=False)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_sporcu['Turnuva'],
            y=df_sporcu['En Yüksek Ortalama'],
            mode='lines+markers',
            name='En Yüksek Ortalama',
            line=dict(color='orange')
        ))
        fig2.update_layout(
            title='En Yüksek Ortalama Gelişimi',
            xaxis_title='Turnuva',
            yaxis_title='EYO',
            xaxis=dict(tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            autosize=True,
            margin=dict(l=60, r=20, t=50, b=40),
            height=300
        )
        grafik_2 = fig2.to_html(full_html=False)

        tablo_kolonlari = ['Turnuva', 'Etap Puanı', 'Toplam Sayı', 'Toplam El', 'Genel Ortalama',
                           'En Yüksek Seri 1', 'En Yüksek Seri 2', 'DGK Sıra']
        df_tablo = df_sporcu[tablo_kolonlari].copy().fillna('')
        tablo_html = df_tablo.to_html(classes='table table-striped table-bordered', index=False, border=0)

        df_dgk_filtered = df_dgk_sporcu[df_dgk_sporcu['Sporcu'] == secili_sporcu].copy()
        if not df_dgk_filtered.empty:
            for col in ['Etap Puanı', 'Toplam Sayı', 'Toplam El', 'En Yüksek Seri 1', 'En Yüksek Seri 2', 'En Yüksek Ortalama']:
                df_dgk_filtered[col] = pd.to_numeric(df_dgk_filtered[col], errors='coerce')

            kolonlar = ['Turnuva', 'Etap Puanı', 'Toplam Sayı', 'Toplam El',
                        'Genel Ortalama', 'En Yüksek Seri 1', 'En Yüksek Seri 2', 'En Yüksek Ortalama']
            df_dgk_filtered = df_dgk_filtered[kolonlar].fillna('')
            dgk_tablo = df_dgk_filtered.to_html(classes='table table-bordered table-sm', index=False, border=0)

        tk_sira_row = df_tk[df_tk['Sporcu'] == secili_sporcu]
        if not tk_sira_row.empty:
            tk_sira = tk_sira_row['TK Sıra'].iloc[0]
            tk_cols = [col for col in tk_sira_row.columns if col != 'Sporcu']
            df_tk_tablo = tk_sira_row[tk_cols].fillna('')
            tk_tablo = df_tk_tablo.to_html(classes='table table-bordered table-sm', index=False, border=0)
        else:
            tk_tablo = "<p>Detay bulunamadı.</p>"

    return grafik_1, grafik_2, tablo_html, dgk_sira, tk_sira, dgk_tablo, tk_tablo

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
