# Mobile Light v6 — Flexible product gallery

Bu sürüm, kabul edilmiş v5 arayüzünü ve iş mantığını korur. Tek işlevsel düzenleme,
`galProducts` kontrolünün runtime snapshot'ında `galleryVariableTemplateHeight`
varyantını açıkça sabitlemek ve her ürün template'inin gerçek alt sınırını saydam
`shpProductTemplateBottom` kontrolüyle belirtmektir.

Telefon ayarları runtime `Properties.json` verisinde korunur: 390×844 tasarım,
`DocumentAppType=Phone`, portrait, `ScaleToFit=false`,
`MaintainAspectRatio=false`, `LockOrientation=false`. Ekranlar `App.Width/App.Height`,
ana container'lar `Parent.Width/Parent.Height` tabanlıdır.

```powershell
python scripts/build_mobile_v6.py
python scripts/validate_mobile_v6.py
```

Validator, taşınabilir yerel Power Fx checker'ı da çağırır ve çıktıyı
`validation/mobile-v6/powerfx-results.txt` dosyasına yazar.

Paketleme `--disable-load-from-yaml` ile yapılır; okunabilir YAML ve gerçek runtime
snapshot aynı üretimde güncellenir. Temel v5 paketi `versions` altında korunur ve
v6 ayrı dosya olarak üretilir.
