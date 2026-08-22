"""AI Router Dashboard — web UI for managing profiles and configuration.

Usage in router.py:
    from dashboard import register_dashboard
    register_dashboard(app, BASE_DIR)

Then open http://127.0.0.1:3459/ui
"""

import json
import os
import re
from pathlib import Path
from flask import request, jsonify

# ─────────────────────────────────────────────────────────────────────────────
# Inline single-page HTML/CSS/JS dashboard
# ─────────────────────────────────────────────────────────────────────────────
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Router</title>
<style>
:root{--bg:#0d1117;--sb:#161b22;--card:#21262d;--bdr:#30363d;--tx:#e6edf3;--mu:#7d8590;
  --ac:#58a6ff;--ok:#3fb950;--er:#f85149;--wn:#d29922}
*{box-sizing:border-box;margin:0;padding:0}
body{font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg);color:var(--tx);display:flex;height:100vh;overflow:hidden}
#sidebar{width:210px;min-width:210px;background:var(--sb);border-right:1px solid var(--bdr);
  display:flex;flex-direction:column;padding:16px 0}
.logo{padding:8px 20px 20px;font-size:16px;font-weight:700;color:var(--ac)}
.logo .sub{color:var(--mu);font-weight:400;font-size:11px;display:block;margin-top:2px}
nav a{display:flex;align-items:center;gap:10px;padding:9px 20px;color:var(--mu);
  border-left:3px solid transparent;transition:all .15s;cursor:pointer;user-select:none}
nav a:hover{color:var(--tx);background:rgba(88,166,255,.07)}
nav a.active{color:var(--ac);border-left-color:var(--ac);background:rgba(88,166,255,.07)}
.icon{font-size:15px;width:20px;text-align:center}
.sb-foot{margin-top:auto;padding:16px 20px;color:var(--mu);font-size:12px}
#main{flex:1;overflow-y:auto;padding:28px 32px}
.sec{display:none}.sec.on{display:block}
h1{font-size:20px;font-weight:600;margin-bottom:4px}
.sub2{color:var(--mu);font-size:13px;margin-bottom:22px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-bottom:24px}
.scard{background:var(--card);border:1px solid var(--bdr);border-radius:8px;padding:16px 20px}
.sval{font-size:28px;font-weight:700;color:var(--ac)}
.slbl{color:var(--mu);font-size:12px;margin-top:4px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--ok);
  margin-right:6px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.btn{padding:7px 14px;border-radius:6px;border:none;cursor:pointer;font-size:13px;
  font-weight:500;transition:opacity .15s}
.btn:hover{opacity:.85}
.btn-p{background:var(--ac);color:#0d1117}
.btn-d{background:var(--er);color:#fff}
.btn-g{background:transparent;border:1px solid var(--bdr);color:var(--tx)}
.btn-s{padding:4px 10px;font-size:12px}
.toolbar{display:flex;align-items:center;gap:10px;margin-bottom:16px}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:10px 12px;color:var(--mu);font-weight:500;font-size:11px;
  text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--bdr)}
td{padding:10px 12px;border-bottom:1px solid rgba(48,54,61,.5);vertical-align:middle}
tr:hover td{background:rgba(88,166,255,.04)}
.tag{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;
  background:rgba(88,166,255,.15);color:var(--ac);margin:1px}
.tag.ok{background:rgba(63,185,80,.15);color:var(--ok)}
.tag.no{background:rgba(248,81,73,.15);color:var(--er)}
.acts{display:flex;gap:6px}
#overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);
  z-index:100;align-items:center;justify-content:center}
#overlay.on{display:flex}
#modal{background:var(--card);border:1px solid var(--bdr);border-radius:10px;
  width:660px;max-width:95vw;max-height:90vh;display:flex;flex-direction:column}
.mh{padding:16px 20px;border-bottom:1px solid var(--bdr);
  display:flex;justify-content:space-between;align-items:center}
.mh h2{font-size:15px;font-weight:600}
.mx{background:none;border:none;color:var(--mu);font-size:22px;cursor:pointer;
  padding:0 4px;line-height:1}
.mb{padding:16px 20px;flex:1;overflow-y:auto}
.mf{padding:12px 20px;border-top:1px solid var(--bdr);
  display:flex;justify-content:flex-end;gap:8px}
.jed{width:100%;min-height:340px;font:13px/1.6 "JetBrains Mono","Fira Code",monospace;
  background:var(--bg);color:var(--tx);border:1px solid var(--bdr);
  border-radius:6px;padding:12px;resize:vertical}
.jed:focus{outline:none;border-color:var(--ac)}
.merr{color:var(--er);font-size:12px;margin-top:8px}
.key-row{display:flex;align-items:center;gap:12px;padding:10px 0;
  border-bottom:1px solid rgba(48,54,61,.4);flex-wrap:wrap}
.kname{font-family:monospace;font-size:13px;min-width:240px}
.kval{font-family:monospace;font-size:12px;color:var(--mu);min-width:140px}
input[type=password],input[type=text],select{background:var(--bg);border:1px solid var(--bdr);
  border-radius:6px;padding:7px 10px;color:var(--tx);font-size:13px}
input:focus,select:focus{outline:none;border-color:var(--ac)}
.lbox{background:var(--card);border:1px solid var(--bdr);border-radius:8px;
  padding:20px;max-width:740px}
.cmd{background:var(--bg);border:1px solid var(--bdr);border-radius:6px;
  padding:14px 16px;font-family:monospace;font-size:13px;line-height:1.9;
  margin:12px 0;white-space:pre-wrap;word-break:break-all}
.ek{color:var(--wn)}.ev{color:var(--ac)}.eb{color:var(--tx);font-weight:bold}
#tools-ed{width:100%;min-height:500px;font:13px/1.6 "JetBrains Mono","Fira Code",monospace;
  background:var(--card);color:var(--tx);border:1px solid var(--bdr);
  border-radius:8px;padding:16px;resize:vertical}
#tools-ed:focus{outline:none;border-color:var(--ac)}
#toast{position:fixed;bottom:24px;right:24px;z-index:200;
  display:flex;flex-direction:column;gap:8px;pointer-events:none}
.tm{padding:10px 16px;border-radius:6px;font-size:13px;pointer-events:auto;
  animation:fup .3s;max-width:320px}
