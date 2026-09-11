# v3.1 — açılış hatası onarımı

Teslim: [Barkod-Uygulamasi-Mobile-Light-v3-1.msapp](../../Barkod-Uygulamasi-Mobile-Light-v3-1.msapp).
Önceki `Mobile-Light-v3.msapp` kullanılmamalıdır.

Kullanıcının Studio hatası: `ErrOpeningDocument_UnknownError`.
Kullanıcının oturum kimliği: `c559ed20-5925-40b6-abcb-3d0b7097cc1f`.
Bu kimlikle Microsoft sunucu telemetrisi sorgulanmadı; aşağıdaki bulgular yerel paket incelemesidir.

## İzole edilen kusur

`scripts/mobile_v3_fixes.py` içindeki kontrol kopyalama yordamı `Children` alanını siliyordu.
Bu yüzden `lblManualProductName`, `txtProductName` ve `btnSearchProduct` kontrol kayıtlarında
boş olması gereken çocuk listesi hiç yoktu. Microsoft PAC 2.11.2'nin belge yükleyicisi
bu paketi kontrol ağacına dönüştürürken `IRStateHelpers.SplitIRAndState` içinde
`System.NullReferenceException` üretti.

Kopyalama yordamı artık `Children = []` yazar. Tüm kontrol kayıtlarının liste taşıdığı
üretim ve doğrulama sırasında kontrol edilir.

Önceki SourceCode pack/unpack turu serileştirilmiş snapshot'ı taşıyordu; kontrol ağacının
yüklenebilirliğini kanıtlamıyordu. Üretim zincirine kontrol ağacını gerçekten okuyan
`pac canvas unpack --layout Experimental` eklendi. Deprecated Experimental çıktı yalnızca
ikincil, salt okunur doğrulamadır; teslim paketi bu çıktıdan üretilmez.

Microsoft'un [kontrol ağacını ayıran kaynak kodu](https://github.com/microsoft/PowerApps-Tooling/blob/master/src/PAModel/IR/IRStateHelpers.cs)
bu alanı işleyen yükleme yolunu gösterir. Kurulu PAC DLL'indeki hata konumu da yerelde incelendi.

## Doğrulama

| Kontrol | Sonuç |
| --- | --- |
| Eski v3 → Microsoft belge yükleyicisi | FAIL — NullReferenceException yeniden üretildi |
| Yeni v3.1 → aynı yükleyici | PASS |
| SourceCode pack + bağımsız unpack | PASS |
| Eski/yeni paket farkının kesin karşılaştırması | PASS |
| 2.516 Power Fx formülü sözdizimi | PASS — sıfır hata |
| 411 OCR, manuel giriş, tek çağrı, yerleşim testi | PASS |

Paket içinde değişenler yalnızca `Controls/15.json` dosyasına eklenen üç boş `Children`
listesi ve `packed.json` içindeki paketleme zamanıdır. Diğer tüm ZIP üye içerikleri bayt
düzeyinde aynıdır. Formüller, sağ üst OCR seçimi, telefon yerleşimi, açık renkler, manuel
giriş, OCR Table şeması, Flow ve bağlantılar korunmuştur.

Kanıtlar: [kesin fark/onarım](repair.json), [eski yükleme hatası](broken-loader.json),
[yeni yükleme başarısı](final-loader.json), [üretime eklenen yükleme kontrolü](document-load.json),
[Power Fx testleri](powerfx-results.txt), [paket ve roundtrip](validation.json).

Tanı sırasında Python ile hazırlanan bir ara ZIP, ters bölü çizgilerini `/` biçimine
çevirdiği için ayrıca metadata yükleme hatası verdi. Bu ara dosya teslim değildir.
Teslim v3.1 doğrudan PAC tarafından üretildi; bu tanı hatası v3'teki kusurla karıştırılmadı.

## Kapsam sınırı

Yerel belge yükleme hatası izole edilip giderildi. Bu kontrol gerçek Power Apps Studio,
telefon, kamera ve tenant Flow oturumu değildir. Kullanıcının Studio'sunda son açılış
ve telefondaki kabul hâlâ doğrulanmalıdır; tüm canlı senaryolar geçmiş gibi raporlanmaz.

## Yeniden üretim

```powershell
python scripts/build_phase3_v2.py --mobile-v3-1
python scripts/validate_mobile_v3.py --mobile-v3-1
python scripts/verify_mobile_v31_repair.py
dotnet run --project scripts/phase3-fxcheck -- validation/mobile-v3-1/fx-input.json
```

Negatif kontrol için eski v3 dosyası kanıt olarak saklanır; üzerine yazılmamalıdır.
