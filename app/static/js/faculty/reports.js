SAAuth.ensureAuthenticated('faculty', '/faculty/login');

document.getElementById('faculty-logout')?.addEventListener('click', ()=> SAAuth.logout('faculty', '/faculty/login'));

let lastReportRecords = [];
let currentReportPage = 1;
let currentReportSize = 15;

function formatLocalDate(date){
    const y = date.getFullYear();
    const m = String(date.getMonth()+1).padStart(2,'0');
    const d = String(date.getDate()).padStart(2,'0');
    return `${y}-${m}-${d}`;
}

function setDatePreset(preset){
    const startEl = document.getElementById('report-start-date');
    const endEl = document.getElementById('report-end-date');
    const today = new Date();
    if(preset === 'today'){
        const d = formatLocalDate(today);
        if(startEl) startEl.value = d;
        if(endEl) endEl.value = d;
    }else if(preset === 'week'){
        const day = today.getDay(); // 0-6, Sun=0
        const diffToMon = (day + 6) % 7; // Mon=0
        const monday = new Date(today); monday.setDate(today.getDate() - diffToMon);
        const sunday = new Date(monday); sunday.setDate(monday.getDate() + 6);
        if(startEl) startEl.value = formatLocalDate(monday);
        if(endEl) endEl.value = formatLocalDate(sunday);
    }else if(preset === 'month'){
        const first = new Date(today.getFullYear(), today.getMonth(), 1);
        const last = new Date(today.getFullYear(), today.getMonth()+1, 0);
        if(startEl) startEl.value = formatLocalDate(first);
        if(endEl) endEl.value = formatLocalDate(last);
    }
}

function setActivePreset(active){
    const ids = ['preset-today','preset-week','preset-month'];
    for(const id of ids){
        const el = document.getElementById(id);
        if(!el) continue;
        if((active && id === `preset-${active}`)){
            el.classList.remove('btn-secondary');
            el.classList.add('btn-primary');
        }else{
            el.classList.remove('btn-primary');
            el.classList.add('btn-secondary');
        }
    }
}

document.getElementById('preset-today')?.addEventListener('click', ()=>{ setDatePreset('today'); setActivePreset('today'); document.getElementById('report-filters')?.dispatchEvent(new Event('submit', { cancelable: true })); });
document.getElementById('preset-week')?.addEventListener('click', ()=>{ setDatePreset('week'); setActivePreset('week'); document.getElementById('report-filters')?.dispatchEvent(new Event('submit', { cancelable: true })); });
document.getElementById('preset-month')?.addEventListener('click', ()=>{ setDatePreset('month'); setActivePreset('month'); document.getElementById('report-filters')?.dispatchEvent(new Event('submit', { cancelable: true })); });
document.getElementById('preset-reset')?.addEventListener('click', ()=>{
    // Clear all filters
    const form = document.getElementById('report-filters');
    if(!form) return;
    // Clear selects and inputs to defaults
    const subject = form.querySelector('select[name="subject"]'); if(subject) subject.value = '';
    const division = form.querySelector('select[name="division"]'); if(division) division.value = '';
    const faculty = form.querySelector('select[name="faculty_id"]'); if(faculty) faculty.value = '';
    const status = form.querySelector('select[name="status"]'); if(status) status.value = '';
    const startEl = document.getElementById('report-start-date'); if(startEl) startEl.value = '';
    const endEl = document.getElementById('report-end-date'); if(endEl) endEl.value = '';
    const sizeSel = form.querySelector('#report-page-size'); if(sizeSel) sizeSel.value = '15';
    const sortSel = form.querySelector('#report-sort'); if(sortSel) sortSel.value = 'date';
    const orderSel = form.querySelector('#report-order'); if(orderSel) orderSel.value = 'desc';
    const pageInput = document.getElementById('report-page'); if(pageInput) pageInput.value = '1';
    setActivePreset(null);
    // Do NOT auto-load on reset per requirement
});

