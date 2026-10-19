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
let currentAccountSnapshot = null;
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

async function loadActiveAccountSnapshot() {
  try {
    const res = await fetch('/api/account');
    if (res.ok) {
      currentAccountSnapshot = await res.json();
    }
  } catch (err) {
    console.warn('No active account snapshot found:', err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  checkBackendHealth();
  initAccountListeners();
  loadActiveAccountSnapshot();
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
      openAbyssTrackerModal();
    });
  }

  // Optimize artifacts button
  const optArtBtn = document.getElementById('optimize-artifacts-btn');
  if (optArtBtn) {
    optArtBtn.addEventListener('click', () => {
      const char = currentShowcaseData?.characters?.[selectedCharacterIndex];
      const charName = char ? char.name : 'Arlecchino';
      openArtifactOptimizerWorkbench(charName);
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

  // Phase 13: Progression Planner Event Handlers
  initProgressionPlannerListeners();
}

/**
 * Initialize Character Progression Planner Event Listeners (Phase 13)
 */
function initProgressionPlannerListeners() {
  const lvlSlider = document.getElementById('target-lvl-slider');
  const lvlVal = document.getElementById('target-lvl-val');
  const talPreset = document.getElementById('target-tal-preset');
  const talVal = document.getElementById('target-tal-val');
  const calcBtn = document.getElementById('calc-progression-btn');

  if (lvlSlider && lvlVal) {
    lvlSlider.addEventListener('input', (e) => {
      lvlVal.textContent = `Lv. ${e.target.value}`;
    });
  }

  if (talPreset && talVal) {
    talPreset.addEventListener('change', (e) => {
      const parts = e.target.value.split(',');
      talVal.textContent = parts.join(' / ');
    });
  }

  if (calcBtn) {
    calcBtn.addEventListener('click', calculateActiveCharacterShortfall);
  }
}

async function calculateActiveCharacterShortfall() {
  const char = currentShowcaseData?.characters?.[selectedCharacterIndex];
  const charName = char ? char.name : 'Arlecchino';

  const lvlSlider = document.getElementById('target-lvl-slider');
  const talPreset = document.getElementById('target-tal-preset');
  const resultsBox = document.getElementById('progression-results-box');
  const resinBadge = document.getElementById('progression-resin-badge');
  const matsList = document.getElementById('progression-missing-materials');
  const farmableTag = document.getElementById('progression-farmable-tag');
  const askAiBtn = document.getElementById('ask-progression-ai-btn');

  if (!resultsBox) return;

  resultsBox.style.display = 'block';
  matsList.innerHTML = '<div class="loading-spinner" style="font-size: 11px;">Calculating inventory shortfall...</div>';

  const targetLvl = lvlSlider ? lvlSlider.value : 90;
  const talParts = talPreset ? talPreset.value.split(',') : [1, 10, 10];
  const normTgt = talParts[0] || 1;
  const skillTgt = talParts[1] || 10;
  const burstTgt = talParts[2] || 10;

  try {
    const res = await fetch(`/api/progression/shortfall/${encodeURIComponent(charName)}?target_level=${targetLvl}&normal_target=${normTgt}&skill_target=${skillTgt}&burst_target=${burstTgt}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const resin = data.shortfall_resin || {};
    resinBadge.textContent = `⚡ ~${resin.total_resin_needed || 0} Resin (${resin.days_of_natural_resin || 0} days)`;

    const breakdown = data.shortfall_breakdown || {};
    const items = Object.entries(breakdown);

    if (items.length === 0) {
      matsList.innerHTML = '<div style="color: #4ade80; font-size: 11px;">✓ All required materials satisfied in inventory!</div>';
    } else {
      matsList.innerHTML = items.map(([name, stat]) => {
        const isSatisfied = stat.missing === 0;
        const color = isSatisfied ? '#4ade80' : 'var(--accent-gold)';
        return `
          <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); padding: 4px 8px; border-radius: 4px;">
            <span style="color: var(--text-main);">${name}</span>
            <span style="font-family: var(--font-mono); color: ${color};">
              ${stat.owned} / ${stat.required} ${isSatisfied ? '✓' : `(need ${stat.missing})`}
            </span>
          </div>
        `;
      }).join('');
    }

    if (data.today_farmable_materials && data.today_farmable_materials.length > 0) {
      farmableTag.textContent = `📅 Farmable Today: ${data.today_farmable_materials.length} material(s)`;
      farmableTag.style.color = 'var(--accent-cyan)';
    } else {
      farmableTag.textContent = '📅 Domain materials not on rotation today';
      farmableTag.style.color = 'var(--text-muted)';
    }

    if (askAiBtn) {
      askAiBtn.onclick = () => {
        askAssistant(`Based on my inventory shortfall for ${charName} (Lv. ${targetLvl}, Talents ${normTgt}/${skillTgt}/${burstTgt}), give me a 3-day optimal farming roadmap.`);
      };
    }
  } catch (err) {
    console.error('Progression shortfall calculation failed:', err);
    matsList.innerHTML = `<div class="text-error" style="font-size: 11px;">Calculation error: ${err.message}</div>`;
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
/**
 * Render Detail Inspector Pane for Selected DB Entity (Phase 11 10-Section Architecture)
 */
async function renderDbDetailInspector(item, category) {
  const pane = document.getElementById('db-detail-pane');
  if (!item || !pane) return;

  if (category === 'characters') {
    await renderCharacterEncyclopedia(item, pane);
  } else if (category === 'weapons') {
    await renderWeaponEncyclopedia(item, pane);
  } else if (category === 'artifacts') {
    renderArtifactEncyclopedia(item, pane);
  }
}

/**
 * 10-Section Character Encyclopedia Implementation
 */
async function renderCharacterEncyclopedia(item, pane) {
  const elemClass = `elem-${item.element.toLowerCase()}`;
  const charIcon = `https://enka.network/ui/${item.icon || `UI_AvatarIcon_${item.name}`}.png`;
  const gachaUrl = getCharacterGachaUrl(item.name);
  const rarityClass = item.rarity === 5 ? 'rarity-5' : 'rarity-4';

  // Check Account Showcase vs GOOD Account Inventory Ownership (Section 3)
  const ownedShowcase = currentShowcaseData?.characters?.find(
    (c) => c.name.toLowerCase() === item.name.toLowerCase()
  );
  const ownedInventory = currentAccountSnapshot?.characters?.find(
    (c) => (c.canonical_name || c.name || '').toLowerCase() === item.name.toLowerCase()
  );
  const isOwned = !!(ownedShowcase || ownedInventory);

  let syncStatus = 'Not Owned in Showcase or Inventory';
  let syncSub = 'Showing canonical baseline build (Lv. 90, C0)';
  let syncActionHtml = '<button class="btn btn-secondary btn-sm" onclick="switchTab(\'account\')">Fetch Showcase or Import GOOD</button>';

  if (ownedShowcase) {
    syncStatus = `Owned in Active Showcase (Lv. ${ownedShowcase.level}, C${ownedShowcase.constellation || 0})`;
    syncSub = `Equipped: ${ownedShowcase.weapon?.name || 'Weapon'} (Lv. ${ownedShowcase.weapon?.level || 90}) • ${ownedShowcase.artifacts?.length || 0}/5 Artifacts`;
    syncActionHtml = `
      <button class="btn btn-secondary btn-sm" onclick="askAssistant('Analyze my showcase ${item.name} build and equipped artifacts. What substats or pieces should I optimize first?')">⚡ Optimize My ${item.name}</button>
      <button class="btn btn-secondary btn-sm" onclick="switchTab('account')">View in Showcase</button>
    `;
  } else if (ownedInventory) {
    const invWep = currentAccountSnapshot?.weapons?.find((w) => w.location === ownedInventory.canonical_name);
    const invArts = (currentAccountSnapshot?.artifacts || []).filter((a) => a.location === ownedInventory.canonical_name);
    const wepText = invWep ? `${invWep.canonical_name} (R${invWep.refinement}, Lv. ${invWep.level})` : 'Unequipped';
    syncStatus = `Owned in Account Inventory (Lv. ${ownedInventory.level}, C${ownedInventory.constellation})`;
    syncSub = `Equipped: ${wepText} • ${invArts.length}/5 Artifacts (GOOD v3)`;
    syncActionHtml = `
      <button class="btn btn-secondary btn-sm" onclick="askAssistant('Review my account inventory build for ${item.name}. What weapons or artifact sets from my bag work best?')">⚡ Review Inventory Build</button>
      <button class="btn btn-secondary btn-sm" onclick="switchTab('account')">View Account Bag</button>
    `;
  }

  // Initial render with skeletons for sections while fetching guide
  pane.innerHTML = `
    <div class="encyclopedia-container">
      <!-- Section 1: Header & Profile Summary -->
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
                <button class="btn btn-primary btn-sm" style="margin-left: auto; padding: 4px 12px; font-size: 12px;" onclick="askAssistant('Review my build and provide recommendations for ${item.name}.')">
                  <span>✨ Review Build with AI</span>
                </button>
              </div>
            </div>
          </div>
          ${item.title ? `<p style="margin-top: 12px; font-size: 13px; color: var(--text-muted); font-style: italic;">"${item.title}"</p>` : ''}
        </div>
      </div>

      <div class="detail-body" style="padding-top: 10px; display: flex; flex-direction: column; gap: 20px;">
        <!-- Section 2: Quick Summary (Role, Strengths, Caveats) -->
        <div class="char-encyclopedia-section" id="encyclopedia-section-summary">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">⚡</span> Quick Summary &amp; Overview</h3>
            <span class="badge badge-info" id="char-role-badge">Loading Role...</span>
          </div>
          <p class="detail-desc" style="margin-bottom: 12px; font-size: 13px; line-height: 1.5;">${item.description || ''}</p>
          <div class="summary-columns" id="char-summary-columns">
            <div class="skeleton" style="height: 80px; border-radius: var(--radius-sm);"></div>
            <div class="skeleton" style="height: 80px; border-radius: var(--radius-sm);"></div>
          </div>
        </div>

        <!-- Section 3: Your Character (Account Integration) -->
        <div class="char-encyclopedia-section" style="padding: 14px;">
          <div class="account-sync-banner ${isOwned ? '' : 'unowned'}">
            <div class="account-sync-left">
              <span style="font-size: 24px;">${isOwned ? (ownedShowcase ? '🛡️' : '📦') : '🔒'}</span>
              <div class="account-sync-details">
                <div class="account-sync-status">
                  ${syncStatus}
                </div>
                <div class="account-sync-sub">
                  ${syncSub}
                </div>
              </div>
            </div>
            <div class="account-sync-actions">
              ${syncActionHtml}
            </div>
          </div>
        </div>

        <!-- Section 4: Interactive Level Scaling Slider (Lv. 1–90) -->
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">📊</span> Dynamic Base Stats &amp; Ascension Scaling</h3>
            <span class="level-badge-large" id="char-level-display">Lv. 90/90</span>
          </div>
          <div class="level-slider-panel">
            <div class="level-slider-controls">
              <div class="level-slider-wrap">
                <span style="font-size: 12px; color: var(--text-muted);">Lv. 1</span>
                <input type="range" id="char-level-slider" min="1" max="90" value="90" step="1">
                <span style="font-size: 12px; color: var(--text-muted);">Lv. 90</span>
              </div>
              <div class="level-presets">
                <button class="level-preset-btn" data-lvl="20">Lv. 20</button>
                <button class="level-preset-btn" data-lvl="40">Lv. 40</button>
                <button class="level-preset-btn" data-lvl="50">Lv. 50</button>
                <button class="level-preset-btn" data-lvl="60">Lv. 60</button>
                <button class="level-preset-btn" data-lvl="70">Lv. 70</button>
                <button class="level-preset-btn" data-lvl="80">Lv. 80</button>
                <button class="level-preset-btn active" data-lvl="90">Lv. 90</button>
              </div>
            </div>
            <div class="dynamic-stats-grid">
              <div class="dynamic-stat-card">
                <div class="dynamic-stat-label">Base HP</div>
                <div class="dynamic-stat-val" id="char-stat-hp">${Math.round(item.base_hp_lvl90 || 0).toLocaleString()}</div>
              </div>
              <div class="dynamic-stat-card">
                <div class="dynamic-stat-label">Base ATK</div>
                <div class="dynamic-stat-val" id="char-stat-atk">${Math.round(item.base_atk_lvl90 || 0)}</div>
              </div>
              <div class="dynamic-stat-card">
                <div class="dynamic-stat-label">Base DEF</div>
                <div class="dynamic-stat-val" id="char-stat-def">${Math.round(item.base_def_lvl90 || 0)}</div>
              </div>
              <div class="dynamic-stat-card">
                <div class="dynamic-stat-label">Ascension Stat</div>
                <div class="dynamic-stat-val gold" id="char-stat-asc">${item.ascension_stat || 'Ascension Stat'} ${item.ascension_stat_val_lvl90 || ''}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Section 5: Talents & Skills with Priorities -->
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">⚔️</span> Talents &amp; Priority Progression</h3>
          </div>
          <div class="talent-priority-strip" id="char-talent-priority-strip">
            <span>Priority Path:</span> <strong id="char-talent-priority-text">Burst (Q) = Skill (E) &gt; Normal Attack</strong>
          </div>
          <div class="talents-accordion" id="char-talents-accordion">
            ${(item.talents || []).map((t) => `
              <div class="accordion-item">
                <div class="accordion-title">
                  <span>${t.name}</span>
                  <span class="badge badge-secondary" style="font-size: 11px;">${t.unlock || 'Talent'}</span>
                </div>
                <div class="accordion-desc">${t.description}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Section 6: Constellations & Milestone Badges -->
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">✨</span> Constellation Milestones</h3>
            <span class="badge badge-secondary">C1 – C6 Progression</span>
          </div>
          <div class="constellation-milestones-grid" id="char-constellations-grid">
            ${(item.constellations || []).map((c) => {
              const isMilestone = [1, 2, 6].includes(c.level) || c.description.toLowerCase().includes('increases') || c.description.toLowerCase().includes('additionally');
              const isOwned = (ownedShowcase && ownedShowcase.constellation >= c.level) || (ownedInventory && ownedInventory.constellation >= c.level);
              return `
                <div class="const-item-v2 ${isMilestone ? 'milestone' : ''} ${isOwned ? 'owned' : ''}">
                  <div class="const-header-row">
                    <span class="const-name-row">C${c.level}: ${c.name}</span>
                    ${isMilestone ? `<span class="const-tag-badge">★ Key Milestone</span>` : ''}
                    ${isOwned ? `<span class="badge badge-gold" style="font-size: 10px;">Owned</span>` : ''}
                  </div>
                  <div class="const-desc-text">${c.description}</div>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <!-- Section 7: Curated Build Recommendations -->
        <div class="char-encyclopedia-section" id="char-build-recommendations">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">🛡️</span> Curated Build Recommendations</h3>
            <span class="badge badge-gold" id="char-build-badge">Theorycrafting BiS</span>
          </div>
          <div id="char-build-body">
            <div class="skeleton" style="height: 140px; border-radius: var(--radius-sm);"></div>
          </div>
        </div>

        <!-- Section 8: Recommended Team Compositions -->
        <div class="char-encyclopedia-section" id="char-teams-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">👥</span> Recommended Team Compositions</h3>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-primary btn-sm" onclick="openTeamBuilderWorkbench('${item.name}')">⚡ Team Builder</button>
              <button class="btn btn-secondary btn-sm" onclick="askAssistant('Recommend team compositions and rotations for ${item.name} based on current meta.')">✨ Ask AI Teams</button>
            </div>
          </div>
          <div class="team-cards-grid" id="char-teams-grid">
            <div class="skeleton" style="height: 120px; border-radius: var(--radius-sm);"></div>
          </div>
        </div>

        <!-- Section 9: Required Materials & Farming Schedule -->
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">📅</span> Materials &amp; Farming Schedule</h3>
            <button class="btn btn-secondary btn-sm" onclick="switchTab('account')">📅 View Today's Rotation</button>
          </div>
          <div id="char-materials-body">
            <div style="margin-bottom: 10px; font-size: 12px; color: var(--text-dim);">Ascension Materials</div>
            <div class="materials-tag-cloud" style="margin-bottom: 14px;">
              ${(item.ascension_materials || []).map((m) => `<span class="material-tag">${m}</span>`).join('')}
            </div>
            <div style="margin-bottom: 10px; font-size: 12px; color: var(--text-dim);">Talent Level Up Books</div>
            <div class="materials-tag-cloud">
              ${(item.talent_materials || []).map((m) => `<span class="material-tag">${m}</span>`).join('')}
            </div>
          </div>
        </div>

        <!-- Section 10: Instant Bridge to AI Assistant -->
        <div class="char-encyclopedia-section" style="background: linear-gradient(135deg, rgba(20, 28, 48, 0.9) 0%, rgba(14, 20, 32, 0.9) 100%); border-color: rgba(94, 234, 212, 0.25);">
          <div class="encyclopedia-section-header" style="border-color: rgba(94, 234, 212, 0.2);">
            <h3 class="encyclopedia-section-title" style="color: #5eead4;"><span class="sec-icon">✨</span> Ask GenshinIQ Assistant About ${item.name}</h3>
          </div>
          <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Ground your questions in verified game database mechanics and your showcase account stats:</p>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="btn btn-secondary btn-sm" onclick="askAssistant('What is the optimal combat rotation and energy requirements for ${item.name}?')">Combat Rotation</button>
            <button class="btn btn-secondary btn-sm" onclick="askAssistant('Compare best weapons for ${item.name} including 4-star F2P alternatives.')">Weapon Alternatives</button>
            <button class="btn btn-secondary btn-sm" onclick="askAssistant('How do I build ${item.name} for Spiral Abyss Floor 12?')">Abyss Floor 12 Strategy</button>
            <button class="btn btn-primary btn-sm" onclick="askAssistant('Give me a full theorycrafting analysis on ${item.name} talent scaling and optimal stat breakpoints.')">✨ In-Depth Theorycrafting</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Attach Slider Listeners
  initCharLevelSlider(item.name);

  // Fetch 10-Section Build Guide
  try {
    const guideRes = await fetch(`/api/data/characters/${encodeURIComponent(item.name)}/guide`);
    if (guideRes.ok) {
      const guide = await guideRes.json();
      populateCharacterGuideSections(item, guide);
    }
  } catch (err) {
    console.warn('Failed to load character guide:', err);
  }
}

/**
 * Initialize Interactive Level Slider for Characters
 */
function initCharLevelSlider(charName) {
  const slider = document.getElementById('char-level-slider');
  const display = document.getElementById('char-level-display');
  const presetBtns = document.querySelectorAll('.level-preset-btn');

  if (!slider) return;

  let debounceTimer = null;
  const updateStats = (level) => {
    if (display) display.textContent = `Lv. ${level}/90`;
    presetBtns.forEach((b) => b.classList.toggle('active', parseInt(b.dataset.lvl) === level));

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/data/characters/${encodeURIComponent(charName)}/scaling?level=${level}`);
        if (res.ok) {
          const data = await res.json();
          const hpEl = document.getElementById('char-stat-hp');
          const atkEl = document.getElementById('char-stat-atk');
          const defEl = document.getElementById('char-stat-def');
          const ascEl = document.getElementById('char-stat-asc');

          if (hpEl) hpEl.textContent = Math.round(data.base_hp || 0).toLocaleString();
          if (atkEl) atkEl.textContent = Math.round(data.base_atk || 0);
          if (defEl) defEl.textContent = Math.round(data.base_def || 0);

          if (ascEl && data.ascension_stats) {
            const entries = Object.entries(data.ascension_stats);
            if (entries.length > 0) {
              const [k, v] = entries[0];
              const formattedVal = (k.includes('crit') || k.includes('bonus') || k.includes('recharge') || k.includes('dmg')) ?
                `${(v * 100).toFixed(1)}%` : Math.round(v);
              ascEl.textContent = `${k.replace('_', ' ')} +${formattedVal}`;
            }
          }
        }
      } catch (err) {
        console.warn('Error fetching character scaling:', err);
      }
    }, 80);
  };

  slider.addEventListener('input', (e) => {
    updateStats(parseInt(e.target.value));
  });

  presetBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const lvl = parseInt(btn.dataset.lvl);
      slider.value = lvl;
      updateStats(lvl);
    });
  });
}

