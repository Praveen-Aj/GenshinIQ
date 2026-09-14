/**
 * GenshinIQ Frontend Application Controller
 * Handles Tab Navigation, Health Diagnostics, Enka Showcase Import, and Game Database Explorer
 */

// ====================================================
// IMAGE ASSET UTILITIES (Enka.Network CDN)
// ====================================================

const CHARACTER_ICONS = {
  'arlecchino': 'UI_AvatarIcon_Arlecchino',
  'furina': 'UI_AvatarIcon_Furina',
  'neuvillette': 'UI_AvatarIcon_Neuvillette',
  'raiden shogun': 'UI_AvatarIcon_Shogun',
  'kaedehara kazuha': 'UI_AvatarIcon_Kazuha',
  'zhongli': 'UI_AvatarIcon_Zhongli',
  'bennett': 'UI_AvatarIcon_Bennett',
  'xiangling': 'UI_AvatarIcon_Xiangling',
  'xingqiu': 'UI_AvatarIcon_Xingqiu',
  'mavuika': 'UI_AvatarIcon_Mavuika',
  'nahida': 'UI_AvatarIcon_Nahida',
  'kachina': 'UI_AvatarIcon_Kachina',
  'citlali': 'UI_AvatarIcon_Citlali',
  'skirk': 'UI_AvatarIcon_SkirkNew',
  'nefer': 'UI_AvatarIcon_Nefer',
  'zibai': 'UI_AvatarIcon_Zibai',
  'xianyun': 'UI_AvatarIcon_Xianyun',
  'shenhe': 'UI_AvatarIcon_Shenhe',
  'navia': 'UI_AvatarIcon_Navia',
  'clorinde': 'UI_AvatarIcon_Clorinde',
  'chiori': 'UI_AvatarIcon_Chiori',
  'yelan': 'UI_AvatarIcon_Yelan',
  'hu tao': 'UI_AvatarIcon_Hutao',
  'yae miko': 'UI_AvatarIcon_Yae',
  'arataki itto': 'UI_AvatarIcon_Itto',
  'kamisato ayaka': 'UI_AvatarIcon_Ayaka',
  'kamisato ayato': 'UI_AvatarIcon_Ayato',
  'shikanoin heizou': 'UI_AvatarIcon_Heizou',
  'sangonomiya kokomi': 'UI_AvatarIcon_Kokomi',
  'kujou sara': 'UI_AvatarIcon_Sara',
  'kuki shinobu': 'UI_AvatarIcon_Shinobu',
  'yun jin': 'UI_AvatarIcon_Yunjin',
  'tartaglia': 'UI_AvatarIcon_Tartaglia',
  'xilonen': 'UI_AvatarIcon_Xilonen',
  'mualani': 'UI_AvatarIcon_Mualani',
  'kinich': 'UI_AvatarIcon_Kinich',
  'chasca': 'UI_AvatarIcon_Chasca',
  'lan yan': 'UI_AvatarIcon_Lanyan',
  'lanyan': 'UI_AvatarIcon_Lanyan',
  'gaming': 'UI_AvatarIcon_Gaming',
  'charlotte': 'UI_AvatarIcon_Charlotte',
  'chevreuse': 'UI_AvatarIcon_Chevreuse',
  'wriothesley': 'UI_AvatarIcon_Wriothesley',
  'lyney': 'UI_AvatarIcon_Lyney',
  'wanderer': 'UI_AvatarIcon_Wanderer',
  'alhaitham': 'UI_AvatarIcon_Alhatham',
  'nilou': 'UI_AvatarIcon_Nilou',
  'cyno': 'UI_AvatarIcon_Cyno',
  'tighnari': 'UI_AvatarIcon_Tighnari',
  'eula': 'UI_AvatarIcon_Eula',
  'ganyu': 'UI_AvatarIcon_Ganyu',
  'venti': 'UI_AvatarIcon_Venti',
  'diluc': 'UI_AvatarIcon_Diluc',
  'jean': 'UI_AvatarIcon_Qin',
  'mona': 'UI_AvatarIcon_Mona',
  'keqing': 'UI_AvatarIcon_Keqing',
  'qiqi': 'UI_AvatarIcon_Qiqi',
  'albedo': 'UI_AvatarIcon_Albedo',
  'xiao': 'UI_AvatarIcon_Xiao',
  'yoimiya': 'UI_AvatarIcon_Yoimiya',
  'kokomi': 'UI_AvatarIcon_Kokomi',
  'ayato': 'UI_AvatarIcon_Ayato',
  'baizhu': 'UI_AvatarIcon_Baizhuer',
  'dehya': 'UI_AvatarIcon_Dehya',
  'collei': 'UI_AvatarIcon_Collei',
  'dori': 'UI_AvatarIcon_Dori',
  'kaveh': 'UI_AvatarIcon_Kaveh',
  'kirara': 'UI_AvatarIcon_Momoka',
  'layla': 'UI_AvatarIcon_Layla',
  'faruzan': 'UI_AvatarIcon_Faruzan',
  'candace': 'UI_AvatarIcon_Candace',
  'emilie': 'UI_AvatarIcon_Emilie',
  'sigewinne': 'UI_AvatarIcon_Sigewinne',
  'sethos': 'UI_AvatarIcon_Sethos',
  'ororon': 'UI_AvatarIcon_Olorun',
  'olorun': 'UI_AvatarIcon_Olorun',
  'ifa': 'UI_AvatarIcon_Ifa',
  'varesa': 'UI_AvatarIcon_Varesa',
  'iansan': 'UI_AvatarIcon_Iansan',
  'mizuki': 'UI_AvatarIcon_Mizuki',
  'escoffier': 'UI_AvatarIcon_Escoffier',
  'odette': 'UI_AvatarIcon_Odette',
  'columbina': 'UI_AvatarIcon_Columbina',
  'alyosha': 'UI_AvatarIcon_Alyosha',
  'jahoda': 'UI_AvatarIcon_Jahoda',
};

function getCharacterIconUrl(name) {
  if (!name) return 'https://enka.network/ui/UI_AvatarIcon_NPC.png';
  const codeName = CHARACTER_ICONS[name.toLowerCase()] || `UI_AvatarIcon_${name}`;
  return `https://enka.network/ui/${codeName}.png`;
}

function getElementSvg(element, size = 18) {
  const elem = (element || '').toLowerCase().trim();
  const colors = {
    pyro: '#ff5e41',
    hydro: '#21c5f5',
    anemo: '#5be0b1',
    electro: '#c370fa',
    dendro: '#87e034',
    cryo: '#9be9fa',
    geo: '#f4c042'
  };
  const color = colors[elem] || '#e9be74';
  const glyphs = {
    pyro: `<path d="M12 2c1 3 4 5 4 9 0 4.4-3.6 8-8 8s-8-3.6-8-8c0-3 2-6 5-7.5-.5 2 0 4.5 1.5 5.5 1-3 3-5 5.5-7z" fill="${color}"/>`,
    hydro: `<path d="M12 2.5C12 2.5 5 11 5 15.5 5 19.1 7.9 22 11.5 22s6.5-2.9 6.5-6.5C18 11 12 2.5 12 2.5z" fill="${color}"/>`,
    anemo: `<path d="M12 2a10 10 0 0 1 7.5 16.6l-2.1-2.1A7 7 0 1 0 7 12H4a8 8 0 1 1 8-8z" fill="${color}"/>`,
    electro: `<path d="M13 2L3 14h8l-2 8 12-12h-8l2-8z" fill="${color}"/>`,
    dendro: `<path d="M17 3c-4.5.5-8.5 4.5-9 9 0 0 2-3 5-3s5 3 5 3-1-4.5-.5-6c.3-.9 1.5-1.5 1.5-1.5s-1-1-2-1.5z M7 13c-3 1-5 4-5 7 3.5 0 6.5-2 7.5-5-.8-.7-1.7-1.4-2.5-2z" fill="${color}"/>`,
    cryo: `<path d="M12 2v20M2 12h20M5 5l14 14M19 5L5 19M12 6l2-2M12 6l-2-2M12 18l2 2M12 18l-2 2M6 12l-2 2M6 12l-2-2M18 12l2 2M18 12l2-2" stroke="${color}" stroke-width="2.5" stroke-linecap="round"/>`,
    geo: `<polygon points="12 2 21 8 21 16 12 22 3 16 3 8" fill="none" stroke="${color}" stroke-width="2.5"/><polygon points="12 6 17 10 17 14 12 18 7 14 7 10" fill="${color}"/>`
  };
  const svgContent = glyphs[elem] || glyphs.pyro;
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" style="filter: drop-shadow(0 1px 3px rgba(0,0,0,0.8)); vertical-align: middle;">${svgContent}</svg>`;
}

function getElementIconUrl(element) {
  const elem = (element || 'pyro').toLowerCase();
  return `https://enka.network/ui/UI_Buff_Element_${elem.charAt(0).toUpperCase() + elem.slice(1)}.png`;
}

function getCharacterGachaUrl(name) {
  if (!name) return null;
  const iconCode = CHARACTER_ICONS[name.toLowerCase()];
  if (!iconCode) return null;
  return `https://enka.network/ui/${iconCode.replace('AvatarIcon', 'Gacha_AvatarImg')}.png`;
}

function getWeaponIconUrl(iconKey) {
  return `https://enka.network/ui/${iconKey || 'UI_EquipIcon_Sword_Zephyrus'}.png`;
}

function getArtifactIconUrl(iconKey) {
  return `https://enka.network/ui/${iconKey || 'UI_RelicIcon_15001_4'}.png`;
}

function getRarityStars(rarity) {
  return '★'.repeat(rarity);
}

function getImgFallback(type) {
  switch (type) {
    case 'character': return 'https://enka.network/ui/UI_AvatarIcon_NPC.png';
    case 'weapon': return 'https://enka.network/ui/UI_EquipIcon_Sword_Zephyrus.png';
    case 'artifact': return 'https://enka.network/ui/UI_RelicIcon_15001_4.png';
    default: return 'https://enka.network/ui/UI_AvatarIcon_NPC.png';
  }
}

// Daily Domain Schedule (Monday/Thursday, Tuesday/Friday, Wednesday/Saturday, Sunday all)
const ROTATION_SCHEDULE = {
  1: {
    day: 'Monday / Thursday',
    talents: [
      { name: 'Freedom', nation: 'Mondstadt', chars: ['Klee', 'Sucrose', 'Diona', 'Aloy', 'Tartaglia', 'Amber', 'Barbara'] },
      { name: 'Prosperity', nation: 'Liyue', chars: ['Keqing', 'Ningguang', 'Qiqi', 'Shenhe', 'Yelan', 'Xiao'] },
      { name: 'Transience', nation: 'Inazuma', chars: ['Yoimiya', 'Kokomi', 'Thoma', 'Heizou', 'Kirara'] },
      { name: 'Admonition', nation: 'Sumeru', chars: ['Tighnari', 'Cyno', 'Candace', 'Faruzan'] },
      { name: 'Equity', nation: 'Fontaine', chars: ['Lyney', 'Neuvillette', 'Navia', 'Sigewinne'] },
      { name: 'Contention', nation: 'Natlan', chars: ['Mavuika', 'Kinich', 'Kachina', 'Citlali'] }
    ]
  },
  2: {
    day: 'Tuesday / Friday',
    talents: [
      { name: 'Resistance', nation: 'Mondstadt', chars: ['Jean', 'Diluc', 'Mona', 'Eula', 'Bennett', 'Noelle', 'Razor'] },
      { name: 'Diligence', nation: 'Liyue', chars: ['Ganyu', 'Hu Tao', 'Kaedehara Kazuha', 'Xiangling', 'Chongyun', 'Yun Jin', 'Yaoyao'] },
      { name: 'Elegance', nation: 'Inazuma', chars: ['Kamisato Ayaka', 'Kamisato Ayato', 'Kujou Sara', 'Arataki Itto', 'Kuki Shinobu'] },
      { name: 'Ingenuity', nation: 'Sumeru', chars: ['Nahida', 'Alhaitham', 'Dori', 'Layla', 'Kaveh'] },
      { name: 'Justice', nation: 'Fontaine', chars: ['Furina', 'Clorinde', 'Charlotte', 'Chevreuse'] },
      { name: 'Kindling', nation: 'Natlan', chars: ['Chasca', 'Olorun', 'Lan Yan'] }
    ]
  },
  3: {
    day: 'Wednesday / Saturday',
    talents: [
      { name: 'Ballad', nation: 'Mondstadt', chars: ['Venti', 'Albedo', 'Fischl', 'Rosaria', 'Kaeya', 'Lisa'] },
      { name: 'Gold', nation: 'Liyue', chars: ['Zhongli', 'Xingqiu', 'Beidou', 'Yanfei', 'Baizhu', 'Gaming'] },
      { name: 'Light', nation: 'Inazuma', chars: ['Raiden Shogun', 'Yae Miko', 'Sayu', 'Gorou'] },
      { name: 'Praxis', nation: 'Sumeru', chars: ['Wanderer', 'Nilou', 'Dehya', 'Collei', 'Sethos'] },
      { name: 'Order', nation: 'Fontaine', chars: ['Arlecchino', 'Wriothesley', 'Lynette', 'Emilie'] },
      { name: 'Conflict', nation: 'Natlan', chars: ['Mualani', 'Xilonen', 'Iansan', 'Varesa'] }
    ]
  }
};

