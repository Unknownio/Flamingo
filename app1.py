# app.py

import os
import sqlite3
import time
from collections import deque

from nicegui import run, ui

import osint_engine
import tracker

# Isolated copies so this redesigned UI can run side by side with app.py
# without touching its database. Override with FLAMINGO_DB / FLAMINGO_PORT.
tracker.DB_FILE = os.environ.get('FLAMINGO_DB', 'exposure_tracker_modern.db')
PORT = int(os.environ.get('FLAMINGO_PORT', '2525'))

# Initialize local SQLite DB
tracker.init_db()

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

ui.add_head_html('''
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
    <style>
        :root {
            --bg: #f6f7f9;
            --surface: #ffffff;
            --surface-2: #f8f9fb;
            --surface-3: #f1f3f7;
            --seg-active: #ffffff;
            --border: #e4e7ec;
            --border-strong: #d3d8e0;
            --text: #101319;
            --muted: #667085;
            --faint: #98a2b3;
            --accent: #2b59c3;
            --accent-soft: rgba(43, 89, 195, .08);
            --accent-ink: #ffffff;
            --ok: #067647;   --ok-bg: #e7f6ee;
            --warn: #a15c07; --warn-bg: #fdf3e1;
            --bad: #b42318;  --bad-bg: #fdecea;
            --info: #175cd3; --info-bg: #e8f0fe;
            --violet: #6941c6; --violet-bg: #f4ebff;
            --teal: #0e7090; --teal-bg: #e0f2f7;
            --shadow-sm: 0 1px 2px rgba(16, 24, 40, .05);
            --shadow: 0 1px 3px rgba(16, 24, 40, .08), 0 1px 2px rgba(16, 24, 40, .04);
            --shadow-lg: 0 12px 32px -12px rgba(16, 24, 40, .18);
            --ring: 0 0 0 3px rgba(43, 89, 195, .16);
            --q-primary: #2b59c3;
        }
        body.body--dark {
            --bg: #0b0d10;
            --surface: #14171c;
            --surface-2: #191d23;
            --surface-3: #1e232a;
            --seg-active: #262c34;
            --border: #242932;
            --border-strong: #333a45;
            --text: #e9ebee;
            --muted: #8b95a4;
            --faint: #616b7a;
            --accent: #7d9bff;
            --accent-soft: rgba(125, 155, 255, .12);
            --accent-ink: #0b0d10;
            --ok: #4cc38a;   --ok-bg: rgba(76, 195, 138, .13);
            --warn: #e0a458; --warn-bg: rgba(224, 164, 88, .13);
            --bad: #ef7b6f;  --bad-bg: rgba(239, 123, 111, .13);
            --info: #84adff; --info-bg: rgba(132, 173, 255, .13);
            --violet: #b692f6; --violet-bg: rgba(182, 146, 246, .13);
            --teal: #67d3eb; --teal-bg: rgba(103, 211, 235, .13);
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, .4);
            --shadow: 0 1px 3px rgba(0, 0, 0, .5);
            --shadow-lg: 0 16px 40px -16px rgba(0, 0, 0, .7);
            --ring: 0 0 0 3px rgba(125, 155, 255, .2);
            --q-primary: #7d9bff;
        }

        html, body { background: var(--bg); }
        body {
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: var(--text);
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }
        .nicegui-content { padding: 0 !important; gap: 0 !important; }

        /* ---------------------------------------------------------------- Header */
        .app-header {
            background: var(--surface) !important;
            color: var(--text) !important;
            border-bottom: 1px solid var(--border);
            box-shadow: none !important;
            padding: 0 !important;
            display: block !important;
        }
        .app-header-inner {
            max-width: 1180px; width: 100%; height: 60px;
            margin: 0 auto; padding: 0 24px;
            display: flex; align-items: center; justify-content: space-between; gap: 16px;
        }
        .brand { display: flex; align-items: center; gap: 11px; min-width: 0; }
        .brand-mark {
            width: 30px; height: 30px; border-radius: 9px; flex: none;
            background: linear-gradient(140deg, var(--accent), #7b3ff2);
            color: var(--accent-ink);
            display: grid; place-items: center;
            font-weight: 700; font-size: 15px; letter-spacing: -.02em;
            box-shadow: var(--shadow-sm);
        }
        .brand-text { display: flex; flex-direction: column; line-height: 1.15; }
        .brand-name { font-weight: 650; font-size: 14.5px; letter-spacing: -.01em; }
        .brand-sub { color: var(--faint); font-size: 11.5px; }
        .header-right { display: flex; align-items: center; gap: 10px; }
        .header-actions { display: flex; align-items: center; gap: 4px; padding-left: 8px; border-left: 1px solid var(--border); }
        .status-pill {
            display: flex; align-items: center; gap: 8px;
            height: 30px; padding: 0 12px; border-radius: 999px;
            background: var(--surface-2); border: 1px solid var(--border);
            color: var(--muted); font-size: 12.5px; font-weight: 520;
            white-space: nowrap;
        }
        .status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 0 3px var(--ok-bg); }
        .status-dot.busy { background: var(--warn); box-shadow: 0 0 0 3px var(--warn-bg); animation: pulse 1.4s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
        .last-scan { color: var(--faint); font-size: 12.5px; white-space: nowrap; }
        @media (max-width: 720px) { .last-scan { display: none; } }

        /* ---------------------------------------------------------------- Layout */
        .page {
            width: 100%; max-width: 1180px; margin: 0 auto;
            padding: 30px 24px 72px;
            display: flex; flex-direction: column; gap: 22px;
        }
        .hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
        .hero-title { font-size: 27px; font-weight: 680; letter-spacing: -.028em; line-height: 1.2; }
        .hero-sub { color: var(--muted); font-size: 14px; margin-top: 6px; max-width: 62ch; }
        .hero-aside { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

        .surface {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 14px; width: 100%; box-shadow: var(--shadow-sm);
        }
        .card-head {
            display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap;
            padding: 15px 20px; border-bottom: 1px solid var(--border);
        }
        .card-head-main { display: flex; align-items: center; gap: 11px; min-width: 0; }
        .card-title { font-size: 14px; font-weight: 620; letter-spacing: -.01em; }
        .card-note { font-size: 12.5px; color: var(--muted); }
        .card-body { padding: 20px; }

        .ico-box {
            width: 30px; height: 30px; border-radius: 9px; flex: none;
            display: grid; place-items: center;
            background: var(--surface-3); color: var(--muted);
        }
        .ico-box.ok   { background: var(--ok-bg);   color: var(--ok); }
        .ico-box.warn { background: var(--warn-bg); color: var(--warn); }
        .ico-box.bad  { background: var(--bad-bg);  color: var(--bad); }
        .ico-box.info { background: var(--info-bg); color: var(--info); }
        .ico-box.violet { background: var(--violet-bg); color: var(--violet); }
        .ico-box.teal { background: var(--teal-bg); color: var(--teal); }

        /* ----------------------------------------------------------------- Form */
        /* The scan row is a grid: three fluid fields plus a fixed CTA column.
           No field or control may carry a min-width, or it overflows its cell. */
        .scan-body {
            display: grid; align-items: center; gap: 12px;
            grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr) minmax(0, 1.2fr) 156px;
            width: 100%; min-width: 0;
        }
        /* NiceGUI inputs are custom-element hosts. Give the host a definite,
           shrink-safe width and pass it down, so labels stay inside the box. */
        .scan-field, .search-wrap { display: block; width: 100%; min-width: 0; max-width: 100%; }
        .scan-field .q-field, .search-wrap .q-field {
            display: block; width: 100%; min-width: 0; max-width: 100%;
        }
        .scan-field .q-field__inner, .search-wrap .q-field__inner,
        .scan-field .q-field__control, .search-wrap .q-field__control {
            width: 100%; min-width: 0; max-width: 100%; box-sizing: border-box;
        }
        .scan-cta { min-width: 0; align-self: center; }
        .scan-cta .q-btn, .scan-cta .btn { width: 100%; min-width: 0; box-shadow: none; }
        /* Keep the icon small and lay icon + label on one centered, non-wrapping line. */
        .scan-cta .q-btn .q-icon, .scan-cta .btn .q-icon { font-size: 18px; flex: 0 0 auto; }
        .scan-cta .q-btn__content, .scan-cta .btn .q-btn__content {
            display: flex; flex-direction: row; align-items: center; justify-content: center;
            gap: 6px; white-space: nowrap;
        }
        /* Quasar's hover overlay (.q-focus-helper) paints a dark rectangle over the
           button; remove it here and rely on a subtle brightness change instead. */
        .scan-cta .q-focus-helper { display: none; }
        .scan-cta .q-btn.btn-primary:hover, .scan-cta .btn.btn-primary:hover { box-shadow: none; }
        .scan-body > .q-btn, .scan-body > .btn { width: 100%; min-width: 0; }

        .q-field--outlined .q-field__control { border-radius: 10px; background: var(--surface-2); transition: box-shadow .15s; }
        .q-field--outlined .q-field__control:before { border-color: var(--border) !important; }
        .q-field--outlined:hover .q-field__control:before { border-color: var(--border-strong) !important; }
        .q-field--focused .q-field__control:before { border-color: var(--accent) !important; }
        .q-field--focused .q-field__control { box-shadow: var(--ring); }
        .q-field__native, .q-field__label { font-size: 14px; }
        .q-field__native { text-overflow: ellipsis; }

        /* -------------------------------------------------------------- Buttons */
        /* flex: 0 0 auto keeps buttons at content width inside flex/grid rows */
        .btn, .q-btn.btn {
            display: inline-flex; align-items: center; justify-content: center; gap: 6px;
            flex: 0 0 auto; width: auto; max-width: 100%;
            height: 32px; min-height: 32px; padding: 0 12px;
            border: 1px solid var(--border); border-radius: 9px;
            background: var(--surface); color: var(--text);
            font-size: 13px; font-weight: 520; letter-spacing: 0; text-transform: none;
            text-decoration: none; cursor: pointer; white-space: nowrap;
            transition: background .15s, border-color .15s, transform .12s, box-shadow .15s;
        }
        .btn:hover, .q-btn.btn:hover { background: var(--surface-2); border-color: var(--border-strong); }
        .btn:active, .q-btn.btn:active { transform: translateY(.5px); }
        .btn-icon, .q-btn.btn-icon { width: 32px; padding: 0; }
        .q-btn.btn-primary, .btn-primary {
            height: 40px; padding: 0 12px; font-size: 14px; font-weight: 560;
            background: var(--accent); border-color: var(--accent); color: var(--accent-ink);
            box-shadow: var(--shadow-sm);
        }
        .q-btn.btn-primary:hover { filter: brightness(1.07); box-shadow: var(--shadow); }
        .q-btn.icon-btn {
            width: 32px; height: 32px; min-height: 32px; padding: 0;
            border-radius: 9px; color: var(--muted); border-color: transparent; background: transparent;
        }
        .q-btn.icon-btn:hover { background: var(--surface-2); border-color: var(--border); color: var(--text); }
        .q-btn.btn-quiet { border-color: transparent; background: transparent; color: var(--muted); }
        .q-btn.btn-quiet:hover { background: var(--surface-2); border-color: var(--border); color: var(--text); }
        .q-btn.link-out {
            height: 30px; padding: 0 11px; font-size: 12.5px; font-weight: 560;
            border-color: transparent; background: var(--accent-soft); color: var(--accent);
        }
        .q-btn.link-out:hover { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }

        /* Safety net: no button should ever stretch to fill its row. */
        .q-btn, .btn { flex: 0 0 auto; width: auto; align-self: center; }
        .q-btn.btn-icon, .q-btn.icon-btn, .btn-icon { width: 32px; flex: 0 0 auto; }
        .q-btn.full-width, .btn.full-width { width: 100%; }

        /* ------------------------------------------------------------------ KPI */
        .kpi-row { display: grid; grid-template-columns: 1.15fr 1fr 1fr; gap: 16px; width: 100%; }
        .kpi {
            padding: 18px 20px; display: flex; flex-direction: column; gap: 12px;
            transition: box-shadow .2s, border-color .2s;
        }
        .kpi:hover { box-shadow: var(--shadow); border-color: var(--border-strong); }
        .kpi-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
        .kpi-label { font-size: 12.5px; font-weight: 550; color: var(--muted); }
        .kpi-main { display: flex; align-items: center; gap: 18px; }
        .kpi-value {
            font-size: 34px; font-weight: 670; letter-spacing: -.035em; line-height: 1.05;
            font-variant-numeric: tabular-nums;
        }
        .kpi-unit { color: var(--faint); font-size: 14px; font-weight: 500; }
        .kpi-hint { font-size: 12.5px; color: var(--muted); }
        .kpi-denom { display: flex; align-items: baseline; gap: 6px; }
        .kpi-stack { display: flex; flex-direction: column; gap: 8px; min-width: 0; }

        .donut { flex: none; width: 104px; height: 104px; position: relative; display: grid; place-items: center; }
        .donut svg { display: block; transform: rotate(-90deg); }
        .donut .track { stroke: var(--surface-3); }
        .donut .value { transition: stroke-dashoffset .7s cubic-bezier(.4,0,.2,1), stroke .3s; }
        .donut-center {
            position: absolute; inset: 0; display: grid; place-content: center; text-align: center;
        }
        .donut-num { font-size: 26px; font-weight: 680; letter-spacing: -.04em; font-variant-numeric: tabular-nums; line-height: 1.05; }
        .donut-cap { font-size: 10px; color: var(--faint); letter-spacing: .06em; text-transform: uppercase; font-weight: 600; }
        .v-low, .v-ok { color: var(--ok); }
        .v-mod { color: var(--warn); }
        .v-high { color: var(--bad); }
        .v-none { color: var(--faint); }
        .m-low, .m-ok { stroke: var(--ok); }
        .m-mod { stroke: var(--warn); }
        .m-high { stroke: var(--bad); }
        .m-none { stroke: var(--faint); }

        .meter { height: 6px; border-radius: 999px; background: var(--surface-3); overflow: hidden; }
        .meter-fill { height: 100%; border-radius: 999px; transition: width .5s cubic-bezier(.4,0,.2,1); }
        .fill-low, .fill-ok { background: var(--ok); }
        .fill-mod { background: var(--warn); }
        .fill-high { background: var(--bad); }
        .fill-none { background: var(--faint); }

        .chip {
            display: inline-flex; align-items: center; gap: 5px; width: fit-content;
            padding: 0 9px; border-radius: 999px;
            font-size: 11.5px; font-weight: 560; line-height: 21px; white-space: nowrap;
        }
        .chip-low, .chip-ok { color: var(--ok); background: var(--ok-bg); }
        .chip-mod { color: var(--warn); background: var(--warn-bg); }
        .chip-high { color: var(--bad); background: var(--bad-bg); }
        .chip-info { color: var(--info); background: var(--info-bg); }
        .chip-violet { color: var(--violet); background: var(--violet-bg); }
        .chip-teal { color: var(--teal); background: var(--teal-bg); }
        .chip-none { color: var(--muted); background: var(--surface-2); border: 1px solid var(--border); }

        /* ------------------------------------------------------------ Breakdown */
        .breakdown { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; width: 100%; }
        .bk-item {
            padding: 15px 16px; display: flex; flex-direction: column; gap: 9px;
            transition: border-color .2s, box-shadow .2s;
        }
        .bk-item:hover { box-shadow: var(--shadow); border-color: var(--border-strong); }
        .bk-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
        .bk-name { font-size: 12.5px; font-weight: 550; color: var(--muted); }
        .bk-count { font-size: 22px; font-weight: 650; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
        .bk-track { height: 5px; border-radius: 999px; background: var(--surface-3); overflow: hidden; }
        .bk-fill { height: 100%; border-radius: 999px; width: 0; transition: width .5s cubic-bezier(.4,0,.2,1); }
        .bk-info .bk-fill { background: var(--info); }
        .bk-bad .bk-fill { background: var(--bad); }
        .bk-warn .bk-fill { background: var(--warn); }
        .bk-violet .bk-fill { background: var(--violet); }
        .bk-teal .bk-fill { background: var(--teal); }
        .bk-foot { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 11.5px; color: var(--faint); }
        .bk-foot span:last-child { text-align: right; }

        /* ------------------------------------------------------------ Findings */
        .toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; min-width: 0; max-width: 100%; }
        .search-wrap { flex: 1 1 240px; max-width: 340px; }
        .segmented {
            display: inline-flex; flex: 0 0 auto; width: max-content; max-width: 100%; min-width: 0;
            gap: 2px; padding: 3px;
            background: var(--surface-2); border: 1px solid var(--border); border-radius: 10px;
        }
        .segmented > * { flex: 0 0 auto; align-self: center; }
        .q-btn.seg {
            flex: 0 0 auto; width: auto; min-width: 0;
            min-height: 26px; padding: 0 12px; border-radius: 7px;
            font-size: 12.5px; font-weight: 540; text-transform: none; letter-spacing: 0;
            color: var(--muted);
        }
        .q-btn.seg:hover { color: var(--text); }
        .q-btn.seg-active { background: var(--seg-active); color: var(--text); box-shadow: var(--shadow-sm); }

        .list-head {
            display: grid; align-items: center; gap: 16px;
            grid-template-columns: minmax(0, 1.05fr) 172px 108px 250px;
            padding: 9px 20px; background: var(--surface-2);
            border-bottom: 1px solid var(--border);
            font-size: 11.5px; font-weight: 580; color: var(--faint);
            letter-spacing: .04em; text-transform: uppercase;
        }
        .list-head span:last-child { text-align: right; }
        .row {
            align-items: center; gap: 16px;
            grid-template-columns: minmax(5, 1.05fr) 172px 108px 250px;
            padding: 13px 20px; border-bottom: 1px solid var(--border);
            transition: background .14s;
        }
        .row:last-child { border-bottom: none; }
        .row:hover { background: var(--surface-2); }
        .row-main { display: flex; align-items: center; gap: 12px; min-width: 0; }
        .src-mark {
            width: 32px; height: 32px; border-radius: 9px; flex: none;
            display: grid; place-items: center;
            font-size: 12px; font-weight: 650; letter-spacing: -.02em;
            background: var(--surface-3); color: var(--muted);
        }
        .src-mark.cat-broker { background: var(--info-bg); color: var(--info); }
        .src-mark.cat-breach { background: var(--bad-bg); color: var(--bad); }
        .src-mark.cat-paste  { background: var(--warn-bg); color: var(--warn); }
        .src-mark.cat-doc    { background: var(--violet-bg); color: var(--violet); }
        .src-mark.cat-other  { background: var(--teal-bg); color: var(--teal); }
        .src { display: flex; flex-direction: column; min-width: 0; }
        .src-name { font-weight: 600; font-size: 13.5px; letter-spacing: -.005em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .src-cat { font-size: 12px; color: var(--muted); }
        .row-title { font-size: 13px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .row-actions { display: flex; justify-content: flex-end; align-items: center; gap: 7px; }
        .row.is-removed { background: linear-gradient(90deg, var(--ok-bg) 0, transparent 46%); }
        .row.is-removed:hover { background: var(--surface-2); }
        .status-cell { display: flex; align-items: center; }

        .empty {
            padding: 60px 24px; text-align: center;
            display: flex; flex-direction: column; gap: 8px; align-items: center;
        }
        .empty .ico-box { width: 44px; height: 44px; border-radius: 13px; margin-bottom: 4px; }
        .empty-title { font-weight: 600; font-size: 15px; letter-spacing: -.01em; }
        .empty-sub { color: var(--muted); font-size: 13px; max-width: 46ch; }

        /* ------------------------------------------------------------ Activity */
        .activity { overflow: hidden; }
        .activity .q-item { padding: 15px 20px !important; min-height: 0 !important; }
        .activity .q-item__label { font-size: 14px; font-weight: 600; letter-spacing: -.01em; }
        .activity .q-expansion-item__content { border-top: 1px solid var(--border); }
        .log {
            height: 280px; padding: 14px 16px;
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 12px; line-height: 1.7; color: var(--muted);
            background: var(--surface-2); border: 1px solid var(--border); border-radius: 11px;
        }

        ::-webkit-scrollbar { width: 9px; height: 9px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 9px; border: 2px solid transparent; background-clip: content-box; }
        ::-webkit-scrollbar-thumb:hover { background: var(--faint); background-clip: content-box; }

        @media (prefers-reduced-motion: reduce) {
            * { animation-duration: .001ms !important; transition-duration: .001ms !important; }
        }
        @media (max-width: 1080px) {
            .breakdown { grid-template-columns: repeat(3, 1fr); }
            .row, .list-head { grid-template-columns: minmax(0, 1fr) 150px 100px 210px; gap: 12px; }
        }
        @media (max-width: 1000px) {
            .kpi-row { grid-template-columns: 1fr; }
            .list-head { display: none; }
            .row { grid-template-columns: 1fr; gap: 10px; align-items: start; }
            .row-actions { justify-content: flex-start; flex-wrap: wrap; }
            .row-title { white-space: normal; }
        }
        @media (max-width: 760px) {
            /* stack the scan form: fields full width, CTA on its own line */
            .scan-body { grid-template-columns: minmax(0, 1fr); }
            .scan-cta, .scan-cta .btn, .scan-cta .q-btn { width: 100% !important; }
            .toolbar { width: 100%; }
            .search-wrap { flex: 1 1 100%; max-width: none; }
        }
        @media (max-width: 620px) {
            .page { padding: 22px 16px 56px; }
            .app-header-inner { padding: 0 16px; }
            .hero-title { font-size: 23px; }
            .breakdown { grid-template-columns: repeat(2, 1fr); }
            .brand-sub { display: none; }
            .kpi-main { flex-direction: column; align-items: flex-start; }
        }
    </style>
''')

