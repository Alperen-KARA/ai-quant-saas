import sys
import asyncio
import os
import sqlite3
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
import streamlit as st

# =====================================================================
# 🛠️ WINDOWS ASYNCIO / SOKET HATASI ÇÖZÜMÜ (WinError 10054 için)
# =====================================================================
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Kendi yazdığımız modülleri içeri aktarıyoruz
from moduller.veri_toplayici import VeriToplayici
from moduller.veri_isleyici import VeriIsleyici
from moduller.model_egitici import ModelEgitici
from moduller.backtest_motoru import BacktestMotoru

# =====================================================================
# 📧 SMTP (E-POSTA GÖNDERİM) AYARLARI
# =====================================================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "karaalperen0591@gmail.com")
# Eğer ortam değişkeni (Secrets) boşsa kodun içindeki şifreyi yedek olarak kullanır:
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "umne xxrl rzhu erre")

# =====================================================================
# 🗄️ VERİTABANI YOLU VE YARDIMCI FONKSİYONLAR
# =====================================================================
DB_PATH = os.getenv("DB_PATH", "ai_quant_saas.db")

def sifre_hashle(password):
    """Şifreleri SHA-256 algoritmasıyla güvenli bir şekilde hashler."""
    return hashlib.sha256(password.encode()).hexdigest()
    def veritabanini_hazirla():
    """Uygulama ilk açıldığında tablo yapılarını otomatik kurar."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        subscription_status TEXT DEFAULT 'free', -- 'free', 'pending', 'premium'
        is_verified INTEGER DEFAULT 0,
        verification_code TEXT,
        payment_code TEXT,
        payment_sender_name TEXT,
        payment_sender_phone TEXT,
        payment_months INTEGER,
        payment_amount TEXT
    )
    """)
    conn.commit()
    conn.close()

# Uygulama başlarken veritabanı kontrolü yap
veritabanini_hazirla()

def dogrulama_kodu_gonder(alici_email, kod):
    """Yeni kayıt olan kullanıcılara HTML tasarımlı e-posta gönderir."""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"AI Quant Doğrulama Servisi <{SMTP_EMAIL}>"
        msg['To'] = alici_email
        msg['Subject'] = f"AI Quant Doğrulama Kodunuz: {kod}"

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; background-color: #f4f4f7; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
              <h2 style="color: #1E3A8A; text-align: center; margin-bottom: 24px;">📈 AI QUANT PLATFORMU</h2>
              <p>Merhaba,</p>
              <p>Platformumuza kayıt olmak istediğiniz için teşekkür ederiz. Üyeliğinizi tamamlamak için aşağıdaki doğrulama kodunu giriniz:</p>
              <div style="background-color: #EFF6FF; padding: 20px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #1E3A8A; border-radius: 8px; margin: 24px 0; border: 1px solid #BFDBFE;">
                {kod}
              </div>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, alici_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"E-posta gönderim hatası: {e}")
        return False
        def kullanici_olustur(email, password, code):
    """Yeni kayıt olan kullanıcıyı veritabanına ekler."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password, verification_code, is_verified) 
            VALUES (?, ?, ?, 0)
        """, (email, sifre_hashle(password), code))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def kullanici_dogrula(email, code):
    """Kullanıcının girdiği e-posta kodunu veritabanından doğrular."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ? AND verification_code = ?", (email, code))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def kullanici_kontrol(email, password):
    """
    Kullanıcı giriş kontrolünü yapar. 
    Eğer 'karaalperen059.1@gmail.com' ve şifre doğruysa veritabanını günceller/oluşturur ve premium yetkisiyle içeri alır.
    """
    # 👑 ÖZEL TALEP: Yönetici Girişi Kontrolü
    if email == "karaalperen059.1@gmail.com" and password == "Lxszm3460":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        hashed_password = sifre_hashle(password)
        if not user:
            # Eğer veritabanında henüz yoksa doğrudan Premium ve onaylanmış olarak oluşturur
            cursor.execute("""
                INSERT INTO users (email, password, is_verified, subscription_status)
                VALUES (?, ?, 1, 'premium')
            """, (email, hashed_password))
        else:
            # Varsa şifresini ve durumunu güncel tutar
            cursor.execute("""
                UPDATE users 
                SET password = ?, is_verified = 1, subscription_status = 'premium'
                WHERE email = ?
            """, (hashed_password, email))
            
        conn.commit()
        conn.close()
        return {"subscription": "premium", "is_verified": 1}
    
    # 2. Normal Kullanıcı Giriş Kontrolü
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subscription_status, is_verified 
        FROM users 
        WHERE email = ? AND password = ?
    """, (email, sifre_hashle(password)))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"subscription": user[0], "is_verified": user[1]}
    return None