let currentShowcaseData = null;
let selectedCharacterIndex = 0;

// Database state
let currentDbCategory = 'characters'; // 'characters', 'weapons', 'artifacts'
let currentElementFilter = 'all';
let dbCache = {
  characters: [],
  weapons: [],
  artifacts: [],
};
let selectedDbItem = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  checkBackendHealth();
  initAccountListeners();
  initDatabaseListeners();
  loadDatabaseCategory('characters');
  initKnowledgeListeners();
  loadKnowledgeBase();
  initChatListeners();
});

/**
 * Tab Navigation Controller
 */
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      switchTab(tab.dataset.tab);
    });
  });
}

function switchTab(tabName) {
  const tabs = document.querySelectorAll('.nav-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach((t) => {
    const isTarget = t.dataset.tab === tabName;
    t.classList.toggle('active', isTarget);
    t.setAttribute('aria-selected', isTarget ? 'true' : 'false');
  });

  panes.forEach((p) => {
    p.classList.toggle('active', p.id === `tab-content-${tabName}`);
  });
}

/**
 * Initialize Account Tab Event Handlers
 */
function initAccountListeners() {
  const importBtn = document.getElementById('import-uid-btn');
  const refreshBtn = document.getElementById('refresh-uid-btn');
  const uidInput = document.getElementById('uid-input');
  const refreshHealthBtn = document.getElementById('refresh-health-btn');
  const copyHealthBtn = document.getElementById('copy-health-btn');

  if (importBtn) {
    importBtn.addEventListener('click', () => {
      const uid = uidInput.value.trim();
      fetchShowcase(uid, false);
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      const uid = uidInput.value.trim();
      fetchShowcase(uid, true);
    });
  }

  if (uidInput) {
    uidInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const uid = uidInput.value.trim();
        fetchShowcase(uid, false);
      }
    });
  }

  if (refreshHealthBtn) {
    refreshHealthBtn.addEventListener('click', checkBackendHealth);
  }

  if (copyHealthBtn) {
    copyHealthBtn.addEventListener('click', async () => {
      const snapshot = window.__latestHealthSnapshot;
      if (!snapshot) return;
      try {
        await navigator.clipboard.writeText(JSON.stringify(snapshot, null, 2));
        copyHealthBtn.textContent = 'Copied';
        setTimeout(() => { copyHealthBtn.textContent = 'Copy Snapshot'; }, 1200);
      } catch (err) {
        console.error('Failed to copy health snapshot:', err);
      }
    });
  }

  // Carousel navigation buttons
  const prevBtn = document.getElementById('carousel-prev-btn');
  const nextBtn = document.getElementById('carousel-next-btn');
  const chipsList = document.getElementById('character-chips-list');
  if (prevBtn && chipsList) {
    prevBtn.addEventListener('click', () => {
      chipsList.scrollBy({ left: -240, behavior: 'smooth' });
    });
  }
  if (nextBtn && chipsList) {
    nextBtn.addEventListener('click', () => {
      chipsList.scrollBy({ left: 240, behavior: 'smooth' });
    });
  }

  // Clickable Spiral Abyss team recommendation action
  const abyssWrap = document.getElementById('prof-abyss-wrap');
  if (abyssWrap) {
    abyssWrap.addEventListener('click', () => {
      const charNames = currentShowcaseData?.characters?.map(c => c.name).join(', ') || 'Arlecchino, Furina, Neuvillette';
      askAssistant(`Recommend me the best two team compositions to 36-star Spiral Abyss Floor 12 using my showcase characters: ${charNames}.`);
    });
  }

  // Optimize artifacts button
  const optArtBtn = document.getElementById('optimize-artifacts-btn');
  if (optArtBtn) {
    optArtBtn.addEventListener('click', () => {
      const char = currentShowcaseData?.characters?.[selectedCharacterIndex];
      if (char) {
        askAssistant(`Analyze my ${char.name} artifacts. Which artifact piece should I replace or re-roll first to maximize DPS? Current stats: CRIT Rate ${((char.stats?.crit_rate || 0)*100).toFixed(1)}%, CRIT DMG ${((char.stats?.crit_dmg || 0)*100).toFixed(1)}%.`);
      }
    });
  }

  // Ask Farming AI button
  const askFarmBtn = document.getElementById('ask-farming-ai-btn');
  if (askFarmBtn) {
    askFarmBtn.addEventListener('click', () => {
      const charNames = currentShowcaseData?.characters?.map(c => c.name).join(', ') || 'my characters';
      askAssistant(`Based on today's domain rotation and my showcase characters (${charNames}), what talent books, domains, or weapons should I prioritize spending my Resin on today?`);
    });
  }
}

/**
 * Fetch Showcase from Backend API
 */
async function fetchShowcase(uid, forceRefresh = false) {
  const errorBanner = document.getElementById('account-error-banner');
  const importBtn = document.getElementById('import-uid-btn');

  if (!uid || uid.length < 9) {
    showAccountError('Please enter a valid 9 or 10-digit Genshin Impact UID.');
    return;
  }

  hideAccountError();
  importBtn.disabled = true;
  importBtn.innerHTML = `<span>Fetching...</span>`;

  try {
    const endpoint = forceRefresh ? `/api/account/${uid}/refresh` : `/api/account/${uid}`;
    const method = forceRefresh ? 'POST' : 'GET';
    const response = await fetch(endpoint, { method });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: 'Failed to load showcase.' }));
      throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
    }

    const data = await response.json();
    currentShowcaseData = data;
    selectedCharacterIndex = 0;
    renderShowcase(data);
  } catch (err) {
    console.error('Showcase fetch error:', err);
    showAccountError(err.message || 'Unable to contact Enka API.');
  } finally {
    importBtn.disabled = false;
    importBtn.innerHTML = `<span>Fetch Showcase</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`;
  }
}

function showAccountError(message) {
  const banner = document.getElementById('account-error-banner');
  const text = document.getElementById('account-error-text');
  if (banner && text) {
    text.textContent = message;
    banner.style.display = 'flex';
  }
}

function hideAccountError() {
  const banner = document.getElementById('account-error-banner');
  if (banner) banner.style.display = 'none';
}

/**
 * Render complete Showcase Data
 */
function renderShowcase(data) {
  const emptyState = document.getElementById('account-empty-state');
  const profileCard = document.getElementById('account-profile-card');
  const selectorContainer = document.getElementById('character-selector-container');
  const activeCharView = document.getElementById('active-character-view');

  if (emptyState) emptyState.style.display = 'none';
  if (profileCard) profileCard.style.display = 'block';

  // 1. Render Profile
  const prof = data.profile || {};
  document.getElementById('prof-nickname').textContent = prof.nickname || 'Traveler';
  document.getElementById('prof-ar').textContent = `AR ${prof.level || 1}`;
  document.getElementById('prof-wl').textContent = `WL ${prof.world_level || 0}`;
  document.getElementById('prof-sig').textContent = prof.signature ? `“${prof.signature}”` : '“No signature set.”';
  document.getElementById('prof-achievements').textContent = (prof.achievement_count || 0).toLocaleString();
  
  const abyssFloor = prof.spiral_abyss_floor ? `Floor ${prof.spiral_abyss_floor}-${prof.spiral_abyss_chamber || 1}` : 'N/A';
  document.getElementById('prof-abyss').textContent = abyssFloor;
  document.getElementById('prof-char-count').textContent = `${data.characters.length} characters`;

  // Render player profile avatar
  const profAvatar = document.getElementById('prof-avatar');
  if (profAvatar) {
    const avatarName = prof.avatar_icon || (data.characters && data.characters.length > 0 ? data.characters[0].name : null);
    if (avatarName) {
      const avatarUrl = getCharacterIconUrl(avatarName);
      profAvatar.innerHTML = `<img src="${avatarUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" alt="${avatarName}" style="width: 100%; height: 100%; object-fit: cover; border-radius: var(--radius-md);">`;
    } else {
      profAvatar.textContent = '👤';
    }
  }

  const cacheBadge = document.getElementById('prof-cache-status');
  if (cacheBadge) {
    cacheBadge.textContent = data.cached ? 'Cached' : 'Fresh Fetch';
    cacheBadge.className = data.cached ? 'badge badge-cache' : 'badge badge-cyan';
  }

  // 2. Render Character Selector Chips
  if (data.characters && data.characters.length > 0) {
    if (selectorContainer) selectorContainer.style.display = 'block';
    if (activeCharView) activeCharView.style.display = 'grid';

    const chipsList = document.getElementById('character-chips-list');
    chipsList.innerHTML = '';

    data.characters.forEach((char, index) => {
      const chip = document.createElement('div');
      chip.className = `char-chip ${index === selectedCharacterIndex ? 'active' : ''}`;
      const iconUrl = getCharacterIconUrl(char.name);
      const elemSvg = getElementSvg(char.element, 18);
      chip.innerHTML = `
        <div style="position: relative; flex-shrink: 0; width: 44px; height: 44px;">
          <img class="char-chip-avatar" src="${iconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" alt="${char.name}" style="width: 44px; height: 44px; border-radius: 50%; border: 2px solid var(--accent-gold); background: rgba(0,0,0,0.3); object-fit: cover;">
          <div style="position: absolute; bottom: -2px; right: -2px;">${elemSvg}</div>
        </div>
        <div>
          <div class="char-chip-name">${char.name}</div>
          <div class="char-chip-lvl">Lv. ${char.level} • C${char.constellation}</div>
        </div>
      `;
      chip.addEventListener('click', () => {
        selectedCharacterIndex = index;
        document.querySelectorAll('.char-chip').forEach((c, i) => {
          c.classList.toggle('active', i === index);
        });
        renderActiveCharacter(data.characters[index]);
      });
      chipsList.appendChild(chip);
    });

    renderActiveCharacter(data.characters[selectedCharacterIndex]);
    renderTodayFarming(data.characters);
  } else {
    if (selectorContainer) selectorContainer.style.display = 'none';
    if (activeCharView) activeCharView.style.display = 'none';
    showAccountError('No character showcase details available for this account.');
  }
}

/**
 * Render Today's Domain Farming Planner
 */