dark = ui.dark_mode(True)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

state = {'scan_id': None, 'filter': 'All', 'query': '', 'busy': False, 'visible_ids': []}
log_queue = deque()  # thread-safe hand-off from scan threads to the UI log

CATEGORY_META = {
    'Data Broker':      ('Brokers',      'cat-broker', 'info',   'storefront'),
    'Breach Leak':      ('Breach leaks', 'cat-breach', 'bad',    'gpp_maybe'),
    'Paste Leak':       ('Paste dumps',  'cat-paste',  'warn',   'content_paste'),
    'Document Leak':    ('Documents',    'cat-doc',    'violet', 'description'),
    'Gravatar Profile': ('Profiles',     'cat-other',  'teal',   'account_circle'),
}
BREAKDOWN_ORDER = ['Data Broker', 'Breach Leak', 'Paste Leak', 'Document Leak', 'Gravatar Profile']
DONUT_CIRCUMFERENCE = 2 * 3.14159265 * 52  # r = 52


def div(*classes):
    return ui.element('div').classes(' '.join(c for c in classes if c))


def cat_meta(category):
    return CATEGORY_META.get(category, ('Other', 'cat-other', 'teal', 'search'))


def initials(source, category):
    text = (source or category or '?').replace('www.', '').strip()
    parts = [p for p in text.replace('-', ' ').replace('_', ' ').split() if p]
    if not parts:
        return '?'
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def risk_level(score):
    if score >= 60:
        return 'High risk', 'high'
    if score >= 30:
        return 'Moderate risk', 'mod'
    return 'Low risk', 'low'


