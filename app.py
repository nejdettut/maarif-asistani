import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# --- AYARLAR ---
st.set_page_config(
    page_title="Maarif Asistanı",
    page_icon="🎓",
    layout="wide"
)

# --- PDF MOTORU ---
def create_pdf(text, title="Sinav Kagidi"):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'MAARIF ASISTANI - SINAV KAGIDI', 0, 1, 'C')
            self.ln(10)
    
    pdf = PDF()
    pdf.add_page()
    
    def tr_duzelt(metin):
        dic = {'ğ':'g', 'Ğ':'G', 'ş':'s', 'Ş':'S', 'ı':'i', 'İ':'I', 'ç':'c', 'Ç':'C', 'ü':'u', 'Ü':'U', 'ö':'o', 'Ö':'O'}
        for k, v in dic.items():
            metin = metin.replace(k, v)
        return metin

    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        clean_line = tr_duzelt(line)
        pdf.multi_cell(0, 10, clean_line)
        
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- GÜVENLİK VE API ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("HATA: API Anahtarı bulunamadı! Lütfen Secrets ayarlarını yapın.")
    st.stop()

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API Hatası: {e}")

# --- ARAYÜZ TASARIMI (VİTRİN) ---
st.write(" ")

# Sayfayı 3 sütuna bölüyoruz, orta sütun daha geniş (Görsel ve Başlık burada olacak)
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    # 1. GÖRSEL (Banner)
    st.image("https://images.unsplash.com/photo-1501504905252-473c47e087f8?q=80&w=1974&auto=format&fit=crop", use_container_width=True)
    
    # 2. BÜYÜK BAŞLIK
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; color: #1E3A8A;'>MAARİF ASİSTANI</h1>", unsafe_allow_html=True)
    
    # 3. İSİM VE UNVAN (Senin İmzan)
    st.markdown("<h3 style='text-align: center; color: #555;'>Nejdet Tut</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #888;'>EdTech Developer & Python Instructor</p>", unsafe_allow_html=True)
    
    st.write("---") # Ayırıcı Çizgi

    # --- AYARLAR KUTUSU ---
    with st.expander("⚙️ Sınav Ayarlarını Yapılandır (Tıkla)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            soru_tipi = st.selectbox(
                "Soru Tipi Seçin:",
                ("Çoktan Seçmeli (Test)", "Doğru / Yanlış", "Boşluk Doldurma", "Klasik (Açık Uçlu)", "Eşleştirme")
            )
            seviye = st.selectbox("Sınıf Seviyesi:", ("İlkokul (1-4)", "Ortaokul (5-8)", "Lise (9-12)", "Üniversite"))
        with c2:
            zorluk = st.slider("Zorluk:", 1, 5, 3)
            soru_sayisi = st.number_input("Soru Sayısı:", 1, 20, 5)

    # ARAMA VE BUTON
    konu = st.text_input("", placeholder="Hangi konuda sınav hazırlamak istersin? (Örn: Kuvvet ve Hareket, Python Döngüler)")
    
    # Butonu ortalamak için küçük sütunlar
    b1, b2, b3 = st.columns([1, 2, 1])
    with b2:
        generate_btn = st.button("✨ Soruları Oluştur", type="primary", use_container_width=True)

# --- İŞ MANTIĞI (BACKEND) ---
if generate_btn:
    if not konu:
        st.warning("Lütfen bir konu yazın.")
    else:
        with st.spinner(f'{soru_tipi} hazırlanıyor...'):
            try:
                # Prompt Kurgusu
                base_instruction = f"Sen uzman bir öğretmensin. Konu: {konu}, Seviye: {seviye}, Zorluk: {zorluk}/5, Adet: {soru_sayisi}."
                
                if soru_tipi == "Çoktan Seçmeli (Test)":
                    type_instruction = "GÖREV: Çoktan seçmeli sorular hazırla (A,B,C,D). Kod veya matematik sorusuysa sağlama yap."
                elif soru_tipi == "Doğru / Yanlış":
                    type_instruction = "GÖREV: Doğru/Yanlış soruları hazırla. Format: '1. [İfade] (___)'. Cevap anahtarında D/Y belirt."
                elif soru_tipi == "Boşluk Doldurma":
                    type_instruction = "GÖREV: Cümledeki anahtar kelimeyi çıkarıp '__________' koy. Cevabı not et."
                elif soru_tipi == "Klasik (Açık Uçlu)":
                    type_instruction = "GÖREV: Yorum ve işlem gerektiren açık uçlu sorular sor. Beklenen cevabı özetle."
                elif soru_tipi == "Eşleştirme":
                    type_instruction = "GÖREV: Grup A (1,2..) ve Grup B (a,b..) olarak eşleştirme sorusu hazırla."

                prompt = f"""
                {base_instruction}
                {type_instruction}
                ÖNEMLİ: Sorular bittikten sonra TAM OLARAK şu ayırıcıyı koy: "---CEVAP_ANAHTARI---". Sonra cevapları yaz.
                """
                
                response = model.generate_content(prompt)
                full_text = response.text
                
                if "---CEVAP_ANAHTARI---" in full_text:
                    parts = full_text.split("---CEVAP_ANAHTARI---")
                    sorular = parts[0].strip()
                    cevaplar = parts[1].strip()
                else:
                    sorular = full_text
                    cevaplar = "Ayrıştırma hatası."

                st.success("Sınav Başarıyla Hazırlandı!")
                
                tab1, tab2 = st.tabs(["📄 Sınav Kağıdı", "🔑 Cevap Anahtarı"])
                with tab1:
                    st.write(sorular)
                with tab2:
                    st.write(cevaplar)
                
                # PDF Oluşturma
                pdf_soru = create_pdf(sorular, title=f"{konu} - {soru_tipi}")
                pdf_tam = create_pdf(full_text.replace("---CEVAP_ANAHTARI---", "\n\nCEVAP ANAHTARI\n----------------"), title="Tam")
                
                # İndirme Butonları
                c_pdf1, c_pdf2 = st.columns(2)
                with c_pdf1:
                    st.download_button("📄 Soruları İndir (PDF)", data=pdf_soru, file_name="sorular.pdf", mime="application/pdf")
                with c_pdf2:
                    st.download_button("📑 Cevaplı İndir (PDF)", data=pdf_tam, file_name="cevapli_sinav.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"Hata: {e}")