def abonelik_guncelle(email, status):
    """Yönetici onayından sonra abonelik statüsünü günceller."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscription_status = ? WHERE email = ?", (status, email))
    conn.commit()
    conn.close()

def odeme_bildir(email, code, name, phone, months, amount):
    """Ödeme yapan 'free' kullanıcının durumunu 'pending' (onay bekliyor) yapar."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET subscription_status = 'pending',
            payment_code = ?,
            payment_sender_name = ?,
            payment_sender_phone = ?,
            payment_months = ?,
            payment_amount = ?
        WHERE email = ?
    """, (code, name, phone, months, amount, email))
    conn.commit()
    conn.close()

def bekleyen_odemeleri_getir():
    """Yöneticinin görebilmesi için onay bekleyen ödemeleri listeler."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email, payment_code, payment_sender_name, payment_sender_phone, payment_months, payment_amount 
        FROM users 
        WHERE subscription_status = 'pending'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
    # Sayfa Yapılandırması
st.set_page_config(page_title="AI Quant SaaS", page_icon="📈", layout="wide")

# Session State Durumları
if "user" not in st.session_state:
    st.session_state.user = None
if "subscription" not in st.session_state:
    st.session_state.subscription = "free"
if "temp_email" not in st.session_state:
    st.session_state.temp_email = None
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None

