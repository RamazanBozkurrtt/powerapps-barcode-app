# Font formülü düzeltmesi

Teslim: [Barkod-Uygulamasi-Mobile-Light-v4.msapp](../../Barkod-Uygulamasi-Mobile-Light-v4.msapp).
Önceki durum: Git `5be43d5`. Bu değişiklik yalnızca Font formüllerini düzeltir.

## Kök neden

`Font.OpenSans` geçerli Canvas Font enum üyesi değildir. Doğru Power Fx ifadesi
`Font.'Open Sans'`, YAML property değeri ise `Font: =Font.'Open Sans'` biçimindedir.
Tek tırnaklar boşluk içeren enum üyesini belirtir; ifade bir string değildir.
Microsoft'un [kontrol şablonu](https://github.com/microsoft/PowerApps-Tooling/blob/master/src/PAModel/ControlTemplates/commonStyleProperties.xml)
aynı üyeyi `%Font.RESERVED%.'Open Sans'` olarak tanımlar. Uygulamanın kendi
`References/Themes.json` içeriği de aynı yerel üyeyi kullanır.

Eski kontrol yalnızca `engine.Parse` çağırıyordu. Sözdizimi doğru görünen
`Font.OpenSans` bu kontrolden geçebilir; enum adının çözümlenmesi denetlenmiyordu.
Artık v4 doğrulaması bütün 53 Font formülünün doğru enum ifadesine eşit olduğunu da kontrol eder.

## Kapsam

| Ekran | Düzeltilen `Font.OpenSans` |
| --- | ---: |
| scrHome | 9 |
| scrScan | 12 |
| scrLoading | 5 |
| scrResults | 19 |
| scrError | 6 |
| Toplam | 51 |

V4'te toplam 53 Font özelliği vardır. Kalan ikisi görünmez `tmrLoadingFlow` ve
`tmrLoadingVisual` kontrollerindeki `App.Theme.Font` ifadeleriydi. Bu iki Font da
`Font.'Open Sans'` olarak açıkça tanımlandı. Bunların bildirilen diğer iki App Checker
hatasının nedeni olduğu doğrulanmış değildir; bütün Font özellikleri artık aynı
geçerli enum ifadesini kullanır. Timer davranışları değiştirilmedi.

Tüm `app-src*` klasörleri, iç içe kontroller ve `.msapr` snapshot verileri tarandı.
`app-src` ve `app-src-phase3` içinde hatalı kullanım yoktu. Diğer kaynaklardaki
195 hatalı kullanım ve snapshot karşılıkları düzeltildi:

| Kaynak | Düzeltilen YAML formülü | Düzeltilen snapshot formülü |
| --- | ---: | ---: |
| app-src-phase3-v2 | 46 | 46 |
| app-src-mobile-v3 | 49 | 49 |
| app-src-mobile-v3-1 | 49 | 49 |
| app-src-mobile-v4 | 51 | 51 |

Üç üretici dosyadaki beş hatalı ifade de düzeltildi; yeniden üretim aynı hatayı getirmez.
Önceki `.msapp` teslimleri ve geçmiş teşhis/test kayıtları karşılaştırma amacıyla
korundu. Bunlar eski ifadeleri içerebilir; güncel teslim yukarıdaki v4 paketidir.

## Doğrulama

- Güncel paket: 53/53 Font formülü `Font.'Open Sans'`; `OpenSans` kullanımı sıfır.
- Bütün `app-src*` YAML dosyaları ve snapshot üyeleri: `OpenSans` kullanımı sıfır.
- Önceki sürüme karşı bütün font dışı property değerleri ve kontrol hiyerarşisi aynı.
  Boyut, konum, renk, metin, OCR, navigation, variables, collections, stock query ve Flow formülleri korunur.
