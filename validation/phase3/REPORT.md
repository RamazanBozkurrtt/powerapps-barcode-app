# Phase 3 doğrulama raporu

Durum: **Kaynak ve paket kontrolleri geçti; canlı kabul testi bekliyor.** Bağlı uygulama/tarayıcı envanteri boş döndü. Power Apps Studio/App Checker, gerçek OCR, Flow istek sayısı ve mobil görsel doğrulama bu ortamda çalıştırılamadı. Bu nedenle tüm kabul kriterlerinin canlı ortamda geçtiği iddia edilmiyor.

## Temel sürüm ve korunmuş akış

`app-src` eski tanılama formülleri içerdiğinden temel olarak `Barkod-Uygulamasi-Phase2-FIXED-v2.msapp` kullanıldı. Yeni tam kaynak `app-src-phase3` altında; mevcut kullanıcı değişiklikleri ve önceki paketler korunmuştur.

Power Apps → TextRecognizer → mevcut `barcode_flow.Run(varAcceptedText)` → mevcut JSON işleme → sonuç ekranı devam ediyor. `GroupBy(colParsedRows, ItemNumber, WarehouseRows)`, ürün adı çelişkisi kontrolü, sayısal dönüşümlerdeki Coalesce ve bağlantı/JSON hata yolları değişmedi. References, Properties ve Header paket içerikleri temel sürümle aynı. Backend, Power Automate ve D365 değiştirilmedi.

## OCR otomatik seçim

Paketin sağlıklı şemasından `Results` tablosu; `Text`, `PageNumber`, `BoundingBox.Top/Left/Height/Width` alanları doğrulandı. Metadata'nın tamamı byte/nesne karşılaştırmasıyla korundu.

`TextRecognizer1.OnChange` içinde:

1. Boş/yalnız boşluk içeren metinler ve Top değeri boş ya da negatif olan satırlar elenir; sıfır koordinatı geçerlidir.
2. AddColumns ile `OcrTop`, `OcrPage`, `OcrLeft` oluşturulur.
3. `SortByColumns(..., "OcrTop", SortOrder.Ascending, "OcrPage", SortOrder.Ascending, "OcrLeft", SortOrder.Ascending, "Text", SortOrder.Ascending)` uygulanır.
4. `Set(varAcceptedText, TrimEnds(First(candidates).Text))` yapılır, kabul kilidi alınır ve `scrLoading` açılır.

Top birincil sıralama anahtarıdır. Eşit Top için sayfa, sol koordinat ve metin sırası kullanılır. Tüm anahtarlar aynıysa kabul edilen metin zaten aynıdır. Ürün adına regex/uzunluk filtresi uygulanmaz. Aday bulunamazsa kabul edilen metin temizlenir, ekranda uyarı ve Notify gösterilir; yükleme ekranına gidilmez. IfError OCR çıktı işleme hatasını yakalar.

`btnContinueWithSelectedProduct` çalışma zamanı ağacından ve YAML'dan kaldırıldı. `TextRecognizer1.Selected` kullanan hiçbir formül kalmadı. Seçim kutuları `ShowBoundingBoxes=false` ile kapatıldı; açıklamalar otomatik akışı anlatıyor.

Scan girişinde eski metin/kilitler temizlenir ve TextRecognizer resetlenir. OCR işlemi aktif ekran Scan olduğunda ve kabul/Flow kilitleri kapalıyken yürür. `varScanAccepted` Navigate'den önce true olur. Flow yalnız yükleme zamanlayıcısındadır. Zamanlayıcı kabul edilmiş boş olmayan metin ve kapalı iki yürütme kilidi ister; kilitler `.Run` öncesi alınır. Loading.OnVisible artık kilidi sıfırlamaz. Kaynakta tam **bir Flow çağrı noktası** vardır. Canlı olay zamanlaması ve ağda tek çağrı kontrolü henüz bekliyor.

## Sonuç ekranı

- Beyaz arka plan; turuncu `#C2410C` vurgu; açık turuncu `#FFF7ED` reserve yüzeyi; koyu gri metinler. Ana sayfa, tarama, yükleme ve hata ekranlarının mavi vurguları da aynı palete alındı.
- “Depo Stokları”, altında gerçek ürün adedi, ardından geniş 56 birim yüksekliğinde “Yeniden Tara” düğmesi. Düğme başlıkla çakışmaz.
- Küçük ürün kartları: ürün adı, ItemNumber, benzersiz ambar sayısı ve +/− açma işareti. Uzun ürün adları AutoHeight ile büyür.
- `varExpandedItemNumber`, Results.OnVisible'da Blank olur. Karta veya başlık/alt başlık/+ alanına dokunmak aynı ürünü kapatır, farklı ürünü tek açık ürün yapar. Düğmenin erişilebilir açıklaması açık/kapalı durumunu belirtir.
- Dış galeri esnek yüksekliktedir (`AutoHeight=true`). Her kartın yüksekliği kendi alt galerisinin konum/yüksekliğinden hesaplanır. Kapalı alt galeri yüksekliği sıfırdır; bütün kartlara aynı genişleme yüksekliği verilmez.
- Ambarlar 80 birim satırlarda solda; stok sağa hizalı, 22 punto ve kalın. Sol alan %57, sağ miktar alanı %39; arada %4 boşluk vardır. Tekrarlayan “Kullanılabilir” yazısı gizlendi. Ayırıcı çizgiler korunur.
- Ambar listesi en fazla 400 birim büyür; beşten fazla satır iç galeride kaydırılır. Dış galeri ürünler arasında kaydırılır.
- Reserve rozeti yalnız `AvailableOnHandQuantity < 3 && ReservedOnHandQuantity <> 0` olduğunda “Reserve: n” gösterir. Ürün adı çelişkisi uyarısı açık kartta korunur.

