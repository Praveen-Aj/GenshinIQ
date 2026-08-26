/**
 * GenshinIQ Frontend Application Controller
 * Handles Tab Navigation, Health Diagnostics, Enka Showcase Import, and Game Database Explorer
 */

function getCharacterIconUrl(name) {
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
    'skirk': 'UI_AvatarIcon_Skirk',
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
  };
  const codeName = CHARACTER_ICONS[name.toLowerCase()] || `UI_AvatarIcon_${name}`;
  return `https://enka.network/ui/${codeName}.png`;
}

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
      chip.innerHTML = `
        <img class="char-chip-avatar" src="${iconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" alt="${char.name}" style="width: 36px; height: 36px; border-radius: 50%; border: 1px solid var(--accent-gold); background: rgba(0,0,0,0.3); object-fit: cover;">
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
  } else {
    if (selectorContainer) selectorContainer.style.display = 'none';
    if (activeCharView) activeCharView.style.display = 'none';
    showAccountError('No character showcase details available for this account.');
  }
}

/**
 * Render Selected Character Build
 */
function renderActiveCharacter(char) {
  if (!char) return;

  const largeAvatar = document.getElementById('char-large-avatar');
  if (largeAvatar) {
    largeAvatar.src = getCharacterIconUrl(char.name);
  }

  document.getElementById('char-name').textContent = char.name;
  const elemBadge = document.getElementById('char-element');
  elemBadge.textContent = char.element;
  elemBadge.className = `elem-badge elem-${char.element.toLowerCase()}`;

  document.getElementById('char-level').textContent = `Lv. ${char.level}/90`;
  document.getElementById('char-constellation').textContent = `C${char.constellation}`;
  document.getElementById('char-friendship').textContent = `♥ ${char.fetter_level}`;

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
    weaponCard.innerHTML = `
      <div style="display: flex; gap: 12px; align-items: center;">
        <img class="weapon-icon" src="${weaponIconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_EquipIcon_Sword_Zephyrus.png'" alt="${w.name}" style="width: 44px; height: 44px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); object-fit: contain;">
        <div style="flex-grow: 1;">
          <div class="weapon-title-row">
            <span class="weapon-name" style="font-weight: 600; color: var(--gold-accent);">${w.name}</span>
            <span class="weapon-refinement">R${w.refinement}</span>
          </div>
          <div class="weapon-stats-row" style="margin-top: 4px; font-size: 0.85em; opacity: 0.8; display: flex; gap: 12px;">
            <span>Lv. ${w.level}/90</span>
            ${w.base_atk ? `<span>Base ATK: <strong>${Math.round(w.base_atk)}</strong></span>` : ''}
            ${w.sub_stat ? `<span>${w.sub_stat.name}: <strong class="stat-highlight">${w.sub_stat.formatted}</strong></span>` : ''}
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
            <span class="substat-val ${isCrit ? 'substat-crit' : ''}">+${sub.formatted}</span>
          </div>
        `;
      }).join('');

      const relicIconUrl = art.icon ? `https://enka.network/ui/${art.icon}.png` : 'https://enka.network/ui/UI_RelicIcon_15001_4.png';

      card.innerHTML = `
        <div style="display: flex; gap: 12px; align-items: flex-start; flex-grow: 1;">
          <img class="art-icon" src="${relicIconUrl}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_RelicIcon_15001_4.png'" alt="${art.set_name}" style="width: 40px; height: 40px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); object-fit: contain;">
          <div class="art-main-col" style="flex-grow: 1;">
            <div class="art-slot-header">
              <span class="art-slot-name">${slotLabels[slot]}</span>
              <span class="art-lvl-badge">+${art.level}</span>
            </div>
            <div class="art-set-name" style="font-weight: 500; font-size: 0.9em; margin-top: 2px;">${art.set_name || art.name}</div>
            <div class="art-main-stat" style="margin-top: 6px; font-size: 0.85em;">
              <div class="art-main-prop" style="opacity: 0.7;">${art.main_stat.name}</div>
              <div class="art-main-val" style="font-weight: 600; color: var(--gold-accent);">${art.main_stat.formatted}</div>
            </div>
          </div>
        </div>
        <div class="art-substats-grid">
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
  const categoryBtns = document.querySelectorAll('.sub-tab-btn');
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
  grid.innerHTML = '<div class="text-muted" style="padding: 20px;">Loading database...</div>';

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
    card.className = `db-item-card ${selectedDbItem?.id === item.id ? 'active' : ''}`;

    if (currentDbCategory === 'characters') {
      const elemClass = `elem-${item.element.toLowerCase()}`;
      const charIcon = `https://enka.network/ui/${item.icon || `UI_AvatarIcon_${item.name}`}.png`;
      card.innerHTML = `
        <div style="display: flex; gap: 12px; align-items: center; flex-grow: 1;">
          <img class="db-card-avatar" src="${charIcon}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 36px; height: 36px; border-radius: 50%; border: 1.5px solid var(--accent-gold); background: rgba(0,0,0,0.2); object-fit: cover;">
          <div>
            <div class="db-item-title">${item.name}</div>
            <div class="db-item-sub">${item.rarity}★ • ${item.weapon_type} • ${item.region || 'Teyvat'}</div>
          </div>
        </div>
        <span class="elem-badge ${elemClass}">${item.element}</span>
      `;
    } else if (currentDbCategory === 'weapons') {
      const weaponIcon = `https://enka.network/ui/${item.icon || `UI_EquipIcon_Sword_Zephyrus`}.png`;
      card.innerHTML = `
        <div style="display: flex; gap: 12px; align-items: center; flex-grow: 1;">
          <img class="db-card-weapon" src="${weaponIcon}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_EquipIcon_Sword_Zephyrus.png'" style="width: 36px; height: 36px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); object-fit: contain;">
          <div>
            <div class="db-item-title">${item.name}</div>
            <div class="db-item-sub">${item.rarity}★ ${item.weapon_type} • Base ATK ${Math.round(item.base_atk_lvl90)}</div>
          </div>
        </div>
        <span class="badge badge-gold">${item.sub_stat_type || 'ATK'}</span>
      `;
    } else if (currentDbCategory === 'artifacts') {
      const artIcon = `https://enka.network/ui/${item.icon || `UI_RelicIcon_15001_4`}.png`;
      card.innerHTML = `
        <div style="display: flex; gap: 12px; align-items: center; flex-grow: 1;">
          <img class="db-card-artifact" src="${artIcon}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_RelicIcon_15001_4.png'" style="width: 36px; height: 36px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); object-fit: contain;">
          <div>
            <div class="db-item-title">${item.name}</div>
            <div class="db-item-sub">Artifact Set • ${item.rarities.join('/')}★</div>
          </div>
        </div>
        <span class="badge badge-cyan">5★ Set</span>
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
    const talentsHtml = (item.talents || []).map((t) => `
      <div class="accordion-item">
        <div class="accordion-title">
          <span>${t.name}</span>
          <span class="badge badge-secondary" style="font-size: 11px;">${t.unlock}</span>
        </div>
        <div class="accordion-desc">${t.description}</div>
      </div>
    `).join('');

    const constsHtml = (item.constellations || []).map((c) => `
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
      <div class="detail-header" style="display: flex; gap: 16px; align-items: center; margin-bottom: 16px;">
        <img class="db-large-avatar" src="${charIcon}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 56px; height: 56px; border-radius: 50%; border: 2px solid var(--accent-gold); background: rgba(0,0,0,0.3); object-fit: cover;">
        <div>
          <h2 style="margin: 0; color: var(--gold-accent);">${item.name}</h2>
          <div class="char-sub-row" style="margin-top: 6px;">
            <span class="elem-badge ${elemClass}">${item.element}</span>
            <span class="badge badge-gold">${item.rarity}★ ${item.weapon_type}</span>
            <span class="badge badge-secondary">${item.region || 'Teyvat'}</span>
          </div>
        </div>
      </div>
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
      <div class="constellations-accordion">${constsHtml}</div>

      <div class="section-title">Required Materials</div>
      <div style="margin-bottom: 8px; font-size: 12px; color: var(--text-dim);">Character Ascension</div>
      <div class="materials-tag-cloud">${ascMatHtml}</div>
      <div style="margin: 12px 0 8px; font-size: 12px; color: var(--text-dim);">Talent Level Up</div>
      <div class="materials-tag-cloud">${talMatHtml}</div>
    `;
  } else if (category === 'weapons') {
    const refHtml = (item.refinements || []).map((r, i) => `
      <div class="accordion-item">
        <div class="accordion-title">Rank ${i + 1}</div>
        <div class="accordion-desc">${r}</div>
      </div>
    `).join('');

    const weaponIcon = `https://enka.network/ui/${item.icon || `UI_EquipIcon_Sword_Zephyrus`}.png`;

    pane.innerHTML = `
      <div class="detail-header" style="display: flex; gap: 16px; align-items: center; margin-bottom: 20px;">
        <img class="db-large-weapon" src="${weaponIcon}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_EquipIcon_Sword_Zephyrus.png'" style="width: 56px; height: 56px; border-radius: 8px; border: 1.5px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.3); object-fit: contain;">
        <div>
          <h2 style="margin: 0; color: var(--gold-accent);">${item.name}</h2>
          <div class="char-sub-row" style="margin-top: 6px;">
            <span class="badge badge-gold">${item.rarity}★ ${item.weapon_type}</span>
          </div>
        </div>
      </div>

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
      <div class="detail-header" style="display: flex; gap: 16px; align-items: center; margin-bottom: 20px;">
        <img class="db-large-artifact" src="${artIcon}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_RelicIcon_15001_4.png'" style="width: 56px; height: 56px; border-radius: 8px; border: 1.5px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.3); object-fit: contain;">
        <div>
          <h2 style="margin: 0; color: var(--gold-accent);">${item.name}</h2>
          <div class="char-sub-row" style="margin-top: 6px;">
            <span class="badge badge-cyan">5★ Artifact Set</span>
          </div>
        </div>
      </div>

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

  statusPill.className = 'status-pill status-loading';
  statusText.textContent = 'Checking API...';

  try {
    const response = await fetch('/api/health');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();

    statusPill.className = 'status-pill status-online';
    statusText.textContent = 'API Online';

    if (diagStatus) diagStatus.textContent = 'Healthy (HTTP 200)';
    if (diagAppName) diagAppName.textContent = data.app_name || 'GenshinIQ';
    if (diagVersion) diagVersion.textContent = `v${data.version || '0.1.0'}`;
    if (diagEnv) diagEnv.textContent = (data.environment || 'development').toUpperCase();
    if (diagTimestamp) diagTimestamp.textContent = data.timestamp || new Date().toISOString();
    if (diagEnkaBase) diagEnkaBase.textContent = data.enka_api_base || '—';
    if (rawPayload) rawPayload.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    statusPill.className = 'status-pill status-offline';
    statusText.textContent = 'API Offline';
    if (diagStatus) diagStatus.textContent = 'Connection Failed';
    if (rawPayload) rawPayload.textContent = `Error: ${err.message}`;
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
}

async function loadKnowledgeBase() {
  const grid = document.getElementById('kb-items-grid');
  if (!grid) return;

  grid.innerHTML = '<div class="loading-spinner">Loading guides...</div>';

  try {
    const response = await fetch('/api/knowledge/documents');
    if (!response.ok) throw new Error('Failed to load guides');
    kbCache = await response.json();
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

function renderKnowledgeGrid(docsToRender = null) {
  const grid = document.getElementById('kb-items-grid');
  if (!grid) return;

  const items = docsToRender || kbCache;
  const filtered = docsToRender ? items : items.filter((doc) => {
    if (currentKbTopic === 'all') return true;
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
    
    const badgeClass = doc.metadata.source_type === 'AUTHORITATIVE' ? 'badge-gold' : 'badge-cyan';
    const characterTag = doc.metadata.character ? `<span class="badge badge-purple" style="margin-left: 6px;">${doc.metadata.character}</span>` : '';

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
            <span class="badge ${badgeClass}">${doc.metadata.source_type}</span>
            ${characterTag}
            <span class="badge badge-gray" style="margin-left: auto;">v${doc.metadata.game_version}</span>
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
    const badgeClass = fullDoc.metadata.source_type === 'AUTHORITATIVE' ? 'badge-gold' : 'badge-cyan';
    const characterTag = fullDoc.metadata.character ? `<span class="badge badge-purple" style="margin-left: 6px; font-size: 0.8em; padding: 4px 8px;">${fullDoc.metadata.character}</span>` : '';

    pane.innerHTML = `
      <div class="db-detail-header" style="margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 16px;">
        <div class="db-item-meta" style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px;">
          <span class="badge ${badgeClass}" style="font-size: 0.8em; padding: 4px 8px;">${fullDoc.metadata.source_type}</span>
          ${characterTag}
          <span class="badge badge-gray" style="margin-left: auto; font-size: 0.8em; padding: 4px 8px;">v${fullDoc.metadata.game_version}</span>
        </div>
        <div style="display: flex; gap: 16px; align-items: center;">
          ${fullDoc.metadata.character ? 
            `<img src="${getCharacterIconUrl(fullDoc.metadata.character)}" onerror="this.onerror=null; this.src='https://enka.network/ui/UI_AvatarIcon_NPC.png'" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid var(--accent-gold); background: rgba(0,0,0,0.3); object-fit: cover;">` :
            `<div style="width: 48px; height: 48px; border-radius: 50%; border: 1.5px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 20px;">⚙️</div>`
          }
          <h2 style="margin: 0; color: var(--gold-accent); font-size: 1.5em; font-weight: 700; line-height: 1.3;">${fullDoc.title}</h2>
        </div>
        <div style="font-size: 0.85em; opacity: 0.7; display: flex; flex-wrap: wrap; gap: 12px; margin-top: 14px;">
          <span><strong>Published:</strong> ${new Date(fullDoc.metadata.published_at).toLocaleDateString()}</span>
          <span>•</span>
          <span><strong>Last Updated:</strong> ${new Date(fullDoc.metadata.updated_at).toLocaleDateString()}</span>
        </div>
        <div style="font-size: 0.85em; opacity: 0.7; margin-top: 6px;">
          <strong>Canonical URL:</strong> <a href="${fullDoc.metadata.source_url}" target="_blank" style="color: var(--cyan-accent); text-decoration: underline; word-break: break-all;">${fullDoc.metadata.source_url}</a>
        </div>
      </div>
      <div class="kb-article-body markdown-body" style="line-height: 1.6; font-size: 0.95em; color: rgba(255,255,255,0.9);">
        ${contentHtml}
      </div>
    `;
  } catch (err) {
    pane.innerHTML = `<div class="text-error">Error loading article details: ${err.message}</div>`;
  }
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
    appendMessageBubble('model', data.content, data.citations);
    
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

function appendMessageBubble(role, content, citations = []) {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;
  
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}-message`;
  
  const avatarDiv = document.createElement('div');
  avatarDiv.className = 'message-avatar';
  avatarDiv.innerHTML = role === 'user' ? '👤' : (role === 'system' ? '⚠️' : '✨');
  
  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'message-bubble';
  
  const htmlContent = parseMarkdownToHtml(content);
  bubbleDiv.innerHTML = htmlContent;
  
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
    summary.innerHTML = `Sources Cited (${citations.length})`;
    
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
      
      const sourceLink = `<a href="${c.source_url}" target="_blank" style="color: var(--cyan-accent); font-weight: 500; text-decoration: underline;">${c.source_name}</a>`;
      const charTag = c.character ? ` <span style="background: rgba(255, 215, 0, 0.15); color: var(--gold-accent); padding: 1px 4px; border-radius: 4px; font-size: 10px;">${c.character}</span>` : '';
      const verTag = c.game_version ? ` <span style="background: rgba(255, 255, 255, 0.1); color: var(--text-muted); padding: 1px 4px; border-radius: 4px; font-size: 10px;">v${c.game_version}</span>` : '';
      
      li.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px;">
          <strong>${c.topic || 'General Reference'}</strong>
          <div>${charTag}${verTag}</div>
        </div>
        <div style="color: var(--text-muted); font-style: italic; margin-bottom: 4px;">"${c.snippet}"</div>
        <div style="font-size: 11px;">Source: ${sourceLink}</div>
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
  avatarDiv.innerHTML = '✨';
  
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


