# powerapps-barcode-app

Güncel ekran kompozisyonu teslimi: **[Barkod-Uygulamasi-Mobile-Light-v5.msapp](Barkod-Uygulamasi-Mobile-Light-v5.msapp)**.

Home aksiyon kartı, iki yöntemli arama formu, kompakt ürün kartları ve merkezde spinner içerir.
V4'teki 76 davranış formülü, App tanımı, timer'lar ve veri bağlantıları korunmuştur.
Yerel formül/paket kontrolleri başarılıdır; v5 Studio App Checker ve gerçek telefon kabulü bekler.

[V5 kaynak ve komutlar](app-src-mobile-v5/README.md) ·
[Yerleşim önizlemesi](validation/mobile-v5/preview/index.html) ·
[Doğrulama raporu](validation/mobile-v5/REPORT.md).

Önceki, font hataları giderilmiş teslim: **[Barkod-Uygulamasi-Mobile-Light-v4.msapp](Barkod-Uygulamasi-Mobile-Light-v4.msapp)**.

Bu paketin Font formülleri düzeltildi: 53 `.Font` özelliği `Font.'Open Sans'` kullanır.
UI düzeni ve iş mantığı korunmuştur. Değişen dosyalar ve doğrulama kapsamı:
[Font düzeltme raporu](validation/font-fix/REPORT.md). Studio App Checker sonucu henüz doğrulanmadı.

Turuncu/beyaz tasarım, kaydırılabilir auto-layout ekranlar, kompakt ürün kartları,
kart içinde ambar detayları ve Türkçe sayı/rezerve gösterimi içerir. V3.1'deki
70 davranış formülü, OCR şeması ve bağlantılar birebir korunmuştur.
Paket/yükleyici ve yerel formül kontrolleri geçti; fiziksel telefon/Studio kabulü bekliyor.

Kaynak ve komutlar: [v4 kaynak](app-src-mobile-v4/README.md).
Kök nedenler, doğrulama ve canlı kabul: [v4 raporu](validation/mobile-v4/REPORT.md).

Önceki teslim: **[Barkod-Uygulamasi-Mobile-Light-v3-1.msapp](Barkod-Uygulamasi-Mobile-Light-v3-1.msapp)**.

v3 açılış hatası nedeniyle kullanılmamalıdır. v3.1, yeni kontrollerin eksik `Children` listelerini
geri ekler; aynı Microsoft belge yükleyicisinde v3 başarısız, v3.1 başarılıdır.
Kanıt: [açılış onarım raporu](validation/mobile-v3-1/REPORT.md).

Telefon odaklı açık arayüz, sağ üst OCR metni seçimi ve klavyeyle ürün adı/kodu girişi içerir.
Önceki Orange/v2 paketleri yerine bu paketi Power Apps Studio'da açın.
Yerel paket ve formül kontrolleri tamamlandı; bağlı Studio/telefon bulunmadığından canlı kabul ve yayın yapılmadı.

```powershell
python scripts/build_phase3_v2.py --mobile-v3-1
python scripts/validate_mobile_v3.py --mobile-v3-1
python scripts/verify_mobile_v31_repair.py
dotnet run --project scripts/phase3-fxcheck -- validation/mobile-v3-1/fx-input.json
```

Kaynak: [app-src-mobile-v3-1](app-src-mobile-v3-1). Özelliklerin doğrulama kapsamı: [rapor](validation/mobile-v3/REPORT.md).
Çalışan paket `.msapr` snapshot'ından üretilir; yalnızca YAML düzenlemek yeterli değildir.
Değişiklikler `scripts/mobile_v3_fixes.py` üzerinden uygulanır. OCR şemasının kaybolmaması için
`--disable-load-from-yaml` korunur. Eski paketler üzerine yazılmaz.
