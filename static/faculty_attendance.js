let ftoken = null;

const fapi = {
  async attendance(day){
    const url = new URL(window.location.origin + '/faculty/attendance');
    if (day) url.searchParams.set('date', day);
    const r = await fetch(url.toString(), { headers:{ 'Authorization': `Bearer ${ftoken}` } });
    return r.json();
  }
};

function renderAttendance(rows){
  const holder = document.getElementById('facAttendance');
  if (!Array.isArray(rows) || rows.length === 0){ 
    holder.textContent = 'No students found'; 
    return; 
  }
  
  // Get subject from first row (all rows should have same subject)
  const subject = rows[0].subject || 'Unknown Subject';
  
  const present = rows.filter(r => r && r.checkedIn);
  const absent = rows.filter(r => r && !r.checkedIn);
  
  const html = [
    `<h4 style="margin-bottom: 12px; color: #374151;">Subject: ${subject}</h4>`,
    `<p style="margin-bottom: 20px; color: #6b7280;">Total Students: ${rows.length} | Present: <span style="color: #059669; font-weight: 500;">${present.length}</span> | Absent: <span style="color: #dc2626; font-weight: 500;">${absent.length}</span></p>`,
    '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">',
    ...rows.map(p => `<div style="padding: 8px; border-radius: 4px; background: #f9fafb; border: 1px solid #e5e7eb; ${p.checkedIn ? 'color: #059669; font-weight: 500;' : 'color: #dc2626;'}">${p.name}</div>`),
    '</div>'
  ].join('');
  holder.innerHTML = html;
}

window.addEventListener('DOMContentLoaded', ()=>{
  try { ftoken = localStorage.getItem('facultyToken'); } catch {}
  if (!ftoken){ location.href = '/faculty'; return; }
  const btn = document.getElementById('facLoadBtn');
  if (btn){
    btn.addEventListener('click', async ()=>{
      const day = document.getElementById('facDate').value;
      
      // Check if the selected date is Saturday or Sunday
      if (day) {
        const date = new Date(day + 'T00:00:00');
        const dayOfWeek = date.getDay(); // 0 = Sunday, 6 = Saturday
        
        if (dayOfWeek === 0 || dayOfWeek === 6) {
          // Weekend - show no classes message
          const holder = document.getElementById('facAttendance');
          holder.innerHTML = '<h4 style="color: #6b7280; text-align: center; padding: 40px;">No Classes (Weekend)</h4>';
          return;
        }
      }
      
      const rows = await fapi.attendance(day);
      renderAttendance(rows);
    });
  }
  
  // Auto-load today's attendance when page loads
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('facDate').value = today;
  
  // Check if today is weekend before auto-loading
  const todayDate = new Date(today + 'T00:00:00');
  const todayDayOfWeek = todayDate.getDay();
  
  if (todayDayOfWeek !== 0 && todayDayOfWeek !== 6) {
    // Not weekend, load attendance
    btn.click();
  } else {
    // Weekend, show no classes message
    const holder = document.getElementById('facAttendance');
    holder.innerHTML = '<h4 style="color: #6b7280; text-align: center; padding: 40px;">No Classes (Weekend)</h4>';
  }
});
