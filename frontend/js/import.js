let pendingData = null;

// File upload
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) readFile(file);
});
fileInput.addEventListener('change', e => { if (e.target.files[0]) readFile(e.target.files[0]); });

function readFile(file) {
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const data = JSON.parse(e.target.result);
      if (!Array.isArray(data)) throw new Error('需要数组格式');
      // 兼容旧格式：移除 status 字段
      data.forEach(item => { delete item.status; });
      pendingData = data;
      const preview = document.getElementById('filePreview');
      preview.style.display = 'block';
      preview.textContent = `正在导入 ${data.length} 条记录...`;
      document.getElementById('jsonText').value = JSON.stringify(data, null, 2);
      // 文件上传后直接触发导入
      doFileImport(data);
    } catch (err) {
      alert('JSON 解析错误: ' + err.message);
    }
  };
  reader.readAsText(file);
}

async function doFileImport(data) {
  try {
    const res = await fetch('/api/items/import?mode=append', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    const preview = document.getElementById('filePreview');
    preview.textContent = `✅ 成功导入 ${result.imported} 条记录！`;
    showToast(`成功导入 ${result.imported} 条记录！`);
  } catch (err) {
    const preview = document.getElementById('filePreview');
    preview.textContent = `❌ 导入失败: ${err.message}`;
    alert('导入失败: ' + err.message);
  }
}

function parseJsonText() {
  const text = document.getElementById('jsonText').value.trim();
  if (!text) return null;
  try {
    const data = JSON.parse(text);
    if (!Array.isArray(data)) throw new Error('需要数组格式');
    // 兼容旧格式：移除 status 字段
    data.forEach(item => { delete item.status; });
    return data;
  } catch (err) {
    alert('JSON 解析错误: ' + err.message);
    return null;
  }
}

function previewImport() {
  const data = parseJsonText();
  if (!data) return;
  const info = document.getElementById('previewInfo');
  info.style.display = 'block';
  info.innerHTML = `
    <p>📋 <strong>预览</strong></p>
    <p>将追加导入 <strong>${data.length}</strong> 条记录</p>
    <p style="font-size:12px;color:var(--text2);margin-top:8px;">物品: ${data.map(i => i.name).join('、')}</p>
  `;
}

async function doImport() {
  const data = parseJsonText();
  if (!data) return;
  try {
    const res = await fetch('/api/items/import?mode=append', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    showToast(`成功导入 ${result.imported} 条记录！`);
    document.getElementById('jsonText').value = '';
    document.getElementById('previewInfo').style.display = 'none';
  } catch (err) {
    alert('导入失败: ' + err.message);
  }
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

function copyPrompt() {
  const el = document.getElementById('aiPrompt');
  // 复制时排除按钮文字
  const clone = el.cloneNode(true);
  const btn = clone.querySelector('.copy-btn');
  if (btn) btn.remove();
  const text = clone.textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    showToast('已复制到剪贴板');
  }).catch(() => {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    showToast('已复制到剪贴板');
  });
}
