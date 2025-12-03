let ftoken = null;

const fapi = {
  async students(){ const r = await fetch('/faculty/students', { headers:{ 'Authorization': `Bearer ${ftoken}` } }); return r.json(); }
};

function renderStudents(studs){
  const holder = document.getElementById('studentsTable');
  if (!Array.isArray(studs) || !studs.length){ holder.textContent = 'No students found'; return; }
  const html = [
    '<table style="width:100%; border-collapse:collapse;">',
    '<thead><tr><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">ID</th><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Name</th><th style="text-align:left; padding:6px; border-bottom:1px solid #e5e7eb;">Position</th></tr></thead>',
    '<tbody>',
    ...studs.map(s => `<tr><td style="padding:6px; border-bottom:1px solid #f3f4f6;">${s.id}</td><td style="padding:6px; border-bottom:1px solid #f3f4f6;">${s.name}</td><td style="padding:6px; border-bottom:1px solid #f3f4f6;">${s.position||'-'}</td></tr>`),
    '</tbody></table>'
  ].join('');
  holder.innerHTML = html;
}

window.addEventListener('DOMContentLoaded', async ()=>{
  try { ftoken = localStorage.getItem('facultyToken'); } catch {}
  if (!ftoken){ location.href = '/faculty'; return; }
  const studs = await fapi.students();
  renderStudents(studs);
});