/**
 * Populate Guide Sections with Structured Backend Data
 */
function populateCharacterGuideSections(char, guide) {
  // 1. Role Badge
  const roleBadge = document.getElementById('char-role-badge');
  if (roleBadge && guide.role) {
    roleBadge.textContent = guide.role;
  }

  // 2. Strengths & Caveats
  const summaryCols = document.getElementById('char-summary-columns');
  if (summaryCols) {
    const strengthsHtml = (guide.strengths || ['High universal value across elemental teams', 'Top-tier utility and versatile application']).map(s => `<li>${s}</li>`).join('');
    const caveatsHtml = (guide.caveats || ['Requires strict energy management', 'Optimal performance depends on proper rotation sequencing']).map(c => `<li>${c}</li>`).join('');

    summaryCols.innerHTML = `
      <div class="summary-col strengths">
        <div class="summary-col-title"><span>✔</span> Strengths</div>
        <ul class="summary-list">${strengthsHtml}</ul>
      </div>
      <div class="summary-col caveats">
        <div class="summary-col-title"><span>⚠️</span> Caveats &amp; Playstyle Notes</div>
        <ul class="summary-list">${caveatsHtml}</ul>
      </div>
    `;
  }

  // 3. Talent Priority Text
  const prioText = document.getElementById('char-talent-priority-text');
  if (prioText && guide.talent_priority) {
    prioText.textContent = Array.isArray(guide.talent_priority) ? guide.talent_priority.join(' > ') : guide.talent_priority;
  }

  // 4. Build Recommendations (Weapons, Artifacts, Benchmarks)
  const buildBadge = document.getElementById('char-build-badge');
  if (buildBadge) {
    if (guide.guide_type === 'CURATED_CHARACTER_GUIDE') {
      buildBadge.className = 'badge badge-gold';
      buildBadge.textContent = '✨ Curated Theorycrafting';
      buildBadge.title = guide.guide_provenance || 'KeqingMains Curated Theorycrafting';
    } else {
      buildBadge.className = 'badge badge-secondary';
      buildBadge.textContent = 'ℹ️ Archetype Baseline';
      buildBadge.title = guide.guide_provenance || 'Elemental & weapon class template';
    }
  }

  const buildBody = document.getElementById('char-build-body');
  if (buildBody) {
    const wepList = (guide.recommended_weapons || []).map((w, idx) => {
      const badgeClass = idx === 0 ? 'bis' : (w.notes?.toLowerCase().includes('f2p') ? 'f2p' : 'alt');
      const badgeText = w.badge || (idx === 0 ? 'BiS ⭐' : (w.notes?.toLowerCase().includes('f2p') ? 'F2P Choice 🛡️' : 'Alternative ⚔️'));
      return `
        <div class="gear-item-card">
          <div class="gear-item-left">
            <span class="gear-badge ${badgeClass}">${badgeText}</span>
            <div>
              <div style="font-weight: 700; font-size: 14px; color: var(--text-bright);">${w.name}</div>
              <div style="font-size: 11px; color: var(--text-muted);">${w.notes || w.desc || 'High synergy scaling'}</div>
            </div>
          </div>
          <div class="gear-stats-row">
            <button class="btn btn-secondary btn-sm" style="font-size: 11px; padding: 2px 8px;" onclick="askAssistant('Compare ${w.name} on ${char.name}. How does it perform?')">Compare</button>
          </div>
        </div>
      `;
    }).join('');

    const artList = (guide.recommended_artifacts || []).map((a, idx) => {
      const setName = a.set_name || a.name || 'Artifact Set';
      const notes = a.notes || a.desc || 'Full set bonus recommendation';
      const badgeClass = idx === 0 ? 'bis' : 'alt';
      const badgeText = a.badge || (idx === 0 ? 'Optimal' : 'Alternative');
      return `
        <div class="gear-item-card">
          <div class="gear-item-left">
            <span class="gear-badge ${badgeClass}">${badgeText}</span>
            <div>
              <div style="font-weight: 700; font-size: 14px; color: var(--text-bright);">${setName}</div>
              <div style="font-size: 11px; color: var(--text-muted);">${notes}</div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    const mainStats = guide.main_stats || {};
    const substats = guide.substat_priorities || ['CRIT Rate / CRIT DMG', 'Energy Recharge', 'ATK% / HP%'];
    const benchmarks = guide.stat_benchmarks || {};

    buildBody.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 16px;">
        <div>
          <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px;">Top Weapons</div>
          <div class="gear-tier-list">${wepList || '<div class="text-muted">Standard 5-star and 4-star weapon archetypes apply.</div>'}</div>
        </div>

        <div>
          <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px;">Recommended Artifact Sets</div>
          <div class="gear-tier-list">${artList || '<div class="text-muted">Standard 4-piece elemental sets.</div>'}</div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
          <div style="background: rgba(0,0,0,0.25); padding: 12px; border-radius: var(--radius-sm);">
            <div style="font-size: 12px; font-weight: 700; color: var(--accent-gold); margin-bottom: 6px;">Main Stat Targets</div>
            <div style="font-size: 12px; line-height: 1.6;">
              <div><strong>Sands:</strong> ${mainStats.sands || 'ATK% / ER% / EM'}</div>
              <div><strong>Goblet:</strong> ${mainStats.goblet || 'Elemental DMG%'}</div>
              <div><strong>Circlet:</strong> ${mainStats.circlet || 'CRIT Rate / CRIT DMG'}</div>
            </div>
          </div>

          <div style="background: rgba(0,0,0,0.25); padding: 12px; border-radius: var(--radius-sm);">
            <div style="font-size: 12px; font-weight: 700; color: #58d68d; margin-bottom: 6px;">Substat Priority</div>
            <div style="font-size: 12px; line-height: 1.6; color: var(--text-bright);">
              ${substats.join(' &gt; ')}
            </div>
          </div>
        </div>

        <div>
          <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Target Stat Benchmarks</div>
          <div class="benchmarks-grid">
            ${Object.entries(benchmarks).map(([k, v]) => `
              <div class="benchmark-card">
                <span style="font-size: 12px; color: var(--text-muted); text-transform: uppercase;">${k.replace('_', ' ')}</span>
                <span style="font-size: 13px; font-weight: 700; color: var(--accent-gold);">${v}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  // 5. Team Compositions
  const teamsGrid = document.getElementById('char-teams-grid');
  if (teamsGrid && guide.teams && guide.teams.length > 0) {
    teamsGrid.innerHTML = guide.teams.map((t) => `
      <div class="team-card-v2">
        <div class="team-header-v2">
          <div>
            <span style="font-weight: 700; font-size: 15px; color: var(--text-bright);">${t.name}</span>
            <span class="badge badge-info" style="margin-left: 8px; font-size: 11px;">${t.archetype}</span>
          </div>
          <button class="btn btn-secondary btn-sm" style="font-size: 11px; padding: 2px 8px;" onclick="askAssistant('Explain rotation details and energy management for ${char.name} in ${t.name} team.')">✨ Team Guide</button>
        </div>
        <div class="team-members-row">
          ${(t.members || []).map((m) => {
            const mIcon = getCharacterIconUrl(m);
            return `
              <div class="team-slot-card" onclick="askAssistant('How does ${m} synergize with ${char.name}?')">
                <img class="team-slot-avatar" src="${mIcon}" onerror="this.onerror=null; this.src='${getImgFallback('character')}'" alt="${m}">
                <span class="team-slot-name">${m}</span>
              </div>
            `;
          }).join('')}
        </div>
        ${t.rotation ? `<div class="team-rotation-note"><strong>Rotation:</strong> ${t.rotation}</div>` : ''}
      </div>
    `).join('');
  }

  // 6. Required Materials & Farming Schedule (from guide.farming)
  if (guide.farming) {
    const matBody = document.getElementById('char-materials-body');
    if (matBody && (guide.farming.ascension_materials?.length || guide.farming.talent_materials?.length)) {
      matBody.innerHTML = `
        <div style="margin-bottom: 10px; font-size: 12px; color: var(--text-dim);">Ascension Materials</div>
        <div class="materials-tag-cloud" style="margin-bottom: 14px;">
          ${(guide.farming.ascension_materials || []).map((m) => `<span class="material-tag">${m}</span>`).join('')}
        </div>
        <div style="margin-bottom: 10px; font-size: 12px; color: var(--text-dim);">Talent Level Up Books</div>
        <div class="materials-tag-cloud">
          ${(guide.farming.talent_materials || []).map((m) => `<span class="material-tag">${m}</span>`).join('')}
        </div>
      `;
    }
  }
}

/**
 * Interactive Weapon Encyclopedia View
 */
async function renderWeaponEncyclopedia(item, pane) {
  const weaponIcon = `https://enka.network/ui/${item.icon || `UI_EquipIcon_Sword_Zephyrus`}.png`;
  const rarityClass = item.rarity === 5 ? 'rarity-5' : (item.rarity === 4 ? 'rarity-4' : '');

  pane.innerHTML = `
    <div class="encyclopedia-container">
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
                <button class="btn btn-primary btn-sm" style="margin-left: auto; padding: 4px 10px; font-size: 12px;" onclick="askAssistant('Which characters make the best use of ${item.name}?')">
                  <span>✨ Ask Synergies</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-body" style="display: flex; flex-direction: column; gap: 20px;">
        <!-- Level & Refinement Scaling Panel -->
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">📊</span> Dynamic Level &amp; Refinement Scaling</h3>
            <span class="level-badge-large" id="wep-level-display">Lv. 90/90 • R1</span>
          </div>
          <div class="level-slider-panel">
            <div style="font-size: 12px; color: var(--text-dim); margin-bottom: 4px;">Refinement Rank</div>
            <div class="refinement-switcher">
              <button class="refinement-pill active" data-r="1">R1</button>
              <button class="refinement-pill" data-r="2">R2</button>
              <button class="refinement-pill" data-r="3">R3</button>
              <button class="refinement-pill" data-r="4">R4</button>
              <button class="refinement-pill" data-r="5">R5</button>
            </div>

            <div class="level-slider-controls" style="margin-top: 6px;">
              <div class="level-slider-wrap">
                <span style="font-size: 12px; color: var(--text-muted);">Lv. 1</span>
                <input type="range" id="wep-level-slider" min="1" max="90" value="90" step="1">
                <span style="font-size: 12px; color: var(--text-muted);">Lv. 90</span>
              </div>
            </div>

            <div class="dynamic-stats-grid" style="margin-top: 10px;">
              <div class="dynamic-stat-card">
                <div class="dynamic-stat-label">Base ATK</div>
                <div class="dynamic-stat-val" id="wep-stat-atk">${Math.round(item.base_atk_lvl90 || 0)}</div>
              </div>
              <div class="dynamic-stat-card">
                <div class="dynamic-stat-label">Sub Stat</div>
                <div class="dynamic-stat-val gold" id="wep-stat-sub">${item.sub_stat_type || '—'} ${item.sub_stat_val_lvl90 || ''}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Weapon Passive -->
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">⚔️</span> Weapon Passive: ${item.passive_name || 'Special Effect'}</h3>
          </div>
          <p class="accordion-desc" style="line-height: 1.6; font-size: 13px; margin-bottom: 14px;">${item.passive_desc || 'No passive effect.'}</p>
          <div class="talents-accordion">
            ${(item.refinements || []).map((r, i) => `
              <div class="accordion-item">
                <div class="accordion-title">Rank ${i + 1}</div>
                <div class="accordion-desc">${r}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Action Triggers -->
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">✨</span> Weapon Synergies &amp; Comparisons</h3>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="btn btn-secondary btn-sm" onclick="askAssistant('Which characters can effectively use ${item.name}?')">Best Characters</button>
            <button class="btn btn-secondary btn-sm" onclick="askAssistant('Is ${item.name} worth refining from R1 to R5?')">Refinement Value</button>
            <button class="btn btn-primary btn-sm" onclick="askAssistant('Compare ${item.name} against top alternatives in the ${item.weapon_type} category.')">✨ Weapon Category Comparison</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Attach weapon slider and refinement listeners
  initWeaponScalingControls(item.name);
}

/**
 * Initialize Weapon Scaling Controls
 */
function initWeaponScalingControls(wepName) {
  const slider = document.getElementById('wep-level-slider');
  const display = document.getElementById('wep-level-display');
  const refPills = document.querySelectorAll('.refinement-pill');

  let currentLvl = 90;
  let currentRef = 1;
  let debounceTimer = null;

  const updateWepStats = () => {
    if (display) display.textContent = `Lv. ${currentLvl}/90 • R${currentRef}`;

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/data/weapons/${encodeURIComponent(wepName)}/scaling?level=${currentLvl}&refinement=${currentRef}`);
        if (res.ok) {
          const data = await res.json();
          const atkEl = document.getElementById('wep-stat-atk');
          const subEl = document.getElementById('wep-stat-sub');

          if (atkEl) atkEl.textContent = Math.round(data.base_atk || 0);
          if (subEl) subEl.textContent = `${data.sub_stat_type || '—'} ${data.sub_stat_formatted || ''}`;
        }
      } catch (err) {
        console.warn('Error fetching weapon scaling:', err);
      }
    }, 80);
  };

  if (slider) {
    slider.addEventListener('input', (e) => {
      currentLvl = parseInt(e.target.value);
      updateWepStats();
    });
  }

  refPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      refPills.forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      currentRef = parseInt(pill.dataset.r);
      updateWepStats();
    });
  });
}

/**
 * Interactive Artifact Set Encyclopedia View
 */
function renderArtifactEncyclopedia(item, pane) {
  const piecesHtml = Object.entries(item.pieces || {}).map(([slot, name]) => `
    <div class="stat-chip">
      <span class="stat-chip-label" style="text-transform: capitalize;">${slot}</span>
      <span class="stat-chip-val">${name}</span>
    </div>
  `).join('');

  const artIcon = `https://enka.network/ui/${item.icon || `UI_RelicIcon_15001_4`}.png`;

  pane.innerHTML = `
    <div class="encyclopedia-container">
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
                <button class="btn btn-primary btn-sm" style="margin-left: auto; padding: 4px 10px; font-size: 12px;" onclick="askAssistant('Which characters can use the 4-piece ${item.name} set optimally?')">
                  <span>✨ Best Characters</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-body" style="display: flex; flex-direction: column; gap: 20px;">
        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">🛡️</span> Set Bonuses</h3>
          </div>
          <div class="accordion-item" style="margin-bottom: 12px;">
            <div class="accordion-title">2-Piece Bonus</div>
            <div class="accordion-desc">${item.bonus_2pc}</div>
          </div>
          ${item.bonus_4pc ? `
          <div class="accordion-item" style="margin-bottom: 8px;">
            <div class="accordion-title">4-Piece Bonus</div>
            <div class="accordion-desc">${item.bonus_4pc}</div>
          </div>` : ''}
        </div>

        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">👑</span> 5-Piece Relic Slots</h3>
          </div>
          <div class="combat-stats-grid">${piecesHtml}</div>
        </div>

        <div class="char-encyclopedia-section">
          <div class="encyclopedia-section-header">
            <h3 class="encyclopedia-section-title"><span class="sec-icon">✨</span> Artifact Optimization Triggers</h3>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="btn btn-secondary btn-sm" onclick="askAssistant('Which characters use 2-piece ${item.name}?')">2-Piece Mix &amp; Match</button>
            <button class="btn btn-secondary btn-sm" onclick="askAssistant('Where do I farm the ${item.name} domain, and what resin efficiency does it have?')">Resin &amp; Domain Efficiency</button>
            <button class="btn btn-primary btn-sm" onclick="askAssistant('Analyze my account inventory and show if any of my characters have equipped ${item.name}.')">✨ Inspect Account Equipment</button>
          </div>
        </div>
      </div>
    </div>
  `;
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
    const [healthResponse, manifestResponse, versionResponse, sourcesResponse, accountResponse, pipelineResponse, completenessResponse, phaseGateResponse, detailedDiagResponse] = await Promise.all([
      fetch('/api/health'),
      fetch('/api/data/manifest'),
      fetch('/api/version/status'),
      fetch('/api/sources'),
      fetch('/api/account/summary').catch(() => null),
      fetch('/api/data/pipeline/status').catch(() => null),
      fetch('/api/data/version-completeness').catch(() => null),
      fetch('/api/project/phase-gate').catch(() => null),
      fetch('/api/diagnostics/detailed').catch(() => null)
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
    const detailedDiagData = detailedDiagResponse && detailedDiagResponse.ok ? await detailedDiagResponse.json() : null;

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

    // Populate Phase 18 Observability & Telemetry Card
    if (detailedDiagData) {
      const telemUptime = document.getElementById('diag-telem-uptime');
      const telemSuccess = document.getElementById('diag-telem-success-rate');
      const telemCache = document.getElementById('diag-telem-cache-rate');
      const telemTotalReqs = document.getElementById('diag-telem-total-reqs');
      const checksumsList = document.getElementById('diag-checksums-list');
      const telemBadge = document.getElementById('diag-telemetry-badge');

      if (telemBadge) {
        telemBadge.textContent = detailedDiagData.system_status || 'Healthy';
        telemBadge.className = detailedDiagData.system_status === 'HEALTHY' ? 'badge badge-success' : 'badge badge-warning';
      }

      if (telemUptime) {
        const upSec = detailedDiagData.uptime_seconds || 0;
        const mins = Math.floor(upSec / 60);
        const secs = Math.floor(upSec % 60);
        telemUptime.textContent = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
      }

      if (telemSuccess) {
        const rate = detailedDiagData.runtime_telemetry?.success_rate_pct ?? 100;
        telemSuccess.textContent = `${rate}%`;
        telemSuccess.style.color = rate >= 95 ? '#34d399' : '#fbbf24';
      }

      if (telemCache) {
        const crate = detailedDiagData.runtime_telemetry?.cache_hit_rate_pct ?? 0;
        telemCache.textContent = `${crate}%`;
      }

      if (telemTotalReqs) {
        telemTotalReqs.textContent = `${detailedDiagData.runtime_telemetry?.total_requests ?? 0} calls (${detailedDiagData.runtime_telemetry?.error_count ?? 0} errs)`;
      }

      if (checksumsList && detailedDiagData.canonical_data?.dataset_checksums) {
        const sums = detailedDiagData.canonical_data.dataset_checksums;
        checksumsList.innerHTML = Object.entries(sums).map(([file, hash]) => `
          <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 11px; color: var(--text-bright);">${file}</span>
            <span class="font-mono" style="font-size: 10px; color: var(--accent-cyan); background: rgba(56,189,248,0.1); padding: 2px 6px; border-radius: 4px;">${hash}</span>
          </div>
        `).join('');
      }
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

// =========================================================================
// VISUAL KNOWLEDGE & GUIDES LIBRARY CONTROLLER (Phase 12 Rebuild)
// =========================================================================

let currentGuideCategory = 'all';
let currentGuideElement = 'all';
let currentGuideWeaponType = 'all';
let currentGuideCuratedOnly = false;
let currentGuideOwnedOnly = false;
let currentGuideSearchQuery = '';
let guidesCache = [];
let selectedGuide = null;

function initKnowledgeListeners() {
  // Category Sub-tabs
  const tabs = document.querySelectorAll('#kb-category-tabs .sub-tab-btn');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      currentGuideCategory = tab.dataset.category || 'all';

      // Toggle secondary filter bars
      const elemBar = document.getElementById('kb-element-filter-bar');
      const wepBar = document.getElementById('kb-weapon-filter-bar');
      if (elemBar) {
        elemBar.style.display = (currentGuideCategory === 'all' || currentGuideCategory === 'characters') ? 'flex' : 'none';
      }
      if (wepBar) {
        wepBar.style.display = (currentGuideCategory === 'weapons') ? 'flex' : 'none';
      }

      loadKnowledgeBase();
    });
  });

  // Element Filter Chips
  const elemChips = document.querySelectorAll('#kb-element-filter-bar .elem-filter-chip');
  elemChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      elemChips.forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      currentGuideElement = chip.dataset.elem || 'all';
      loadKnowledgeBase();
    });
  });

  // Weapon Type Filter Chips
  const wepChips = document.querySelectorAll('#kb-weapon-filter-bar .filter-chip');
  wepChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      wepChips.forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      currentGuideWeaponType = chip.dataset.weptype || 'all';
      loadKnowledgeBase();
    });
  });

  // Toggles
  const curatedToggle = document.getElementById('kb-curated-only-toggle');
  if (curatedToggle) {
    curatedToggle.addEventListener('change', (e) => {
      currentGuideCuratedOnly = e.target.checked;
      loadKnowledgeBase();
    });
  }

  const ownedToggle = document.getElementById('kb-owned-only-toggle');
  if (ownedToggle) {
    ownedToggle.addEventListener('change', (e) => {
      currentGuideOwnedOnly = e.target.checked;
      loadKnowledgeBase();
    });
  }

  // Search Input with Debounce
  const searchInput = document.getElementById('kb-search-input');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentGuideSearchQuery = searchInput.value.trim();
        loadKnowledgeBase();
      }, 250);
    });
  }

  // Refresh Button
  const refreshKbBtn = document.getElementById('refresh-kb-btn');
  if (refreshKbBtn) {
    refreshKbBtn.addEventListener('click', () => loadKnowledgeBase(true));
  }
}

