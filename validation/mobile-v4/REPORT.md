# Mobile Light v4 — UI/UX refactor

Bu rapor ilk UI refactor doğrulamasını kaydeder. Sonraki yalnızca Font formülü
düzeltmesi, güncel paket özeti ve App Checker sınırı için [Font raporuna](../font-fix/REPORT.md) bakın.

Teslim: [v4 .msapp](../../Barkod-Uygulamasi-Mobile-Light-v4.msapp).
Kaynak: [app-src-mobile-v4](../../app-src-mobile-v4/README.md).

## İnceleme ve nedenler

README'nin güncel olarak işaret ettiği v3.1 incelendi; `app-src` eski sürümdür.
Yerelde önceden değiştirilmiş dosyalar ve v3.1 teslimi korunmuştur.

| Bulgu | Uygulanan düzeltme |
| --- | --- |
| Home CTA `Max(340, Parent.Height - 148)` ile alta sabitleniyordu. | Başlık, açıklama, CTA ve alt bilgi tek dikey akışta. |
| OCR kontrolü 56 px, iç `ButtonHeight` 70 px; yazı 20, ikon 24. | İç/dış yükseklik 48 px; yazı 14, ikon 20; dış çerçeve kaldırıldı. Native fotoğraf aksiyonu korundu. |
| Form kontrolleri sabit Y değerleriyle konumlanıyordu. | Kaydırılabilir dikey form ve yatay geri/başlık konteyneri. |
| Minimum ekran yüksekliği 480 idi; küçük viewport/klavyede ekran görünür alandan büyük kalabiliyordu. | Ekranlar doğrudan App.Width/App.Height kullanıyor; minimum 320×240. İçerik gerektiğinde kayıyor. |
| Sonuçlar ürün + ambar satırlarına düzleştirilmiş, bütün satırlar 112 px idi. | Bir ürün = bir esnek yükseklikli kart. Ambar galerisi kartın içinde, 64 px satırlar ve tek dış kaydırma. |
| Sonuç başlığı 192 px alan tüketiyordu. | 48 px başlık ve outlined arama aksiyonu, 24 px sonuç sayısı. |
| Miktarlar `0.##` ile biçimleniyordu; etiket `Reserve:` idi. | Sayısal Value + açık tr-TR biçimi, gereksiz sıfır yok; Türkçe Rezerve ve boş/sıfır görünürlük kontrolü. |
| Loading öğeleri ayrı merkez hesapları ve büyük aralıklar kullanıyordu. | Ortalanmış, içerik yüksekliğine bağlı kart; açıklama, aranan ürün ve belirsiz ilerleme çubuğu. |

Scale to fit / aspect ratio / orientation kilitleri v3.1'de zaten kapalıydı.
Sorun yalnızca ayar değildi: içerik akışı ve kontrolün iç/dış boyutları tutarsızdı.
Konteyner yaklaşımı Microsoft'un [responsive uygulama rehberine](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/build-responsive-apps)
ve [dikey konteyner belgelerine](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-vertical-container) dayanır.

## Tasarım sistemi

- Primary `#C2410C`, zemin/kart beyaz, ikincil yüzey `#FFF7ED`, nötr yüzey `#F9FAFB`, sınır `#E5E7EB`.
- Ana metin `#1F2937`, ikincil metin `#4B5563`; tüm fontlar Open Sans.
- Home başlığı 26, sayfa başlıkları 18–20, ürün adı 15, gövde/etiket 14, yardımcı metin 12.
- Kenar boşluğu 16, alt iç boşluk 24, aralıklar 8/12/16; düğme/input radius 8, loading kartı 12.
- Input 48 px, ana aksiyonlar 48 px, ikincil arama 44 px. Ürün başlığının tamamı dokunulabilir.
- İçerik genişliği en fazla 600 px; tablet/yatay ekranda metin ve düğmeler aşırı genişlemez.
- Header dışında ekran yüksekliğine bağlı sabit footer yok. Küçük ekranda içerik kaydırılabilir.

Safe area yaklaşımı: host'un verdiği App.Height/App.Width kullanılır; üstte 16 ve
altta 24 px ek pay bırakılır. İşletim sisteminin inset ölçülerini okuyan bir API
varsayılmamıştır. Çentik, klavye ve navigation bar davranışı fiziksel cihazda
ayrıca doğrulanmalıdır.

