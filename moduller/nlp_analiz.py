import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

class NLPAnalizor:
    """
    FinBERT modelini kullanarak finansal metinlerin ve haberlerin
    duygu analizini (Sentiment Analysis) yapan sınıf.
    """
    def __init__(self):
        print("🤖 FinBERT Yapay Zeka Modeli yükleniyor (İlk çalıştırmada biraz sürebilir)...")
        # Finansal analiz için eğitilmiş ProsusAI/finbert modelini çağırıyoruz
        self.model_adi = "ProsusAI/finbert"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_adi)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_adi)
        print("✅ FinBERT başarıyla yüklendi ve kullanıma hazır.")

    def duygu_analizi_yap(self, metin: str) -> dict:
        """
        Verilen İngilizce finansal metnin olumlu, olumsuz ve nötr olasılıklarını hesaplar.
        """
        # Hata Önleme: Eğer metin boşsa veya None ise doğrudan nötr döndür
        if not metin or not isinstance(metin, str) or metin.strip() == "":
            return {
                "Olumlu": 0.0,
                "Olumsuz": 0.0,
                "Notr": 1.0,
                "Baskin_Duygu": "Notr",
                "Net_Skor": 0.0
            }

        # Metni yapay zekanın anlayacağı sayılara (token) dönüştür
        girdiler = self.tokenizer(metin, padding=True, truncation=True, return_tensors='pt')
        
        # Modeli çalıştır (Gradyan hesaplamayı kapatarak hızı arttırıyoruz)
        with torch.no_grad():
            çıktılar = self.model(**girdiler)
        
        # Çıkan ham skorları olasılık yüzdelerine (Softmax yardımıyla) çevir
        olasiliklar = F.softmax(çıktılar.logits, dim=-1).numpy()[0]
        
        # Sonuçları etiketleriyle eşleştir
        sonuc = {
            "Olumlu": round(olasiliklar[0], 4),
            "Olumsuz": round(olasiliklar[1], 4),
            "Notr": round(olasiliklar[2], 4)
        }
        
        # Baskın olan duyguyu ve skorunu belirle
        en_yuksek_duygu = max(sonuc, key=sonuc.get)
        sonuc["Baskin_Duygu"] = en_yuksek_duygu
        # Net Duygu Skoru
        sonuc["Net_Skor"] = round(sonuc["Olumlu"] - sonuc["Olumsuz"], 4)
        
        return sonuc