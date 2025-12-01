import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import time

# --- AYARLAR ---

# 1.API Anahtarını Streamlit'in gizli kasasından çekiyoruz.
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("HATA: API Anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını yapın.")
    st.stop()

# 2. SAYFA YAPISI (Genişletilmiş Layout)
st.set_page_config(
    page_title="Maarif Asistanı",
    page_icon="🎓",
    layout="wide" 
)

# 3. TÜRKÇE KARAKTER DESTEKLİ PDF FONKSİYONU
def create_pdf(text, title="Sinav Kagidi"):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'MAARIF ASISTANI - SINAV KAGIDI', 0, 1, 'C')
            self.ln(10)
    
    pdf = PDF()
    pdf.add_page()
    
    # Türkçe karakter sorunu olmaması için font ayarı (Arial kullanıyoruz)
    # Not: FPDF'in standart fontu Türkçe karakterleri tam desteklemeyebilir.
    # Bu yüzden karakterleri latin alfabesine çeviren bir düzeltme yapıyoruz.
    # İleride özel font dosyası yükleyerek bunu tam çözebiliriz.
    def tr_duzelt(metin):
        dic = {'ğ':'g', 'Ğ':'G', 'ş':'s', 'Ş':'S', 'ı':'i', 'İ':'I', 'ç':'c', 'Ç':'C', 'ü':'u', 'Ü':'U', 'ö':'o', 'Ö':'O'}
        for k, v in dic.items():
            metin = metin.replace(k, v)
        return metin

    pdf.set_font("Arial", size=12)
    
    # Satır satır yazma
    for line in text.split('\n'):
        # Karakterleri PDF uyumlu hale getir
        clean_line = tr_duzelt(line)
        pdf.multi_cell(0, 10, clean_line)
        
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# 4. YAPAY ZEKA AYARLARI
try:
    if "GOOGLE_API_KEY" in st.secrets:
        API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API Hatası: {e}")

# --- ARAYÜZ (GOOGLE TARZI TASARIM) ---

# Üst Boşluk (Logoyu ortaya itmek için)
st.write(" ")
st.write(" ")

# ORTA SÜTUNU OLUŞTURUYORUZ (Her şey ortada dursun)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # LOGO
    st.image("https://images.unsplash.com/photo-1546410531-bb4caa6b424d?q=80&w=2071&auto=format&fit=crop", caption="Maarif Asistanı", use_container_width=True)
    st.markdown("<h1 style='text-align: center; color: #333;'>Maarif Asistanı</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Yapay Zeka Destekli Sınav Hazırlama Motoru</p>", unsafe_allow_html=True)

    # AYARLAR (Açılır Kapanır Kutu - Expander)
    with st.expander("⚙️ Sınav Ayarlarını Yapılandır (Tıkla)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            seviye = st.selectbox("Sınıf Seviyesi:", ("İlkokul (1-4)", "Ortaokul (5-8)", "Lise (9-12)", "Üniversite Hazırlık"))
        with c2:
            zorluk = st.slider("Zorluk:", 1, 5, 3)
        with c3:
            soru_sayisi = st.number_input("Soru Sayısı:", 1, 20, 5)

    # ARAMA ÇUBUĞU VE BUTON (Google Gibi)
    konu = st.text_input("", placeholder="Hangi konuda sınav hazırlamak istersin? (Örn: Kuvvet ve Hareket, Python Listeler)")
    
    # Butonu Ortalamak İçin
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        generate_btn = st.button("✨ Sınavı Oluştur", type="primary", use_container_width=True)

# --- İŞLEM BÖLÜMÜ ---
if generate_btn:
    if not konu:
        st.warning("Lütfen bir konu yazın.")
    else:
        with st.spinner('Yapay Zeka soruları kurguluyor...'):
            try:
                # Prompt (Cevap anahtarını ayırmak için özel işaret ekledik)
                prompt = f"""
                Sen MEB müfredatına hakim uzman bir öğretmensin.
                Konu: {konu}, Seviye: {seviye}, Zorluk: {zorluk}/5, Soru Sayısı: {soru_sayisi}.
                
                GÖREV:
                1. Soruları hazırla.
                2. Şıkları (A,B,C,D) net yaz.
                3. Kod soruları varsa zihninde sağlama yap.
                4. EN SONA, sorular bittikten sonra tam olarak şu ayırıcıyı koy: "---CEVAP_ANAHTARI_BOLUMU---"
                5. Bu ayırıcıdan sonra cevap anahtarını yaz.
                
                Çıktı Formatı:
                Soru 1: ...
                ...
                ---CEVAP_ANAHTARI_BOLUMU---
                1-A
                2-C
                ...
                """
                
                response = model.generate_content(prompt)
                full_text = response.text
                
                # METNİ PARÇALA (Sorular ve Cevaplar)
                if "---CEVAP_ANAHTARI_BOLUMU---" in full_text:
                    parts = full_text.split("---CEVAP_ANAHTARI_BOLUMU---")
                    sorular_kismi = parts[0].strip()
                    cevaplar_kismi = parts[1].strip()
                else:
                    sorular_kismi = full_text
                    cevaplar_kismi = "Cevap anahtarı ayrıştırılamadı."

                # EKRANA BAS
                st.success("Sınav Hazır!")
                st.write(sorular_kismi)
                with st.expander("Cevap Anahtarını Gör"):
                    st.write(cevaplar_kismi)
                
                # PDF OLUŞTURMA (İki seçenek)
                pdf_sorular = create_pdf(sorular_kismi, title=f"{konu} - Sorular")
                pdf_tam = create_pdf(full_text.replace("---CEVAP_ANAHTARI_BOLUMU---", "\n\nCEVAP ANAHTARI\n----------------"), title=f"{konu} - Tam")

                # BUTONLAR
                col_pdf1, col_pdf2 = st.columns(2)
                with col_pdf1:
                    st.download_button(
                        label="📄 Sadece Soruları İndir (PDF)",
                        data=pdf_sorular,
                        file_name=f"{konu}_sorular.pdf",
                        mime="application/pdf"
                    )
                with col_pdf2:
                    st.download_button(
                        label="📑 Cevap Anahtarlı İndir (PDF)",
                        data=pdf_tam,
                        file_name=f"{konu}_tam.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Hata: {e}")
