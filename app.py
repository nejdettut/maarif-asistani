import streamlit as st
import google.generativeai as genai
import time

# --- AYARLAR ---
# 1. API Anahtarını gizli kasadan çekiyoruz
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını yapın.")
    st.stop() 

# 2. SAYFA YAPISI
st.set_page_config(
    page_title="Maarif Asistanı",
    page_icon="🎓",
    layout="centered"
)

# 3. YAPAY ZEKA AYARLARI
try:
    genai.configure(api_key=API_KEY)
    # SENİN HESABINDA KESİN ÇALIŞAN MODEL: GEMINI 2.5 FLASH
    # Daha önce test ettik ve çalıştı. Hız limiti koyduğumuz için hata vermeyecek.
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"API Anahtarı hatası: {e}")

# --- ARAYÜZ (FRONTEND) ---
st.image("https://images.unsplash.com/photo-1546410531-bb4caa6b424d?q=80&w=2071&auto=format&fit=crop", caption="Eğitimde Yapay Zeka Dönemi")
st.title("🇹🇷 Maarif Asistanı")
st.markdown("**Bilişim Öğretmeni Nejdet Tut** tarafından geliştirilmiştir.")
st.write("---")

st.sidebar.header("⚙️ Sınav Ayarları")

# KULLANICI GİRDİLERİ
konu = st.text_input("Sınav Konusu:", "Örn: Python Döngüler, Kurtuluş Savaşı, Basit Elektrik Devreleri")

seviye = st.sidebar.selectbox(
    "Sınıf Seviyesi:",
    ("İlkokul (1-4)", "Ortaokul (5-8)", "Lise (9-12)", "Üniversite Hazırlık")
)

zorluk = st.sidebar.slider("Zorluk Seviyesi:", 1, 5, 3)
soru_sayisi = st.sidebar.number_input("Soru Sayısı:", min_value=1, max_value=20, value=5)

# --- İŞ MANTIĞI (BACKEND) ---
if st.button("Soruları Oluştur", type="primary"):
    if not API_KEY or "ANAHTARINI_YAPISTIR" in API_KEY:
        st.error("⚠️ Lütfen kod dosyasını açıp API Anahtarınızı 'API_KEY' kısmına yapıştırın!")
    else:
        with st.spinner('Yapay Zeka soruları hazırlıyor... (Kota güvenliği için 3 saniye bekleniyor)'):
            try:
                # KOTA GÜVENLİĞİ: Google'ın seni "robot" sanmaması için fren yapıyoruz
                time.sleep(3) 
                
                # GÜÇLENDİRİLMİŞ PROMPT (Hatasız Hesaplama İçin)
                prompt = f"""
                Sen Türk Milli Eğitim Müfredatına hakim, detaycı ve hatasız çalışan bir öğretmensin.
                
                GÖREV:
                Aşağıdaki kriterlere göre çoktan seçmeli sınav soruları hazırla.
                
                KONU: {konu}
                SEVİYE: {seviye}
                ZORLUK: {zorluk} / 5
                SORU SAYISI: {soru_sayisi} adet
                
                ÖZEL TALİMAT (ZİNCİRLEME DÜŞÜNCE TEKNİĞİ):
                Cevapları "tahmin etme", "hesapla".
                Özellikle kod veya mantık sorularında:
                1. Önce soruyu kurgula.
                2. Şıkları yazmadan önce kodun çıktısını adım adım zihninde çalıştır.
                3. Doğru cevabı kesinleştirdikten sonra şıkları yaz.
                
                ÇIKTI FORMATI (Aynen Bunu Kullan):
                Soru 1: [Soru Metni]
                A) ... B) ... C) ... D) ...
                
                (ÖĞRETMEN İÇİN NOT):
                Doğru Cevap: [Şık]
                Açıklama: Çünkü kod çalıştırıldığında x değeri... (kısa açıklama)
                
                (Tüm sorular için bu formatı uygula).
                """
                
                # API'YE İSTEK GÖNDER
                response = model.generate_content(prompt)
                
                # CEVABI EKRANA BAS
                st.success("✅ Sorular Hazırlandı!")
                st.markdown("### 📝 Sınav Kağıdı")
                st.write(response.text)
                
                # İNDİRME BUTONU
                st.download_button(
                    label="📥 Sınavı İndir (TXT)",
                    data=response.text,
                    file_name="sinav_sorulari.txt",
                    mime="text/plain"
                )
                
                # YASAL UYARI
                st.warning("⚠️ YASAL UYARI: Soruları sınıfta uygulamadan önce mutlaka kontrol ediniz.")
                
            except Exception as e:
                if "429" in str(e):
                    st.error("🚨 HIZ SINIRI: Lütfen biraz bekleyip tekrar deneyin.")
                elif "404" in str(e):
                     st.error(f"MODEL BULUNAMADI: Kodun içindeki model ismini kontrol et. Hata: {e}")
                else:
                    st.error(f"Bir hata oluştu: {e}")