// ── 图标数据库：按分类组织，每个分类有具体的 emoji 图标 ──
const ICON_REGISTRY = [
  {
    category: '数码产品',
    icons: [
      { emoji: '🎮', label: '游戏机' },
      { emoji: '📹', label: '投影仪' },
      { emoji: '📱', label: '手机' },
      { emoji: '💻', label: '笔记本' },
      { emoji: '🖥', label: '台式机' },
      { emoji: '⌨', label: '键盘' },
      { emoji: '🖱', label: '鼠标' },
      { emoji: '🎧', label: '耳机' },
      { emoji: '📷', label: '相机' },
      { emoji: '⌚', label: '手表' },
      { emoji: '📺', label: '显示器' },
      { emoji: '🔋', label: '充电宝' },
      { emoji: '🔌', label: '充电器' },
      { emoji: '💾', label: '硬盘' },
      { emoji: '💽', label: '固态硬盘' },
      { emoji: '📀', label: 'U盘' },
      { emoji: '🃏', label: '存储卡' },
      { emoji: '⚙', label: 'CPU' },
      { emoji: '🎛', label: '显卡' },
      { emoji: '🖨', label: '打印机' },
      { emoji: '📡', label: '路由器' },
      { emoji: '🎵', label: '音箱' },
      { emoji: '🎤', label: '麦克风' },
      { emoji: '🕹', label: '手柄' },
    ]
  },
  {
    category: '家居日用',
    icons: [
      { emoji: '🛋', label: '沙发' },
      { emoji: '🛏', label: '床' },
      { emoji: '💺', label: '椅子' },
      { emoji: '🗄', label: '柜子' },
      { emoji: '🚿', label: '花洒' },
      { emoji: '🧹', label: '扫把' },
      { emoji: '🧽', label: '拖把' },
      { emoji: '🗑', label: '垃圾桶' },
      { emoji: '🧴', label: '洗护用品' },
      { emoji: '🪥', label: '牙刷' },
      { emoji: '🧻', label: '纸巾' },
      { emoji: '🕯', label: '香薰' },
      { emoji: '🪞', label: '镜子' },
      { emoji: '🖼', label: '装饰画' },
      { emoji: '🌱', label: '绿植' },
      { emoji: '📦', label: '收纳盒' },
    ]
  },
  {
    category: '家用电器',
    icons: [
      { emoji: '❄', label: '冰箱' },
      { emoji: '🌀', label: '洗衣机' },
      { emoji: '🌡', label: '空调' },
      { emoji: '🤖', label: '扫地机' },
      { emoji: '🍳', label: '电饭煲' },
      { emoji: '☕', label: '咖啡机' },
      { emoji: '🍵', label: '热水壶' },
      { emoji: '🧇', label: '烤箱' },
      { emoji: '💨', label: '吹风机' },
      { emoji: '🔧', label: '吸尘器' },
      { emoji: '💡', label: '台灯' },
      { emoji: '🔦', label: '手电筒' },
      { emoji: '💧', label: '加湿器' },
      { emoji: '🌿', label: '空气净化器' },
    ]
  },
  {
    category: '户外运动',
    icons: [
      { emoji: '⛺', label: '帐篷' },
      { emoji: '🎒', label: '背包' },
      { emoji: '👟', label: '登山鞋' },
      { emoji: '🧗', label: '攀岩' },
      { emoji: '🏊', label: '游泳' },
      { emoji: '🚴', label: '自行车' },
      { emoji: '🎿', label: '滑雪' },
      { emoji: '🛹', label: '滑板' },
      { emoji: '🏋', label: '健身' },
      { emoji: '🧘', label: '瑜伽' },
      { emoji: '🎣', label: '钓鱼' },
      { emoji: '🏸', label: '球拍' },
      { emoji: '⚽', label: '足球' },
      { emoji: '🏀', label: '篮球' },
      { emoji: '🎯', label: '飞镖' },
      { emoji: '🥊', label: '拳击' },
    ]
  },
  {
    category: '服装鞋帽',
    icons: [
      { emoji: '👕', label: 'T恤' },
      { emoji: '👔', label: '衬衫' },
      { emoji: '🧥', label: '外套' },
      { emoji: '👗', label: '裙子' },
      { emoji: '👖', label: '裤子' },
      { emoji: '👟', label: '运动鞋' },
      { emoji: '👠', label: '高跟鞋' },
      { emoji: '🩴', label: '拖鞋' },
      { emoji: '🧣', label: '围巾' },
      { emoji: '🧤', label: '手套' },
      { emoji: '🎩', label: '帽子' },
      { emoji: '🕶', label: '墨镜' },
      { emoji: '👜', label: '包包' },
      { emoji: '💍', label: '戒指' },
      { emoji: '📿', label: '项链' },
    ]
  },
  {
    category: '美妆护肤',
    icons: [
      { emoji: '💄', label: '口红' },
      { emoji: '🧴', label: '面霜' },
      { emoji: '🧼', label: '洗面奶' },
      { emoji: '🪞', label: '化妆镜' },
      { emoji: '💅', label: '指甲油' },
      { emoji: '🎭', label: '面膜' },
      { emoji: '🌸', label: '香水' },
      { emoji: '💇', label: '梳子' },
      { emoji: '✨', label: '精华液' },
      { emoji: '☀', label: '防晒霜' },
    ]
  },
  {
    category: '食品饮料',
    icons: [
      { emoji: '🍵', label: '茶叶' },
      { emoji: '☕', label: '咖啡' },
      { emoji: '🧃', label: '果汁' },
      { emoji: '🥛', label: '牛奶' },
      { emoji: '🍺', label: '啤酒' },
      { emoji: '🍷', label: '红酒' },
      { emoji: '🥤', label: '奶茶' },
      { emoji: '🍪', label: '零食' },
      { emoji: '🍫', label: '巧克力' },
      { emoji: '🍎', label: '水果' },
      { emoji: '🥦', label: '蔬菜' },
      { emoji: '🍜', label: '方便面' },
    ]
  },
  {
    category: '交通工具',
    icons: [
      { emoji: '🚗', label: '汽车' },
      { emoji: '🚙', label: 'SUV' },
      { emoji: '🏍', label: '摩托车' },
      { emoji: '🛵', label: '电动车' },
      { emoji: '🚲', label: '自行车' },
      { emoji: '🛴', label: '滑板车' },
      { emoji: '🚌', label: '公交' },
      { emoji: '🚆', label: '火车' },
      { emoji: '✈', label: '飞机' },
      { emoji: '🚀', label: '火箭' },
    ]
  },
  {
    category: '书籍文具',
    icons: [
      { emoji: '📖', label: '书籍' },
      { emoji: '📚', label: '书堆' },
      { emoji: '📓', label: '笔记本' },
      { emoji: '✏', label: '铅笔' },
      { emoji: '🖊', label: '钢笔' },
      { emoji: '📝', label: '便签' },
      { emoji: '📐', label: '尺子' },
      { emoji: '🧮', label: '计算器' },
      { emoji: '📌', label: '图钉' },
      { emoji: '📎', label: '回形针' },
      { emoji: '🖍', label: '蜡笔' },
      { emoji: '🎨', label: '画具' },
    ]
  },
  {
    category: '其他',
    icons: [
      { emoji: '📦', label: '包裹' },
      { emoji: '🎁', label: '礼物' },
      { emoji: '🏷', label: '标签' },
      { emoji: '🔧', label: '工具' },
      { emoji: '🔑', label: '钥匙' },
      { emoji: '🧸', label: '玩偶' },
      { emoji: '🪙', label: '硬币' },
      { emoji: '💎', label: '宝石' },
      { emoji: '🎪', label: '其他' },
    ]
  },
];

// 获取所有图标（平铺）
function getAllIcons() {
  const all = [];
  ICON_REGISTRY.forEach(cat => {
    cat.icons.forEach(icon => {
      all.push({ ...icon, category: cat.category });
    });
  });
  return all;
}

// 获取分类列表
function getIconCategories() {
  return ['全部', ...ICON_REGISTRY.map(c => c.category)];
}
