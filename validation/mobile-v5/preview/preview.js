// Limited layout simulator. It is not Canvas runtime or an App Checker substitute.
const C=window.controls, P=Object.fromEntries(Object.entries(C).map(([n,c])=>[n,Object.fromEntries(c.Rules.map(r=>[r.Property,r.InvariantScript]))]));
const box=document.querySelector('#phone'), measure=document.querySelector('#measure');
let W=390,H=844,screen='scrHome',expanded=false,long=false,input='',cache={},stack=new Set();
window.previewErrors=[];
const warehouses=[['05',0],['BODIST-AND',30],['GEBZ1',1],['GEBZ2',1]].map(([InventoryWarehouseId,AvailableOnHandQuantity])=>({InventoryWarehouseId,AvailableOnHandQuantity,ReservedOnHandQuantity:0}));
function products(){return Array.from({length:17},(_,i)=>({ItemNumber:String(7217820110+i),ProductName:long&&i===0?'570477 EB — Endüstriyel bağlantı parçası, uzun ürün açıklaması':`${570477+i} EB`,WarehouseRows:warehouses,HasNameConflict:false}));}
const enumNames=new Set(['Font','FontWeight','Align','VerticalAlign','LayoutMode','LayoutDirection','LayoutAlignItems','LayoutJustifyContent','LayoutOverflow','AlignInContainer','DisplayMode','ImagePosition','BorderStyle','LoadingSpinner','Live']);
const trees=new Map();
function parse(s){
 if(trees.has(s))return trees.get(s);
 const t=s.match(/"(?:[^"]|"")*"|'[^']*'|\d+(?:\.\d+)?|[A-Za-z_][\w]*|&&|\|\||<>|<=|>=|[().,!+*/=&<>%-]/g)||[];let i=0;
 const prec={'||':1,'&&':2,'=':3,'<>':3,'<':3,'>':3,'<=':3,'>=':3,'&':4,'+':5,'-':5,'*':6,'/':6,'%':6};
 function expr(min=0){let a;const x=t[i++];
  if(x==='!'||x==='-')a=['unary',x,expr(7)];
  else if(x==='('){a=expr();if(t[i++]!==')')throw Error('missing )');}
  else if(x?.startsWith('"'))a=['literal',x.slice(1,-1).replaceAll('""','"')];
  else if(/^\d/.test(x))a=['literal',Number(x)];
  else if(x==='true'||x==='false')a=['literal',x==='true'];
  else if(t[i]==='('){i++;const args=[];if(t[i]!==')')do{args.push(expr());if(t[i]!==',')break;i++;}while(true);if(t[i++]!==')')throw Error('call )');a=['call',x,args];}
  else{const path=[x];while(t[i]==='.'){i++;path.push(t[i++].replace(/^'|'$/g,''));}a=['ref',path];}
  while(prec[t[i]]>=min){const op=t[i++];a=['binary',op,a,expr(prec[op]+1)];}return a;
 }const ast=expr();if(i!==t.length)throw Error('unparsed '+s);trees.set(s,ast);return ast;
}
function evaluate(a,n,ctx){
 if(a[0]==='literal')return a[1];
 if(a[0]==='ref'){
  const [head,...rest]=a[1];
  if(enumNames.has(head))return rest.join('.');
  let obj;
  if(head==='Parent'||head==='Self'||C[head]){
   const target=head==='Self'?n:head==='Parent'?C[n].Parent:head;
   if(!rest.length)return target;
   if(target==='App')obj={Width:W,Height:H,ActiveScreen:screen,Theme:{Colors:{Primary:'#c2410c',Darker10:'#9a3412',Lighter70:'#ffedd5'},Font:'Open Sans'}};
   else return prop(target,rest[0],ctx);
  }else if(head==='ThisItem')obj=ctx;
  else if(head in ctx)obj=ctx[head];
  else if(head==='varAcceptedText')return long?'57047 — Uzun ürün adı / kodu':'57047';
  else if(head==='varErrorMessage')return long?'Bağlantı kurulamadı. İnternet bağlantınızı kontrol ederek yeniden deneyin. Sorgulanan ürüne ilişkin stok bilgileri şu anda alınamıyor.':'Bağlantı kurulamadı. İnternet bağlantınızı kontrol edip yeniden deneyin.';
  else if(head==='varProductExpanded')return expanded;
  else if(head==='varExpandedItemNumber')return products()[0].ItemNumber;
  else if(head==='colProductGroups')return products();
  else if(head==='varScanReady')return true;
  else if(['varOcrEmpty','varScanAccepted','varFlowCallStarted'].includes(head))return false;
  else throw Error('unknown '+head);
  return rest.reduce((v,k)=>v?.[k],obj);
 }
 if(a[0]==='unary'){const v=evaluate(a[2],n,ctx);return a[1]==='!'?!v:-v;}
 if(a[0]==='binary'){const x=evaluate(a[2],n,ctx),op=a[1];if(op==='&&'&&!x)return false;if(op==='||'&&x)return true;const y=evaluate(a[3],n,ctx);return ({'+':()=>x+y,'-':()=>x-y,'*':()=>x*y,'/':()=>x/y,'%':()=>x%y,'&':()=>String(x??'')+String(y??''),'=':()=>x===y,'<>':()=>x!==y,'<':()=>x<y,'>':()=>x>y,'<=':()=>x<=y,'>=':()=>x>=y,'&&':()=>x&&y,'||':()=>x||y})[op]();}
 const f=a[1],args=a[2],ev=x=>evaluate(x,n,ctx);
 if(f==='If')return ev(args[0])?ev(args[1]):args[2]?ev(args[2]):false;
 if(f==='IfError'){try{return ev(args[0]);}catch{return ev(args[1]);}}
 if(f==='Distinct')return [...new Set(ev(args[0]).map(row=>evaluate(args[1],n,row)))];
 const v=args.map(ev);
 switch(f){case'Min':return Math.min(...v);case'Max':return Math.max(...v);case'Char':return String.fromCharCode(v[0]);case'IsBlank':return v[0]==null||v[0]==='';case'IsEmpty':return !v[0]?.length;case'TrimEnds':return v[0].trim();case'CountRows':return v[0].length;case'Coalesce':return v.find(x=>x!=null&&x!=='');case'Value':return Number(v[0]);case'Text':return typeof v[0]==='number'?v[0].toLocaleString(v[2]||'en-US',{useGrouping:false,maximumFractionDigits:v[1]==='0'?0:8}):String(v[0]);case'RGBA':return `rgba(${v.join(',')})`;case'EncodeUrl':return encodeURIComponent(v[0]);default:throw Error('unsupported '+f);}
}
function fx(formula,n,ctx){return evaluate(parse(formula),n,ctx);}
function prop(n,p,ctx={}){
 const key=n+'.'+p+'.'+(ctx.ItemNumber||ctx.InventoryWarehouseId||'');if(key in cache)return cache[key];
 if(stack.has(key))throw Error('cycle '+key);stack.add(key);
 let val;try{
  if(n==='App')val=p==='Width'?W:H;
  else if(p==='Text'&&n==='txtProductName')val=input;
  else if(p==='Value'&&n==='tmrLoadingVisual')val=350;
  else if(p==='TemplateWidth')val=prop(n,'Width',ctx)-(n==='galProducts'?16:0);
  else if(!(p in P[n]))val=({Color:'#1f2937',Fill:'transparent',BorderColor:'transparent',Visible:true,AutoHeight:false,FontWeight:'Normal',Align:'Left',VerticalAlign:'Top',Size:14})[p]??0;
  else val=fx(P[n][p],n,ctx);
  if(p==='Height'&&C[n].Template.Name==='label'&&prop(n,'AutoHeight',ctx)){
   const width=prop(n,'Width',ctx),size=prop(n,'Size',ctx)*4/3;
   Object.assign(measure.style,{width:width+'px',fontSize:size+'px',fontWeight:weight(prop(n,'FontWeight',ctx)),padding:`${prop(n,'PaddingTop',ctx)}px ${prop(n,'PaddingRight',ctx)}px ${prop(n,'PaddingBottom',ctx)}px ${prop(n,'PaddingLeft',ctx)}px`});
   measure.textContent=prop(n,'Text',ctx);val=Math.max(val,Math.ceil(measure.getBoundingClientRect().height));
  }
 }finally{stack.delete(key);}cache[key]=val;return val;
}
const weight=v=>({Bold:'700',Semibold:'600',Normal:'400',Lighter:'300'})[v]||'400';
function draw(n,parent,x,y,ctx={}){
 if(!prop(n,'Visible',ctx))return;
 const c=C[n],kind=c.Template.Name,w=prop(n,'Width',ctx),h=prop(n,'Height',ctx);
 if(['galleryTemplate','timer','hostControl','appinfo'].includes(kind))return;
 let el=document.createElement(kind==='button'?'button':kind==='text'?'input':kind==='image'?'img':'div');
 el.className='control '+(kind==='label'?'label':kind==='text'?'field':kind==='button'||kind==='TextRecognizer'?'action':'surface');el.dataset.name=n;
 Object.assign(el.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px',background:prop(n,'Fill',ctx),color:prop(n,'Color',ctx),borderColor:prop(n,'BorderColor',ctx),borderWidth:prop(n,'BorderThickness',ctx)+'px',borderRadius:prop(n,'RadiusTopLeft',ctx)+'px',fontSize:prop(n,'Size',ctx)*4/3+'px',fontWeight:weight(prop(n,'FontWeight',ctx)),textAlign:String(prop(n,'Align',ctx)).toLowerCase(),padding:`${prop(n,'PaddingTop',ctx)}px ${prop(n,'PaddingRight',ctx)}px ${prop(n,'PaddingBottom',ctx)}px ${prop(n,'PaddingLeft',ctx)}px`});
 parent.append(el);
 if(kind==='label'){el.textContent=prop(n,'Text',ctx);el.style.justifyContent=({Middle:'center',Bottom:'end'})[prop(n,'VerticalAlign',ctx)]||'start';}
 if(kind==='button'){
  el.textContent=prop(n,'Text',ctx);const disabled=prop(n,'DisplayMode',ctx)==='Disabled';el.disabled=disabled;
  if(disabled)Object.assign(el.style,{background:prop(n,'DisabledFill',ctx),color:prop(n,'DisabledColor',ctx),borderColor:prop(n,'DisabledBorderColor',ctx)});
  if(n==='btnScan')el.onclick=()=>show('scrScan');
  if(['btnScanBack','btnErrorHome'].includes(n))el.onclick=()=>show('scrHome');
  if(['btnResultsScanAgain','btnErrorRetry'].includes(n))el.onclick=()=>show('scrScan');
  if(n==='btnSearchProduct')el.onclick=()=>{show('scrLoading');setTimeout(()=>show('scrResults'),800);};
  if(n==='btnProductToggle')el.onclick=()=>{expanded=!expanded;render();};
 }
 if(kind==='text'){el.placeholder=fx(P[n].HintText,n,ctx);el.value=input;el.oninput=e=>{input=e.target.value;cache={};const b=box.querySelector('[data-name=btnSearchProduct]');const disabled=prop('btnSearchProduct','DisplayMode')==='Disabled';b.disabled=disabled;b.style.background=prop('btnSearchProduct',disabled?'DisabledFill':'Fill');b.style.color=prop('btnSearchProduct',disabled?'DisabledColor':'Color');};}
 if(kind==='TextRecognizer'){el.textContent='▣  '+prop(n,'Text',ctx);Object.assign(el.style,{fontSize:'18px',display:'flex',justifyContent:'center',alignItems:'center',color:prop(n,'FontColor',ctx),background:prop(n,'FillColor',ctx),borderRadius:'8px',border:'1px solid #c2410c'});}
 if(kind==='image')el.src=prop(n,'Image',ctx);
 if(kind==='groupContainer'){
  const px=prop(n,'PaddingLeft',ctx),py=prop(n,'PaddingTop',ctx),gap=prop(n,'LayoutGap',ctx),horizontal=prop(n,'LayoutDirection',ctx)==='Horizontal';
  if(prop(n,'LayoutOverflowY',ctx)==='Scroll')el.style.overflowY='auto';
  el.style.padding='0';let cursor=horizontal?px:py;
  for(const child of c.Children){const cn=child.Name;if(!prop(cn,'Visible',ctx))continue;const cw=prop(cn,'Width',ctx),ch=prop(cn,'Height',ctx);const align=prop(cn,'AlignInContainer',ctx);let cx=horizontal?cursor:px,cy=horizontal?py:cursor;
   if(!horizontal&&align==='Center')cx=(w-cw)/2;
   if(horizontal&&(align==='Center'||prop(n,'LayoutAlignItems',ctx)==='Center'))cy=(h-ch)/2;
   draw(cn,el,cx,cy,ctx);cursor+=(horizontal?cw:ch)+gap;
  }
  el.dataset.contentEnd=cursor-gap+(horizontal?prop(n,'PaddingRight',ctx):prop(n,'PaddingBottom',ctx));
 }
 if(kind==='gallery'){
  el.style.padding='0';if(n==='galProducts')el.style.overflowY='auto';
  const rows=n==='galProducts'?products():ctx.WarehouseRows;let cy=0;
  for(const row of rows){const pad=prop(n,'TemplatePadding',ctx),rh=n==='galProducts'?Math.max(prop(n,'TemplateSize',row),prop('btnProductCard','Height',row)):prop(n,'TemplateSize',row);const template=document.createElement('div');Object.assign(template.style,{position:'absolute',left:(n==='galProducts'?pad:0)+'px',top:cy+'px',width:prop(n,'TemplateWidth',row)+'px',height:rh+'px'});el.append(template);
   for(const child of [...c.Children].sort((a,b)=>prop(a.Name,'ZIndex',row)-prop(b.Name,'ZIndex',row))){if(child.Template.Name!=='galleryTemplate')draw(child.Name,template,prop(child.Name,'X',row),prop(child.Name,'Y',row),row);}
   cy+=rh+pad;
  }
 }
 return el;
}
function show(s){screen=s;document.querySelector('#screen').value=s;render();}
function render(){cache={};stack=new Set();window.previewErrors=[];box.innerHTML='';box.style.width=W+'px';box.style.height=H+'px';try{for(const c of C[screen].Children)draw(c.Name,box,prop(c.Name,'X'),prop(c.Name,'Y'));}catch(e){window.previewErrors.push(e.message);console.error(e);}}
window.preview={set:async(o)=>{({width:W=W,height:H=H,screen:screen=screen,expanded:expanded=expanded,long:long=long}=o);input=o.input??input;await document.fonts.ready;render();},render};
document.querySelector('#screen').onchange=e=>show(e.target.value);
document.querySelector('#viewport').onchange=e=>{[W,H]=e.target.value.split('×').map(Number);render();};
document.querySelector('#expand').onclick=()=>{expanded=!expanded;show('scrResults');};document.querySelector('#long').onclick=()=>{long=!long;render();};
document.fonts.ready.then(render);
