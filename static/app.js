const api = {
  async employees() { return fetch('/employees').then(r=>r.json()); },
  async addDemoEmployee() {
    const name = 'Demo ' + Math.floor(Math.random()*1000);
    const res = await fetch('/employees', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ name, position:'Staff', password:'demo' }) });
    return res.json();
  },
  async latestLog(empId){ const r = await fetch(`/LogInOut/${empId}`); return r.ok ? r.json() : null; },
  async toggleLog(empId, coords, locName){
    const r = await fetch('/LogInOut', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ employee_id: empId, latitude: coords?.latitude, longitude: coords?.longitude, location_name: locName||'Office' }) });
    return r.json();
  },
  async nearest(lat,lng){ const r = await fetch('/get_nearest_locations', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ lat, lng, limit:5 }) }); return r.json(); },
  async uploadPhoto(empId, file){ const fd = new FormData(); fd.append('file', file); const r = await fetch(`/upload_photo/${empId}`, { method:'POST', body: fd }); return r.json(); }
}

let currentCoords = null;

async function refreshEmployees(){
  const sel = document.getElementById('employeeSelect');
  sel.innerHTML = '';
  const list = await api.employees();
  if (!Array.isArray(list) || !list.length) {
    const opt = document.createElement('option'); opt.value=''; opt.textContent='No employees yet'; sel.appendChild(opt);
    return;
  }
  for (const e of list){ const opt = document.createElement('option'); opt.value = e.id; opt.textContent = `${e.id} - ${e.name}`; sel.appendChild(opt); }
  if (sel.value) updateLatestLog();
}

function updateStatusBadge(text){ document.getElementById('statusBadge').textContent = text; }

async function updateLatestLog(){
  const sel = document.getElementById('employeeSelect');
  const empId = parseInt(sel.value||'0', 10);
  if (!empId) { document.getElementById('latestLog').textContent = '-'; return; }
  const log = await api.latestLog(empId);
  document.getElementById('latestLog').textContent = JSON.stringify(log || {message:'No logs'}, null, 2);
  if (log && log.check_in_time && !log.check_out_time) updateStatusBadge('Checked In');
  else if (log && log.check_in_time && log.check_out_time) updateStatusBadge('Checked Out');
  else updateStatusBadge('-');
}

function getLocation(){
  const locText = document.getElementById('locText');
  if (!navigator.geolocation){ locText.textContent = 'Geolocation not supported'; return; }
  navigator.geolocation.getCurrentPosition(pos=>{
    currentCoords = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
    locText.textContent = `Got location: ${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)}`;
  }, err=>{ locText.textContent = 'Location error: ' + err.message; });
}

async function checkInOut(){
  const sel = document.getElementById('employeeSelect');
  const empId = parseInt(sel.value||'0', 10);
  if (!empId) { toast('Select an employee'); return; }
  if (!currentCoords) { toast('Get location first'); return; }
  const res = await api.toggleLog(empId, currentCoords, 'Field');
  toast(res.message || 'Done');
  await updateLatestLog();
}

async function findNearest(){
  if (!currentCoords) { toast('Get location first'); return; }
  const list = await api.nearest(currentCoords.latitude, currentCoords.longitude);
  const holder = document.getElementById('nearestList');
  holder.innerHTML = list.map(l=>`<div class="row"><strong>${l.name}</strong><span class="muted">${l.distance}m</span></div>`).join('') || '<div class="muted">No locations</div>';
}

async function uploadPhoto(){
  const sel = document.getElementById('employeeSelect');
  const empId = parseInt(sel.value||'0', 10);
  if (!empId) { toast('Select an employee'); return; }
  const file = document.getElementById('photoFile').files[0];
  if (!file) { toast('Choose a file'); return; }
  const res = await api.uploadPhoto(empId, file);
  toast(res.message || 'Uploaded');
  const link = document.getElementById('viewPhotoBtn'); link.href = `/get_photo/${empId}`;
}

window.addEventListener('DOMContentLoaded', ()=>{
  document.getElementById('refreshEmployeesBtn').addEventListener('click', refreshEmployees);
  document.getElementById('addDemoEmpBtn').addEventListener('click', async()=>{ await api.addDemoEmployee(); await refreshEmployees(); });
  document.getElementById('getLocationBtn').addEventListener('click', getLocation);
  document.getElementById('checkInOutBtn').addEventListener('click', checkInOut);
  document.getElementById('nearestBtn').addEventListener('click', findNearest);
  document.getElementById('uploadBtn').addEventListener('click', uploadPhoto);
  document.getElementById('employeeSelect').addEventListener('change', updateLatestLog);
  refreshEmployees();
});
