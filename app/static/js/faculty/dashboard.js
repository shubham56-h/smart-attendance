SAAuth.ensureAuthenticated('faculty', '/faculty/login');

document.getElementById('faculty-logout')?.addEventListener('click', ()=> SAAuth.logout('faculty', '/faculty/login'));

let lastReportRecords = [];
let currentReportPage = 1;
let currentReportSize = 15;
let lastReportQuery = '';

document.getElementById('faculty-update-location')?.addEventListener('click', async ()=>{
	const msg = document.getElementById('faculty-location-msg');
	try{
		const coords = await SA.getCurrentPosition();
		const res = await SA.apiFetch('faculty', '/faculty/update_location', { method: 'POST', body: coords, auth: true });
		const data = await res.json();
		SA.showMsg(msg, data.message || (res.ok ? 'Location updated' : 'Failed'), res.ok);
	}catch(err){ SA.showMsg(msg, 'Location permission denied or error', false); }
});

document.getElementById('generate-otp')?.addEventListener('click', async ()=>{
	const msg = document.getElementById('otp-msg');
	try{
		const res = await SA.apiFetch('faculty', '/faculty/generate_otp', { method: 'POST', auth: true });
		const data = await res.json();
		if(res.ok){ SA.showMsg(msg, `OTP: ${data.otp} (expires in 5 minutes)`); }
		else{ SA.showMsg(msg, data.message || 'Failed to generate OTP', false); }
	}catch(err){ SA.showMsg(msg, 'Network error', false); }
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
    // If faculty_id is empty, remove it to avoid sending empty param
    if(!formData.get('faculty_id')){ formData.delete('faculty_id'); }
    // Manage page/size
    currentReportSize = parseInt(sizeSelect?.value || formData.get('size') || '15', 10) || 15;
    currentReportPage = parseInt(pageInput?.value || formData.get('page') || '1', 10) || 1;
    formData.set('size', String(currentReportSize));
    formData.set('page', String(currentReportPage));
    const params = new URLSearchParams(Object.fromEntries(formData.entries()));
    lastReportQuery = params.toString();
    // UI loading state
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
			tr.innerHTML = `<td class=\"py-2 pl-4 pr-4\">${r.student_name}</td>
			<td class=\"py-2 pr-4\">${r.roll_number}</td>
			<td class=\"py-2 pr-4\">${r.division}</td>
			<td class=\"py-2 pr-4\">${r.faculty_name || 'N/A'}</td>
			<td class=\"py-2 pr-4\">${r.subject}</td>
			<td class=\"py-2 pr-4\">${r.date}</td>
			<td class=\"py-2 pr-4\">${r.status}</td>
			<td class=\"py-2 pr-4\"><button class=\"btn-secondary text-xs\" data-action=\"delete-attendance\" data-id=\"${r.id}\">Mark Absent</button></td>`;
			tableBody.appendChild(tr);
		}
        if((data.records || []).length === 0){ emptyEl?.classList.remove('hidden'); }
	}else{
        lastReportRecords = [];
        if(countEl){ 
            countEl.textContent = '0';
            // Add animation class to parent for visual feedback
            const countValueEl = countEl.parentElement;
            if(countValueEl){
                countValueEl.classList.add('animate');
                setTimeout(()=> countValueEl.classList.remove('animate'), 500);
            }
        }
        if(pageInfo){ pageInfo.textContent = ''; }
        if(prevBtn){ prevBtn.disabled = true; }
        if(nextBtn){ nextBtn.disabled = true; }
		const tr = document.createElement('tr');
		tr.innerHTML = `<td class=\"py-2 pl-4 pr-4 text-red-600\" colspan=\"8\">${data.message || 'No records or failed to load'}</td>`;
		tableBody.appendChild(tr);
	}
});

// Pagination controls
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

// Reset to first page when filters (except page/size) change
document.getElementById('report-filters')?.addEventListener('change', (e)=>{
    const target = e.target;
    if(!(target instanceof HTMLElement)) return;
    // if user changed any filter control except the hidden page input, reset page to 1
    if(target.id !== 'report-page'){
        const pageInput = document.getElementById('report-page');
        if(pageInput) pageInput.value = '1';
    }
});

function downloadBlob(content, mimeType, filename){
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(()=>{ URL.revokeObjectURL(url); a.remove(); }, 0);
}

function toCsv(records){
    const headers = ['Student','Roll','Division','Faculty','Subject','Date','Status'];
    const lines = [headers.join(',')];
    for(const r of records){
        const row = [
            r.student_name,
            r.roll_number,
            r.division,
            r.faculty_name || 'N/A',
            r.subject,
            r.date,
            r.status
        ].map(v=>{
            const s = v==null ? '' : String(v);
            const needsQuote = /[",\n]/.test(s);
            const escaped = s.replace(/"/g, '""');
            return needsQuote ? `"${escaped}"` : escaped;
        });
        lines.push(row.join(','));
    }
    return lines.join('\n');
}

function toExcelHtml(records){
    const header = '<tr><th>Student</th><th>Roll</th><th>Division</th><th>Faculty</th><th>Subject</th><th>Date</th><th>Status</th></tr>';
    const rows = records.map(r=>
        `<tr>`+
        `<td>${r.student_name||''}</td>`+
        `<td>${r.roll_number||''}</td>`+
        `<td>${r.division||''}</td>`+
        `<td>${r.faculty_name||'N/A'}</td>`+
        `<td>${r.subject||''}</td>`+
        `<td>${r.date||''}</td>`+
        `<td>${r.status||''}</td>`+
        `</tr>`
    ).join('');
    const table = `<table>${header}${rows}</table>`;
    // Excel can open HTML table with this MIME type
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>${table}</body></html>`;
    return html;
}

document.getElementById('report-download-csv')?.addEventListener('click', async ()=>{
    // Download ALL filtered data as CSV via export endpoint
    const form = document.getElementById('report-filters');
    if(!form) return;
    const formData = new FormData(form);
    // Remove pagination for export
    formData.delete('page');
    // Keep size if you want, but server ignores it; ensure filters only
    const params = new URLSearchParams(Object.fromEntries(formData.entries()));
    params.set('format', 'csv');
    try{
        const res = await SA.apiFetch('faculty', `/faculty/export_reports?${params.toString()}`, { method: 'GET', auth: true });
        const blob = await res.blob();
        if(!res.ok){ alert('Failed to export CSV'); return; }
        const ts = new Date().toISOString().slice(0,10);
        downloadBlob(blob, 'text/csv;charset=utf-8;', `attendance-${ts}.csv`);
    }catch(err){ alert('Network error'); }
});

document.getElementById('report-download-excel')?.addEventListener('click', async ()=>{
    // Download ALL filtered data as Excel-compatible HTML via export endpoint
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
        downloadBlob(blob, 'application/vnd.ms-excel;charset=utf-8;', `attendance-${ts}.xls`);
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

// Handle delete (Mark Absent) with confirmation via event delegation
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
        // reload current results by programmatically re-submitting the filters form
        document.getElementById('report-filters')?.dispatchEvent(new Event('submit', { cancelable: true }));
    }catch(err){ alert('Network error'); }
    finally{ target.disabled = false; }
});