async function loadKnowledgeBase(forceRefresh = false) {
  const grid = document.getElementById('kb-items-grid');
  if (!grid) return;

  grid.innerHTML = '<div class="loading-spinner">Loading visual guides...</div>';

  try {
    // 1. Fetch Summary Stats
    fetchGuideSummary();

    // 2. Fetch Guides List
    const params = new URLSearchParams({
      category: currentGuideCategory,
      availability: currentGuideCuratedOnly ? 'curated' : 'all',
      owned_only: currentGuideOwnedOnly ? 'true' : 'false'
    });

    if (currentGuideSearchQuery) params.append('q', currentGuideSearchQuery);
    if (currentGuideElement && currentGuideElement !== 'all') params.append('element', currentGuideElement);
    if (currentGuideWeaponType && currentGuideWeaponType !== 'all') params.append('weapon_type', currentGuideWeaponType);

    const res = await fetch(`/api/guides?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    guidesCache = data.items || [];

    renderKnowledgeGrid(guidesCache);
  } catch (err) {
    console.error('Failed to load guides:', err);
    grid.innerHTML = `<div class="text-error" style="padding: 16px;">Failed to load guides: ${err.message}</div>`;
  }
}

async function fetchGuideSummary() {
  const bar = document.getElementById('kb-summary-bar');
  if (!bar) return;

  try {
    const res = await fetch('/api/guides/summary');
    if (!res.ok) return;
    const data = await res.json();

    bar.innerHTML = `
      <div class="diag-item">
        <span class="diag-label">Total Visual Guides</span>
        <span class="diag-val font-mono" style="color: var(--accent-gold); font-weight: 700;">${data.total_guides || 0}</span>
      </div>
      <div class="diag-item">
        <span class="diag-label">Curated Theorycrafting</span>
        <span class="diag-val" style="color: var(--accent-cyan); font-weight: 700;">${data.curated_guides || 0}</span>
      </div>
      <div class="diag-item">
        <span class="diag-label">Archetype Baselines</span>
        <span class="diag-val font-mono">${data.archetype_baselines || 0}</span>
      </div>
      <div class="diag-item">
        <span class="diag-label">Characters & Weapons</span>
        <span class="diag-val">${data.categories?.characters || 0} Chars / ${data.categories?.weapons || 0} Weps</span>
      </div>
      <div class="diag-item">
        <span class="diag-label">Artifacts & Teams</span>
        <span class="diag-val">${data.categories?.artifacts || 0} Sets / ${data.categories?.teams || 0} Archetypes</span>
      </div>
    `;
  } catch (e) {
    console.warn('Failed to load guide summary:', e);
  }
}

function renderKnowledgeGrid(items) {
  const grid = document.getElementById('kb-items-grid');
  if (!grid) return;

  if (!items || items.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="padding: 30px 20px;">
        <div class="empty-icon">🔍</div>
        <p>No guides found matching your active filters.</p>
        <button class="btn btn-secondary btn-sm" style="margin-top: 10px;" onclick="resetGuideFilters()">Reset Filters</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = '';
  items.forEach((item) => {
    const card = document.createElement('div');
    const isSelected = selectedGuide && selectedGuide.id === item.id;
    card.className = `db-list-item card card-glass ${isSelected ? 'active' : ''}`;

    // Badge styling
    let badgeClass = 'badge-secondary';
    if (item.guide_type === 'CURATED_THEORYCRAFTING' || item.guide_type === 'CURATED_CHARACTER_GUIDE' || item.guide_type === 'CURATED_WEAPON_GUIDE') {
      badgeClass = 'badge-gold';
    } else if (item.guide_type === 'CURATED_ARTIFACT_GUIDE' || item.guide_type === 'CURATED_TEAM_GUIDE') {
      badgeClass = 'badge-cyan';
    } else if (item.guide_type === 'CURATED_MECHANICS_GUIDE') {
      badgeClass = 'badge-purple';
    }

    const iconSrc = item.icon_url || 'https://enka.network/ui/UI_AvatarIcon_NPC.png';
    const rarityClass = item.rarity === 5 ? 'rarity-5-border' : (item.rarity === 4 ? 'rarity-4-border' : '');

    card.innerHTML = `
      <div style="display: flex; gap: 12px; align-items: flex-start; width: 100%;">
        <img src="${iconSrc}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" class="${rarityClass}" style="width: 44px; height: 44px; border-radius: 8px; background: rgba(0,0,0,0.3); object-fit: cover; flex-shrink: 0;">
        <div style="flex-grow: 1; min-width: 0;">
          <div style="display: flex; gap: 6px; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span class="badge ${badgeClass}" style="font-size: 10px; padding: 2px 6px;">${item.guide_badge || 'Guide'}</span>
            ${item.element ? `<span class="badge elem-${item.element.toLowerCase()}" style="font-size: 10px; padding: 2px 6px;">${item.element}</span>` : ''}
          </div>
          <div style="font-weight: 700; color: var(--accent-gold); font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${item.title}</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">${item.subtitle || ''}</div>
          <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px; line-height: 1.35; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${item.summary || ''}</div>
        </div>
      </div>
    `;

    card.addEventListener('click', () => {
      document.querySelectorAll('#kb-items-grid .db-list-item').forEach((c) => c.classList.remove('active'));
      card.classList.add('active');
      inspectGuide(item);
    });

    grid.appendChild(card);
  });
}

function resetGuideFilters() {
  currentGuideElement = 'all';
  currentGuideWeaponType = 'all';
  currentGuideCuratedOnly = false;
  currentGuideOwnedOnly = false;
  currentGuideSearchQuery = '';

  const searchInput = document.getElementById('kb-search-input');
  if (searchInput) searchInput.value = '';

  const curatedToggle = document.getElementById('kb-curated-only-toggle');
  if (curatedToggle) curatedToggle.checked = false;

  const ownedToggle = document.getElementById('kb-owned-only-toggle');
  if (ownedToggle) ownedToggle.checked = false;

  document.querySelectorAll('#kb-element-filter-bar .elem-filter-chip').forEach(c => c.classList.toggle('active', c.dataset.elem === 'all'));
  document.querySelectorAll('#kb-weapon-filter-bar .filter-chip').forEach(c => c.classList.toggle('active', c.dataset.weptype === 'all'));

  loadKnowledgeBase();
}

async function inspectGuide(item) {
  const pane = document.getElementById('kb-detail-pane');
  if (!pane) return;

  selectedGuide = item;
  pane.innerHTML = '<div class="loading-spinner">Loading structured guide...</div>';

  try {
    let endpoint = '';
    const cat = item.category;

    if (cat === 'characters') {
      endpoint = `/api/guides/character/${encodeURIComponent(item.entity_id)}`;
    } else if (cat === 'weapons') {
      endpoint = `/api/guides/weapon/${encodeURIComponent(item.entity_id)}`;
    } else if (cat === 'artifacts') {
      endpoint = `/api/guides/artifact/${encodeURIComponent(item.entity_id)}`;
    } else if (cat === 'teams') {
      endpoint = `/api/guides/teams/${encodeURIComponent(item.entity_id)}`;
    } else if (cat === 'mechanics') {
      endpoint = `/api/guides/mechanics/${encodeURIComponent(item.entity_id)}`;
    } else if (cat === 'farming') {
      endpoint = `/api/guides/farming`;
    }

    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (cat === 'characters') {
      renderCharacterGuideView(data, pane);
    } else if (cat === 'weapons') {
      renderWeaponGuideView(data, pane);
    } else if (cat === 'artifacts') {
      renderArtifactGuideView(data, pane);
    } else if (cat === 'teams') {
      renderTeamGuideView(data, pane);
    } else if (cat === 'mechanics') {
      renderMechanicsGuideView(data, pane);
    } else if (cat === 'farming') {
      renderFarmingGuideView(data, pane);
    }
  } catch (err) {
    console.error('Error fetching guide detail:', err);
    pane.innerHTML = `<div class="text-error" style="padding: 20px;">Failed to load guide details: ${err.message}</div>`;
  }
}

// -------------------------------------------------------------------------
// Category-Specific Visual View Renderers
// -------------------------------------------------------------------------

function renderCharacterGuideView(g, pane) {
  const aiActionsHtml = (g.ai_actions || []).map(a => `
    <button class="btn btn-primary btn-sm" onclick="triggerGuideAction(${JSON.stringify(a.prompt)})">
      ${a.label}
    </button>
  `).join('');

  // Weapon recommendations
  const weaponsHtml = (g.weapon_recommendations || []).map(w => `
    <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">
      <div>
        <div style="font-weight: 700; color: var(--accent-gold); font-size: 13px;">${w.name}</div>
        <div style="font-size: 11px; color: var(--text-muted);">${w.notes || 'High synergy option.'}</div>
      </div>
      <span class="badge ${w.tier === 'BiS' ? 'badge-gold' : 'badge-cyan'}" style="font-size: 10px; padding: 3px 8px; flex-shrink: 0;">${w.tier || 'Best'}</span>
    </div>
  `).join('') || '<div style="color: var(--text-muted); font-size: 12px;">Standard weapon scaling applies.</div>';

  // Artifact recommendations
  const artifactsHtml = (g.artifact_recommendations || []).map(a => `
    <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-weight: 700; color: var(--accent-cyan); font-size: 13px;">${a.set_name}</span>
        <span class="badge badge-info" style="font-size: 10px;">${a.pieces || 4}-pc</span>
      </div>
      <div style="font-size: 11px; color: var(--text-muted);">${a.notes || 'Optimal 4-piece set.'}</div>
    </div>
  `).join('') || '<div style="color: var(--text-muted); font-size: 12px;">Standard artifact sets.</div>';

  // Teams
  const teamsHtml = (g.teams || []).map(t => `
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
      <div style="font-weight: 700; color: var(--accent-gold); font-size: 13px; margin-bottom: 4px;">${t.name}</div>
      <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">${t.notes || 'Strong elemental resonance & synergy.'}</div>
      <div style="display: flex; gap: 6px; flex-wrap: wrap;">
        ${(t.members || []).map(m => `
          <span class="badge badge-secondary" style="font-size: 11px;">${m}</span>
        `).join('')}
      </div>
    </div>
  `).join('') || '<div style="color: var(--text-muted); font-size: 12px;">Versatile team slot.</div>';

  pane.innerHTML = `
    <div class="encyclopedia-container" style="padding: 10px;">
      <!-- Hero Banner -->
      <div class="detail-hero" style="min-height: 140px; margin-bottom: 16px;">
        <div class="detail-hero-gradient"></div>
        <div class="detail-hero-content">
          <div class="detail-hero-top">
            <img class="detail-hero-icon rarity-${g.rarity || 5}" src="${g.icon_url || 'https://enka.network/ui/UI_AvatarIcon_NPC.png'}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" alt="${g.name}">
            <div class="detail-hero-info">
              <h2>${g.name}</h2>
              <div class="detail-hero-meta" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 6px;">
                <span class="badge elem-${(g.element || 'pyro').toLowerCase()}">${g.element}</span>
                <span class="badge badge-secondary">${g.weapon_type}</span>
                <span class="badge badge-gold">${g.role}</span>
                <span class="badge badge-cache">${g.guide_badge}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Summary -->
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <p style="font-size: 13px; color: var(--text-main); line-height: 1.5; margin: 0;">${g.summary || ''}</p>
      </div>

      <!-- AI Contextual Actions Bar -->
      <div style="background: rgba(233,190,116,0.08); border: 1px solid rgba(233,190,116,0.3); border-radius: 10px; padding: 12px 14px; margin-bottom: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">✨ Instant AI Account Guidance</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${aiActionsHtml}
        </div>
      </div>

      <!-- Two-Column Layout for Builds -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 16px;">
        <!-- Left: Weapons & Talents -->
        <div>
          <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
            <div class="encyclopedia-section-header">
              <h3 class="encyclopedia-section-title"><span class="sec-icon">⚔️</span> Recommended Weapons</h3>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              ${weaponsHtml}
            </div>
          </div>

          <div class="char-encyclopedia-section">
            <div class="encyclopedia-section-header">
              <h3 class="encyclopedia-section-title"><span class="sec-icon">📜</span> Talent Upgrade Priority</h3>
            </div>
            <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 8px;">
              ${(g.talent_priority || ['Burst', 'Skill', 'Normal Attack']).map((t, idx) => `
                <span class="badge badge-gold" style="font-size: 12px; font-weight: 700;">${idx + 1}. ${t}</span>
              `).join('<span style="color: var(--text-dim); font-size: 11px;">→</span>')}
            </div>
            <p style="font-size: 12px; color: var(--text-muted); margin: 0;">Focus skill levels according to combat rotation priority.</p>
          </div>
        </div>

        <!-- Right: Artifacts & Stats -->
        <div>
          <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
            <div class="encyclopedia-section-header">
              <h3 class="encyclopedia-section-title"><span class="sec-icon">🛡️</span> Artifact Recommendations</h3>
            </div>
            ${artifactsHtml}
            <div style="margin-top: 10px; background: rgba(0,0,0,0.25); border-radius: 6px; padding: 10px; font-size: 11px;">
              <div style="font-weight: 700; color: var(--accent-gold); margin-bottom: 4px;">Main Stat Priorities:</div>
              <div><strong>Sands:</strong> ${g.main_stat_priorities?.sands || 'ATK% / ER'}</div>
              <div><strong>Goblet:</strong> ${g.main_stat_priorities?.goblet || 'Elemental DMG Bonus'}</div>
              <div><strong>Circlet:</strong> ${g.main_stat_priorities?.circlet || 'CRIT Rate / CRIT DMG'}</div>
            </div>
            <div style="margin-top: 8px; font-size: 11px; color: var(--text-muted);">
              <strong>Substat Priority:</strong> ${(g.substat_priorities || ['CRIT Rate', 'CRIT DMG', 'ATK%']).join(' > ')}
            </div>
          </div>
        </div>
      </div>

      <!-- Stat Target Benchmarks -->
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">🎯</span> Target Stat Benchmarks</h3>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px;">
          <div class="stat-chip"><span class="stat-chip-label">CRIT Rate</span><span class="stat-chip-val" style="color: var(--accent-gold);">${g.stat_targets?.crit_rate || '70%+'}</span></div>
          <div class="stat-chip"><span class="stat-chip-label">CRIT DMG</span><span class="stat-chip-val" style="color: var(--accent-gold);">${g.stat_targets?.crit_dmg || '140%+'}</span></div>
          <div class="stat-chip"><span class="stat-chip-label">Energy Recharge</span><span class="stat-chip-val" style="color: var(--accent-cyan);">${g.stat_targets?.energy_recharge || '130%+'}</span></div>
          <div class="stat-chip"><span class="stat-chip-label">Primary Stat</span><span class="stat-chip-val">${g.stat_targets?.primary_stat_target || '2,000+ ATK'}</span></div>
        </div>
      </div>

      <!-- Synergistic Teams -->
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">👥</span> Recommended Team Compositions</h3>
        </div>
        ${teamsHtml}
      </div>

      <!-- Rotation Breakdown -->
      ${g.rotation_summary ? `
      <div class="char-encyclopedia-section">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">🔄</span> Core Combat Rotation</h3>
        </div>
        <div style="background: rgba(0,0,0,0.3); border-left: 3px solid var(--accent-gold); padding: 10px 14px; border-radius: 4px; font-size: 12px; line-height: 1.5;">
          ${g.rotation_summary}
        </div>
      </div>` : ''}
    </div>
  `;
}

function renderWeaponGuideView(w, pane) {
  const aiActionsHtml = (w.ai_actions || []).map(a => `
    <button class="btn btn-primary btn-sm" onclick="triggerGuideAction(${JSON.stringify(a.prompt)})">
      ${a.label}
    </button>
  `).join('');

  const notableUsersHtml = (w.notable_users || []).map(u => `
    <div style="display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 6px 10px;">
      <img src="${getCharacterIconUrl(u)}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;">
      <span style="font-weight: 600; font-size: 12px; color: var(--text-main);">${u}</span>
    </div>
  `).join('') || '<div style="color: var(--text-muted); font-size: 12px;">Universal weapon option.</div>';

  pane.innerHTML = `
    <div class="encyclopedia-container" style="padding: 10px;">
      <div class="detail-hero" style="min-height: 140px; margin-bottom: 16px;">
        <div class="detail-hero-gradient"></div>
        <div class="detail-hero-content">
          <div class="detail-hero-top">
            <img class="detail-hero-icon rarity-${w.rarity || 5}" src="${w.icon_url}" onerror="this.onerror=null; this.src='${getImgFallback('weapon')}'" alt="${w.name}">
            <div class="detail-hero-info">
              <h2>${w.name}</h2>
              <div class="detail-hero-meta" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 6px;">
                <span class="rarity-stars rarity-${w.rarity || 5}">${getRarityStars(w.rarity || 5)}</span>
                <span class="badge badge-secondary">${w.weapon_type}</span>
                <span class="badge badge-gold">${w.guide_badge}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style="background: rgba(233,190,116,0.08); border: 1px solid rgba(233,190,116,0.3); border-radius: 10px; padding: 12px 14px; margin-bottom: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">✨ Instant AI Weapon Analysis</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${aiActionsHtml}
        </div>
      </div>

      <!-- Stat Curves -->
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">📊</span> Deterministic Combat Scaling</h3>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
          <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px;">
            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">Level 1 Baseline</div>
            <div style="font-size: 14px; font-weight: 700; color: var(--text-main);">Base ATK: ${Math.round(w.base_atk_lv1 || 0)}</div>
            <div style="font-size: 12px; color: var(--accent-gold); margin-top: 2px;">${w.sub_stat_type || '—'}: ${w.sub_stat_lv1 || '—'}</div>
          </div>
          <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px; border: 1px solid rgba(233,190,116,0.25);">
            <div style="font-size: 11px; color: var(--accent-gold); margin-bottom: 4px; font-weight: 700;">Level 90 Ceiling</div>
            <div style="font-size: 14px; font-weight: 700; color: var(--accent-gold);">Base ATK: ${Math.round(w.base_atk_lv90 || 0)}</div>
            <div style="font-size: 12px; color: var(--accent-cyan); margin-top: 2px;">${w.sub_stat_type || '—'}: ${w.sub_stat_lv90 || '—'}</div>
          </div>
        </div>
      </div>

      <!-- Weapon Passive -->
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">⚔️</span> Weapon Passive: ${w.passive_name || 'Special Effect'}</h3>
        </div>
        <p style="font-size: 13px; line-height: 1.6; color: var(--text-main); margin-bottom: 12px;">${w.passive_desc || 'Increases stats based on refinement rank.'}</p>
        <div style="font-size: 11px; color: var(--text-muted);">${w.f2p_context || ''}</div>
      </div>

      <!-- Notable Users -->
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">👤</span> Notable Characters</h3>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px;">
          ${notableUsersHtml}
        </div>
      </div>
    </div>
  `;
}

function renderArtifactGuideView(art, pane) {
  const aiActionsHtml = (art.ai_actions || []).map(a => `
    <button class="btn btn-primary btn-sm" onclick="triggerGuideAction(${JSON.stringify(a.prompt)})">
      ${a.label}
    </button>
  `).join('');

  const notableUsersHtml = (art.notable_users || []).map(u => `
    <div style="display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 6px 10px;">
      <img src="${getCharacterIconUrl(u)}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;">
      <span style="font-weight: 600; font-size: 12px; color: var(--text-main);">${u}</span>
    </div>
  `).join('') || '<div style="color: var(--text-muted); font-size: 12px;">Universal set option.</div>';

  pane.innerHTML = `
    <div class="encyclopedia-container" style="padding: 10px;">
      <div class="detail-hero" style="min-height: 140px; margin-bottom: 16px;">
        <div class="detail-hero-gradient"></div>
        <div class="detail-hero-content">
          <div class="detail-hero-top">
            <img class="detail-hero-icon rarity-5" src="${art.icon_url}" onerror="this.onerror=null; this.src='${getImgFallback('artifact')}'" alt="${art.name}">
            <div class="detail-hero-info">
              <h2>${art.name}</h2>
              <div class="detail-hero-meta" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 6px;">
                <span class="rarity-stars rarity-5">★★★★★</span>
                <span class="badge badge-cyan">${art.guide_badge}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style="background: rgba(233,190,116,0.08); border: 1px solid rgba(233,190,116,0.3); border-radius: 10px; padding: 12px 14px; margin-bottom: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">✨ Instant AI Artifact Check</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${aiActionsHtml}
        </div>
      </div>

      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">🛡️</span> Set Bonuses</h3>
        </div>
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px; margin-bottom: 10px;">
          <div style="font-weight: 700; color: var(--accent-gold); font-size: 12px; margin-bottom: 4px;">2-Piece Bonus</div>
          <div style="font-size: 13px; line-height: 1.5; color: var(--text-main);">${art.bonus_2pc || 'Increases stats.'}</div>
        </div>
        ${art.bonus_4pc ? `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px;">
          <div style="font-weight: 700; color: var(--accent-cyan); font-size: 12px; margin-bottom: 4px;">4-Piece Bonus</div>
          <div style="font-size: 13px; line-height: 1.5; color: var(--text-main);">${art.bonus_4pc}</div>
        </div>` : ''}
      </div>

      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">👤</span> Notable Users</h3>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px;">
          ${notableUsersHtml}
        </div>
      </div>

      <div class="char-encyclopedia-section">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">📍</span> Domain &amp; Farming Schedule</h3>
        </div>
        <div style="font-size: 12px; color: var(--text-muted); line-height: 1.5;">
          <div><strong>Domain:</strong> ${art.domain_info?.domain_name || 'Artifact Reliquary Domain'}</div>
          <div><strong>Availability:</strong> ${art.domain_info?.days_available || 'Always Available (Every Day)'}</div>
        </div>
      </div>
    </div>
  `;
}

function renderTeamGuideView(t, pane) {
  const coreCharsHtml = (t.core_characters || []).map(c => `
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px; display: flex; align-items: center; gap: 10px;">
      <img src="${getCharacterIconUrl(c.name)}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 38px; height: 38px; border-radius: 50%; object-fit: cover;">
      <div>
        <div style="font-weight: 700; color: var(--accent-gold); font-size: 13px;">${c.name}</div>
        <div style="font-size: 11px; color: var(--accent-cyan);">${c.role}</div>
      </div>
    </div>
  `).join('');

  const stepsHtml = (t.rotation_steps || []).map((step, idx) => `
    <div style="display: flex; gap: 10px; align-items: flex-start; margin-bottom: 10px;">
      <span class="badge badge-gold" style="font-size: 11px; font-weight: 700; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; border-radius: 50%; flex-shrink: 0;">${idx + 1}</span>
      <div style="font-size: 12px; line-height: 1.5; color: var(--text-main);">${step}</div>
    </div>
  `).join('');

  pane.innerHTML = `
    <div class="encyclopedia-container" style="padding: 10px;">
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <span class="badge badge-cyan" style="margin-bottom: 8px;">${t.archetype}</span>
        <h2 style="color: var(--accent-gold); margin: 0 0 8px 0; font-size: 20px;">${t.title}</h2>
        <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin: 0;">${t.summary}</p>
      </div>

      <div style="background: rgba(233,190,116,0.08); border: 1px solid rgba(233,190,116,0.3); border-radius: 10px; padding: 12px 14px; margin-bottom: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">✨ Instant AI Team Builder</div>
        <button class="btn btn-primary btn-sm" onclick="triggerGuideAction('Can I build a ${t.title} team using characters available on my account?')">
          ✨ Check If I Can Build This Team
        </button>
      </div>

      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">👥</span> Core Roster</h3>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
          ${coreCharsHtml}
        </div>
      </div>

      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">🔄</span> Step-by-Step Execution Sequence</h3>
        </div>
        <div style="background: rgba(0,0,0,0.25); border-radius: 8px; padding: 14px;">
          ${stepsHtml}
        </div>
      </div>

      <div class="char-encyclopedia-section">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">🔀</span> Team Variations</h3>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${(t.variants || []).map(v => `<span class="badge badge-secondary" style="font-size: 11px; padding: 4px 10px;">${v}</span>`).join('')}
        </div>
      </div>
    </div>
  `;
}

function renderMechanicsGuideView(m, pane) {
  const sectionsHtml = (m.visual_sections || []).map(s => `
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px; margin-bottom: 10px;">
      <div style="font-weight: 700; color: var(--accent-gold); font-size: 13px; margin-bottom: 4px;">${s.heading}</div>
      <div style="font-size: 12px; color: var(--text-main); line-height: 1.5;">${s.content}</div>
    </div>
  `).join('');

  const formulasHtml = (m.key_formulas || []).map(f => `
    <div style="font-family: var(--font-mono); font-size: 11px; background: rgba(0,0,0,0.35); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--accent-cyan); margin-bottom: 6px; color: var(--accent-cyan);">
      ${f}
    </div>
  `).join('');

  pane.innerHTML = `
    <div class="encyclopedia-container" style="padding: 10px;">
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <span class="badge badge-purple" style="margin-bottom: 8px;">${m.topic}</span>
        <h2 style="color: var(--accent-gold); margin: 0 0 8px 0; font-size: 20px;">${m.title}</h2>
        <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin: 0;">${m.summary}</p>
      </div>

      <div style="background: rgba(233,190,116,0.08); border: 1px solid rgba(233,190,116,0.3); border-radius: 10px; padding: 12px 14px; margin-bottom: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">✨ Mechanics AI Assistant</div>
        <button class="btn btn-primary btn-sm" onclick="triggerGuideAction('Explain ${m.title} and how it applies to my team compositions.')">
          ✨ Explain for My Characters
        </button>
      </div>

      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">⚙️</span> Mechanics Deep Dive</h3>
        </div>
        ${sectionsHtml}
      </div>

      ${m.key_formulas && m.key_formulas.length ? `
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">📐</span> Mathematical Formulas</h3>
        </div>
        ${formulasHtml}
      </div>` : ''}

      ${m.takeaways && m.takeaways.length ? `
      <div class="char-encyclopedia-section">
        <div class="encyclopedia-section-header">
          <h3 class="encyclopedia-section-title"><span class="sec-icon">💡</span> Practical Takeaways</h3>
        </div>
        <ul style="padding-left: 20px; font-size: 12px; line-height: 1.6; color: var(--text-main);">
          ${m.takeaways.map(t => `<li>${t}</li>`).join('')}
        </ul>
      </div>` : ''}
    </div>
  `;
}

function renderFarmingGuideView(f, pane) {
  const regions = f.regions || {};
  const regionCardsHtml = Object.entries(regions).map(([rName, books]) => `
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px; margin-bottom: 12px;">
      <div style="font-weight: 700; color: var(--accent-gold); font-size: 14px; margin-bottom: 8px; text-transform: capitalize;">${rName}</div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        ${Object.entries(books).map(([bName, data]) => `
          <div style="background: rgba(0,0,0,0.25); border-radius: 6px; padding: 8px 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-weight: 600; color: var(--accent-cyan); font-size: 12px;">Teachings of ${bName}</span>
              <span class="badge badge-secondary" style="font-size: 10px;">${data.days || ''}</span>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
              ${(data.characters || []).map(c => `<span class="badge badge-secondary" style="font-size: 10px;">${c}</span>`).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');

  pane.innerHTML = `
    <div class="encyclopedia-container" style="padding: 10px;">
      <div class="char-encyclopedia-section" style="margin-bottom: 16px;">
        <span class="badge badge-gold" style="margin-bottom: 8px;">Weekly Domain Planner</span>
        <h2 style="color: var(--accent-gold); margin: 0 0 8px 0; font-size: 20px;">Daily Domain Farming Rotations</h2>
        <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin: 0;">Comprehensive schedule of regional talent books and weapon materials available on alternating weekdays.</p>
      </div>

      <div style="background: rgba(233,190,116,0.08); border: 1px solid rgba(233,190,116,0.3); border-radius: 10px; padding: 12px 14px; margin-bottom: 20px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">✨ Farming AI Assistant</div>
        <button class="btn btn-primary btn-sm" onclick="triggerGuideAction('What domain materials should I farm today based on the characters in my account showcase?')">
          ✨ What Should I Farm Today?
        </button>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;">
        ${regionCardsHtml}
      </div>
    </div>
  `;
}

function triggerGuideAction(promptText) {
  if (typeof askAssistant === 'function') {
    askAssistant(promptText);
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



function parseMarkdownToHtml(md) {
  if (!md) return '';
  let html = md;
  
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const sanitizeUrl = (url) => {
    if (!url) return '#';
    const clean = url.trim().replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    if (/^(https?:\/\/|\/|\.\/|#|mailto:)/i.test(clean) && !/javascript:|data:|vbscript:/i.test(clean)) {
      return clean;
    }
    return '#';
  };

  // Parse Images: ![Alt Text](url)
  html = html.replace(/!\[(.*?)\]\((.*?)\)/g, (match, alt, url) => {
    const safeUrl = sanitizeUrl(url);
    const safeAlt = (alt || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    return `<img src="${safeUrl}" alt="${safeAlt}" loading="lazy" style="max-width: 100%; border-radius: 8px; margin: 16px 0; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: block; height: auto;">`;
  });

  // Parse Links: [Link Text](url)
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, (match, text, url) => {
    const safeUrl = sanitizeUrl(url);
    const safeText = (text || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" style="color: var(--cyan-accent); text-decoration: underline;">${safeText}</a>`;
  });

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

/**
 * ====================================================
 * PHASE 14: TEAM BUILDING & SYNERGY WORKBENCH
 * ====================================================
 */
let currentWorkbenchTeam = ['Arlecchino', 'Yelan', 'Bennett', 'Zhongli'];

async function openTeamBuilderWorkbench(focalName = null) {
  const modal = document.getElementById('team-builder-modal');
  if (!modal) return;
  modal.style.display = 'flex';

  if (!dbCache['characters'] || dbCache['characters'].length === 0) {
    try {
      const res = await fetch('/api/data/characters');
      if (res.ok) {
        dbCache['characters'] = await res.json();
      }
    } catch (e) {
      console.warn('Failed to pre-fetch characters for team builder:', e);
    }
  }

  if (focalName) {
    try {
      const recRes = await fetch(`/api/teams/recommend/${encodeURIComponent(focalName)}`);
      if (recRes.ok) {
        const recData = await recRes.json();
        if (recData.teams && recData.teams.length > 0) {
          currentWorkbenchTeam = [...recData.teams[0].members];
        } else {
          currentWorkbenchTeam = [focalName, 'Xingqiu', 'Bennett', 'Kaedehara Kazuha'];
        }
      }
    } catch (e) {
      currentWorkbenchTeam = [focalName, 'Xingqiu', 'Bennett', 'Zhongli'];
    }
  }

  renderTeamWorkbenchSlots();
  await evaluateWorkbenchTeam();
}

function closeTeamBuilderModal() {
  const modal = document.getElementById('team-builder-modal');
  if (modal) modal.style.display = 'none';
}

function renderTeamWorkbenchSlots() {
  const container = document.getElementById('team-workbench-slots');
  if (!container) return;

  const allChars = (dbCache['characters'] || []).map(c => c.name).sort();
  const charOptions = allChars.length > 0 ? allChars : [
    'Arlecchino', 'Bennett', 'Furina', 'Kaedehara Kazuha', 'Neuvillette',
    'Raiden Shogun', 'Xiangling', 'Xingqiu', 'Yelan', 'Zhongli', 'Hu Tao', 'Nahida'
  ];

  container.innerHTML = [0, 1, 2, 3].map(idx => {
    const selectedChar = currentWorkbenchTeam[idx] || '';
    const avatarUrl = getCharacterIconUrl(selectedChar);
    return `
      <div class="team-slot-box">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase;">Slot ${idx + 1}</div>
        <img class="slot-avatar-img" id="slot-img-${idx}" src="${avatarUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" alt="${selectedChar}">
        <select class="slot-char-select" onchange="onWorkbenchSlotChange(${idx}, this.value)">
          <option value="" ${!selectedChar ? 'selected' : ''}>-- Empty --</option>
          ${charOptions.map(name => `<option value="${name}" ${name === selectedChar ? 'selected' : ''}>${name}</option>`).join('')}
        </select>
      </div>
    `;
  }).join('');
}

function onWorkbenchSlotChange(slotIdx, newCharName) {
  if (newCharName) {
    currentWorkbenchTeam[slotIdx] = newCharName;
  } else {
    currentWorkbenchTeam.splice(slotIdx, 1);
  }
  const img = document.getElementById(`slot-img-${slotIdx}`);
  if (img) {
    img.src = getCharacterIconUrl(newCharName);
  }
  evaluateWorkbenchTeam();
}

function resetWorkbenchTeam() {
  currentWorkbenchTeam = ['Arlecchino', 'Yelan', 'Bennett', 'Zhongli'];
  renderTeamWorkbenchSlots();
  evaluateWorkbenchTeam();
}

async function evaluateWorkbenchTeam() {
  const activeTeam = currentWorkbenchTeam.filter(Boolean);
  if (activeTeam.length === 0) return;

  const resultsDiv = document.getElementById('team-eval-results');
  if (resultsDiv) resultsDiv.style.display = 'grid';

  try {
    const res = await fetch('/api/teams/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ characters: activeTeam })
    });

    if (!res.ok) {
      const err = await res.json();
      console.warn('Evaluation failed:', err);
      return;
    }

    const data = await res.json();
    renderWorkbenchEvaluation(data);
  } catch (err) {
    console.error('Error evaluating team:', err);
  }
}

function renderWorkbenchEvaluation(data) {
  const scoreVal = document.getElementById('workbench-score-val');
  const scoreCircle = document.getElementById('workbench-score-circle');
  const verdictTitle = document.getElementById('workbench-verdict-title');
  const verdictDesc = document.getElementById('workbench-verdict-desc');
  const aiBtn = document.getElementById('workbench-ai-review-btn');

  const score = data.synergy_score || 0;
  if (scoreVal) scoreVal.textContent = score;

  const scoreColor = score >= 90 ? '#e9be74' : (score >= 75 ? '#56e2d5' : (score >= 60 ? '#60a5fa' : '#f87171'));
  if (scoreCircle) scoreCircle.style.borderColor = scoreColor;
  if (scoreVal) scoreVal.style.color = scoreColor;

  if (verdictTitle) verdictTitle.textContent = score >= 90 ? '🌟 S-Tier Synergy' : (score >= 75 ? '⚡ A-Tier Synergy' : (score >= 60 ? '🛡️ B-Tier Synergy' : '⚠️ Suboptimal Synergy'));
  if (verdictDesc) verdictDesc.textContent = data.verdict || '';

  if (aiBtn) {
    aiBtn.onclick = () => {
      closeTeamBuilderModal();
      switchTab('chat');
      askAssistant(data.ai_prompt || 'Review my team composition and optimize rotations.');
    };
  }

  // Resonances
  const resList = document.getElementById('workbench-resonances-list');
  if (resList) {
    if (data.active_resonances && data.active_resonances.length > 0) {
      resList.innerHTML = data.active_resonances.map(r => `
        <div style="font-size: 12px; display: flex; align-items: flex-start; gap: 6px;">
          <span style="color: var(--accent-gold); font-weight: 700;">✓ ${r.name}:</span>
          <span style="color: var(--text-muted);">${r.effect}</span>
        </div>
      `).join('');
    } else {
      resList.innerHTML = '<span style="font-size: 12px; color: var(--text-dim);">No elemental resonance active (requires 2 of same element or 4 unique elements).</span>';
    }
  }

  // Reactions
  const reactList = document.getElementById('workbench-reactions-list');
  if (reactList) {
    if (data.elemental_reactions && data.elemental_reactions.length > 0) {
      reactList.innerHTML = data.elemental_reactions.map(r => `
        <div><strong>${r.name}</strong> <span style="color: var(--text-dim);">(${r.type})</span>: ${r.effect}</div>
      `).join('');
    } else {
      reactList.innerHTML = '<span style="color: var(--text-dim);">No elemental reactions enabled.</span>';
    }
  }

  // Warnings
  const warnList = document.getElementById('workbench-warnings-list');
  if (warnList) {
    if (data.warnings && data.warnings.length > 0) {
      warnList.innerHTML = data.warnings.map(w => `<div>⚠️ ${w}</div>`).join('');
    } else {
      warnList.innerHTML = '<div style="color: #4ade80;">✓ Role distribution is balanced. No sustainability risks detected.</div>';
    }
  }

  // Rotation Steps
  const rotList = document.getElementById('workbench-rotation-steps');
  if (rotList) {
    if (data.rotation_flow && data.rotation_flow.length > 0) {
      rotList.innerHTML = data.rotation_flow.map(s => `
        <div style="font-size: 12px; color: var(--text-bright); background: rgba(0,0,0,0.25); padding: 6px 10px; border-radius: 4px;">
          ${s}
        </div>
      `).join('');
    } else {
      rotList.innerHTML = '<span style="color: var(--text-dim);">Add characters to generate combat rotation.</span>';
    }
  }
}

/**
 * ====================================================
 * PHASE 15: ARTIFACT OPTIMIZER WORKBENCH
 * ====================================================
 */
function openArtifactOptimizerWorkbench(charName = 'Arlecchino') {
  const modal = document.getElementById('artifact-optimizer-modal');
  if (!modal) return;
  modal.style.display = 'flex';

  const charInput = document.getElementById('optimizer-char-input');
  if (charInput) charInput.value = charName;

  runArtifactOptimizer();
}

function closeArtifactOptimizerModal() {
  const modal = document.getElementById('artifact-optimizer-modal');
  if (modal) modal.style.display = 'none';
}

async function runArtifactOptimizer() {
  const charName = document.getElementById('optimizer-char-input')?.value?.trim() || 'Arlecchino';
  const minEr = parseFloat(document.getElementById('optimizer-min-er-input')?.value || 0);
  const reqSet = document.getElementById('optimizer-set-select')?.value || null;
  const container = document.getElementById('optimizer-results-container');

  if (!container) return;
  container.innerHTML = `
    <div style="text-align: center; padding: 40px;">
      <div class="skeleton" style="width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 16px;"></div>
      <div style="font-size: 14px; color: var(--accent-gold); font-weight: 700;">Evaluating Account Artifacts &amp; Combinations...</div>
      <p style="font-size: 12px; color: var(--text-muted); margin-top: 6px;">Pruning search space across 5 artifact slots...</p>
    </div>
  `;

  try {
    const res = await fetch('/api/optimizer/character', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        character_name: charName,
        min_er: minEr,
        required_set: reqSet,
        max_results: 3
      })
    });

    if (!res.ok) {
      const err = await res.json();
      container.innerHTML = `<div class="alert-banner alert-error" style="display:flex;"><span>⚠️ ${err.detail || 'Optimizer calculation failed.'}</span></div>`;
      return;
    }

    const data = await res.json();
    renderArtifactOptimizerResults(data);
  } catch (err) {
    container.innerHTML = `<div class="alert-banner alert-error" style="display:flex;"><span>⚠️ Connection error: ${err.message}</span></div>`;
  }
}

