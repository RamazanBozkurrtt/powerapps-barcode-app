# Phase 3 v2 — kart/Flow/açık yüzey düzeltmesi

Bu klasör `Barkod-Uygulamasi-Phase3-Orange-v2.msapp` paketinin tam kaynağıdır. Önceki Orange paketi yerine **v2** kullanılır. Önceki kaynak ve paketler değiştirilmedi.

Repository kökünden:

```powershell
python scripts/build_phase3_v2.py
python scripts/validate_phase3_v2.py
dotnet run --project scripts/phase3-fxcheck -- validation/phase3-v2/fx-input.json
```

`build_phase3_v2.py`, `phase3_v2_fixes.py` ve Microsoft'un `button_2.2.0.xml` kontrol tanımını kullanır. Ekran YAML'ı çalışma zamanı ağacından üretilir; `.msapr` onarılmış OCR metadata'sını ve aynı formülleri içerir. Metadata kaybını önlemek için `--disable-load-from-yaml` korunur. Sadece YAML'ı düzenlemek çalışma zamanı snapshot'ını güncellemez; değişikliği build kaynaklarına uygulayın.

Doğrudan paketleme:

```powershell
pac canvas pack --sources app-src-phase3-v2 --msapp Barkod-Uygulamasi-Phase3-Orange-v2.msapp --layout SourceCode --disable-load-from-yaml --overwrite
```

Kabul durumu ve kalan canlı kontroller: `validation/phase3-v2/REPORT.md`.
