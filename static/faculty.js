let ftoken = null;

const fapi = {
  async login(identifier, password){ 
    // Check if identifier is an email
    const isEmail = identifier.includes('@');
    const body = isEmail ? { email: identifier, password } : { name: identifier, password };
    
    const r = await fetch('/login_faculty', { 
      method:'POST', 
      headers:{'Content-Type':'application/json'}, 
      body: JSON.stringify(body) 
    }); 
    return r.json(); 
  }
};

function toast(msg, type='info'){ const t=document.getElementById('toast'); if(!t) return; t.textContent=msg; t.className='toast show '+type; setTimeout(()=>t.classList.remove('show'),2500);}  

window.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('facLoginBtn');
  if (!btn) return; // not on login page
  btn.addEventListener('click', async () => {
    const identifier = (document.getElementById('facName').value || '').trim();
    const pw = document.getElementById('facPassword').value || '';
    const res = await fapi.login(identifier, pw);
    if (!res.token){ toast(res.error || 'Faculty login failed', 'error'); return; }
    ftoken = res.token;
    try { localStorage.setItem('facultyToken', ftoken); } catch {}
    // Redirect to attendance view page
    location.href = '/faculty/attendance_view';
  });
});
