import pandas as pd
import numpy as np

class VeriIsleyici:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
    def teknik_gostergeleri_ekle(self) -> pd.DataFrame:
        df = self.df
        
        # 1. Basit Hareketli Ortalamalar (SMA)
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # 2. Göreceli Güç Endeksi (RSI)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # 3. Bollinger Bantları
        df['BB_Orta'] = df['Close'].rolling(window=20).mean()
        df['BB_Standart_Sapma'] = df['Close'].rolling(window=20).std()
        df['BB_Ust'] = df['BB_Orta'] + (df['BB_Standart_Sapma'] * 2)
        df['BB_Alt'] = df['BB_Orta'] - (df['BB_Standart_Sapma'] * 2)
        
        # 4. Momentum Göstergesi
        df['Momentum'] = df['Close'] - df['Close'].shift(10)
        
        # 5. Volatilite (ATR)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR_14'] = true_range.rolling(14).mean()
        
        df.dropna(inplace=True)
        return df