# Mobile Light v5

Yalnızca ekran kompozisyonu ve görsel bilgi hiyerarşisi değiştirildi.
Temel paket, kullanıcı tarafından Formula hatalarının giderildiği doğrulanan v4'tür.

[V5 uygulaması](../Barkod-Uygulamasi-Mobile-Light-v5.msapp) ·
[Rapor](../validation/mobile-v5/REPORT.md) ·
[Paket kaynaklarından üretilen önizleme](../validation/mobile-v5/preview/index.html)

Üretim kaynağı `scripts/mobile_v5_composition.py` dosyasıdır.
`build_mobile_v5.py`, çalışan v4 paketini temel alır; YAML ve `.msapr` verilerini
aynı kontrol ağacından üretir. OCR şemasını korumak için
`pac canvas pack --layout SourceCode --disable-load-from-yaml` kullanılır.
Önceki v4 paketi ve kaynakları bu UI refactor sırasında değiştirilmez.

```powershell
python scripts/build_mobile_v5.py
python scripts/validate_mobile_v5.py
python scripts/preview_mobile_v5.py
```

Python bağımlılıkları: PyYAML; önizleme için Playwright ve Microsoft Edge.
PAC PATH üzerinde yoksa üretici bu çalışma alanındaki `build/font-tools` altında
hazırlanmış yerel PAC/.NET araçlarını kullanır. Önizlemenin ilk üretimi Open Sans
fontunu Google Fonts deposundan indirir; font lisansı önizleme klasöründedir.

Kaynak, formül ve görsel simülasyon kontrolleri canlı Studio ve telefon testi değildir.
Yayınlama veya backend değişikliği yapılmadı.