def cat_level(count):
    if count <= 0:
        return 'clear', 'none'
    if count >= 5:
        return 'elevated', 'high'
    if count >= 2:
        return 'watch', 'mod'
    return 'low', 'low'


def div_icon(tone, icon, size='17px'):
    with div(f'ico-box {tone}'):
        ui.icon(icon).style(f'font-size:{size}')


def donut_svg(offset, tone):
    return (
        '<svg width="104" height="104" viewBox="0 0 120 120">'
        '<circle class="track" cx="60" cy="60" r="52" fill="none" stroke-width="11"/>'
        f'<circle class="value m-{tone}" cx="60" cy="60" r="52" fill="none" stroke-width="11" '
        f'stroke-linecap="round" stroke-dasharray="{DONUT_CIRCUMFERENCE:.1f}" '
        f'stroke-dashoffset="{offset:.1f}"/></svg>'
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def toggle_theme():
    dark.set_value(not dark.value)
    theme_btn.props(f'icon={"light_mode" if dark.value else "dark_mode"}')


with ui.header().classes('app-header'):
    with div('app-header-inner'):
        with div('brand'):
            with div('brand-mark'):
                ui.label('F')
            with div('brand-text'):
                ui.label('Flamingo').classes('brand-name')
                ui.label('Exposure monitoring').classes('brand-sub')

        with div('header-right'):
            with div('status-pill'):
                status_dot = div('status-dot')
                status_text = ui.label('Ready')
            last_scan_label = ui.label('No scans yet').classes('last-scan')
            with div('header-actions'):
                theme_btn = ui.button(icon='light_mode', on_click=toggle_theme) \
                    .props('flat round dense').classes('icon-btn')
                theme_btn.tooltip('Toggle light / dark theme')
                refresh_btn = ui.button(icon='refresh', on_click=lambda: refresh_results_view()) \
                    .props('flat round dense').classes('icon-btn')
                refresh_btn.tooltip('Reload from the local database')

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

with div('page'):

    # --- Hero ---------------------------------------------------------------
    with div('hero'):
        with div():
            ui.label('Exposure report').classes('hero-title')
            ui.label('Find where personal information is exposed, then track every '
                     'removal request through to completion.').classes('hero-sub')
        with div('hero-aside'):
            hero_chip = ui.label('No scan yet').classes('chip chip-none')
            export_btn = ui.button('Export CSV', icon='download') \
                .props('flat no-caps dense').classes('btn btn-quiet')
            export_btn.tooltip('Download the latest report as a CSV file')

    # --- New scan -----------------------------------------------------------
    with div('surface'):
        with div('card-head'):
            with div('card-head-main'):
                div_icon('', 'travel_explore')
                with div():
                    ui.label('New scan').classes('card-title')
                    ui.label('Enter a name, an email address, or both.').classes('card-note')

        with div('card-body'):
            with div('scan-body'):
                name_input = ui.input(label='Full name', placeholder='Jane Doe') \
                    .props('outlined dense clearable').classes('scan-field grow')
                loc_input = ui.input(label='Location', placeholder='Seattle, WA') \
                    .props('outlined dense clearable').classes('scan-field')
                email_input = ui.input(label='Email address', placeholder='jane@example.com') \
                    .props('outlined dense clearable').classes('scan-field grow')
                with div('scan-cta'):
                    scan_btn = ui.button('Run scan', icon='radar') \
                        .props('unelevated no-caps').classes('btn btn-primary')

    # --- KPI tiles ----------------------------------------------------------
    with div('kpi-row'):
        with div('surface', 'kpi'):
            with div('kpi-head'):
                ui.label('Exposure score').classes('kpi-label')
                risk_chip = ui.label('No scan yet').classes('chip chip-none')
            with div('kpi-main'):
                with div('donut'):
                    donut_html = ui.html(donut_svg(DONUT_CIRCUMFERENCE, 'none'))
                    with div('donut-center'):
                        score_label = ui.label('0').classes('donut-num v-none')
                        ui.label('of 100').classes('donut-cap')
                with div('kpi-stack'):
                    score_delta = ui.label('Awaiting first scan').classes('card-note')
                    score_trend = div('')
                    ui.label('Weighted across brokers, breach records, paste dumps '
                             'and public documents.').classes('kpi-hint')

        with div('surface', 'kpi'):
            with div('kpi-head'):
                ui.label('Exposures found').classes('kpi-label')
                div_icon('info', 'manage_search')
            with div('kpi-denom'):
                total_hits_label = ui.label('0').classes('kpi-value')
                ui.label('records').classes('kpi-unit')
            with div('kpi-stack'):
                hits_breakdown = ui.label('No findings yet').classes('kpi-hint')
                with div('meter'):
                    hits_fill = div('meter-fill', 'fill-none').style('width:0%')

        with div('surface', 'kpi'):
            with div('kpi-head'):
                ui.label('Removal progress').classes('kpi-label')
                div_icon('ok', 'task_alt')
            with div('kpi-denom'):
                progress_label = ui.label('0%').classes('kpi-value')
                ui.label('resolved').classes('kpi-unit')
            with div('kpi-stack'):
                progress_hint = ui.label('0 of 0 resolved').classes('kpi-hint')
                with div('meter'):
                    progress_fill = div('meter-fill', 'fill-ok').style('width:0%')
                progress_eta = ui.label('Run a scan to start remediation.').classes('card-note')

    # --- Source breakdown ---------------------------------------------------
    breakdown_container = div('breakdown')

    # --- Findings -----------------------------------------------------------
    with div('surface'):
        with div('card-head'):
            with div('card-head-main'):
                div_icon('', 'shield_moon')
                with div():
                    ui.label('Findings').classes('card-title')
                    shown_label = ui.label('No scans yet').classes('card-note')

            with div('toolbar'):
                search_input = ui.input(placeholder='Search source or title') \
                    .props('outlined dense clearable').classes('search-wrap')
                search_input.on_value_change(lambda e: set_query(e.value or ''))

                filter_buttons = {}
                with div('segmented'):
                    for _label in ('All', 'Pending', 'Removed'):
                        filter_buttons[_label] = ui.button(
                            _label, on_click=lambda _, f=_label: set_filter(f)
                        ).props('flat no-caps dense').classes('seg')

                bulk_btn = ui.button('Mark all removed', icon='done_all') \
                    .props('flat no-caps dense').classes('btn btn-quiet')
                bulk_btn.tooltip('Mark every pending finding in the current view as removed')

        with div('list-head'):
            ui.label('Source')
            ui.label('Description')
            ui.label('Status')
            ui.label('Actions')

        table_container = div()

    # --- Scan activity ------------------------------------------------------
    with ui.expansion().classes('surface activity') as activity_panel:
        with activity_panel.add_slot('header'):
            with div('card-head-main').style('flex:1'):
                div_icon('', 'terminal')
                with div():
                    ui.label('Scan activity').classes('card-title')
                    ui.label('Live log from the scanner engine').classes('card-note')
            log_count = ui.label('idle').classes('card-note')
        with div('card-body'):
            activity_log = ui.log(max_lines=400).classes('log w-full')


# ---------------------------------------------------------------------------
# Controller logic
# ---------------------------------------------------------------------------

def set_busy(busy, text):
    state['busy'] = busy
    status_text.set_text(text)
    status_dot.classes(replace='status-dot busy' if busy else 'status-dot')
    if busy:
        scan_btn.props('loading')
        scan_btn.disable()
    else:
        scan_btn.props(remove='loading')
        scan_btn.enable()


def log(msg):
    """Called from worker threads; the timer below flushes it to the UI."""
    stamp = time.strftime('%H:%M:%S')
    for line in str(msg).splitlines() or ['']:
        log_queue.append(f'{stamp}  {line}' if line.strip() else '')


def flush_log():
    pushed = 0
    while log_queue:
        activity_log.push(log_queue.popleft())
        pushed += 1
    if pushed:
        log_count.set_text('streaming' if state['busy'] else 'up to date')


ui.timer(0.2, flush_log)


def recent_scans(limit=14):
    """Score history for the trend sparkline (oldest first)."""
    try:
        with sqlite3.connect(tracker.DB_FILE) as conn:
            rows = conn.execute(
                'SELECT score FROM scans ORDER BY id DESC LIMIT ?', (limit,)
            ).fetchall()
        return [r[0] if r[0] is not None else 0 for r in reversed(rows)]
    except Exception:
        return []


def render_sparkline(scores):
    """Small inline-SVG trend line of recent exposure scores."""
    score_trend.clear()
    if len(scores) < 2:
        score_trend.classes(replace='')
        return
    width, height, pad = 200.0, 44.0, 6.0
    low, high = min(scores), max(scores)
    span = (high - low) or 1
    step = (width - 2 * pad) / (len(scores) - 1)
    pts = []
    for index, value in enumerate(scores):
        x = pad + index * step
        y = height - pad - ((value - low) / span) * (height - 2 * pad)
        pts.append(f'{x:.1f},{y:.1f}')
    dots = ''.join(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="2.6"/>' for p in pts)
    score_trend.classes(replace='')
    with score_trend:
        with div('kpi-stack'):
            ui.html(
                f'<svg class="spark" viewBox="0 0 {width:.0f} {height:.0f}" '
                f'preserveAspectRatio="none"><polyline points="{" ".join(pts)}"/>{dots}</svg>'
            )
            with div('spark-legend'):
                ui.label(f'oldest · min {low}')
                ui.label(f'latest · max {high}')


def set_filter(value):
    state['filter'] = value
    refresh_results_view()


def set_query(value):
    state['query'] = value
    refresh_results_view()


def make_toggle(finding_id, current_status):
    def handler():
        new_status = 'Pending' if current_status == 'Removed' else 'Removed'
        tracker.update_finding_status(finding_id, new_status)
        tracker.recalculate_active_score(state['scan_id'])
        ui.notify(f'Marked as {new_status.lower()}', position='bottom-right', timeout=1500)
        refresh_results_view()
    return handler


def mark_all_removed():
    targets = state.get('visible_ids') or []
    if not targets:
        ui.notify('Nothing pending in this view.', position='bottom-right', timeout=1600)
        return
    for finding_id in targets:
        tracker.update_finding_status(finding_id, 'Removed')
    tracker.recalculate_active_score(state['scan_id'])
    ui.notify(f'{len(targets)} finding(s) marked as removed.', type='positive',
              position='bottom-right', timeout=1800)
    refresh_results_view()


def export_csv():
    _scan_id, _score, _status, findings = tracker.get_latest_scan_findings()
    if not findings:
        ui.notify('No findings to export yet.', type='warning', position='bottom-right')
        return

    def cell(value):
        return '"' + str(value if value is not None else '').replace('"', '""') + '"'

    lines = ['source,category,title,status,url,opt_out_url']
    for item in findings:
        lines.append(','.join(cell(item[key]) for key in
                              ('source', 'category', 'title', 'status', 'url', 'opt_out_url')))
    stamp = time.strftime('%Y%m%d-%H%M')
    try:
        ui.download('\n'.join(lines).encode('utf-8'),
                    f'flamingo-exposure-{stamp}.csv')
        ui.notify('Report exported.', type='positive', position='bottom-right')
    except Exception as exc:
        ui.notify(f'Export failed: {exc}', type='negative', position='bottom-right')


export_btn.on_click(export_csv)
bulk_btn.on_click(mark_all_removed)


def render_empty(icon, title, message):
    with table_container:
        with div('empty'):
            div_icon('', icon, '22px')
            ui.label(title).classes('empty-title')
            ui.label(message).classes('empty-sub')


def render_breakdown(findings):
    counts = {}
    for item in findings:
        counts[item['category']] = counts.get(item['category'], 0) + 1
    peak = max(counts.values()) if counts else 0

    breakdown_container.clear()
    with breakdown_container:
        for category in BREAKDOWN_ORDER:
            short, _mark, tone, icon = cat_meta(category)
            count = counts.get(category, 0)
            label, _key = cat_level(count)
            share = int(count / len(findings) * 100) if findings else 0
            with div('surface', 'bk-item', f'bk-{tone}'):
                with div('bk-top'):
                    ui.label(short).classes('bk-name')
                    div_icon(tone, icon)
                with div('bk-top'):
                    ui.label(str(count)).classes('bk-count')
                    ui.label(label).classes('chip chip-' + ('none' if count == 0 else tone))
                with div('bk-track'):
                    div('bk-fill').style(f'width:{int(count / peak * 100) if peak else 0}%')
                with div('bk-foot'):
                    ui.label(category)
                    ui.label(f'{share}%')


def refresh_results_view():
    """Renders findings, updates the summary tiles, and applies the active filter."""
    table_container.clear()

    scan_id, active_score, _status, findings = tracker.get_latest_scan_findings()
    state['scan_id'] = scan_id

    total_items = len(findings)
    removed_items = sum(1 for item in findings if item['status'] == 'Removed')
    pending_items = total_items - removed_items
    prog_pct = int((removed_items / total_items) * 100) if total_items > 0 else 0

    # --- Exposure score tile
    level, key = risk_level(active_score) if scan_id else ('No scan yet', 'none')
    score_label.set_text(str(active_score))
    score_label.classes(replace=f'donut-num v-{key}')
    clamped = min(max(active_score, 0), 100)
    donut_html.set_content(donut_svg(DONUT_CIRCUMFERENCE * (1 - clamped / 100), key))
    risk_chip.set_text(level)
    risk_chip.classes(replace=f'chip chip-{key}')

    history = recent_scans()
    render_sparkline(history)
    if len(history) >= 2:
        delta = history[-1] - history[-2]
        if delta:
            tone = 'chip-high' if delta > 0 else 'chip-ok'
            score_delta.set_text(f'{"+" if delta > 0 else ""}{delta} vs previous scan')
            score_delta.classes(replace=f'chip {tone}')
        else:
            score_delta.set_text('Unchanged since the last scan')
            score_delta.classes(replace='card-note')
    elif scan_id:
        score_delta.set_text('First recorded scan')
        score_delta.classes(replace='card-note')
    else:
        score_delta.set_text('Awaiting first scan')
        score_delta.classes(replace='card-note')

    # --- Totals tile
    total_hits_label.set_text(str(total_items))
    by_cat = {}
    for item in findings:
        by_cat[item['category']] = by_cat.get(item['category'], 0) + 1
    top = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)[:2]
    hits_breakdown.set_text(
        ' · '.join(f'{count} {cat_meta(cat)[0].lower()}' for cat, count in top) if top
        else f'Across {len(BREAKDOWN_ORDER)} source categories'
    )
    hits_fill.style(replace=f'width:{min(total_items * 6, 100)}%')
    hits_fill.classes(replace=f'meter-fill {"fill-none" if not total_items else "fill-low"}')

    # --- Remediation tile
    progress_label.set_text(f'{prog_pct}%')
    progress_fill.style(replace=f'width:{prog_pct}%')
    progress_hint.set_text(f'{removed_items} of {total_items} resolved')
    if not total_items:
        progress_eta.set_text('Run a scan to start remediation.')
    elif pending_items == 0:
        progress_eta.set_text('All clear — every finding is marked removed.')
    else:
        progress_eta.set_text(f'{pending_items} removal request(s) still open.')

    hero_chip.set_text(level if scan_id else 'No scan yet')
    hero_chip.classes(replace=f'chip chip-{key}')
    last_scan_label.set_text(
        f'Last scan {time.strftime("%b %d, %H:%M")}' if scan_id else 'No scans yet'
    )

    # --- Filter control
    for label, btn in filter_buttons.items():
        btn.classes(replace='seg seg-active' if label == state['filter'] else 'seg')

    filtered = findings
    if state['filter'] != 'All':
        filtered = [f for f in filtered if f['status'] == state['filter']]
    query = state['query'].strip().lower()
    if query:
        filtered = [f for f in filtered
                    if query in (f['source'] or '').lower() or query in (f['title'] or '').lower()]

    shown_label.set_text(f'Showing {len(filtered)} of {total_items}' if total_items else 'No scans yet')

    pending_visible = [f['id'] for f in filtered if f['status'] != 'Removed']
    state['visible_ids'] = pending_visible
    bulk_btn.set_visibility(bool(pending_visible))

    render_breakdown(findings)

    if total_items == 0:
        render_empty('radar', 'No results yet',
                     'Run a scan to populate this report. Risk score, findings and '
                     'removal tracking all appear here.')
        return
    if not filtered:
        reason = f'No findings match "{state["query"]}".' if query else \
            f'No findings are currently marked {state["filter"].lower()}.'
        render_empty('filter_alt', 'Nothing to show', reason)
        return

    for item in filtered:
        is_removed = item['status'] == 'Removed'
        _short, mark, _tone, _icon = cat_meta(item['category'])

        with table_container:
            with div('row', 'is-removed' if is_removed else ''):
                with div('row-main'):
                    with div(f'src-mark {mark}'):
                        ui.label(initials(item['source'], item['category']))
                    with div('src'):
                        ui.label(item['source']).classes('src-name')
                        ui.label(item['category']).classes('src-cat')

                ui.label(item['title']).classes('row-title').tooltip(item['title'])

                with div('status-cell'):
                    ui.label('Removed' if is_removed else 'Pending') \
                        .classes('chip chip-ok' if is_removed else 'chip chip-mod')

                with div('row-actions'):
                    if item['url'] and item['url'] != 'N/A':
                        report_link = ui.link(target=item['url'], new_tab=True).classes('btn btn-icon')
                        with report_link:
                            ui.icon('open_in_new', size='16px')
                        report_link.tooltip('Open the public listing')

                    if item['opt_out_url'] and item['opt_out_url'] != 'N/A':
                        ui.link('Opt out', item['opt_out_url'], new_tab=True).classes('btn link-out')

                    ui.button(
                        'Reopen' if is_removed else 'Mark removed',
                        icon='undo' if is_removed else 'check',
                        on_click=make_toggle(item['id'], item['status']),
                    ).props('flat no-caps dense').classes('btn btn-quiet' if is_removed else 'btn')


async def start_scan_workflow():
    """Runs the full scanning sequence without blocking the UI."""
    if state['busy']:
        return

    name = name_input.value.strip()
    loc = loc_input.value.strip()
    email = email_input.value.strip()

    if not name and not email:
        ui.notify('Enter a name or an email address to start a scan.', type='warning', position='top')
        return

    activity_log.clear()
    activity_panel.set_value(True)
    set_busy(True, 'Scanning')

    log('Scan started')
    log(f'  Name      {name or "-"}')
    log(f'  Location  {loc or "-"}')
    log(f'  Email     {email or "-"}')
    log('')

    try:
        # 1. Data brokers
        broker_hits = await run.io_bound(
            osint_engine.scan_data_brokers, name, loc, log_callback=log) if name else []

        # 2. Search-engine dork scans (pastes, files)
        dork_hits = await run.io_bound(
            osint_engine.scan_google_dorks, name, email, log_callback=log)

        # 3. Breach data
        breach_hits = await run.io_bound(
            osint_engine.check_email_breaches, email, log_callback=log) if email else []

        # 4. Gravatar
        grav_hit = await run.io_bound(
            osint_engine.check_gravatar_profile, email, log_callback=log) if email else False

        all_findings = broker_hits + dork_hits + breach_hits
        if grav_hit:
            all_findings.append({
                'category': 'Gravatar Profile',
                'source': 'Gravatar',
                'title': 'Public Gravatar profile linked to email',
                'url': 'https://gravatar.com',
                'opt_out_url': 'N/A',
            })

        raw_score = min(
            (len(broker_hits) * 5) + (len(breach_hits) * 8) + (len(dork_hits) * 5) + (10 if grav_hit else 0),
            100,
        )
        raw_status = risk_level(raw_score)[0]

        tracker.save_scan_results(
            {'name': name, 'location': loc, 'email': email}, raw_score, raw_status, all_findings)

        log('')
        log(f'Scan complete. {len(all_findings)} finding(s) saved.')
        state['filter'] = 'All'
        state['query'] = ''
        search_input.set_value('')
        refresh_results_view()
        ui.notify(f'Scan complete: {len(all_findings)} finding(s)', type='positive', position='bottom-right')

    except Exception as exc:  # keep the UI usable if a source fails
        log(f'Scan failed: {exc}')
        ui.notify(f'Scan failed: {exc}', type='negative', position='top')
    finally:
        flush_log()
        set_busy(False, 'Ready')


scan_btn.on_click(start_scan_workflow)
for _field in (name_input, loc_input, email_input):
    _field.on('keydown.enter', start_scan_workflow)

ui.keyboard(on_key=lambda e: search_input.run_method('focus')
           if e.action.keydown and e.key == 'k' and (e.modifiers.ctrl or e.modifiers.meta) else None)

# Render initial database view on page launch
refresh_results_view()

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='Flamingo | Exposure monitoring', port=PORT)