function renderArtifactOptimizerResults(data) {
  const container = document.getElementById('optimizer-results-container');
  if (!container) return;

  const candidates = data.optimal_candidates || [];
  if (candidates.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <h3>No Valid Loadout Satisfying Constraints</h3>
        <p>No 5-piece artifact combination met the minimum Energy Recharge (${data.min_er || 0}%) or required 4-piece set.</p>
      </div>
    `;
    return;
  }

  const deltaHtml = data.stat_delta?.delta_cv !== undefined ? `
    <div style="display: flex; gap: 14px; align-items: center; background: rgba(0,0,0,0.3); border: 1px solid rgba(233,190,116,0.25); border-radius: var(--radius-sm); padding: 10px 14px; margin-bottom: 16px;">
      <div>
        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">CV Delta vs Current:</span>
        <strong style="color: ${data.stat_delta.delta_cv >= 0 ? '#4ade80' : '#f87171'}; font-size: 14px; margin-left: 6px;">
          ${data.stat_delta.delta_cv >= 0 ? '+' : ''}${data.stat_delta.delta_cv} CV
        </strong>
      </div>
      <div>
        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Roll Value Delta:</span>
        <strong style="color: ${data.stat_delta.delta_weighted_rv >= 0 ? '#4ade80' : '#f87171'}; font-size: 14px; margin-left: 6px;">
          ${data.stat_delta.delta_weighted_rv >= 0 ? '+' : ''}${data.stat_delta.delta_weighted_rv}% RV
        </strong>
      </div>
      <div style="margin-left: auto;">
        <span class="badge ${data.stat_delta.delta_cv >= 0 ? 'badge-gold' : 'badge-secondary'}">${data.stat_delta.verdict || 'Evaluated'}</span>
      </div>
    </div>
  ` : '';

  const cardsHtml = candidates.map((cand, idx) => {
    const isTop = idx === 0;
    const piecesHtml = (cand.artifacts || []).map(art => `
      <div style="background: rgba(14,20,32,0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 10px; display: flex; flex-direction: column; gap: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 10px; font-weight: 700; color: var(--accent-gold); text-transform: uppercase;">${art.slot}</span>
          <span class="badge ${art.cv >= 30 ? 'badge-gold' : 'badge-secondary'}" style="font-size: 10px; padding: 1px 4px;">${art.cv} CV</span>
        </div>
        <div style="font-size: 12px; font-weight: 600; color: var(--text-bright);">${art.set_name}</div>
        <div style="font-size: 11px; color: var(--text-muted);">${art.main_stat} (+${art.level})</div>
        <div style="font-size: 10px; color: var(--accent-cyan); margin-top: auto;">📍 ${art.location}</div>
      </div>
    `).join('');

    return `
      <div class="card card-glass" style="margin-bottom: 16px; border: 1px solid ${isTop ? 'rgba(233,190,116,0.45)' : 'rgba(255,255,255,0.08)'}; padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span class="badge ${isTop ? 'badge-gold' : 'badge-secondary'}" style="font-weight: 700;">#${idx + 1} Candidate Loadout</span>
            <span style="font-size: 13px; font-weight: 700; color: var(--text-bright);">${(cand.active_sets || []).join(' + ') || 'Rainbow Set'}</span>
          </div>
          <div style="display: flex; gap: 12px; align-items: center;">
            <span style="font-size: 12px;">Total CV: <strong style="color: var(--accent-gold);">${cand.total_crit_value}</strong></span>
            <span style="font-size: 12px;">Weighted RV: <strong style="color: #56e2d5;">${cand.total_weighted_rv}%</strong></span>
            <span style="font-size: 12px;">ER: <strong style="color: #60a5fa;">${cand.total_er_pct}%</strong></span>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 12px;">
          ${piecesHtml}
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 8px;">
          <button class="btn btn-secondary btn-sm" onclick="askAssistant('How does the #${idx + 1} artifact loadout with ${(cand.active_sets || []).join(' + ')} compare to standard build benchmarks for ${data.character}?')">
            ✨ Ask AI Analysis
          </button>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    ${deltaHtml}
    ${cardsHtml}
    ${data.notice ? `<div style="font-size: 11px; color: var(--text-dim); text-align: center; margin-top: 10px;">ℹ️ ${data.notice}</div>` : ''}
  `;
}

/**
 * ====================================================
 * PHASE 16: COMBAT SIMULATION & GCSIM EXPORTER
 * ====================================================
 */
async function runWorkbenchCombatSimulation() {
  const activeTeam = currentWorkbenchTeam.filter(Boolean);
  if (activeTeam.length === 0) return;

  const card = document.getElementById('workbench-simulation-card');
  const content = document.getElementById('workbench-simulation-content');
  if (!card || !content) return;

  card.style.display = 'block';
  content.innerHTML = `
    <div style="text-align: center; padding: 16px;">
      <div class="skeleton" style="height: 20px; width: 60%; margin: 0 auto 8px;"></div>
      <div style="font-size: 11px; color: var(--text-muted);">Simulating second-by-second rotation damage &amp; motion values...</div>
    </div>
  `;

  try {
    const res = await fetch('/api/simulation/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team: activeTeam,
        duration_sec: 20,
        enemy_count: 1,
        enemy_res_pct: 10.0
      })
    });

    if (!res.ok) {
      const err = await res.json();
      content.innerHTML = `<div style="font-size: 12px; color: #f87171;">⚠️ ${err.detail || 'Simulation execution failed.'}</div>`;
      return;
    }

    const data = await res.json();
    renderSimulationCard(data);
  } catch (err) {
    content.innerHTML = `<div style="font-size: 12px; color: #f87171;">⚠️ Connection error: ${err.message}</div>`;
  }
}

function renderSimulationCard(data) {
  const content = document.getElementById('workbench-simulation-content');
  if (!content) return;

  const dps = Math.round(data.summary_metrics?.team_dps || 0).toLocaleString();
  const total = Math.round(data.summary_metrics?.total_damage || 0).toLocaleString();
  const chars = data.character_breakdown || [];

  const charBars = chars.map(c => `
    <div style="margin-bottom: 6px;">
      <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px;">
        <span style="font-weight: 600; color: var(--text-bright);">${c.character}</span>
        <span style="color: var(--text-muted);">${c.damage_share_pct}% (${Math.round(c.dps).toLocaleString()} DPS)</span>
      </div>
      <div style="height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;">
        <div style="height: 100%; width: ${c.damage_share_pct}%; background: var(--accent-gold); border-radius: 3px;"></div>
      </div>
    </div>
  `).join('');

  content.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
      <div>
        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Team DPS:</span>
        <span style="font-size: 20px; font-weight: 700; color: var(--accent-gold); margin-left: 6px;">${dps}</span>
      </div>
      <div style="font-size: 11px; color: var(--text-dim);">
        Total Damage (20s): <strong style="color: var(--text-bright);">${total}</strong>
      </div>
    </div>
    <div style="margin-bottom: 10px;">
      <div style="font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px;">Damage Share per Character</div>
      ${charBars}
    </div>
    <div style="font-size: 10px; color: var(--text-dim); line-height: 1.4; border-top: 1px dashed rgba(255,255,255,0.08); padding-top: 6px;">
      Engine: ${data.engine} • Lv 100 Dummy (10% RES)
    </div>
  `;
}

async function exportWorkbenchGcsimConfig() {
  const activeTeam = currentWorkbenchTeam.filter(Boolean);
  if (activeTeam.length === 0) return;

  try {
    const res = await fetch('/api/simulation/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team: activeTeam,
        duration_sec: 90,
        iterations: 1000
      })
    });

    if (res.ok) {
      const data = await res.json();
      await navigator.clipboard.writeText(data.gcsim_config);
      alert('gcsim configuration script copied to clipboard!');
    }
  } catch (e) {
    console.error('Failed to export gcsim config:', e);
  }
}

