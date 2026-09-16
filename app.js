/* The Many Calcuttas — an era-layered map of Kolkata's heritage.
 *
 * Colour encodes whichever grouping is active (era or type); the glyph inside
 * the pin always says what the building actually is.
 */

const CENTRE = [22.5726, 88.3639];      // Lal Dighi, where the city started

const ERA_COLOURS = {
  'Early Settlement':     '#c0392b',
  'Company Raj':          '#e8833a',
  'Imperial Capital':     '#4aa96c',
  'Late Raj & Art Deco':  '#3d9ae0',
  'Independent India':    '#a370d8',
  'Date Undetermined':    '#8d8d95',
};

const CATEGORY_COLOURS = {
  'Rajbari, Mansion & House':     '#c9453b',
  'Temple & Thakurbari':          '#e8833a',
  'Memorial, Statue & Gate':      '#cf9a2e',
  'Other Faiths':                 '#d8c23a',
  'Commerce, Market & Hotel':     '#9cbf3f',
  'Club, Park & Sport':           '#5cb85c',
  'Mosque & Imambara':            '#2f9e6e',
  'Hospital & Medical':           '#34bfa4',
  'Ghat & Riverfront':            '#2fb4c4',
  'Church & Chapel':              '#4a8fe0',
  'Government, Court & Fort':     '#5a6fd4',
  'Museum, Library & Archive':    '#8f6bd8',
  'Theatre & Cinema':             '#b45cd6',
  'School, College & University': '#e0589e',
  'Cemetery, Tomb & Crematorium': '#9b9088',
  'Bridge, Tower & Public Works': '#6f7c8c',
};

// 24×24 glyphs, filled with currentColor.
const GLYPHS = {
  'Temple & Thakurbari':          '<path d="M12 2l5 7H7l5-7zM6 10h12v2.5H6zM7.5 14h9v8h-3v-4.5h-3V22h-3z"/>',
  'Mosque & Imambara':            '<path d="M12 2.5c-3.2 2.2-5 4.6-5 7.3V11h10V9.8c0-2.7-1.8-5.1-5-7.3zM6 12.5h12V22h-3.2v-3.6a2.8 2.8 0 0 0-5.6 0V22H6z"/>',
  'Church & Chapel':              '<path d="M10.8 2h2.4v3.2H16v2.4h-2.8V22h-2.4V7.6H8V5.2h2.8z"/>',
  'Other Faiths':                 '<path d="M12 2l2.5 6.2L21 8.8l-4.9 4.3 1.5 6.5L12 16.2 6.4 19.6l1.5-6.5L3 8.8l6.5-.6z"/>',
  'Ghat & Riverfront':            '<path d="M2 19.5h20V22H2zM5 15.8h17v2.9H5zM9 12.1h13V15H9zM13 8.4h9v2.9h-9z"/>',
  'Cemetery, Tomb & Crematorium': '<path d="M12 2a5 5 0 0 0-5 5v15h10V7a5 5 0 0 0-5-5zm-1.1 3.6h2.2v2.1h2.1V10h-2.1v4.3h-2.2V10H8.8V7.7h2.1z"/>',
  'Theatre & Cinema':             '<path fill-rule="evenodd" d="M2.6 4.6h18.8a1 1 0 0 1 1 1v12.8a1 1 0 0 1-1 1H2.6a1 1 0 0 1-1-1V5.6a1 1 0 0 1 1-1zM9.6 8v8l6.4-4z"/>',
  'Club, Park & Sport':           '<path d="M12 1.8l4.3 6.4h-2.5l3.4 5h-2.6l3.6 5.2H13V22h-2v-3.6H5.8l3.6-5.2H6.8l3.4-5H7.7z"/>',
  'Hospital & Medical':           '<path d="M9.8 2h4.4v5.8H20v4.4h-5.8V22H9.8V12.2H4V7.8h5.8z"/>',
  'Museum, Library & Archive':    '<path d="M12 2l10 5.2v2.2H2V7.2zM3.8 11.2h2.4v7.4H3.8zM9 11.2h2.4v7.4H9zM13.8 11.2h2.4v7.4h-2.4zM18.6 11.2H21v7.4h-2.4zM2 20h20v2H2z"/>',
  'School, College & University': '<path d="M12 6.3C9.6 4.3 6.6 3.6 3 4v14.2c3.6-.4 6.6.3 9 2.2V6.3zm1 0v14.1c2.4-1.9 5.4-2.6 9-2.2V4c-3.6-.4-6.6.3-9 2.3z"/>',
  'Government, Court & Fort':     '<path fill-rule="evenodd" d="M3 5.4h3.2v2.2h3.2V5.4h3.2v2.2h3.2V5.4H21V22H3zm7 9h4V22h-4z"/>',
  'Memorial, Statue & Gate':      '<path d="M10.9 2h2.2l2.2 6.6V18H8.7V8.6zM6.9 19.4h10.2V22H6.9z"/>',
  'Commerce, Market & Hotel':     '<path fill-rule="evenodd" d="M2 3.4h20l-1.6 5.4H3.6zM4.2 10.6h15.6V22H4.2zm4.6 3v5.6h6.4v-5.6z"/>',
  'Bridge, Tower & Public Works': '<path fill-rule="evenodd" d="M1.6 16.4h2.2V6.2H6v10.2h12V6.2h2.2v10.2h2.2v2.4H1.6zm6.6 0h7.6v-1.2a3.8 3.8 0 0 0-7.6 0z"/>',
  'Rajbari, Mansion & House':     '<path d="M12 2.6L21.4 10v12h-6.2v-6.8H8.8V22H2.6V10z"/>',
};