document.getElementById('report-filters')?.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const tableBody = document.getElementById('report-rows');
    const countEl = document.getElementById('report-count');
    const emptyEl = document.getElementById('report-empty');
    const loadBtn = document.getElementById('report-load');
    const pageInfo = document.getElementById('report-page-info');
    const prevBtn = document.getElementById('report-page-prev');
    const nextBtn = document.getElementById('report-page-next');
    const pageInput = document.getElementById('report-page');
    const sizeSelect = document.getElementById('report-page-size');
    const formData = new FormData(e.target);
    if(!formData.get('faculty_id')){ formData.delete('faculty_id'); }
    currentReportSize = parseInt(sizeSelect?.value || formData.get('size') || '15', 10) || 15;
    currentReportPage = parseInt(pageInput?.value || formData.get('page') || '1', 10) || 1;
    formData.set('size', String(currentReportSize));
    formData.set('page', String(currentReportPage));
    // If start/end provided, drop single date param if present on form
    formData.delete('date');
    const params = new URLSearchParams(Object.fromEntries(formData.entries()));
    if(loadBtn){ loadBtn.disabled = true; loadBtn.textContent = 'Loading...'; }
    emptyEl?.classList.add('hidden');
    tableBody.innerHTML = '';
    const res = await SA.apiFetch('faculty', `/faculty/view_reports?${params.toString()}`, { method: 'GET', auth: true });
    const data = await res.json();
    if(loadBtn){ loadBtn.disabled = false; loadBtn.textContent = 'Load'; }
    tableBody.innerHTML = '';
    if(res.ok && Array.isArray(data.records)){
        lastReportRecords = data.records || [];
        const total = Number(data.total || 0);
        const page = Number(data.page || currentReportPage);
        const size = Number(data.size || currentReportSize);
        const startIdx = total ? (page - 1) * size + 1 : 0;
        const endIdx = Math.min(page * size, total);
        if(countEl){
            countEl.textContent = String(total);
            // Add animation class to parent for visual feedback
            const countValueEl = countEl.parentElement;
            if(countValueEl){
                countValueEl.classList.add('animate');
                setTimeout(()=> countValueEl.classList.remove('animate'), 500);
            }
        }
        if(pageInfo){ pageInfo.textContent = total ? `Showing ${startIdx}–${endIdx} of ${total}` : ''; }
        if(prevBtn){ prevBtn.disabled = page <= 1; }
        if(nextBtn){ nextBtn.disabled = endIdx >= total; }
        if(pageInput){ pageInput.value = String(page); }
        for(const r of data.records){
            const tr = document.createElement('tr');
            tr.innerHTML = `<td class="py-2 pl-4 pr-4">${r.student_name}</td>
            <td class="py-2 pr-4">${r.roll_number}</td>
            <td class="py-2 pr-4">${r.division}</td>
            <td class="py-2 pr-4">${r.faculty_name || 'N/A'}</td>
            <td class="py-2 pr-4">${r.subject}</td>
            <td class="py-2 pr-4">${r.date}</td>
            <td class="py-2 pr-4">${r.status}</td>
            <td class="py-2 pr-4"><button class="btn-secondary text-xs" data-action="delete-attendance" data-id="${r.id}">Mark Absent</button></td>`;
            tableBody.appendChild(tr);
        }
        if((data.records || []).length === 0){ emptyEl?.classList.remove('hidden'); }
    }else{
        lastReportRecords = [];
        if(countEl){ countEl.textContent = '0'; }
        if(pageInfo){ pageInfo.textContent = ''; }
        if(prevBtn){ prevBtn.disabled = true; }
        if(nextBtn){ nextBtn.disabled = true; }
        const tr = document.createElement('tr');
        tr.innerHTML = `<td class="py-2 pl-4 pr-4 text-red-600" colspan="8">${data.message || 'No records or failed to load'}</td>`;
        tableBody.appendChild(tr);
    }
});

document.getElementById('report-page-prev')?.addEventListener('click', ()=>{
    const pageInput = document.getElementById('report-page');
    const form = document.getElementById('report-filters');
    const sizeSelect = document.getElementById('report-page-size');
    const page = Math.max(1, (parseInt(pageInput?.value || '1', 10) || 1) - 1);
    if(pageInput) pageInput.value = String(page);
    if(sizeSelect) currentReportSize = parseInt(sizeSelect.value || '15', 10) || 15;
    form?.dispatchEvent(new Event('submit', { cancelable: true }));
});

