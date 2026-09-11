# Mobile Light v3 — yerel doğrulama

**GEÇERSİZ TESLİM:** Kullanıcı v3 için `ErrOpeningDocument_UnknownError` bildirdi.
Eksik `Children` listeleri Microsoft belge yükleyicisinde çökme üretiyor.
Bu rapordaki paket/roundtrip testleri açılış kabulü değildir. Düzeltilmiş teslim ve
negatif/pozitif yükleme kanıtları [v3.1 raporundadır](../mobile-v3-1/REPORT.md).

Teslim: [Barkod-Uygulamasi-Mobile-Light-v3.msapp](../../Barkod-Uygulamasi-Mobile-Light-v3.msapp).
Bu paket önceki Orange/v2 tesliminin yerine kullanılmalıdır. Mevcut canlı uygulama bu oturumda değiştirilmedi veya yayımlanmadı.

## Bulgular ve düzeltmeler

| İstek | Kaynakta bulunan durum | Yeni davranış |
| --- | --- | --- |
| Sağ üst metin | Top artan, Left artan sıralama soldakini tercih ediyordu. | İlk sayfanın en üst satırında sağ kenarı en ileride olan metin seçilir. Üst kutunun yarım yüksekliği kadar düşey kayma aynı satır sayılır; alt satırdaki sağ metin üst satırı geçmez. |
| Gereksiz OCR hatası | Boş sonuç anında Notify üretiyordu; Top koordinatı eksik okunabilir metinler tamamen eleniyordu. | Boş sonuç navigasyon veya uyarı üretmez; sonraki sonuç işlenebilir. Konumu olmayan okunabilir metinler yedek olarak korunur. Gerçek formül/çıktı hatası ekran içinde, manuel giriş seçeneğiyle gösterilir. |
| Telefon ekranı | ScaleToFit=true, MaintainAspectRatio=true, 640px minimum genişlik ve 1136px tasarıma göre sabit yerleşimler vardı. | Ölçekleme ve oran kilidi kapalı; minimum genişlik 320px. Beş ekranın yerleşimi telefon için yeniden düzenlendi. Beyaz ekran zemini tüm alanı doldurur. |
| Açık arayüz | Önceki v2 yerel paketinde ekran dolguları zaten beyazdı; telefonda görülen koyuluğun yayımlanan sürüm/oynatıcıdaki kaynağı bağlı cihaz olmadan kesinleştirilemedi. | Görünen yüzeyler, metinler ve etkin/pasif/üzerine gelme/basılma durumları açık zemin ve kontrastlı renklerle açıkça tanımlı. Modern düğme bağımlılığı yok. |
| Klavyeyle giriş | Önceki üretim betiği manuel devam kontrolünü kaldırıyordu. | Gerçek Classic/TextInput ile ürün adı/kodu girişi, boş girişte pasif “Stok sorgula” düğmesi. Yazılmış metin OCR'dan öncelikli; baş/son boşluklar temizlenir. |

OCR değişim olayının cihazda tam hangi anda geldiği bu oturumda gözlenmedi. Dolayısıyla boş sonuç uyarısının kaynakta koşulsuz üretildiği kesindir; cihazdaki olay zamanlaması için bir runtime tespiti iddia edilmez. Metinsiz fotoğraf için kesin hata zamanı uydurulmaz: metin gelmezse kullanıcı tekrar görüntü seçebilir veya ürün adını yazabilir.

## Geçen kontroller

