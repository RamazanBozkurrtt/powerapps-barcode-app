# V5 — Ekran kompozisyonu

Teslim: [Barkod-Uygulamasi-Mobile-Light-v5.msapp](../../Barkod-Uygulamasi-Mobile-Light-v5.msapp).
Temel: kullanıcının Formula hatalarının giderildiğini doğruladığı v4 paketi.
V4 SHA-256: `609ccadfd0de010f92228e6bb46a9709060a2ceca6af055d3b77d7a2e78ca579`.

## Kompozisyon

- **Home:** tek kontrol listesi yerine başlık/açıklama grubu, bağımsız beyaz aksiyon kartı
  ve kısa yardımcı bilgi. Başlık sola hizalı ve iki satırdır. Üst boşluk içerik yüksekliğiyle
  hesaplanır, 24–88 px aralığında sınırlandırılır; ekranı doldurmak için boş kontrol eklenmez.
- **Scan:** geri/başlık satırı ve kısa açıklamadan sonra form kartı. Fotoğraf yöntemi yumuşak
  turuncu yüzeyde, native OCR aksiyonu beyaz ve turuncu çerçevelidir. `ya da` ayırıcısının
  altında etiket, input ve dolgulu `Stok sorgula` düğmesi bulunur. Boş girişte disabled
  düğme gri dolgulu görünür; mevcut etkinleştirme formülü aynen korunur.
- **Results:** kapalı ürün kartı tek satırlık ad için 76 px + 8 px galeri aralığıdır.
  Ürün adı, ürün kodu ve sağa hizalı ambar sayısı ayrıdır. Uzun ürün adı kartı büyütür.
  Açılan kartta ambar ve kullanılabilir stok iki sütundadır; satırlar 52 px, rezerve
  miktarı stok sayısının altında ikincil bilgidir. Veri ayrıştırma ve sayısal formatlama korunur.
- **Loading:** merkezde içeriği kadar büyüyen kart, 48 px spinner, başlık ve ayrı aranan
  ürün etiketi/değeri. Spinner mevcut `tmrLoadingVisual.Value` değerini yalnızca okur.
  Yeni değişken, timer veya Flow çağrısı yoktur.
- **Error:** aynı kart, padding, tipografi ve aksiyon stilleri. Hata mesajı ve retry/home
  davranışları korunur.

## Tasarım ve responsive davranış

Tek native font: `Font.'Open Sans'`. Sayfa başlığı 20–28 pt, bölüm başlığı 17–19 pt,
gövde/label 14–15 pt; yardımcı bilgi 12–13 pt. Turuncu `#C2410C`, beyaz kartlar,
açık nötr zemin, 12–16 px köşe yarıçapı ve ince sınır kullanılır; gradient/dark mode yoktur.

Kök içerik alanı maksimum 560 px genişliğinde ortalanır; yatay padding 20 px'tir.
Ana yerleşim auto-layout container'larla yapılır. Kart yüksekliği çocukların gerçek
yüksekliğinden hesaplanır; sarılan metinler yer açar. Home/Scan/Error üst boşlukları
sınırlıdır. Küçük ekran, yatay yön ve klavye yüksekliğinde dış container kaydırılır.
İç içe ambar listesinde ayrı scroll yoktur; sonuçlar tek galeri üzerinden kaydırılır.

Galeri şablonundaki koordinatlar ebeveyn genişliği ve önceki içeriğin yüksekliğine
bağlıdır. Galerinin iç yerleşim gereksinimi Microsoft'un
[responsive layout rehberinde](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/create-responsive-layout)
belirtilir. Diğer ekranlarda çocukların konumunu
[dikey container](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-vertical-container)
yönetir.

## İş mantığının korunması

- V4'teki **76 On* davranış formülü birebir aynı**.
- App tanımı, `tmrLoadingFlow` ve `tmrLoadingVisual` kontrol verileri birebir aynı.
- Mevcut kontrol şablonları, OCR dinamik şeması, data kaynakları, bağlantılar ve Header aynı.
- Items, Default, DisplayMode ve timer Start/Reset/Duration/Repeat formülleri korunur.
- Navigation, OCR seçimi, Flow çağrısı, collections, variables ve stok sorgusu değiştirilmez.
- Değişen dinamik Text ifadeleri yalnızca sunum amaçlıdır: ürün kodu ile ambar sayısını
  ayırır; yüklemede aranan ürünü ayrı satırda gösterir; arama yardım metnini kısaltır.
- `References/Templates.json` dosyasına yalnızca Microsoft'un image 2.2.0 şablonu eklenir.
  Kaynak/provenance: [image-template-origin.json](../../scripts/image-template-origin.json).

## Doğrulama