/**
 * ====================================================
 * PHASE 17: SPIRAL ABYSS TRACKER MODAL
 * ====================================================
 */
let currentAbyssData = null;
let currentAbyssChamber = 1;

async function openAbyssTrackerModal() {
  const modal = document.getElementById('abyss-tracker-modal');
  if (!modal) return;
  modal.style.display = 'flex';

  try {
    const [curRes, recRes] = await Promise.all([
      fetch('/api/abyss/current'),
      fetch('/api/abyss/recommendations')
    ]);

    if (curRes.ok) {
      currentAbyssData = await curRes.json();
      renderAbyssHeader(currentAbyssData);
      renderAbyssChamber(currentAbyssChamber);
    }

    if (recRes.ok) {
      const recData = await recRes.json();
      renderAbyssTeams(recData);
    }
  } catch (err) {
    console.error('Failed to load Abyss data:', err);
  }
}

function closeAbyssTrackerModal() {
  const modal = document.getElementById('abyss-tracker-modal');
  if (modal) modal.style.display = 'none';
}

function renderAbyssHeader(data) {
  const title = document.getElementById('abyss-blessing-title');
  const desc = document.getElementById('abyss-blessing-desc');
  const badge = document.getElementById('abyss-cycle-badge');

  if (title) title.textContent = data.blessing?.name || 'Blessing of the Abyssal Moon';
  if (desc) desc.textContent = data.blessing?.effect || '';
  if (badge) badge.textContent = `Floor ${data.floor} • ${data.period || 'Active'}`;
}

