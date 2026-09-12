# Mobile Light v6 — Flexible product gallery raporu

## 1. Root cause

Nested `galWarehouses` yüksekliği item bazında doğru büyürken, standart dikey parent
gallery her ürün satırını sabit `TemplateSize=76` aralığıyla yerleştirirse sonraki ürün
kartları expanded içeriğin üzerine gelir. Bu bir ZIndex problemi değildir.

İncelenen v5 runtime snapshot'ında `galProducts` zaten
`galleryVariableTemplateHeight` olarak bulunuyordu. Ancak üretim kodu varyantı açıkça
atamıyor ve expanded içeriğin gerçek alt sınırını bildiren terminal bir template
kontrolü oluşturmuyordu. v6 bu iki koşulu runtime snapshot ve okunabilir YAML'da
açıkça kalıcılaştırır.

## 2. Değiştirilen dosyalar

- `scripts/build_mobile_v6.py`
- `scripts/validate_mobile_v6.py`
- `app-src-mobile-v6/README.md`
- `app-src-mobile-v6/Src/scrResults.pa.yaml`
- `app-src-mobile-v6/Barkod-Uygulamasi-Phase2-FIXED-v2.msapr`
- `validation/mobile-v6/*`
- `versions/Barkod-Uygulamasi-Mobile-Light-v6.msapp`

Paket seviyesinde v5 → v6 arasında yalnızca `Controls/38.json`, `Properties.json`,
`Src/scrResults.pa.yaml` ve PAC tarafından üretilen `packed.json` farklıdır.

## 3. galProducts değişikliği

- Control ve sürüm korunur: `Gallery@2.15.0`.
- Runtime varyantı açıkça `galleryVariableTemplateHeight`; YAML varyantı
  `VariableHeight` olarak sabitlenir.
- `Items=colProductGroups`, `TemplateSize=76` ve mevcut görünüm formülleri korunur.
- Saydam `shpProductTemplateBottom` rectangle'ı template sonuna eklenir. Kontrolün
  alt sınırı kapalı item'da 76 px, yalnızca seçili expanded item'da
  `galWarehouses.Y + galWarehouses.Height + 12` olur.
- Bütün item'ları topluca büyüten global TemplateSize formülü kullanılmaz.

## 4. galWarehouses değişikliği

Değişiklik yoktur. Control JSON'u v5 ile aynıdır. Özellikle:

- `Items=ThisItem.WarehouseRows`
- `TemplateSize=52`
- mevcut item-bazlı `Height`
- mevcut item-bazlı `Visible`

formülleri birebir korunmuştur. `btnProductCard.Height` mevcut toplam kart yüksekliği
formülünü kullanmaya devam eder.

## 5. Responsive/runtime ayarları

Paket runtime `Properties.json` ayarları korunmuş ve validator ile doğrulanmıştır:

- `DocumentLayoutWidth=390`
- `DocumentLayoutHeight=844`
- `DocumentAppType=Phone`
- `DocumentLayoutOrientation=portrait`
- `DocumentLayoutScaleToFit=false`
- `DocumentLayoutMaintainAspectRatio=false`
- `DocumentLayoutLockOrientation=false`

Beş screen `Width=App.Width`, `Height=App.Height`; beş ana container
`Height=Parent.Height` ve `Parent.Width` tabanlı genişlik kullanır. Source içinde root
layout'u 390×844'e kilitleyen Width/Height formülü yoktur.

## 6. Korunan business logic

V5'teki 84 mevcut `On*` formülü birebir aynıdır. `App`, loading timer'ları,
navigation, OCR, Flow, collections, variables, stock query, data source/reference
verileri ve nested gallery aynı bırakılmıştır. Bütün Font property'leri
`Font.'Open Sans'` kullanır.

## 7. Validation sonuçları

- PAC SourceCode pack: PASS
- PAC SourceCode unpack/byte round-trip: PASS
- PAC Experimental document-loader unpack: PASS
- 3.662 runtime Power Fx formülü: 0 yerel parse hatası
- 232 çalıştırılabilir Power Fx senaryosu: PASS
- Product template alt sınırı: kapalı 76, başka item açıkken 76, seçili item açıkken
  örnek 4×52 warehouse satırında 320: PASS
- Runtime/YAML flexible gallery ve spacer parity: PASS
- Responsive manifest/root formülleri: PASS
- Geçersiz `OpenSans` / `Font.OpenSans`: 0
- V5 SHA-256 build öncesi ve sonrası aynı: PASS

Power Apps Studio/App Checker ve fiziksel telefon testi bu ortamda çalıştırılmadı.
Paketteki `AppCheckerResult.sarif`, v5'ten byte-identical korunmuş üç tarihsel
`btnContinueWithSelectedProduct.OnSelect` finding'i içerir; bunlar yeni canlı App
Checker sonucu değildir ve bu görevde business logic değiştirilmediği için müdahale
edilmemiştir. Bu nedenle canlı App Checker sonucu PASS olarak raporlanmaz.

Kanıtlar: `build.json`, `static-checks.json`, `powerfx-results.txt`, `pack.json`,
`roundtrip.json`, `document-load.json`.

## 8. Yeni .msapp yolu

`versions/Barkod-Uygulamasi-Mobile-Light-v6.msapp`

SHA-256: `c824ae8ef8bfc6855560b69566b1cd67a84adef875a90a33d0027a639b5a7cbe`

Önceki çalışan `versions/Barkod-Uygulamasi-Mobile-Light-v5.msapp` overwrite edilmedi;
korunan SHA-256 değeri
`326d989cc73539f4dce37c27af4a9ded53d8958d113098d843f3b736f5354673`.
