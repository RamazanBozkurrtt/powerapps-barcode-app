"""UI-only refactor. No mutation of OCR, dispatch, parsing or business state."""
import copy
import json

WHITE = 'RGBA(255, 255, 255, 1)'
INK = 'RGBA(31, 41, 55, 1)'
MUTED = 'RGBA(75, 85, 99, 1)'
ORANGE = 'RGBA(194, 65, 12, 1)'
SOFT = 'RGBA(255, 247, 237, 1)'
BORDER = 'RGBA(229, 231, 235, 1)'
SURFACE = 'RGBA(249, 250, 251, 1)'


def apply_ui(cs, setp, get, changed, original):
    uid = 3000

    def new(source, name, parent, kind=None):
        nonlocal uid
        uid += 1
        c = copy.deepcopy(cs[source])
        c.update(Name=name, Parent=parent, ControlUniqueId=str(uid), PublishOrderIndex=uid, Children=[])
        if kind:
            c['Template'].update(Id='http://microsoft.com/appmagic/'+kind, Name=kind, Version='1.0')
            c.update(Rules=[], ControlPropertyState=[], VariantName='verticalAutoLayoutContainer')
        cs[name] = c
        changed[name] = {r['Property'] for r in c['Rules']}
        cs[parent]['Children'].append(c)
        return c

    def move(name, parent):
        c = cs[name]
        old = cs[c['Parent']]
        old['Children'] = [x for x in old['Children'] if x['Name'] != name]
        c['Parent'] = parent
        cs[parent]['Children'].append(c)

    def container(name, parent, children, horizontal=False, **props):
        c = new('lblScanTitle', name, parent, 'groupContainer')
        c['VariantName'] = 'horizontalAutoLayoutContainer' if horizontal else 'verticalAutoLayoutContainer'
        setp(name, X='0', Y='0', Width='Parent.Width', Height='Parent.Height',
             LayoutMode='LayoutMode.Auto', LayoutDirection='LayoutDirection.Horizontal' if horizontal else 'LayoutDirection.Vertical',
             LayoutAlignItems='LayoutAlignItems.Stretch', LayoutJustifyContent='LayoutJustifyContent.Start',
             LayoutGap='8', LayoutWrap='false', LayoutOverflowX='LayoutOverflow.Hide',
             LayoutOverflowY='LayoutOverflow.Hide', LayoutMinWidth='0', LayoutMinHeight='0',
             FillPortions='0', Fill=WHITE, Visible='true', BorderThickness='0',
             PaddingTop='0', PaddingBottom='0', PaddingLeft='0', PaddingRight='0')
        setp(name, **props)
        for n in children:
            move(n, name)
            setp(n, X='0', Y='0', FillPortions='0', LayoutMinWidth='0', LayoutMinHeight='0',
                 AlignInContainer='AlignInContainer.Stretch')
            if not horizontal:
                setp(n, Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight')
        return c

    def root(name, screen, children, **props):
        defaults = dict(X='(Parent.Width - Self.Width) / 2', Y='0',
                         Width='Min(Parent.Width, 600)', Height='Parent.Height', PaddingLeft='16',
                         PaddingRight='16', PaddingTop='16', PaddingBottom='24',
                         LayoutOverflowY='LayoutOverflow.Scroll')
        defaults.update(props)
        return container(name, screen, children, **defaults)

    # Fixed readable type sizes, content-sized labels, no viewport-scaled fonts.
    for n, c in list(cs.items()):
        kind = c['Template']['Name']
        if kind == 'screen':
            setp(n, Width='App.Width', Height='App.Height', Fill=WHITE)
        if kind == 'label':
            setp(n, Font="Font.'Open Sans'", Color=INK, Size='14', PaddingLeft='0', PaddingRight='0',
                 PaddingTop='0', PaddingBottom='0')
        if kind in ('button', 'text'):
            setp(n, RadiusTopLeft='8', RadiusTopRight='8', RadiusBottomLeft='8', RadiusBottomRight='8')
    setp('App', MinScreenWidth='320', MinScreenHeight='240')

    for n in ['shpHomeTopGlow', 'lblHomeCardTitle', 'btnLoadingHalo', 'lblResultsEyebrow']:
        setp(n, Visible='false')
    root('conHome', 'scrHome', ['lblHomeEyebrow', 'lblHomeTitle', 'lblHomeCardBody', 'btnScan', 'lblHomeFooter'], LayoutGap='16')
    setp('lblHomeEyebrow', Text='"STOK ASİSTANI"', Height='24', Size='12', Color=ORANGE)
    setp('lblHomeTitle', Height='88', AutoHeight='true', Size='26', FontWeight='FontWeight.Bold')
    setp('lblHomeCardBody', Text='"Etiketi fotoğraflayın veya ürün adı / koduyla depolardaki stokları sorgulayın."',
         Height='60', AutoHeight='true', Color=MUTED, Size='15')
    setp('btnScan', Height='48', Size='16')
    setp('lblHomeFooter', Height='40', AutoHeight='true', Size='12', Color=MUTED,
         Text='"Kullanılabilir stok ve rezerve miktarları tek ekranda."')

    root('conSearch', 'scrScan', [], LayoutGap='16')
    container('conSearchHeader', 'conSearch', ['btnScanBack', 'lblScanTitle'], horizontal=True, Height='48')
    setp('btnScanBack', Text='"‹ Geri"', Width='72', Height='48', Size='14', Fill=WHITE,
         Color=ORANGE, BorderThickness='0', HoverFill=SOFT, HoverColor=ORANGE, PressedFill=SOFT, PressedColor=ORANGE)
    setp('lblScanTitle', Size='20', Height='48', FillPortions='1', Width='Parent.Width - 80')
    container('conSearchForm', 'conSearch', ['lblScanInstruction', 'TextRecognizer1', 'lblManualProductName', 'txtProductName', 'btnSearchProduct', 'lblScanHint'],
              Height='lblScanInstruction.Height + TextRecognizer1.Height + lblManualProductName.Height + txtProductName.Height + btnSearchProduct.Height + lblScanHint.Height + 60',
              LayoutGap='12')
    for n in ['conSearchHeader', 'conSearchForm']:
        setp(n, Width='Parent.Width - 32', AlignInContainer='AlignInContainer.Stretch')
    setp('lblScanInstruction', Text='"Etiketi fotoğraflayın veya ürün adı / kodunu yazın."', Height='40', AutoHeight='true', Color=MUTED)
    # Use the native OCR action alone; no outer button/surface to create a double frame.
    setp('TextRecognizer1', Height='48', ButtonHeight='48', CommandBarFontSize='14', CommandBarIconSize='20',
         Text='"Fotoğraf çek veya seç"', FillColor=ORANGE, FontColor=WHITE, BorderThickness='0', BorderColor=ORANGE)
    setp('lblManualProductName', Height='24', Size='14')
    setp('txtProductName', Height='48', HintText='"Örn. 57047 veya ürün adı"', Fill=SURFACE,
         BorderColor=BORDER, FocusedBorderThickness='2', Size='16')
    setp('btnSearchProduct', Height='48', DisabledFill='RGBA(229, 231, 235, 1)',
         DisabledColor='RGBA(107, 114, 128, 1)', DisabledBorderColor='RGBA(229, 231, 235, 1)')
    setp('lblScanHint', Height='56', AutoHeight='true', Size='12', Color=MUTED,
         Text='If(varOcrEmpty, "Görüntü işlenemedi. Tekrar deneyin veya ürün adını yazın.", "Fotoğrafta üst satırın sağındaki metin kullanılır. Dilerseniz ürün adını doğrudan yazabilirsiniz.")')

    root('conLoading', 'scrLoading', [])
    container('conLoadingCard', 'conLoading', ['lblLoadingTitle', 'lblLoadingBody', 'lblLoadingProduct'],
              Height='lblLoadingTitle.Height + lblLoadingBody.Height + lblLoadingProduct.Height + 80',
              PaddingTop='24', PaddingBottom='24', PaddingLeft='16', PaddingRight='16',
              LayoutGap='16', Fill=SURFACE, BorderColor=BORDER, BorderThickness='1',
              RadiusTopLeft='12', RadiusTopRight='12', RadiusBottomLeft='12', RadiusBottomRight='12')
    setp('conLoading', LayoutJustifyContent='If(Parent.Height > conLoadingCard.Height + 40, LayoutJustifyContent.Center, LayoutJustifyContent.Start)')
    setp('conLoadingCard', Width='Parent.Width - 32', AlignInContainer='AlignInContainer.Stretch')
    setp('scrLoading', LoadingSpinner='LoadingSpinner.Controls')
    setp('lblLoadingTitle', Text='"Stok bilgileri hazırlanıyor"', Height='56', AutoHeight='true', Size='18', Live='Live.Polite')
    setp('lblLoadingBody', Text='"Depolardaki kullanılabilir ve rezerve miktarlar kontrol ediliyor."',
         Height='60', AutoHeight='true', Size='14', Color=MUTED)
    setp('lblLoadingProduct', Text='"Aranan ürün: " & varAcceptedText', Height='40', AutoHeight='true', Fill=SOFT, Size='14', PaddingLeft='12', PaddingRight='12')
    new('tmrLoadingFlow', 'tmrLoadingVisual', 'scrLoading')
    setp('tmrLoadingVisual', Duration='1600', Repeat='true', AutoStart='false',
         Start='App.ActiveScreen = scrLoading', Reset='App.ActiveScreen <> scrLoading',
         OnTimerStart='false', OnTimerEnd='false', Visible='false')
    container('conLoadingProgress', 'conLoadingCard', [], horizontal=True, Height='4', Fill=BORDER)
    setp('conLoadingProgress', Width='Parent.Width - 32', AlignInContainer='AlignInContainer.Stretch')
    new('shpWarehouseDivider', 'shpLoadingProgress', 'conLoadingProgress')
    setp('shpLoadingProgress', X='0', Y='0', Height='4',
         Width='Max(24, Parent.Width * tmrLoadingVisual.Value / tmrLoadingVisual.Duration)',
         Fill=ORANGE, Visible='true', FillPortions='0', LayoutMinWidth='0', LayoutMinHeight='0', OnSelect='false')
    cs['conLoadingCard']['Children'].insert(0, cs['conLoadingCard']['Children'].pop())
    setp('conLoadingCard', Height='lblLoadingTitle.Height + lblLoadingBody.Height + lblLoadingProduct.Height + 100')

    root('conResults', 'scrResults', [], LayoutOverflowY='LayoutOverflow.Hide')
    container('conResultsHeader', 'conResults', ['lblResultsTitle', 'btnResultsScanAgain'], horizontal=True, Height='48')
    setp('conResultsHeader', Width='Parent.Width - 32', AlignInContainer='AlignInContainer.Stretch')
    setp('lblResultsTitle', Text='"Depo stokları"', Size='18', Height='48', FillPortions='1', Width='Parent.Width - 132')
    setp('btnResultsScanAgain', Text='"Yeni ürün ara"', AccessibleLabel='"Yeni ürün ara"', Width='124', Height='44', Size='12',
         Fill=WHITE, Color=ORANGE, HoverFill=SOFT, HoverColor=ORANGE, PressedFill=SOFT, PressedColor=ORANGE)
    for n in ['lblResultsCount', 'galProducts', 'lblResultsEmptyTitle', 'lblResultsEmptyBody']:
        move(n, 'conResults')
        setp(n, X='0', Y='0', Width='Parent.Width - 32', FillPortions='0', LayoutMinWidth='0', LayoutMinHeight='0', AlignInContainer='AlignInContainer.Stretch')
    setp('lblResultsCount', Height='24', Size='12', Color=MUTED)
    setp('btnResultsEmptyMark', Visible='false')
    setp('lblResultsEmptyTitle', Height='64', AutoHeight='true', Size='18')
    setp('lblResultsEmptyBody', Height='80', AutoHeight='true', Size='14')
    setp('galProducts', FillPortions='1', Height='Max(0, Parent.Height - 128)', TemplateSize='84', TemplatePadding='8',
         AutoHeight='true', Items='colProductGroups', LayoutMinHeight='0', Fill=SURFACE)
    cs['galProducts']['VariantName'] = 'galleryVariableTemplateHeight'
    expanded = 'varProductExpanded && varExpandedItemNumber = ThisItem.ItemNumber'
    # Restore one nested, non-scrolling warehouse gallery per expanded product.
    def walk(v):
        if isinstance(v, dict):
            yield v
            for x in v.values(): yield from walk(x)
        elif isinstance(v, list):
            for x in v: yield from walk(x)
    originals = {c['Name']: c for n, b in original.items() if n.startswith('Controls/')
                 for c in walk(json.loads(b)) if 'Rules' in c and 'Name' in c}
    gal = copy.deepcopy(originals['galWarehouses'])
    gal['Children'] = [copy.deepcopy(c) for c in gal['Children'] if c['Template']['Name'] == 'galleryTemplate']
    for c in gal['Children']: c['Children'] = []
    gal['Parent'] = 'galProducts'
    cs['galWarehouses'] = gal
    cs['galProducts']['Children'].append(gal)
    changed['galWarehouses'] = {r['Property'] for r in gal['Rules']}
    for c in gal['Children']: cs[c['Name']] = c
    for n in ['lblWarehouseName', 'lblWarehouseAvailable', 'lblWarehouseReserved', 'shpWarehouseDivider']:
        move(n, 'galWarehouses')
    setp('galWarehouses', Items='ThisItem.WarehouseRows', X='16', Y='lblWarehouseHeading.Y + lblWarehouseHeading.Height',
         Width='Parent.TemplateWidth - 32', Height=f'If({expanded}, CountRows(ThisItem.WarehouseRows) * 64, 0)',
         TemplateSize='64', TemplatePadding='0', AutoHeight='false', ShowScrollbar='false', Visible=expanded,
         DelayItemLoading='false', Fill=WHITE)
    for n in ['lblProductName', 'lblProductNumber', 'lblProductChevron', 'btnProductToggle']:
        setp(n, Visible='true')
    setp('lblProductName', X='16', Y='12', Width='Parent.TemplateWidth - 76', Height='24', AutoHeight='true', Size='15')
    setp('lblProductNumber', X='16', Y='lblProductName.Y + lblProductName.Height + 4',
         Height='24', Width='Parent.TemplateWidth - 32', Size='12', Color=MUTED, FontWeight='FontWeight.Normal',
         Text='ThisItem.ItemNumber & " · " & CountRows(Distinct(ThisItem.WarehouseRows, InventoryWarehouseId)) & " ambar"')
    setp('lblProductChevron', X='Parent.TemplateWidth - 56', Y='8', Width='44', Height='44',
         Text=f'If({expanded}, "⌄", "›")', Size='24', Color=ORANGE)
    setp('btnProductToggle', X='4', Y='0', Width='Parent.TemplateWidth - 8', Height='lblProductNumber.Y + lblProductNumber.Height + 12')
    setp('lblProductConflict', X='16', Y='btnProductToggle.Height', Width='Parent.TemplateWidth - 32',
         Visible=f'{expanded} && ThisItem.HasNameConflict', Height=f'If({expanded} && ThisItem.HasNameConflict, 48, 0)', Size='12')
    new('lblProductNumber', 'lblWarehouseHeading', 'galProducts')
    setp('lblWarehouseHeading', X='16', Y='lblProductConflict.Y + lblProductConflict.Height', Width='(Parent.TemplateWidth - 32) * 0.45',
         Height=f'If({expanded}, 32, 0)', Visible=expanded, Text='"Ambar"', Size='12', Color=ORANGE, OnSelect='false')
    new('lblWarehouseHeading', 'lblAvailableHeading', 'galProducts')
    setp('lblAvailableHeading', X='16 + (Parent.TemplateWidth - 32) * 0.45', Width='(Parent.TemplateWidth - 32) * 0.55',
         Text='"Kullanılabilir"', Align='Align.Right')
    setp('btnProductCard', X='4', Y='0', Width='Parent.TemplateWidth - 8',
         Height='galWarehouses.Y + galWarehouses.Height + 8', BorderColor=BORDER, Fill=WHITE, DisabledFill=WHITE)
    setp('lblWarehouseName', X='0', Y='8', Width='Parent.TemplateWidth * 0.45', Height='48', Size='13',
         Visible='true', AutoHeight='false')
    setp('lblWarehouseAvailable', X='Parent.TemplateWidth * 0.45', Y='8', Width='Parent.TemplateWidth * 0.55',
         Height='24', Size='12', Visible='true', FontWeight='FontWeight.Semibold',
         Text='IfError(Text(Value(ThisItem.AvailableOnHandQuantity), "0.########", "tr-TR"), "—")')
    setp('lblWarehouseReserved', X='Parent.TemplateWidth * 0.45', Y='32', Width='Parent.TemplateWidth * 0.55',
         Height='24', Size='12', Align='Align.Right', Fill=WHITE, Color=MUTED,
         Text='"Rezerve: " & IfError(Text(Value(ThisItem.ReservedOnHandQuantity), "0.########", "tr-TR"), "—")',
         Visible='!IsBlank(ThisItem.ReservedOnHandQuantity) && ThisItem.ReservedOnHandQuantity <> 0')
    setp('shpWarehouseDivider', X='0', Y='63', Width='Parent.TemplateWidth', Height='1', Fill=BORDER, Visible='true')

    root('conError', 'scrError', ['lblErrorTitle', 'lblErrorBody', 'btnErrorRetry', 'btnErrorHome'], LayoutGap='16')
    setp('btnErrorMark', Visible='false')
    setp('lblErrorTitle', Height='56', AutoHeight='true', Size='20')
    setp('lblErrorBody', Height='80', AutoHeight='true', Size='14', Color=MUTED)
    setp('btnErrorRetry', Height='48', Size='16')
    setp('btnErrorHome', Height='48', Size='16', Fill=WHITE, Color=ORANGE, HoverFill=SOFT, HoverColor=ORANGE, PressedFill=SOFT, PressedColor=ORANGE)
    # Keep runtime tree order and Studio's ordering metadata in agreement after
    # reparenting. In particular, the old hint ZIndex must not precede the input.
    for n, c in cs.items():
        if c['Template']['Name'] == 'timer':
            setp(n, Font="Font.'Open Sans'")
        if c['Template']['Name'] == 'groupContainer':
            for index, child in enumerate(c['Children'], 1):
                setp(child['Name'], ZIndex=str(index))
            if c['Parent'].startswith('scr'):
                setp(n, ZIndex='100')
