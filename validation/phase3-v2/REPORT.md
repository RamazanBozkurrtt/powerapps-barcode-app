# Phase 3 v2 — düzeltme ve doğrulama

Çıktı: `Barkod-Uygulamasi-Phase3-Orange-v2.msapp`.

Kaynak/paket/regresyon kontrolleri geçti. **Canlı Player/Studio doğrulaması yapılmadı:** bu oturumdaki bilgisayar aracı `apps=[]`, `browsers=[]` döndürdü. Kullanıcının hatası alındı; önceki rapordaki paket/parser PASS sonuçlarının gerçek arayüz kabul testi olmadığı dikkate alındı.

## Üst üste binen, basılmayan kartlar

Önceki kaynakta dış galerinin `TemplateSize=1` olması, yüksek kartlarla birlikte kullanılıyordu. Ayrıca yeni +/− etiketi, diğer galeri çocuklarından farklı olarak boş galleryTemplate düğümünün içine eklenmişti. Bunlar bu düzeltmede kaldırıldı; canlı ekran olmadan sorunun tek nedeninin bunlar olduğu ileri sürülmüyor.

Yeni yapı **tek standart dikey galeri** kullanır: `TemplateSize=112`, `TemplatePadding=8`, `AutoHeight=false`. Ürün başlıkları ve açık ürünün ambarları aynı galeride ayrı gerçek satırlar olarak gösterilir. İç içe galeri ve değişken şablon yüksekliği yoktur. Böylece satırların yerleşimi içerik ölçüm olaylarına bağlı değildir; tüm kontroller 112 birimlik satır sınırı içinde kalır. Tek kaydırma alanı vardır.

Canonical `colProductGroups` hâlâ ItemNumber'a göre gruplanmıştır. `galProducts.Items`, bu koleksiyondan yalnız görüntüleme için `IsProduct` başlık/ambar satırlarını üretir. `varProductExpanded` açık/kapalı durumunu, `varExpandedItemNumber` açık ürünü tutar. Boş ItemNumber da başlangıçtaki Blank state ile yanlışlıkla açık sayılmaz. Başka ürüne basmak öncekinin detaylarını kaldırır. Aynı ürüne basmak kapatır.

Başlığın tamamında `btnProductToggle` isimli tek, şeffaf, klavyeyle erişilebilir ve en üst katmanda bir düğme vardır. OnSelect doğrudan state değiştirir; başka düğmeye `Select()` yönlendirmesi gerekmez. Ambar satırlarında bu tıklama katmanı görünmez. Sayılar sağda, ambar solda; reserve koşulu aynıdır.

## Tarama ekranına giriş / Flow

`scrScan.OnVisible` önce `varScanReady=false` yapar, tüm istek/kabul state'lerini temizler ve giriş anındaki `OriginalImage` değerini kaydeder. Reset bu kapalı durumda yapılır. OCR OnChange, yalnız şu koşullarla metni kabul edebilir:

- Scan ekranı aktif ve reset bölümü bitmiş olmalı.
- Kabul/Flow kilitleri kapalı olmalı.
- OriginalImage boş olmamalı ve ekran girişinde kaydedilen görselden farklı olmalı.

Reset'in boş görsel olayı uyarı ya da Navigate üretmez; eski görsel tabanını temizler. Böylece reset sonrasında aynı dosya tekrar seçilebilir. Sıralama hâlâ Top → Page → Left → Text; manuel ürün seçimi yoktur.

Zamanlayıcı `AutoStart=false`, `Repeat=false`, `AutoPause=true` kullanır. `Start` ve `OnTimerEnd` aynı koşulu taşır:

```powerfx
App.ActiveScreen = scrLoading &&
varScanAccepted && !IsBlank(varAcceptedText) &&
!varFlowCallStarted && !varLoadingExecutionStarted
```

Loading dışındayken timer resetlenir. Çağrı kilitleri mevcut tek `.Run()` öncesinde alınır. Home/Scan giriş formüllerinde Flow çağrısı yoktur. Flow yanıtını parse eden, ItemNumber gruplarını kuran ve hata ekranına yönlendiren gövde temel sürümle birebir karşılaştırıldı.

**Erişim isteği ayrımı:** Kullanıcının gördüğü isteğin Monitor kaydı bu oturumda yok. TextRecognizer'ın AI Builder model bağlantısını başlatması veya Power Apps'in connector izin istemesi, `barcode_flow.Run` çalışmasıyla aynı şey değildir. Bu değişiklik erken stok Flow çağrısına karşı koruma sağlar; platformun bağlantı izin ekranını bastırdığı iddia edilmiyor. AI Builder şemasını bozabilecek LoadSchema/metadata değişikliği yapılmadı.

## Beyaz yüzeyler

Tüm modern düğmeler, renkleri her durumda açıkça tanımlanan klasik düğmelere çevrildi. Kaynağın ModernThemes girdisinde açık renk paleti tanımı bulunmadığı için yüzeylerin bu varsayımlara bağlı kalması kaldırıldı. Ekran, kart ve disabled yüzeyleri beyaz; eylem düğmeleri turuncu; hover/pressed durumları da açıkça tanımlı. Yazılar okunabilir koyu gri, turuncu düğme yazıları beyazdır.

