"""Explicit classic surfaces, fixed-row accordion, and fresh-image dispatch guard."""
import copy


def apply_fixes(controls, docs, setp, get, changed):
    white = 'RGBA(255, 255, 255, 1)'
    orange = 'RGBA(194, 65, 12, 1)'
    ink = 'RGBA(55, 65, 81, 1)'
    soft = 'RGBA(255, 247, 237, 1)'

    # Native classic controls have explicit fills for every visual state.
    # The source package's ModernThemes entry supplies no palette definition.
    for name,c in list(controls.items()):
        if c['Template']['Name'] != 'PowerApps_CoreControls_ButtonCanvas':
            continue
        old = {r['Property']:r['InvariantScript'] for r in c['Rules']}
        c['Template'] = copy.deepcopy(controls['lblProductName']['Template'])
        c['Template'].update(Id='http://microsoft.com/appmagic/button',Name='button',Version='2.2.0')
        c['VariantName']=''
        c['Rules']=[]
        c['ControlPropertyState']=[]
        changed[name]=set()
        keep=['X','Y','Width','Height','Visible','DisplayMode','Text','OnSelect','AccessibleLabel','TabIndex','ZIndex']
        setp(name,**{p:old[p] for p in keep if p in old})
        decorative=old.get('DisplayMode')=='DisplayMode.Disabled'
        setp(name, Font='Font.OpenSans', Size='16', FontWeight='FontWeight.Semibold',
             Fill=white if decorative else orange, Color=ink if decorative else white,
             HoverFill=soft if decorative else 'RGBA(154, 52, 18, 1)',
             PressedFill=soft if decorative else 'RGBA(124, 45, 18, 1)',
             HoverColor=ink if decorative else white, PressedColor=ink if decorative else white,
             DisabledFill=white, DisabledColor=ink, DisabledBorderColor='RGBA(229, 231, 235, 1)',
             BorderColor='RGBA(229, 231, 235, 1)' if decorative else orange,
             HoverBorderColor=orange, PressedBorderColor=orange, BorderThickness='1',
             FocusedBorderColor=orange, FocusedBorderThickness='3',
             RadiusTopLeft='12',RadiusTopRight='12',RadiusBottomLeft='12',RadiusBottomRight='12')
        if decorative:setp(name,TabIndex='-1')

    setp('App',OnStart=get('App','OnStart')+';\nSet(varProductExpanded, false);\nSet(varScanReady, false);\nSet(varScanEntryImage, "")')
    # Close dispatch before touching the OCR control. A screen transition is not a scan.
    setp('scrScan',OnVisible='''Set(varScanReady, false);
Set(varScanAccepted, false);
Set(varFlowCallStarted, false);
Set(varLoadingExecutionStarted, false);
Set(varOcrEmpty, false);
Set(varAcceptedText, "");
Set(varErrorMessage, "");
Set(varResultJson, "");
Set(varScanEntryImage, TextRecognizer1.OriginalImage);
Reset(TextRecognizer1);
Set(varScanReady, true)''',OnHidden='Set(varScanReady, false)')
    ocr=get('TextRecognizer1','OnChange')
    ocr=ocr.replace('App.ActiveScreen = scrScan && !varScanAccepted && !varFlowCallStarted,',
        '''varScanReady && App.ActiveScreen = scrScan && !varScanAccepted && !varFlowCallStarted &&
    !IsBlank(TextRecognizer1.OriginalImage) && TextRecognizer1.OriginalImage <> varScanEntryImage,''')
    # Reset-to-empty does not warn or navigate. It makes selecting the same file again valid.
    ocr='''If(
    varScanReady && App.ActiveScreen = scrScan && IsBlank(TextRecognizer1.OriginalImage),
    Set(varScanEntryImage, "")
);
'''+ocr
    setp('TextRecognizer1',OnChange=ocr, DefaultImage='""', ImageDisplayed='false',
         Height='96',Y='246',FillColor=orange,FontColor=white,
         DisabledFill=white,DisabledColor=ink)
    setp('btnScanSurface',Height='180',Y='214',Fill=white,DisabledFill=white)
    setp('lblScanHint',Y='418',Height='80')
    setp('btnScanEmptyCard',Y='418')
    setp('lblScanEmptyTitle',Y='430')
    setp('lblScanEmptyBody',Y='468')
    for n in ['shpScanGuideTopLeft','shpScanGuideTopRight','shpScanGuideBottomLeft','shpScanGuideBottomRight']:
        setp(n,Visible='false')

    dispatch='App.ActiveScreen = scrLoading && varScanAccepted && !IsBlank(varAcceptedText) && !varFlowCallStarted && !varLoadingExecutionStarted'
    timer=get('tmrLoadingFlow','OnTimerEnd')
    timer=timer.replace('varScanAccepted && !IsBlank(varAcceptedText) && !varFlowCallStarted && !varLoadingExecutionStarted',dispatch,1)
    setp('tmrLoadingFlow',AutoStart='false',Start=dispatch,
         Reset='App.ActiveScreen <> scrLoading',AutoPause='true',Repeat='false',OnTimerEnd=timer)

    # ItemNumber groups remain the canonical data. Only the display is flattened.
    # Each header/detail occupies a real fixed-height gallery row, with one scrollbar.
    rows='''Ungroup(
    ForAll(
        colProductGroups As product,
        {
            DisplayRows: Ungroup(
                Table(
                    {
                        Rows: Table(
                            {
                                IsProduct: true,
                                ItemNumber: product.ItemNumber,
                                ProductName: product.ProductName,
                                HasNameConflict: product.HasNameConflict,
                                WarehouseCount: CountRows(Distinct(product.WarehouseRows, InventoryWarehouseId)),
                                InventoryWarehouseId: "",
                                AvailableOnHandQuantity: 0,
                                ReservedOnHandQuantity: 0
                            }
                        )
                    },
                    {
                        Rows: ForAll(
                            Filter(product.WarehouseRows, varProductExpanded && varExpandedItemNumber = product.ItemNumber) As warehouse,
                            {
                                IsProduct: false,
                                ItemNumber: product.ItemNumber,
                                ProductName: product.ProductName,
                                HasNameConflict: false,
                                WarehouseCount: 0,
                                InventoryWarehouseId: warehouse.InventoryWarehouseId,
                                AvailableOnHandQuantity: warehouse.AvailableOnHandQuantity,
                                ReservedOnHandQuantity: warehouse.ReservedOnHandQuantity
                            }
                        )
                    }
                ),
                Rows
            )
        }
    ),
    DisplayRows
)'''
    setp('scrResults',OnVisible='Set(varProductExpanded, false);\nSet(varExpandedItemNumber, Blank())')
    setp('galProducts',AutoHeight='false',TemplateSize='112',TemplatePadding='8',Items=rows,
         Fill=white,ShowScrollbar='true',Selectable='false')
    controls['galProducts']['VariantName']='galleryVertical'
    gal=controls['galProducts']
    # Runtime children of a gallery are siblings of its empty galleryTemplate.
    # Move the warehouse labels into this one gallery and remove the nested gallery.
    warehouse_names=['lblWarehouseName','lblWarehouseAvailable','lblWarehouseReserved','shpWarehouseDivider']
    gal['Children']=[c for c in gal['Children'] if c['Name']!='galWarehouses']
    for c in gal['Children']:
        if c.get('Template',{}).get('Name')=='galleryTemplate':c['Children']=[]
    gal['Children'].append(controls['lblProductChevron'])
    for n in warehouse_names:
        c=controls[n]
        c['Parent']='galProducts'
        gal['Children'].append(c)
    removed=[n for n,c in controls.items() if c.get('Parent')=='galWarehouses']+['galWarehouses']
    for n in removed:controls.pop(n,None)
    # Re-add retained controls (their Parent has already changed).
    expanded='varProductExpanded && varExpandedItemNumber = ThisItem.ItemNumber'
    toggle='''Set(varProductExpanded, !varProductExpanded || varExpandedItemNumber <> ThisItem.ItemNumber);
Set(varExpandedItemNumber, ThisItem.ItemNumber)'''
    setp('btnProductCard',Height='108',Y='0',DisplayMode='DisplayMode.View',Fill=white,
         BorderColor='If(ThisItem.IsProduct, RGBA(229, 231, 235, 1), RGBA(255, 255, 255, 1))',
         OnSelect='false',TabIndex='-1',ZIndex='1')
    setp('lblProductName',X='24',Y='10',Height='48',AutoHeight='false',Size='16',
         Text='Coalesce(ThisItem.ProductName, ThisItem.ItemNumber, "Ürün")',
         Tooltip='ThisItem.ProductName',Visible='ThisItem.IsProduct',OnSelect=toggle,ZIndex='2')
    setp('lblProductNumber',Y='62',Height='26',Visible='ThisItem.IsProduct',OnSelect=toggle,ZIndex='3',
         Text='ThisItem.ItemNumber & "  •  " & ThisItem.WarehouseCount & " ambar"')
    setp('lblProductConflict',Y='88',Height='18',Size='9',
         Visible='ThisItem.IsProduct && ThisItem.HasNameConflict',ZIndex='4')
    setp('lblProductChevron',Y='16',Visible='ThisItem.IsProduct',Text=f'If({expanded}, "−", "+")',
         OnSelect=toggle,ZIndex='5')
    setp('lblWarehouseName',X='24',Y='18',Height='34',Width='Parent.TemplateWidth * 0.57 - 24',
         Visible='!ThisItem.IsProduct',ZIndex='6')
    setp('lblWarehouseAvailable',X='Parent.TemplateWidth * 0.61',Y='16',Height='48',
         Width='Parent.TemplateWidth * 0.39 - 24',Visible='!ThisItem.IsProduct',ZIndex='7')
    setp('lblWarehouseReserved',X='24',Y='60',Width='Parent.TemplateWidth * 0.57 - 24',ZIndex='8',
         Visible='!ThisItem.IsProduct && ThisItem.AvailableOnHandQuantity < 3 && ThisItem.ReservedOnHandQuantity <> 0')
    setp('shpWarehouseDivider',X='24',Y='107',Width='Parent.TemplateWidth - 48',Height='1',
         Visible='!ThisItem.IsProduct',ZIndex='9')
    # One keyboard-focusable, topmost hit target per product header.
    hit=copy.deepcopy(controls['btnProductCard'])
    hit.update(Name='btnProductToggle',ControlUniqueId='2002',PublishOrderIndex=2002)
    controls['btnProductToggle']=hit
    gal['Children'].append(hit)
    setp('btnProductToggle',Visible='ThisItem.IsProduct',DisplayMode='DisplayMode.Edit',
         Fill='RGBA(255, 255, 255, 0)',HoverFill='RGBA(255, 247, 237, 0.15)',
         PressedFill='RGBA(255, 237, 213, 0.25)',BorderThickness='0',TabIndex='0',
         Text='""',OnSelect=toggle,ZIndex='20',
         AccessibleLabel='Coalesce(ThisItem.ProductName, ThisItem.ItemNumber) & If(varProductExpanded && varExpandedItemNumber = ThisItem.ItemNumber, ", açık. Kapat", ", kapalı. Ambarları aç")')

    # All visible surfaces are explicit; no dark theme-dependent fills remain.
    for name,c in controls.items():
        if c['Template']['Name']=='screen':setp(name,Fill=white)
        if c['Template']['Name']=='label':setp(name,Font='Font.OpenSans')
    setp('shpHomeTopGlow',Fill=white)