function switchAbyssChamber(chamberNum) {
  currentAbyssChamber = chamberNum;
  document.querySelectorAll('#abyss-chamber-tabs .sub-tab-btn').forEach(btn => {
    btn.classList.toggle('active', parseInt(btn.dataset.chamber) === chamberNum);
  });
  renderAbyssChamber(chamberNum);
}

function renderAbyssChamber(chamberNum) {
  const container = document.getElementById('abyss-chamber-content');
  if (!container || !currentAbyssData) return;

  const chamber = currentAbyssData.chambers?.find(c => c.chamber === chamberNum);
  if (!chamber) return;

  const renderHalf = (halfData, halfTitle) => {
    const enemiesHtml = (halfData.enemies || []).map(e => `
      <div style="background: rgba(14,20,32,0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 12px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <span style="font-weight: 700; font-size: 13px; color: var(--text-bright);">${e.name}</span>
          <span class="badge badge-secondary" style="font-size: 10px;">${(e.hp / 1000000).toFixed(2)}M HP</span>
        </div>
        <div style="font-size: 11px; color: var(--accent-gold); margin-bottom: 4px;">🎯 Weakness: ${e.weakness}</div>
        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">🛡️ Res: ${e.resistances}</div>
        <div style="font-size: 11px; color: #5eead4; line-height: 1.4;">💡 Tip: ${e.advisory}</div>
      </div>
    `).join('');

    return `
      <div style="background: rgba(0,0,0,0.25); border-radius: var(--radius-sm); padding: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <h4 style="font-size: 13px; font-weight: 700; color: var(--accent-gold); margin: 0;">${halfTitle}</h4>
          <span style="font-size: 11px; color: var(--text-dim);">${halfData.enemy_count} Targets</span>
        </div>
        ${enemiesHtml}
      </div>
    `;
  };

  container.innerHTML = `
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
      ${renderHalf(chamber.first_half, 'First Half')}
      ${renderHalf(chamber.second_half, 'Second Half')}
    </div>
  `;
}

