(() => {
  'use strict';
  const panel=document.getElementById('assistant-panel'), toggle=document.getElementById('assistant-toggle');
  if(!panel||!toggle) return;
  const form=document.getElementById('assistant-form'), input=document.getElementById('assistant-question');
  const log=document.getElementById('assistant-messages'), status=document.getElementById('assistant-status');
  let busy=false;
  const el=(tag,text,className)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;};
  function close(){panel.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.focus();}
  toggle.addEventListener('click',()=>{if(!panel.hidden){close();return;}panel.hidden=false;toggle.setAttribute('aria-expanded','true');input.focus();});
  document.getElementById('assistant-close').addEventListener('click',close);
  panel.addEventListener('keydown',e=>{if(e.key==='Escape'){close();e.preventDefault();}});
  const safeURL=(value)=>{try{const url=new URL(value,window.location.origin);return url.origin===window.location.origin&&url.protocol===window.location.protocol?url.href:null;}catch{return null;}};
  function link(label,url){const node=el('a',label);const target=safeURL(url);if(target)node.href=target;return node;}
  function quoteLink(name){return link('Solicitar cotización','/cotizacion?servicio='+encodeURIComponent(name));}
  function card(product){
    const node=el('article',undefined,'assistant-card');
    if(product.image){const url=safeURL(product.image);if(url){const image=el('img');image.src=url;image.alt='Imagen publicada de '+product.name;image.loading='lazy';node.append(image);}}
    else node.append(el('span','AFCyber · '+product.category,'card-type'));
    node.append(el('h3',product.name),el('p',product.description));
    const list=el('ul');for(const feature of product.features||[])list.append(el('li',feature));if(list.children.length)node.append(list);
    node.append(el('p','Plataforma: '+(product.platform||'No publicada')),el('p','Estado comercial: '+product.commercial_status));
    const links=el('div',undefined,'assistant-links');links.append(link('Conocer más',product.url));if(product.quote_available)links.append(quoteLink(product.name));links.append(link('Hablar con un asesor','/contacto'));node.append(links);return node;
  }
  function show(data){
    const response=el('div',undefined,'assistant-message');response.append(el('p',data.text));
    for(const category of data.categories||[]){const button=el('button',category);button.type='button';button.dataset.assistantQuery='Categoría: '+category;response.append(button);}
    if(data.comparison?.length){const wrapper=el('div',undefined,'assistant-compare'),table=el('table'),thead=el('thead'),header=el('tr');header.append(el('th','Aspecto'));for(const p of data.products)header.append(el('th',p.name));thead.append(header);table.append(thead);const body=el('tbody');for(const row of data.comparison){const tr=el('tr');tr.append(el('th',row.label));for(const [index,value] of row.values.entries()){const cell=el('td',value);cell.dataset.product=data.products[index].name;cell.setAttribute('aria-label',data.products[index].name+': '+value);tr.append(cell);}body.append(tr);}table.append(body);wrapper.append(table);response.append(wrapper);}
    for(const product of data.products||[])response.append(card(product));
    for(const service of data.services||[]){const node=el('article',undefined,'assistant-card');node.append(el('h3',service.name),el('p',service.description),link('Ver servicio',service.url),quoteLink(service.name));response.append(node);}
    const links=el('div',undefined,'assistant-links');for(const item of data.links||[])links.append(link(item.label,item.url));response.append(links);
    if(data.sources?.length)response.append(el('small','Fuente: información pública de AFCyber Solutions.'));
    log.append(response);while(log.children.length>40)log.firstElementChild.remove();response.scrollIntoView({block:'nearest',behavior:'instant'});
  }
  async function ask(message){
    if(busy||!message.trim()||message.length>600)return;
    busy=true;form.querySelector('button').disabled=true;status.textContent='Buscando información pública…';
    log.append(el('div',message,'assistant-message user'));
    const body=new FormData();body.set('message',message);body.set('_csrf_token',window.AFCYBER.csrf);
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),15000);
    try{const response=await fetch('/asistente/responder',{method:'POST',body,credentials:'same-origin',signal:controller.signal});if(!response.headers.get('content-type')?.includes('application/json'))throw new Error('No se pudo procesar la consulta. Recarga la página e inténtalo de nuevo.');const data=await response.json();if(!response.ok)throw new Error(data.error||'No se pudo responder.');show(data);status.textContent='';}
    catch(error){status.textContent=error.name==='AbortError'?'La consulta tardó demasiado. Intenta de nuevo.':error.message==='Failed to fetch'?'No se pudo conectar. Intenta de nuevo.':error.message;}
    finally{clearTimeout(timeout);busy=false;form.querySelector('button').disabled=false;}
  }
  form.addEventListener('submit',event=>{event.preventDefault();const message=input.value;input.value='';ask(message);});
  panel.addEventListener('click',event=>{const button=event.target.closest('button[data-assistant-query]');if(button)ask(button.dataset.assistantQuery);});
})();
