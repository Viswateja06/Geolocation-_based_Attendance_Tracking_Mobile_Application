let authToken = null;
let student = null;
let currentCoords = null;

const api = {
  async register(name, password){
    const r = await fetch('/register_student', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ name, password }) });
    return r.json();
  },
  async login(name, password){
    const r = await fetch('/login_student', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ name, password }) });
    return r.json();
  },
  async me(){ const r = await fetch('/student/me', { headers:{ 'Authorization': `Bearer ${authToken}` } }); return r.ok ? r.json() : null; },
  async status(){ const r = await fetch('/student/status', { headers:{ 'Authorization': `Bearer ${authToken}` } }); return r.ok ? r.json() : null; },
  async history(startDate, endDate){
    const url = new URL(window.location.origin + '/student/history');
    if (startDate && endDate){ url.searchParams.set('startDate', startDate); url.searchParams.set('endDate', endDate); }
    const r = await fetch(url.toString(), { headers:{ 'Authorization': `Bearer ${authToken}` } });
    return r.ok ? r.json() : [];
  },
  async loginout(lat, lng, action, timestamp, subject) {
    // Use the device current time; server will enforce IST time windows
    const now = timestamp || new Date();

    const body = {
      latitude: lat,
      longitude: lng,
      action: action,
      timestamp: now.toISOString()
    };
    
    // Add subject if provided
    if (subject) {
      body.subject = subject;
    }

    const r = await fetch('/student/loginout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(body)
    });
    return r.json();
  },
  async uploadPhoto(file){ const fd = new FormData(); fd.append('file', file); const r = await fetch(`/upload_photo/${student?.id}`, { method:'POST', body: fd }); return r.json(); },
  async facultyLogin(name, password){ const r = await fetch('/login_faculty', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ name, password }) }); return r.json(); },
  async facultyStudents(ftoken){ const r = await fetch('/faculty/students', { headers:{ 'Authorization': `Bearer ${ftoken}` } }); return r.json(); },
  async facultyAttendance(ftoken, day){ const url = new URL(window.location.origin + '/faculty/attendance'); if(day) url.searchParams.set('date', day); const r = await fetch(url.toString(), { headers:{ 'Authorization': `Bearer ${ftoken}` } }); return r.json(); }
}

function showAuth(){
  document.getElementById('authCard').style.display='';
  document.getElementById('dash').style.display='none';
}
function showDash(){
  document.getElementById('authCard').style.display='none';
  document.getElementById('dash').style.display='';
}

function updateStatusBadge(text){ document.getElementById('statusBadge').textContent = text; }

function renderTodayStatus(st){
  const holder = document.getElementById('todayStatus');
  if (!st || (!st.checkedIn && !st.checkedOut)){
    holder.textContent = 'No status for today';
    return;
  }
  const statusLabel = st.checkedIn && !st.checkedOut ? 'Checked In' : (st.checkedIn && st.checkedOut ? 'Checked Out' : '-');
  const isCurrentlyCheckedIn = st.isCurrentlyCheckedIn || false;
  const html = [
    '<table style="width:100%; border-collapse:collapse;">',
    '<tbody>',
    `<tr><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Status</th><td style="padding:6px; border-bottom:1px solid #f3f4f6;">${statusLabel}</td></tr>`,
    `<tr><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Check-In</th><td style="padding:6px; border-bottom:1px solid #f3f4f6;">${st.checkInTime || '-'}</td></tr>`,
    `<tr><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Check-Out</th><td style="padding:6px; border-bottom:1px solid #f3f4f6;">${st.checkOutTime || '-'}</td></tr>`,
    `<tr><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Location</th><td style="padding:6px; border-bottom:1px solid #f3f4f6;">${st.location || '-'}</td></tr>`,
    `<tr><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Attendance</th><td style="padding:6px; border-bottom:1px solid #f3f4f6; color: ${isCurrentlyCheckedIn ? '#059669' : '#dc2626'};">${isCurrentlyCheckedIn ? '✅ You can mark attendance' : '❌ Check-in required to mark attendance'}</td></tr>`,
    '</tbody></table>'
  ].join('');
  holder.innerHTML = html;
}

function renderHistory(logs){
  const holder = document.getElementById('historyList');
  if (!Array.isArray(logs) || !logs.length){ holder.textContent = 'No history in the selected range'; return; }
  const header = '<thead><tr><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Date</th><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Check-In</th><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Check-Out</th><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Location</th></tr></thead>';
  const rows = logs.map(l => `<tr><td style=\"padding:6px; border-bottom:1px solid #f3f4f6;\">${l.date || '-'}</td><td style=\"padding:6px; border-bottom:1px solid #f3f4f6;\">${l.check_in_time || l.checkInTime || '-'}</td><td style=\"padding:6px; border-bottom:1px solid #f3f4f6;\">${l.check_out_time || l.checkOutTime || '-'}</td><td style=\"padding:6px; border-bottom:1px solid #f3f4f6;\">${l.location_name || l.location || '-'}</td></tr>`).join('');
  holder.innerHTML = `<table style="width:100%; border-collapse:collapse;">${header}<tbody>${rows}</tbody></table>`;
}