const FALLBACK_GLYPH = '<circle cx="12" cy="12" r="5"/>';

/* ─────────────────────────── state ─────────────────────────── */

const state = {
  monuments: [],
  eras: [],
  groupBy: 'era',
  layers: new Map(),        // group name -> { cluster, colour, visible, monuments }
  markers: new Map(),       // monument id -> { marker, group }
  fuse: null,
  selected: null,
  pendingMoveEnd: null,
};

const map = L.map('map', { zoomControl: true, minZoom: 9 }).setView(CENTRE, 12);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  maxZoom: 19,
}).addTo(map);

/* ───────────────────────── rendering ───────────────────────── */

function colourFor(monument) {
  return state.groupBy === 'era'
    ? ERA_COLOURS[monument.era] || '#8d8d95'
    : CATEGORY_COLOURS[monument.category] || '#8d8d95';
}

function pinIcon(monument) {
  const colour = colourFor(monument);
  const glyph = GLYPHS[monument.category] || FALLBACK_GLYPH;
  return L.divIcon({
    className: 'custom-pin',
    html: `<div class="pin-wrap">
      <svg width="28" height="38" viewBox="0 0 28 38" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 0C6.27 0 0 6.27 0 14c0 10.5 14 24 14 24s14-13.5 14-24c0-7.73-6.27-14-14-14z" fill="${colour}"/>
        <circle cx="14" cy="14" r="9.4" fill="#fdfcfa"/>
      </svg>
      <svg class="pin-glyph" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">${glyph}</svg>
    </div>`,
    iconSize: [28, 38],
    iconAnchor: [14, 38],
  });
}

function clusterIconFactory(colour) {
  return (cluster) => {
    const n = cluster.getChildCount();
    const size = n < 10 ? 34 : n < 50 ? 40 : 46;
    return L.divIcon({
      className: 'marker-cluster',
      html: `<div style="background:${colour};width:${size - 10}px;height:${size - 10}px">${n}</div>`,
      iconSize: [size, size],
    });
  };
}

function groupsOf(monuments) {
  const order = state.groupBy === 'era'
    ? state.eras.map((e) => e.name)
    : Object.keys(CATEGORY_COLOURS);
  const buckets = new Map();
  monuments.forEach((m) => {
    const key = state.groupBy === 'era' ? m.era : m.category;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(m);
  });
  // Keep the canonical order, then anything unexpected, alphabetically.
  const keys = order.filter((k) => buckets.has(k))
    .concat([...buckets.keys()].filter((k) => !order.includes(k)).sort());
  return keys.map((k) => [k, buckets.get(k)]);
}