function renderTodayFarming(characters = []) {
  const widget = document.getElementById('today-farming-widget');
  const body = document.getElementById('farming-body');
  const title = document.getElementById('farming-today-title');
  if (!widget || !body) return;

  const now = new Date();
  const dayOfWeek = now.getDay(); // 0 = Sun, 1 = Mon, 2 = Tue, 3 = Wed, 4 = Thu, 5 = Fri, 6 = Sat
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const todayName = dayNames[dayOfWeek];

  title.textContent = `${todayName}'s Domain Rotation & Farming Planner`;
  widget.style.display = 'block';

  let schedKey = dayOfWeek;
  if (schedKey === 4) schedKey = 1;
  else if (schedKey === 5) schedKey = 2;
  else if (schedKey === 6) schedKey = 3;

  if (dayOfWeek === 0) {
    body.innerHTML = `
      <div style="grid-column: 1 / -1; background: rgba(233,190,116,0.08); border: 1px solid rgba(233,190,116,0.3); border-radius: var(--radius-md); padding: 16px;">
        <h4 style="color: var(--accent-gold); font-size: 15px; margin-bottom: 6px;">✨ Sunday Bonus: All Domains Open!</h4>
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">All talent books and weapon ascension materials across all 6 nations are farmable today.</p>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${characters.map(c => `<button class="btn btn-secondary btn-sm" onclick="askAssistant('What materials and talent books do I need to farm for ${c.name}?')">${c.name} Guide</button>`).join('')}
        </div>
      </div>
    `;
    return;
  }

  const sched = ROTATION_SCHEDULE[schedKey];
  if (!sched) return;

  body.innerHTML = sched.talents.map(t => {
    const matchedChars = characters.filter(c => t.chars.some(tc => tc.toLowerCase() === c.name.toLowerCase()));
    const hasMatch = matchedChars.length > 0;
    
    return `
      <div style="background: var(--bg-subcard); border: 1px solid ${hasMatch ? 'var(--accent-gold)' : 'rgba(255,255,255,0.08)'}; border-radius: var(--radius-md); padding: 14px; box-shadow: ${hasMatch ? '0 0 12px rgba(233,190,116,0.15)' : 'none'};">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
          <span style="font-weight: 700; color: ${hasMatch ? 'var(--accent-gold)' : 'var(--text-main)'}; font-size: 14px;">Teachings of ${t.name}</span>
          <span class="badge badge-secondary" style="font-size: 11px;">${t.nation}</span>
        </div>
        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">
          Used by: ${t.chars.slice(0, 4).join(', ')}${t.chars.length > 4 ? ', ...' : ''}
        </div>
        ${hasMatch ? `
          <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed rgba(233,190,116,0.3);">
            <div style="font-size: 11px; font-weight: 600; color: var(--accent-gold); margin-bottom: 4px;">⚡ Ready to farm for your:</div>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
              ${matchedChars.map(mc => `
                <span class="badge badge-gold" style="cursor: pointer;" onclick="askAssistant('How many ${t.name} books do I need to max my ${mc.name}?')">
                  ${mc.name} (Lv. ${mc.level})
                </span>
              `).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

/**
 * Render Selected Character Build
 */
function renderActiveCharacter(char) {
  if (!char) return;
  currentActiveCharacterName = char.name;
  const mbContainer = document.getElementById('char-math-breakdown');
  if (mbContainer && mbContainer.getAttribute('data-char') !== char.name) {
    mbContainer.style.display = 'none';
  }

  const largeAvatar = document.getElementById('char-large-avatar');
  if (largeAvatar) {
    largeAvatar.src = getCharacterIconUrl(char.name);
  }

  const elemWrap = document.getElementById('char-element-icon-wrap');
  if (elemWrap) {
    elemWrap.innerHTML = getElementSvg(char.element, 22);
  }

  // Set Gacha Splash Art background on Hero Banner
  const heroBg = document.getElementById('active-char-hero-bg');
  if (heroBg) {
    const gachaUrl = getCharacterGachaUrl(char.name);
    if (gachaUrl) {
      heroBg.src = gachaUrl;
      heroBg.style.display = 'block';
      heroBg.onerror = () => { heroBg.style.display = 'none'; };
    } else {
      heroBg.style.display = 'none';
    }
  }

  document.getElementById('char-name').textContent = char.name;
  const elemBadge = document.getElementById('char-element');
  elemBadge.textContent = char.element;
  elemBadge.className = `elem-badge elem-${char.element.toLowerCase()}`;

  document.getElementById('char-level').textContent = `Lv. ${char.level}/90`;
  document.getElementById('char-constellation').textContent = `C${char.constellation}`;
  document.getElementById('char-friendship').textContent = `♥ ${char.fetter_level}`;

  // Interactive Action Buttons on Hero Banner
  const actionsWrap = document.getElementById('char-hero-actions');
  if (actionsWrap) {
    const wName = char.weapon ? char.weapon.name : 'equipped weapon';
    const cr = ((char.stats?.crit_rate || 0.05) * 100).toFixed(1);
    const cd = ((char.stats?.crit_dmg || 0.5) * 100).toFixed(1);
    actionsWrap.innerHTML = `
      <button class="btn btn-primary btn-sm" onclick="askAssistant('Review my ${char.name} build. Analyze my weapon (${wName}), stats (CRIT ${cr}% / ${cd}%), and artifact sets.')">
        <span>✨ Ask AI to Review Build</span>
      </button>
      <button class="btn btn-secondary btn-sm" onclick="askAssistant('What are the best teams, artifact substat priorities, and talent crowning order for ${char.name}?')">
        <span>📖 Theorycrafting Guide</span>
      </button>
      <button class="btn btn-secondary btn-sm" id="btn-inspect-math" onclick="toggleMathBreakdown('${char.name}')">
        <span>⚡ Stat Breakdown</span>
      </button>
    `;
  }

  // Talents
  const talentsGrid = document.getElementById('char-talents-grid');
  talentsGrid.innerHTML = '';
  const talentLabels = ['Normal Attack', 'Elemental Skill', 'Elemental Burst'];

  if (char.talents && char.talents.length > 0) {
    char.talents.forEach((t, i) => {
      const isBoosted = t.boosted_level > t.level;
      const box = document.createElement('div');
      box.className = 'talent-box';
      box.innerHTML = `
        <div class="talent-type">${talentLabels[i] || `Talent ${i + 1}`}</div>
        <div class="talent-lvl ${isBoosted ? 'boosted' : ''}">Lv. ${t.boosted_level} ${isBoosted ? '★' : ''}</div>
      `;
      talentsGrid.appendChild(box);
    });
  } else {
    talentsGrid.innerHTML = `<div class="talent-box"><div class="talent-lvl">Talents hidden</div></div>`;
  }

  // Weapon
  const weaponCard = document.getElementById('char-weapon-card');
  if (char.weapon) {
    const w = char.weapon;
    const weaponIconUrl = w.icon ? `https://enka.network/ui/${w.icon}.png` : 'https://enka.network/ui/UI_EquipIcon_Sword_Zephyrus.png';
    const stars = getRarityStars(w.rarity || 4);
    const rarityClass = (w.rarity === 5) ? 'rarity-5-border' : 'rarity-4-border';
    weaponCard.innerHTML = `
      <div style="display: flex; gap: 16px; align-items: center;">
        <div style="position: relative; flex-shrink: 0;">
          <img class="weapon-icon ${rarityClass}" src="${weaponIconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_EquipIcon_Sword_Zephyrus.png'" alt="${w.name}" style="width: 52px; height: 52px; border-radius: 8px; background: rgba(0,0,0,0.3); object-fit: contain; padding: 2px;">
        </div>
        <div style="flex-grow: 1;">
          <div class="weapon-title-row">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="weapon-name" style="font-weight: 700; color: var(--text-main); font-size: 15px;">${w.name}</span>
              <span class="rarity-stars ${w.rarity === 5 ? 'rarity-5' : 'rarity-4'}">${stars}</span>
            </div>
            <span class="weapon-refinement">R${w.refinement}</span>
          </div>
          <div class="weapon-stats-row" style="margin-top: 6px; font-size: 13px; display: flex; gap: 12px; flex-wrap: wrap;">
            <span style="background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 4px;">Lv. ${w.level}/90</span>
            ${w.base_atk ? `<span style="background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 4px;">Base ATK: <strong style="color: var(--text-main);">${Math.round(w.base_atk)}</strong></span>` : ''}
            ${w.sub_stat ? `<span style="background: rgba(233,190,116,0.1); border: 1px solid rgba(233,190,116,0.25); padding: 2px 8px; border-radius: 4px; color: var(--accent-gold);">${w.sub_stat.name}: <strong>${w.sub_stat.formatted}</strong></span>` : ''}
          </div>
        </div>
      </div>
    `;
  } else {
    weaponCard.innerHTML = `<p class="text-muted">No weapon equipped</p>`;
  }

  // Combat Stats
  const statsGrid = document.getElementById('char-combat-stats-grid');
  statsGrid.innerHTML = '';
  const s = char.stats || {};

  const statItems = [
    { label: 'Max HP', val: Math.round(s.max_hp || 0).toLocaleString() },
    { label: 'ATK', val: Math.round(s.atk || 0).toLocaleString() },
    { label: 'DEF', val: Math.round(s.defense || 0).toLocaleString() },
    { label: 'Elemental Mastery', val: Math.round(s.elemental_mastery || 0) },
    { label: 'CRIT Rate', val: `${((s.crit_rate || 0.05) * 100).toFixed(1)}%`, highlight: true },
    { label: 'CRIT DMG', val: `${((s.crit_dmg || 0.5) * 100).toFixed(1)}%`, highlight: true },
    { label: 'Energy Recharge', val: `${((s.energy_recharge || 1.0) * 100).toFixed(1)}%` },
  ];

  if (s.damage_bonuses) {
    for (const [elem, bonus] of Object.entries(s.damage_bonuses)) {
      if (bonus > 0.01) {
        statItems.push({ label: `${elem} DMG`, val: `${(bonus * 100).toFixed(1)}%`, highlight: true });
      }
    }
  }

  statItems.forEach((item) => {
    const chip = document.createElement('div');
    chip.className = 'stat-chip';
    chip.innerHTML = `
      <span class="stat-chip-label">${item.label}</span>
      <span class="stat-chip-val ${item.highlight ? 'stat-highlight' : ''}">${item.val}</span>
    `;
    statsGrid.appendChild(chip);
  });

  renderArtifacts(char.artifacts || []);
}

function renderArtifacts(artifacts) {
  const artifactsList = document.getElementById('char-artifacts-list');
  artifactsList.innerHTML = '';

  // Calculate active Set Bonuses
  const setCounts = {};
  artifacts.forEach(a => {
    const sName = a.set_name || a.name;
    if (sName) {
      setCounts[sName] = (setCounts[sName] || 0) + 1;
    }
  });

  const setBonusesEl = document.getElementById('char-set-bonuses');
  if (setBonusesEl) {
    const bonusBadges = [];
    for (const [setName, count] of Object.entries(setCounts)) {
      if (count >= 4) {
        bonusBadges.push(`<span class="badge badge-gold" style="box-shadow: 0 0 10px var(--accent-gold-glow);">${setName} (4-pc)</span>`);
      } else if (count >= 2) {
        bonusBadges.push(`<span class="badge badge-cyan">${setName} (2-pc)</span>`);
      }
    }
    if (bonusBadges.length > 0) {
      setBonusesEl.innerHTML = bonusBadges.join(' ');
      setBonusesEl.className = '';
    } else {
      setBonusesEl.textContent = 'No Set Bonus';
      setBonusesEl.className = 'badge badge-cache';
    }
  }

  const slotOrder = ['flower', 'plume', 'sands', 'goblet', 'circlet'];
  const slotLabels = {
    flower: 'Flower of Life',
    plume: 'Plume of Death',
    sands: 'Sands of Eon',
    goblet: 'Goblet of Eonothem',
    circlet: 'Circlet of Logos',
  };

  slotOrder.forEach((slot) => {
    const art = artifacts.find((a) => a.slot === slot);
    const card = document.createElement('div');
    card.className = 'artifact-card';

    if (art) {
      const subItemsHtml = art.substats.map((sub) => {
        const isCrit = sub.key.includes('CRITICAL');
        return `
          <div class="art-substat-item">
            <span class="substat-name">${sub.name}</span>
            <span class="substat-val ${isCrit ? 'substat-crit' : ''}">+${sub.formatted}${isCrit ? ' ★' : ''}</span>
          </div>
        `;
      }).join('');

      const relicIconUrl = art.icon ? `https://enka.network/ui/${art.icon}.png` : 'https://enka.network/ui/UI_RelicIcon_15001_4.png';

      card.innerHTML = `
        <div style="display: flex; gap: 14px; align-items: flex-start; flex-grow: 1;">
          <div style="position: relative; flex-shrink: 0;">
            <img class="art-icon rarity-5-border" src="${relicIconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_RelicIcon_15001_4.png'" alt="${art.set_name}" style="width: 48px; height: 48px; border-radius: 8px; background: rgba(0,0,0,0.3); object-fit: contain; padding: 2px;">
          </div>
          <div class="art-main-col" style="flex-grow: 1;">
            <div class="art-slot-header">
              <span class="art-slot-name">${slotLabels[slot]}</span>
              <span class="art-lvl-badge">+${art.level}</span>
            </div>
            <div class="art-set-name" style="font-weight: 600; font-size: 0.9em; margin-top: 2px; color: var(--text-muted);">${art.set_name || art.name}</div>
            <div class="art-main-stat" style="margin-top: 6px; display: flex; justify-content: space-between; align-items: baseline;">
              <span class="art-main-prop" style="font-size: 11px; opacity: 0.8; text-transform: uppercase;">${art.main_stat.name}</span>
              <span class="art-main-val" style="font-weight: 700; font-size: 16px; color: var(--accent-gold); font-family: var(--font-mono);">${art.main_stat.formatted}</span>
            </div>
          </div>
        </div>
        <div class="art-substats-grid" style="margin-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
          ${subItemsHtml || '<span class="text-muted">No substats</span>'}
        </div>
      `;
    } else {
      card.innerHTML = `
        <div class="art-main-col">
          <span class="art-slot-name">${slotLabels[slot]}</span>
          <div class="text-muted" style="font-size: 12px; margin-top: 4px;">Empty Slot</div>
        </div>
        <div class="text-muted" style="font-size: 13px;">No artifact equipped</div>
      `;
    }

    artifactsList.appendChild(card);
  });
}

/**
 * ====================================================
 * PHASE 2: DATABASE EXPLORER CONTROLLER
 * ====================================================
 */
function initDatabaseListeners() {
  const categoryBtns = document.querySelectorAll('#tab-content-characters .sub-tab-btn[data-category]');
  categoryBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      categoryBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentDbCategory = btn.dataset.category;

      const elemBar = document.getElementById('element-filter-bar');
      if (elemBar) {
        elemBar.style.display = currentDbCategory === 'characters' ? 'flex' : 'none';
      }

      loadDatabaseCategory(currentDbCategory);
    });
  });

  const elemChips = document.querySelectorAll('.elem-filter-chip');
  elemChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      elemChips.forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      currentElementFilter = chip.dataset.elem;
      filterAndRenderDbItems();
    });
  });

  const searchInput = document.getElementById('db-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      filterAndRenderDbItems();
    });
  }
}

