"""Phone layout and OCR/manual acceptance. Applied to both snapshot and review YAML."""
import copy

# Treat slightly skewed boxes on the uppermost line as one row, then prefer its
# rightmost edge. Missing geometry must never discard otherwise readable text.
OCR_SELECTION = '''With(
    { readable: Filter(TextRecognizer1.Results, !IsBlank(TrimEnds(Text))) },
    With(
        { positioned: SortByColumns(
            AddColumns(
                Filter(readable, !IsBlank(BoundingBox.Top) && BoundingBox.Top >= 0 &&
                    !IsBlank(BoundingBox.Left) && BoundingBox.Left >= 0),
                OcrPage, Coalesce(PageNumber, 1),
                OcrTop, BoundingBox.Top,
                OcrRight, BoundingBox.Left + Max(0, Coalesce(BoundingBox.Width, 0))
            ),
            "OcrPage", SortOrder.Ascending, "OcrTop", SortOrder.Ascending,
            "OcrRight", SortOrder.Descending, "Text", SortOrder.Ascending
        ) },
        If(IsEmpty(positioned), TrimEnds(First(readable).Text),
            With({ anchor: First(positioned) },
                TrimEnds(First(SortByColumns(
                    Filter(positioned, OcrPage = anchor.OcrPage &&
                        OcrTop <= anchor.OcrTop + Max(0, Coalesce(anchor.BoundingBox.Height, 0)) / 2),
                    "OcrRight", SortOrder.Descending, "OcrTop", SortOrder.Ascending,
                    "Text", SortOrder.Ascending
                )).Text)
            )
        )
    )
)'''

OCR_GUARD = '''varScanReady && App.ActiveScreen = scrScan && !varScanAccepted && !varFlowCallStarted &&
    IsBlank(TrimEnds(txtProductName.Text)) && !IsBlank(TextRecognizer1.OriginalImage) &&
    TextRecognizer1.OriginalImage <> varScanEntryImage'''
MANUAL_GUARD = '''varScanReady && App.ActiveScreen = scrScan && !varScanAccepted &&
    !varFlowCallStarted && !IsBlank(TrimEnds(txtProductName.Text))'''