TextRecognizer'ın dahili resim önizlemesi `ImageDisplayed=false` ile kapatıldı; siyah görüntü alanı yerine beyaz yüzeyde görsel seçme düğmesi vardır. OCR ve görsel seçme işlevi korunur. Ana ekranın eski mavi arka plan vurgusu da beyazdır.

Klasik düğmenin yalnız adı eklenmedi: Microsoft'un kendi örnek deposundan alınan gerçek `button_2.2.0.xml` tanımı `References/Templates.json` içine paketlendi. Kaynak ve tree SHA bilgisi `scripts/button-template-origin.json` içindedir. Backend DataSources ve diğer bağlantı referansları aynıdır; yalnız UI template referansı genişletildi.

## Doğrulama sonuçları

| Kontrol | Sonuç |
| --- | --- |
| PAC pack + taze klasöre unpack + snapshot eşitliği | PASS |
| OCR Template metadata'sı | Değişmedi |
| Backend referansları ve Flow parse/group/error gövdesi | Değişmedi |
| Tek galeri, doğru parent/child ilişkisi, benzersiz kontrol kimlikleri | PASS |
| Bütün satır çocukları Y + Height ≤ 112 | PASS |
| Header hit target: en üst ZIndex, Edit, TabIndex=0 | PASS |
| Button template paket içinde, beyaz ekranlar, modern düğme kalmadı | PASS |
| Power Fx parser: 2.389 gerçek paket formülü | 0 sözdizimi hatası |
| OCR Top sıralaması | 9/9 PASS |
| Timer dispatch koşulu: 32 durum kombinasyonu | 32/32 PASS |
| Yeni/eski/boş görsel, reset, tekrar olay, ekran dışı olay | 7/7 PASS |
| Reserve görünürlüğü sınırları | 4/4 PASS |

Toplam **52 Power Fx senaryosu geçti**. Koşullar paket içindeki gerçek formüllerden alınıp sentetik girdilerle çalıştırıldı. Bu testler AI Builder ağ çağrısı veya gerçek olay zamanlaması testi değildir.

Dört tam accordion veri çıktısı senaryosu ayrıca `fx-input.json.studio_cases` içinde tutuldu. Standalone Microsoft Power Fx interpreter, Canvas'ta bulunan `Ungroup` fonksiyonunu desteklemediğinden bunlara PASS verilmedi. Gerçek tıklama, aç/kapat ve mobil görüntü kontrolleri Studio/Player'da bekliyor. Tarihsel AppCheckerResult.sarif veya Properties.BindingErrorCount yeni Studio kontrolü sayılmadı.

## Dosyalar ve tekrar çalıştırma

- `app-src-phase3-v2/Src/scrResults.pa.yaml`: tek galeri ve gerçek satırlar; başlık tıklama alanı.
- `app-src-phase3-v2/Src/scrScan.pa.yaml`: yeni görsel kontrolü, reset koruması, beyaz tarama alanı.
- `app-src-phase3-v2/Src/scrLoading.pa.yaml`: açık timer Start/Reset ve ekran kontrolü.
- `app-src-phase3-v2/Src/App.pa.yaml`: yeni state başlangıçları.
- `scrHome.pa.yaml`, `scrError.pa.yaml`: beyaz yüzeyler/klasik düğmeler.
- `app-src-phase3-v2/*.msapr`: runtime kaynak, metadata ve klasik button template.
- `scripts/build_phase3_v2.py`, `phase3_v2_fixes.py`: yeni paket üretimi.
- `scripts/validate_phase3_v2.py`, `scripts/phase3-fxcheck/Program.cs`: paket yapısı ve Power Fx regresyonları.
- `validation/phase3-v2/`: komut çıktıları, testler, hash/boyut bilgisi ve bu rapor.

```powershell
python scripts/build_phase3_v2.py
python scripts/validate_phase3_v2.py
dotnet run --project scripts/phase3-fxcheck -- validation/phase3-v2/fx-input.json
```

Canlı kabul: Home → Scan girişinde barcode_flow çağrısı olmadığını Monitor'da; yeni/same-file görselde tek çağrıyı; iki ürün arasında aç/kapatı; beşten fazla ambarın tek kaydırmayla erişilebilirliğini ve beyaz yüzeylerin cihazda görünümünü doğrulayın.

Referanslar: [Microsoft galeri kontrolü](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/control-gallery), [Microsoft Text Recognizer](https://learn.microsoft.com/en-us/ai-builder/prebuilt-text-recognizer-component-in-powerapps), [Microsoft klasik düğme template kaynağı](https://github.com/microsoft/teams-powerapps-app-templates/blob/main/Inspection/DataverseSolution/CanvasApps/msft_reviewinspections_1dd45_DocumentUri_src/pkgs/button_2.2.0.xml).