async function loadDatabaseCategory(category) {
  const grid = document.getElementById('db-items-grid');
  // Skeleton loading
  grid.innerHTML = Array(6).fill('').map(() => `
    <div class="db-item-card" style="pointer-events: none;">
      <div style="display: flex; gap: 14px; align-items: center; width: 100%;">
        <div class="skeleton" style="width: 52px; height: 52px; border-radius: 50%; flex-shrink: 0;"></div>
        <div style="flex: 1;">
          <div class="skeleton" style="width: 60%; height: 16px; margin-bottom: 6px;"></div>
          <div class="skeleton" style="width: 40%; height: 12px;"></div>
        </div>
      </div>
    </div>
  `).join('');

  try {
    const res = await fetch(`/api/data/${category}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    dbCache[category] = data;
    filterAndRenderDbItems();
  } catch (err) {
    grid.innerHTML = `<div class="text-muted" style="padding: 20px;">Failed to load ${category}: ${err.message}</div>`;
  }
}

function filterAndRenderDbItems() {
  const grid = document.getElementById('db-items-grid');
  const searchVal = (document.getElementById('db-search-input')?.value || '').toLowerCase().trim();
  const items = dbCache[currentDbCategory] || [];

  let filtered = items;

  // Filter by element if in characters view
  if (currentDbCategory === 'characters' && currentElementFilter !== 'all') {
    filtered = filtered.filter((c) => c.element.toLowerCase() === currentElementFilter.toLowerCase());
  }

  // Filter by search keyword
  if (searchVal) {
    filtered = filtered.filter((item) => {
      return (
        item.name.toLowerCase().includes(searchVal) ||
        (item.title && item.title.toLowerCase().includes(searchVal)) ||
        (item.description && item.description.toLowerCase().includes(searchVal)) ||
        (item.bonus_2pc && item.bonus_2pc.toLowerCase().includes(searchVal))
      );
    });
  }

  grid.innerHTML = '';
  if (filtered.length === 0) {
    grid.innerHTML = '<div class="text-muted" style="padding: 20px;">No entries match filter.</div>';
    return;
  }

  filtered.forEach((item, index) => {
    const card = document.createElement('div');
    card.className = `db-item-card animate-in ${selectedDbItem?.id === item.id ? 'active' : ''}`;
    card.style.animationDelay = `${Math.min(index * 30, 300)}ms`;

    if (currentDbCategory === 'characters') {
      const elemClass = `elem-${item.element.toLowerCase()}`;
      const charIcon = `https://enka.network/ui/${item.icon || `UI_AvatarIcon_${item.name}`}.png`;
      const rarityClass = `rarity-${item.rarity}`;
      card.innerHTML = `
        <div style="display: flex; gap: 14px; align-items: center; flex-grow: 1;">
          <img class="db-card-avatar ${rarityClass}" src="${charIcon}" onerror="this.onerror=null; this.src='${getImgFallback('character')}'" alt="${item.name}">
          <div class="db-item-info">
            <div class="db-item-title">${item.name}</div>
            <div class="rarity-stars rarity-${item.rarity}">${getRarityStars(item.rarity)}</div>
            <div class="db-item-sub">${item.weapon_type} • ${item.region || 'Teyvat'}</div>
          </div>
        </div>
        <div class="db-item-badges">
          <span class="elem-badge ${elemClass}">
            ${getElementSvg(item.element, 16)}
            ${item.element}
          </span>
        </div>
      `;
    } else if (currentDbCategory === 'weapons') {
      const weaponIcon = `https://enka.network/ui/${item.icon || `UI_EquipIcon_Sword_Zephyrus`}.png`;
      const rarityClass = `rarity-${item.rarity}`;
      card.innerHTML = `
        <div style="display: flex; gap: 14px; align-items: center; flex-grow: 1;">
          <img class="db-card-weapon ${rarityClass}" src="${weaponIcon}" onerror="this.onerror=null; this.src='${getImgFallback('weapon')}'" alt="${item.name}">
          <div class="db-item-info">
            <div class="db-item-title">${item.name}</div>
            <div class="rarity-stars rarity-${item.rarity}">${getRarityStars(item.rarity)}</div>
            <div class="db-item-sub">${item.weapon_type} • Base ATK ${Math.round(item.base_atk_lvl90)}</div>
          </div>
        </div>
        <div class="db-item-badges">
          <span class="badge badge-gold">${item.sub_stat_type || 'ATK'}</span>
        </div>
      `;
    } else if (currentDbCategory === 'artifacts') {
      const artIcon = `https://enka.network/ui/${item.icon || `UI_RelicIcon_15001_4`}.png`;
      card.innerHTML = `
        <div style="display: flex; gap: 14px; align-items: center; flex-grow: 1;">
          <img class="db-card-artifact" src="${artIcon}" onerror="this.onerror=null; this.src='${getImgFallback('artifact')}'" alt="${item.name}">
          <div class="db-item-info">
            <div class="db-item-title">${item.name}</div>
            <div class="rarity-stars rarity-5">${getRarityStars(5)}</div>
            <div class="db-item-sub" style="white-space: normal; line-height: 1.3;">${(item.bonus_2pc || '').substring(0, 60)}${(item.bonus_2pc || '').length > 60 ? '...' : ''}</div>
          </div>
        </div>
        <div class="db-item-badges">
          <span class="badge badge-cyan">Artifact Set</span>
        </div>
      `;
    }

    card.addEventListener('click', () => {
      selectedDbItem = item;
      document.querySelectorAll('.db-item-card').forEach((c) => c.classList.remove('active'));
      card.classList.add('active');
      renderDbDetailInspector(item, currentDbCategory);
    });

    grid.appendChild(card);
  });

  // Auto-select first item if none selected
  if (filtered.length > 0 && (!selectedDbItem || !filtered.find((f) => f.id === selectedDbItem.id))) {
    selectedDbItem = filtered[0];
    const firstCard = grid.querySelector('.db-item-card');
    if (firstCard) firstCard.classList.add('active');
    renderDbDetailInspector(filtered[0], currentDbCategory);
  }
}


/**
 * Render Detail Inspector Pane for Selected DB Entity
 */
function renderDbDetailInspector(item, category) {
  const pane = document.getElementById('db-detail-pane');
  if (!item) return;

  if (category === 'characters') {
    const elemClass = `elem-${item.element.toLowerCase()}`;
    const charIcon = `https://enka.network/ui/${item.icon || `UI_AvatarIcon_${item.name}`}.png`;
    const gachaUrl = getCharacterGachaUrl(item.name);
    const rarityClass = item.rarity === 5 ? 'rarity-5' : 'rarity-4';

    const talentsHtml = (item.talents || []).map((t) => `
      <div class="accordion-item">
        <div class="accordion-title">
          <span>${t.name}</span>
          <span class="badge badge-secondary" style="font-size: 11px;">${t.unlock}</span>
        </div>
        <div class="accordion-desc">${t.description}</div>
      </div>
    `).join('');

    // Constellation dots + descriptions
    const maxConst = 6;
    const consts = item.constellations || [];
    const constDotsHtml = Array.from({ length: maxConst }, (_, i) => {
      const has = consts.find(c => c.level === i + 1);
      return `<div class="const-dot ${has ? 'lit' : ''}" title="${has ? has.name : `C${i+1} Locked`}">${i + 1}</div>`;
    }).join('');

    const constsHtml = consts.map((c) => `
      <div class="accordion-item">
        <div class="accordion-title">
          <span>C${c.level}: ${c.name}</span>
        </div>
        <div class="accordion-desc">${c.description}</div>
      </div>
    `).join('');

    const ascMatHtml = (item.ascension_materials || []).map((m) => `<span class="material-tag">${m}</span>`).join('');
    const talMatHtml = (item.talent_materials || []).map((m) => `<span class="material-tag">${m}</span>`).join('');

    pane.innerHTML = `
      <div class="detail-hero">
        ${gachaUrl ? `<img class="detail-hero-bg" src="${gachaUrl}" alt="" loading="lazy">` : ''}
        <div class="detail-hero-gradient"></div>
        <div class="detail-hero-content">
          <div class="detail-hero-top">
            <img class="detail-hero-avatar ${rarityClass}" src="${charIcon}" onerror="this.onerror=null; this.src='${getImgFallback('character')}'" alt="${item.name}">
            <div class="detail-hero-info">
              <h2 style="display: flex; align-items: center; gap: 8px;">
                ${getElementSvg(item.element, 24)}
                ${item.name}
              </h2>
              <div class="detail-hero-meta" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <span class="rarity-stars rarity-${item.rarity}" style="font-size: 14px;">${getRarityStars(item.rarity)}</span>
                <span class="badge badge-gold">${item.weapon_type}</span>
                <span class="badge badge-secondary">${item.region || 'Teyvat'}</span>
                <button class="btn btn-primary btn-sm" style="margin-left: auto; padding: 4px 10px; font-size: 12px;" onclick="askAssistant('Provide a comprehensive theorycrafting build guide for ${item.name} including best in slot weapons, artifact sets, main stats, substats, and team synergies.')">
                  <span>✨ Ask AI Guide</span>
                </button>
              </div>
            </div>
          </div>
          ${item.title ? `<p style="margin-top: 12px; font-size: 13px; color: var(--text-muted); font-style: italic;">"${item.title}"</p>` : ''}
        </div>
      </div>
      <div class="detail-body">
        <p class="detail-desc" style="margin-bottom: 20px; line-height: 1.5; font-size: 0.9em; opacity: 0.8;">${item.description || ''}</p>

        <div class="section-title">Base Attributes (Level 90)</div>
        <div class="detail-stats-grid">
          <div class="detail-stat-box">
            <div class="detail-stat-label">Base HP</div>
            <div class="detail-stat-val">${Math.round(item.base_hp_lvl90).toLocaleString()}</div>
          </div>
          <div class="detail-stat-box">
            <div class="detail-stat-label">Base ATK</div>
            <div class="detail-stat-val">${Math.round(item.base_atk_lvl90)}</div>
          </div>
          <div class="detail-stat-box">
            <div class="detail-stat-label">Base DEF</div>
            <div class="detail-stat-val">${Math.round(item.base_def_lvl90)}</div>
          </div>
          <div class="detail-stat-box">
            <div class="detail-stat-label">Ascension Stat</div>
            <div class="detail-stat-val" style="color: var(--accent-gold);">${item.ascension_stat} ${item.ascension_stat_val_lvl90}</div>
          </div>
        </div>

        <div class="section-title">Talents &amp; Skills</div>
        <div class="talents-accordion">${talentsHtml}</div>

        <div class="section-title">Constellations</div>
        <div class="constellation-dots">${constDotsHtml}</div>
        <div class="constellations-accordion">${constsHtml}</div>

        ${(ascMatHtml || talMatHtml) ? `
        <div class="section-title">Required Materials</div>
        ${ascMatHtml ? `
          <div style="margin-bottom: 8px; font-size: 12px; color: var(--text-dim);">Character Ascension</div>
          <div class="materials-tag-cloud">${ascMatHtml}</div>
        ` : ''}
        ${talMatHtml ? `
          <div style="margin: 12px 0 8px; font-size: 12px; color: var(--text-dim);">Talent Level Up</div>
          <div class="materials-tag-cloud">${talMatHtml}</div>
        ` : ''}
        ` : ''}
      </div>
    `;
  } else if (category === 'weapons') {
    const refHtml = (item.refinements || []).map((r, i) => `
      <div class="accordion-item">
        <div class="accordion-title">Rank ${i + 1}</div>
        <div class="accordion-desc">${r}</div>
      </div>
    `).join('');

    const weaponIcon = `https://enka.network/ui/${item.icon || `UI_EquipIcon_Sword_Zephyrus`}.png`;
    const rarityClass = item.rarity === 5 ? 'rarity-5' : (item.rarity === 4 ? 'rarity-4' : '');

    pane.innerHTML = `
      <div class="detail-hero" style="min-height: 140px;">
        <div class="detail-hero-gradient"></div>
        <div class="detail-hero-content">
          <div class="detail-hero-top">
            <img class="detail-hero-icon ${rarityClass}" src="${weaponIcon}" onerror="this.onerror=null; this.src='${getImgFallback('weapon')}'" alt="${item.name}">
            <div class="detail-hero-info">
              <h2>${item.name}</h2>
              <div class="detail-hero-meta">
                <span class="rarity-stars rarity-${item.rarity}" style="font-size: 14px;">${getRarityStars(item.rarity)}</span>
                <span class="badge badge-gold">${item.weapon_type}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="detail-body">
        <div class="section-title">Weapon Attributes (Level 90)</div>
        <div class="detail-stats-grid">
          <div class="detail-stat-box">
            <div class="detail-stat-label">Base ATK (Lv. 90)</div>
            <div class="detail-stat-val">${Math.round(item.base_atk_lvl90)}</div>
          </div>
          <div class="detail-stat-box">
            <div class="detail-stat-label">Sub Stat</div>
            <div class="detail-stat-val" style="color: var(--accent-gold);">${item.sub_stat_type || '—'} ${item.sub_stat_val_lvl90 || ''}</div>
          </div>
        </div>

        <div class="section-title">Weapon Passive: ${item.passive_name || 'Special Effect'}</div>
        <p class="accordion-desc" style="margin-bottom: 16px; line-height: 1.5; font-size: 0.95em;">${item.passive_desc || ''}</p>

        <div class="section-title">Refinement Progression (R1–R5)</div>
        <div class="talents-accordion">${refHtml}</div>
      </div>
    `;
  } else if (category === 'artifacts') {
    const piecesHtml = Object.entries(item.pieces || {}).map(([slot, name]) => `
      <div class="stat-chip">
        <span class="stat-chip-label" style="text-transform: capitalize;">${slot}</span>
        <span class="stat-chip-val">${name}</span>
      </div>
    `).join('');

    const artIcon = `https://enka.network/ui/${item.icon || `UI_RelicIcon_15001_4`}.png`;

    pane.innerHTML = `
      <div class="detail-hero" style="min-height: 140px;">
        <div class="detail-hero-gradient"></div>
        <div class="detail-hero-content">
          <div class="detail-hero-top">
            <img class="detail-hero-icon rarity-5" src="${artIcon}" onerror="this.onerror=null; this.src='${getImgFallback('artifact')}'" alt="${item.name}">
            <div class="detail-hero-info">
              <h2>${item.name}</h2>
              <div class="detail-hero-meta">
                <span class="rarity-stars rarity-5" style="font-size: 14px;">${getRarityStars(5)}</span>
                <span class="badge badge-cyan">Artifact Set</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="detail-body">
        <div class="section-title">Set Bonuses</div>
        <div class="accordion-item" style="margin-bottom: 12px;">
          <div class="accordion-title">2-Piece Bonus</div>
          <div class="accordion-desc">${item.bonus_2pc}</div>
        </div>
        ${item.bonus_4pc ? `
        <div class="accordion-item" style="margin-bottom: 20px;">
          <div class="accordion-title">4-Piece Bonus</div>
          <div class="accordion-desc">${item.bonus_4pc}</div>
        </div>` : ''}

        <div class="section-title">Set Pieces</div>
        <div class="combat-stats-grid">${piecesHtml}</div>
      </div>
    `;
  }
}

