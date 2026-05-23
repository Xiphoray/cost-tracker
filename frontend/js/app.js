// HTML 转义，防止 XSS
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// CATEGORY_ICONS: 从 ICON_REGISTRY 构建分类→默认emoji映射
const CATEGORY_ICONS = {};
if (typeof ICON_REGISTRY !== 'undefined') {
  ICON_REGISTRY.forEach(cat => {
    CATEGORY_ICONS[cat.category] = cat.icons[0]?.emoji || '📦';
  });
}

let allItems = [];

// ── calc_method 切换：显示/隐藏使用次数输入 ──
function syncCalcMethod(method = '按时间', usageCount = 0) {
  document.querySelectorAll('#calcToggle button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.method === method);
  });
  const row = document.getElementById('usageCountRow');
  if (row) row.style.display = method === '按频次' ? '' : 'none';
  const input = document.getElementById('fUsageCount');
  if (input) input.value = method === '按频次' && usageCount ? usageCount : '';
}

function setupCalcToggle() {
  document.querySelectorAll('#calcToggle button').forEach(btn => {
    btn.addEventListener('click', () => syncCalcMethod(btn.dataset.method));
  });
  const usageInput = document.getElementById('fUsageCount');
  if (usageInput) {
    usageInput.addEventListener('wheel', event => {
      event.preventDefault();
      event.stopPropagation();
    }, { passive: false });
  }
}

// ── 判断物品状态：按退役时间 ──
function getItemStatus(item) {
  if (!item.retirement_date) return 'active';
  const today = new Date().toISOString().slice(0, 10);
  return item.retirement_date <= today ? 'retired' : 'active';
}

function getItemStatusLabel(item) {
  return getItemStatus(item) === 'retired' ? '已退役' : '在用';
}

function getUsageCount(item) {
  return parseInt(item.usage_count, 10) || 0;
}

function formatCostLabel(item) {
  if (item.calc_method === '不计算') return '不计成本';
  if (item.calc_method === '按频次') {
    const count = getUsageCount(item);
    const unitCost = count > 0 ? item.price / count : 0;
    return `¥${unitCost.toFixed(2)}/次 × ${count}次`;
  }
  return `¥${item.daily_cost.toFixed(2)}/天`;
}

function openAddModal() {
  document.getElementById('editId').value = '';
  document.getElementById('fName').value = '';
  document.getElementById('fPrice').value = '';
  document.getElementById('fDate').value = new Date().toISOString().slice(0, 10);
  document.getElementById('fCategory').value = '其他';
  document.getElementById('fCategoryDisplay').textContent = '其他';
  document.getElementById('fNote').value = '';
  document.getElementById('fImage').value = '';
  document.getElementById('fRetireDate').value = '';
  document.getElementById('selectedIconEmoji').textContent = '📦';
  syncCalcMethod('按时间');
  document.getElementById('itemModal').classList.add('open');
}

function closeModal() {
  document.getElementById('itemModal').classList.remove('open');
}

function openEditModal(id) {
  const item = allItems.find(i => i.id === id);
  if (!item) return;
  document.getElementById('editId').value = id;
  document.getElementById('fName').value = item.name;
  document.getElementById('fPrice').value = item.price;
  document.getElementById('fDate').value = item.purchase_date;
  document.getElementById('fCategory').value = item.category;
  document.getElementById('fCategoryDisplay').textContent = item.category;
  document.getElementById('fNote').value = item.note || '';
  document.getElementById('fImage').value = item.image_url || '';
  document.getElementById('fRetireDate').value = item.retirement_date || '';
  const selectedEmoji = item.image_url && item.image_url.length <= 4 ? item.image_url : (CATEGORY_ICONS[item.category] || '📦');
  document.getElementById('selectedIconEmoji').textContent = selectedEmoji;
  const method = item.calc_method || '按时间';
  syncCalcMethod(method, item.usage_count || 0);
  document.getElementById('itemModal').classList.add('open');
}

