# Mobile Light v3.1

`Barkod-Uygulamasi-Mobile-Light-v3-1.msapp` için tam SourceCode kaynak ağacı.
v3'teki üç yaprak kontrolün eksik `Children: []` alanları onarıldı.
Formüller, OCR şeması, açık arayüz, mobil yerleşim ve manuel giriş v3 ile aynı.

Repository kökünden `python scripts/build_phase3_v2.py --mobile-v3-1` ile üretin.
Betik SourceCode roundtrip yanında Microsoft'un kontrol ağacını okuyan belge yükleyicisini de çalıştırır.
Experimental çıktı yalnızca okuma testi içindir; yeniden paketlenmez.
Çalışma snapshot'ı `.msapr` içindedir. Sadece YAML'ı değiştirmek yeterli değildir.
`--disable-load-from-yaml` korunmalıdır.

Kanıtlar ve tüm komutlar: [onarım raporu](../validation/mobile-v3-1/REPORT.md).