function renderAbyssTeams(recData) {
  const container = document.getElementById('abyss-teams-container');
  if (!container) return;

  const renderSideList = (teams, sideTitle) => {
    const listHtml = (teams || []).map(t => {
      const avatarsHtml = (t.members || []).map(m => {
        const iconUrl = getCharacterIconUrl(m);
        return `
          <div style="text-align: center;">
            <img src="${iconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 36px; height: 36px; border-radius: 50%; border: 1.5px solid var(--accent-gold); object-fit: cover;">
            <div style="font-size: 9px; color: var(--text-muted); margin-top: 2px;">${m.split(' ')[0]}</div>
          </div>
        `;
      }).join('');

      return `
        <div style="background: rgba(14,20,32,0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 10px; margin-bottom: 10px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-weight: 700; font-size: 12px; color: var(--text-bright);">${t.name}</span>
            <span class="badge ${t.fully_owned ? 'badge-gold' : 'badge-secondary'}" style="font-size: 10px;">
              ${t.fully_owned ? '✓ Owned' : `${t.owned_count}/4 Owned`}
            </span>
          </div>
          <div style="display: flex; gap: 10px; margin-bottom: 6px;">
            ${avatarsHtml}
          </div>
          <div style="font-size: 11px; color: var(--text-muted); line-height: 1.4;">${t.rationale}</div>
        </div>
      `;
    }).join('');

    return `
      <div>
        <div style="font-size: 12px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 8px;">${sideTitle}</div>
        ${listHtml}
      </div>
    `;
  };

  container.innerHTML = `
    ${renderSideList(recData.side_1_recommendations, 'Side 1 Recommendations')}
    ${renderSideList(recData.side_2_recommendations, 'Side 2 Recommendations')}
  `;
}




