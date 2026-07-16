import pandas as pd
import numpy as np
from xgboost import XGBClassifier

class ModelEgitici:
    def __init__(self):
        # XGBoost Sınıflandırıcı Modeli
        self.model = XGBClassifier(
            n_estimators=100, 
            max_depth=4, 
            learning_rate=0.05, 
            random_state=42,
            eval_metric='logloss'
        )
        self.ozellikler = [
            'SMA_10', 'SMA_50', 'RSI_14', 'BB_Ust', 'BB_Alt', 
            'Momentum', 'ATR_14', 'SP500', 'DXY', 'GOLD', 'VIX'
        ]
        
    def veriyi_hazirla(self, df: pd.DataFrame, haber_skorlari: list = None) -> pd.DataFrame:
        df = df.copy()
        
        # Hedef Değişken: 3 gün sonraki kapanış fiyatı bugünkü fiyattan yüksek mi?
        df['Hedef_Fiyat'] = df['Close'].shift(-3)
        df['Hedef'] = (df['Hedef_Fiyat'] > df['Close']).astype(int)
        
        # Haber skorları entegrasyonu (Opsiyonel)
        if haber_skorlari and len(haber_skorlari) == len(df):
            df['Haber_Skor'] = haber_skorlari
            if 'Haber_Skor' not in self.ozellikler:
                self.ozellikler.append('Haber_Skor')
                
        df.dropna(subset=['Hedef_Fiyat'], inplace=True)
        return df
        
    def egit_ve_test_et(self, df: pd.DataFrame):
        X = df[self.ozellikler]
        y = df['Hedef']
        
        # Zaman Serisi Bölmesi (Veri sızıntısını önlemek için shuffle=False)
        split_index = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
        y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]
        
        self.model.fit(X_train, y_train)
        dogruluk = self.model.score(X_test, y_test)
        print(f"🎯 Sınıflandırma Doğruluk Skoru: %{dogruluk * 100:.2f}")
        return dogruluk