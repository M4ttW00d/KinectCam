const api = (path, body) =>
  fetch(path, {
    method: body !== undefined ? 'POST' : 'GET',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }).then(r => r.json());

// ── State polling ──
const badge = document.getElementById('status-badge');
let lastConnected = null;
let currentTilt = 0;

async function pollState() {
  try {
    const state = await api('/api/state');

    if (state.connected !== lastConnected) {
      lastConnected = state.connected;
      badge.textContent = state.connected ? 'Connected' : 'Disconnected';
      badge.className = 'badge ' + (state.connected ? 'connected' : 'disconnected');
    }

    if (!dragging) {
      currentTilt = state.tilt;
      tiltSlider.value = currentTilt;
      tiltValue.textContent = currentTilt + '°';
    }

    document.querySelectorAll('.led-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.led === state.led);
    });

    mirrorToggle.checked = state.mirror;

  } catch (_) {
    badge.textContent = 'Disconnected';
    badge.className = 'badge disconnected';
    lastConnected = false;
  }
}

setInterval(pollState, 1500);
pollState();

// ── Tilt ──
const tiltSlider = document.getElementById('tilt-slider');
const tiltValue  = document.getElementById('tilt-value');
const tiltUp     = document.getElementById('tilt-up');
const tiltDown   = document.getElementById('tilt-down');
const tiltLevel  = document.getElementById('tilt-level');
let dragging = false;
let tiltTimer = null;

const STEP = 5;

function applyTilt(angle) {
  currentTilt = Math.max(-30, Math.min(30, angle));
  tiltSlider.value = currentTilt;
  tiltValue.textContent = currentTilt + '°';
  sendTilt(currentTilt);
}

tiltUp.addEventListener('click', () => applyTilt(currentTilt + STEP));
tiltDown.addEventListener('click', () => applyTilt(currentTilt - STEP));
tiltLevel.addEventListener('click', () => applyTilt(0));

tiltSlider.addEventListener('mousedown',  () => { dragging = true; });
tiltSlider.addEventListener('touchstart', () => { dragging = true; });

tiltSlider.addEventListener('input', () => {
  currentTilt = Number(tiltSlider.value);
  tiltValue.textContent = currentTilt + '°';
  clearTimeout(tiltTimer);
  tiltTimer = setTimeout(() => sendTilt(currentTilt), 300);
});

tiltSlider.addEventListener('mouseup',  () => { dragging = false; sendTilt(currentTilt); });
tiltSlider.addEventListener('touchend', () => { dragging = false; sendTilt(currentTilt); });

function sendTilt(angle) {
  api('/api/tilt', { angle }).catch(() => {});
}

// ── LED ──
document.querySelectorAll('.led-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.led-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    api('/api/led', { led: btn.dataset.led }).catch(() => {});
  });
});

// ── Mirror ──
const mirrorToggle = document.getElementById('mirror-toggle');
mirrorToggle.addEventListener('change', () => {
  api('/api/mirror', { mirror: mirrorToggle.checked }).catch(() => {});
});