function getLocation(){
  const locText = document.getElementById('locText');
  if (!navigator.geolocation){ locText.textContent = 'Geolocation not supported'; return; }
  const opts = { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 };
  navigator.geolocation.getCurrentPosition(pos=>{
    currentCoords = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
    locText.textContent = `Location: ${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)}`;
  }, err=>{
    locText.textContent = 'Location error: ' + err.message;
    toast('Unable to get location', 'error');
  }, opts);
}

async function refreshStatus(){
  if (!authToken) return;
  const st = await api.status();
  renderTodayStatus(st);
  if (st && st.checkedIn && !st.checkedOut) updateStatusBadge('Checked In');
  else if (st && st.checkedIn && st.checkedOut) updateStatusBadge('Checked Out');
  else updateStatusBadge('-');
  
  // Check if today is weekend and update UI accordingly
  const today = new Date();
  const dayOfWeek = today.getDay(); // 0 = Sunday, 6 = Saturday
  
  const checkInBtn = document.getElementById('checkInBtn');
  const checkOutBtn = document.getElementById('checkOutBtn');
  const getLocationBtn = document.getElementById('getLocationBtn');
  const locText = document.getElementById('locText');
  const statusBadge = document.getElementById('statusBadge');
  
  if (dayOfWeek === 0 || dayOfWeek === 6) {
    // Weekend - hide check-in/check-out buttons and show no classes message
    if (checkInBtn) checkInBtn.style.display = 'none';
    if (checkOutBtn) checkOutBtn.style.display = 'none';
    if (getLocationBtn) getLocationBtn.style.display = 'none';
    if (locText) locText.style.display = 'none';
    if (statusBadge) statusBadge.style.display = 'none';
    
    // Update today's status to show no classes
    const todayStatus = document.getElementById('todayStatus');
    if (todayStatus) {
      todayStatus.innerHTML = '<div style="text-align: center; padding: 40px; color: #6b7280; font-size: 18px;">No Classes (Weekend)</div>';
    }
  } else {
    // Weekday - show check-in/check-out buttons
    if (checkInBtn) checkInBtn.style.display = '';
    if (checkOutBtn) checkOutBtn.style.display = '';
    if (getLocationBtn) getLocationBtn.style.display = '';
    if (locText) locText.style.display = '';
    if (statusBadge) statusBadge.style.display = '';
  }
}

async function doCheckIn() {
  if (!student) { toast('Please login first', 'error'); return; }
  if (!currentCoords) { toast('Please get your location first', 'error'); return; }
  
  // Use current device time; backend validates allowed window
  const checkInTime = new Date();
  
  const res = await api.loginout(currentCoords.latitude, currentCoords.longitude, 'checkin');
  if (res && res.error) {
    if (res.distance !== undefined && res.allowedRadius !== undefined) {
      toast(`Not in campus: ${res.distance}m away (allowed ${res.allowedRadius}m)`, 'error');
    } else {
      toast(res.error, 'error');
    }
  } else {
    toast('Checked in successfully at ' + checkInTime.toLocaleTimeString(), 'success');
    await refreshStatus();
  }
}

async function doCheckOut() {
  if (!student) { toast('Please login first', 'error'); return; }
  if (!currentCoords) { toast('Please get your location first', 'error'); return; }
  
  // Use current device time; backend validates allowed window
  const checkOutTime = new Date();
  
  const res = await api.loginout(currentCoords.latitude, currentCoords.longitude, 'checkout');
  if (res && res.error) {
    if (res.distance !== undefined && res.allowedRadius !== undefined) {
      toast(`Not in campus: ${res.distance}m away (allowed ${res.allowedRadius}m)`, 'error');
    } else {
      toast(res.error, 'error');
    }
  } else {
    toast('Checked out successfully at ' + checkOutTime.toLocaleTimeString(), 'success');
    await refreshStatus();
  }
}

async function loadHistory(){
  if (!authToken) return;
  
  const startDate = document.getElementById('histStart').value;
  const endDate = document.getElementById('histEnd').value;
  
  try {
    document.getElementById('historyList').textContent = 'Loading...';
    const logs = await api.history(startDate, endDate);
    renderHistory(logs);
  } catch (error) {
    console.error('Error loading history:', error);
    toast('Failed to load history', 'error');
    document.getElementById('historyList').textContent = 'Error loading history';
  }
}