- PAC ile paketleme ve bağımsız yeniden unpack: PASS. Yeniden açılan snapshot paket içeriğiyle bayt düzeyinde eşleşti.
- Sağlıklı OCR Results Table / BoundingBox şeması korundu; `LoadFromYaml=false` korundu.
- Bağlantılar, Flow yanıt ayrıştırma/gruplama/hata işleme mantığı değişmedi. `barcode_flow.Run` tek yerde bulunuyor.
- Microsoft Power Fx: **2.516 formül parse edildi, sıfır sözdizimi hatası**. Bu tüm uygulamanın Studio bağlama kontrolü anlamına gelmez.
- Microsoft Power Fx: **411 çalıştırılabilir senaryo PASS**. Gerçek paket formülleri üzerinden sağ üst seçim, eğiklik, girdi sırasından bağımsızlık, eksik koordinatlar, boş/geciken çıktı, Türkçe ve sayısal adlar, OCR–manuel giriş önceliği, eski görüntü ve çift sorgu engeli, ekran geometrisi kontrol edildi.
- Yerleşim: 320×480, 320×568, 360×640, 375×667, 390×844, 412×915, 430×932, 844×390, 390×300 ölçülerinde kontrol sınırları değerlendirildi. 480px'den kısa alanda minimum tuval 480px kalır; bunun oynatıcıdaki kaydırma ve klavye davranışı ayrıca canlı kontrol gerektirir. Bu bir ekran görüntüsü veya metin kırpılma testi değildir.
- Kontrast: gövde 14,68:1; yardımcı metin 7,56:1; ana düğme 5,18:1; pasif düğme 6,87:1; rezerv bilgisi 4,88:1.

Kanıtlar: [paket/roundtrip](validation.json), [statik kontroller](static-checks.json), [Power Fx sonuçları](powerfx-results.txt), [test girdileri](fx-input.json).
Eski paketten gelen `BindingErrorCount` gibi kayıt anı sayaçları yeniden ölçülmüş gibi sıfırlanmadı; güncel Studio App Checker sonucu mevcut değil.

## Canlı kabul — tamamlanmadı

Tarayıcı/uygulama envanteri boş döndü. Power Apps Studio, gerçek telefon, kamera/galeri veya tenant Flow çağrısı çalıştırılmadı. Bu nedenle uçtan uca tüm sorunların kapandığı iddia edilmez.

Bağlı Studio ve telefonda bu **v3** paketini açtıktan sonra gereken kabul:

1. Ana sayfa → ürün ara: görüntü seçmeden hata çıkmaması; açık ve koyu cihaz temasında uygulama yüzeylerinin açık kalması.
2. Kamera ve galeriden üst solda, üst sağda ve alt sağda ayrı kodlar bulunan etiket: üst sağ kodun bir kez sorgulanması. Geciken ve metinsiz fotoğraf: gereksiz ürün bulunamadı bildirimi olmaması.
3. Aynı görseli yeniden seçme, geri dönme ve art arda düğmeye dokunma: eski sonuç veya çift Flow çağrısı oluşmaması.
4. Klavyeyle Türkçe ürün adı ve sayısal kod: girişin görünür kalması, klavye açılıp kapanması, boş girişin sorgulanmaması ve yazılan ürünle stok sorgusu. OCR sürerken yazmaya başlandığında manuel girişin korunması.
5. Küçük/büyük telefon, yatay görünüm, uzun ürün adı ve depo kodu: metin kırpılması/üst üste binme olmaması; sonuç kartı açma/kapama ve hata/boş sonuç ekranları. İşletim sisteminin kendi durum/gezinme çubukları uygulamanın tuvali dışındadır.
6. Studio kaydet/aç döngüsünden sonra OCR çıktı şemasının korunması ve App Checker sonucu.

## Üretim ve kaynaklar

Komutlar repository [README](../../README.md) dosyasındadır. Yeni özellikler `scripts/mobile_v3_fixes.py` üzerinden, ortak üreticiye `--mobile-v3` verilerek uygulanır. Hem insan tarafından okunabilen YAML hem çalıştırılan snapshot aynı ağaçtan yazılır.

Yerleşim ayarları Microsoft'un [responsive Canvas uygulamaları](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/create-responsive-layout) rehberindeki Scale to fit/oran kilidi yaklaşımını izler. OCR, [Text Recognizer Results, BoundingBox ve PageNumber](https://learn.microsoft.com/en-us/ai-builder/prebuilt-text-recognizer-component-in-powerapps) çıktıları üzerinden seçilir. Yeni giriş kontrolünün tanımı [Microsoft uygulama şablonundan](https://github.com/microsoft/teams-powerapps-app-templates/blob/75a82892c578397bdd19909af09651fffbb2e2be/Inspection/DataverseSolution/CanvasApps/msft_reviewinspections_1dd45_DocumentUri_src/pkgs/text_2.3.2.xml) değişmeden alınmıştır.