document.getElementById('report-page-next')?.addEventListener('click', ()=>{
    const pageInput = document.getElementById('report-page');
    const form = document.getElementById('report-filters');
    const sizeSelect = document.getElementById('report-page-size');
    const page = (parseInt(pageInput?.value || '1', 10) || 1) + 1;
    if(pageInput) pageInput.value = String(page);
    if(sizeSelect) currentReportSize = parseInt(sizeSelect.value || '15', 10) || 15;
    form?.dispatchEvent(new Event('submit', { cancelable: true }));
});

document.getElementById('report-filters')?.addEventListener('change', (e)=>{
    const target = e.target;
    if(!(target instanceof HTMLElement)) return;
    if(target.id !== 'report-page'){
        const pageInput = document.getElementById('report-page');
        if(pageInput) pageInput.value = '1';
    }
    // If manual date changes, clear active preset highlight
    if(target.id === 'report-start-date' || target.id === 'report-end-date'){
        setActivePreset(null);
    }
});

// Export buttons
document.getElementById('report-download-csv')?.addEventListener('click', async ()=>{
    const form = document.getElementById('report-filters');
    if(!form) return;
    const formData = new FormData(form);
    formData.delete('page');
    const params = new URLSearchParams(Object.fromEntries(formData.entries()));
    params.set('format', 'csv');
    try{
        const res = await SA.apiFetch('faculty', `/faculty/export_reports?${params.toString()}`, { method: 'GET', auth: true });
        const blob = await res.blob();
        if(!res.ok){ alert('Failed to export CSV'); return; }
        const ts = new Date().toISOString().slice(0,10);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `attendance-${ts}.csv`;
        document.body.appendChild(a); a.click();
        setTimeout(()=>{ URL.revokeObjectURL(url); a.remove(); }, 0);
    }catch(err){ alert('Network error'); }
});

document.getElementById('report-download-excel')?.addEventListener('click', async ()=>{
    const form = document.getElementById('report-filters');
    if(!form) return;
    const formData = new FormData(form);
    formData.delete('page');
    const params = new URLSearchParams(Object.fromEntries(formData.entries()));
    params.set('format', 'excel');
    try{
        const res = await SA.apiFetch('faculty', `/faculty/export_reports?${params.toString()}`, { method: 'GET', auth: true });
        const blob = await res.blob();
        if(!res.ok){ alert('Failed to export Excel'); return; }
        const ts = new Date().toISOString().slice(0,10);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `attendance-${ts}.xls`;
        document.body.appendChild(a); a.click();
        setTimeout(()=>{ URL.revokeObjectURL(url); a.remove(); }, 0);
    }catch(err){ alert('Network error'); }
});

// Populate faculty dropdown on load
(async ()=>{
    const select = document.getElementById('report-faculty-select');
    if(!select) return;
    try{
        const res = await SA.apiFetch('faculty', '/faculty/list', { method: 'GET', auth: true });
        const data = await res.json();
        if(res.ok && Array.isArray(data.faculty)){
            for(const f of data.faculty){
                const opt = document.createElement('option');
                opt.value = String(f.id);
                opt.textContent = f.full_name;
                select.appendChild(opt);
            }
        }
    }catch(err){ /* ignore populate errors */ }
})();

// Delete (Mark Absent)
document.getElementById('report-rows')?.addEventListener('click', async (e)=>{
    const target = e.target;
    if(!(target instanceof HTMLElement)) return;
    if(target.dataset.action !== 'delete-attendance') return;
    const id = target.dataset.id;
    if(!id) return;
    const ok = window.confirm('Are you sure you want to mark this record as Absent? This will delete it.');
    if(!ok) return;
    target.disabled = true;
    try{
        const res = await SA.apiFetch('faculty', `/faculty/attendance/${id}`, { method: 'DELETE', auth: true });
        const data = await res.json();
        if(!res.ok){ alert(data.message || 'Failed to delete record'); return; }
        document.getElementById('report-filters')?.dispatchEvent(new Event('submit', { cancelable: true }));
    }catch(err){ alert('Network error'); }
    finally{ target.disabled = false; }
});


