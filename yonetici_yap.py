import sqlite3

# Veritabanına bağlanıyoruz
conn = sqlite3.connect("ai_quant_saas.db")
cursor = conn.cursor()

# E-posta adresini doğrudan aktif ve premium yapıyoruz
cursor.execute("""
    UPDATE users 
    SET is_verified = 1, subscription_status = 'premium' 
    WHERE email = 'karaalperen0591@gmail.com'
""")

conn.commit()
conn.close()
print("Hesabınız başarıyla Premium ve Aktif yapıldı! Şimdi Streamlit'e girip sayfayı yenileyebilirsiniz.")