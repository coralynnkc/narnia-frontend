/* ─── Constants ─────────────────────────────────────────────────────── */
const LABEL_ORDER = [
  'ACTIVE_SPEAKER', 'ACTIVE_PERFORMER', 'ACTIVE_THOUGHT',
  'ADDRESSED', 'MENTIONED_ONLY', 'MISCELLANEOUS',
];
const LABEL_COLORS = {
  ACTIVE_SPEAKER:   '#4a9eff',
  ACTIVE_PERFORMER: '#5dd87a',
  ACTIVE_THOUGHT:   '#b47aff',
  ADDRESSED:        '#ff7a5a',
  MENTIONED_ONLY:   '#7a7a8a',
  MISCELLANEOUS:    '#5a5e78',
};
const LABEL_SHORT = {
  ACTIVE_SPEAKER:   'Speaker',
  ACTIVE_PERFORMER: 'Performer',
  ACTIVE_THOUGHT:   'Thought',
  ADDRESSED:        'Addressed',
  MENTIONED_ONLY:   'Mentioned',
  MISCELLANEOUS:    'Misc',
};

/* ─── Chart registry ────────────────────────────────────────────────── */
const charts = {};
function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

/* ─── Global state ──────────────────────────────────────────────────── */
let allData = null;
let activeSlug = null;

/* ─── Chart.js defaults ──────────────────────────────────────────────── */
function setChartDefaults() {
  Chart.defaults.color = '#8b8fa8';
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.plugins.legend.labels.boxWidth = 10;
  Chart.defaults.plugins.legend.labels.padding = 12;
}

/* ─── Overview charts ────────────────────────────────────────────────── */
function renderLabelDistChart(meta) {
  const id = 'chart-label-dist';
  destroyChart(id);
  const total = Object.values(meta.label_counts).reduce((a, b) => a + b, 0);
  charts[id] = new Chart(document.getElementById(id), {
    type: 'bar',
    data: {
      labels: LABEL_ORDER.map(l => LABEL_SHORT[l]),
      datasets: [{
        data: LABEL_ORDER.map(l => meta.label_counts[l] || 0),
        backgroundColor: LABEL_ORDER.map(l => LABEL_COLORS[l]),
        borderRadius: 4,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(ctx) {
              const pct = ((ctx.parsed.x / total) * 100).toFixed(1);
              return ` ${ctx.parsed.x.toLocaleString()} (${pct}%)`;
            },
          },
        },
      },
      scales: {
        x: { grid: { color: '#2d3148' }, ticks: { color: '#8b8fa8' }, border: { color: '#2d3148' } },
        y: { grid: { display: false }, ticks: { color: '#e8e8f0', font: { size: 12 } }, border: { color: '#2d3148' } },
      },
    },
  });
}