- 70 mevcut On* davranış formülü birebir korunur; OCR şeması ve References aynı.
- Paket/snapshot ZIP bütünlüğü ve YAML/runtime formül eşliği başarılı.
- 3.093 formülde Power Fx parse hatası sıfır; mevcut 197 çalıştırılabilir kontrol başarılı.
- PAC 2.11.2 SourceCode pack ve unpack başarılı; açılan snapshot'ın paket üyeleri bayt düzeyinde aynı.
- Microsoft belge yükleyicisiyle `--layout Experimental` salt okunur açma başarılı (exit 0).
  Bu çıktı yeniden paketlenmedi. Orijinal ZIP dosya yolu yazımı ve metadata korundu.
- Kaynaktan PAC ile tekrar üretilen pakette runtime JSON verileri aynı; YAML'da yalnızca
  LF/CRLF satır sonu farkı ve `packed.json` içinde üretim metadata farkı var.
- Font değişiklikleri dışında bütün paket üyeleri bayt düzeyinde aynı; gömülü geçmiş
  App Checker SARIF kaydı silinmedi veya yeni sonuç gibi değiştirilmedi.

Ayrıntılı property envanteri, değişen paket üyeleri ve güncel SHA-256:
[audit.json](audit.json). Standart v4 kontrolleri:
[static-checks.json](../mobile-v4/static-checks.json).
Son paket doğrulaması ve SHA-256: [validation.json](validation.json).
Kanıtlar: [Power Fx](powerfx-results.txt), [PAC pack](pack-final.json),
[SourceCode unpack](unpack-sourcecode-final.json),
[Microsoft belge yükleyicisi](unpack-experimental-final.txt).

**Studio App Checker `Formula errors = 0` kabul kriteri henüz doğrulanmadı.**
Bu oturumda bağlı Power Apps Studio yoktur. Yerel kaynak/paket kontrolleri Studio'nun
tam type/binding kontrolünün yerine geçmez. Bildirilen toplam 53 hata ile kesin
olarak bulunan 51 geçersiz enum kullanımı arasındaki fark, güncel Studio sonucu
olmadan diğer hataların çözüldüğü şeklinde yorumlanamaz.

## Değişen dosyalar

- `app-src-mobile-v4/Src/{scrHome,scrScan,scrLoading,scrResults,scrError}.pa.yaml`
- Aynı beş ekran dosyası: `app-src-phase3-v2/Src`, `app-src-mobile-v3/Src`, `app-src-mobile-v3-1/Src`
- Bu dört kaynak klasöründeki `Barkod-Uygulamasi-Phase2-FIXED-v2.msapr`
- `Barkod-Uygulamasi-Mobile-Light-v4.msapp`
- `scripts/phase3_v2_fixes.py`, `scripts/mobile_v3_fixes.py`, `scripts/mobile_v4_ui.py`
- `scripts/validate_mobile_v4.py`, yeni `scripts/validate_font_fix.py`
- `validation/mobile-v4/fx-input.json`
- `README.md`, `app-src-mobile-v4/README.md`, `validation/mobile-v4/REPORT.md`
- Bu rapor ve `validation/font-fix` altındaki doğrulama kanıtları

Kaynak ve paket için dosya adlarının tek tek listesi `audit.json` içindedir.

## Yeniden doğrulama

Python ve PyYAML ile:

```powershell
python scripts/validate_font_fix.py --baseline 5be43d5
python scripts/validate_mobile_v4.py
```

PAC ile paket kontrolü (üretimde OCR şemasını koruyan `--disable-load-from-yaml` kullanılır):

```powershell
pac canvas pack --sources app-src-mobile-v4 --msapp build/font-check.msapp --layout SourceCode --disable-load-from-yaml
pac canvas unpack --msapp Barkod-Uygulamasi-Mobile-Light-v4.msapp --sources build/font-check-sourcecode --layout SourceCode
pac canvas unpack --msapp Barkod-Uygulamasi-Mobile-Light-v4.msapp --sources build/font-check-loader --layout Experimental
```

Son kabul için güncel v4 paketini Power Apps Studio'da açıp App Checker → Formulas
sayısını kontrol edin. Hedef sıfırdır; bu rapor canlı Studio sonucu iddia etmez.
