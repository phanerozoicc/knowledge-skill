#!/usr/bin/env node
/**
 * notion-sync local engine.
 *
 * Zero-dependency Node script. Does NOT call Notion — the agent does MCP I/O
 * and feeds this script structured data. This script owns all local work:
 *   - parse/build markdown + frontmatter
 *   - maintain .notion-sync-index.json (keyed by Notion page id)
 *   - three-state pull decision (new / update / suspected-rename-or-delete)
 *   - emit Notion write parameters for push
 *   - status report
 *
 * Usage:
 *   sync.js pull  <pages.json>      pull: read agent-prepared pages JSON, write local files + index + report
 *   sync.js push  <file.md>         push: read a local file, emit Notion write params JSON for the agent
 *   sync.js status                  status: scan local vs index, report
 *
 * See references/local-format.md for the file format and index schema.
 *
 * Exit codes: 0 ok, 1 usage, 2 data error.
 */

const fs = require('fs');
const path = require('path');

const REPO = process.env.NOTION_SYNC_REPO || findRepoRoot();
const INDEX_PATH = path.join(REPO, '.notion-sync-index.json');
const TRASH_DIR = path.join(REPO, '.notion-sync-trash');
const DATA_SOURCE_ID = 'a0837cf8-c21b-4877-a713-63a8cb0d5dc5'; // Knowledge Units

// ---------- frontmatter ----------

function parseFrontmatter(md) {
  const m = md.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!m) return { fm: {}, body: md };
  const fm = {};
  const raw = m[1];
  // simple line parser: key: value  (values may be bare, "quoted", or boolean-looking)
  for (const line of raw.split(/\r?\n/)) {
    const mm = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (!mm) continue;
    let [, k, v] = mm;
    v = v.trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1).replace(/\\"/g, '"');
    } else if (v === 'true') v = true;
    else if (v === 'false') v = false;
    fm[k] = v;
  }
  return { fm, body: m[2] };
}

