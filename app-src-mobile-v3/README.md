# Mobile Light v3

Bu klasör `Barkod-Uygulamasi-Mobile-Light-v3.msapp` paketinin kaynak ağacıdır.
Üretim ve doğrulama komutları repository kökündeki README'dedir.
İnsan tarafından okunabilen YAML ve çalıştırılan `.msapr` aynı kontrol ağacından üretilir.
Değişiklikleri `scripts/mobile_v3_fixes.py` üzerinde yapıp paketi yeniden üretin.

`pac canvas pack --sources app-src-mobile-v3 --msapp Barkod-Uygulamasi-Mobile-Light-v3.msapp --layout SourceCode --disable-load-from-yaml --overwrite`

YAML yüklemeyi açmayın: önceki Studio kaydında OCR Results tablo şemasının boş Record'a dönüştüğü belgelenmiştir.
Canlı telefon/Studio kabul durumu `validation/mobile-v3/REPORT.md` dosyasındadır.
