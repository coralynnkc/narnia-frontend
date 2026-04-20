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
  MISCELLANEOUS:    '#3a3a4a',
};

const LABEL_COLORS_ALPHA = Object.fromEntries(
  Object.entries(LABEL_COLORS).map(([k, v]) => [k, v + '33'])
);

const LABEL_SHORT = {
  ACTIVE_SPEAKER:   'Speaker',
  ACTIVE_PERFORMER: 'Performer',
  ACTIVE_THOUGHT:   'Thought',
  ADDRESSED:        'Addressed',
  MENTIONED_ONLY:   'Mentioned Only',
  MISCELLANEOUS:    'Misc',
};

/* ─── Chart registry (destroy before recreate) ──────────────────────── */
const charts = {};

function destroyChart(id) {
  if (charts[id]) {
    charts[id].destroy();
    delete charts[id];
  }
}

/* ─── Chart.js global defaults ──────────────────────────────────────── */
function setChartDefaults() {
  Chart.defaults.color = '#8b8fa8';
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.padding = 14;
}

/* ─── Overview: Label Distribution (horizontal bar) ────────────────── */
function renderLabelDistChart(meta) {
  const id = 'chart-label-dist';
  destroyChart(id);
  const canvas = document.getElementById(id);
  const total = Object.values(meta.label_counts).reduce((a, b) => a + b, 0);

  const labels = LABEL_ORDER.map(l => LABEL_SHORT[l]);
  const counts = LABEL_ORDER.map(l => meta.label_counts[l] || 0);
  const colors = LABEL_ORDER.map(l => LABEL_COLORS[l]);

  charts[id] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: counts,
        backgroundColor: colors,
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
              return ` ${ctx.parsed.x.toLocaleString()} mentions (${pct}%)`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: '#2d3148' },
          ticks: { color: '#8b8fa8' },
          border: { color: '#2d3148' },
        },
        y: {
          grid: { display: false },
          ticks: { color: '#e8e8f0', font: { size: 12 } },
          border: { color: '#2d3148' },
        },
      },
    },
  });
}

/* ─── Overview: Chapter Density (bar) ──────────────────────────────── */
function renderChapterDensityChart(meta) {
  const id = 'chart-chapter-density';
  destroyChart(id);
  const canvas = document.getElementById(id);

  const labels = meta.chapter_density.map(d => `Ch.${d.chapter}`);
  const densities = meta.chapter_density.map(d => d.density);
  const notes = meta.chapter_density.map(d => d.note);

  charts[id] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Mentions / sentence',
        data: densities,
        backgroundColor: densities.map(d =>
          d >= 1.2 ? '#c9a22799' : d >= 0.9 ? '#4a9eff55' : '#2d314899'
        ),
        borderColor: densities.map(d =>
          d >= 1.2 ? '#c9a227' : d >= 0.9 ? '#4a9eff' : '#3a3f5a'
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
            label(ctx) {
              const note = notes[ctx.dataIndex];
              const base = ` ${ctx.parsed.y.toFixed(2)} mentions/sentence`;
              return note ? [base, `  ${note}`] : [base];
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8b8fa8', font: { size: 11 } },
          border: { color: '#2d3148' },
        },
        y: {
          grid: { color: '#2d3148' },
          ticks: { color: '#8b8fa8' },
          border: { color: '#2d3148' },
          title: { display: true, text: 'mentions / sentence', color: '#555870', font: { size: 11 } },
        },
      },
    },
  });
}

/* ─── Character Grid ────────────────────────────────────────────────── */
function renderCharacterGrid(characters) {
  const grid = document.getElementById('character-grid');
  const major = characters.filter(c => c.tier === 'major');

  grid.innerHTML = major.map(char => {
    const ratio = char.active_ratio;
    const barClass = ratio >= 70 ? 'green' : ratio >= 50 ? 'yellow' : 'red';
    return `
      <div class="char-card" data-slug="${char.slug}" role="button" tabindex="0" aria-label="View ${char.canonical}">
        <div class="char-name">${char.canonical}</div>
        <div class="char-count">${char.total.toLocaleString()}</div>
        <div class="char-count-label">mentions</div>
        <div class="active-bar-wrap">
          <div class="active-bar-track">
            <div class="active-bar-fill active-bar-fill--${barClass}" style="width:${ratio}%"></div>
          </div>
          <div class="char-ratio-label">${ratio.toFixed(1)}% active agency</div>
        </div>
      </div>
    `;
  }).join('');

  grid.querySelectorAll('.char-card').forEach(card => {
    card.addEventListener('click', () => openPanel(card.dataset.slug));
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openPanel(card.dataset.slug);
      }
    });
  });
}

/* ─── Supporting Cast ────────────────────────────────────────────────── */
function renderSupportingCast(characters) {
  const grid = document.getElementById('supporting-grid');
  const minor = characters.filter(c => c.tier === 'minor');
  grid.innerHTML = minor.map(c =>
    `<span class="minor-chip">${c.canonical}<span>${c.total}</span></span>`
  ).join('');
}

/* ─── Detail Panel ───────────────────────────────────────────────────── */
let currentData = null;

