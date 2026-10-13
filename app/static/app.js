(()=>{
  // Theme --------------------------------------------------------------
  const root=document.documentElement;
  const saved=localStorage.getItem('sapfx-theme')||'dark'; root.dataset.theme=saved;
  const updateTheme=()=>{document.querySelectorAll('[data-theme-label]').forEach(x=>x.textContent=root.dataset.theme==='dark'?'Claro':'Oscuro');document.querySelectorAll('[data-theme-icon]').forEach(x=>x.textContent=root.dataset.theme==='dark'?'☀':'◐')}; updateTheme();
  document.querySelectorAll('[data-theme-toggle]').forEach(b=>b.addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';localStorage.setItem('sapfx-theme',root.dataset.theme);updateTheme()}));
  // Clock/menu ---------------------------------------------------------
  const tick=()=>document.querySelectorAll('[data-live-clock]').forEach(x=>x.textContent=new Intl.DateTimeFormat('es-HN',{dateStyle:'medium',timeStyle:'short'}).format(new Date())); tick(); setInterval(tick,30000);
  const sidebar=document.querySelector('.sidebar'),backdrop=document.querySelector('[data-sidebar-backdrop]'); const closeMenu=()=>{sidebar?.classList.remove('open');backdrop?.classList.remove('show')};
  document.querySelectorAll('[data-menu-toggle]').forEach(b=>b.onclick=()=>{sidebar?.classList.toggle('open');backdrop?.classList.toggle('show')}); backdrop?.addEventListener('click',closeMenu);

  // First-run company row builder -------------------------------------
  const list=document.querySelector('[data-company-list]'),tpl=document.querySelector('#company-row-template');
  const renumber=()=>document.querySelectorAll('[data-company-row]').forEach((r,i)=>{const x=r.querySelector('.row-index');if(x)x.textContent=i+1});
  document.querySelector('[data-add-company]')?.addEventListener('click',()=>{if(!tpl||!list)return;list.appendChild(tpl.content.cloneNode(true));renumber();syncSharedCreds()});
  document.addEventListener('click',e=>{const b=e.target.closest('[data-remove-company]');if(!b)return;const rows=document.querySelectorAll('[data-company-row]');if(rows.length<=1)return; b.closest('[data-company-row]')?.remove();renumber()});
  const same=document.querySelector('[data-same-sap]');
  const syncSharedCreds=()=>{const on=!!same?.checked;document.querySelectorAll('.individual-creds').forEach(x=>x.classList.toggle('hidden-by-shared',on));document.querySelector('[data-shared-creds]')?.classList.toggle('hidden-by-shared',!on)}; same?.addEventListener('change',syncSharedCreds);syncSharedCreds();
  const toggles=document.querySelectorAll('[data-toggle-target]');toggles.forEach(x=>{const apply=()=>{const target=document.querySelector(x.dataset.toggleTarget);target?.classList.toggle('muted-group',!x.checked)};x.addEventListener('change',apply);apply()});
  const rootInput=document.querySelector('input[name="service_layer_root"]'),verInput=document.querySelector('select[name="odata_version"]'),preview=document.querySelector('[data-endpoint-preview]');
  const endpointPreview=()=>{if(!preview||!rootInput||!verInput)return;const clean=(rootInput.value||'').replace(/\/$/,'').replace(/\/v\d+$/i,'');preview.textContent=`${clean}/${verInput.value||'v2'}`};rootInput?.addEventListener('input',endpointPreview);verInput?.addEventListener('change',endpointPreview);endpointPreview();


  // Step-by-step setup with non-sensitive draft recovery ----------------
  const setupForm=document.querySelector('form.setup-form');
  if(setupForm){
    setupForm.dataset.noGuard='true';
    const sections=[...setupForm.querySelectorAll('.setup-card')];
    const chips=[...document.querySelectorAll('.setup-steps > span')];
    const key='atas-setup-draft-v1';
    let step=0;
    const nav=document.createElement('div');
    nav.className='setup-navigation';
    nav.innerHTML='<span data-setup-position></span><div><button type="button" class="btn secondary" data-setup-back>← Anterior</button> <button type="button" class="btn primary" data-setup-next>Siguiente →</button></div>';
    setupForm.appendChild(nav);
    const alerts=document.createElement('div');alerts.className='setup-error';alerts.hidden=true;
    setupForm.prepend(alerts);
    const setError=(message)=>{alerts.textContent=message;alerts.hidden=!message;if(message)alerts.scrollIntoView({block:'center'})};
    const show=(index)=>{
      step=Math.max(0,Math.min(index,sections.length-1));
      sections.forEach((section,i)=>{section.hidden=i!==step;section.classList.toggle('setup-active',i===step)});
      chips.forEach((chip,i)=>{chip.classList.toggle('active',i===step);chip.classList.toggle('completed',i<step)});
      nav.querySelector('[data-setup-back]').disabled=step===0;
      nav.querySelector('[data-setup-next]').textContent=step===sections.length-1?'Revisar y guardar ✓':'Siguiente →';
      nav.querySelector('[data-setup-position]').textContent='Paso '+(step+1)+' de '+sections.length;
      setError('');
    };
    const draft=()=>{
      const values={};
      setupForm.querySelectorAll('input,select,textarea').forEach(el=>{
        if(!el.name||el.type==='password'||el.type==='file'||el.type==='hidden')return;
        (values[el.name]??=[]).push(el.type==='checkbox'?el.checked:el.value);
      });
      try{sessionStorage.setItem(key,JSON.stringify({values,step}))}catch(_){}
    };
    try{
      const saved=JSON.parse(sessionStorage.getItem(key)||'null');
      if(saved?.values){
        const positions={};
        setupForm.querySelectorAll('input,select,textarea').forEach(el=>{
          if(!el.name||el.type==='password'||el.type==='file'||el.type==='hidden')return;
          const i=positions[el.name]||0;positions[el.name]=i+1;
          const value=saved.values[el.name]?.[i];
          if(value===undefined)return;
          if(el.type==='checkbox')el.checked=!!value;
          else el.value=value;
        });
        step=saved.step||0;
      }
    }catch(_){}
    setupForm.addEventListener('input',draft);
    setupForm.addEventListener('change',draft);
    chips.forEach((chip,i)=>{chip.tabIndex=0;chip.setAttribute('role','button');chip.onclick=()=>{draft();show(i)};chip.onkeydown=e=>{if(e.key==='Enter')show(i)}});
    nav.querySelector('[data-setup-back]').onclick=()=>{draft();show(step-1)};
    const validateStep=()=>{
      const fields=[...sections[step].querySelectorAll('[required]')].filter(el=>!el.disabled&&!el.closest('.hidden-by-shared'));
      const invalid=fields.find(el=>!el.checkValidity());
      if(invalid){invalid.reportValidity();return false}return true;
    };
    nav.querySelector('[data-setup-next]').onclick=()=>{
      if(!validateStep())return;
      draft();
      if(step===sections.length-1)setupForm.requestSubmit();
      else show(step+1);
    };
    setupForm.addEventListener('submit',async e=>{
      e.preventDefault();if(!validateStep())return;
      draft();setError('');
      nav.querySelector('[data-setup-next]').disabled=true;
      try{
        const res=await fetch('/setup',{method:'POST',body:new FormData(setupForm),credentials:'same-origin'});
        if(res.ok||res.redirected){sessionStorage.removeItem(key);location.assign(res.url&&new URL(res.url).pathname!='/setup'?res.url:'/login?welcome=1');return}
        const html=await res.text();
        const doc=new DOMParser().parseFromString(html,'text/html');
        const error=doc.querySelector('.setup-error');
        const message=error?.textContent?.trim()||'No se pudo guardar. Revise la configuración.';
        setError(message);
        const match=message.match(/(?:fuente|banco|BCH|TCR)/i);
        if(match){show(5);setError(message)}
      }catch(err){setError('No fue posible contactar al servidor. Los datos ingresados siguen en pantalla.')}
      finally{nav.querySelector('[data-setup-next]').disabled=false}
    });
    show(step);
  }

  // Toast --------------------------------------------------------------
  const layer=document.createElement('div');layer.className='toast-layer';document.body.appendChild(layer);
  const toast=(title,msg='',type='ok',timeout=4500)=>{const e=document.createElement('div');e.className=`toast-card ${type}`;e.innerHTML=`<div class="toast-icon">${type==='bad'?'!':type==='warn'?'•':'✓'}</div><div><b>${title}</b><span>${msg}</span></div><button>×</button>`;e.querySelector('button').onclick=()=>e.remove();layer.appendChild(e);requestAnimationFrame(()=>e.classList.add('show'));setTimeout(()=>{e.classList.remove('show');setTimeout(()=>e.remove(),250)},timeout)};window.SapFxToast=toast;
  const done=sessionStorage.getItem('sapfx-process-done');if(done){sessionStorage.removeItem('sapfx-process-done');toast('Proceso finalizado',done,'ok')}

  // Rich process workflow overlay ------------------------------------
  const guard=document.createElement('div');guard.className='process-guard v5';guard.innerHTML=`<div class="process-workflow-card"><div class="process-head"><div><small>ATAS</small><h2 data-p-title>Ejecutando proceso</h2><p data-p-detail>Preparando operación...</p></div><div class="process-live"><i></i> EN PROCESO</div></div><div class="process-steps">${['Banco','Validación','SAP','Comparación','Escritura','Verificación','Registro'].map((x,i)=>`<div class="p-step" data-step="${i}"><span>${i+1}</span><b>${x}</b></div>`).join('<em>→</em>')}</div><div class="process-main"><div class="process-visual"><div class="server-orb">SAP</div></div><div class="process-log"><h3>Flujo en tiempo real</h3><div data-p-log></div></div></div><div class="process-progress"><span data-p-bar></span></div><div class="process-warning">No cierre esta ventana ni inicie otra acción mientras finaliza el proceso.</div></div>`;document.body.appendChild(guard);
  let processTimer=null;
  const messages=['Trayendo datos del banco oficial...','Validando tasas, rangos y consistencia...','Conectando con SAP Service Layer...','Leyendo tasa actual y comparando valores...','Aplicando cambios si corresponde...','Verificando el valor guardado en SAP...','Registrando auditoría y resultado final...'];
  const showProcess=(title,detail)=>{clearInterval(processTimer);guard.querySelector('[data-p-title]').textContent=title||'Ejecutando proceso';guard.querySelector('[data-p-detail]').textContent=detail||'Procesando la operación solicitada.';guard.classList.add('active');document.body.classList.add('is-busy');const log=guard.querySelector('[data-p-log]');log.innerHTML='';let i=0;const advance=()=>{document.querySelectorAll('.p-step').forEach((x,n)=>x.classList.toggle('done',n<i));const current=guard.querySelector(`.p-step[data-step="${Math.min(i,6)}"]`);current?.classList.add('active');document.querySelectorAll('.p-step').forEach((x,n)=>{if(n!==Math.min(i,6))x.classList.remove('active')});if(i<messages.length){const row=document.createElement('div');row.className='process-log-row active';row.innerHTML=`<span>${new Date().toLocaleTimeString('es-HN',{hour12:false})}</span><i></i><b>${messages[i]}</b>`;log.appendChild(row);log.scrollTop=log.scrollHeight;guard.querySelector('[data-p-bar]').style.width=`${Math.min(92,10+(i+1)*12)}%`;i++}};advance();processTimer=setInterval(()=>{if(i<messages.length)advance()},850)};
  document.querySelectorAll('form').forEach(form=>{if((form.method||'get').toLowerCase()!=='post'||form.dataset.noGuard==='true')return;form.addEventListener('submit',e=>{if(e.defaultPrevented)return;const submit=e.submitter||document.activeElement;const title=submit?.dataset?.process||form.dataset.process||(submit?.textContent||'Procesando').trim();const detail=submit?.dataset?.processDetail||form.dataset.processDetail||'El sistema está procesando la operación solicitada.';sessionStorage.setItem('sapfx-process-done',title);showProcess(title,detail)})});

  // Entrance animation -------------------------------------------------
  if(!matchMedia('(prefers-reduced-motion: reduce)').matches){document.querySelectorAll('.card,.kpi-card,.company-card,.automation-card,.bank-card,.setup-card').forEach((e,i)=>{e.classList.add('reveal-item');e.style.setProperty('--reveal-delay',`${Math.min(i*35,420)}ms`);requestAnimationFrame(()=>e.classList.add('revealed'))})}

  // Guided tour --------------------------------------------------------
  const steps=[['.brand','Tu identidad','El nombre y logo configurados identifican esta instalación.'],['a[href="/companies"]','Bases SAP','Agrega CompanyDB y, si lo necesitas, un Service Layer diferente por empresa.'],['a[href="/automation"]','Automatización','Programa la revisión diaria y controla la escritura en producción.'],['a[href="/banks"]','Bancos','Consulta los conectores bancarios y su estado.'],['a[href="/transactions"]','Trazabilidad','Cada lectura, cambio, verificación o error queda registrado.'],['a[href="/reports"]','Reportes','Exporta información para Contabilidad y auditoría.'],['a[href="/settings"]','Configuración','Cambia branding, integración global y notificaciones salientes.'],['.theme-toggle','Tema visual','Alterna modo oscuro y claro cuando quieras.']];
  const tour=document.createElement('div');tour.className='tour-layer';tour.innerHTML='<div class="tour-shade"></div><div class="tour-popover"><div class="tour-kicker">RECORRIDO GUIADO</div><h3></h3><p></p><div class="tour-progress"></div><div class="tour-actions"><button data-skip>Omitir</button><div><button data-prev>Anterior</button><button class="primary" data-next>Siguiente</button></div></div></div></div>';document.body.appendChild(tour);let ti=0,target=null;const pop=tour.querySelector('.tour-popover');
  const closeTour=()=>{target?.classList.remove('tour-focus');tour.classList.remove('active');localStorage.setItem('sapfx-tour-seen','1')};
  const render=()=>{target?.classList.remove('tour-focus');const s=steps[ti];target=document.querySelector(s[0]);if(!target){if(ti<steps.length-1){ti++;return render()}return closeTour()}target.classList.add('tour-focus');target.scrollIntoView({behavior:'smooth',block:'center'});pop.querySelector('h3').textContent=s[1];pop.querySelector('p').textContent=s[2];pop.querySelector('.tour-progress').textContent=`${ti+1} de ${steps.length}`;pop.querySelector('[data-prev]').disabled=ti===0;pop.querySelector('[data-next]').textContent=ti===steps.length-1?'Finalizar':'Siguiente';setTimeout(()=>{const r=target.getBoundingClientRect(),w=Math.min(390,innerWidth-32);pop.style.width=w+'px';let top=r.bottom+14;if(top+pop.offsetHeight>innerHeight)top=Math.max(16,r.top-pop.offsetHeight-14);pop.style.top=Math.max(16,top)+'px';pop.style.left=Math.min(innerWidth-w-16,Math.max(16,r.left))+'px'},180)};
  const startTour=()=>{ti=0;tour.classList.add('active');render()};document.querySelectorAll('[data-tour-start]').forEach(b=>b.onclick=startTour);tour.querySelector('[data-skip]').onclick=closeTour;tour.querySelector('[data-prev]').onclick=()=>{if(ti){ti--;render()}};tour.querySelector('[data-next]').onclick=()=>{if(ti>=steps.length-1)return closeTour();ti++;render()};
  const params=new URLSearchParams(location.search);if(params.get('welcome')==='1'){localStorage.removeItem('sapfx-tour-seen');setTimeout(()=>{toast('Configuración completada','Bienvenido a Atas. Iniciamos un recorrido rápido.','ok',6000);startTour()},800)}
})();