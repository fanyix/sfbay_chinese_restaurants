const U = () => new Proxy(function(){}, { get:(t,k)=> k===Symbol.toPrimitive ? (()=>'') : (k==='length'?0:(k==='contains'?()=>true:(k==='distance'?()=>1234:U()))), apply:()=>U(), construct:()=>U(), set:()=>true });
var L = U();
var innerWidth=390, innerHeight=844;
var matchMedia = q => ({ matches: q.includes('max-width') ? MOBILE : q.includes('hover: hover') ? !MOBILE : false, addEventListener(){} });
var addEventListener = ()=>{}; var alert = ()=>{};
var navigator = { userAgent: MOBILE ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)' };
var getComputedStyle = () => ({ top: '47px' });
const els = {};
function El(id){ const o={id, children:[], value:'', checked:false, innerHTML:'', textContent:'', dataset:{}, hidden:false, offsetTop:100, offsetHeight: id==='side'?776:(id==='sab-probe'?34:30), clientHeight:300, scrollTop:0,
  style:{ setProperty(k,v){ o.style[k]=v }, removeProperty(){} },
  appendChild(c){this.children.push(c)}, insertAdjacentHTML(p,h){this.innerHTML+=h}, querySelectorAll(){return []}, querySelector(){return null}, setAttribute(k,v){this[k]=v}, getAttribute(k){return this[k]},
  addEventListener(){}, blur(){}, setPointerCapture(){},
  classList:{ s:new Set(), add(c){this.s.add(c)}, remove(c){this.s.delete(c)}, contains(c){return this.s.has(c)}, toggle(c,f){ f?this.s.add(c):this.s.delete(c)} } }; return o; }
var document = { getElementById: id => els[id] || (els[id]=El(id)), createElement: t => El(t), querySelectorAll: () => [], querySelector: s => els[s] || (els[s]=El(s)) };