function openPanel(slug) {
  const char = currentData.characters.find(c => c.slug === slug);
  if (!char) return;

  // Update hash
  history.replaceState(null, '', `#character=${slug}`);

  // Populate header
  document.getElementById('panel-name').textContent = char.canonical;
  document.getElementById('panel-eyebrow').textContent = char.tier === 'major' ? 'Major Character' : 'Character';
  document.getElementById('panel-blurb').textContent = char.blurb;

  // Meta pills
  const meta = document.getElementById('panel-meta');
  const activeChapterRange = char.chapter_first === char.chapter_last
    ? `Ch.${char.chapter_first}`
    : `Ch.${char.chapter_first}–${char.chapter_last}`;
  meta.innerHTML = [
    `<span class="meta-pill"><strong>${char.total.toLocaleString()}</strong> mentions</span>`,
    `<span class="meta-pill"><strong>${char.active_ratio.toFixed(1)}%</strong> active agency</span>`,
    `<span class="meta-pill"><strong>${char.chapter_count}</strong> chapters (${activeChapterRange})</span>`,
    char.alias_count > 0 ? `<span class="meta-pill"><strong>${char.alias_count}</strong> surface forms resolved</span>` : '',
  ].join('');

  // Donut chart
  renderDonutChart(char);

  // Chapter bar chart
  renderChapterBarChart(char);

  // Alias chips
  const aliasBock = document.getElementById('panel-aliases-block');
  const chipsEl = document.getElementById('alias-chips');
  if (char.aliases && char.aliases.length > 0) {
    chipsEl.innerHTML = char.aliases.map(a =>
      `<span class="alias-chip">"${a}"</span>`
    ).join('');
    aliasBock.style.display = '';
  } else {
    aliasBock.style.display = 'none';
  }

  // Show panel
  document.getElementById('detail-panel').classList.add('open');
  document.getElementById('detail-panel').setAttribute('aria-hidden', 'false');
  document.getElementById('panel-overlay').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closePanel() {
  document.getElementById('detail-panel').classList.remove('open');
  document.getElementById('detail-panel').setAttribute('aria-hidden', 'true');
  document.getElementById('panel-overlay').classList.remove('active');
  document.body.style.overflow = '';
  history.replaceState(null, '', window.location.pathname);
}

function renderDonutChart(char) {
  const id = 'chart-detail-donut';
  destroyChart(id);
  const canvas = document.getElementById(id);

  const labels = LABEL_ORDER.map(l => LABEL_SHORT[l]);
  const data = LABEL_ORDER.map(l => char.labels[l] || 0);
  const colors = LABEL_ORDER.map(l => LABEL_COLORS[l]);

  charts[id] = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors,
        borderColor: '#1a1d27',
        borderWidth: 2,
        hoverOffset: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '60%',
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#8b8fa8',
            font: { size: 11 },
            boxWidth: 10,
            padding: 10,
            generateLabels(chart) {
              const ds = chart.data.datasets[0];
              const total = ds.data.reduce((a, b) => a + b, 0);
              return chart.data.labels.map((label, i) => ({
                text: `${label}  ${ds.data[i]} (${((ds.data[i]/total)*100).toFixed(0)}%)`,
                fillStyle: ds.backgroundColor[i],
                strokeStyle: ds.borderColor,
                hidden: ds.data[i] === 0,
                index: i,
              }));
            },
          },
        },
        tooltip: {
          callbacks: {
            label(ctx) {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = ((ctx.parsed / total) * 100).toFixed(1);
              return ` ${ctx.parsed} mentions (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

function renderChapterBarChart(char) {
  const id = 'chart-detail-chapters';
  destroyChart(id);
  const canvas = document.getElementById(id);

  const labels = char.chapters.map((_, i) => `Ch.${i + 1}`);
  const data = char.chapters;
  const maxVal = Math.max(...data);

  charts[id] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Mentions',
        data,
        backgroundColor: data.map(v =>
          v === 0 ? '#2d314830' : v === maxVal ? '#c9a22799' : '#4a9eff44'
        ),
        borderColor: data.map(v =>
          v === 0 ? 'transparent' : v === maxVal ? '#c9a227' : '#4a9eff'
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
            label(ctx) {
              return ctx.parsed.y === 0
                ? ' Not present'
                : ` ${ctx.parsed.y} mentions`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#8b8fa8', font: { size: 10 } },
          border: { color: '#2d3148' },
        },
        y: {
          grid: { color: '#2d314855' },
          ticks: {
            color: '#8b8fa8',
            font: { size: 10 },
            stepSize: Math.max(1, Math.floor(maxVal / 4)),
          },
          border: { color: '#2d3148' },
          min: 0,
        },
      },
    },
  });
}

/* ─── Stats from data ────────────────────────────────────────────────── */
function updateStats(meta) {
  const el = document.getElementById('stat-sentences');
  if (el) el.textContent = meta.total_sentences.toLocaleString();
  const el2 = document.getElementById('stat-mentions');
  if (el2) el2.textContent = meta.total_mentions.toLocaleString();
  const el3 = document.getElementById('stat-characters');
  if (el3) el3.textContent = meta.total_characters.toLocaleString();
}

/* ─── Init ───────────────────────────────────────────────────────────── */
async function init() {
  setChartDefaults();

  // Wire panel close
  document.getElementById('panel-close').addEventListener('click', closePanel);
  document.getElementById('panel-overlay').addEventListener('click', closePanel);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closePanel();
  });

  // Load data
  let data;
  try {
    const res = await fetch('./data/narnia_data.json');
    data = await res.json();
  } catch (e) {
    console.error('Failed to load narnia_data.json', e);
    return;
  }

  currentData = data;

  // Render
  updateStats(data.meta);
  renderLabelDistChart(data.meta);
  renderChapterDensityChart(data.meta);
  renderCharacterGrid(data.characters);
  renderSupportingCast(data.characters);

  // Hash routing — open panel if hash present
  const hash = window.location.hash;
  const match = hash.match(/^#character=(.+)$/);
  if (match) {
    openPanel(decodeURIComponent(match[1]));
  }
}

document.addEventListener('DOMContentLoaded', init);
