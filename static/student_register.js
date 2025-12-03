let authToken = null;

const api = {
  async register(name, email, password){
    const r = await fetch('/register_student', { 
      method: 'POST', 
      headers: {'Content-Type': 'application/json'}, 
      body: JSON.stringify({ name, email, password }) 
    });
    return r.json();
  }
};

// Email validation function
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
}

function toast(msg, type='info'){ const t=document.getElementById('toast'); if(!t) return; t.textContent=msg; t.className='toast show '+type; setTimeout(()=>t.classList.remove('show'),2500);}  

window.addEventListener('DOMContentLoaded', ()=>{
  const btn = document.getElementById('registerBtn');
  const msg = document.getElementById('regMsg');
  
  btn.addEventListener('click', async()=>{
    // Get form values
    const name = (document.getElementById('regName').value || '').trim();
    const email = (document.getElementById('regEmail').value || '').trim();
    const password = document.getElementById('regPassword').value || '';
    const confirmPassword = document.getElementById('regConfirmPassword').value || '';
    
    // Validation
    if (!name || !email || !password || !confirmPassword) {
      msg.textContent = 'All fields are required';
      msg.style.color = 'red';
      return;
    }
    
    if (!isValidEmail(email)) {
      msg.textContent = 'Please enter a valid email address';
      msg.style.color = 'red';
      return;
    }
    
    if (password.length < 6) {
      msg.textContent = 'Password must be at least 6 characters long';
      msg.style.color = 'red';
      return;
    }
    
    if (password !== confirmPassword) {
      msg.textContent = 'Passwords do not match';
      msg.style.color = 'red';
      return;
    }
    
    try {
      // Show loading state
      btn.disabled = true;
      btn.textContent = 'Registering...';
      
      // Call the registration API
      const res = await api.register(name, email, password);
      
      if (res && res.token) {
        msg.textContent = 'Registration successful! Redirecting to login...';
        msg.style.color = 'green';
        
        try { 
          localStorage.setItem('studentToken', res.token); 
        } catch (e) {
          console.error('Error saving token:', e);
        }
        
        // Redirect to login page after a short delay
        setTimeout(() => { 
          window.location.href = '/student';
        }, 1500);
      } else {
        throw new Error(res?.error || 'Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      msg.textContent = error.message || 'Registration failed. Please try again.';
      msg.style.color = 'red';
    } finally {
      // Reset button state
      btn.disabled = false;
      btn.textContent = 'Register';
    }
  });
});