function rebuildLayers() {
  state.layers.forEach(({ cluster }) => map.removeLayer(cluster));
  state.layers.clear();
  state.markers.clear();

  groupsOf(state.monuments).forEach(([name, monuments]) => {
    const colour = state.groupBy === 'era'
      ? ERA_COLOURS[name] || '#8d8d95'
      : CATEGORY_COLOURS[name] || '#8d8d95';

    const cluster = L.markerClusterGroup({
      maxClusterRadius: 46,
      disableClusteringAtZoom: 16,
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      iconCreateFunction: clusterIconFactory(colour),
    });

    monuments.forEach((m) => {
      const marker = L.marker([m.lat, m.lng], { icon: pinIcon(m), title: m.name });
      marker.on('click', () => openCard(m));
      cluster.addLayer(marker);
      state.markers.set(m.id, { marker, group: name });
    });

    cluster.addTo(map);
    state.layers.set(name, { cluster, colour, visible: true, monuments });
  });

  renderLayerList();
}

function subtitleFor(name, monuments) {
  if (state.groupBy === 'era') {
    const era = state.eras.find((e) => e.name === name);
    if (!era) return '';
    if (era.from == null && era.to == null) return 'no date on record';
    if (era.from == null) return `up to ${era.to}`;
    if (era.to == null) return `${era.from} onwards`;
    return `${era.from}–${era.to}`;
  }
  const dated = monuments.filter((m) => m.year).map((m) => m.year);
  if (!dated.length) return 'undated';
  const lo = Math.min(...dated);
  const hi = Math.max(...dated);
  return lo === hi ? `${lo}` : `${lo}–${hi}`;
}

function renderLayerList() {
  const list = document.getElementById('layer-list');
  list.innerHTML = '';

  state.layers.forEach((layer, name) => {
    const row = document.createElement('label');
    row.className = 'layer-item';

    const glyph = state.groupBy === 'category'
      ? `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">${GLYPHS[name] || FALLBACK_GLYPH}</svg>`
      : '';

    row.innerHTML = `
      <input type="checkbox" checked aria-label="${name}" />
      <span class="layer-swatch" style="background:${layer.colour}">${glyph}</span>
      <span class="layer-text">
        <span class="layer-name"></span>
        <span class="layer-sub"></span>
      </span>
      <span class="layer-count">${layer.monuments.length}</span>`;

    row.querySelector('.layer-name').textContent = name;
    row.querySelector('.layer-sub').textContent = subtitleFor(name, layer.monuments);

    const box = row.querySelector('input');
    box.addEventListener('change', () => setLayerVisible(name, box.checked));
    list.appendChild(row);
  });

  updateStatLine();
}

function setLayerVisible(name, visible) {
  const layer = state.layers.get(name);
  if (!layer) return;
  layer.visible = visible;
  if (visible) layer.cluster.addTo(map);
  else map.removeLayer(layer.cluster);

  [...document.querySelectorAll('.layer-item')].forEach((row) => {
    if (row.querySelector('.layer-name').textContent === name) {
      row.classList.toggle('off', !visible);
      row.querySelector('input').checked = visible;
    }
  });
  updateStatLine();
}

function updateStatLine() {
  let shown = 0;
  state.layers.forEach((l) => { if (l.visible) shown += l.monuments.length; });
  const years = state.monuments.filter((m) => m.year).map((m) => m.year);
  const span = years.length ? `${Math.min(...years)}–${Math.max(...years)}` : '';
  document.getElementById('stat-line').textContent =
    `${shown} of ${state.monuments.length} sites shown · ${span}`;
}

/* ───────────────────────── info card ───────────────────────── */

const card = document.getElementById('info-card');

