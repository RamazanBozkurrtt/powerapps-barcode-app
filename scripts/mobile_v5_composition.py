"""Screen composition only. Existing events, data bindings and timers are retained."""
import copy

FONT = "Font.'Open Sans'"
WHITE = 'RGBA(255, 255, 255, 1)'
INK = 'RGBA(31, 41, 55, 1)'
MUTED = 'RGBA(75, 85, 99, 1)'
ORANGE = 'RGBA(194, 65, 12, 1)'
SOFT = 'RGBA(255, 247, 237, 1)'
BORDER = 'RGBA(229, 231, 235, 1)'
SURFACE = 'RGBA(249, 250, 251, 1)'
CLEAR = 'RGBA(0, 0, 0, 0)'


def apply_composition(cs, setp, get, changed):
    uid = max(int(c['ControlUniqueId']) for c in cs.values()) + 1

    def clone(source, name, parent):
        nonlocal uid
        c = copy.deepcopy(cs[source])
        c.update(Name=name, Parent=parent, ControlUniqueId=str(uid),
                 PublishOrderIndex=uid, Children=[])
        uid += 1
        cs[name] = c
        cs[parent]['Children'].append(c)
        changed[name] = {r['Property'] for r in c['Rules']}
        return c

    def move(name, parent):
        c = cs[name]
        old_parent = cs[c['Parent']]
        old_parent['Children'] = [x for x in old_parent['Children'] if x['Name'] != name]
        cs[parent]['Children'].append(c)
        c['Parent'] = parent
        setp(name, X='0', Y='0', Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight',
             FillPortions='0', LayoutMinWidth='0', LayoutMinHeight='0',
             AlignInContainer='AlignInContainer.Stretch')

    def group(name, parent, children=(), **props):
        clone('conSearchForm', name, parent)
        setp(name, X='0', Y='0', Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight',
             Height='0', FillPortions='0', LayoutMinWidth='0', LayoutMinHeight='0',
             AlignInContainer='AlignInContainer.Stretch', LayoutGap='12',
             PaddingTop='0', PaddingBottom='0', PaddingLeft='0', PaddingRight='0',
             LayoutDirection='LayoutDirection.Vertical', LayoutAlignItems='LayoutAlignItems.Stretch',
             LayoutJustifyContent='LayoutJustifyContent.Start', LayoutOverflowY='LayoutOverflow.Hide',
             Fill=CLEAR, BorderThickness='0', Visible='true')
        for n in children:
            move(n, name)
        setp(name, **props)

    def label(name, parent, text, **props):
        clone('lblHomeTitle', name, parent)
        setp(name, Text=text, Height='28', Size='14', Font=FONT, AutoHeight='true',
             FontWeight='FontWeight.Normal', Align='Align.Left', VerticalAlign='VerticalAlign.Top',
             Color=INK, Fill=CLEAR, Visible='true', OnSelect='false', TabIndex='-1',
             X='0', Y='0', Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight',
             FillPortions='0', LayoutMinWidth='0', LayoutMinHeight='0',
             PaddingTop='0', PaddingBottom='0', PaddingLeft='0', PaddingRight='0',
             AlignInContainer='AlignInContainer.Stretch')
        setp(name, **props)

    def card(name, padding=20, fill=WHITE):
        setp(name, Fill=fill, BorderColor=BORDER, BorderThickness='1',
             RadiusTopLeft='16', RadiusTopRight='16', RadiusBottomLeft='16', RadiusBottomRight='16',
             PaddingLeft=str(padding), PaddingRight=str(padding),
             PaddingTop=str(padding), PaddingBottom=str(padding))

    def fit(name):
        # Vertical containers grow with their actual children, including wrapped text.
        nodes = [x['Name'] for x in cs[name]['Children']]
        terms = [f'{n}.Height' for n in nodes]
        terms += [f'Self.LayoutGap * {max(0, len(nodes)-1)}', 'Self.PaddingTop', 'Self.PaddingBottom']
        setp(name, Height=' + '.join(terms))

    for n in ['conHome', 'conSearch', 'conLoading', 'conResults', 'conError']:
        setp(n, Width='Min(Parent.Width, 560)', X='(Parent.Width - Self.Width) / 2',
             Height='Parent.Height', PaddingLeft='20', PaddingRight='20',
             PaddingTop='24', PaddingBottom='24', LayoutGap='20', Fill=CLEAR,
             LayoutJustifyContent='LayoutJustifyContent.Start')
    for n in ['scrHome', 'scrScan', 'scrLoading', 'scrResults', 'scrError']:
        setp(n, Fill=SURFACE)
    for n, c in list(cs.items()):
        if c['Template']['Name'] == 'label':
            setp(n, Font=FONT, Fill=CLEAR)
        if c['Template']['Name'] == 'button':
            setp(n, Font=FONT)
    for n in ['btnScan', 'btnSearchProduct', 'btnErrorRetry', 'btnErrorHome', 'btnResultsScanAgain']:
        setp(n, Align='Align.Center', PaddingLeft='12', PaddingRight='12')

    # Home: an editorial introduction, one useful action card, one short note.
    group('conHomeIntro', 'conHome', ['lblHomeEyebrow', 'lblHomeTitle', 'lblHomeCardBody'])
    setp('lblHomeEyebrow', Text='"STOK ASİSTANI"', Height='24', Size='13', Color=ORANGE,
         FontWeight='FontWeight.Semibold', Align='Align.Left')
    setp('lblHomeTitle', Text='"Ürünü bulun." & Char(10) & "Stokları görün."',
         Height='96', Size='If(App.Width < 360, 26, 28)', AutoHeight='true', Align='Align.Left')
    setp('lblHomeCardBody', Text='"Depolardaki stok durumunu ürün etiketi, ürün adı veya ürün koduyla hızlıca sorgulayın."',
         Height='80', Size='15', AutoHeight='true', Align='Align.Left', Color=MUTED)
    fit('conHomeIntro')
    group('conHomeAction', 'conHome', ['lblHomeCardTitle'])
    card('conHomeAction')
    setp('lblHomeCardTitle', Visible='true', Text='"Ürün arayın"', Height='32',
         Size='18', FontWeight='FontWeight.Semibold', Align='Align.Left', AutoHeight='true')
    label('lblHomeActionBody', 'conHomeAction', '"Etiketi fotoğraflayın veya ürün bilgilerini yazarak başlayın."',
          Height='52', Color=MUTED)
    move('btnScan', 'conHomeAction')
    setp('btnScan', Text='"Ürün ara"', Height='52', Size='16')
    fit('conHomeAction')
    move('lblHomeFooter', 'conHome')
    setp('lblHomeFooter', Text='"Kullanılabilir ve rezerve stokları tek ekranda görüntüleyin."',
         Height='48', Size='13', Color=MUTED, Align='Align.Left', AutoHeight='true')
    setp('conHome', LayoutGap='24',
         PaddingTop='Max(24, Min(88, (Parent.Height - conHomeIntro.Height - conHomeAction.Height - lblHomeFooter.Height - 72) / 3))')

    # Search: header, purpose, and a bounded form card with two distinct methods.
    move('lblScanInstruction', 'conSearch')
    cs['conSearch']['Children'] = [cs[n] for n in ['conSearchHeader', 'lblScanInstruction', 'conSearchForm']]
    setp('conSearch', LayoutGap='16',
         PaddingTop='Max(16, Min(40, (Parent.Height - conSearchHeader.Height - lblScanInstruction.Height - conSearchForm.Height - 56) / 3))')
    setp('conSearchHeader', Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight',
         Fill=CLEAR, Height='48', LayoutAlignItems='LayoutAlignItems.Center')
    setp('btnScanBack', Width='76', Fill=CLEAR, HoverFill=SOFT, Text='"‹ Geri"')
    setp('lblScanTitle', Text='"Ürün ara"', Size='20', Align='Align.Left',
         Width='Parent.Width - btnScanBack.Width - Parent.LayoutGap')
    setp('lblScanInstruction', Text='"Etiketi fotoğraflayın ya da ürün adı veya koduyla arayın."',
         Height='48', Size='14', Align='Align.Left', Color=MUTED, AutoHeight='true')
    setp('conSearchForm', Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight', LayoutGap='16')
    card('conSearchForm', padding=16)
    group('conPhotoMethod', 'conSearchForm')
    card('conPhotoMethod', padding=16, fill=SOFT)
    setp('conPhotoMethod', BorderThickness='0', LayoutGap='8')
    label('lblPhotoTitle', 'conPhotoMethod', '"Fotoğraf ile ürün bul"', Height='32', Size='17', FontWeight='FontWeight.Semibold')
    label('lblPhotoBody', 'conPhotoMethod', '"Ürün etiketini fotoğraflayın veya galeriden seçin."', Height='48', Color=MUTED, Size='14')
    move('TextRecognizer1', 'conPhotoMethod')
    setp('TextRecognizer1', Text='"Fotoğraf çek / seç"', Height='48', ButtonHeight='48',
         FillColor=WHITE, FontColor=ORANGE, BorderColor=ORANGE, BorderThickness='1',
         CommandBarFontSize='14', CommandBarIconSize='20')
    fit('conPhotoMethod')
    group('conMethodDivider', 'conSearchForm', LayoutDirection='LayoutDirection.Horizontal',
          LayoutAlignItems='LayoutAlignItems.Center', Height='24', LayoutGap='12')
    cs['conMethodDivider']['VariantName'] = 'horizontalAutoLayoutContainer'
    for n in ['shpMethodLeft', 'shpMethodRight']:
        clone('shpWarehouseDivider', n, 'conMethodDivider')
        setp(n, Fill=BORDER, Height='1', Width='(Parent.Width - 72) / 2',
             X='0', Y='0', Visible='true', OnSelect='false', FillPortions='1',
             LayoutMinWidth='0', LayoutMinHeight='0', AlignInContainer='AlignInContainer.Center')
    label('lblMethodOr', 'conMethodDivider', '"ya da"', Height='24', Width='48', AutoHeight='false',
          Align='Align.Center', Color=MUTED, Size='13', AlignInContainer='AlignInContainer.Center')
    cs['conMethodDivider']['Children'] = [cs[n] for n in ['shpMethodLeft', 'lblMethodOr', 'shpMethodRight']]
    group('conManualMethod', 'conSearchForm', ['lblManualProductName', 'txtProductName', 'btnSearchProduct'], LayoutGap='12')
    setp('lblManualProductName', Text='"Ürün adı / kodu"', Height='28', Size='14',
         Align='Align.Left', FontWeight='FontWeight.Semibold', AutoHeight='true')
    setp('txtProductName', Height='48', Fill=WHITE, BorderColor='RGBA(156, 163, 175, 1)',
         HintText='"Örn. 57047 veya ürün adı"', Size='14', PaddingLeft='12')
    setp('btnSearchProduct', Text='"Stok sorgula"', Height='48', Size='15',
         DisabledFill='RGBA(209, 213, 219, 1)', DisabledColor='RGBA(75, 85, 99, 1)',
         DisabledBorderColor='RGBA(209, 213, 219, 1)')
    fit('conManualMethod')
    move('lblScanHint', 'conSearchForm')
    setp('lblScanHint', Text='If(varOcrEmpty, "Etiket okunamadı. Yeniden fotoğraflayın veya ürün bilgisini yazın.", "İki yöntemden birini kullanmanız yeterli.")',
         Height='44', Size='13', Align='Align.Left', AutoHeight='true', Color=MUTED)
    fit('conSearchForm')

    # Loading: a real visual spinner driven by the existing UI timer; no new state.
    setp('conLoadingProgress', Visible='false', Height='0')
    move('conLoadingProgress', 'scrLoading')
    setp('conLoadingProgress', Visible='false', Width='0', Height='0')
    image = clone('shpWarehouseDivider', 'imgLoadingSpinner', 'conLoadingCard')
    image['Template'].update(Id='http://microsoft.com/appmagic/image', Name='image', Version='2.2.0')
    image.update(Rules=[], ControlPropertyState=[], VariantName='')
    changed['imgLoadingSpinner'] = set()
    setp('imgLoadingSpinner', X='0', Y='0', Width='48', Height='48',
         AlignInContainer='AlignInContainer.Center', LayoutMinWidth='48', LayoutMinHeight='48',
         FillPortions='0', Visible='true', AccessibleLabel='"Stok sorgulanıyor"', TabIndex='-1',
         OnSelect='false', ImagePosition='ImagePosition.Fit',
         Image='"data:image/svg+xml;utf8," & EncodeUrl("<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 48 48\'><circle cx=\'24\' cy=\'24\' r=\'19\' fill=\'none\' stroke=\'#F3E8DF\' stroke-width=\'4\'/><path d=\'M24 5a19 19 0 0 1 19 19\' fill=\'none\' stroke=\'#C2410C\' stroke-width=\'4\' stroke-linecap=\'round\' transform=\'rotate(" & Text(tmrLoadingVisual.Value * 360 / tmrLoadingVisual.Duration, "0", "en-US") & " 24 24)\'/></svg>")')
    card('conLoadingCard', padding=24)
    setp('conLoadingCard', Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight', LayoutGap='16')
    setp('lblLoadingTitle', Text='"Stok bilgileri hazırlanıyor"', Height='56', Size='19',
         FontWeight='FontWeight.Semibold', Align='Align.Center', AutoHeight='true')
    setp('lblLoadingBody', Text='"Aranan ürün"', Height='24', Size='13', Align='Align.Center', Color=MUTED)
    setp('lblLoadingProduct', Text='varAcceptedText', Height='48', Size='20',
         FontWeight='FontWeight.Semibold', Align='Align.Center', AutoHeight='true', Fill=CLEAR)
    cs['conLoadingCard']['Children'] = [cs[n] for n in ['imgLoadingSpinner', 'lblLoadingTitle', 'lblLoadingBody', 'lblLoadingProduct']]
    fit('conLoadingCard')
    setp('conLoading', PaddingTop='Max(24, (Parent.Height - conLoadingCard.Height) / 2)', LayoutGap='0')

    # Results: compact two-line summary and separate warehouse/quantity columns.
    setp('conResults', PaddingTop='16', PaddingBottom='16', LayoutGap='12')
    for n in ['conResultsHeader', 'lblResultsCount', 'galProducts', 'lblResultsEmptyTitle', 'lblResultsEmptyBody']:
        setp(n, Width='Parent.Width - Parent.PaddingLeft - Parent.PaddingRight')
    setp('conResultsHeader', Fill=CLEAR, LayoutAlignItems='LayoutAlignItems.Center')
    setp('lblResultsTitle', Text='If(App.Width < 360, "Sonuçlar", "Stok sonuçları")',
         Size='18', AutoHeight='false', Height='48', VerticalAlign='VerticalAlign.Middle')
    setp('btnResultsScanAgain', Text='"Yeni arama"', Width='120', Size='13', PaddingLeft='8', PaddingRight='8')
    setp('lblResultsTitle', Width='Parent.Width - btnResultsScanAgain.Width - Parent.LayoutGap')
    setp('lblResultsCount', Size='13', Height='24', Color=MUTED, Align='Align.Left')
    setp('galProducts', Height='Max(0, Parent.Height - Parent.PaddingTop - Parent.PaddingBottom - conResultsHeader.Height - lblResultsCount.Height - 24)',
         TemplateSize='76', TemplatePadding='8', Fill=CLEAR)
    expanded = 'varProductExpanded && varExpandedItemNumber = ThisItem.ItemNumber'
    setp('btnProductCard', X='0', Y='0', Width='Parent.TemplateWidth', Fill=WHITE,
         BorderThickness='1', BorderColor=BORDER, DisabledFill=WHITE, DisabledBorderColor=BORDER,
         RadiusTopLeft='12', RadiusTopRight='12', RadiusBottomLeft='12', RadiusBottomRight='12',
         Height=f'If({expanded}, galWarehouses.Y + galWarehouses.Height + 12, btnProductToggle.Height)')
    setp('lblProductName', X='16', Y='12', Width='Parent.TemplateWidth - 64', Height='26',
         Size='15', AutoHeight='true', FontWeight='FontWeight.Semibold', Align='Align.Left')
    setp('lblProductNumber', Text='ThisItem.ItemNumber', X='16',
         Y='lblProductName.Y + lblProductName.Height + 2', Width='Parent.TemplateWidth - 120',
         Height='24', Size='13', Color=MUTED)
    label('lblProductWarehouseCount', 'galProducts',
          'CountRows(Distinct(ThisItem.WarehouseRows, InventoryWarehouseId)) & " ambar"',
          X='Parent.TemplateWidth - 100', Y='lblProductNumber.Y', Width='84', Height='24',
          AutoHeight='false', Size='13', Color=MUTED, Align='Align.Right')
    setp('lblProductChevron', X='Parent.TemplateWidth - 48', Y='4', Width='44', Height='44',
         Size='22', Color=ORANGE, Align='Align.Center')
    setp('btnProductToggle', X='0', Y='0', Width='Parent.TemplateWidth',
         Height='lblProductNumber.Y + lblProductNumber.Height + 12',
         Fill=CLEAR, HoverFill='RGBA(194, 65, 12, 0.04)', PressedFill='RGBA(194, 65, 12, 0.08)',
         FocusedBorderColor=ORANGE, FocusedBorderThickness='2')
    setp('lblProductConflict', Y='btnProductToggle.Height', X='16', Width='Parent.TemplateWidth - 32',
         Size='13', Height=f'If({expanded} && ThisItem.HasNameConflict, 48, 0)')
    setp('lblWarehouseHeading', X='16', Y='lblProductConflict.Y + lblProductConflict.Height',
         Width='(Parent.TemplateWidth - 32) * 0.48', Height=f'If({expanded}, 32, 0)',
         Size='12', FontWeight='FontWeight.Semibold', Color=MUTED)
    setp('lblAvailableHeading', X='16 + (Parent.TemplateWidth - 32) * 0.48',
         Width='(Parent.TemplateWidth - 32) * 0.52', Y='lblWarehouseHeading.Y',
         Height='lblWarehouseHeading.Height', Size='12', Color=MUTED)
    setp('galWarehouses', X='16', Y='lblWarehouseHeading.Y + lblWarehouseHeading.Height',
         Width='Parent.TemplateWidth - 32', Height=f'If({expanded}, CountRows(ThisItem.WarehouseRows) * 52, 0)', TemplateSize='52')
    setp('lblWarehouseName', X='0', Y='6', Width='Parent.TemplateWidth * 0.48',
         Height='40', Size='13', AutoHeight='false', VerticalAlign='VerticalAlign.Middle')
    setp('lblWarehouseAvailable', X='Parent.TemplateWidth * 0.48', Y='4',
         Width='Parent.TemplateWidth * 0.52', Height='24', Size='14', Align='Align.Right')
    setp('lblWarehouseReserved', X='Parent.TemplateWidth * 0.48', Y='28',
         Width='Parent.TemplateWidth * 0.52', Height='22', Size='12', Align='Align.Right')
    setp('shpWarehouseDivider', X='0', Y='51', Height='1', Width='Parent.TemplateWidth')

    # Error/empty states share the same content-sized surface and readable copy.
    group('conErrorCard', 'conError', ['lblErrorTitle', 'lblErrorBody', 'btnErrorRetry', 'btnErrorHome'], LayoutGap='16')
    card('conErrorCard', padding=24)
    setp('lblErrorTitle', Height='56', Size='21', Align='Align.Left', AutoHeight='true')
    setp('lblErrorBody', Height='80', Size='14', Align='Align.Left', AutoHeight='true', Color=MUTED)
    setp('btnErrorRetry', Height='48', Size='15')
    setp('btnErrorHome', Height='48', Size='15')
    fit('conErrorCard')
    setp('conError', PaddingTop='Max(24, Min(120, (Parent.Height - conErrorCard.Height) / 3))')
    setp('lblResultsEmptyTitle', Size='20', Align='Align.Left', Height='64')
    setp('lblResultsEmptyBody', Size='14', Align='Align.Left', Height='80')

    # Auto-layout order must agree with both serialized children and ZIndex.
    for c in cs.values():
        if c['Template']['Name'] == 'groupContainer':
            for index, child in enumerate(c['Children'], 1):
                setp(child['Name'], ZIndex=str(index))
    for index, n in enumerate(['btnProductCard', 'lblProductName', 'lblProductNumber',
                              'lblProductWarehouseCount', 'lblProductConflict', 'lblWarehouseHeading',
                              'lblAvailableHeading', 'galWarehouses', 'lblProductChevron'], 1):
        setp(n, ZIndex=str(index))
