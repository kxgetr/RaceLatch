# RaceLatch

İşaretlenmiş thread geçişlerini arar ve hatalı sırayı yeniden yürütür.

## Kullanım

Python 3.11+.

```sh
python racelatch.py counter.py --out race.json
python racelatch.py counter.py --replay race.json
```

Senaryo dosyası scenario(checkpoint) içinde her çağrıda yeni durum, isim → thread fonksiyonu sözlüğü ve son durum kontrol fonksiyonu döndürür. Paylaşılan değişkenlere erişirken checkpoint("etiket") çağır. Her adımda tek thread ilerler. Bloklayan G/Ç veya başka bir thread bekleyen kilitler bu modele uygun değildir. --budget ve --depth aramayı sınırlar. 0 arama tamamlandı, 1 hata bulundu veya yeniden üretildi, 2 sonuç eksik anlamına gelir.

## Uçtan uca doğrulama

```sh
python verify.py
```

MIT lisansı.