function openCard(monument) {
  state.selected = monument;

  document.getElementById('card-title').textContent = monument.name;

  const era = document.getElementById('card-era');
  era.textContent = monument.era;
  era.style.background = ERA_COLOURS[monument.era] || '#8d8d95';

  document.getElementById('card-category').textContent = monument.category;
  document.getElementById('card-built').textContent =
    monument.year ? `Built ${monument.built}` : 'Date unrecorded';

  document.getElementById('card-desc').textContent = monument.description;

  const facts = document.getElementById('card-facts');
  facts.innerHTML = '';
  const rows = [
    ['Address', monument.address],
    ['Also listed as', monument.also_known_as && monument.also_known_as.join(', ')],
    ['Protected', monument.monument_id && `${monument.monument_id} — ${monument.protection}`],
    ['Style', monument.styles && monument.styles.length ? monument.styles.join(', ') : null],
    ['Architect', monument.architects && monument.architects.length ? monument.architects.join(', ') : null],
    ['Distance', `${monument.km_from_centre} km from Lal Dighi`],
  ];
  rows.forEach(([label, value]) => {
    if (!value) return;
    const dt = document.createElement('dt');
    dt.textContent = label;
    const dd = document.createElement('dd');
    dd.textContent = value;
    facts.append(dt, dd);
  });

  renderFurtherReading(monument.further_reading);

  document.getElementById('card-directions').href =
    `https://www.google.com/maps/dir/?api=1&destination=${monument.lat},${monument.lng}`;
  linkOrHide('card-wikipedia', monument.wikipedia);
  linkOrHide('card-wikidata', monument.wikidata);

  loadHero(monument);

  card.scrollTop = 0;
  card.classList.add('active');
  if (window.innerWidth <= 860) document.getElementById('sidebar').classList.add('collapsed');

  history.replaceState(null, '', `#${monument.id}`);
  highlightPin(monument.id);
  flyTo(monument);
}

function renderFurtherReading(entry) {
  const el = document.getElementById('card-further');
  el.textContent = '';
  el.classList.toggle('hidden', !entry);
  if (!entry) return;

  const label = document.createElement('span');
  label.className = 'further-label';
  label.textContent = 'Further reading';

  const link = document.createElement('a');
  link.href = entry.url;
  link.target = '_blank';
  link.rel = 'noopener';
  link.textContent = entry.title;

  const credit = document.createElement('span');
  credit.className = 'further-credit';
  credit.textContent = entry.credit;

  el.append(label, link, credit);
}

function linkOrHide(id, href) {
  const el = document.getElementById(id);
  el.classList.toggle('hidden', !href);
  if (href) el.href = href;
}

function loadHero(monument) {
  const hero = document.getElementById('card-hero');
  const loader = document.getElementById('card-loader');
  hero.style.backgroundImage = 'none';

  if (!monument.image) {
    hero.classList.add('empty');
    loader.textContent = 'No photograph on record';
    return;
  }

  hero.classList.remove('empty');
  loader.textContent = 'Loading photograph…';

  const img = new Image();
  const wanted = monument.id;
  img.onload = () => {
    if (state.selected && state.selected.id !== wanted) return;
    hero.style.backgroundImage = `url('${monument.image}')`;
    loader.textContent = '';
  };
  img.onerror = () => {
    if (state.selected && state.selected.id !== wanted) return;
    hero.classList.add('empty');
    loader.textContent = 'No photograph on record';
  };
  img.src = monument.image;
}

function closeCard() {
  card.classList.remove('active');
  state.selected = null;
  highlightPin(null);
  history.replaceState(null, '', window.location.pathname + window.location.search);
}

function highlightPin(id) {
  state.markers.forEach(({ marker }, key) => {
    const el = marker.getElement();
    if (el) el.classList.toggle('selected', key === id);
  });
}

function flyTo(monument) {
  const entry = state.markers.get(monument.id);
  if (!entry) return;
  const layer = state.layers.get(entry.group);
  if (layer && !layer.visible) setLayerVisible(entry.group, true);

  // Drop any handler still waiting on the previous flight, or it will fire
  // mid-way through this one and pan straight back to the last monument.
  if (state.pendingMoveEnd) map.off('moveend', state.pendingMoveEnd);

  state.pendingMoveEnd = () => {
    state.pendingMoveEnd = null;
    if (layer) layer.cluster.zoomToShowLayer(entry.marker, () => highlightPin(monument.id));
  };
  map.once('moveend', state.pendingMoveEnd);
  map.flyTo([monument.lat, monument.lng], Math.max(map.getZoom(), 16), { duration: 0.9 });
}

