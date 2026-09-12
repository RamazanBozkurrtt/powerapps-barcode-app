# Mobile Light v4

Telefon öncelikli turuncu/beyaz Canvas UI refactor kaynağı.

Teslim: [Barkod-Uygulamasi-Mobile-Light-v4.msapp](../Barkod-Uygulamasi-Mobile-Light-v4.msapp).
Font düzeltmesi ve güncel paket doğrulaması: [rapor](../validation/font-fix/REPORT.md).
Detaylı değişiklik ve doğrulama: [rapor](../validation/mobile-v4/REPORT.md).

```powershell
python scripts/build_phase3_v2.py --mobile-v4
python scripts/validate_mobile_v4.py
python scripts/validate_font_fix.py --baseline 5be43d5
dotnet run --project scripts/phase3-fxcheck -- validation/mobile-v4/fx-input.json
```

UI tanımı `scripts/mobile_v4_ui.py` içindedir. `Src/*.pa.yaml` dosyaları, çalışan
`.msapr` snapshot ile aynı kontrol ağacı ve formüllerden üretilir. Yalnızca YAML
düzenlemek teslim paketini değiştirmez. OCR şemasını korumak için üretimde
`--disable-load-from-yaml` kullanılır. PAC SourceCode pack/unpack ve Microsoft
belge yükleyicisiyle Experimental read-only unpack üretim sırasında çalışır.

Önceki paketler korunur. Studio ve fiziksel telefon kabulü henüz yapılmamıştır.
