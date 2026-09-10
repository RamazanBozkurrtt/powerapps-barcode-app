# Phase 3 — turuncu / beyaz Canvas App

Bu klasör yeni teslimatın tam kaynağıdır. Eski `app-src` tanılama sürümüdür; bu teslimatı paketlerken kullanmayın.

`Src/*.pa.yaml` okunabilir ekran/formül kaynağıdır. `.msapr` aynı formülleri ve onarılmış TextRecognizer metadata'sını taşıyan çalışma zamanı snapshot'ıdır. Metadata kaybını önlemek için iki temsil birlikte güncellenir ve YAML yüklemesi kapalı paketlenir. Yalnız YAML'ı değiştirip aşağıdaki komutla paketlemek çalışma zamanı formüllerini güncellemez.

Repository kökünden tekrar üretim:

```powershell
python scripts/build_phase3.py
```

Doğrudan paketleme:

```powershell
pac canvas pack --sources app-src-phase3 --msapp Barkod-Uygulamasi-Phase3-Orange.msapp --layout SourceCode --disable-load-from-yaml --overwrite
```

Temel paket: `Barkod-Uygulamasi-Phase2-FIXED-v2.msapp`. Çalışan sürümün Flow çağrısı, JSON işleme, ItemNumber gruplaması ve hata yolları korunur. Ayrıntılar: `validation/phase3/REPORT.md`.
