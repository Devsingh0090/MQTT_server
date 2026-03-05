document.getElementById('uploadForm').addEventListener('submit', async function(e){
  e.preventDefault();
  const fileInput = document.getElementById('file');
  const status = document.getElementById('status');
  // No broker/topic fields in UI — backend will use server defaults
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
// template download button is a normal link, no dynamic port refresh needed