function renderChapterDensityChart(meta) {
  const id = 'chart-chapter-density';
  destroyChart(id);
  const densities = meta.chapter_density.map(d => d.density);
  const notes = meta.chapter_density.map(d => d.note);
  charts[id] = new Chart(document.getElementById(id), {
    type: 'bar',
    data: {
      labels: meta.chapter_density.map(d => `${d.chapter}`),
      datasets: [{
        data: densities,
        backgroundColor: densities.map(d => d >= 1.2 ? '#c9a22799' : '#4a9eff33'),
        borderColor: densities.map(d => d >= 1.2 ? '#c9a227' : '#4a9eff66'),
        borderWidth: 1.5,
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title(items) { return `Chapter ${items[0].label}`; },
            label(ctx) {
              const note = notes[ctx.dataIndex];
              const base = ` ${ctx.parsed.y.toFixed(2)} mentions/sentence`;
              return note ? [base, `  ${note}`] : base;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8b8fa8', font: { size: 10 } },
          border: { color: '#2d3148' },
          title: { display: true, text: 'Chapter', color: '#555870', font: { size: 11 } },
        },
        y: {
          grid: { color: '#2d3148' },
          ticks: { color: '#8b8fa8' },
          border: { color: '#2d3148' },
        },
      },
    },
  });
}

/* ─── Search ─────────────────────────────────────────────────────────── */
function initSearch() {
  const input = document.getElementById('search-input');
  const dropdown = document.getElementById('search-dropdown');
  const clearBtn = document.getElementById('search-clear');
  const chars = allData.characters;

  let highlighted = -1;

  function getMatches(query) {
    const q = query.toLowerCase().trim();
    if (!q) return chars.slice(0, 8);
    return chars
      .filter(c => c.canonical.toLowerCase().includes(q))
      .slice(0, 10);
  }

  function renderDropdown(matches, query) {
    if (!matches.length) {
      dropdown.innerHTML = '<li class="dropdown-empty">No characters found</li>';
      dropdown.hidden = false;
      return;
    }
    dropdown.innerHTML = matches.map((c, i) => `
      <li class="dropdown-item" role="option" data-slug="${c.slug}" data-index="${i}">
        <span class="dropdown-item-name">${highlight(c.canonical, query)}</span>
        <span class="dropdown-item-count">${c.total.toLocaleString()} mentions</span>
      </li>
    `).join('');
    dropdown.hidden = false;
    highlighted = -1;

    dropdown.querySelectorAll('.dropdown-item').forEach(item => {
      item.addEventListener('mousedown', e => {
        e.preventDefault();
        selectCharacter(item.dataset.slug, chars.find(c => c.slug === item.dataset.slug).canonical);
      });
    });
  }

  function highlight(name, query) {
    if (!query) return name;
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return name.replace(re, '<mark>$1</mark>');
  }

  function closeDropdown() {
    dropdown.hidden = true;
    highlighted = -1;
  }

  function selectCharacter(slug, name) {
    input.value = name;
    clearBtn.hidden = false;
    closeDropdown();
    showReport(slug);
  }

  input.addEventListener('input', () => {
    const q = input.value;
    clearBtn.hidden = !q;
    if (!q) {
      // If cleared, show global view
      closeDropdown();
      if (activeSlug) showGlobal();
      return;
    }
    renderDropdown(getMatches(q), q);
  });

  input.addEventListener('focus', () => {
    if (!input.value) renderDropdown(getMatches(''), '');
  });

  input.addEventListener('keydown', e => {
    const items = dropdown.querySelectorAll('.dropdown-item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      highlighted = Math.min(highlighted + 1, items.length - 1);
      updateHighlight(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      highlighted = Math.max(highlighted - 1, -1);
      updateHighlight(items);
    } else if (e.key === 'Enter') {
      if (highlighted >= 0 && items[highlighted]) {
        const slug = items[highlighted].dataset.slug;
        const name = chars.find(c => c.slug === slug).canonical;
        selectCharacter(slug, name);
      }
    } else if (e.key === 'Escape') {
      closeDropdown();
    }
  });

  function updateHighlight(items) {
    items.forEach((el, i) => {
      el.setAttribute('aria-selected', i === highlighted ? 'true' : 'false');
    });
  }

  clearBtn.addEventListener('click', () => {
    input.value = '';
    clearBtn.hidden = true;
    closeDropdown();
    showGlobal();
    input.focus();
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrap')) closeDropdown();
  });

  document.getElementById('report-back').addEventListener('click', () => {
    input.value = '';
    clearBtn.hidden = true;
    showGlobal();
  });
}

/* ─── View switching ─────────────────────────────────────────────────── */
function showGlobal() {
  activeSlug = null;
  document.getElementById('global-view').hidden = false;
  document.getElementById('report-view').hidden = true;
  history.replaceState(null, '', window.location.pathname);
}

function showReport(slug) {
  activeSlug = slug;
  const char = allData.characters.find(c => c.slug === slug);
  if (!char) return;

  // Header
  document.getElementById('report-eyebrow').textContent =
    char.tier === 'major' ? 'Major Character' : 'Character';
  document.getElementById('report-name').textContent = char.canonical;

  const activeRange = char.chapter_first === char.chapter_last
    ? `Ch.${char.chapter_first}`
    : `Ch.${char.chapter_first}–${char.chapter_last}`;

  document.getElementById('report-pills').innerHTML = [
    `<span class="report-pill"><strong>${char.total.toLocaleString()}</strong> mentions</span>`,
    `<span class="report-pill"><strong>${char.active_ratio.toFixed(1)}%</strong> active agency</span>`,
    `<span class="report-pill"><strong>${char.chapter_count}</strong> of 17 chapters (${activeRange})</span>`,
    char.alias_count > 0
      ? `<span class="report-pill"><strong>${char.alias_count}</strong> surface forms resolved</span>`
      : '',
  ].join('');

  document.getElementById('report-blurb').textContent = char.blurb;

  // Charts
  renderDonutChart(char);
  renderChapterBar(char);

  // Aliases
  const aliasBlock = document.getElementById('report-aliases');
  const chipsEl = document.getElementById('alias-chips');
  if (char.aliases && char.aliases.length > 0) {
    chipsEl.innerHTML = char.aliases
      .map(a => `<span class="alias-chip">"${a}"</span>`)
      .join('');
    aliasBlock.style.display = '';
  } else {
    aliasBlock.style.display = 'none';
  }

  document.getElementById('global-view').hidden = true;
  document.getElementById('report-view').hidden = false;

  history.replaceState(null, '', `#character=${slug}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderDonutChart(char) {
  const id = 'chart-donut';
  destroyChart(id);
  const data = LABEL_ORDER.map(l => char.labels[l] || 0);
  const total = data.reduce((a, b) => a + b, 0);
  charts[id] = new Chart(document.getElementById(id), {
    type: 'doughnut',
    data: {
      labels: LABEL_ORDER.map(l => LABEL_SHORT[l]),
      datasets: [{
        data,
        backgroundColor: LABEL_ORDER.map(l => LABEL_COLORS[l]),
        borderColor: '#1a1d27',
        borderWidth: 2,
        hoverOffset: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '62%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#e8e8f0',
            font: { size: 11 },
            generateLabels(chart) {
              return chart.data.labels.map((label, i) => ({
                text: `${label}  ${((data[i]/total)*100).toFixed(0)}%`,
                fillStyle: chart.data.datasets[0].backgroundColor[i],
                strokeStyle: '#1a1d27',
                hidden: data[i] === 0,
                index: i,
              }));
            },
          },
        },
        tooltip: {
          callbacks: {
            label(ctx) {
              const pct = ((ctx.parsed / total) * 100).toFixed(1);
              return ` ${ctx.parsed} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

function renderChapterBar(char) {
  const id = 'chart-chapters';
  destroyChart(id);
  const data = char.chapters;
  const maxVal = Math.max(...data, 1);
  charts[id] = new Chart(document.getElementById(id), {
    type: 'bar',
    data: {
      labels: data.map((_, i) => `${i + 1}`),
      datasets: [{
        label: 'Mentions',
        data,
        backgroundColor: data.map(v =>
          v === 0 ? '#2d314820'
          : v === maxVal ? '#c9a22799'
          : '#4a9eff44'
        ),
        borderColor: data.map(v =>
          v === 0 ? 'transparent'
          : v === maxVal ? '#c9a227'
          : '#4a9eff'
        ),
        borderWidth: 1.5,
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title(items) { return `Chapter ${items[0].label}`; },
            label(ctx) {
              return ctx.parsed.y === 0 ? ' Not present' : ` ${ctx.parsed.y} mentions`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8b8fa8', font: { size: 10 } },
          border: { color: '#2d3148' },
          title: { display: true, text: 'Chapter', color: '#555870', font: { size: 11 } },
        },
        y: {
          grid: { color: '#2d314855' },
          ticks: { color: '#8b8fa8', font: { size: 10 }, stepSize: Math.max(1, Math.floor(maxVal / 4)) },
          border: { color: '#2d3148' },
          min: 0,
        },
      },
    },
  });
}

/* ─── Stats update ───────────────────────────────────────────────────── */
function updateStats(meta) {
  const s = id => document.getElementById(id);
  if (s('stat-sentences')) s('stat-sentences').textContent = meta.total_sentences.toLocaleString();
  if (s('stat-mentions')) s('stat-mentions').textContent = meta.total_mentions.toLocaleString();
  if (s('stat-chars')) s('stat-chars').textContent = meta.total_characters.toLocaleString();
}

/* ─── Init ───────────────────────────────────────────────────────────── */
async function init() {
  setChartDefaults();

  let data;
  try {
    const res = await fetch('./data/narnia_data.json');
    data = await res.json();
  } catch (e) {
    console.error('Failed to load narnia_data.json', e);
    return;
  }
  allData = data;

  updateStats(data.meta);
  renderLabelDistChart(data.meta);
  renderChapterDensityChart(data.meta);
  initSearch();

  // Hash routing
  const match = window.location.hash.match(/^#character=(.+)$/);
  if (match) {
    const slug = decodeURIComponent(match[1]);
    const char = data.characters.find(c => c.slug === slug);
    if (char) {
      const input = document.getElementById('search-input');
      const clearBtn = document.getElementById('search-clear');
      input.value = char.canonical;
      clearBtn.hidden = false;
      showReport(slug);
    }
  }
}

document.addEventListener('DOMContentLoaded', init);