function persistToken(token){
  try {
    // Used by student dashboard
    localStorage.setItem('studentToken', token);
    // Used by history.js
    localStorage.setItem('authToken', token);
  } catch {}
}
function readToken(){ try { return localStorage.getItem('studentToken'); } catch { return null; } }
function clearToken(){
  try {
    localStorage.removeItem('studentToken');
    localStorage.removeItem('authToken');
  } catch {}
}

window.addEventListener('DOMContentLoaded', async ()=>{
  // Register handler
  const regBtn = document.getElementById('registerBtn');
  if (regBtn) {
    regBtn.addEventListener('click', async()=>{
      const name = (document.getElementById('regName').value || '').trim();
      const pw = document.getElementById('regPassword').value || '';
      if (!name || !pw) { toast('Enter name and password'); return; }
      const res = await api.register(name, pw);
      if (res && res.token) {
        authToken = res.token; persistToken(authToken);
        student = res.student;
        document.getElementById('studentName').textContent = student.name;
        showDash();
        // Navigate to the dashboard section and focus it
        try { location.hash = '#dash'; } catch {}
        try { document.getElementById('dash').scrollIntoView({behavior:'smooth', block:'start'}); } catch {}
        await refreshStatus();
        toast('Registered and logged in', 'success');
      } else {
        toast((res && res.error) || 'Registration failed', 'error');
      }
    });
  }

  // Login handler
  const loginBtn = document.getElementById('loginBtn');
  if (loginBtn) {
    loginBtn.addEventListener('click', async()=>{
      const name = (document.getElementById('loginName').value || '').trim();
      const pw = document.getElementById('loginPassword').value || '';
      if (!name || !pw) { toast('Enter name and password'); return; }
      const res = await api.login(name, pw);
      if (res && res.token) {
        authToken = res.token; persistToken(authToken);
        student = res.student;
        document.getElementById('studentName').textContent = student.name;
        showDash();
        // Navigate to the dashboard section and focus it
        try { location.hash = '#dash'; } catch {}
        try { document.getElementById('dash').scrollIntoView({behavior:'smooth', block:'start'}); } catch {}
        await refreshStatus();
        toast('Logged in', 'success');
      } else {
        toast((res && res.error) || 'Invalid credentials', 'error');
      }
    });
  }
  document.getElementById('logoutBtn').addEventListener('click', ()=>{ authToken=null; student=null; clearToken(); showAuth(); updateStatusBadge('-'); document.getElementById('todayStatus').textContent='-'; });
  document.getElementById('getLocationBtn').addEventListener('click', getLocation);
  document.getElementById('checkInBtn').addEventListener('click', doCheckIn);
  document.getElementById('checkOutBtn').addEventListener('click', doCheckOut);
  // View full history on separate page
  const viewHistoryBtn = document.getElementById('viewHistoryBtn');
  if (viewHistoryBtn){
    viewHistoryBtn.addEventListener('click', (e)=>{
      e.preventDefault();
      if (authToken){
        window.location.href = `/history?token=${encodeURIComponent(authToken)}`;
      } else {
        toast('Please log in to view history', 'error');
      }
    });
  }
  document.getElementById('facLoginBtn').addEventListener('click', async()=>{
    const name = (document.getElementById('facName').value || '').trim();
    const pw = document.getElementById('facPassword').value || '';
    const res = await api.facultyLogin(name, pw);
    if (!res.token){ toast(res.error || 'Faculty login failed', 'error'); return; }
    const ftoken = res.token;
    document.getElementById('facultyViews').style.display='';
    const studs = await api.facultyStudents(ftoken);
    document.getElementById('facStudents').textContent = JSON.stringify(studs, null, 2);
    document.getElementById('facLoadBtn').onclick = async()=>{
      const day = document.getElementById('facDate').value;
      const rows = await api.facultyAttendance(ftoken, day);
      document.getElementById('facAttendance').textContent = JSON.stringify(rows, null, 2);
    };
  });
  // Set default date range for history (last 30 days)
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 30);
  
  // Format dates as YYYY-MM-DD
  const formatDate = (date) => date.toISOString().split('T')[0];
  
  // Set default date values
  document.getElementById('histStart').value = formatDate(startDate);
  document.getElementById('histEnd').value = formatDate(endDate);
  
  // Load history when the page loads
  if (authToken) {
    loadHistory();
  }
  
  // Handle load history button click
  const loadHistoryBtn = document.getElementById('loadHistoryBtn');
  if (loadHistoryBtn) {
    loadHistoryBtn.addEventListener('click', loadHistory);
  }

  // Photo upload removed

  const saved = readToken();
  if (saved){
    authToken = saved;
    const me = await api.me();
    if (me){ student = me; document.getElementById('studentName').textContent = student.name; showDash(); await refreshStatus(); }
    else { clearToken(); showAuth(); }
  } else {
    showAuth();
  }
});