async function saveItem() {
  const id = document.getElementById('editId').value;
  const activeCalc = document.querySelector('#calcToggle button.active');
  const data = {
    name: document.getElementById('fName').value,
    price: parseFloat(document.getElementById('fPrice').value),
    purchase_date: document.getElementById('fDate').value,
    category: document.getElementById('fCategory').value,
    note: document.getElementById('fNote').value,
    image_url: document.getElementById('fImage').value,
    retirement_date: document.getElementById('fRetireDate').value || '',
    warranty_date: '',
    calc_method: activeCalc ? activeCalc.dataset.method : '按时间',
    usage_count: parseInt(document.getElementById('fUsageCount').value, 10) || 0,
  };
  if (data.calc_method !== '按频次') data.usage_count = 0;
  if (!data.name || !data.price || !data.purchase_date) {
    alert('请填写名称、价格和日期');
    return;
  }
  try {
    const url = id ? `/api/items/${id}` : '/api/items';
    const method = id ? 'PUT' : 'POST';
    const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    if (!res.ok) {
      let message = '保存失败，请稍后重试';
      try {
        const err = await res.json();
        message = err.detail || err.message || message;
      } catch (_) {}
      alert(message);
      return;
    }
  } catch (err) {
    console.error('保存物品失败:', err);
    alert('网络异常，保存失败，请检查连接后重试');
    return;
  }
  closeModal();
  await loadItems();
  await loadStats();
}