| Kontrol | Sonuç |
| --- | --- |
| 3.636 runtime Power Fx formülü | 0 parse hatası |
| 229 çalıştırılabilir kontrol | PASS |
| 699 kontrol/property referansı ve kullanılan UI enum üyeleri | PASS |
| Bütün Font formülleri; geçersiz `OpenSans` | 0 geçersiz kullanım |
| YAML/runtime formülleri ve kontrol hiyerarşisi | Aynı |
| PAC SourceCode pack/unpack | PASS; snapshot roundtrip bayt eşliği |
| Microsoft belge yükleyicisi, Experimental salt okunur unpack | PASS |
| 42 paket kaynaklı yerleşim simülasyonu | Yatay taşma yok |
| 6 viewport'ta boş/whitespace input, enabled düğme ve scroll erişimi | PASS |
| V5 canlı Studio App Checker | **Çalıştırılmadı** |
| Gerçek telefonda Power Apps uygulaması | **Test edilmedi** |

Formül referans denetimi, kullanılan enum üyelerini ve kontrol property isimlerini
kontrol eder; Canvas host'un tüm type/binding/delegation davranışlarını taklit etmez.
Bu nedenle **`App Checker Formula errors = 0` ve gerçek telefon görünümü kabulü
henüz tamamlanmış değildir**. Yerel test başarısı canlı kabul yerine raporlanmaz.

Kanıtlar: [build.json](build.json), [statik kontroller](static-checks.json),
[Power Fx çıktısı](powerfx-results.txt), [pack](pack.json), [roundtrip](roundtrip.json),
[belge yükleyicisi](document-load.json), [yerleşim kontrolleri](preview/layout-checks.json).
Güncel paket SHA-256 değeri `build.json` içindedir.

## Görsel inceleme

[Etkileşimli yerleşim önizlemesini açın](preview/index.html). Bu yerel HTML, v5 paketinin
kontrol ağacını ve görsel formüllerini kullanır; örnek stok verileriyle çalışır.
OCR/kamera/Flow çağırmaz. Metin ölçümü Edge/Open Sans üzerinden yapılır; native Power Apps
render farkları, işletim sistemi safe area'sı ve gerçek klavye davranışı burada ölçülmez.

320×568, 360×640, 390×844, 430×932, 844×390 ve 390×240 viewport'ları kontrol edildi.
Sonuçlarda 17 ürün, ilk kart açık ve uzun ürün adı durumları incelendi. Küçük ekranda
başlık ve secondary düğme taşmaları inceleme sırasında giderildi. Klavye yüksekliği
simülasyonunda form aşağı kaydırılarak `Stok sorgula` düğmesine erişim doğrulandı.

- [Home 390×844](preview/scrHome-390x844-default.png)
- [Scan 390×844](preview/scrScan-390x844-default.png)
- [Sonuç kartları](preview/scrResults-390x844-default.png)
- [Açık ürün kartı](preview/scrResults-390x844-expanded.png)
- [Loading](preview/scrLoading-390x844-default.png)
- [Error](preview/scrError-390x844-default.png)
- [Klavye yüksekliğinde manuel arama](preview/scrScan-390x240-manual-ready.png)

## Canlı kabul için kalan adım

1. V5 paketini Power Apps Studio'da açın; App Checker → Formulas sayısının **0** olduğunu doğrulayın.
2. Gerçek telefonda Home ve Scan kartlarının yerleşimini, geri/arama aksiyonlarını ve klavye açıldığında scroll erişimini kontrol edin.
3. Fotoğraf ve manuel aramayla aynı sorguyu çalıştırın; loading, sonuç ve hata durumlarını görün.
4. 17 ürünlü sonuçta kapalı/açık kartları, uzun adları, ambar miktarlarını ve rezerve satırını kontrol edin.

Bağlı Studio veya test telefonu olmadığı için bu dört adım bu oturumda tamamlanmadı;
uygulama yayınlanmadı.

## Dosyalar ve yeniden üretim

Yeni uygulama/snapshot ve beş ekran: `Barkod-Uygulamasi-Mobile-Light-v5.msapp`, `app-src-mobile-v5`.
Üretici: `scripts/build_mobile_v5.py`, `scripts/mobile_v5_composition.py`.
Doğrulama: `scripts/validate_mobile_v5.py`.
Önizleme: `scripts/preview_mobile_v5.py`, `scripts/mobile_v5_preview.html`, `scripts/mobile_v5_preview.js`.
Image kontrol şablonu: `scripts/image_2.2.0.xml` ve kaynak kaydı.
Rapor/kanıtlar: `validation/mobile-v5`. Kök README güncel teslimi v5 olarak gösterir.

```powershell
python scripts/build_mobile_v5.py
python scripts/validate_mobile_v5.py
python scripts/preview_mobile_v5.py
```

Bu çalışma alanında Power Fx kontrolleri taşınabilir .NET ile çalıştırıldı:

```powershell
& 'build/font-tools/dotnet/dotnet.exe' 'build/font-tools/check/bin/Debug/net10.0/check.dll' validation/mobile-v5/fx-input.json
```