## Yapılan kontroller

| Kontrol | Sonuç |
| --- | --- |
| PAC SourceCode pack, YAML yüklemesi kapalı | PASS |
| Yeni dizine PAC unpack ve snapshot içerik karşılaştırması | PASS |
| Sağlıklı TextRecognizer Template metadata'sı | Değişmedi |
| Backend bağlantıları, Flow parse/group/error gövdesi | Değişmedi |
| Manuel seçim formül referansı | 0 |
| Flow çağrı noktası | 1 |
| Microsoft Power Fx parser, invariant kültür, 2.389 runtime formülü | 0 sözdizimi hatası |
| Power Fx interpreter: paketten alınan gerçek sıralama ifadesi | 9/9 PASS |
| Studio tip/bağlama kontrolü ve gerçek UI/OCR/Flow | Çalıştırılamadı |

Dokuz OCR testi: karışık sıra, ters sıra, boşluk metni, eşit Top/sol konum farkı, eşit konum/metin farkı, boş-negatif Top, boş tablo, yalnız geçersiz adaylar, farklı sayfalarda Top önceliği. Bunlar gerçek Power Fx ifadeleriyle sentetik satırlarda çalıştırıldı; AI Builder çağrısı değildir. Parser testi de Studio'nun kontrol/connector bağlama kontrolünün yerini tutmaz. Eski AppCheckerResult.sarif yeni test sonucu olarak kullanılmadı.

Kanıtlar: `pack.json`, `roundtrip.json`, `validation.json`, `powerfx-results.txt`, `fx-input.json`. Paket SHA-256 ve boyutu `validation.json` içindedir.

## Dosyalar

Yeni kaynak dosyaları:

- `app-src-phase3/Src/App.pa.yaml`: çalışan başlangıç koleksiyonu ve accordion state başlangıcı.
- `app-src-phase3/Src/scrScan.pa.yaml`: otomatik OCR, hata/boş sonuç ve manuel seçimin kaldırılması.
- `app-src-phase3/Src/scrLoading.pa.yaml`: tek çağrı kilitleri, korunmuş stok işleme.
- `app-src-phase3/Src/scrResults.pa.yaml`: accordion, ürün/ambar satırları ve açık tema.
- `app-src-phase3/Src/scrHome.pa.yaml`, `scrError.pa.yaml`: ortak turuncu palet.
- `app-src-phase3/*.msapr`: aynı runtime formülleri ve sağlıklı metadata.
- `app-src-phase3/README.md`: doğru paketleme yolu ve kaynak uyarısı.
- `scripts/build_phase3.py`: tekrar üretilebilir build ve paket karşılaştırmaları.
- `scripts/phase3-fxcheck/`: yerel PAC Power Fx kütüphaneleriyle parser/interpreter kontrolü.
- `Barkod-Uygulamasi-Phase3-Orange.msapp`: yeni paket.

Önceki `app-src` üzerine yazılmadı. `_EditorState.pa.yaml` ve backend içerikleri temel paketinden taşındı.

## Studio'da kalan kabul testi

Paketi içe aktarıp App Checker çalıştırın; farklı sıralı çok satırlı görselde fiziksel en üst metnin seçildiğini, hiçbir kutuya dokunmadan sonuca geçildiğini ve Monitor'da tek barcode_flow çağrısı olduğunu doğrulayın. Boş görsel, yeniden tarama, bağlantı hatası, aynı görseli tekrar tarama, iki ürün arasında aç/kapat, beşten fazla ambar, uzun başlık/kod ve reserve sınırlarını (2/3 stok ve 0/pozitif reserve) gerçek mobil Player'da kontrol edin. Bu oturumda referans ekran görüntüsü sağlanmadı; gerçek ekranın görsel karşılaştırması yapılmadı.

Alanların anlamı için [Microsoft Text Recognizer belgesi](https://learn.microsoft.com/en-us/ai-builder/prebuilt-text-recognizer-component-in-powerapps); içerikle büyüyen galeri yaklaşımı için [Microsoft esnek galeri belgesi](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/gallery-dynamic-sizing) kullanıldı. Kesin OCR alan adları uygulamanın kendi sağlıklı şemasından alındı.