/* ────────────────────────── search ────────────────────────── */

const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');

function runSearch() {
  const query = searchInput.value.trim();
  if (!query || !state.fuse) {
    searchResults.style.display = 'none';
    return;
  }
  const hits = state.fuse.search(query).slice(0, 8);
  searchResults.innerHTML = '';

  if (!hits.length) {
    const empty = document.createElement('div');
    empty.className = 'search-result-item';
    empty.style.color = 'var(--text-faint)';
    empty.textContent = 'Nothing found';
    searchResults.appendChild(empty);
  } else {
    hits.forEach(({ item }) => {
      const row = document.createElement('div');
      row.className = 'search-result-item';
      row.setAttribute('role', 'option');

      const title = document.createElement('div');
      title.className = 'search-result-title';
      title.textContent = item.name;

      const sub = document.createElement('div');
      sub.className = 'search-result-sub';
      const era = document.createElement('em');
      era.textContent = item.era;
      sub.append(era, document.createTextNode(` · ${item.category}`));

      row.append(title, sub);
      row.addEventListener('click', () => {
        openCard(item);
        searchResults.style.display = 'none';
        searchInput.value = '';
      });
      searchResults.appendChild(row);
    });
  }
  searchResults.style.display = 'block';
}

searchInput.addEventListener('input', runSearch);
searchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { searchInput.value = ''; searchResults.style.display = 'none'; }
});
document.addEventListener('click', (e) => {
  if (!e.target.closest('.search-box-container')) searchResults.style.display = 'none';
});

/* ───────────────────────── controls ───────────────────────── */

document.getElementById('sidebar-toggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('collapsed');
  setTimeout(() => map.invalidateSize(), 380);
});

document.querySelector('.close-card-btn').addEventListener('click', closeCard);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeCard(); });

document.getElementById('select-all').addEventListener('click', () =>
  state.layers.forEach((_, name) => setLayerVisible(name, true)));
document.getElementById('select-none').addEventListener('click', () =>
  state.layers.forEach((_, name) => setLayerVisible(name, false)));

document.querySelectorAll('.group-switch button').forEach((btn) => {
  btn.addEventListener('click', () => {
    if (btn.dataset.group === state.groupBy) return;
    document.querySelectorAll('.group-switch button').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    state.groupBy = btn.dataset.group;
    rebuildLayers();
    if (state.selected) highlightPin(state.selected.id);
  });
});

function openFromHash() {
  const wanted = window.location.hash.replace('#', '');
  if (!wanted) {
    if (state.selected) closeCard();
    return;
  }
  if (state.selected && state.selected.id === wanted) return;
  const target = state.monuments.find((m) => m.id === wanted);
  if (target) openCard(target);
}

/* ────────────────────────── bootstrap ────────────────────────── */

Promise.all([
  fetch('monuments.json').then((r) => r.json()),
  fetch('eras.json').then((r) => r.json()),
])
  .then(([monuments, eras]) => {
    state.monuments = monuments;
    state.eras = eras;

    state.fuse = new Fuse(monuments, {
      keys: [
        { name: 'name', weight: 0.55 },
        { name: 'address', weight: 0.15 },
        { name: 'category', weight: 0.12 },
        { name: 'era', weight: 0.08 },
        { name: 'description', weight: 0.1 },
      ],
      threshold: 0.36,
      ignoreLocation: true,
    });

    rebuildLayers();

    // On a phone the sidebar covers the whole screen — show the map first.
    if (window.innerWidth <= 860) document.getElementById('sidebar').classList.add('collapsed');

    openFromHash();
    // A fragment-only change doesn't reload the page, so links between sites
    // (and the back button) have to be handled here.
    window.addEventListener('hashchange', openFromHash);
  })
  .catch((err) => {
    console.error('Could not load the dataset:', err);
    document.getElementById('layer-list').textContent =
      'The dataset failed to load. If you opened this file directly, serve the folder over HTTP instead.';
  });