.tm.ok{background:#1f3d2e;border:1px solid var(--ok);color:var(--ok)}
.tm.err{background:#3d1f1f;border:1px solid var(--er);color:var(--er)}
@keyframes fup{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
code{font-family:monospace;font-size:12px;background:rgba(255,255,255,.06);
  padding:1px 5px;border-radius:3px}
.empty{color:var(--mu);text-align:center;padding:40px}
label{font-size:12px;color:var(--mu);display:block;margin-bottom:5px}
</style>
</head>
<body>

<div id="sidebar">
  <div class="logo">⚡ AI Router<span class="sub">dashboard</span></div>
  <nav>
    <a class="active" data-s="status"  onclick="nav(this,'status')"><span class="icon">📊</span>Status</a>
    <a data-s="agents"    onclick="nav(this,'agents')"><span class="icon">🤖</span>Agents</a>
    <a data-s="providers" onclick="nav(this,'providers')"><span class="icon">🌐</span>Providers</a>
    <a data-s="harnesses" onclick="nav(this,'harnesses')"><span class="icon">🔧</span>Harnesses</a>
    <a data-s="tools"     onclick="nav(this,'tools')"><span class="icon">🛠</span>Tool Profiles</a>
    <a data-s="keys"      onclick="nav(this,'keys')"><span class="icon">🔑</span>API Keys</a>
    <a data-s="launch"    onclick="nav(this,'launch')"><span class="icon">🚀</span>Launch</a>
    <a data-s="log"       onclick="nav(this,'log')"><span class="icon">📋</span>Request Log</a>
  </nav>
  <div class="sb-foot">:3459</div>
</div>

<div id="main">
  <!-- STATUS -->
  <div id="s-status" class="sec on">
    <h1>Status</h1><p class="sub2">AI Router runtime overview</p>
    <div class="grid" id="stat-cards"></div>
    <p id="stat-info" style="color:var(--mu);font-size:12px"></p>
  </div>

  <!-- AGENTS -->
  <div id="s-agents" class="sec">
    <h1>Agent Profiles</h1>
    <p class="sub2">Each agent maps a harness + provider + model + tool profile</p>
    <div class="toolbar">
      <button class="btn btn-p" onclick="newItem('agents')">+ New Agent</button>
    </div>
    <table>
      <thead><tr><th>Slug</th><th>Name</th><th>Harness</th><th>Provider</th><th>Model</th><th>Tools</th><th></th></tr></thead>
      <tbody id="tb-agents"><tr><td colspan="7" class="empty">Loading…</td></tr></tbody>
    </table>
  </div>

  <!-- PROVIDERS -->
  <div id="s-providers" class="sec">
    <h1>Provider Profiles</h1>
    <p class="sub2">Upstream API endpoints and authentication</p>
    <div class="toolbar">
      <button class="btn btn-p" onclick="newItem('providers')">+ New Provider</button>
    </div>
    <table>
      <thead><tr><th>Slug</th><th>Name</th><th>Base URL</th><th>API Key Env</th><th>Protocols</th><th></th></tr></thead>
      <tbody id="tb-providers"><tr><td colspan="6" class="empty">Loading…</td></tr></tbody>
    </table>
  </div>

  <!-- HARNESSES -->
  <div id="s-harnesses" class="sec">
    <h1>Harness Profiles</h1>
    <p class="sub2">Client harness configurations</p>
    <div class="toolbar">
      <button class="btn btn-p" onclick="newItem('harnesses')">+ New Harness</button>
      <button class="btn btn-g" onclick="scanSystemHarnesses()">🔍 Scan System</button>
    </div>
    <table>
      <thead><tr><th>Slug</th><th>Binary</th><th>Protocol</th><th>Launch Mode</th><th>Tools</th><th>Profiles</th><th></th></tr></thead>
      <tbody id="tb-harnesses"><tr><td colspan="7" class="empty">Loading…</td></tr></tbody>
    </table>

    <details style="margin-top:16px">
      <summary style="cursor:pointer;font-weight:600;color:var(--tx);padding:8px 0">📦 Available Harnesses (click to install)</summary>
      <div id="harness-catalog" style="margin-top:10px"><span class="empty" style="padding:12px">Click to load catalog...</span></div>
    </details>
    <script>
    document.querySelector('#s-harnesses details').addEventListener('toggle', function(e) {
      if (this.open) loadHarnessCatalog();
    });
    </script>
  </div>

  <!-- TOOLS -->
  <div id="s-tools" class="sec">
    <h1>Tool Profiles</h1>
    <p class="sub2">Controls which tools each agent can use</p>
    <div class="toolbar">
      <button class="btn btn-p" onclick="saveTools()">💾 Save</button>
      <button class="btn btn-g" onclick="loadTools()">↺ Reload</button>
    </div>
    <textarea id="tools-ed"></textarea>
  </div>

  <!-- KEYS -->
  <div id="s-keys" class="sec">
    <h1>API Keys</h1>
    <p class="sub2">Environment variables from <code>.env</code> — values are masked</p>
    <div class="toolbar">
      <button class="btn btn-p" onclick="saveKeys()">💾 Save to .env</button>
      <button class="btn btn-g" onclick="loadKeys()">↺ Refresh</button>
    </div>
    <div id="keys-list"></div>
  </div>

  <!-- LAUNCH -->
  <div id="s-launch" class="sec">
    <h1>Launch</h1>
    <p class="sub2">Generate the shell command to start a harness session</p>
    <div class="lbox">
      <div style="margin-bottom:16px">
        <label>Agent Profile</label>
        <select id="launch-sel" onchange="showLaunch()" style="min-width:300px">
          <option value="">— select agent —</option>
        </select>
      </div>
      <div id="launch-out"></div>
    </div>
  </div>

  <!-- REQUEST LOG -->
  <div id="s-log" class="sec">
    <h1>Request Log</h1>
    <p class="sub2">Live view of requests passing through the router — verify model routing</p>
    <div class="toolbar">
      <button class="btn btn-g" onclick="loadRequestLog()">↺ Refresh</button>
      <span style="font-size:11px;color:var(--mu);margin-left:12px">Shows last 50 requests (most recent first)</span>
    </div>
    <table>
      <thead><tr><th>Time</th><th>Agent</th><th>Harness</th><th>Model (harness sent)</th><th>→</th><th>Model (actually used)</th><th>Provider</th></tr></thead>
      <tbody id="tb-log"><tr><td colspan="7" class="empty">Click Refresh to load</td></tr></tbody>
    </table>
  </div>
</div>

<!-- Modal -->
<div id="overlay">
  <div id="modal">
    <div class="mh"><h2 id="mtitle"></h2><button class="mx" onclick="closeModal()">×</button></div>
    <div class="mb">
      <textarea class="jed" id="med"></textarea>
      <div class="merr" id="merr" style="display:none"></div>
    </div>
    <div class="mf">
      <button class="btn btn-g" onclick="closeModal()">Cancel</button>
      <button class="btn btn-p" id="msave" onclick="doSave()">Save</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
'use strict';

// ── Utilities ──────────────────────────────────────────────────────────────

async function api(method, url, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  const ct = r.headers.get('content-type') || '';
  const d = ct.includes('json') ? await r.json() : await r.text();
  if (!r.ok) throw new Error((d && d.error) ? d.error : 'HTTP ' + r.status);
  return d;
}

function toast(msg, ok = true) {
  const el = document.createElement('div');
  el.className = 'tm ' + (ok ? 'ok' : 'err');
  el.textContent = msg;
  document.getElementById('toast').append(el);
  setTimeout(() => el.remove(), 3500);
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

// ── Navigation ─────────────────────────────────────────────────────────────

const loaders = {};
function nav(el, name) {
  document.querySelectorAll('.sec').forEach(s => s.classList.remove('on'));
  document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
  document.getElementById('s-' + name).classList.add('on');
  el.classList.add('active');
  if (loaders[name]) loaders[name]();
}

// ── Modal ──────────────────────────────────────────────────────────────────

let _saveFn = null;
function openModal(title, data, saveFn) {
  _saveFn = saveFn;
  document.getElementById('mtitle').textContent = title;
  document.getElementById('med').value = JSON.stringify(data, null, 2);
  document.getElementById('med').readOnly = !saveFn;
  document.getElementById('msave').style.display = saveFn ? '' : 'none';
  document.getElementById('merr').style.display = 'none';
  document.getElementById('overlay').classList.add('on');
  setTimeout(() => document.getElementById('med').focus(), 50);
}
function closeModal() { document.getElementById('overlay').classList.remove('on'); }
function doSave() {
  let d;
  try { d = JSON.parse(document.getElementById('med').value); }
  catch (e) {
    const el = document.getElementById('merr');
    el.textContent = 'JSON error: ' + e.message;
    el.style.display = 'block';
    return;
  }
  _saveFn && _saveFn(d);
}
document.getElementById('overlay').addEventListener('click', e => {
  if (e.target.id === 'overlay' && !_modalLoading) closeModal();
});

// ── Status ─────────────────────────────────────────────────────────────────

loaders.status = async function () {
  try {
    const s = await api('GET', '/api/status');
    document.getElementById('stat-cards').innerHTML =
      '<div class="scard"><div class="sval"><span class="dot"></span>Running</div><div class="slbl">Router Status</div></div>' +
      '<div class="scard"><div class="sval">' + s.agents + '</div><div class="slbl">Agents</div></div>' +
      '<div class="scard"><div class="sval">' + s.providers + '</div><div class="slbl">Providers</div></div>' +
      '<div class="scard"><div class="sval">' + s.harnesses + '</div><div class="slbl">Harnesses</div></div>';
    document.getElementById('stat-info').innerHTML =
      'Endpoints: <code>/v1/messages</code> (Anthropic) &nbsp;·&nbsp; ' +
      '<code>/v1/chat/completions</code> (OpenAI) &nbsp;·&nbsp; ' +
      '<code>/health</code> &nbsp;·&nbsp; <code>/ui</code>';
  } catch (e) { toast(e.message, false); }
};

// ── Agents ─────────────────────────────────────────────────────────────────

let _formOpts = null;
let _orModels = null;

async function loadFormOpts(forceRefresh) {
  if (!_formOpts || forceRefresh) _formOpts = await api('GET', '/api/form-options');
  return _formOpts;
}
async function loadModels() {
  if (!_orModels) _orModels = await api('GET', '/api/openrouter-models');
  return _orModels;
}

loaders.agents = async function () {
  const tb = document.getElementById('tb-agents');
  try {
    const list = await api('GET', '/api/agents');
    if (!list.length) { tb.innerHTML = '<tr><td colspan="7" class="empty">No agents yet — click + New Agent</td></tr>'; return; }
    tb.innerHTML = list.map(d =>
      '<tr>' +
      '<td><code>' + esc(d._slug) + '</code></td>' +
      '<td>' + esc(d.name || '—') + '</td>' +
      '<td><span class="tag">' + esc(d.harness || '—') + '</span></td>' +
      '<td><span class="tag">' + esc(d.provider || '—') + '</span></td>' +
      '<td style="font:12px monospace;color:var(--mu)">' + esc(d.model || '—') + '</td>' +
      '<td><span class="tag ok">' + esc(d.tool_profile || '—') + '</span></td>' +
      '<td class="acts">' +
        '<button class="btn btn-g btn-s" onclick="editAgentForm(\'' + esc(d._slug) + '\')">Edit</button>' +
        '<button class="btn btn-g btn-s" onclick="editItem(\' agents\',\'' + esc(d._slug) + '\')">JSON</button>' +
        '<button class="btn btn-d btn-s" onclick="delItem(\'agents\',\'' + esc(d._slug) + '\')">Del</button>' +
      '</td></tr>'
    ).join('');
  } catch (e) { tb.innerHTML = '<tr><td colspan="7" class="empty">' + esc(e.message) + '</td></tr>'; }
};


// ── Providers ──────────────────────────────────────────────────────────────

loaders.providers = async function () {
  const tb = document.getElementById('tb-providers');
  try {
    const list = await api('GET', '/api/providers');
    if (!list.length) { tb.innerHTML = '<tr><td colspan="6" class="empty">No providers yet</td></tr>'; return; }
    tb.innerHTML = list.map(d => {
      const protos = Object.keys(d.endpoints || {}).map(p => '<span class="tag">' + esc(p) + '</span>').join(' ');
      return '<tr>' +
        '<td><code>' + esc(d._slug) + '</code></td>' +
        '<td>' + esc(d.name || d._slug) + '</td>' +
        '<td style="font:12px monospace;color:var(--mu)">' + esc(d.base_url || '—') + '</td>' +
        '<td><code>' + esc(d.api_key_env || '—') + '</code></td>' +
        '<td>' + (protos || '—') + '</td>' +
        '<td class="acts">' +
          '<button class="btn btn-g btn-s" onclick="editItem(\'providers\',\'' + esc(d._slug) + '\')">Edit</button>' +
          '<button class="btn btn-d btn-s" onclick="delItem(\'providers\',\'' + esc(d._slug) + '\')">Del</button>' +
        '</td></tr>';
    }).join('');
  } catch (e) { tb.innerHTML = '<tr><td colspan="6" class="empty">' + esc(e.message) + '</td></tr>'; }
};

// ── Harnesses ──────────────────────────────────────────────────────────────

loaders.harnesses = async function () {
  const tb = document.getElementById('tb-harnesses');
  try {
    const list = await api('GET', '/api/harnesses');
    if (!list.length) { tb.innerHTML = '<tr><td colspan="7" class="empty">No harnesses</td></tr>'; return; }
    tb.innerHTML = list.map(d => {
      const toolCount = (d.available_tools||[]).length;
      const profileCount = Object.keys(d.tool_profiles||{}).length;
      return '<tr>' +
        '<td><code>' + esc(d._slug) + '</code></td>' +
        '<td><code>' + esc(d.binary || '—') + '</code></td>' +
        '<td><span class="tag">' + esc(d.speaks_protocol || '—') + '</span></td>' +
        '<td><span class="tag">' + esc(d.launch_mode || '—') + '</span></td>' +
        '<td><span class="tag'+(toolCount?' ok':' no')+'">' + toolCount + ' tools</span></td>' +
        '<td><span class="tag">' + profileCount + ' profiles</span></td>' +
        '<td class="acts">' +
          '<button class="btn btn-p btn-s" onclick="editHarnessForm(\'' + esc(d._slug) + '\')">Edit</button>' +
          '<button class="btn btn-g btn-s" onclick="editItem(\'harnesses\',\'' + esc(d._slug) + '\')">JSON</button>' +
          '<button class="btn btn-d btn-s" onclick="delItem(\'harnesses\',\'' + esc(d._slug) + '\')">Del</button>' +
        '</td></tr>';
    }).join('');
  } catch (e) { tb.innerHTML = '<tr><td colspan="7" class="empty">' + esc(e.message) + '</td></tr>'; }
};

async function scanSystemHarnesses() {
  try {
    const result = await api('POST', '/api/harnesses/discover-system');
    if (result.found && result.found.length) {
      let msg = 'Found: ' + result.found.map(f => f.binary + ' (' + f.path + ')').join(', ');
      if (result.created.length) msg += '\nCreated: ' + result.created.join(', ');
      toast(msg);
      loaders.harnesses();
    } else {
      toast('No known harness binaries found on PATH', false);
    }
  } catch(e) { toast(e.message, false); }
}

async function loadHarnessCatalog() {
  const container = document.getElementById('harness-catalog');
  try {
    const catalog = await api('GET', '/api/harnesses/catalog');
    if (!catalog.length) { container.innerHTML = '<span class="empty">No harnesses in catalog</span>'; return; }
    container.innerHTML = '<div style="display:grid;gap:10px">' + catalog.map(h => {
      const isIncompat = h.incompatible || (h.speaks_protocol === 'openai-responses');
      const status = h.installed
        ? '<span class="tag ok">✅ Installed</span> <code style="font-size:11px">' + esc(h.binary_path) + '</code>'
        : isIncompat ? '<span class="tag" style="background:#3d1f1f;color:var(--er)">⛔ Incompatible</span>'
        : '<span class="tag no">❌ Not installed</span>';
      const methods = Object.keys(h.install_commands || {});
      const installBtns = h.installed ? '' : methods.map(m =>
        '<button class="btn btn-p btn-s" style="margin-right:4px" onclick="installHarness(\'' + esc(h.binary) + '\',\'' + m + '\')">' + m + '</button>'
      ).join('');
      return '<div style="background:var(--bg);border:1px solid var(--bdr);border-radius:8px;padding:12px">' +
        '<div style="display:flex;justify-content:space-between;align-items:center">' +
        '<div><b>' + esc(h.name) + '</b> <code style="color:var(--mu)">(' + esc(h.binary) + ')</code>' +
        ' <span class="tag">' + esc(h.speaks_protocol) + '</span></div>' +
        '<div>' + status + '</div></div>' +
        '<div style="font-size:12px;color:var(--mu);margin-top:4px">' + esc(h.description) + '</div>' +
        (h.homepage ? '<div style="font-size:11px;margin-top:4px"><a href="'+esc(h.homepage)+'" target="_blank" style="color:var(--ac)">' + esc(h.homepage) + '</a></div>' : '') +
        (!h.installed && !isIncompat && methods.length ? '<div style="margin-top:8px">Install via: ' + installBtns + '</div>' : '') +
        (h.installed && !h.has_profile ? '<div style="margin-top:8px"><button class="btn btn-g btn-s" onclick="scanSystemHarnesses()">Create Profile</button></div>' : '') +
        '</div>';
    }).join('') + '</div>';
  } catch(e) { container.innerHTML = '<span class="empty">Error: ' + esc(e.message) + '</span>'; }
}

async function installHarness(binary, method) {
  if (!confirm('Install ' + binary + ' via ' + method + '?\n\nCommand will be run with shell=True.')) return;
  toast('Installing ' + binary + ' via ' + method + '... (may take a minute)');
  try {
    const result = await api('POST', '/api/harnesses/install', {binary, method});
    if (result.success) {
      toast('✅ ' + binary + ' installed at: ' + (result.binary_path || 'PATH'));
      loadHarnessCatalog();
      loaders.harnesses();
    } else {
      toast('❌ Install failed (exit ' + result.returncode + '): ' + (result.stderr || result.stdout).slice(0, 200), false);
    }
  } catch(e) { toast(e.message, false); }
}


// ── Harness Form Editor ───────────────────────────────────────────────────

async function editHarnessForm(slug) {
  const harness = await api('GET', '/api/harnesses/' + slug);
  openHarnessFormModal(slug, harness);
}

function openHarnessFormModal(slug, harness) {
  const title = 'Edit Harness: ' + slug;
  const lmOpts = ['env','config_file','config_file_plus_env'].map(m =>
    '<option value="'+m+'"'+(harness.launch_mode===m?' selected':'')+'>'+m+'</option>'
  ).join('');
  const prOpts = ['anthropic','openai'].map(p =>
    '<option value="'+p+'"'+(harness.speaks_protocol===p?' selected':'')+'>'+p+'</option>'
  ).join('');

  const envRows = Object.entries(harness.env_map||{}).map(([k,v]) =>
    '<div class="hf-env-row" style="display:flex;gap:8px;margin-bottom:6px">' +
    '<input type="text" class="hf-envk" value="'+esc(k)+'" style="width:40%" placeholder="key">' +
    '<input type="text" class="hf-envv" value="'+esc(v)+'" style="width:50%" placeholder="ENV_VAR">' +
    '<button class="btn btn-d btn-s" onclick="this.parentElement.remove()">×</button></div>'
  ).join('');

  const extraArgs = (harness.extra_args||[]).join(', ');
  const availTools = (harness.available_tools||[]).join(', ');

  // Tool profiles section
  const tpEntries = Object.entries(harness.tool_profiles||{});
  const tpHtml = tpEntries.map(([name, tp]) => {
    const modeTag = tp.mode === 'keep_all' ? '🟢 keep_all' : tp.mode === 'strip_all' ? '🔴 strip_all' : '🟡 whitelist';
    const toolsList = (tp.tools||[]).join(', ');
    return '<div style="background:var(--bg);border:1px solid var(--bdr);border-radius:6px;padding:10px;margin-bottom:8px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center">' +
      '<b>' + esc(name) + '</b> <span class="tag">' + modeTag + '</span></div>' +
      '<div style="font-size:11px;color:var(--mu);margin-top:4px">' + esc(tp.description||'') + '</div>' +
      (toolsList ? '<div style="font-size:11px;color:var(--mu);margin-top:4px">Tools: ' + esc(toolsList) + '</div>' : '') +
      '</div>';
  }).join('');

  const html = `
    <div style="display:grid;gap:14px">
      <div style="display:grid;grid-template-columns:1fr 1fr 2fr;gap:12px">
        <div><label>Binary</label><input type="text" id="hf-binary" value="${esc(harness.binary||'')}" style="width:100%"></div>
        <div><label>Binary Path <span style="color:var(--mu)">(auto-detected)</span></label><input type="text" id="hf-binpath" value="${esc(harness.binary_path||'')}" style="width:100%" placeholder="(will resolve from PATH)"></div>
        <div style="font-size:11px;color:var(--mu);align-self:end;padding-bottom:8px">${harness.binary_path ? '✅ <code>' + esc(harness.binary_path) + '</code>' : '⚠️ No path resolved yet — click Scan System'}</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div><label>Launch Mode</label><select id="hf-lmode" style="width:100%">${lmOpts}</select></div>
        <div><label>Protocol</label><select id="hf-proto" style="width:100%">${prOpts}</select></div>
      </div>
      <div>
        <label>Env Map <button class="btn btn-g btn-s" style="margin-left:8px" onclick="addEnvRow()">+ Add</button></label>
        <div id="hf-envmap" style="margin-top:6px">${envRows}</div>
      </div>
      <div><label>Extra Args <span style="color:var(--mu)">(comma-separated)</span></label>
        <input type="text" id="hf-args" value="${esc(extraArgs)}" style="width:100%" placeholder="--flag, value"></div>
      <div style="border-top:1px solid var(--bdr);padding-top:12px">
        <label>Available Tools <button class="btn btn-g btn-s" style="margin-left:8px" onclick="discoverTools('${esc(slug)}')">🔍 Discover</button></label>
        <textarea id="hf-tools" style="width:100%;min-height:60px;font:12px monospace;background:var(--bg);border:1px solid var(--bdr);border-radius:6px;padding:8px;color:var(--tx);resize:vertical;margin-top:6px">${esc(availTools)}</textarea>
        <div style="font-size:11px;color:var(--mu)">Comma-separated. Use Discover to auto-capture from next request.</div>
      </div>
      <div style="border-top:1px solid var(--bdr);padding-top:12px">
        <label>Tool Profiles</label>
        <div style="margin-top:6px">${tpHtml || '<span class="empty" style="padding:10px">No profiles defined</span>'}</div>
        <div style="margin-top:8px;font-size:11px;color:var(--mu)">Edit tool profiles in the JSON view for advanced changes.</div>
      </div>
    </div>`;

  document.getElementById('mtitle').textContent = title;
  document.getElementById('med').style.display = 'none';
  document.getElementById('merr').style.display = 'none';

  let formDiv = document.getElementById('af-form');
  if (!formDiv) {
    formDiv = document.createElement('div');
    formDiv.id = 'af-form';
    document.querySelector('.mb').prepend(formDiv);
  }
  formDiv.innerHTML = html;
  formDiv.style.display = 'block';

  _saveFn = async function() {
    const envMap = {};
    document.querySelectorAll('.hf-env-row').forEach(row => {
      const k = row.querySelector('.hf-envk').value.trim();
      const v = row.querySelector('.hf-envv').value.trim();
      if (k) envMap[k] = v;
    });
    const argsRaw = document.getElementById('hf-args').value;
    const extraArgs = argsRaw.split(',').map(s=>s.trim()).filter(Boolean);
    const toolsRaw = document.getElementById('hf-tools').value;
    const availTools = toolsRaw.split(',').map(s=>s.trim()).filter(Boolean);

    const data = {
      name: slug,
      binary: document.getElementById('hf-binary').value.trim(),
      binary_path: document.getElementById('hf-binpath').value.trim(),
      launch_mode: document.getElementById('hf-lmode').value,
      speaks_protocol: document.getElementById('hf-proto').value,
      env_map: envMap,
      extra_args: extraArgs,
      available_tools: availTools,
      tool_profiles: harness.tool_profiles || {},
    };
    // Preserve config_template if it exists
    if (harness.config_template) data.config_template = harness.config_template;
    if (harness.config_file_path) data.config_file_path = harness.config_file_path;

    try {
      await api('PUT', '/api/harnesses/' + slug, data);
      toast(slug + ' saved');
      closeModal();
      loaders.harnesses();
    } catch(e) { toast(e.message, false); }
  };

  document.getElementById('msave').style.display = '';
  document.getElementById('msave').onclick = function() { _saveFn && _saveFn(); };
  document.getElementById('overlay').classList.add('on');
}

function addEnvRow() {
  const row = document.createElement('div');
  row.className = 'hf-env-row';
  row.style.cssText = 'display:flex;gap:8px;margin-bottom:6px';
  row.innerHTML = '<input type="text" class="hf-envk" value="" style="width:40%" placeholder="key">' +
    '<input type="text" class="hf-envv" value="" style="width:50%" placeholder="ENV_VAR">' +
    '<button class="btn btn-d btn-s" onclick="this.parentElement.remove()">×</button>';
  document.getElementById('hf-envmap').appendChild(row);
}

async function discoverTools(slug) {
  try {
    const result = await api('POST', '/api/harnesses/' + slug + '/discover-tools');
    if (result.source === 'captured' && result.tools && result.tools.length) {
      document.getElementById('hf-tools').value = result.tools.join(', ');
      toast('✅ Discovered ' + result.tools.length + ' tools from captured request');
    } else if (result.source === 'pending') {
      toast('⏳ Capture armed! Send one request through this harness, then click Discover again.\n' +
            '(Use any agent with this harness to trigger capture)', false);
    } else {
      toast('No tools found — send a request through this harness first', false);
    }
  } catch(e) { toast(e.message, false); }
}

// ── Tool Profiles ──────────────────────────────────────────────────────────

loaders.tools = loadTools;
async function loadTools() {
  try {
    const d = await api('GET', '/api/tool-profiles');
    document.getElementById('tools-ed').value = JSON.stringify(d, null, 2);
  } catch (e) { toast(e.message, false); }
}
async function saveTools() {
  try {
    const d = JSON.parse(document.getElementById('tools-ed').value);
    await api('PUT', '/api/tool-profiles', d);
    toast('Tool profiles saved');
  } catch (e) { toast(e.message, false); }
}

// ── API Keys ───────────────────────────────────────────────────────────────

loaders.keys = loadKeys;
async function loadKeys() {
  try {
    const data = await api('GET', '/api/keys');
    const entries = Object.entries(data);
    if (!entries.length) {
      document.getElementById('keys-list').innerHTML = '<p class="empty">No API key env vars found in provider profiles.</p>';
      return;
    }
    document.getElementById('keys-list').innerHTML = entries.map(([name, info]) =>
      '<div class="key-row">' +
        '<span class="kname">' + esc(name) + '</span>' +
        '<span class="tag ' + (info.set ? 'ok' : 'no') + '">' + (info.set ? 'set' : 'not set') + '</span>' +
        (info.in_file ? '<span class="tag ok" style="font-size:10px">in .env</span>' : '') +
        '<span class="kval">' + esc(info.masked || '—') + '</span>' +
        '<input type="password" data-key="' + esc(name) + '" placeholder="New value…" style="flex:1;min-width:200px">' +
      '</div>'
    ).join('');
  } catch (e) {
    document.getElementById('keys-list').innerHTML = '<p class="empty">' + esc(e.message) + '</p>';
  }
}
async function saveKeys() {
  const updates = {};
  document.querySelectorAll('#keys-list input[data-key]').forEach(inp => {
    if (inp.value.trim()) updates[inp.dataset.key] = inp.value.trim();
  });
  if (!Object.keys(updates).length) { toast('No new values entered'); return; }
  try {
    await api('PUT', '/api/keys', updates);
    toast('Keys saved to .env — restart router to apply');
    loadKeys();
  } catch (e) { toast(e.message, false); }
}

// ── Launch ─────────────────────────────────────────────────────────────────

let _lastCmd = '';
let _lastBashCmd = '';
loaders.launch = async function () {
  try {
    const list = await api('GET', '/api/agents');
    const sel = document.getElementById('launch-sel');
    const prev = sel.value;
    sel.innerHTML = '<option value="">— select agent —</option>' +
      list.map(d =>
        '<option value="' + esc(d._slug) + '"' + (d._slug === prev ? ' selected' : '') + '>' +
        esc((d.name || d._slug) + ' (' + d._slug + ')') + '</option>'
      ).join('');
    if (prev) showLaunch();
  } catch (e) { toast(e.message, false); }
};

async function showLaunch() {
  const slug = document.getElementById('launch-sel').value;
  const out = document.getElementById('launch-out');
  if (!slug) { out.innerHTML = ''; return; }
  try {
    const info = await api('GET', '/api/launch/' + slug);
    const envPairs = Object.entries(info.env);
    const binary = info.harness.binary || 'claude';
    const args = (info.harness.extra_args && info.harness.extra_args.length)
                  ? ' ' + info.harness.extra_args.join(' ') : '';

    // PowerShell format (Windows)
    const psCmd = envPairs.map(([k,v]) => '$env:' + k + '="' + v + '"').join('; ') +
                  '; ' + binary + args;
    // Bash format (Unix)
    const bashCmd = envPairs.map(([k,v]) => k + '="' + v + '"').join(' ') +
                    ' ' + binary + args;
    _lastCmd = psCmd;
    _lastBashCmd = bashCmd;

    const envHtml = envPairs.map(([k,v]) =>
      '<span class="ek">' + esc(k) + '</span>=<span class="ev">"' + esc(v) + '"</span>'
    ).join(' ');
    const argsHtml = (info.harness.extra_args || []).map(a => ' ' + esc(a)).join('');

    let configNote = '';
    if (info.config_note) {
      configNote = '<details style="margin-top:12px"><summary style="cursor:pointer;color:var(--mu);font-size:12px">Config file template (expand)</summary>' +
        '<pre style="margin-top:8px;font-size:11px;color:var(--mu);background:var(--bg);padding:12px;border-radius:6px;overflow-x:auto">' +
        esc(info.config_note) + '</pre></details>';
    }

    out.innerHTML =
      '<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">' +
        '<button class="btn btn-p" onclick="launchAgent(\'' + esc(slug) + '\')">🚀 Launch</button>' +
        '<button class="btn btn-g btn-s" onclick="copyLaunchCmd(\'ps\')">📋 PowerShell</button>' +
        '<button class="btn btn-g btn-s" onclick="copyLaunchCmd(\'bash\')">📋 Bash</button>' +
      '</div>' +
      '<p style="color:var(--mu);font-size:12px;margin-bottom:6px">PowerShell:</p>' +
      '<div class="cmd" style="font-size:11px">' + esc(psCmd) + '</div>' +
      '<p style="color:var(--mu);font-size:12px;margin:8px 0 4px">Bash / WSL:</p>' +
      '<div class="cmd" style="font-size:11px">' + esc(bashCmd) + '</div>' +
      '<p style="font-size:12px;color:var(--mu);margin:8px 0 12px">' +
        'Agent: <b>' + esc(info.agent.name || slug) + '</b> &nbsp;·&nbsp; ' +
        'Harness: <b>' + esc(info.agent.harness || '') + '</b> &nbsp;·&nbsp; ' +
        'Provider: <b>' + esc(info.agent.provider || '') + '</b> &nbsp;·&nbsp; ' +
        'Model: <code>' + esc(info.agent.model || '') + '</code>' +
      '</p>' +
      configNote;
  } catch (e) {
    out.innerHTML = '<p style="color:var(--er);font-size:13px">' + esc(e.message) + '</p>';
  }
}

function copyLaunchCmd(fmt) {
  const text = fmt === 'bash' ? _lastBashCmd : _lastCmd;
  if (text) navigator.clipboard.writeText(text).then(() => toast('Copied ' + fmt + ' command!'));
}

async function launchAgent(slug) {
  try {
    const result = await api('POST', '/api/launch/' + slug);
    if (result.success) {
      toast('🚀 ' + (result.binary || 'harness') + ' launched (PID: ' + (result.pid || '?') + ')');
    } else {
      toast('❌ Launch failed: ' + (result.error || result.stderr || 'unknown error'), false);
    }
  } catch(e) { toast(e.message, false); }
}


// ── Request Log ───────────────────────────────────────────────────────────

loaders.log = loadRequestLog;
async function loadRequestLog() {
  const tb = document.getElementById('tb-log');
  try {
    const log = await api('GET', '/api/request-log');
    if (!log.length) { tb.innerHTML = '<tr><td colspan="7" class="empty">No requests yet — send a request through any agent</td></tr>'; return; }
    tb.innerHTML = log.map(r => {
      const modelChanged = r.model_from_harness !== r.model_sent;
      return '<tr>' +
        '<td><code>' + esc(r.ts) + '</code></td>' +
        '<td>' + esc(r.agent) + '</td>' +
        '<td><span class="tag">' + esc(r.harness) + '</span></td>' +
        '<td style="color:var(--mu)">' + esc(r.model_from_harness || '(none)') + '</td>' +
        '<td>' + (modelChanged ? '✅' : '➖') + '</td>' +
        '<td style="font-weight:' + (modelChanged ? '600' : 'normal') + '">' + esc(r.model_sent) + '</td>' +
        '<td><span class="tag">' + esc(r.provider) + '</span></td>' +
        '</tr>';
    }).join('');
  } catch(e) { tb.innerHTML = '<tr><td colspan="7" class="empty">' + esc(e.message) + '</td></tr>'; }
}

// ── Agent Form Editor ──────────────────────────────────────────────────────

async function editAgentForm(slug) {
  const [opts, agent] = await Promise.all([
    loadFormOpts(),
    slug ? api('GET', '/api/agents/' + slug) : Promise.resolve({})
  ]);
  openAgentFormModal(slug, agent, opts);
}

async function newAgentForm() {
  const opts = await loadFormOpts();
  openAgentFormModal(null, {harness:'claude-code',provider:'openrouter',tool_profile:'coding',fusion:null}, opts);
}

function modelShortName(fullId) {
  // "nvidia/nemotron-3-ultra:free" → "nemotron-3-ultra:free"
  const idx = (fullId || '').indexOf('/');
  return idx >= 0 ? fullId.slice(idx + 1) : fullId;
}

function openAgentFormModal(slug, agent, opts) {
  const isNew = !slug;
  const title = isNew ? 'New Agent' : 'Edit: ' + slug;
  const hasFusion = (agent.model || '').includes('fusion');

  const hOpts = opts.harnesses.map(h => '<option value="'+esc(h)+'"'+(agent.harness===h?' selected':'')+'>'+esc(h)+'</option>').join('');
  const pOpts = opts.providers.map(p => '<option value="'+esc(p)+'"'+(agent.provider===p?' selected':'')+'>'+esc(p)+'</option>').join('');
  // Build tool profile options from harness-specific profiles (if available)
  const harnessToolProfiles = (opts.harness_tool_profiles && opts.harness_tool_profiles[agent.harness]) || opts.tool_profiles;
  const tOpts = harnessToolProfiles.map(t => '<option value="'+esc(t)+'"'+(agent.tool_profile===t?' selected':'')+'>'+esc(t)+'</option>').join('');

  const fusionAnalysis = (agent.fusion && agent.fusion.analysis_models) ? agent.fusion.analysis_models.join(', ') : '';
  const fusionJudge = (agent.fusion && agent.fusion.model) ? agent.fusion.model : '';

  const html = `
    <div style="display:grid;gap:14px">
      <div><label>Profile Name</label><input type="text" id="af-name" value="${esc(agent.name||'')}" style="width:100%" placeholder="Claude Open Solar"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
        <div><label>Harness</label><select id="af-harness" style="width:100%" onchange="onHarnessChange()">${hOpts}</select></div>
        <div><label>Provider</label><select id="af-provider" style="width:100%" onchange="onProviderChange()">${pOpts}</select></div>
        <div><label>Tool Profile</label><select id="af-tools" style="width:100%">${tOpts}</select></div>
      </div>
      <div><label>Model <span style="color:var(--mu)">(type to filter — models load when provider is selected)</span></label>
        <input type="text" id="af-model-search" value="" style="width:100%;margin-bottom:6px" placeholder="Search models..." oninput="filterModels()">
        <select id="af-model" style="width:100%;height:140px" size="8" onchange="onModelChange()">
          <option value="">Select provider first...</option>
        </select>
        <input type="hidden" id="af-model-val" value="${esc(agent.model||'')}">
        <div style="margin-top:4px;font-size:11px;color:var(--mu)" id="af-model-info">Current: <code>${esc(agent.model||'none')}</code></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div><label>Max Tokens <span style="color:var(--mu)">(0 = no cap)</span></label><input type="number" id="af-maxtok" value="${agent.max_tokens||0}" style="width:100%"></div>
      </div>
      <div id="af-fusion-section" style="border-top:1px solid var(--bdr);padding-top:12px;display:${hasFusion?'block':'none'}">
        <p style="color:var(--ac);font-size:13px;margin-bottom:10px">⚡ Fusion Panel Configuration</p>
        <div style="margin-bottom:10px"><label>Judge Model</label>
          <input type="text" id="af-fusion-judge" value="${esc(fusionJudge)}" style="width:100%" placeholder="anthropic/claude-opus-4-8">
        </div>
        <div><label>Analysis Models <span style="color:var(--mu)">(comma-separated)</span></label>
          <input type="text" id="af-fusion-analysis" value="${esc(fusionAnalysis)}" style="width:100%" placeholder="model-1, model-2, model-3">
        </div>
      </div>
    </div>`;

  document.getElementById('mtitle').textContent = title;
  document.getElementById('med').style.display = 'none';
  document.getElementById('merr').style.display = 'none';

  let formDiv = document.getElementById('af-form');
  if (!formDiv) {
    formDiv = document.createElement('div');
    formDiv.id = 'af-form';
    document.querySelector('.mb').prepend(formDiv);
  }
  formDiv.innerHTML = html;
  formDiv.style.display = 'block';

  // Auto-load models for current provider (delayed to avoid overlay click race)
  setTimeout(() => onProviderChange(), 100);

  // Save handler
  _saveFn = async function() {
    const modelVal = document.getElementById('af-model-val').value.trim() || document.getElementById('af-model').value;
    const data = {
      name: document.getElementById('af-name').value.trim(),
      harness: document.getElementById('af-harness').value,
      provider: document.getElementById('af-provider').value,
      model: modelVal,
      tool_profile: document.getElementById('af-tools').value,
    };
    const mt = parseInt(document.getElementById('af-maxtok').value);
    if (mt > 0) data.max_tokens = mt;
    // Auto-detect fusion
    if (modelVal.includes('fusion')) {
      const analysisRaw = document.getElementById('af-fusion-analysis').value;
      data.fusion = {
        id: 'fusion',
        analysis_models: analysisRaw.split(',').map(s=>s.trim()).filter(Boolean),
        model: document.getElementById('af-fusion-judge').value.trim()
      };
    } else {
      data.fusion = null;
    }
    if (!data.name) { toast('Name required', false); return; }
    if (!data.model) { toast('Model required', false); return; }
    try {
      if (isNew) {
        const s = data.name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        if (!s) { toast('Name required (used to generate slug)', false); return; }
        data.slug = s;
        await api('POST', '/api/agents', data);
        toast('Created ' + s);
      } else {
        await api('PUT', '/api/agents/' + slug, data);
        toast(slug + ' saved');
      }
      closeModal();
      loaders.agents();
    } catch(e) { toast(e.message, false); }
  };

  document.getElementById('msave').style.display = '';
  document.getElementById('msave').onclick = function() { _saveFn && _saveFn(); };
  document.getElementById('overlay').classList.add('on');
}


// When harness changes, reload tool profile options for that harness
async function onHarnessChange() {
  const harness = document.getElementById('af-harness').value;
  const sel = document.getElementById('af-tools');
  const currentTP = sel.value;
  try {
    const opts = await loadFormOpts(true);
    const profiles = (opts.harness_tool_profiles && opts.harness_tool_profiles[harness]) || opts.tool_profiles || [];
    sel.innerHTML = profiles.map(t =>
      '<option value="'+esc(t)+'"'+(t===currentTP?' selected':'')+'>'+esc(t)+'</option>'
    ).join('');
  } catch(e) { /* keep existing options */ }
}

// Model list management
let _modelCache = {}; // provider → models array

let _modalLoading = false;
async function onProviderChange() {
  const provider = document.getElementById('af-provider').value;
  const sel = document.getElementById('af-model');
  const currentVal = document.getElementById('af-model-val').value;
  sel.innerHTML = '<option value="">Loading models...</option>';
  _modalLoading = true;

  try {
    let models;
    if (_modelCache[provider]) {
      models = _modelCache[provider];
    } else if (provider === 'openrouter') {
      models = await loadModels();
      _modelCache[provider] = models;
    } else {
      // For non-OpenRouter providers, show a text input instead
      sel.innerHTML = '<option value="">(Enter model ID manually for this provider)</option>';
      _modalLoading = false;
      return;
    }
    renderModelList(models, currentVal);
  } catch(e) {
    sel.innerHTML = '<option value="">Error loading models: ' + esc(e.message) + '</option>';
  } finally {
    _modalLoading = false;
  }
}

function renderModelList(models, selectedVal) {
  const sel = document.getElementById('af-model');
  const search = (document.getElementById('af-model-search').value || '').toLowerCase();
  const filtered = search ? models.filter(m => m.id.toLowerCase().includes(search) || (m.name||'').toLowerCase().includes(search)) : models;
  const shown = filtered.slice(0, 100); // Limit for performance

  sel.innerHTML = shown.map(m => {
    const short = modelShortName(m.id);
    const label = (m.free ? '🆓 ' : '💰 ') + short + (m.tools ? ' 🔧' : '') +
      (m.context ? ' [' + Math.round(m.context/1000) + 'K]' : '');
    const isSelected = m.id === selectedVal ? ' selected' : '';
    return '<option value="' + esc(m.id) + '"' + isSelected + '>' + esc(label) + '</option>';
  }).join('');

  if (shown.length < filtered.length) {
    sel.innerHTML += '<option disabled>... ' + (filtered.length - shown.length) + ' more (type to filter)</option>';
  }
  if (!shown.length) {
    sel.innerHTML = '<option value="">No models match "' + esc(search) + '"</option>';
  }
}

function filterModels() {
  const provider = document.getElementById('af-provider').value;
  const models = _modelCache[provider];
  if (models) {
    const currentVal = document.getElementById('af-model-val').value;
    renderModelList(models, currentVal);
  }
}

function onModelChange() {
  const sel = document.getElementById('af-model');
  const val = sel.value;
  if (val) {
    document.getElementById('af-model-val').value = val;
    document.getElementById('af-model-info').innerHTML = 'Selected: <code>' + esc(val) + '</code>';
    // Auto-show/hide fusion section
    const fusionSec = document.getElementById('af-fusion-section');
    if (val.includes('fusion')) {
      fusionSec.style.display = 'block';
    } else {
      fusionSec.style.display = 'none';
    }
  }
}

// ── Generic CRUD ───────────────────────────────────────────────────────────

const TMPL = {
  agents: {
    _slug: 'my-agent', name: 'My Agent',
    harness: 'claude-code', provider: 'openrouter',
    model: 'openrouter/auto', tool_profile: 'coding'
  },
  providers: {
    _slug: 'my-provider', name: 'My Provider',
    base_url: 'https://api.example.com',
    api_key_env: 'EXAMPLE_API_KEY',
    endpoints: { openai: '/v1/chat/completions' }
  },
  harnesses: {
    _slug: 'my-harness', name: 'my-harness',
    binary: 'my-harness',
    launch_mode: 'env',
    speaks_protocol: 'openai',
    env_map: { base_url: 'OPENAI_BASE_URL', auth_token: 'OPENAI_API_KEY' },
    extra_args: []
  },
};

async function editItem(type, slug) {
  try {
    const d = await api('GET', '/api/' + type + '/' + slug);
    d._slug = slug;
    openModal('Edit: ' + slug, d, async upd => {
      const body = {};
      for (const [k,v] of Object.entries(upd)) { if (!k.startsWith('_')) body[k] = v; }
      await api('PUT', '/api/' + type + '/' + slug, body);
      toast(slug + ' saved');
      closeModal();
      if (loaders[type]) loaders[type]();
    });
  } catch (e) { toast(e.message, false); }
}

async function viewItem(type, slug) {
  try {
    const d = await api('GET', '/api/' + type + '/' + slug);
    openModal('View: ' + slug, d, null);
  } catch (e) { toast(e.message, false); }
}

function newItem(type) {
  if (type === 'agents') { newAgentForm(); return; }
  const tmpl = JSON.parse(JSON.stringify(TMPL[type] || { _slug: 'new-item' }));
  openModal('New ' + type.slice(0, -1), tmpl, async data => {
    const slug = String(data._slug || '').trim().toLowerCase().replace(/\s+/g, '-');
    if (!slug) { toast('_slug field required', false); return; }
    const body = { slug };
    for (const [k,v] of Object.entries(data)) { if (!k.startsWith('_')) body[k] = v; }
    await api('POST', '/api/' + type, body);
    toast('Created ' + slug);
    closeModal();
    if (loaders[type]) loaders[type]();
  });
}

async function delItem(type, slug) {
  if (!confirm('Delete "' + slug + '"?\nThis cannot be undone.')) return;
  try {
    await api('DELETE', '/api/' + type + '/' + slug);
    toast(slug + ' deleted');
    if (loaders[type]) loaders[type]();
  } catch (e) { toast(e.message, false); }
}

// ── Init ───────────────────────────────────────────────────────────────────
loaders.status();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Flask route registration
# ─────────────────────────────────────────────────────────────────────────────

def register_dashboard(app, base_dir):
    """Register all dashboard routes on the Flask app.

    Args:
        app:      the Flask application instance
        base_dir: root directory of the ai-router project (Path or str)
    """
    base = Path(base_dir)
    agents_dir    = base / "profiles" / "agents"
    providers_dir = base / "profiles" / "providers"
    harnesses_dir = base / "profiles" / "harnesses"
    tool_file     = base / "profiles" / "tool-profiles.json"
    env_file      = base / ".env"

    # ── helpers ───────────────────────────────────────────────────────────────

    def _find_binary_fallback(binary_name):
        """Search common install locations for a binary not on PATH."""
        import platform
        candidates = []
        if platform.system() == "Windows":
            # pip user-site Scripts
            user_home = Path.home()
            for py_ver in ["Python312", "Python311", "Python310", "Python39"]:
                candidates.append(user_home / "AppData" / "Roaming" / "Python" / py_ver / "Scripts" / f"{binary_name}.exe")
            # pip global Scripts
            for prefix in [Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")]:
                for py_ver in ["Python312", "Python311", "Python310", "Python39"]:
                    candidates.append(prefix / py_ver / "Scripts" / f"{binary_name}.exe")
            # npm global
            candidates.append(user_home / "AppData" / "Roaming" / "npm" / f"{binary_name}.cmd")
            candidates.append(user_home / "AppData" / "Roaming" / "npm" / f"{binary_name}.exe")
            # Programs directory (direct binary installs like opencode)
            local_app_data = Path(os.environ.get("LOCALAPPDATA", user_home / "AppData" / "Local"))
            candidates.append(local_app_data / "Programs" / binary_name / f"{binary_name}.exe")
            # Nested package directory (e.g. goose-package/goose.exe)
            candidates.append(local_app_data / "Programs" / binary_name / f"{binary_name}-package" / f"{binary_name}.exe")
        else:
            # Unix pip user
            candidates.append(Path.home() / ".local" / "bin" / binary_name)
            # Unix global
            candidates.append(Path("/usr/local/bin") / binary_name)

        for p in candidates:
            if p.exists():
                return str(p)
        return None

    def _list_dir(d: Path):
        result = []
        for p in sorted(d.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                data["_slug"] = p.stem
                result.append(data)
            except Exception:
                result.append({"_slug": p.stem, "name": p.stem})
        return result

    def _read_one(d: Path, slug: str):
        p = d / f"{slug}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def _save_one(d: Path, slug: str, data: dict):
        clean = {k: v for k, v in data.items() if not k.startswith("_")}
        (d / f"{slug}.json").write_text(json.dumps(clean, indent=2), encoding="utf-8")

    def _read_env():
        if not env_file.exists():
            return {}
        result = {}
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip().strip('"').strip("'")
        return result

    def _write_env(updates: dict):
        lines = []
        existing = {}  # key → line index
        if env_file.exists():
            for i, line in enumerate(env_file.read_text(encoding="utf-8").splitlines()):
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k, _, _ = s.partition("=")
                    existing[k.strip()] = i
                lines.append(line)
        for key, value in updates.items():
            if key in existing:
                lines[existing[key]] = f"{key}={value}"
            else:
                lines.append(f"{key}={value}")
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _crud_routes(url_prefix: str, directory: Path):
        """Register GET-list, GET-one, PUT, POST, DELETE for a profile directory."""

        @app.route(url_prefix, methods=["GET"], endpoint=f"list_{url_prefix.strip('/')}")
        def _list():
            return jsonify(_list_dir(directory))

        @app.route(f"{url_prefix}/<slug>", methods=["GET"], endpoint=f"get_{url_prefix.strip('/')}")
        def _get(slug):
            d = _read_one(directory, slug)
            if d is None:
                return jsonify({"error": "Not found"}), 404
            return jsonify(d)

        @app.route(f"{url_prefix}/<slug>", methods=["PUT"], endpoint=f"put_{url_prefix.strip('/')}")
        def _put(slug):
            p = directory / f"{slug}.json"
            if not p.exists():
                return jsonify({"error": "Not found"}), 404
            _save_one(directory, slug, request.get_json(force=True))
            return jsonify({"ok": True})

        @app.route(url_prefix, methods=["POST"], endpoint=f"post_{url_prefix.strip('/')}")
        def _post():
            data = request.get_json(force=True)
            slug = re.sub(r"\s+", "-", (data.get("slug") or data.get("_slug") or "").strip().lower())
            if not slug:
                return jsonify({"error": "slug required"}), 400
            p = directory / f"{slug}.json"
            if p.exists():
                return jsonify({"error": f"'{slug}' already exists"}), 409
            _save_one(directory, slug, {k: v for k, v in data.items() if k not in ("slug", "_slug")})
            return jsonify({"ok": True, "slug": slug}), 201

        @app.route(f"{url_prefix}/<slug>", methods=["DELETE"], endpoint=f"del_{url_prefix.strip('/')}")
        def _del(slug):
            p = directory / f"{slug}.json"
            if not p.exists():
                return jsonify({"error": "Not found"}), 404
            p.unlink()
            return jsonify({"ok": True})

    # ── UI ────────────────────────────────────────────────────────────────────

    @app.route("/ui")
    @app.route("/ui/")
    def dashboard_ui():
        return DASHBOARD_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}

    # ── Status ────────────────────────────────────────────────────────────────

    @app.route("/api/status")
    def api_status():
        return jsonify({
            "status": "running",
            "agents":    len(list(agents_dir.glob("*.json"))),
            "providers": len(list(providers_dir.glob("*.json"))),
            "harnesses": len(list(harnesses_dir.glob("*.json"))),
        })

    # ── Profile CRUD ──────────────────────────────────────────────────────────

    _crud_routes("/api/agents",    agents_dir)
    _crud_routes("/api/providers", providers_dir)
    _crud_routes("/api/harnesses", harnesses_dir)

    # ── Tool profiles ─────────────────────────────────────────────────────────

    @app.route("/api/tool-profiles", methods=["GET"])
    def get_tool_profiles():
        if not tool_file.exists():
            return jsonify({})
        return jsonify(json.loads(tool_file.read_text(encoding="utf-8")))

    @app.route("/api/tool-profiles", methods=["PUT"])
    def put_tool_profiles():
        tool_file.write_text(json.dumps(request.get_json(force=True), indent=2), encoding="utf-8")
        return jsonify({"ok": True})

    # ── API Keys ──────────────────────────────────────────────────────────────

    @app.route("/api/keys", methods=["GET"])
    def get_keys():
        known = set()
        for p in providers_dir.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                if "api_key_env" in d:
                    known.add(d["api_key_env"])
            except Exception:
                pass

        file_vals = _read_env()
        result = {}
        for var in sorted(known | set(file_vals)):
            val = os.environ.get(var) or file_vals.get(var, "")
            if val:
                n = len(val)
                masked = (val[:4] + "·" * min(n - 8, 12) + val[-4:]) if n > 8 else "****"
                result[var] = {"set": True, "masked": masked, "in_file": var in file_vals}
            else:
                result[var] = {"set": False, "masked": "", "in_file": False}
        return jsonify(result)

    @app.route("/api/keys", methods=["PUT"])
    def put_keys():
        _write_env(request.get_json(force=True))
        return jsonify({"ok": True})

    # ── Launch ────────────────────────────────────────────────────────────────

    @app.route("/api/launch/<slug>")
    def get_launch(slug):
        agent = _read_one(agents_dir, slug)
        # Fallback: search by display name if slug file not found
        if agent is None:
            search_name = slug.replace('-', ' ').lower()
            for p in agents_dir.glob('*.json'):
                try:
                    data = json.loads(p.read_text(encoding='utf-8'))
                    if data.get('name', '').lower() == search_name:
                        agent = data
                        slug = p.stem
                        break
                except Exception:
                    pass
        if agent is None:
            return jsonify({"error": "Agent not found"}), 404

        harness_name = agent.get("harness", "")
        harness = _read_one(harnesses_dir, harness_name)
        if harness is None:
            return jsonify({"error": f"Harness '{harness_name}' not found"}), 404

        protocol = harness.get("speaks_protocol", "anthropic")
        router_base = "http://127.0.0.1:3459"
        # Anthropic SDK appends /v1/messages; OpenAI SDK appends /chat/completions
        base_url_val = router_base if protocol == "anthropic" else f"{router_base}/v1"

        env_map = harness.get("env_map", {})
        env_vals = {}
        if "base_url"   in env_map: env_vals[env_map["base_url"]]   = base_url_val
        if "auth_token" in env_map: env_vals[env_map["auth_token"]] = slug

        # For config-file harnesses, render the template for display
        config_note = None
        if harness.get("config_template"):
            try:
                tpl = json.dumps(harness["config_template"], indent=2)
                tpl = tpl.replace("{{base_url}}", base_url_val)
                tpl = tpl.replace("{{model}}", agent.get("model", ""))
                config_note = (
                    f"Write to: {harness.get('config_file_path', 'opencode.json')}\n\n{tpl}"
                )
            except Exception:
                pass

        return jsonify({
            "agent":       agent,
            "harness":     harness,
            "env":         env_vals,
            "config_note": config_note,
        })

    @app.route("/api/launch/<slug>", methods=["POST"])
    def post_launch(slug):
        """Launch a harness process for the given agent profile."""
        import subprocess
        import shutil

        agent = _read_one(agents_dir, slug)
        # Fallback: search by display name if slug file not found
        if agent is None:
            search_name = slug.replace('-', ' ').lower()
            for p in agents_dir.glob('*.json'):
                try:
                    data = json.loads(p.read_text(encoding='utf-8'))
                    if data.get('name', '').lower() == search_name:
                        agent = data
                        slug = p.stem
                        break
                except Exception:
                    pass
        if agent is None:
            return jsonify({"error": "Agent not found"}), 404

        harness_name = agent.get("harness", "")
        harness = _read_one(harnesses_dir, harness_name)
        if harness is None:
            return jsonify({"error": f"Harness '{harness_name}' not found"}), 404

        is_native = agent.get("native", False)

        binary = harness.get("binary", "")
        binary_path = harness.get("binary_path", "") or shutil.which(binary)
        # If not on PATH, search common pip/npm install locations
        if not binary_path:
            binary_path = _find_binary_fallback(binary)
        if not binary_path:
            return jsonify({"error": f"Binary '{binary}' not found on PATH or common install locations. "
                            f"You may need to add the install directory to your PATH.", "success": False}), 400

        # Build environment variables
        protocol = harness.get("speaks_protocol", "anthropic")
        router_base = "http://127.0.0.1:3459"
        # Some harnesses (e.g. Goose) append /v1 themselves — respect base_url_no_v1 flag
        if harness.get("base_url_no_v1"):
            base_url_val = router_base
        elif protocol == "anthropic":
            base_url_val = router_base
        else:
            base_url_val = f"{router_base}/v1"

        env_map = harness.get("env_map", {})
        launch_env = dict(os.environ)
        # Add any path_additions to PATH (e.g. Node.js for dsh)
        if harness.get("path_additions"):
            import platform as _plat
            sep = ";" if _plat.system() == "Windows" else ":"
            launch_env["PATH"] = sep.join(harness["path_additions"]) + sep + launch_env.get("PATH", "")
        if not is_native:
            if "base_url"   in env_map: launch_env[env_map["base_url"]]   = base_url_val
            if "auth_token" in env_map: launch_env[env_map["auth_token"]] = slug

        # For config-file harnesses, write the config file before launching
        if harness.get("config_file_path") and (harness.get("config_template") or harness.get("config_template_raw")):
            try:
                if harness.get("config_template_raw"):
                    # Raw template (TOML, YAML, etc.) — just string replace
                    tpl = harness["config_template_raw"]
                else:
                    # JSON template
                    tpl = json.dumps(harness["config_template"], indent=2)
                tpl = tpl.replace("{{base_url}}", base_url_val)
                tpl = tpl.replace("{{model}}", agent.get("model", ""))
                tpl = tpl.replace("{{auth_token}}", slug)
                config_path = Path(harness["config_file_path"]).expanduser()
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(tpl, encoding="utf-8")
            except Exception as e:
                return jsonify({"error": f"Failed to write config: {e}", "success": False}), 500

        # Build command — open in a NEW TERMINAL so the user can interact
        import platform
        is_windows = platform.system() == "Windows"


        extra_args = harness.get("extra_args", [])
        # Replace template placeholders in extra_args
        extra_args = [a.replace("{{model}}", agent.get("model", ""))
                       .replace("{{base_url}}", base_url_val)
                       .replace("{{auth_token}}", slug)
                      for a in extra_args]
        args_str = ' '.join(extra_args) if extra_args else ''

        try:
            if is_windows:
                # Write a temp .ps1 script (avoids all Start-Process quoting hell)
                debug_dir = base / "debug"
                debug_dir.mkdir(exist_ok=True)
                script_path = debug_dir / f"launch_{slug}.ps1"

                ps_lines = [f"# AI Router Launch Script for: {slug}"]
                if not is_native:
                    if "base_url" in env_map:
                        ps_lines.append(f'$env:{env_map["base_url"]} = "{base_url_val}"')
                    if "auth_token" in env_map:
                        ps_lines.append(f'$env:{env_map["auth_token"]} = "{slug}"')
                ps_lines.append('Write-Host ""')
                if is_native:
                    ps_lines.append(f'Write-Host "[AI Router] Launching {binary_path} (native mode)" -ForegroundColor Magenta')
                else:
                    ps_lines.append(f'Write-Host "[AI Router] Launching {binary_path} with:" -ForegroundColor Cyan')
                    if "base_url" in env_map:
                        ps_lines.append(f'Write-Host "  {env_map["base_url"]} = {base_url_val}" -ForegroundColor Green')
                    if "auth_token" in env_map:
                        ps_lines.append(f'Write-Host "  {env_map["auth_token"]} = {slug}" -ForegroundColor Green')
                    if harness.get("config_file_path"):
                        ps_lines.append(f'Write-Host "  Config written: {harness["config_file_path"]}" -ForegroundColor Yellow')
                    model_val = agent.get("model", "")
                    if model_val:
                        ps_lines.append(f'Write-Host "  Model override: {model_val}" -ForegroundColor Yellow')
                ps_lines.append('Write-Host ""')
                ps_lines.append(f'{binary_path} {args_str}'.strip())
                script_path.write_text('\n'.join(ps_lines), encoding="utf-8")

                # Launch PowerShell with the script in a new window
                proc = subprocess.Popen(
                    ['powershell', '-Command',
                     f'Start-Process powershell -ArgumentList \"-NoExit\",\"-File\",\"{script_path}\"'],
                    env=launch_env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                # Unix: try common terminal emulators
                env_prefix = ' '.join(f'{k}="{v}"' for k, v in [
                    (env_map.get("base_url", ""), base_url_val),
                    (env_map.get("auth_token", ""), slug)
                ] if k)
                full_shell_cmd = f'{env_prefix} {binary_path} {args_str}'

                # Try terminal emulators in order of preference
                import shutil as _shutil
                for term_cmd in [
                    ['gnome-terminal', '--', 'bash', '-c', full_shell_cmd + '; exec bash'],
                    ['xterm', '-e', full_shell_cmd],
                    ['bash', '-c', full_shell_cmd],  # fallback: run in background
                ]:
                    if _shutil.which(term_cmd[0]):
                        proc = subprocess.Popen(
                            term_cmd, env=launch_env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                        break
                else:
                    return jsonify({"error": "No terminal emulator found", "success": False}), 400

            return jsonify({
                "success": True,
                "pid": proc.pid,
                "binary": binary_path,
                "message": f"Opened {binary_path} in a new terminal window",
                "env_set": {k: v for k, v in [(env_map.get("base_url", ""), base_url_val),
                                               (env_map.get("auth_token", ""), slug)] if k},
            })
        except FileNotFoundError:
            return jsonify({"error": f"Binary not found: {binary_path or binary}", "success": False}), 400
        except Exception as e:
            return jsonify({"error": str(e), "success": False}), 500


    # ── OpenRouter Models (cached) ────────────────────────────────────────────

    _models_cache = {"data": None, "ts": 0}

    @app.route("/api/openrouter-models")
    def get_openrouter_models():
        import time
        now = time.time()
        # Cache for 10 minutes
        if _models_cache["data"] and (now - _models_cache["ts"]) < 600:
            return jsonify(_models_cache["data"])
        try:
            import requests as req
            r = req.get("https://openrouter.ai/api/v1/models", timeout=10)
            models = r.json().get("data", [])
            result = []
            for m in models:
                supported = m.get("supported_parameters", [])
                pricing = m.get("pricing", {})
                result.append({
                    "id": m["id"],
                    "name": m.get("name", m["id"]),
                    "context": m.get("context_length", 0),
                    "tools": "tools" in supported or "tool_choice" in supported,
                    "free": float(pricing.get("prompt", "1")) == 0,
                    "prompt_cost": float(pricing.get("prompt", "0")) * 1000000,
                    "completion_cost": float(pricing.get("completion", "0")) * 1000000,
                })
            result.sort(key=lambda x: (0 if x["free"] else 1, x["prompt_cost"]))
            _models_cache["data"] = result
            _models_cache["ts"] = now
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ── Discover tools ─────────────────────────────────────────────────────

    @app.route("/api/harnesses/<slug>/discover-tools", methods=["POST"])
    def discover_tools(slug):
        """Discover tools for a harness.

        Reads from per-harness debug file (written by router on each request).
        If no per-harness data exists, auto-launches the harness with a free model
        so the user only needs to send one message to capture tools.
        """
        import subprocess
        import platform

        harness_path = harnesses_dir / f"{slug}.json"
        if not harness_path.exists():
            return jsonify({"error": "Harness not found"}), 404

        # Read from per-harness debug file (written by router on each request)
        debug_dir = base / "debug"
        debug_file = debug_dir / f"tools_{slug}.json"
        tools = []

        if debug_file.exists():
            try:
                debug_data = json.loads(debug_file.read_text(encoding="utf-8"))
                tools = debug_data.get("tools", [])
            except Exception:
                pass

        if tools:
            # Save back to harness profile
            harness_data = json.loads(harness_path.read_text(encoding="utf-8"))
            harness_data["available_tools"] = sorted(set(tools))
            harness_path.write_text(json.dumps(harness_data, indent=2), encoding="utf-8")
            return jsonify({"tools": sorted(set(tools)), "count": len(tools), "source": "captured"})
        # Check if harness uses tools at all
        harness_data = json.loads(harness_path.read_text(encoding="utf-8"))
        if harness_data.get("uses_tools") is False:
            return jsonify({
                "tools": [],
                "count": 0,
                "source": "not_applicable",
                "message": f"Harness '{slug}' does not use function calling / tools API. "
                           f"It uses text-based edit formats instead. Tool discovery is not applicable."
            })


        # No per-harness data yet — fully automated probe
        # Launch harness as background subprocess, pipe a prompt, wait for tools
        harness_data = json.loads(harness_path.read_text(encoding="utf-8"))
        harness_data["available_tools"] = []  # Reset to trigger auto-capture
        harness_path.write_text(json.dumps(harness_data, indent=2), encoding="utf-8")

        # Find or create a temporary probe agent for this harness
        probe_slug = f"_probe-{slug}"
        probe_model = "nvidia/nemotron-3-ultra-550b-a55b:free"
        probe_file = agents_dir / f"{probe_slug}.json"
        probe_agent = {
            "name": f"Probe ({slug})",
            "harness": slug,
            "provider": "openrouter",
            "model": probe_model,
            "tool_profile": "full",
            "fusion": None,
        }
        probe_file.write_text(json.dumps(probe_agent, indent=2), encoding="utf-8")

        # Resolve binary
        import shutil
        harness = harness_data
        binary = harness.get("binary", "")
        binary_path = harness.get("binary_path", "") or shutil.which(binary) or _find_binary_fallback(binary)

        if not binary_path:
            return jsonify({
                "tools": [],
                "count": 0,
                "source": "error",
                "message": f"Binary '{binary}' not found. Install the harness first."
            })

        # Build launch environment
        protocol = harness.get("speaks_protocol", "openai")
        router_base = "http://127.0.0.1:3459"
        # Respect base_url_no_v1 flag (e.g. Goose appends /v1 itself)
        if harness.get("base_url_no_v1"):
            base_url_val = router_base
        elif protocol == "anthropic":
            base_url_val = router_base
        else:
            base_url_val = f"{router_base}/v1"

        env_map = harness.get("env_map", {})
        launch_env = dict(os.environ)
        # Add any path_additions to PATH (e.g. Node.js for dsh)
        if harness.get("path_additions"):
            import platform
            sep = ";" if platform.system() == "Windows" else ":"
            launch_env["PATH"] = sep.join(harness["path_additions"]) + sep + launch_env.get("PATH", "")
        if "base_url" in env_map:
            launch_env[env_map["base_url"]] = base_url_val
        if "auth_token" in env_map:
            launch_env[env_map["auth_token"]] = probe_slug
        # Additional env vars for probe (e.g. GEMINI_CLI_TRUST_WORKSPACE)
        if harness.get("probe_env"):
            launch_env.update(harness["probe_env"])

        # For config-file harnesses, write the config
        if harness.get("config_file_path") and (harness.get("config_template") or harness.get("config_template_raw")):
            try:
                if harness.get("config_template_raw"):
                    tpl = harness["config_template_raw"]
                else:
                    tpl = json.dumps(harness["config_template"], indent=2)
                tpl = tpl.replace("{{base_url}}", base_url_val)
                tpl = tpl.replace("{{model}}", probe_model)
                tpl = tpl.replace("{{auth_token}}", probe_slug)
                config_path = Path(harness["config_file_path"]).expanduser()
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(tpl, encoding="utf-8")
            except Exception:
                pass

        # Build command: probe_override_args replaces extra_args+probe_args entirely
        if harness.get("probe_override_args"):
            probe_cmd_args = harness["probe_override_args"]
        else:
            extra_args = harness.get("extra_args", [])
            extra_args = [a.replace("{{model}}", probe_model)
                           .replace("{{base_url}}", base_url_val)
                           .replace("{{auth_token}}", probe_slug)
                          for a in extra_args]
            probe_args = harness.get("probe_args", [])
            probe_cmd_args = extra_args + probe_args
        cmd_list = [binary_path] + probe_cmd_args

        # Launch harness as background process
        import time
        debug_dir = base / "debug"
        debug_dir.mkdir(exist_ok=True)
        debug_file = debug_dir / f"tools_{slug}.json"

        # Remove stale debug file to ensure fresh capture
        if debug_file.exists():
            debug_file.unlink()

        proc = None
        try:
            # Use shell=True for .cmd files on Windows
            use_shell = binary_path.endswith('.cmd')
            proc = subprocess.Popen(
                cmd_list if not use_shell else ' '.join(cmd_list),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=launch_env,
                cwd=str(base),
                shell=use_shell,
            )

            # If no probe_args with a message/text flag, pipe stdin as fallback
            has_message_flag = any(f in probe_cmd_args for f in ["--message", "--text", "run", "hi"])
            if not has_message_flag:
                time.sleep(3)
                if proc.poll() is None:
                    try:
                        proc.stdin.write(b"hi\n")
                        proc.stdin.flush()
                    except Exception:
                        pass

            # Poll for tools capture (router writes debug file on request)
            captured_tools = []
            timeout_secs = harness.get("discover_timeout", 30)
            for _ in range(timeout_secs):  # Configurable timeout (default 30s)
                time.sleep(1)
                if debug_file.exists():
                    try:
                        debug_data = json.loads(debug_file.read_text(encoding="utf-8"))
                        captured_tools = debug_data.get("tools", [])
                        if captured_tools:
                            break
                    except Exception:
                        pass

        except Exception as e:
            return jsonify({
                "tools": [],
                "count": 0,
                "source": "error",
                "message": f"Failed to launch probe: {e}"
            })
        finally:
            # Kill the probe process
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            # Clean up probe agent
            try:
                probe_file.unlink()
            except Exception:
                pass

        if captured_tools:
            # Save to harness profile
            harness_data["available_tools"] = sorted(set(captured_tools))
            harness_path.write_text(json.dumps(harness_data, indent=2), encoding="utf-8")
            return jsonify({"tools": sorted(set(captured_tools)), "count": len(captured_tools), "source": "auto_captured"})
        else:
            # Capture stderr for debugging
            stderr_output = ""
            if proc:
                try:
                    stderr_output = proc.stderr.read().decode("utf-8", errors="replace")[-1000:]
                except Exception:
                    pass
            timeout_secs = harness.get("discover_timeout", 30)
            return jsonify({
                "tools": [],
                "count": 0,
                "source": "timeout",
                "message": f"Probe timed out — harness '{slug}' did not send tools within {timeout_secs}s. "
                           f"The harness may require interactive input or may not be compatible with automated probing.",
                "stderr": stderr_output,
                "command": ' '.join(cmd_list),
            })

    # ── Form data for agent editor ────────────────────────────────────────

    @app.route("/api/form-options")
    def get_form_options():
        """Return available harnesses, providers, and tool profiles for form dropdowns."""
        # Exclude incompatible harnesses (e.g. codex)
        incompatible_slugs = {info["slug"] for info in HARNESS_CATALOG.values() if info.get("incompatible")}
        harnesses = [p.stem for p in sorted(harnesses_dir.glob("*.json")) if p.stem not in incompatible_slugs]
        providers = [p.stem for p in sorted(providers_dir.glob("*.json"))]

        # Legacy global tool profiles (fallback)
        tool_profiles = []
        if tool_file.exists():
            tool_profiles = list(json.loads(tool_file.read_text(encoding="utf-8")).keys())

        # Per-harness tool profiles
        harness_tool_profiles = {}
        for h_path in sorted(harnesses_dir.glob("*.json")):
            try:
                h_data = json.loads(h_path.read_text(encoding="utf-8"))
                tp = h_data.get("tool_profiles", {})
                if tp:
                    harness_tool_profiles[h_path.stem] = list(tp.keys())
            except Exception:
                pass

        # Native-only harnesses (for UI: restrict provider dropdown to 'native')
        native_only_harnesses = []
        for h_path in sorted(harnesses_dir.glob("*.json")):
            try:
                h_data = json.loads(h_path.read_text(encoding="utf-8"))
                if h_data.get("native_only"):
                    native_only_harnesses.append(h_path.stem)
            except Exception:
                pass

        return jsonify({
            "harnesses": harnesses,
            "providers": providers,
            "tool_profiles": tool_profiles,
            "harness_tool_profiles": harness_tool_profiles,
            "native_only_harnesses": native_only_harnesses,
        })

    # ── Harness catalog, auto-discovery & installation ───────────────────

    # Full registry of known AI coding harnesses
    HARNESS_CATALOG = {
        "claude": {
            "name": "Claude Code",
            "slug": "claude-code",
            "binary": "claude",
            "description": "Anthropic's official CLI for Claude",
            "install_commands": {
                "npm": "npm install -g @anthropic-ai/claude-code",
                "brew": "brew install claude-code",
                "curl": "curl -fsSL https://claude.ai/install.sh | bash",
            },
            "launch_mode": "env",
            "speaks_protocol": "anthropic",
            "env_map": {"base_url": "ANTHROPIC_BASE_URL", "auth_token": "ANTHROPIC_AUTH_TOKEN"},
            "extra_args": [],
            "homepage": "https://docs.anthropic.com/en/docs/claude-code",
        },
        "aider": {
            "name": "Aider",
            "slug": "aider",
            "binary": "aider",
            "description": "AI pair programming in your terminal (multi-provider via LiteLLM)",
            "install_commands": {
                "pip": "pip install aider-chat",
                "python-m-pip": "python -m pip install aider-chat",
                "pipx": "pipx install aider-chat",
            },
            "launch_mode": "env",
            "speaks_protocol": "openai",
            "env_map": {"base_url": "OPENAI_API_BASE", "auth_token": "OPENAI_API_KEY"},
            "extra_args": [],
            "homepage": "https://aider.chat",
        },
        "codex": {
            "name": "OpenAI Codex CLI",
            "slug": "codex",
            "binary": "codex",
            "description": "Native-only — uses OpenAI API directly. Cannot route through third-party providers.",
            "install_commands": {},
            "launch_mode": "env",
            "speaks_protocol": "openai-responses",
            "env_map": {},
            "extra_args": [],
            "homepage": "https://github.com/openai/codex",
            "native_only": True,
            "install_commands": {
                "npm": "npm install -g @openai/codex",
            },
        },
        "goose": {
            "name": "Goose (Block)",
            "slug": "goose",
            "binary": "goose",
            "description": "Open-source AI agent by Block (Square) with MCP support",
            "install_commands": {
                "powershell": 'Invoke-WebRequest -Uri "https://github.com/block/goose/releases/latest/download/goose-x86_64-pc-windows-msvc.zip" -OutFile "$env:TEMP\\goose.zip"; Expand-Archive "$env:TEMP\\goose.zip" -DestinationPath "$env:LOCALAPPDATA\\Programs\\goose" -Force; [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";$env:LOCALAPPDATA\\Programs\\goose", "User")',
                "curl (Unix)": "curl -fsSL https://github.com/block/goose/releases/latest/download/download_cli.sh | bash",
                "brew": "brew install block/tap/goose",
            },
            "launch_mode": "env",
            "speaks_protocol": "openai",
            "base_url_no_v1": True,
            "env_map": {"base_url": "OPENAI_HOST", "auth_token": "OPENAI_API_KEY"},
            "extra_args": ["session", "--provider", "openai"],
            "probe_override_args": ["run", "--text", "hi", "--provider", "openai", "--no-session"],
            "homepage": "https://github.com/block/goose",
        },
        "opencode": {
            "name": "OpenCode",
            "slug": "opencode",
            "binary": "opencode",
            "description": "Go-based TUI with multi-provider support and LSP integration",
            "install_commands": {
                "powershell": 'Invoke-WebRequest -Uri "https://github.com/sst/opencode/releases/latest/download/opencode-windows-x64.zip" -OutFile "$env:TEMP\\opencode.zip"; Expand-Archive "$env:TEMP\\opencode.zip" -DestinationPath "$env:LOCALAPPDATA\\Programs\\opencode" -Force; [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";$env:LOCALAPPDATA\\Programs\\opencode", "User")',
                "brew": "brew install sst/tap/opencode",
            },
            "launch_mode": "config_file",
            "speaks_protocol": "openai",
            "env_map": {},
            "extra_args": [],
            "config_file_path": "opencode.json",
            "config_template": {
                "$schema": "https://opencode.ai/config.json",
                "provider": {"router": {"npm": "@ai-sdk/openai-compatible", "options": {"baseURL": "{{base_url}}"}, "models": {"{{model}}": {}}}},
                "model": "router/{{model}}"
            },
            "homepage": "https://opencode.ai",
        },
        "gemini": {
            "name": "Gemini CLI (Google)",
            "slug": "gemini",
            "binary": "gemini",
            "description": "Google's CLI for Gemini models (supports OpenAI-compatible mode)",
            "install_commands": {
                "npm": "npm install -g @google/gemini-cli",
            },
            "launch_mode": "env",
            "speaks_protocol": "openai",
            "env_map": {"base_url": "GEMINI_BASE_URL", "auth_token": "GEMINI_API_KEY"},
            "extra_args": [],
            "homepage": "https://github.com/google-gemini/gemini-cli",
        },
        "amp": {
            "name": "Amp (Sourcegraph)",
            "slug": "amp",
            "binary": "amp",
            "description": "Sourcegraph's AI coding agent with Cody context integration",
            "install_commands": {
                "npm": "npm install -g @sourcegraph/amp",
                "brew": "brew install sourcegraph/amp/amp",
            },
            "launch_mode": "env",
            "speaks_protocol": "anthropic",
            "env_map": {"base_url": "ANTHROPIC_BASE_URL", "auth_token": "ANTHROPIC_API_KEY"},
            "extra_args": [],
            "homepage": "https://ampcode.com",
        },
        "dsh": {
            "name": "DeepSeek Harness",
            "slug": "deepseek-harness",
            "binary": "dsh",
            "description": "DeepSeek's official agentic coding harness (developer preview, npm)",
            "install_commands": {
                "npm": "npm install -g @deepseek-ai/dsh",
            },
            "launch_mode": "config_file_plus_env",
            "speaks_protocol": "openai",
            "env_map": {"auth_token": "DEEPSEEK_API_KEY"},
            "extra_args": ["--profile", "headless"],
            "config_file_path": "~/.dsh/settings.yaml",
            "config_template": {"provider": {"custom": {"base_url": "{{base_url}}", "protocol": "openai-compatible", "models": ["{{model}}"]}}},
            "homepage": "https://github.com/deepseek-ai/deepseek-harness",
        },
    }

    @app.route("/api/harnesses/catalog")
    def get_harness_catalog():
        """Return the full catalog of known harnesses with install status."""
        import shutil
        result = []
        for binary, info in HARNESS_CATALOG.items():
            if info.get("incompatible"):
                continue
            path = shutil.which(binary) or _find_binary_fallback(binary)
            harness_file = harnesses_dir / f"{info['slug']}.json"
            result.append({
                "binary": binary,
                "name": info["name"],
                "slug": info["slug"],
                "description": info["description"],
                "homepage": info.get("homepage", ""),
                "install_commands": info.get("install_commands", {}),
                "installed": path is not None,
                "binary_path": path or "",
                "has_profile": harness_file.exists(),
                "speaks_protocol": info["speaks_protocol"],
            })
        return jsonify(result)

    @app.route("/api/harnesses/discover-system", methods=["POST"])
    def discover_system_harnesses():
        """Scan system for known harness binaries and create profiles for any found."""
        import shutil

        found = []
        created = []

        for binary, defaults in HARNESS_CATALOG.items():
            if defaults.get("incompatible"):
                continue
            path = shutil.which(binary) or _find_binary_fallback(binary)
            if path:
                found.append({"binary": binary, "path": path, "slug": defaults["slug"]})
                harness_file = harnesses_dir / f"{defaults['slug']}.json"
                if not harness_file.exists():
                    profile = {
                        "name": defaults["name"],
                        "binary": binary,
                        "binary_path": path,
                        "launch_mode": defaults["launch_mode"],
                        "speaks_protocol": defaults["speaks_protocol"],
                        "env_map": defaults.get("env_map", {}),
                        "extra_args": defaults.get("extra_args", []),
                        "available_tools": [],
                        "tool_profiles": {
                            "full": {"description": "All tools (pass-through)", "mode": "keep_all"},
                            "coding": {"description": "Essential coding tools", "mode": "whitelist",
                                       "tools": ["PowerShell", "Read", "Write", "Edit", "Grep", "Glob",
                                                  "Agent", "WebSearch", "WebFetch", "AskUserQuestion",
                                                  "TaskOutput", "TaskStop", "SendMessage"]},
                            "minimal": {"description": "File ops + shell only", "mode": "whitelist",
                                        "tools": ["PowerShell", "Read", "Write", "Edit", "Grep", "Glob"]},
                            "none": {"description": "Strip all tools", "mode": "strip_all"},
                        },
                    }
                    if "config_file_path" in defaults:
                        profile["config_file_path"] = defaults["config_file_path"]
                    if "config_template" in defaults:
                        profile["config_template"] = defaults["config_template"]
                    harness_file.write_text(json.dumps(profile, indent=2), encoding="utf-8")
                    created.append(defaults["slug"])
                else:
                    # Update binary_path if empty
                    try:
                        existing = json.loads(harness_file.read_text(encoding="utf-8"))
                        if not existing.get("binary_path"):
                            existing["binary_path"] = path
                            harness_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
                    except Exception:
                        pass

        return jsonify({
            "found": found,
            "created": created,
            "message": f"Found {len(found)} harness binaries, created {len(created)} new profiles"
        })

    @app.route("/api/harnesses/install", methods=["POST"])
    def install_harness():
        """Install a harness binary using its preferred install command."""
        import subprocess
        import shutil
        import platform

        data = request.get_json(force=True)
        binary = data.get("binary", "")
        method = data.get("method", "")  # npm, pip, pipx, brew, curl

        if binary not in HARNESS_CATALOG:
            return jsonify({"error": f"Unknown harness '{binary}'"}), 404

        info = HARNESS_CATALOG[binary]
        install_commands = info.get("install_commands", {})

        if not install_commands:
            return jsonify({"error": f"No install commands available for '{binary}'"}), 400

        # Auto-select method if not specified
        if not method:
            is_win = platform.system() == "Windows"
            # Platform-aware preference order
            if is_win:
                preferred_order = ["npm", "pip", "pipx", "powershell", "brew", "curl"]
            else:
                preferred_order = ["npm", "pip", "pipx", "brew", "curl", "powershell"]
            for preferred in preferred_order:
                if preferred in install_commands:
                    method = preferred
                    break

        if method not in install_commands:
            return jsonify({
                "error": f"Method '{method}' not available for '{binary}'",
                "available_methods": list(install_commands.keys())
            }), 400

        cmd = install_commands[method]

        # Check if the install tool itself is available
        tool_binary = method
        if method == "powershell":
            tool_binary = "powershell"
        elif method == "curl":
            tool_binary = "curl"
        if not shutil.which(tool_binary):
            return jsonify({
                "error": f"'{tool_binary}' not found on PATH. Install it first or choose another method.",
                "available_methods": [m for m in install_commands if shutil.which(m if m not in ('curl', 'powershell') else m)]
            }), 400

        # Auto-create harness profile from catalog data (binary_path resolved at launch time)
        harness_file = harnesses_dir / f"{info['slug']}.json"
        if not harness_file.exists():
            profile = {
                "name": info["name"],
                "binary": binary,
                "binary_path": "",
                "launch_mode": info.get("launch_mode", "env"),
                "speaks_protocol": info.get("speaks_protocol", "openai"),
                "env_map": info.get("env_map", {}),
                "extra_args": info.get("extra_args", []),
                "available_tools": [],
                "tool_profiles": {
                    "full": {"description": "All tools (pass-through)", "mode": "keep_all"},
                    "coding": {"description": "Essential coding tools", "mode": "whitelist",
                               "tools": ["PowerShell", "Read", "Write", "Edit", "Grep", "Glob",
                                          "Agent", "WebSearch", "WebFetch", "AskUserQuestion",
                                          "TaskOutput", "TaskStop", "SendMessage"]},
                    "minimal": {"description": "File ops + shell only", "mode": "whitelist",
                                "tools": ["PowerShell", "Read", "Write", "Edit", "Grep", "Glob"]},
                    "none": {"description": "Strip all tools", "mode": "strip_all"},
                },
            }
            if "config_file_path" in info:
                profile["config_file_path"] = info["config_file_path"]
            if "config_template" in info:
                profile["config_template"] = info["config_template"]
            harness_file.write_text(json.dumps(profile, indent=2), encoding="utf-8")


        # Run the install command in a visible terminal window
        import platform
        is_windows = platform.system() == "Windows"

        try:
            if is_windows:
                # Write install script so user can see progress in real-time
                debug_dir = base / "debug"
                debug_dir.mkdir(exist_ok=True)
                script_path = debug_dir / f"install_{binary}.ps1"

                ps_lines = [
                    f"# AI Router Install Script for: {info['name']}",
                    f'Write-Host "" ',
                    f'Write-Host "[AI Router] Installing {info["name"]}..." -ForegroundColor Cyan',
                    f'Write-Host "  Method: {method}" -ForegroundColor Green',
                    f'Write-Host "  Command: {cmd.replace(chr(34), "`" + chr(34))}" -ForegroundColor Yellow',
                    f'Write-Host "" ',
                    f'{cmd}',
                    f'Write-Host "" ',
                    f'if ($? -and (-not $LASTEXITCODE -or $LASTEXITCODE -eq 0)) {{',
                    f'    Write-Host "[AI Router] \u2705 Install completed successfully!" -ForegroundColor Green',
                    f'}} else {{',
                    f'    Write-Host "[AI Router] \u274c Install failed (exit code: $LASTEXITCODE)" -ForegroundColor Red',
                    f'}}',
                    f'Write-Host "" ',
                    f'Write-Host "Press any key to close..." -ForegroundColor Gray',
                    f'$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")',
                ]
                script_path.write_text('\n'.join(ps_lines), encoding="utf-8")

                # Launch PowerShell with the script in a new visible window
                proc = subprocess.Popen(
                    ['powershell', '-Command',
                     f'Start-Process powershell -ArgumentList "-NoExit","-ExecutionPolicy","Bypass","-File","{script_path}"'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

                return jsonify({
                    "success": True,
                    "message": f"Install launched in new terminal window. Check the PowerShell window for progress.",
                    "command": cmd,
                    "script": str(script_path),
                    "pid": proc.pid,
                })
            else:
                # Unix: open in terminal emulator
                import shutil as _shutil
                full_cmd = f'echo "[AI Router] Installing {info["name"]}..."; {cmd}; echo ""; echo "Done. Press enter to close."; read'
                launched = False
                for term_cmd in [
                    ['gnome-terminal', '--', 'bash', '-c', full_cmd],
                    ['xterm', '-e', f'bash -c \"{full_cmd}\"'],
                ]:
                    if _shutil.which(term_cmd[0]):
                        proc = subprocess.Popen(
                            term_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                        launched = True
                        break

                if launched:
                    return jsonify({
                        "success": True,
                        "message": f"Install launched in new terminal window.",
                        "command": cmd,
                        "pid": proc.pid,
                    })
                else:
                    # Fallback: run inline (old behavior)
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=120,
                        env={**os.environ, "CI": "true"}
                    )
                    return jsonify({
                        "success": result.returncode == 0,
                        "command": cmd,
                        "stdout": result.stdout[-2000:] if result.stdout else "",
                        "stderr": result.stderr[-2000:] if result.stderr else "",
                        "returncode": result.returncode,
                    })

        except Exception as e:
            return jsonify({"error": str(e), "command": cmd}), 500


    @app.route("/api/harnesses/configure/<slug>", methods=["POST"])
    def configure_harness(slug):
        """Open interactive terminal for harness configuration (e.g. goose configure)."""
        import subprocess
        import platform

        harness_path = harnesses_dir / f"{slug}.json"
        if not harness_path.exists():
            return jsonify({"error": "Harness not found"}), 404

        harness = json.loads(harness_path.read_text(encoding="utf-8"))
        binary_path = harness.get("binary_path", "")
        if not binary_path:
            import shutil
            binary_path = shutil.which(harness.get("binary", "")) or _find_binary_fallback(harness.get("binary", ""))
        if not binary_path:
            return jsonify({"error": f"Binary not found for '{slug}'"}), 400

        configure_cmd = request.json.get("command", "configure") if request.json else "configure"

        is_windows = platform.system() == "Windows"
        try:
            if is_windows:
                debug_dir = base / "debug"
                debug_dir.mkdir(exist_ok=True)
                script_path = debug_dir / f"configure_{slug}.ps1"
                harness_display = harness.get('name', slug)
                ps_lines = [
                    f"# AI Router Configure Script for: {slug}",
                    'Write-Host ""',
                    f'Write-Host "[AI Router] Interactive Configuration for {harness_display}" -ForegroundColor Cyan',
                    'Write-Host "Follow the prompts to complete setup." -ForegroundColor Yellow',
                    'Write-Host ""',
                    f'{binary_path} {configure_cmd}',
                    'Write-Host ""',
                    'Write-Host "Configuration complete! You can close this window." -ForegroundColor Green',
                ]
                script_path.write_text('\n'.join(ps_lines), encoding="utf-8")
                proc = subprocess.Popen(
                    ['powershell', '-Command',
                     f'Start-Process powershell -ArgumentList "-NoExit","-File","{script_path}"'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                full_cmd = f'{binary_path} {configure_cmd}'
                import shutil as _shutil
                for term_cmd in [
                    ['gnome-terminal', '--', 'bash', '-c', full_cmd + '; exec bash'],
                    ['xterm', '-e', full_cmd],
                ]:
                    if _shutil.which(term_cmd[0]):
                        proc = subprocess.Popen(
                            term_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                        break
                else:
                    return jsonify({"error": "No terminal emulator found"}), 400

            return jsonify({
                "success": True,
                "message": f"Opened interactive configuration for {slug}",
                "command": f"{binary_path} {configure_cmd}"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