## İş mantığının korunması

v3.1'de bulunan **70 On* davranış formülünün tamamı birebir aynı**.
OCR Results şeması, bütün References dosyaları ve Header.json bayt düzeyinde aynı.
Flow timer Start/Reset/Duration/Repeat/AutoStart/AutoPause değerleri de aynı.
Tek `barcode_flow.Run` çağrı noktası korunur. Veri ayrıştırma, GroupBy, hata
yönlendirmesi, OCR sağ üst metin seçimi ve manuel giriş önceliği değişmez.

Değişen `galProducts.Items`, yalnızca sunum katmanıdır: mevcut `colProductGroups`
doğrudan kartları besler; `ThisItem.WarehouseRows` açılan detayları besler.
Mevcut expand/collapse değişkenleri ve event formülleri korunur.

Yeni `tmrLoadingVisual` sadece ilerleme çubuğunu hareket ettirir. OnTimerEnd ve
OnTimerStart `false`; hiçbir değişkeni veya akışı değiştirmez, yüzde ilerleme iddiası yoktur.

Mevcut parser null rezerveyi sıfıra dönüştürdüğünden UI null ile gerçek sıfırı
ayırt edemez. Backend'e dokunmamak için ikisi de gizlenir; sıfır dışındaki rezerve
değerler kullanılabilir miktardan bağımsız gösterilir.

## Doğrulama

- PAC SourceCode pack ve bağımsız unpack: PASS; snapshot roundtrip bayt eşitliği.
- Microsoft belge yükleyicisi (`pac canvas unpack --layout Experimental`): PASS.
  Experimental çıktı yalnızca okunur, yeniden paketlenmez.
- YAML/runtime formül ve hiyerarşi eşliği: PASS.
- 3.093 Power Fx formülü: sıfır parse hatası.
- 197 çalıştırılabilir kontrol: PASS. OCR/manuel/dispatch regresyonları, sayısal
  formatlar, boş rezerve, 10 viewport genişliği ve açılmış/kapalı ambar yükseklikleri.
- `030 → 30`, `01 → 1`, `12.5 → 12,5`, negatif ve büyük sayılar doğrulandı.
- Kontrol kimlikleri benzersiz, bütün kontrollerde Children listesi var;
  konteynerlerin çocuk sırası ve ZIndex değerleri uyumlu.

Kanıtlar: [paket](validation.json), [yükleyici](document-load.json),
[yapısal kontroller](static-checks.json), [Power Fx çıktısı](powerfx-results.txt).

Bu testler gerçek Canvas render'ı veya tenant App Checker type/binding kontrolü
değildir. Tarayıcı envanteri `apps: [], browsers: []` döndürdü; bağlı Studio veya
fiziksel telefon yok. Canlı import, kamera, Flow ve telefon kabulü yapılmış gibi
raporlanmaz. Özellikle esnek galeri yeniden ölçümü ve native OCR düğmesi cihazda
görsel olarak doğrulanmalıdır.

## Canlı kabul adımları

1. V4 paketini Studio'da ayrı uygulama olarak açın; App Checker'da yeni hata olmadığını doğrulayın.
2. Aynı sürümü fiziksel telefonda açın; 320/360/390/430 genişlik, yatay yön ve klavye açık hallerinde header/form erişimini kontrol edin.
3. Home → manuel ürün → loading → sonuç; aynı akışı fotoğrafla tekrarlayın. Bir kabul edilen arama için tek Flow çağrısı olmalı.
4. 17 ürünlü sonuçta ilk/orta/son kartları açıp kapatın; uzun ürün adı, 0/1/çok ambar ve rezerve değerlerini kontrol edin.
5. Boş sonuç, bağlantı hatası ve yeniden aramayı kontrol edin; status/navigation bar altında kontrol kalmamalı.

## Yeniden üretim

```powershell
python scripts/build_phase3_v2.py --mobile-v4
python scripts/validate_mobile_v4.py
dotnet run --project scripts/phase3-fxcheck -- validation/mobile-v4/fx-input.json
```
