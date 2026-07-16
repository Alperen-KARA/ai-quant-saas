import yfinance as yf
import pandas as pd
from datetime import datetime

class VeriToplayici:
    def __init__(self):
        pass
        
    def coklu_hisse_ve_makro_indir(self, hisseler: list, baslangic: str, bitis: str) -> dict:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Çoklu veri indirme işlemi başladı ({len(hisseler)} hisse)...")
        sonuclar = {}
        
        # Makro Göstergeler (S&P 500, Dolar Endeksi, Altın, Tahvil)
        try:
            sp500 = yf.download("^GSPC", start=baslangic, end=bitis, progress=False)[['Close']].rename(columns={'Close': 'SP500'})
            dxy = yf.download("DX-Y.NYB", start=baslangic, end=bitis, progress=False)[['Close']].rename(columns={'Close': 'DXY'})
            gold = yf.download("GC=F", start=baslangic, end=bitis, progress=False)[['Close']].rename(columns={'Close': 'GOLD'})
            vix = yf.download("^VIX", start=baslangic, end=bitis, progress=False)[['Close']].rename(columns={'Close': 'VIX'})
            
            # Verileri birleştiriyoruz
            makro_df = sp500.join([dxy, gold, vix], how='inner')
        except Exception as e:
            print(f"⚠️ Makro veriler indirilirken hata oluştu: {e}")
            return {}
            
        for hisse in hisseler:
            print(f"📥 {hisse} verisi indiriliyor...")
            try:
                hisse_df = yf.download(hisse, start=baslangic, end=bitis, progress=False)
                if hisse_df.empty:
                    continue
                
                # Tekil indeks seviyesine indirgeme (MultiIndex kolonu temizliği)
                hisse_df.columns = [col[0] if isinstance(col, tuple) else col for col in hisse_df.columns]
                makro_df.columns = [col[0] if isinstance(col, tuple) else col for col in makro_df.columns]
                
                # Makro verileri hisse senedi verisiyle birleştiriyoruz
                bilesik_df = hisse_df.join(makro_df, how='inner')
                
                # =====================================================================
                # 🛠️ YENİ PANDAS UYUMLU DOLDURMA YÖNTEMİ (Hata Veren Kısım Düzenlendi)
                # =====================================================================
                bilesik_df = bilesik_df.ffill()  # Eski fillna(method='ffill') yerine
                bilesik_df = bilesik_df.bfill()  # Eski fillna(method='bfill') yerine
                
                sonuclar[hisse] = bilesik_df
            except Exception as e:
                print(f"⚠️ {hisse} indirilirken hata: {e}")
                
        print("🚀 Tüm seçilen hisselerin gelişmiş makro veri entegrasyonu tamamlandı!\n")
        return sonuclar