def apply_mobile(controls, setp, get, changed):
    white = 'RGBA(255, 255, 255, 1)'
    ink = 'RGBA(31, 41, 55, 1)'
    muted = 'RGBA(75, 85, 99, 1)'
    orange = 'RGBA(194, 65, 12, 1)'
    soft = 'RGBA(255, 247, 237, 1)'

    def clone(source, name, uid, kind=None):
        c = copy.deepcopy(controls[source])
        c.update(Name=name, Parent='scrScan', ControlUniqueId=str(uid), PublishOrderIndex=uid)
        # Leaf controls still require an explicit child array in the serialized
        # ControlInfo. Omitting it crashes Microsoft's SplitIRAndState loader.
        c['Children'] = []
        if kind:
            c['Template'] = copy.deepcopy(controls['lblProductName']['Template'])
            c['Template'].update(Id='http://microsoft.com/appmagic/text', Name='text', Version='2.3.2')
            c['Rules'] = []
            c['ControlPropertyState'] = []
            c['VariantName'] = ''
        controls[name] = c
        controls['scrScan']['Children'].append(c)
        changed[name] = {r['Property'] for r in c['Rules']}

    clone('lblScanInstruction', 'lblManualProductName', 2101)
    clone('lblScanInstruction', 'txtProductName', 2102, 'text')
    clone('btnScan', 'btnSearchProduct', 2103)
    setp('lblManualProductName', Text='"Ürün adı / kodu"', X='20', Y='236',
         Width='Parent.Width - 40', Height='28', Size='14', FontWeight='FontWeight.Semibold',
         Visible='true', ZIndex='30')
    setp('txtProductName', Default='""', HintText='"Ürün adını klavyeyle yazın"',
         AccessibleLabel='"Ürün adı veya kodu. Klavyeyle girin, ardından Stok sorgula düğmesine dokunun."',
         Mode='TextMode.SingleLine', Format='TextFormat.Text', MaxLength='250',
         DelayOutput='false', Clear='true', Reset='false', OnChange='false', OnSelect='false',
         X='20', Y='268', Width='Parent.Width - 40', Height='48',
         Font='Font.OpenSans', Size='16', Color=ink, Fill=white,
         BorderColor=muted, BorderThickness='1', HoverFill=white, HoverColor=ink,
         HoverBorderColor=orange, PressedFill=white, PressedColor=ink,
         DisabledFill='RGBA(243, 244, 246, 1)', DisabledColor=muted, DisabledBorderColor=muted,
         FocusedBorderColor=orange, FocusedBorderThickness='3',
         RadiusTopLeft='8', RadiusTopRight='8', RadiusBottomLeft='8', RadiusBottomRight='8',
         PaddingLeft='12', PaddingRight='12', PaddingTop='8', PaddingBottom='8',
         Visible='true', DisplayMode='If(varScanAccepted, DisplayMode.Disabled, DisplayMode.Edit)',
         TabIndex='0', ZIndex='31')
    setp('btnSearchProduct', Text='"Stok sorgula"', X='20', Y='328', Width='Parent.Width - 40',
         Height='48', Size='16', Visible='true', TabIndex='0', ZIndex='32',
         AccessibleLabel='"Yazılan ürün adı veya koduyla stok sorgula"',
         DisplayMode=f'If({MANUAL_GUARD}, DisplayMode.Edit, DisplayMode.Disabled)',
         OnSelect=f'''If({MANUAL_GUARD},
    Set(varAcceptedText, TrimEnds(txtProductName.Text));
    Set(varOcrEmpty, false);
    Set(varScanAccepted, true);
    Navigate(scrLoading, ScreenTransition.Fade)
)''')

    setp('App', MinScreenWidth='320', MinScreenHeight='480')
    setp('scrScan', OnVisible=get('scrScan', 'OnVisible').replace(
        'Reset(TextRecognizer1);', 'Reset(txtProductName);\nReset(TextRecognizer1);'))
    setp('TextRecognizer1', OnChange=f'''If(
    varScanReady && App.ActiveScreen = scrScan && IsBlank(TextRecognizer1.OriginalImage),
    Set(varScanEntryImage, "")
);
If({OCR_GUARD},
    IfError(
        With({{ chosenText: {OCR_SELECTION} }},
            If(!IsBlank(chosenText),
                Set(varAcceptedText, chosenText);
                Set(varOcrEmpty, false);
                Set(varScanAccepted, true);
                Navigate(scrLoading, ScreenTransition.Fade),
                Set(varOcrEmpty, false)
            )
        ),
        Set(varOcrEmpty, true)
    )
)''', X='20', Y='140', Width='Parent.Width - 40', Height='56',
         Text='"Fotoğraf çek veya seç"', FillColor=orange, FontColor=white,
         DisabledFill=white, DisabledColor=muted,
         DisplayMode='If(varScanAccepted, DisplayMode.Disabled, DisplayMode.Edit)')

    # Explicit colours in every interactive state; independent of device theme.
    for name, c in controls.items():
        kind = c['Template']['Name']
        if kind == 'screen':
            setp(name, Fill=white, Width='Max(App.Width, App.MinScreenWidth)',
                 Height='Max(App.Height, App.MinScreenHeight)')
        if kind == 'label':
            setp(name, Color=ink, DisabledColor=muted, Font='Font.OpenSans')
        if kind == 'button' and name != 'btnProductToggle':
            decorative = get(name, 'DisplayMode') in ['DisplayMode.Disabled', 'DisplayMode.View']
            setp(name, Fill=white if decorative else orange, Color=ink if decorative else white,
                 DisabledFill='RGBA(243, 244, 246, 1)', DisabledColor=muted,
                 HoverColor=ink if decorative else white, PressedColor=ink if decorative else white,
                 HoverFill=soft if decorative else 'RGBA(154, 52, 18, 1)',
                 PressedFill=soft if decorative else 'RGBA(124, 45, 18, 1)')
    # Full-width phone controls with 20px outer and 12px inner spacing.
    def box(name, x, y, w, h, **props):
        setp(name, X=str(x), Y=str(y), Width=str(w), Height=str(h), **props)

    for n in ['btnHomeHeroCard','btnHomeScanMark','lblHomeCardHint','lblScanGuideCaption',
              'btnScanSurface','btnScanEmptyCard','lblScanEmptyTitle','lblScanEmptyBody',
              'btnLoadingCard','btnErrorCard','btnResultsEmptyCard']:
        setp(n, Visible='false')
    box('lblHomeEyebrow',20,24,'Parent.Width - 40',28,Size='12',Color=orange)
    box('lblHomeTitle',20,64,'Parent.Width - 40',108,Size='24',
        Text='"Ürünü bulun.\nStokları görün."')
    box('lblHomeCardTitle',20,192,'Parent.Width - 40',40,Size='16',Text='"Fotoğrafla veya yazarak"')
    box('lblHomeCardBody',20,240,'Parent.Width - 40',84,Size='15',
        Text='"Etiketi fotoğraflayın veya ürün adını yazın. Fotoğrafta sağ üstteki metin seçilir."')
    box('btnScan',20,'Max(340, Parent.Height - 148)','Parent.Width - 40',52,Size='16',Text='"Ürün ara"')
    box('lblHomeFooter',20,'btnScan.Y + btnScan.Height + 12','Parent.Width - 40',60,Size='12',Color=muted)

    box('btnScanBack',16,16,44,44,Size='24')
    box('lblScanTitle',72,16,'Parent.Width - 92',44,Size='20',Text='"Ürün ara"')
    box('lblScanInstruction',20,72,'Parent.Width - 40',60,Size='14',
        Text='"Fotoğrafta en üst satırın sağındaki metin seçilir."')
    box('lblScanHint',20,392,'Parent.Width - 40',72,Size='12',Visible='true',Color=muted,
        Live='Live.Polite', Text='If(varOcrEmpty, "Görüntü işlenemedi. Yeniden deneyin veya ürün adını yazın.", "Metin gelmezse ürün adını yazın. Yazmaya başladığınızda sorgu sizin girişinizi kullanır.")')
    setp('lblManualProductName',Color=ink)

    box('btnLoadingHalo','(Parent.Width - Self.Width) / 2','Max(24, (Parent.Height - 330) / 2)',72,72,Size='24')
    box('lblLoadingTitle',20,'btnLoadingHalo.Y + 88','Parent.Width - 40',60,Size='18')
    box('lblLoadingBody',20,'lblLoadingTitle.Y + 68','Parent.Width - 40',68,Size='14')
    box('lblLoadingProduct',20,'lblLoadingBody.Y + 80','Parent.Width - 40',64,Size='15',Fill=soft,Color=ink)

    box('lblResultsEyebrow',20,16,'Parent.Width - 40',24,Size='11',Color=orange)
    box('lblResultsTitle',20,44,'Parent.Width - 40',40,Size='24')
    box('lblResultsCount',20,88,'Parent.Width - 40',28,Size='14')
    box('btnResultsScanAgain',20,128,'Parent.Width - 40',48,Size='16',Text='"Yeni ürün ara"')
    box('galProducts',8,192,'Parent.Width - 16','Max(112, Parent.Height - Self.Y - 16)')
    box('btnResultsEmptyMark','(Parent.Width - Self.Width) / 2',208,64,64,Size='24')
    box('lblResultsEmptyTitle',20,284,'Parent.Width - 40',60,Size='18')
    box('lblResultsEmptyBody',20,352,'Parent.Width - 40',80,Size='14',
        Text='"Stok kaydı yok. Yeni ürün ara düğmesinden adı yazarak veya fotoğrafla tekrar deneyin."')
    setp('lblWarehouseName', Size='12', Height='40', Tooltip='ThisItem.InventoryWarehouseId')
    setp('lblWarehouseAvailable',Size='18')
    setp('lblWarehouseReserved',Size='10',Color=orange,Fill=soft)
    setp('lblProductNumber',Size='11')
    setp('lblProductName',Size='14')
    setp('lblProductConflict',Size='9')

    box('btnErrorMark','(Parent.Width - Self.Width) / 2','Max(16, (Parent.Height - 448) / 2)',64,64,Size='26')
    box('lblErrorTitle',20,'btnErrorMark.Y + 76','Parent.Width - 40',60,Size='20')
    box('lblErrorBody',20,'lblErrorTitle.Y + 68','Parent.Width - 40',120,Size='14')
    box('btnErrorRetry',20,'lblErrorBody.Y + 136','Parent.Width - 40',48,Size='16')
    box('btnErrorHome',20,'btnErrorRetry.Y + 60','Parent.Width - 40',48,Size='16')
