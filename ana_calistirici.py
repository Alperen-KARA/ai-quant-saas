from moduller.veri_toplayici import VeriToplayici
from moduller.veri_isleyici import VeriIsleyici
from moduller.model_egitici import ModelEgitici
from moduller.backtest_motoru import BacktestMotoru
from sklearn.model_selection import train_test_split
import pandas as pd
from datetime import datetime

def canli_sinyal_raporu_uret(islenmis_hisseler_dict: dict, egitilmis_modeller_dict: dict):
    """
    Sistemin en güncel gün verilerine bakarak yarınki borsa açılışı için
    kullanıcıya profesyonel bir yapay zeka sinyal raporu üretir.
    """
    print("\n==============================================")
    print("📢 YARIN İÇİN CANLI YAPAY ZEKA SİNYAL RAPORU 📢")
    print("==============================================")
    print(f"Rapor Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("----------------------------------------------")
    
    en_iyi_hisse = None
    en_yuksek_ihtimal = 0.0
    tum_sinyaller = []
    
    for sembol, df in islenmis_hisseler_dict.items():
        # En son satırı (en güncel günü) alıyoruz
        son_gun_verisi = df.iloc[[-1]]
        model = egitilmis_modeller_dict[sembol]
        
        # Gelecek günü tahmin et
        X_son = son_gun_verisi[model.ozellikler]
        prob = model.model.predict_proba(X_son)[0]
        yukselis_ihtimali = prob[1] * 100
        dusis_ihtimali = prob[0] * 100
        
        tum_sinyaller.append({
            "Hisse": sembol,
            "Yukselis_Ihtimali": round(yukselis_ihtimali, 2),
            "Dusis_Ihtimali": round(dusis_ihtimali, 2)
        })
        
        if yukselis_ihtimali > en_yuksek_ihtimal:
            en_yuksek_ihtimal = yukselis_ihtimali
            en_iyi_hisse = sembol

    # Sinyalleri olasılığa göre sıralayalım
    tum_sinyaller = sorted(tum_sinyaller, key=lambda x: x['Yukselis_Ihtimali'], reverse=True)
    
    print("📊 Hisselerin Yarınki Yükseliş Olasılıkları:")
    for s in tum_sinyaller:
        durum_ikonu = "🟢" if s['Yukselis_Ihtimali'] >= 55.0 else "🟡"
        print(f"  {durum_ikonu} {s['Hisse']}: Yükseliş İhtimali: %{s['Yukselis_Ihtimali']} | Düşüş İhtimali: %{s['Dusis_Ihtimali']}")
        
    print("----------------------------------------------")
    if en_yuksek_ihtimal >= 55.0:
        print(f"💡 YAPAY ZEKA TAVSİYESİ (GÖSTERGE):")
        print(f"  En güçlü yükseliş sinyali %{en_yuksek_ihtimal:.2f} ile **{en_iyi_hisse}** hissesindedir.")
        print(f"  Eğer nakitteyseniz portföyü **{en_iyi_hisse}** hissesine kaydırmayı değerlendirebilirsiniz.")
    else:
        print("💡 YAPAY ZEKA TAVSİYESİ (GÖSTERGE):")
        print("  Hiçbir hissede %55 üzerinde güçlü yükseliş sinyali bulunamadı.")
        print("  Piyasa belirsiz görünüyor, nakitte kalıp korunmak daha güvenli olabilir.")
    print("==============================================\n")

def ana_akisi_baslat():
    print("=== COKLU PORTFOY YAPAY ZEKA YATIRIM SİSTEMİ BAŞLATILIYOR ===\n")
    
    hisseler = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
    # En güncel veriyi çekmek için bugünün tarihine kadar olan verileri istiyoruz
    baslangic = "2023-01-01"
    bitis = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Çoklu veri indirme
    toplayici = VeriToplayici()
    coklu_ham_veri = toplayici.coklu_hisse_ve_makro_indir(hisseler, baslangic, bitis)
    
    if not coklu_ham_veri:
        print("❌ Veriler indirilemediği için sistem durduruldu.")
        return
        
    islenmis_hisseler = {}
    egitilmis_modeller = {}
    test_hisseler = {}
    
    for sembol, df in coklu_ham_veri.items():
        print(f"\n🧠 {sembol} için model hazırlanıyor...")
        isleyici = VeriIsleyici(df)
        islenmis_df = isleyici.teknik_gostergeleri_ekle()
        
        egitici = ModelEgitici()
        hazir_df = egitici.veriyi_hazirla(islenmis_df, haber_skorlari=[])
        egitici.egit_ve_test_et(hazir_df)
        
        # Test seti bölmesi
        _, test_df = train_test_split(hazir_df, test_size=0.2, shuffle=False)
        
        test_hisseler[sembol] = test_df
        egitilmis_modeller[sembol] = egitici
        islenmis_hisseler[sembol] = hazir_df
        
    # 2. Portföy Backtest Motorunu Çalıştırma
    simulasyon = BacktestMotoru(baslangic_bakiyesi=10000.0, komisyon_orani=0.001)
    sonuc = simulasyon.portfoy_calistir(
        test_hisseler, 
        egitilmis_modeller, 
        esik_degeri=55.0, 
        min_elde_tutma=3
    )
    
    print("\n==============================================")
    print("🏆 DİNAMİK PORTFÖY BACKTEST RAPORU 🏆")
    print("==============================================")
    print(f"💵 Başlangıç Sermayesi: {sonuc['Baslangic']}$")
    print(f"💰 Yapay Zeka Portföy Değeri: {sonuc['Nihai_Portfoy']}$")
    print(f"📈 Yapay Zeka Portföy Net Getiri: %{sonuc['Yapay_Zeka_Portfoy_Getiri_Yuzde']}")
    print(f"📉 S&P 500 Endeks Getirisi: %{sonuc['Endeks_Getiri_Yuzde']}")
    print(f"🔄 Gerçekleşen Rotasyon İşlem Sayısı: {sonuc['Islem_Sayisi']}")
    print("==============================================")

    # 3. Canlı Sinyal Raporunu Çalıştır
    canli_sinyal_raporu_uret(islenmis_hisseler, egitilmis_modeller)

if __name__ == "__main__":
    ana_akisi_baslat()