function yamlScalar(v) {
  if (v === null || v === undefined) return '""';
  if (typeof v === 'boolean') return String(v);
  if (typeof v === 'number') return String(v);
  // escape inner quotes + collapse newlines for single-line yaml
  const s = String(v).replace(/"/g, '\\"').replace(/\r?\n/g, ' ');
  return `"${s}"`;
}

function buildFrontmatter(meta) {
  const lines = ['---'];
  lines.push(`notion_id: ${meta.notion_id || ''}`);
  lines.push(`notion_url: ${meta.notion_url || ''}`);
  lines.push(`last_edited_time: ${meta.last_edited_time || ''}`);
  lines.push(`synced_at: ${meta.synced_at || ''}`);
  lines.push(`type: ${meta.type || ''}`);
  lines.push(`status: ${meta.status || ''}`);
  lines.push(`domain: ${meta.domain || ''}`);
  lines.push(`source_url: ${meta.source_url || ''}`);
  lines.push(`memory: ${meta.memory === true || meta.memory === '__YES__'}`);
  lines.push(`review_question: ${yamlScalar(meta.review_question || '')}`);
  lines.push(`review_answer: ${yamlScalar(meta.review_answer || '')}`);
  lines.push('---');
  return lines.join('\n');
}

// ---------- index ----------

function loadIndex() {
  if (!fs.existsSync(INDEX_PATH)) return {};
  try {
    return JSON.parse(fs.readFileSync(INDEX_PATH, 'utf8'));
  } catch (e) {
    console.error(`error: index file corrupt: ${INDEX_PATH}: ${e.message}`);
    process.exit(2);
  }
}

function saveIndex(idx) {
  fs.writeFileSync(INDEX_PATH, JSON.stringify(idx, null, 2) + '\n');
}

// ---------- paths ----------

function sanitizeFilename(name) {
  return String(name || '').replace(/[/\\:*?"<>|]/g, ' ').replace(/\s+/g, ' ').trim();
}

function domainDir(domain) {
  const d = Array.isArray(domain) ? domain[0] : domain;
  return path.join('knowledge-unit', d || 'Uncategorized');
}

function pageIdFromUrl(url) {
  if (!url) return '';
  const m = String(url).match(/([0-9a-f]{32})(?:[?#]|$)/i);
  return m ? m[1] : '';
}

// ---------- three-state decision ----------

/**
 * @param {Array} pages - agent-prepared pages from Notion
 *   each: { id, url, name, last_edited_time, type, status, domain, source_url,
 *           memory, review_question, review_answer, content }
 *   - id: notion page id (32-hex) — required
 *   - content: markdown body (may be "" for blank Notion pages; caller rebuilds from props)
 * @param {Object} opts
 *   - full: when true, this is a complete pull of the data source, so the reverse
 *           scan (local notion_id not in pull → suspect notion-side deletion) runs.
 *           Default false: partial pulls skip the reverse scan to avoid false alarms.
 * Writes local files, updates index, returns a report object.
 */
function doPull(pages, opts = {}) {
  const idx = loadIndex();
  const dsIdx = idx[DATA_SOURCE_ID] || (idx[DATA_SOURCE_ID] = {});
  const report = { created: [], updated: [], skipped: [], suspected: [], nowUtc: new Date().toISOString(), full: !!opts.full };

  for (const p of pages) {
    const id = p.id || pageIdFromUrl(p.url);
    if (!id) { report.suspected.push({ reason: 'missing id', page: p }); continue; }
    const relDir = domainDir(p.domain);
    const fname = sanitizeFilename(p.name) + '.md';
    const relPath = path.join(relDir, fname);
    const absPath = path.join(REPO, relPath);
    const syncedAt = new Date().toISOString();

    const entry = dsIdx[id];
    const exists = entry ? fs.existsSync(path.join(REPO, entry.filename || relPath)) : false;

    if (entry && exists) {
      // known + present: incremental compare by last_edited_time
      if (p.last_edited_time && entry.last_edited_time === p.last_edited_time) {
        report.skipped.push({ id, filename: entry.filename });
        continue;
      }
      // update: back up old then overwrite
      backupFile(path.join(REPO, entry.filename));
      writeLocalFile(absPath, p, syncedAt);
      dsIdx[id] = { filename: entry.filename, last_edited_time: p.last_edited_time || syncedAt, synced_at: syncedAt };
      report.updated.push({ id, filename: entry.filename });
    } else if (entry && !exists) {
      // known but file gone locally: suspected rename or delete — DO NOT auto-process
      report.suspected.push({ id, reason: 'file missing locally (rename or delete?)', expected: entry.filename, name: p.name });
    } else {
      // new: create
      fs.mkdirSync(path.dirname(absPath), { recursive: true });
      writeLocalFile(absPath, p, syncedAt);
      dsIdx[id] = { filename: relPath, last_edited_time: p.last_edited_time || syncedAt, synced_at: syncedAt };
      report.created.push({ id, filename: relPath });
    }
  }

  // reverse scan: ONLY on a full pull. Partial pulls (subset of pages) would
  // otherwise flag every un-fetched page as "notion-side deleted", a false alarm.
  if (opts.full) {
    const pulledIds = new Set(pages.map(p => p.id || pageIdFromUrl(p.url)).filter(Boolean));
    const localFiles = walkMd(path.join(REPO, 'knowledge-unit'));
    for (const fp of localFiles) {
      const md = fs.readFileSync(fp, 'utf8');
      const { fm } = parseFrontmatter(md);
      if (fm.notion_id && !pulledIds.has(fm.notion_id)) {
        report.suspected.push({ id: fm.notion_id, reason: 'notion-side deleted (local kept)', filename: path.relative(REPO, fp) });
      }
    }
  }

  saveIndex(idx);
  return report;
}

function writeLocalFile(absPath, p, syncedAt) {
  const meta = {
    notion_id: p.id || pageIdFromUrl(p.url),
    notion_url: p.url || '',
    last_edited_time: p.last_edited_time || '',
    synced_at: syncedAt,
    type: p.type, status: p.status, domain: arrayFirst(p.domain),
    source_url: p.source_url || '',
    memory: p.memory, review_question: p.review_question || '', review_answer: p.review_answer || '',
  };
  const fm = buildFrontmatter(meta);
  const body = (p.content || '').trim();
  fs.writeFileSync(absPath, `${fm}\n\n${body}\n`);
}

function backupFile(absPath) {
  if (!fs.existsSync(absPath)) return;
  fs.mkdirSync(TRASH_DIR, { recursive: true });
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const dest = path.join(TRASH_DIR, `${path.basename(absPath)}.${ts}.bak`);
  fs.copyFileSync(absPath, dest);
}

// ---------- push ----------

/**
 * Read a local file and emit Notion write parameters as JSON.
 * The agent consumes this to call notion-update-page or notion-create-pages.
 * If the file has notion_id → update payload; otherwise → create payload.
 */
function doPush(fileArg) {
  const absPath = resolveLocal(fileArg);
  if (!fs.existsSync(absPath)) { console.error(`error: file not found: ${absPath}`); process.exit(2); }
  const md = fs.readFileSync(absPath, 'utf8');
  const { fm, body } = parseFrontmatter(md);

  const props = {
    Name: path.basename(absPath, '.md'),
    Type: fm.type || '',
    Status: fm.status || '',
    Domain: fm.domain || '',
    'Source URL': fm.source_url || '',
    Memory: fm.memory === true ? '__YES__' : '__NO__',
  };
  if (fm.memory === true) {
    if (fm.review_question) props['Review Question'] = fm.review_question;
    if (fm.review_answer) props['Review Answer'] = fm.review_answer;
  }

  const out = {
    action: fm.notion_id ? 'update' : 'create',
    notion_id: fm.notion_id || null,
    notion_url: fm.notion_url || null,
    properties: props,
    content: body.trim(),
    notes: [],
  };
  // multi-select: Notion create-pages accepts single string per property; remind caller
  out.notes.push('Domain: pass single string value to Notion (multi-select quirk).');
  if (!fm.notion_id) {
    out.notes.push('After notion-create-pages succeeds, rewrite this file\'s frontmatter: set notion_id/notion_url/last_edited_time/synced_at, then update .notion-sync-index.json.');
  } else {
    out.notes.push('After notion-update-page succeeds, update frontmatter synced_at + index last_edited_time/synced_at.');
  }
  return out;
}

// ---------- status ----------

function doStatus() {
  const idx = loadIndex();
  const dsIdx = idx[DATA_SOURCE_ID] || {};
  const localFiles = walkMd(path.join(REPO, 'knowledge-unit'));
  const report = { tracked: 0, localFiles: 0, missingLocal: [], missingIndex: [], byDomain: {} };

  report.tracked = Object.keys(dsIdx).length;
  report.localFiles = localFiles.length;

  for (const [id, entry] of Object.entries(dsIdx)) {
    if (!fs.existsSync(path.join(REPO, entry.filename))) {
      report.missingLocal.push({ id, filename: entry.filename });
    }
  }
  for (const fp of localFiles) {
    const { fm } = parseFrontmatter(fs.readFileSync(fp, 'utf8'));
    const dom = fm.domain || 'Uncategorized';
    report.byDomain[dom] = (report.byDomain[dom] || 0) + 1;
    if (!fm.notion_id || !dsIdx[fm.notion_id]) {
      report.missingIndex.push({ filename: path.relative(REPO, fp), notion_id: fm.notion_id || '(none)' });
    }
  }
  return report;
}

// ---------- helpers ----------

function arrayFirst(v) {
  if (Array.isArray(v)) return v[0] || '';
  return v || '';
}

function walkMd(dir) {
  if (!fs.existsSync(dir)) return [];
  let out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out = out.concat(walkMd(p));
    else if (e.name.endsWith('.md')) out.push(p);
  }
  return out;
}

function resolveLocal(arg) {
  if (path.isAbsolute(arg)) return arg;
  // Prefer resolving relative to the repo root (so `knowledge-unit/Java/x.md` works
  // from anywhere), then fall back to cwd.
  const fromRepo = path.join(REPO, arg);
  if (fs.existsSync(fromRepo)) return fromRepo;
  return path.resolve(process.cwd(), arg);
}

function findRepoRoot() {
  let dir = process.cwd();
  for (let i = 0; i < 8; i++) {
    if (fs.existsSync(path.join(dir, '.git')) || fs.existsSync(path.join(dir, 'knowledge-unit'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

// ---------- reports ----------

function printPullReport(r) {
  console.log('=== Pull Report ===');
  console.log(`created:  ${r.created.length}`);
  for (const x of r.created) console.log(`  + ${x.filename}`);
  console.log(`updated:  ${r.updated.length}`);
  for (const x of r.updated) console.log(`  * ${x.filename}`);
  console.log(`skipped:  ${r.skipped.length}`);
  console.log(`suspected (needs confirmation): ${r.suspected.length}`);
  for (const x of r.suspected) {
    console.log(`  ? [${x.id || '?'}] ${x.reason || ''}${x.expected ? ' (expected: ' + x.expected + ')' : ''}${x.name ? ' name="' + x.name + '"' : ''}${x.filename ? ' file=' + x.filename : ''}`);
  }
  console.log(`synced_at: ${r.nowUtc}`);
}

function printStatusReport(r) {
  console.log('=== Status ===');
  console.log(`index entries (tracked): ${r.tracked}`);
  console.log(`local .md files:        ${r.localFiles}`);
  console.log(`by domain:`, r.byDomain);
  if (r.missingLocal.length) {
    console.log(`missing locally (notion has, local gone — suspected rename/delete): ${r.missingLocal.length}`);
    for (const x of r.missingLocal) console.log(`  ? [${x.id}] ${x.filename}`);
  }
  if (r.missingIndex.length) {
    console.log(`missing from index (local-only or untracked): ${r.missingIndex.length}`);
    for (const x of r.missingIndex) console.log(`  - ${x.filename}  (notion_id: ${x.notion_id})`);
  }
  if (!r.missingLocal.length && !r.missingIndex.length) console.log('local files and index are consistent.');
}

// ---------- CLI ----------

const argv = process.argv.slice(2);
const cmd = argv[0];
const arg = argv.slice(1).find(a => !a.startsWith('--'));
const full = argv.includes('--full');

function usage() {
  console.log(`usage:
  sync.js pull  <pages.json> [--full]   pull pages (agent-prepared) into local files + index
                                      (--full: complete pull; runs reverse-scan for notion-side deletions)
  sync.js push  <file.md>      emit Notion write params for a local file
  sync.js status               report local vs index consistency

pages.json schema (array):
  [{ "id","url","name","last_edited_time","type","status","domain",
     "source_url","memory","review_question","review_answer","content" }]
  - domain: single string or ["Tag"]; content: markdown body ("" ok for blank Notion pages)`);
}

if (cmd === 'pull') {
  if (!arg) { usage(); process.exit(1); }
  const abs = path.resolve(process.cwd(), arg);
  let pages;
  try { pages = JSON.parse(fs.readFileSync(abs, 'utf8')); }
  catch (e) { console.error(`error: cannot read pages json ${abs}: ${e.message}`); process.exit(2); }
  if (!Array.isArray(pages)) { console.error('error: pages json must be an array'); process.exit(2); }
  printPullReport(doPull(pages, { full }));
} else if (cmd === 'push') {
  if (!arg) { usage(); process.exit(1); }
  console.log(JSON.stringify(doPush(arg), null, 2));
} else if (cmd === 'status') {
  printStatusReport(doStatus());
} else {
  usage();
  process.exit(cmd ? 1 : 0);
}
