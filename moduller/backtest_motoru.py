import pandas as pd

class BacktestMotoru:
    def __init__(self, baslangic_bakiyesi: float = 10000.0, komisyon_orani: float = 0.001):
        self.baslangic_bakiyesi = baslangic_bakiyesi
        self.komisyon_orani = komisyon_orani
        
    def portfoy_calistir(self, test_hisseler: dict, egitilmis_modeller: dict, esik_degeri: float = 55.0, min_elde_tutma: int = 3) -> dict:
        print(f"📊 Portföy Backtest Motoru Sabır Filtresiyle Çalışıyor... (Min. Elde Tutma: {min_elde_tutma} gün)")
        
        bakiye = self.baslangic_bakiyesi
        eldeki_hisse = None
        alis_fiyati = 0.0
        adet = 0.0
        islem_sayisi = 0
        elde_tutulan_gun = 0
        
        # 1. ORTAK TARİHLERİ BUL VE GÜVENLİK KONTROLÜ YAP
        ortak_tarihler = None
        for sembol, df in test_hisseler.items():
            if df.empty:
                continue
            if ortak_tarihler is None:
                ortak_tarihler = df.index
            else:
                ortak_tarihler = ortak_tarihler.intersection(df.index)
                
        # Eğer hiç ortak tarih bulunamazsa çökmemek için tüm hisselerin birleşik tarih indeksini kullanıyoruz
        if ortak_tarihler is None or len(ortak_tarihler) == 0:
            all_indices = [df.index for df in test_hisseler.values() if not df.empty]
            if all_indices:
                # Tüm tarihleri birleştirip benzersiz olanları sıralıyoruz
                ortak_tarihler = sorted(list(set().union(*all_indices)))
            else:
                # Tamamen boşsa varsayılan boş bir liste döndür
                ortak_tarihler = []
        else:
            ortak_tarihler = sorted(list(ortak_tarihler))

        # Eğer hala hiç tarih yoksa sıfır getiri ile güvenli çıkış yap
        if not ortak_tarihler:
            return {
                "Baslangic": self.baslangic_bakiyesi,
                "Nihai_Portfoy": self.baslangic_bakiyesi,
                "Yapay_Zeka_Portfoy_Getiri_Yuzde": 0.0,
                "Endeks_Getiri_Yuzde": 0.0,
                "Islem_Sayisi": 0
            }
        
        # 2. BACKTEST SİMÜLASYON DÖNGÜSÜ
        for i in range(len(ortak_tarihler)):
            tarih = ortak_tarihler[i]
            
            # Portföy güncelleme ve hisse satışı kontrolü
            if eldeki_hisse is not None:
                elde_tutulan_gun += 1
                guncel_hisse_df = test_hisseler[eldeki_hisse]
                
                # Eğer ilgili güne ait veri o hissede yoksa pas geçiyoruz
                if tarih in guncel_hisse_df.index:
                    guncel_kapanis = float(guncel_hisse_df.loc[tarih, 'Close'].iloc[0]) if isinstance(guncel_hisse_df.loc[tarih, 'Close'], pd.Series) else float(guncel_hisse_df.loc[tarih, 'Close'])
                    
                    # Sabır Filtresi: En az 'min_elde_tutma' gün elde tutulacak
                    if elde_tutulan_gun >= min_elde_tutma:
                        en_iyi_hisse = None
                        en_yuksek_ihtimal = 0.0
                        
                        for sembol, df in test_hisseler.items():
                            if tarih in df.index:
                                satir = df.loc[[tarih]]
                                model_obj = egitilmis_modeller[sembol]
                                X_guncel = satir[model_obj.ozellikler]
                                prob = model_obj.model.predict_proba(X_guncel)[0]
                                yukselis_ihtimali = prob[1] * 100
                                
                                if yukselis_ihtimali > en_yuksek_ihtimal:
                                    en_yuksek_ihtimal = yukselis_ihtimali
                                    en_iyi_hisse = sembol
                                
                        if en_iyi_hisse != eldeki_hisse and en_yuksek_ihtimal >= esik_degeri:
                            bakiye = adet * guncel_kapanis * (1 - self.komisyon_orani)
                            islem_sayisi += 1
                            eldeki_hisse = None
                            adet = 0.0
                            elde_tutulan_gun = 0
            
            # Portföye yeni hisse alımı
            if eldeki_hisse is None:
                en_iyi_hisse = None
                en_yuksek_ihtimal = 0.0
                
                for sembol, df in test_hisseler.items():
                    if tarih in df.index:
                        satir = df.loc[[tarih]]
                        model_obj = egitilmis_modeller[sembol]
                        X_guncel = satir[model_obj.ozellikler]
                        prob = model_obj.model.predict_proba(X_guncel)[0]
                        yukselis_ihtimali = prob[1] * 100
                        
                        if yukselis_ihtimali > en_yuksek_ihtimal:
                            en_yuksek_ihtimal = yukselis_ihtimali
                            en_iyi_hisse = sembol
                
                if en_yuksek_ihtimal >= esik_degeri and en_iyi_hisse is not None:
                    hedef_hisse_df = test_hisseler[en_iyi_hisse]
                    guncel_kapanis = float(hedef_hisse_df.loc[tarih, 'Close'].iloc[0]) if isinstance(hedef_hisse_df.loc[tarih, 'Close'], pd.Series) else float(hedef_hisse_df.loc[tarih, 'Close'])
                    
                    bakiye = bakiye * (1 - self.komisyon_orani)
                    adet = bakiye / guncel_kapanis
                    eldeki_hisse = en_iyi_hisse
                    alis_fiyati = guncel_kapanis
                    bakiye = 0.0
                    elde_tutulan_gun = 0
                    islem_sayisi += 1
                    
        # Portföyü nakde çevirip son duruma bakma
        if eldeki_hisse is not None:
            son_tarih = ortak_tarihler[-1]
            son_hisse_df = test_hisseler[eldeki_hisse]
            if son_tarih in son_hisse_df.index:
                son_kapanis = float(son_hisse_df.loc[son_tarih, 'Close'].iloc[0]) if isinstance(son_hisse_df.loc[son_tarih, 'Close'], pd.Series) else float(son_hisse_df.loc[son_tarih, 'Close'])
                bakiye = adet * son_kapanis * (1 - self.komisyon_orani)
            else:
                bakiye = adet * alis_fiyati  # Veri yoksa alış fiyatından koru
            
        getiri_yuzde = ((bakiye - self.baslangic_bakiyesi) / self.baslangic_bakiyesi) * 100
        
        # Referans Endeks Karşılaştırması (Hata korumalı)
        endeks_getiri = 0.0
        try:
            referans_hisse = list(test_hisseler.keys())[0]
            referans_df = test_hisseler[referans_hisse]
            sp_baslangic = referans_df.loc[ortak_tarihler[0], 'SP500']
            sp_bitis = referans_df.loc[ortak_tarihler[-1], 'SP500']
            sp_baslangic_val = float(sp_baslangic.iloc[0]) if isinstance(sp_baslangic, pd.Series) else float(sp_baslangic)
            sp_bitis_val = float(sp_bitis.iloc[0]) if isinstance(sp_bitis, pd.Series) else float(sp_bitis)
            endeks_getiri = ((sp_bitis_val - sp_baslangic_val) / sp_baslangic_val) * 100
        except Exception:
            pass
        
        return {
            "Baslangic": self.baslangic_bakiyesi,
            "Nihai_Portfoy": round(bakiye, 2),
            "Yapay_Zeka_Portfoy_Getiri_Yuzde": round(getiri_yuzde, 2),
            "Endeks_Getiri_Yuzde": round(endeks_getiri, 2),
            "Islem_Sayisi": islem_sayisi
        }