async function deleteItem(id) {
  if (!confirm('确定删除？')) return;
  try {
    const res = await fetch(`/api/items/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      alert('删除失败，请稍后重试');
      return;
    }
  } catch (err) {
    console.error('删除物品失败:', err);
    alert('网络异常，删除失败');
    return;
  }
  await loadItems();
  await loadStats();
}

function renderItems(items) {
  const container = document.getElementById('itemsYearGroups');
  if (!items.length) {
    container.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="icon">📭</div><p>暂无实体物品，点击上方添加</p></div>';
    const itemsCount = document.getElementById('itemsCount');
    if (itemsCount) itemsCount.textContent = '0 项';
    return;
  }

  const years = {};
  items.forEach(item => {
    const year = item.purchase_date ? item.purchase_date.slice(0, 4) : '未知年份';
    if (!years[year]) years[year] = [];
    years[year].push(item);
  });

  const sortedYears = Object.keys(years).sort((a, b) => {
    if (a === '未知年份') return 1;
    if (b === '未知年份') return -1;
    return b.localeCompare(a);
  });
  const itemsCount = document.getElementById('itemsCount');
  if (itemsCount) itemsCount.textContent = `${items.length} 项`;

  container.innerHTML = sortedYears.map(year => {
    const yearItems = years[year];
    return `
      <details class="year-group" ${year === sortedYears[0] ? 'open' : ''}>
        <summary class="section-header collapsible-header year-summary">
          <div class="section-title-row"><span class="section-icon">📅</span><h3>${year}</h3></div>
          <span class="section-sub">${yearItems.length} 项</span>
        </summary>
        <div class="items-grid">
          ${yearItems.map(item => {
            const status = getItemStatus(item);
            const statusLabel = getItemStatusLabel(item);
            const statusClass = status === 'retired' ? 'status-broken' : 'status-active';
            const note = item.note ? `<div class="note">💭 ${escapeHtml(item.note)}</div>` : '';
            return `
            <div class="item-card">
              <div class="cat-icon-emoji">${escapeHtml(item.image_url) || CATEGORY_ICONS[item.category] || '📦'}</div>
              <div class="name">${escapeHtml(item.name)}</div>
              <div class="meta">
                <span class="tag">${escapeHtml(item.category)}</span>
                <span class="tag ${statusClass}">${statusLabel}</span>
              </div>
              <div class="price-row">
                <span class="price">¥${item.price.toFixed(2)}</span>
                <span class="daily">${formatCostLabel(item)}</span>
              </div>
              <div class="days">📅 ${item.purchase_date} · 已用 ${item.days} 天</div>
              ${item.retirement_date ? `<div class="days">🏁 退役: ${item.retirement_date}</div>` : ''}
              ${note}
              <div class="actions">
                <button class="btn btn-outline btn-sm" onclick="openEditModal(${item.id})">编辑</button>
                <button class="btn btn-danger btn-sm" onclick="deleteItem(${item.id})">删除</button>
              </div>
            </div>
            `;
          }).join('')}
        </div>
      </details>
    `;
  }).join('');
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const d = await res.json();
    document.getElementById('totalCount').textContent = d.total_count;
    document.getElementById('totalValue').textContent = '¥' + d.total_value.toLocaleString();
    document.getElementById('todayCost').textContent = '¥' + Number(d.today_cost).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('avgDailyCost').textContent = '¥' + d.avg_daily_cost.toFixed(2);
    document.getElementById('monthSpending').textContent = '¥' + Number(d.month_spending).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const subInfo = document.getElementById('subSummary');
    if (subInfo) subInfo.textContent = `${d.subscription_count} 项订阅 · 月费 ¥${d.subscription_monthly.toFixed(2)}`;
    const subsCount = document.getElementById('subsCount');
    if (subsCount) subsCount.textContent = `${d.subscription_count} 项`;
  } catch (err) {
    console.error('加载统计失败:', err);
  }
}

async function loadItems() {
  try {
    const res = await fetch('/api/items');
    if (!res.ok) return;
    allItems = await res.json();
    applyFilters();
  } catch (err) {
    console.error('加载物品失败:', err);
  }
}

let allSubs = [];
async function loadSubscriptions() {
  try {
    const res = await fetch('/api/subscriptions');
    if (!res.ok) return;
    allSubs = await res.json();
    renderSubs(allSubs);
    const subsCount = document.getElementById('subsCount');
    if (subsCount) subsCount.textContent = `${allSubs.length} 项`;
  } catch (err) {
    console.error('加载订阅失败:', err);
  }
}

function renderSubs(subs) {
  const grid = document.getElementById('subsGrid');
  if (!subs.length) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="icon">📭</div><p>暂无订阅，点击上方添加</p></div>';
    return;
  }
  grid.innerHTML = subs.map(s => `
    <div class="item-card">
      <div class="cat-icon-emoji">🧾</div>
      <div class="name">${escapeHtml(s.name)}</div>
      <div class="meta">
        <span class="tag">${escapeHtml(s.billing_cycle)}</span>
        <span class="tag ${s.auto_renew ? 'status-active' : 'status-broken'}">${s.auto_renew ? '自动续订' : '手动续订'}</span>
      </div>
      <div class="price-row">
        <span class="price">¥${s.price_per_cycle.toFixed(2)}/${s.billing_cycle.replace('付','')}</span>
        <span class="daily">¥<strong>${s.daily_cost.toFixed(2)}</strong>/天</span>
      </div>
      <div class="days">📅 开始 ${s.start_date} · 月费 ¥${s.monthly_cost.toFixed(2)}</div>
      <div class="note">累计约 ¥${s.total_spent.toFixed(2)}</div>
      <div class="actions">
        <button class="btn btn-outline btn-sm" onclick="openEditSubModal(${s.id})">编辑</button>
        <button class="btn btn-accent btn-sm" onclick="renewSubscription(${s.id})">一键续订</button>
        <button class="btn btn-danger btn-sm" onclick="deleteSubscription(${s.id})">删除</button>
      </div>
    </div>
  `).join('');
}

function openAddSubModal() {
  document.getElementById('editSubId').value = '';
  document.getElementById('fSubName').value = '';
  document.getElementById('fSubStart').value = new Date().toISOString().slice(0, 10);
  document.getElementById('fSubPrice').value = '';
  syncSubAutoRenew(1);
  document.querySelectorAll('#subCycleToggle button').forEach(b => b.classList.remove('active'));
  document.querySelector('#subCycleToggle button[data-cycle="月付"]').classList.add('active');
  document.getElementById('subModal').classList.add('open');
}

function openEditSubModal(id) {
  const s = allSubs.find(i => i.id === id);
  if (!s) return;
  document.getElementById('editSubId').value = id;
  document.getElementById('fSubName').value = s.name;
  document.getElementById('fSubStart').value = s.start_date;
  document.getElementById('fSubPrice').value = s.price_per_cycle;
  syncSubAutoRenew(s.auto_renew ? 1 : 0);
  document.querySelectorAll('#subCycleToggle button').forEach(b => b.classList.remove('active'));
  const t = document.querySelector(`#subCycleToggle button[data-cycle="${s.billing_cycle}"]`);
  if (t) t.classList.add('active');
  document.getElementById('subModal').classList.add('open');
}

function closeSubModal() {
  document.getElementById('subModal').classList.remove('open');
}
function syncSubAutoRenew(value) {
  document.querySelectorAll('#subAutoRenewToggle button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.auto === String(value));
  });
}

function selectSubAutoRenew(event) {
  event.preventDefault();
  document.querySelectorAll('#subAutoRenewToggle button').forEach(b => b.classList.remove('active'));
  event.currentTarget.classList.add('active');
}


function selectSubCycle(event) {
  event.preventDefault();
  document.querySelectorAll('#subCycleToggle button').forEach(b => b.classList.remove('active'));
  event.currentTarget.classList.add('active');
}

async function saveSubscription() {
  const id = document.getElementById('editSubId').value;
  const active = document.querySelector('#subCycleToggle button.active');
  const data = {
    name: document.getElementById('fSubName').value,
    start_date: document.getElementById('fSubStart').value,
    billing_cycle: active ? active.dataset.cycle : '月付',
    price_per_cycle: parseFloat(document.getElementById('fSubPrice').value),
    auto_renew: document.querySelector('#subAutoRenewToggle button.active')?.dataset.auto === '1',
  };
  if (!data.name || !data.start_date || !data.price_per_cycle) {
    alert('请填写名称、开始时间和费用');
    return;
  }
  if (id) {
    try {
      const res = await fetch(`/api/subscriptions/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!res.ok) { alert('保存失败，请稍后重试'); return; }
    } catch (err) {
      console.error('保存订阅失败:', err);
      alert('网络异常，保存失败');
      return;
    }
  } else {
    try {
      const res = await fetch('/api/subscriptions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!res.ok) { alert('保存失败，请稍后重试'); return; }
    } catch (err) {
      console.error('保存订阅失败:', err);
      alert('网络异常，保存失败');
      return;
    }
  }
  closeSubModal();
  await loadSubscriptions();
  await loadStats();
}

async function renewSubscription(id) {
  try {
    const res = await fetch(`/api/subscriptions/${id}/renew`, { method: 'POST' });
    if (!res.ok) { alert('续订失败，请稍后重试'); return; }
  } catch (err) {
    console.error('续订失败:', err);
    alert('网络异常，续订失败');
    return;
  }
  await loadSubscriptions();
  await loadStats();
}

async function deleteSubscription(id) {
  if (!confirm('确定删除该订阅？')) return;
  try {
    const res = await fetch(`/api/subscriptions/${id}`, { method: 'DELETE' });
    if (!res.ok) { alert('删除失败，请稍后重试'); return; }
  } catch (err) {
    console.error('删除订阅失败:', err);
    alert('网络异常，删除失败');
    return;
  }
  await loadSubscriptions();
  await loadStats();
}

function applyFilters() {
  const cat = document.getElementById('filterCategory').value;
  const status = document.getElementById('filterStatus').value;
  const sort = document.getElementById('sortBy').value;
  let items = allItems.filter(i => {
    if (cat && i.category !== cat) return false;
    if (status === 'active' && getItemStatus(i) !== 'active') return false;
    if (status === 'retired' && getItemStatus(i) !== 'retired') return false;
    return true;
  });
  if (sort === 'daily_cost') items.sort((a, b) => b.daily_cost - a.daily_cost);
  else if (sort === 'price') items.sort((a, b) => b.price - a.price);
  else if (sort === 'purchase_date') items.sort((a, b) => b.purchase_date.localeCompare(a.purchase_date));
  renderItems(items);
}

document.getElementById('filterCategory').addEventListener('change', applyFilters);
document.getElementById('filterStatus').addEventListener('change', applyFilters);
document.getElementById('sortBy').addEventListener('change', applyFilters);

// ── 分类下拉切换 ──
function toggleCategoryDropdown() {
  const sel = document.getElementById('fCategory');
  if (sel.style.display === 'none') {
    sel.style.display = 'block';
    sel.size = sel.options.length;
    sel.focus();
  } else {
    sel.style.display = 'none';
  }
}
document.getElementById('fCategory').addEventListener('change', function() {
  document.getElementById('fCategoryDisplay').textContent = this.value;
  this.style.display = 'none';
});
document.getElementById('fCategory').addEventListener('blur', function() {
  this.style.display = 'none';
});

// ── 计算方式切换 ──
document.getElementById('calcToggle').addEventListener('click', (e) => {
  if (e.target.tagName !== 'BUTTON') return;
  document.querySelectorAll('#calcToggle button').forEach(b => b.classList.remove('active'));
  e.target.classList.add('active');
});

// ── 图标选择器 ──
let currentIconCategory = '全部';

function openIconPicker() {
  document.getElementById('iconPickerOverlay').classList.add('open');
  document.getElementById('iconSearch').value = '';
  renderIconTabs();
  renderIconGrid();
}

function closeIconPicker() {
  document.getElementById('iconPickerOverlay').classList.remove('open');
}

function renderIconTabs() {
  const tabs = getIconCategories();
  const container = document.getElementById('iconPickerTabs');
  container.innerHTML = tabs.map(cat =>
    `<button class="${cat === currentIconCategory ? 'active' : ''}" onclick="selectIconCategory('${cat}')">${cat}</button>`
  ).join('');
}

function selectIconCategory(cat) {
  currentIconCategory = cat;
  renderIconTabs();
  renderIconGrid();
}

function renderIconGrid() {
  const search = document.getElementById('iconSearch').value.trim().toLowerCase();
  let icons = getAllIcons();

  if (currentIconCategory !== '全部') {
    icons = icons.filter(i => i.category === currentIconCategory);
  }
  if (search) {
    icons = icons.filter(i => i.label.includes(search) || i.category.includes(search));
  }

  const grid = document.getElementById('iconPickerGrid');
  if (icons.length === 0) {
    grid.innerHTML = '<p class="empty-hint">没有找到匹配的图标</p>';
    return;
  }
  grid.innerHTML = icons.map(icon =>
    `<div class="icon-pick-item" onclick="pickIcon('${icon.emoji}')">
      <span class="icon-pick-emoji">${icon.emoji}</span>
      <span class="icon-pick-label">${icon.label}</span>
    </div>`
  ).join('');
}

function filterIcons() {
  renderIconGrid();
}

function pickIcon(emoji) {
  document.getElementById('selectedIconEmoji').textContent = emoji;
  document.getElementById('fImage').value = emoji;
  closeIconPicker();
}

// 点击遮罩层关闭 Modal（阻止内部点击冒泡）
document.getElementById("itemModal").addEventListener("click", function(e) {
  if (e.target === this) closeModal();
});

setupCalcToggle();
loadStats();
loadItems();
loadSubscriptions();
