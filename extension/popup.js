const BASE = 'http://localhost:36000';
const STEP = 5;

const angleEl = document.getElementById('angle');
const statusEl = document.getElementById('status');
let currentTilt = 0;

async function getState() {
  try {
    const res = await fetch(`${BASE}/api/state`);
    const state = await res.json();
    currentTilt = state.tilt;
    angleEl.textContent = `${Math.round(currentTilt)}°`;
    statusEl.textContent = state.connected ? 'Connected' : 'Disconnected';
    statusEl.className = 'status ' + (state.connected ? 'connected' : 'disconnected');
  } catch {
    statusEl.textContent = 'Disconnected';
    statusEl.className = 'status disconnected';
  }
}

async function sendTilt(angle) {
  angle = Math.max(-30, Math.min(30, angle));
  try {
    await fetch(`${BASE}/api/tilt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ angle }),
    });
    currentTilt = angle;
    angleEl.textContent = `${Math.round(angle)}°`;
  } catch {}
}

document.getElementById('btn-up').addEventListener('click', () => sendTilt(currentTilt + STEP));
document.getElementById('btn-down').addEventListener('click', () => sendTilt(currentTilt - STEP));
document.getElementById('btn-level').addEventListener('click', () => sendTilt(0));

getState();
setInterval(getState, 1500);
