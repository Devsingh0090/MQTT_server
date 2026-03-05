document.getElementById('uploadForm').addEventListener('submit', async function(e){
  e.preventDefault();
  const fileInput = document.getElementById('file');
  const status = document.getElementById('status');
  if (!fileInput.files.length){ status.innerText='Choose an Excel file.'; return; }
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  status.innerText = 'Uploading...';
  try{
    const res = await fetch('/upload', { method:'POST', body: fd });
    const json = await res.json();
    if (!res.ok) {
      status.innerText = 'Error: ' + (json.error || res.statusText);
    } else {
      status.innerText = 'Published ' + json.sent + ' IDs (server defaults used)';
    }
  }catch(err){ status.innerText = 'Network error: '+err.message }
});

// Clear stored IDs on ESP32
const clearBtn = document.getElementById('clearButton');
if (clearBtn){
  clearBtn.addEventListener('click', async function(){
    if (!confirm('Clear all IDs stored on the ESP32? This cannot be undone.')) return;
    const status = document.getElementById('status');
    status.innerText = 'Sending clear command...';
    try{
      const res = await fetch('/clear', { method: 'POST' });
      const js = await res.json();
      if (!res.ok) status.innerText = 'Error: ' + (js.error || res.statusText);
      else status.innerText = 'Clear command sent to ' + js.topic + ' @ ' + js.broker;
    }catch(err){ status.innerText = 'Network error: '+err.message }
  });
}