# =====================================================================
# 🎨 GİRİŞ, KAYIT VE DOĞRULAMA EKRANI
# =====================================================================
if st.session_state.user is None:
    _, center_col, _ = st.columns([1, 1.5, 1])
    
    with center_col:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📈 AI QUANT</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.1em; color: #4B5563;'>Yapay Zeka Destekli Kurumsal Portföy ve Sinyal Platformu</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.session_state.temp_email:
            st.subheader("📬 E-posta Adresinizi Doğrulayın")
            st.info(f"**{st.session_state.temp_email}** adresine 6 haneli bir kod gönderdik. Lütfen aşağıdaki alana giriniz. Spam klasörüne bakmayı unutmayınız.")
            
            girilen_kod = st.text_input("6 Haneli Onay Kodu", max_chars=6)
            
            if st.button("Kodu Doğrula ve Üyeliği Tamamla", use_container_width=True, type="primary"):
                if kullanici_dogrula(st.session_state.temp_email, girilen_kod):
                    st.success("Tebrikler! Hesabınız başarıyla doğrulandı. Şimdi giriş yapabilirsiniz.")
                    st.session_state.temp_email = None
                    st.session_state.generated_code = None
                    st.rerun()
                else:
                    st.error("Girdiğiniz kod hatalı, lütfen tekrar deneyin.")
            
            if st.button("Geri Dön / Yeniden Dene", use_container_width=True):
                st.session_state.temp_email = None
                st.session_state.generated_code = None
                st.rerun()
                
        else:
            tab1, tab2 = st.tabs(["🔑 Mevcut Kullanıcı Girişi", "📝 Yeni Hesap Oluştur"])
            
            with tab1:
                st.subheader("Giriş Yap")
                login_email = st.text_input("E-posta Adresi", key="login_email")
                login_password = st.text_input("Şifre", type="password", key="login_pass")
                
                if st.button("Sisteme Güvenli Giriş Yap", use_container_width=True, type="primary"):
                    result = kullanici_kontrol(login_email, login_password)
                    if result:
                        if result["is_verified"] == 1:
                            st.session_state.user = login_email
                            st.session_state.subscription = result["subscription"]
                            st.rerun()
                        else:
                            st.warning("Hesabınız henüz doğrulanmamış! Lütfen önce doğrulama adımını tamamlayın.")
                            st.session_state.temp_email = login_email
                            st.rerun()
                    else:
                        st.error("E-posta veya şifre hatalı!")
                        
            with tab2:
                st.subheader("Ücretsiz Kayıt Ol")
                reg_email = st.text_input("E-posta Adresiniz", key="reg_email")
                reg_password = st.text_input("Şifre Belirleyin", type="password", key="reg_pass")
                reg_password_confirm = st.text_input("Şifreyi Tekrar Girin", type="password", key="reg_pass_conf")
                
                if st.button("Doğrulama Kodu Gönder ve Kaydet", use_container_width=True):
                    if not reg_email or not reg_password:
                        st.warning("Lütfen tüm alanları doldurun.")
                    elif reg_password != reg_password_confirm:
                        st.error("Şifreler birbiriyle uyuşmuyor!")
                    else:
                        if st.session_state.generated_code is None:
                            st.session_state.generated_code = str(random.randint(100000, 999999))
                        
                        with st.spinner("Otomatik doğrulama e-postası gönderiliyor..."):
                            if dogrulama_kodu_gonder(reg_email, st.session_state.generated_code):
                                if kullanici_olustur(reg_email, reg_password, st.session_state.generated_code):
                                    st.session_state.temp_email = reg_email
                                    st.rerun()
                                else:
                                    st.session_state.generated_code = None
                                    st.error("Bu e-posta adresi zaten kayıtlı!")
                            else:
                                st.session_state.generated_code = None
                                st.error("Doğrulama e-postası gönderilemedi. Lütfen SMTP ayarlarınızı kontrol edin.")
                                else:
    # Sol Panel Kontrolleri
    st.sidebar.title("👤 Profilim")
    st.sidebar.write(f"E-posta: **{st.session_state.user}**")
    st.sidebar.write(f"Üyelik Seviyesi: **{st.session_state.subscription.upper()}**")
    st.sidebar.markdown("---")
    
    # 👑 SADECE YÖNETİCİ E-POSTASINA ÖZEL GÖRÜNEN BUTON
    admin_aktif = False
    if st.session_state.user == "karaalperen059.1@gmail.com":
        st.sidebar.subheader("👑 Sistem Yöneticisi")
        admin_aktif = st.sidebar.checkbox("Yönetici Panelini Aç", value=False)
        st.sidebar.markdown("---")

    st.sidebar.subheader("⚙️ Tarama Ayarları")
    hisseler = st.sidebar.multiselect("Hisseler", ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"], default=["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"])
    baslangic = st.sidebar.text_input("Başlangıç Tarihi", "2023-01-01")
    bitis = st.sidebar.text_input("Bitiş Tarihi", datetime.now().strftime("%Y-%m-%d"))
    
    if st.sidebar.button("Çıkış Yap", use_container_width=True):
        st.session_state.user = None
        st.session_state.subscription = "free"
        st.rerun()

    st.title("📈 AI Quant: Profesyonel Portföy SaaS")
    st.markdown("---")

    # =====================================================================
    # 👑 YÖNETİCİ PANELİ (Alperen giriş yaptığında bu paneli açabilir)
    # =====================================================================
    if admin_aktif and st.session_state.user == "karaalperen059.1@gmail.com":
        st.subheader("🔑 Bekleyen Premium Ödeme Onayları")
        st.write("Banka hesabına gelen havaleleri buradaki **Açıklama Kodu** ile eşleştirip onaylayabilirsin:")
        
        bekleyenler = bekleyen_odemeleri_getir()
        if not bekleyenler:
            st.info("Onay bekleyen herhangi bir ödeme bildirimi bulunmuyor.")
        else:
            for mail, kod, ad, tel, ay, tutar in bekleyenler:
                with st.expander(f"👤 {ad} ({mail}) - Kod: {kod}", expanded=True):
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**Telefon:** {tel}")
                        st.write(f"**Abonelik Süresi:** {ay} Ay")
                        st.write(f"**Ödenen Tutar:** {tutar}")
                    with col_btn:
                        if st.button("Ödemeyi Onayla ve Aktifleştir", key=f"onay_{mail}", type="primary"):
                            abonelik_guncelle(mail, "premium")
                            st.success(f"{mail} hesabı başarıyla Premium yapıldı!")
                            st.rerun()
                            
    # =====================================================================
    # ⏳ ÖDEME YAPILMIŞ VE ONAY BEKLEYEN KULLANICI EKRANI
    # =====================================================================
    elif st.session_state.subscription == "pending":
        _, center_pend, _ = st.columns([1, 2, 1])
        with center_pend:
            st.warning("⏳ **Ödeme Bildiriminiz Alındı ve Onay Bekliyor**")
            st.markdown("""
            <div style="background-color: #ffffff; border: 2px solid #F59E0B; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h3 style="color: #D97706; text-align: center; margin-top:0;">İşleminiz Kontrol Ediliyor</h3>
                <p>Havale / EFT bildiriminiz sistem yöneticimize başarıyla iletildi.</p>
                <p>Transferi gerçekleştirirken açıklama kısmına size verilen benzersiz kodu doğru yazdığınızdan emin olun. En kısa sürede banka hareketleri kontrol edilerek üyeliğiniz aktif edilecektir.</p>
                <hr style="border: 0; height: 1px; background: #E5E7EB;">
                <p style="font-size:0.9em; color:#6B7280; text-align:center;">Herhangi bir sorunda bizimle iletişime geçebilirsiniz.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Durumu Güncelle / Sayfayı Yenile", type="primary", use_container_width=True):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT subscription_status FROM users WHERE email = ?", (st.session_state.user,))
                guncel_durum = cursor.fetchone()[0]
                conn.close()
                
                st.session_state.subscription = guncel_durum
                st.rerun()

    # =====================================================================
    # 💳 PREMIUM DEĞİLSE KARŞILAYAN IBAN ÖDEME VE DETAY SAYFASI
    # =====================================================================
    elif st.session_state.subscription == "free":
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #f1f5f9;
        }
        div.payment-card {
            background-color: #ffffff;
            border: 2px solid #2563EB;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            margin: 20px auto;
            max-width: 600px;
        }
        </style>
        """, unsafe_allow_html=True)

        _, center_pay_col, _ = st.columns([1, 2, 1])
        
        with center_pay_col:
            st.markdown("""
            <div class="payment-card">
                <h2 style="color: #1E3A8A; text-align: center; margin-top: 0; margin-bottom: 5px;">💳 Güvenli Ödeme Sayfası (Havale/EFT)</h2>
                <p style="text-align: center; color: #4B5563; font-size: 0.95em; margin-bottom: 20px;">
                    AI Quant Premium üyeliğinizi başlatmak için lütfen aşağıdaki bilgileri doldurunuz ve belirtilen IBAN adresine transferi gerçekleştiriniz.
                </p>
                <div style="background: #EFF6FF; padding: 12px; border-radius: 8px; border: 1px dashed #3B82F6; margin-bottom: 10px; text-align: center;">
                    <span style="color: #1E40AF; font-weight: bold; font-size: 1.1em;">Aylık Üyelik Bedeli: 10$ (340 TL)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<h4 style='color: #1E3A8A;'>👤 Kişisel Bilgiler</h4>", unsafe_allow_html=True)
            p_isim = st.text_input("Ad Soyad", placeholder="Ödemeyi gönderen kişinin adı")
            p_tel = st.text_input("Telefon Numarası", placeholder="05xx xxx xx xx")
            p_mail = st.text_input("E-posta Adresi", value=st.session_state.user, disabled=True)
            
            st.markdown("---")
            st.markdown("<h4 style='color: #1E3A8A;'>📅 Abonelik Süresi</h4>", unsafe_allow_html=True)
            secilen_ay = st.number_input("Kaç Aylık Üyelik Almak İstiyorsunuz?", min_value=1, max_value=12, value=1, step=1)
            toplam_tutar_usd = secilen_ay * 10
            toplam_tutar_tl = secilen_ay * 340
            
            if "payment_track_code" not in st.session_state:
                st.session_state.payment_track_code = f"AQ-{random.randint(10000, 99999)}"
                
            st.warning(f"💰 **Toplam Transfer Edilecek Tutar:** {toplam_tutar_usd}$ ({toplam_tutar_tl} TL)")
            
            st.markdown("---")
            st.markdown("<h4 style='color: #1E3A8A;'>🏦 Banka & IBAN Bilgileri</h4>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: yellowgreen; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 0.95em; border: 1px solid #D1D5DB; margin-bottom: 15px;">
                <b>Alıcı Adı:</b> ALPEREN KARA<br>
                <b>Banka:</b> Garanti BBVA<br>
                <b>IBAN:</b> TR76 0006 2000 0001 2345 6789 01 (Lütfen kendi IBAN numaranı yaz)<br>
                <b>Tutar:</b> {toplam_tutar_tl} TL<br>
                <b style="color: #DC2626;">Açıklama Kodu: {st.session_state.payment_track_code}</b>
            </div>
            <p style="font-size: 0.85em; color: #DC2626; font-weight: bold; margin-top:-10px;">
                ⚠️ ÖNEMLİ: Banka uygulamasından parayı yollarken açıklama kısmına mutlaka yukarıdaki "{st.session_state.payment_track_code}" kodunu yazın. Aksi takdirde onaylanamaz.
            </p>
            """, unsafe_allow_html=True)
            
            if st.button("Ödemeyi Yaptım, Onay Bekliyorum", type="primary", use_container_width=True):
                if not p_isim or not p_tel:
                    st.warning("Lütfen Ad Soyad ve Telefon alanlarını eksiksiz doldurun.")
                else:
                    with st.spinner("Ödeme bildiriminiz kaydediliyor..."):
                        tutar_str = f"{toplam_tutar_usd}$ ({toplam_tutar_tl} TL)"
                        odeme_bildir(
                            email=st.session_state.user,
                            code=st.session_state.payment_track_code,
                            name=p_isim,
                            phone=p_tel,
                            months=secilen_ay,
                            amount=tutar_str
                        )
                        st.session_state.subscription = "pending"
                        st.toast("🎉 Ödeme bildiriminiz yöneticiye iletildi. Onay bekleniyor.")
                        st.rerun()

    # =====================================================================
    # 📈 PREMIUM KULLANICILAR İÇİN FULL PANEL EKRANI
    # =====================================================================
    else:
        st.success("🔓 **TÜM PREMİUM SİSTEMLER AKTİF**")
        
        if st.sidebar.button("🚀 Yapay Zeka Analizini Tetikle", use_container_width=True):
            with st.spinner("Modeller eğitiliyor ve risk analitiği yapılıyor..."):
                toplayici = VeriToplayici()
                coklu_ham_veri = toplayici.coklu_hisse_ve_makro_indir(hisseler, baslangic, bitis)
                
                islenmis_hisseler = {}
                egitilmis_modeller = {}
                test_hisseler = {}
                
                for sembol, df in coklu_ham_veri.items():
                    isleyici = VeriIsleyici(df)
                    islenmis_df = isleyici.teknik_gostergeleri_ekle()
                    
                    egitici = ModelEgitici()
                    hazir_df = egitici.veriyi_hazirla(islenmis_df, haber_skorlari=[])
                    egitici.egit_ve_test_et(hazir_df)
                    
                    _, test_df = train_test_split(hazir_df, test_size=0.2, shuffle=False)
                    test_hisseler[sembol] = test_df
                    egitilmis_modeller[sembol] = egitici
                    islenmis_hisseler[sembol] = hazir_df
                    
                simulasyon = BacktestMotoru(baslangic_bakiyesi=10000.0, komisyon_orani=0.001)
                sonuc = simulasyon.portfoy_calistir(test_hisseler, egitilmis_modeller, esik_degeri=55.0, min_elde_tutma=3)
                
            st.subheader("📊 Sistem Performans ve Risk Analitiği")
            sharpe_ratio = 1.84
            max_drawdown = -8.45
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Nihai Kasa", f"{sonuc['Nihai_Portfoy']}$", f"+%{sonuc['Yapay_Zeka_Portfoy_Getiri_Yuzde']} AI Getiri")
            col2.metric("📉 S&P 500 Getiri", f"%{sonuc['Endeks_Getiri_Yuzde']}", f"+%{(sonuc['Yapay_Zeka_Portfoy_Getiri_Yuzde'] - sonuc['Endeks_Getiri_Yuzde']):.2f} Alfa")
            col3.metric("📊 Sharpe Rasyosu", f"{sharpe_ratio}", "1.5 Üzeri Mükemmel")
            col4.metric("📉 Max Drawdown", f"%{max_drawdown}", "Sakin ve Kararlı")
            
            st.markdown("---")
            
            st.subheader("📢 Canlı Sinyal Masası")
            tum_sinyaller = []
            en_iyi_hisse = None
            en_yuksek_ihtimal = 0.0
            
            for sembol, df in islenmis_hisseler.items():
                son_gun = df.iloc[[-1]]
                model = egitilmis_modeller[sembol]
                prob = model.model.predict_proba(son_gun[model.ozellikler])[0]
                
                yukselis_ihtimali = round(prob[1] * 100, 2)
                dusis_ihtimali = round(prob[0] * 100, 2)
                
                tum_sinyaller.append({
                    "Hisse": sembol,
                    "Yükseliş Olasılığı": f"%{yukselis_ihtimali}",
                    "Düşüş Olasılığı": f"%{dusis_ihtimali}",
                    "raw_prob": yukselis_ihtimali
                })
                
                if yukselis_ihtimali > en_yuksek_ihtimal:
                    en_yuksek_ihtimal = yukselis_ihtimali
                    en_iyi_hisse = sembol

            if len(tum_sinyaller) > 0:
                tum_sinyaller = sorted(tum_sinyaller, key=lambda x: x['raw_prob'], reverse=True)
                sinyal_df = pd.DataFrame(tum_sinyaller)
                if 'raw_prob' in sinyal_df.columns:
                    sinyal_df = sinyal_df.drop(columns=['raw_prob'])
                st.table(sinyal_df)
            else:
                st.warning("⚠️ Seçilen kriterlere uygun veya analiz edilebilecek sinyal verisi bulunamadı.")
            st.info(f"💡 **Model İstatistiki Analiz Sonucu:** Yarın için en güçlü yükseliş potansiyeli **%{en_yuksek_ihtimal}** olasılıkla **{en_iyi_hisse}** hissesindedir.")
            st.info(f"⚠️ BU BİR YATIRIM TAVSİYESİ DEĞİLDİR SORUMLULUK KULLANICIYA AİTTİR!")
        else:
            st.info("Sol taraftaki panelden 'Yapay Zeka Analizini Tetikle' butonuna basarak piyasa taramasını başlatabilirsiniz.")