/**
 * Health Diagnostics Ping
 */
async function checkBackendHealth() {
  const statusPill = document.getElementById('system-status-pill');
  const statusText = document.getElementById('system-status-text');
  const diagStatus = document.getElementById('diag-api-status');
  const diagAppName = document.getElementById('diag-app-name');
  const diagVersion = document.getElementById('diag-version');
  const diagEnv = document.getElementById('diag-env');
  const diagTimestamp = document.getElementById('diag-timestamp');
  const diagEnkaBase = document.getElementById('diag-enka-base');
  const rawPayload = document.getElementById('raw-health-json');
  const manifestStatus = document.getElementById('diag-manifest-status');
  const manifestCacheDir = document.getElementById('diag-cache-dir');
  const manifestDocCount = document.getElementById('diag-manifest-doc-count');
  const manifestGameCount = document.getElementById('diag-manifest-game-count');
  const manifestSourceCount = document.getElementById('diag-manifest-source-count');

  // Phase 2 Version elements
  const diagGameVer = document.getElementById('diag-game-ver');
  const diagGamePatch = document.getElementById('diag-game-patch-name');
  const diagGameRelease = document.getElementById('diag-game-release');
  const diagGameRegion = document.getElementById('diag-game-region');
  const diagGameTotalVer = document.getElementById('diag-game-total-versions');
  const diagGameStaleDocs = document.getElementById('diag-game-stale-docs');
  const diagGameVerification = document.getElementById('diag-game-verification');
  const gameVerBadge = document.getElementById('game-version-badge');

  statusPill.className = 'status-pill status-loading';
  statusText.textContent = 'Checking API...';

  try {
    const [healthResponse, manifestResponse, versionResponse, sourcesResponse, accountResponse, pipelineResponse, completenessResponse, phaseGateResponse] = await Promise.all([
      fetch('/api/health'),
      fetch('/api/data/manifest'),
      fetch('/api/version/status'),
      fetch('/api/sources'),
      fetch('/api/account/summary').catch(() => null),
      fetch('/api/data/pipeline/status').catch(() => null),
      fetch('/api/data/version-completeness').catch(() => null),
      fetch('/api/project/phase-gate').catch(() => null)
    ]);
    if (!healthResponse.ok) throw new Error(`HTTP ${healthResponse.status}`);
    if (!manifestResponse.ok) throw new Error(`HTTP ${manifestResponse.status}`);
    const data = await healthResponse.json();
    const manifest = await manifestResponse.json();
    const versionData = versionResponse.ok ? await versionResponse.json() : null;
    const sourcesData = sourcesResponse.ok ? await sourcesResponse.json() : [];
    const accSummary = accountResponse && accountResponse.ok ? await accountResponse.json() : null;
    const pipelineData = pipelineResponse && pipelineResponse.ok ? await pipelineResponse.json() : null;
    const completenessData = completenessResponse && completenessResponse.ok ? await completenessResponse.json() : null;
    const phaseGateData = phaseGateResponse && phaseGateResponse.ok ? await phaseGateResponse.json() : null;

    statusPill.className = 'status-pill status-online';
    statusText.textContent = 'API Online';

    if (accSummary) {
      const diagAccChar = document.getElementById('diag-acc-char-count');
      const diagAccWeapon = document.getElementById('diag-acc-weapon-count');
      const diagAccArtifact = document.getElementById('diag-acc-artifact-count');
      const diagAccMaterial = document.getElementById('diag-acc-material-count');
      const diagAccTime = document.getElementById('diag-acc-timestamp');
      const diagAccBadge = document.getElementById('diag-account-format-badge');

      if (diagAccChar) diagAccChar.textContent = `${accSummary.total_characters} (${accSummary.built_characters_lvl90} Lv.90)`;
      if (diagAccWeapon) diagAccWeapon.textContent = `${accSummary.total_weapon_instances} (${accSummary.leveled_weapons_lvl90} Lv.90)`;
      if (diagAccArtifact) diagAccArtifact.textContent = `${accSummary.total_artifact_instances} (${accSummary.plus_20_artifacts} +20)`;
      if (diagAccMaterial) diagAccMaterial.textContent = `${accSummary.total_material_types} (${accSummary.unresolved_material_types} general)`;
      if (diagAccTime) diagAccTime.textContent = accSummary.imported_at ? accSummary.imported_at.substring(0, 19).replace('T', ' ') : '—';
      if (diagAccBadge) diagAccBadge.textContent = `${accSummary.source_format} • Normalized`;
    }

    if (pipelineData) {
      const diagActiveData = document.getElementById('diag-active-dataset-ver');
      const diagPipeStatus = document.getElementById('diag-pipeline-update-status');
      if (diagActiveData) diagActiveData.textContent = `v${pipelineData.active_canonical_dataset_version}`;
      if (diagPipeStatus) {
        diagPipeStatus.textContent = pipelineData.update_status;
        if (pipelineData.active_canonical_dataset_version === pipelineData.detected_game_version) {
          diagPipeStatus.style.color = 'var(--accent-teal)';
        } else {
          diagPipeStatus.style.color = 'var(--accent-gold)';
        }
      }
    }

    // Populate Version Completeness & Phase Gate Card
    if (completenessData && phaseGateData) {
      const diagCompStatus = document.getElementById('diag-completeness-status');
      const diagStructGate = document.getElementById('diag-struct-data-gate');
      const diagGameGate = document.getElementById('diag-game-content-gate');
      const diagKnowGate = document.getElementById('diag-knowledge-gate');
      const diagProvGate = document.getElementById('diag-provenance-gate');
      const diagFreshGate = document.getElementById('diag-freshness-gate');
      const diagBlockers = document.getElementById('diag-phase-blockers');
      const phaseBadge = document.getElementById('phase-gate-badge');

      if (diagCompStatus) {
        diagCompStatus.textContent = completenessData.overall_status === 'COMPLETE' ? '🟢 COMPLETE' : '🔴 INCOMPLETE';
        diagCompStatus.style.color = completenessData.overall_status === 'COMPLETE' ? '#34d399' : '#f87171';
      }

      if (phaseBadge) {
        if (phaseGateData.phase_8_allowed) {
          phaseBadge.textContent = '🟢 SAFE TO PROCEED (PHASE 8 READY)';
          phaseBadge.style.background = 'rgba(52, 211, 153, 0.2)';
          phaseBadge.style.color = '#34d399';
          phaseBadge.style.borderColor = '#10b981';
        } else {
          phaseBadge.textContent = '🔴 PHASE 8 BLOCKED';
          phaseBadge.style.background = 'rgba(239, 68, 68, 0.2)';
          phaseBadge.style.color = '#f87171';
          phaseBadge.style.borderColor = '#ef4444';
        }
      }

      const diagCharGate = document.getElementById('diag-char-gate');
      const diagWeapGate = document.getElementById('diag-weap-gate');
      const diagArtGate = document.getElementById('diag-art-gate');
      const diagTeamGate = document.getElementById('diag-team-gate');
      const diagTcGate = document.getElementById('diag-tc-gate');
      const diagPatchGate = document.getElementById('diag-patch-gate');

      if (diagStructGate) {
        diagStructGate.textContent = `${completenessData.structured_data.status === 'COMPLETE' ? '✓' : '⚠'} ${completenessData.structured_data.status} (${Math.round(completenessData.structured_data.coverage * 100)}%)`;
        diagStructGate.style.color = completenessData.structured_data.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagGameGate) {
        diagGameGate.textContent = `${completenessData.game_content.status === 'COMPLETE' ? '✓' : '⚠'} ${completenessData.game_content.status} (${Math.round(completenessData.game_content.coverage * 100)}%)`;
        diagGameGate.style.color = completenessData.game_content.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagCharGate && completenessData.knowledge?.character_guides) {
        const cg = completenessData.knowledge.character_guides;
        diagCharGate.textContent = `${cg.status === 'COMPLETE' ? '✓' : '⚠'} ${cg.status} (${Math.round(cg.coverage_ratio * 100)}% — ${cg.verified_count}/${cg.expected_count})`;
        diagCharGate.style.color = cg.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagWeapGate && completenessData.knowledge?.weapon_guides) {
        const wg = completenessData.knowledge.weapon_guides;
        diagWeapGate.textContent = `${wg.status === 'COMPLETE' ? '✓' : '⚠'} ${wg.status} (${Math.round(wg.coverage_ratio * 100)}%)`;
        diagWeapGate.style.color = wg.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagArtGate && completenessData.knowledge?.artifact_guides) {
        const ag = completenessData.knowledge.artifact_guides;
        diagArtGate.textContent = `${ag.status === 'COMPLETE' ? '✓' : '⚠'} ${ag.status} (${Math.round(ag.coverage_ratio * 100)}%)`;
        diagArtGate.style.color = ag.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagTeamGate && completenessData.knowledge?.team_building) {
        const tg = completenessData.knowledge.team_building;
        diagTeamGate.textContent = `${tg.status === 'COMPLETE' ? '✓' : '⚠'} ${tg.status} (${Math.round(tg.coverage_ratio * 100)}%)`;
        diagTeamGate.style.color = tg.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagTcGate && completenessData.knowledge?.theorycrafting) {
        const tcg = completenessData.knowledge.theorycrafting;
        diagTcGate.textContent = `${tcg.status === 'COMPLETE' ? '✓' : '⚠'} ${tcg.status} (${Math.round(tcg.coverage_ratio * 100)}%)`;
        diagTcGate.style.color = tcg.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagPatchGate && completenessData.knowledge?.current_version_changes) {
        const pg = completenessData.knowledge.current_version_changes;
        diagPatchGate.textContent = `${pg.status === 'COMPLETE' ? '✓' : '⚠'} ${pg.status} (${Math.round(pg.coverage_ratio * 100)}%)`;
        diagPatchGate.style.color = pg.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagKnowGate) {
        diagKnowGate.textContent = `${completenessData.knowledge.status === 'COMPLETE' ? '✓' : '⚠'} ${completenessData.knowledge.status} (${Math.round(completenessData.knowledge.coverage * 100)}%)`;
        diagKnowGate.style.color = completenessData.knowledge.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagProvGate) {
        diagProvGate.textContent = `${completenessData.provenance.status === 'COMPLETE' ? '✓' : '⚠'} ${completenessData.provenance.status} (${completenessData.provenance.records_with_valid_provenance} Valid)`;
        diagProvGate.style.color = completenessData.provenance.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagFreshGate) {
        diagFreshGate.textContent = `${completenessData.freshness.status === 'COMPLETE' ? '✓' : '⚠'} ${completenessData.freshness.status} (${Math.round(completenessData.freshness.freshness_ratio * 100)}%)`;
        diagFreshGate.style.color = completenessData.freshness.status === 'COMPLETE' ? '#34d399' : '#fbbf24';
      }
      if (diagBlockers) {
        if (completenessData.blockers && completenessData.blockers.length > 0) {
          diagBlockers.innerHTML = completenessData.blockers.map(b => `<div style="margin-bottom: 2px;">• ${b}</div>`).join('');
        } else {
          diagBlockers.textContent = 'None — All gates passed!';
        }
      }
    }

    if (diagStatus) diagStatus.textContent = 'Healthy (HTTP 200)';
    if (diagAppName) diagAppName.textContent = data.app_name || 'GenshinIQ';
    if (diagVersion) diagVersion.textContent = `v${data.version || '0.1.0'}`;
    if (diagEnv) diagEnv.textContent = (data.environment || 'development').toUpperCase();
    if (diagTimestamp) diagTimestamp.textContent = data.timestamp || new Date().toISOString();
    if (diagEnkaBase) diagEnkaBase.textContent = data.enka_api_base || '—';
    if (rawPayload) rawPayload.textContent = JSON.stringify({ ...data, version_status: versionData, source_registry_count: sourcesData.length, pipeline: pipelineData }, null, 2);
    window.__latestHealthSnapshot = { health: data, manifest, version: versionData, sources: sourcesData, pipeline: pipelineData };

    // Update Version Card
    if (versionData) {
      const diagActualCurrentVer = document.getElementById('diag-actual-current-ver');
      const diagLatestKnownVer = document.getElementById('diag-latest-known-ver');
      const diagProjectTargetVer = document.getElementById('diag-project-target-ver');
      const diagLastVersionVerif = document.getElementById('diag-last-version-verification');

      if (diagActualCurrentVer) diagActualCurrentVer.textContent = `v${versionData.current_version}`;
      if (diagLatestKnownVer) diagLatestKnownVer.textContent = `v${versionData.latest_known_version || versionData.current_version}`;
      if (diagProjectTargetVer) diagProjectTargetVer.textContent = `v${versionData.project_target_version || versionData.current_version}`;
      if (diagLastVersionVerif) diagLastVersionVerif.textContent = versionData.last_version_verification ? versionData.last_version_verification.substring(0, 10) : '2026-09-08';

      const diagUpdateAvailable = document.getElementById('diag-game-update-available');
      if (diagUpdateAvailable) {
        diagUpdateAvailable.textContent = versionData.update_available ? 'Yes (Update Detected)' : 'No';
        diagUpdateAvailable.style.color = versionData.update_available ? 'var(--accent-cyan)' : 'var(--accent-gold)';
      }

      if (diagGamePatch) diagGamePatch.textContent = versionData.patch_name;
      if (diagGameVerification) diagGameVerification.textContent = `${versionData.verification_status || 'VERIFIED'} (${versionData.discovery_status || 'AVAILABLE'})`;
      if (diagGameTotalVer) diagGameTotalVer.textContent = `${versionData.total_tracked_versions} Patches`;
      if (diagGameStaleDocs) diagGameStaleDocs.textContent = `${versionData.stale_document_count} flagged of ${versionData.total_document_count} (Change-Aware)`;
      if (gameVerBadge) gameVerBadge.textContent = `v${versionData.current_version} Verified Current`;
    }

    if (manifestStatus) manifestStatus.textContent = 'Live manifest loaded';
    if (manifestCacheDir) manifestCacheDir.textContent = manifest.runtime_cache_dir || '—';
    if (manifestDocCount) manifestDocCount.textContent = `${manifest.knowledge_base?.total_documents ?? 0}`;
    if (manifestGameCount) {
      const gameData = manifest.game_data || {};
      manifestGameCount.textContent = `${gameData.characters ?? 0} chars • ${gameData.weapons ?? 0} weapons • ${gameData.artifact_sets ?? 0} sets`;
    }
    if (manifestSourceCount) {
      const tiers = manifest.knowledge_base?.source_tier_counts || {};
      const t1 = tiers['Tier 1'] || 0;
      const t2 = tiers['Tier 2'] || 0;
      const t5 = tiers['Tier 5'] || 0;
      manifestSourceCount.textContent = `${t1} Official (T1) • ${t2} Theorycrafting (T2) • ${t5} Community (T5)`;
    }

    // Populate Sources Registry
    const sourcesList = document.getElementById('sources-registry-list');
    const sourceCountBadge = document.getElementById('diag-source-count-badge');
    if (sourceCountBadge && sourcesData.length) {
      sourceCountBadge.textContent = `${sourcesData.length} Canonical Sources`;
    }
    if (sourcesList && sourcesData.length) {
      sourcesList.innerHTML = sourcesData.map(src => {
        const badgeInfo = getSourceBadge(src.source_type, src.tier);
        return `
          <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 12px; font-size: 0.8em;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
              <span class="badge ${badgeInfo.css}" style="font-size: 9px; padding: 2px 6px;">Tier ${src.tier}</span>
              <span class="font-mono" style="font-size: 10px; opacity: 0.7;">${src.source_id}</span>
            </div>
            <div style="font-weight: 600; color: var(--gold-accent); margin-bottom: 4px;">${src.name}</div>
            <div style="font-size: 10px; color: var(--text-dim); margin-bottom: 6px;">Trust: ${src.trust_level} • Frequency: ${src.update_frequency}</div>
            <div style="font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              <a href="${src.canonical_verification_url || src.base_url}" target="_blank" style="color: var(--cyan-accent); text-decoration: underline;">${src.canonical_verification_url || src.base_url}</a>
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    statusPill.className = 'status-pill status-offline';
    statusText.textContent = 'API Offline';
    if (diagStatus) diagStatus.textContent = 'Connection Failed';
    if (rawPayload) rawPayload.textContent = `Error: ${err.message}`;
    window.__latestHealthSnapshot = null;
    if (manifestStatus) manifestStatus.textContent = 'Manifest unavailable';
  }
}

// Knowledge Base State
let currentKbTopic = 'all';
let kbCache = [];
let selectedKbItem = null;

function initKnowledgeListeners() {
  const tabs = document.querySelectorAll('#tab-content-knowledge .sub-tab-btn');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      currentKbTopic = tab.dataset.topic;
      renderKnowledgeGrid();
    });
  });

  const searchInput = document.getElementById('kb-search-input');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const query = searchInput.value.trim();
        if (query.length > 0) {
          searchKnowledgeBase(query);
        } else {
          loadKnowledgeBase();
        }
      }, 300);
    });
  }

  const refreshKbBtn = document.getElementById('refresh-kb-btn');
  if (refreshKbBtn) {
    refreshKbBtn.addEventListener('click', () => loadKnowledgeBase(true));
  }
}

async function loadKnowledgeBase(forceRefresh = false) {
  const grid = document.getElementById('kb-items-grid');
  if (!grid) return;

  grid.innerHTML = '<div class="loading-spinner">Loading guides...</div>';

  try {
    const response = await fetch(`/api/knowledge/documents${forceRefresh ? `?t=${Date.now()}` : ''}`);
    if (!response.ok) throw new Error('Failed to load guides');
    kbCache = await response.json();
    renderKnowledgeSummary(kbCache);
    renderKnowledgeGrid();
  } catch (err) {
    grid.innerHTML = `<div class="text-error">Error loading knowledge base: ${err.message}</div>`;
  }
}

async function searchKnowledgeBase(query) {
  const grid = document.getElementById('kb-items-grid');
  if (!grid) return;

  grid.innerHTML = '<div class="loading-spinner">Searching...</div>';

  try {
    const response = await fetch(`/api/knowledge/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Search request failed');
    const results = await response.json();
    
    const docs = results.map(r => {
      const cached = kbCache.find(c => c.id === r.id);
      if (cached) return cached;
      return {
        id: r.id,
        title: r.title,
        summary: r.summary,
        content: '',
        metadata: {
          source: r.source,
          source_type: r.source_type,
          character: r.character,
          topic: r.topic,
          game_version: r.game_version,
          tags: []
        }
      };
    });

    renderKnowledgeGrid(docs);
  } catch (err) {
    grid.innerHTML = `<div class="text-error">Error: ${err.message}</div>`;
  }
}

function getSourceBadge(sourceType, tier) {
  const t = Number(tier) || 5;
  if (t === 1 || sourceType === 'OFFICIAL' || sourceType === 'AUTHORITATIVE') {
    return { css: 'badge-gold', label: 'Tier 1 • Official' };
  }
  if (t === 2 || sourceType === 'KQM' || sourceType === 'TCL' || sourceType === 'THEORYCRAFTING') {
    return { css: 'badge-cyan', label: sourceType === 'TCL' ? 'Tier 2 • KQM TCL' : 'Tier 2 • KQM Guide' };
  }
  if (t === 3 || sourceType === 'STRUCTURED_DATA') {
    return { css: 'badge-blue', label: 'Tier 3 • Structured Data' };
  }
  if (t === 4 || sourceType === 'STATISTICAL') {
    return { css: 'badge-indigo', label: 'Tier 4 • Statistical' };
  }
  return { css: 'badge-purple', label: 'Tier 5 • Community Wiki' };
}

function renderKnowledgeGrid(docsToRender = null) {
  const grid = document.getElementById('kb-items-grid');
  if (!grid) return;

  const activeVersion = window.__latestHealthSnapshot?.version?.current_version || '7.0';
  const items = docsToRender || kbCache;
  const filtered = docsToRender ? items : items.filter((doc) => {
    if (currentKbTopic === 'all') return true;
    if (currentKbTopic === 'current') return doc.metadata.game_version === activeVersion;
    return doc.metadata.topic === currentKbTopic;
  });

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-state"><p>No guides found matching this category.</p></div>';
    return;
  }

  grid.innerHTML = '';
  filtered.forEach((doc) => {
    const card = document.createElement('div');
    card.className = `db-list-item card card-glass ${selectedKbItem && selectedKbItem.id === doc.id ? 'active' : ''}`;
    
    const badgeInfo = getSourceBadge(doc.metadata.source_type, doc.metadata.authority_tier);
    const characterTag = doc.metadata.character ? `<span class="badge badge-purple" style="margin-left: 6px;">${doc.metadata.character}</span>` : '';

    // Change-aware freshness and version badge styling
    let verBadgeClass = 'badge-gray';
    let verBadgeText = `v${doc.metadata.game_version}`;
    const freshness = (doc.metadata.freshness || doc.metadata.freshness_status || '').toLowerCase();
    if (doc.metadata.game_version === activeVersion || freshness === 'current') {
      verBadgeClass = 'badge-success';
      verBadgeText = `v${doc.metadata.game_version} Current`;
    } else if (freshness === 'recent_compatible' || (doc.metadata.game_version && doc.metadata.game_version.startsWith('6.'))) {
      verBadgeClass = 'badge-info';
      verBadgeText = `v${doc.metadata.game_version} Compatible`;
    } else if (freshness === 'stale') {
      verBadgeClass = 'badge-warning';
      verBadgeText = `v${doc.metadata.game_version} Stale`;
    } else if (freshness === 'historical') {
      verBadgeClass = 'badge-secondary';
      verBadgeText = `v${doc.metadata.game_version} Historical`;
    }

    let mediaTag = '';
    if (doc.metadata.character) {
      const charIconUrl = getCharacterIconUrl(doc.metadata.character);
      mediaTag = `<img src="${charIconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 36px; height: 36px; border-radius: 50%; border: 1.5px solid var(--accent-gold); background: rgba(0,0,0,0.3); object-fit: cover; flex-shrink: 0;">`;
    } else {
      mediaTag = `<div style="width: 36px; height: 36px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.15); background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;">⚙️</div>`;
    }

    card.innerHTML = `
      <div style="display: flex; gap: 12px; align-items: flex-start; width: 100%;">
        ${mediaTag}
        <div style="flex-grow: 1;">
          <div class="db-item-meta" style="display: flex; gap: 6px; align-items: center; font-size: 0.75em; flex-wrap: wrap;">
            <span class="badge ${badgeInfo.css}">${badgeInfo.label}</span>
            ${characterTag}
            <span class="badge ${verBadgeClass}" style="margin-left: auto;">${verBadgeText}</span>
          </div>
          <div class="db-item-name" style="margin-top: 8px; font-weight: 600; color: var(--gold-accent);">${doc.title}</div>
          <div class="db-item-sub" style="margin-top: 6px; font-size: 0.85em; opacity: 0.8; line-height: 1.4;">${doc.summary}</div>
          <div class="db-item-source" style="margin-top: 10px; font-size: 0.75em; opacity: 0.6; text-align: right;">Source: ${doc.metadata.source}</div>
        </div>
      </div>
    `;

    card.addEventListener('click', () => {
      document.querySelectorAll('#kb-items-grid .db-list-item').forEach((c) => c.classList.remove('active'));
      card.classList.add('active');
      inspectKnowledgeDocument(doc);
    });

    grid.appendChild(card);
  });
}

async function inspectKnowledgeDocument(doc) {
  const pane = document.getElementById('kb-detail-pane');
  if (!pane) return;

  pane.innerHTML = '<div class="loading-spinner">Loading article...</div>';

  try {
    let fullDoc = doc;
    if (!doc.content) {
      const response = await fetch(`/api/knowledge/documents/${doc.id}`);
      if (!response.ok) throw new Error('Failed to fetch full article');
      fullDoc = await response.json();
    }
    
    selectedKbItem = fullDoc;

    const contentHtml = parseMarkdownToHtml(fullDoc.content);
    const badgeInfo = getSourceBadge(fullDoc.metadata.source_type, fullDoc.metadata.authority_tier);
    const characterTag = fullDoc.metadata.character ? `<span class="badge badge-purple" style="margin-left: 6px; font-size: 0.8em; padding: 4px 8px;">${fullDoc.metadata.character}</span>` : '';

    const activeVersion = window.__latestHealthSnapshot?.version?.current_version || '7.0';
    const isStale = fullDoc.metadata.game_version && fullDoc.metadata.game_version !== activeVersion;
    const staleNoticeHtml = isStale ? `
      <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 0.85em; color: #fde68a;">
        ⚠️ <strong>Patch Compatibility Notice:</strong> This article was compiled for <strong>v${fullDoc.metadata.game_version}</strong>. The active live game version is <strong>v${activeVersion}</strong>. Mechanics adjustments or newer weapon/character additions may apply.
      </div>
    ` : '';

    const hashShort = fullDoc.metadata.content_hash ? `${fullDoc.metadata.content_hash.substring(0, 16)}...` : '—';
    const pubDate = fullDoc.metadata.published_at ? new Date(fullDoc.metadata.published_at).toLocaleDateString() : 'Unknown';
    const updDate = fullDoc.metadata.updated_at ? new Date(fullDoc.metadata.updated_at).toLocaleDateString() : 'Unknown';

    pane.innerHTML = `
      <div class="db-detail-header" style="margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 16px;">
        <div class="db-item-meta" style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap;">
          <span class="badge ${badgeInfo.css}" style="font-size: 0.8em; padding: 4px 8px;">${badgeInfo.label}</span>
          ${characterTag}
          <span class="badge ${fullDoc.metadata.game_version === activeVersion ? 'badge-success' : 'badge-gray'}" style="margin-left: auto; font-size: 0.8em; padding: 4px 8px;">v${fullDoc.metadata.game_version}${fullDoc.metadata.game_version === activeVersion ? ' Current' : ''}</span>
        </div>
        <div style="display: flex; gap: 16px; align-items: center;">
          ${fullDoc.metadata.character ? 
            `<img src="${getCharacterIconUrl(fullDoc.metadata.character)}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid var(--accent-gold); background: rgba(0,0,0,0.3); object-fit: cover;">` :
            `<div style="width: 48px; height: 48px; border-radius: 50%; border: 1.5px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 20px;">⚙️</div>`
          }
          <h2 style="margin: 0; color: var(--gold-accent); font-size: 1.5em; font-weight: 700; line-height: 1.3;">${fullDoc.title}</h2>
        </div>
        
        <!-- Phase 3 Provenance Inspector Box -->
        <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 14px; margin-top: 14px; font-size: 0.8em; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px 16px;">
          <div><strong style="color: var(--text-muted);">Source ID:</strong> <span class="font-mono" style="color: var(--accent-gold);">${fullDoc.metadata.source_id || '—'}</span></div>
          <div><strong style="color: var(--text-muted);">Authority Tier:</strong> <span>Tier ${fullDoc.metadata.authority_tier}</span></div>
          <div><strong style="color: var(--text-muted);">Published:</strong> <span>${pubDate}</span></div>
          <div><strong style="color: var(--text-muted);">Last Updated:</strong> <span>${updDate}</span></div>
          <div style="grid-column: 1 / -1;"><strong style="color: var(--text-muted);">Verification URL:</strong> <a href="${fullDoc.metadata.canonical_url || fullDoc.metadata.source_url}" target="_blank" style="color: var(--cyan-accent); text-decoration: underline; word-break: break-all;">${fullDoc.metadata.canonical_url || fullDoc.metadata.source_url}</a></div>
          <div style="grid-column: 1 / -1;"><strong style="color: var(--text-muted);">SHA-256 Digest:</strong> <span class="font-mono" title="${fullDoc.metadata.content_hash}" style="color: var(--text-dim); cursor: help;">${hashShort}</span></div>
        </div>
      </div>
      ${staleNoticeHtml}
      <div class="kb-article-body markdown-body" style="line-height: 1.6; font-size: 0.95em; color: rgba(255,255,255,0.9);">
        ${contentHtml}
      </div>
    `;
  } catch (err) {
    pane.innerHTML = `<div class="text-error">Error loading article details: ${err.message}</div>`;
  }
}

function compareVersionStrings(a, b) {
  const parse = (value) => String(value || '0.0').split('.').map((part) => Number.parseInt(part, 10) || 0);
  const left = parse(a);
  const right = parse(b);
  const length = Math.max(left.length, right.length);

  for (let i = 0; i < length; i += 1) {
    const diff = (left[i] || 0) - (right[i] || 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

function renderKnowledgeSummary(docs = kbCache) {
  const summaryHost = document.getElementById('kb-summary-bar');
  if (!summaryHost) return;

  const total = docs.length;
  const official = docs.filter((d) => d.metadata.authority_tier === 1 || d.metadata.source_type === 'OFFICIAL').length;
  const theorycrafting = docs.filter((d) => d.metadata.authority_tier === 2 || d.metadata.source_type === 'KQM' || d.metadata.source_type === 'TCL').length;
  const community = docs.filter((d) => d.metadata.authority_tier === 5 || d.metadata.source_type === 'COMMUNITY').length;
  const mechanics = docs.filter((d) => d.metadata.topic === 'Game Mechanics').length;
  const activeVersion = window.__latestHealthSnapshot?.version?.current_version || '7.0';

  summaryHost.innerHTML = `
    <div class="diag-item" style="min-width: 130px;">
      <span class="diag-label">Documents</span>
      <span class="diag-val">${total}</span>
    </div>
    <div class="diag-item" style="min-width: 140px;">
      <span class="diag-label">Tier 1 Official</span>
      <span class="diag-val" style="color: var(--accent-gold);">${official}</span>
    </div>
    <div class="diag-item" style="min-width: 160px;">
      <span class="diag-label">Tier 2 Theorycrafting</span>
      <span class="diag-val" style="color: var(--accent-cyan);">${theorycrafting}</span>
    </div>
    <div class="diag-item" style="min-width: 160px;">
      <span class="diag-label">Tier 5 Community</span>
      <span class="diag-val" style="color: #c084fc;">${community}</span>
    </div>
    <div class="diag-item" style="min-width: 130px;">
      <span class="diag-label">Mechanics</span>
      <span class="diag-val">${mechanics}</span>
    </div>
    <div class="diag-item" style="min-width: 160px;">
      <span class="diag-label">Active Live Version</span>
      <span class="diag-val" style="color: var(--accent-gold); font-weight: 700;">v${activeVersion}</span>
    </div>
  `;
}

function parseMarkdownToHtml(md) {
  if (!md) return '';
  let html = md;
  
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Parse Images: ![Alt Text](url)
  html = html.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1" style="max-width: 100%; border-radius: 8px; margin: 16px 0; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: block; height: auto;">');

  // Parse Links: [Link Text](url)
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: var(--cyan-accent); text-decoration: underline;">$1</a>');

  html = html.replace(/^### (.*$)/gim, '<h4 style="color: var(--gold-accent); margin-top: 20px; margin-bottom: 8px; font-weight: 600; border-left: 3px solid var(--gold-accent); padding-left: 8px; font-size: 1.1em;">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="color: var(--gold-accent); margin-top: 28px; margin-bottom: 12px; font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 6px; font-size: 1.25em;">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 style="color: var(--gold-accent); margin-top: 28px; margin-bottom: 14px; font-weight: 700; font-size: 1.45em;">$1</h2>');

  html = html.replace(/^\s*[-*]\s+(.*)$/gim, '<li style="margin-left: 18px; margin-bottom: 6px; list-style-type: disc;">$1</li>');
  html = html.replace(/(<li.*<\/li>)/gim, '<ul>$1</ul>');
  html = html.replace(/<\/ul>\s*<ul>/gim, '');

  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`(.*?)`/g, '<code class="font-mono" style="background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; font-size: 0.9em; color: var(--cyan-accent);">$1</code>');

  const paragraphs = html.split(/\n\n+/);
  html = paragraphs.map(p => {
    const trimmed = p.trim();
    if (trimmed.startsWith('<h') || trimmed.startsWith('<ul') || trimmed.startsWith('<li') || trimmed.startsWith('<ol')) {
      return p;
    }
    return `<p style="margin-bottom: 14px; text-align: justify;">${p.replace(/\n/g, '<br>')}</p>`;
  }).join('\n');

  return html;
}

let chatHistory = [];

function initChatListeners() {
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  
  if (chatInput && sendBtn) {
    sendBtn.addEventListener('click', () => sendMessage());
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }
  
  window.askAssistant = askAssistant;
}

function askAssistant(text) {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.value = text;
    sendMessage();
    switchTab('chat');
  }
}

async function sendMessage() {
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const chatMessages = document.getElementById('chat-messages');
  
  if (!chatInput || !chatMessages) return;
  
  const text = chatInput.value.trim();
  if (!text) return;
  
  // Disable input & send button
  chatInput.disabled = true;
  if (sendBtn) sendBtn.disabled = true;
  chatInput.value = '';
  
  // Append user message bubble
  appendMessageBubble('user', text);
  chatHistory.push({ role: 'user', content: text });
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Append typing indicator
  const typingId = appendTypingIndicator();
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Fetch active UID if imported
  const uid = document.getElementById('uid-input')?.value.trim() || null;
  
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: chatHistory,
        uid: uid
      })
    });
    
    // Remove typing indicator
    removeTypingIndicator(typingId);
    
    if (!response.ok) {
      const errText = await response.text();
      appendMessageBubble('system', `Error: Failed to fetch response. (${response.status}) ${errText}`);
      throw new Error(`Failed to send message: ${response.status}`);
    }
    
    const data = await response.json();
    chatHistory.push({ role: 'model', content: data.content });
    
    // Render assistant bubble
    appendMessageBubble('model', data.content, data.citations, data.query_intents, data.sources_used, data.evidence_types, data.grounding_status, data.grounding_score, data.claims);
    
  } catch (error) {
    console.error('Chat error:', error);
    removeTypingIndicator(typingId);
    appendMessageBubble('system', `Failed to contact chat assistant: ${error.message}`);
  } finally {
    // Re-enable inputs
    chatInput.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
    chatInput.focus();
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

function appendMessageBubble(role, content, citations = [], queryIntents = [], sourcesUsed = [], evidenceTypes = [], groundingStatus = null, groundingScore = null, claims = []) {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;
  
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}-message`;
  
  const avatarDiv = document.createElement('div');
  avatarDiv.className = 'message-avatar';
  if (role === 'user') {
    avatarDiv.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
  } else if (role === 'system') {
    avatarDiv.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff5555" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
  } else {
    avatarDiv.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--accent-gold)" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`;
  }
  
  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'message-bubble';
  
  const htmlContent = parseMarkdownToHtml(content);
  bubbleDiv.innerHTML = htmlContent;

  // Append Phase 8/10 routing and grounding transparency bar
  if (role === 'model' && ((queryIntents && queryIntents.length > 0) || (sourcesUsed && sourcesUsed.length > 0) || groundingStatus)) {
    const metaContainer = document.createElement('div');
    metaContainer.className = 'routing-transparency-meta';
    metaContainer.style.marginTop = '10px';
    metaContainer.style.paddingTop = '6px';
    metaContainer.style.borderTop = '1px solid rgba(255, 255, 255, 0.08)';
    metaContainer.style.fontSize = '11px';
    metaContainer.style.display = 'flex';
    metaContainer.style.flexWrap = 'wrap';
    metaContainer.style.gap = '6px';
    metaContainer.style.alignItems = 'center';

    if (groundingStatus) {
      const groundPill = document.createElement('span');
      const pct = (groundingScore !== null && groundingScore !== undefined) ? ` (${Math.round(groundingScore * 100)}%)` : '';
      if (groundingStatus === 'fully_grounded') {
        groundPill.style.background = 'rgba(46, 213, 115, 0.15)';
        groundPill.style.color = '#2ed573';
        groundPill.style.border = '1px solid rgba(46, 213, 115, 0.4)';
        groundPill.textContent = `✨ Grounded${pct}`;
      } else if (groundingStatus === 'partially_grounded') {
        groundPill.style.background = 'rgba(255, 171, 0, 0.15)';
        groundPill.style.color = '#ffab00';
        groundPill.style.border = '1px solid rgba(255, 171, 0, 0.4)';
        groundPill.textContent = `⚠️ Partially Grounded${pct}`;
      } else {
        groundPill.style.background = 'rgba(255, 71, 87, 0.15)';
        groundPill.style.color = '#ff4757';
        groundPill.style.border = '1px solid rgba(255, 71, 87, 0.4)';
        groundPill.textContent = `⛔ Ungrounded`;
      }
      groundPill.style.padding = '1px 6px';
      groundPill.style.borderRadius = '4px';
      metaContainer.appendChild(groundPill);
    }

    if (queryIntents && queryIntents.length > 0) {
      const intentPill = document.createElement('span');
      intentPill.style.background = 'rgba(233, 190, 116, 0.12)';
      intentPill.style.color = 'var(--accent-gold)';
      intentPill.style.border = '1px solid rgba(233, 190, 116, 0.3)';
      intentPill.style.padding = '1px 6px';
      intentPill.style.borderRadius = '4px';
      intentPill.textContent = `Intent: ${queryIntents.join(', ')}`;
      metaContainer.appendChild(intentPill);
    }
    if (sourcesUsed && sourcesUsed.length > 0) {
      const sourcesPill = document.createElement('span');
      sourcesPill.style.background = 'rgba(78, 205, 196, 0.12)';
      sourcesPill.style.color = 'var(--accent-cyan)';
      sourcesPill.style.border = '1px solid rgba(78, 205, 196, 0.3)';
      sourcesPill.style.padding = '1px 6px';
      sourcesPill.style.borderRadius = '4px';
      sourcesPill.textContent = `Sources: ${sourcesUsed.join(', ')}`;
      metaContainer.appendChild(sourcesPill);
    }
    if (evidenceTypes && evidenceTypes.length > 0) {
      const evidPill = document.createElement('span');
      evidPill.style.background = 'rgba(195, 112, 250, 0.12)';
      evidPill.style.color = '#c370fa';
      evidPill.style.border = '1px solid rgba(195, 112, 250, 0.3)';
      evidPill.style.padding = '1px 6px';
      evidPill.style.borderRadius = '4px';
      evidPill.textContent = `Evidence: ${evidenceTypes.join(', ')}`;
      metaContainer.appendChild(evidPill);
    }
    bubbleDiv.appendChild(metaContainer);
  }
  
  // Append citations if model role and has citations
  if (role === 'model' && citations && citations.length > 0) {
    const citationContainer = document.createElement('div');
    citationContainer.className = 'citation-container';
    citationContainer.style.marginTop = '12px';
    citationContainer.style.borderTop = '1px solid rgba(255, 255, 255, 0.1)';
    citationContainer.style.paddingTop = '8px';
    
    const details = document.createElement('details');
    details.style.cursor = 'pointer';
    
    const summary = document.createElement('summary');
    summary.style.color = 'var(--gold-accent)';
    summary.style.fontSize = '12px';
    summary.style.fontWeight = '500';
    summary.style.outline = 'none';
    summary.innerHTML = `Sources & Citations (${citations.length})`;
    
    const citationList = document.createElement('ul');
    citationList.style.listStyleType = 'none';
    citationList.style.paddingLeft = '0';
    citationList.style.marginTop = '6px';
    citationList.style.fontSize = '12px';
    
    citations.forEach(c => {
      const li = document.createElement('li');
      li.style.marginBottom = '6px';
      li.style.background = 'rgba(255, 255, 255, 0.03)';
      li.style.padding = '6px 10px';
      li.style.borderRadius = '6px';
      li.style.borderLeft = '2px solid var(--gold-accent)';
      
      let typeBadge = '';
      if (c.citation_type === 'dataset') {
        typeBadge = `<span style="background: rgba(78, 205, 196, 0.15); color: var(--accent-cyan); border: 1px solid rgba(78, 205, 196, 0.35); font-size: 9px; padding: 1px 5px; border-radius: 4px; margin-right: 4px; font-weight: 600;">DATASET</span>`;
      } else if (c.citation_type === 'calculation') {
        typeBadge = `<span style="background: rgba(233, 190, 116, 0.15); color: var(--accent-gold); border: 1px solid rgba(233, 190, 116, 0.35); font-size: 9px; padding: 1px 5px; border-radius: 4px; margin-right: 4px; font-weight: 600;">CALCULATION</span>`;
      } else if (c.citation_type === 'account') {
        typeBadge = `<span style="background: rgba(195, 112, 250, 0.15); color: #c370fa; border: 1px solid rgba(195, 112, 250, 0.35); font-size: 9px; padding: 1px 5px; border-radius: 4px; margin-right: 4px; font-weight: 600;">ACCOUNT</span>`;
      } else {
        typeBadge = `<span style="background: rgba(84, 160, 255, 0.15); color: #54a0ff; border: 1px solid rgba(84, 160, 255, 0.35); font-size: 9px; padding: 1px 5px; border-radius: 4px; margin-right: 4px; font-weight: 600;">SOURCE</span>`;
      }

      const sourceLink = `<a href="${c.source_url}" target="_blank" style="color: var(--cyan-accent); font-weight: 500; text-decoration: underline;">${c.display_label || c.source_name}</a>`;
      const canonicalLink = c.canonical_url && c.canonical_url !== c.source_url ? ` • <a href="${c.canonical_url}" target="_blank" style="color: var(--accent-gold); text-decoration: underline;">Verify (Canonical)</a>` : '';
      const tierBadge = c.authority_tier ? `<span class="badge ${c.authority_tier === 1 ? 'badge-gold' : (c.authority_tier === 2 ? 'badge-cyan' : 'badge-purple')}" style="font-size: 9px; padding: 1px 5px; margin-right: 4px;">Tier ${c.authority_tier}</span>` : '';
      const charTag = c.character ? ` <span style="background: rgba(255, 215, 0, 0.15); color: var(--gold-accent); padding: 1px 4px; border-radius: 4px; font-size: 10px;">${c.character}</span>` : '';
      const verTag = c.game_version ? ` <span style="background: rgba(255, 255, 255, 0.1); color: var(--text-muted); padding: 1px 4px; border-radius: 4px; font-size: 10px;">v${c.game_version}</span>` : '';
      const claimInfo = c.claim_supported ? `<div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Supported Claim: <span style="color: #d1d5db;">${c.claim_supported}</span></div>` : '';
      
      li.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px;">
          <div style="display: flex; align-items: center; gap: 4px;">
            ${typeBadge}
            ${tierBadge}
            <strong>${c.topic || 'General Reference'}</strong>
          </div>
          <div>${charTag}${verTag}</div>
        </div>
        <div style="color: var(--text-muted); font-style: italic; margin-bottom: 4px;">"${c.snippet}"</div>
        <div style="font-size: 11px;">Source: ${sourceLink}${canonicalLink}</div>
        ${claimInfo}
      `;
      
      citationList.appendChild(li);
    });
    
    details.appendChild(summary);
    details.appendChild(citationList);
    citationContainer.appendChild(details);
    bubbleDiv.appendChild(citationContainer);
  }
  
  msgDiv.appendChild(avatarDiv);
  msgDiv.appendChild(bubbleDiv);
  chatMessages.appendChild(msgDiv);
  
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTypingIndicator() {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return null;
  
  const id = 'typing-' + Date.now();
  
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message model-message typing-indicator-msg';
  msgDiv.id = id;
  
  const avatarDiv = document.createElement('div');
  avatarDiv.className = 'message-avatar';
  avatarDiv.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--accent-gold)" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`;
  
  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'message-bubble';
  bubbleDiv.style.padding = '12px 16px';
  bubbleDiv.innerHTML = `
    <div style="display: flex; align-items: center; gap: 4px;">
      <span class="typing-dot" style="width: 8px; height: 8px; background: var(--gold-accent); border-radius: 50%; display: inline-block; animation: bounce 1.4s infinite ease-in-out both;"></span>
      <span class="typing-dot" style="width: 8px; height: 8px; background: var(--gold-accent); border-radius: 50%; display: inline-block; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.2s;"></span>
      <span class="typing-dot" style="width: 8px; height: 8px; background: var(--gold-accent); border-radius: 50%; display: inline-block; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.4s;"></span>
    </div>
    <style>
      @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1.0); }
      }
    </style>
  `;
  
  msgDiv.appendChild(avatarDiv);
  msgDiv.appendChild(bubbleDiv);
  chatMessages.appendChild(msgDiv);
  
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  if (!id) return;
  const indicator = document.getElementById(id);
  if (indicator) {
    indicator.remove();
  }
}

/**
 * Phase 7 — Deterministic Build & Stat Engine UI Integration
 */
let currentActiveCharacterName = '';

function toggleCurrentCharMathBreakdown() {
  if (currentActiveCharacterName) {
    toggleMathBreakdown(currentActiveCharacterName);
  }
}

async function toggleMathBreakdown(charName) {
  const container = document.getElementById('char-math-breakdown');
  if (!container) return;

  if (container.style.display === 'block' && container.getAttribute('data-char') === charName) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';
  container.setAttribute('data-char', charName);
  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; padding: 16px; color: var(--accent-gold);">
      <span>⚡ Calculating audited deterministic build breakdown for <strong>${charName}</strong>...</span>
    </div>
  `;

  try {
    const res = await fetch(`/api/build/${encodeURIComponent(charName)}/breakdown`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Calculation error' }));
      container.innerHTML = `
        <div style="color: #ff6b6b; padding: 12px; font-size: 13px;">
          <strong>⚠️ Deterministic Engine Note:</strong> ${err.detail || 'Could not resolve build snapshot for this character.'}
        </div>
      `;
      return;
    }
    const data = await res.json();
    renderMathBreakdown(container, data, charName);
  } catch (err) {
    container.innerHTML = `
      <div style="color: #ff6b6b; padding: 12px; font-size: 13px;">
        <strong>Network Error:</strong> ${err.message}
      </div>
    `;
  }
}

function renderMathBreakdown(container, data, charName) {
  const statusColor = data.status === 'COMPLETE' ? 'var(--status-online)' : 'var(--status-loading)';
  const statusBadge = `<span style="background: rgba(61, 220, 132, 0.15); border: 1px solid ${statusColor}; color: ${statusColor}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">${data.status}</span>`;
  const cvBadge = `<span style="background: rgba(233,190,116,0.15); border: 1px solid var(--accent-gold); color: var(--accent-gold); padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">Artifact Total CV: ${data.artifact_cv_total ? data.artifact_cv_total.toFixed(1) : '0.0'}</span>`;

  // Core formula rows
  const formatStatEquation = (label, b, isPercent = false) => {
    if (!b) return '';
    const baseFormatted = isPercent ? `${(b.base * 100).toFixed(1)}%` : Math.round(b.base).toLocaleString();
    const finalFormatted = isPercent ? `${(b.final * 100).toFixed(1)}%` : Math.round(b.final).toLocaleString();
    const pctStr = b.percent > 0 ? ` + ${(b.percent * 100).toFixed(1)}%` : '';
    const flatStr = b.flat > 0 ? ` + ${Math.round(b.flat).toLocaleString()}` : '';
    return `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06); font-size: 12px;">
        <span style="font-weight: 600; color: var(--text-main); width: 120px;">${label}</span>
        <span style="color: var(--text-muted); font-family: var(--font-mono); font-size: 11px; flex: 1; text-align: center;">
          Base ${baseFormatted}${pctStr}${flatStr}
        </span>
        <span style="font-weight: 700; color: var(--accent-gold); font-family: var(--font-mono); width: 90px; text-align: right;">
          ${finalFormatted}
        </span>
      </div>
    `;
  };

  // Active Set Bonuses HTML
  let setsHtml = '';
  if (data.active_set_bonuses && data.active_set_bonuses.length > 0) {
    setsHtml = `
      <div style="margin-top: 10px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Active Set Bonuses</div>
        <div style="display: flex; flex-direction: column; gap: 4px;">
          ${data.active_set_bonuses.map(s => `
            <div style="background: rgba(255,255,255,0.04); border-radius: 4px; padding: 6px 8px; font-size: 11px;">
              <span style="font-weight: 600; color: var(--text-main);">${s.set_name} (${s.pieces}-pc):</span>
              <span style="color: var(--text-muted);">${s.description || 'Stat boost activated'}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  // Artifact slots CV
  let slotsHtml = '';
  if (data.slot_breakdowns && Object.keys(data.slot_breakdowns).length > 0) {
    const slotNames = { flower: 'Flower', plume: 'Plume', sands: 'Sands', goblet: 'Goblet', circlet: 'Circlet' };
    slotsHtml = `
      <div style="margin-top: 10px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Artifact Slot Breakdown & CV</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 6px;">
          ${Object.entries(data.slot_breakdowns).map(([slot, art]) => `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 8px; font-size: 11px;">
              <div style="display: flex; justify-content: space-between; font-weight: 600; color: var(--text-main); margin-bottom: 2px;">
                <span>${slotNames[slot] || slot}</span>
                <span style="color: var(--accent-cyan); font-family: var(--font-mono);">${art.cv.toFixed(1)} CV</span>
              </div>
              <div style="color: var(--text-muted); font-size: 10px;">${art.main_stat.stat}: +${art.main_stat.value >= 1 ? Math.round(art.main_stat.value) : (art.main_stat.value * 100).toFixed(1) + '%'}</div>
              <div style="color: var(--text-dim); font-size: 9px; margin-top: 2px;">+${art.level} • ${art.set_name}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid rgba(233,190,116,0.25); padding-bottom: 8px;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-weight: 700; font-size: 13px; color: var(--accent-gold);">⚡ Deterministic Stat Breakdown</span>
        ${statusBadge}
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        ${cvBadge}
        <button onclick="document.getElementById('char-math-breakdown').style.display='none'" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 16px; padding: 0 4px;" title="Close">×</button>
      </div>
    </div>

    <div style="background: rgba(0,0,0,0.25); border-radius: 6px; padding: 8px;">
      ${formatStatEquation('Max HP', data.hp)}
      ${formatStatEquation('Base & Total ATK', data.atk)}
      ${formatStatEquation('DEF', data.defense)}
      ${formatStatEquation('CRIT Rate', data.crit_rate, true)}
      ${formatStatEquation('CRIT DMG', data.crit_dmg, true)}
      ${formatStatEquation('Energy Recharge', data.energy_recharge, true)}
      ${formatStatEquation('Elemental Mastery', data.elemental_mastery)}
    </div>

    ${setsHtml}
    ${slotsHtml}

    <div style="margin-top: 10px; font-size: 10px; color: var(--text-dim); text-align: center; border-top: 1px dashed rgba(255,255,255,0.08); padding-top: 6px;">
      Audited Canonical Engine: Base HP/ATK/DEF curve scaling + GOOD v3 snapshot aggregation. Zero hallucinated values.
    </div>
  `;
}

