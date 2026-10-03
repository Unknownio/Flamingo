# app.py

import time
from collections import deque

from nicegui import run, ui

import osint_engine
import tracker

# Initialize local SQLite DB
tracker.init_db()

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

ui.add_head_html('''
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
    <style>
        :root {
            --bg: #f5f6f8;
            --surface: #ffffff;
            --surface-2: #f9fafb;
            --seg-active: #ffffff;
            --border: #e3e6eb;
            --text: #14171c;
            --muted: #667085;
            --faint: #98a2b3;
            --accent: #2b59c3;
            --accent-ink: #ffffff;
            --ok: #067647;   --ok-bg: #e8f6ee;
            --warn: #a15c07; --warn-bg: #fdf3e1;
            --bad: #b42318;  --bad-bg: #fdecea;
            --q-primary: #2b59c3;
        }
        body.body--dark {
            --bg: #0e1013;
            --surface: #15181c;
            --surface-2: #1a1e23;
            --seg-active: #272c34;
            --border: #262b32;
            --text: #e7e9ec;
            --muted: #8c95a3;
            --faint: #5f6877;
            --accent: #7d9bff;
            --accent-ink: #0e1013;
            --ok: #4cc38a;   --ok-bg: rgba(76, 195, 138, .12);
            --warn: #e0a458; --warn-bg: rgba(224, 164, 88, .12);
            --bad: #ef7b6f;  --bad-bg: rgba(239, 123, 111, .12);
            --q-primary: #7d9bff;
        }

        html, body { background: var(--bg); }
        body {
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }
        .nicegui-content { padding: 0 !important; gap: 0 !important; }

        /* Header */
        .app-header {
            background: var(--surface) !important;
            color: var(--text) !important;
            border-bottom: 1px solid var(--border);
            box-shadow: none !important;
            padding: 0 !important;
            display: block !important;
        }
        .app-header-inner {
            max-width: 1120px; width: 100%; height: 56px;
            margin: 0 auto; padding: 0 24px;
            display: flex; align-items: center; justify-content: space-between;
        }
        .brand { display: flex; align-items: center; gap: 10px; }
        .brand-mark {
            width: 26px; height: 26px; border-radius: 7px;
            background: var(--accent); color: var(--accent-ink);
            display: grid; place-items: center;
            font-weight: 700; font-size: 14px;
        }
        .brand-name { font-weight: 650; font-size: 15px; letter-spacing: -.01em; }
        .brand-sep { width: 1px; height: 16px; background: var(--border); }
        .brand-sub { color: var(--muted); font-size: 13px; }
        .header-right { display: flex; align-items: center; gap: 16px; }
        .status { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }
        .status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }
        .status-dot.busy { background: var(--warn); }

        /* Layout */
        .page {
            width: 100%; max-width: 1120px; margin: 0 auto;
            padding: 32px 24px 64px;
            display: flex; flex-direction: column; gap: 20px;
        }
        .page-title { font-size: 22px; font-weight: 650; letter-spacing: -.02em; line-height: 1.25; }
        .page-sub { color: var(--muted); font-size: 14px; margin-top: 2px; }
        .surface { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; width: 100%; }
        .card-head {
            display: flex; align-items: center; justify-content: space-between; gap: 16px;
            padding: 14px 20px; border-bottom: 1px solid var(--border);
        }
        .card-title { font-size: 14px; font-weight: 600; }
        .card-note { font-size: 13px; color: var(--muted); }
        .card-body { padding: 20px; }

        /* Form */
        .form-grid {
            display: grid; gap: 12px; align-items: start;
            grid-template-columns: 1.2fr 1fr 1.2fr auto;
        }
        .q-field--outlined .q-field__control { border-radius: 8px; }
        .q-field--outlined .q-field__control:before { border-color: var(--border) !important; }
        .q-field--outlined:hover .q-field__control:before { border-color: var(--faint) !important; }
        .q-field__native, .q-field__label { font-size: 14px; }

        /* Buttons */
        .btn, .q-btn.btn {
            display: inline-flex; align-items: center; justify-content: center; gap: 6px;
            height: 32px; min-height: 32px; padding: 0 12px;
            border: 1px solid var(--border); border-radius: 7px;
            background: var(--surface); color: var(--text);
            font-size: 13px; font-weight: 500; letter-spacing: 0; text-transform: none;
            text-decoration: none; cursor: pointer; white-space: nowrap;
            transition: background .15s, border-color .15s;
        }
        .btn:hover, .q-btn.btn:hover { background: var(--surface-2); border-color: var(--faint); }
        .btn-icon, .q-btn.btn-icon { width: 32px; padding: 0; }
        .q-btn.btn-primary, .btn-primary {
            height: 40px; padding: 0 20px; font-size: 14px;
            background: var(--accent); border-color: var(--accent); color: var(--accent-ink);
        }
        .q-btn.btn-primary:hover, .btn-primary:hover { background: var(--accent); border-color: var(--accent); filter: brightness(1.08); }
        .q-btn.icon-btn {
            width: 32px; height: 32px; min-height: 32px; padding: 0;
            border-radius: 7px; color: var(--muted);
        }

        /* Summary tiles */
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; width: 100%; }
        .stat { padding: 18px 20px; display: flex; flex-direction: column; gap: 4px; }
        .stat-label { font-size: 13px; font-weight: 500; color: var(--muted); }
        .stat-row { display: flex; align-items: baseline; gap: 6px; }
        .stat-value {
            font-size: 30px; font-weight: 650; letter-spacing: -.03em; line-height: 1.15;
            font-variant-numeric: tabular-nums;
        }
        .stat-unit { color: var(--faint); font-size: 14px; }
        .stat-hint { font-size: 12.5px; color: var(--muted); margin-top: 2px; }
        .meter { height: 4px; border-radius: 4px; background: var(--border); overflow: hidden; margin-top: 8px; }
        .meter-fill { height: 100%; border-radius: 4px; transition: width .4s ease; }
        .fill-low, .fill-ok { background: var(--ok); }
        .fill-mod { background: var(--warn); }
        .fill-high { background: var(--bad); }
        .fill-none { background: var(--faint); }

        .chip {
            display: inline-flex; align-items: center; width: fit-content;
            padding: 0 9px; border-radius: 999px;
            font-size: 12px; font-weight: 500; line-height: 20px;
        }
        .chip-low, .chip-ok { color: var(--ok); background: var(--ok-bg); }
        .chip-mod { color: var(--warn); background: var(--warn-bg); }
        .chip-high { color: var(--bad); background: var(--bad-bg); }
        .chip-none { color: var(--muted); background: var(--surface-2); border: 1px solid var(--border); }

        /* Segmented filter */
        .segmented {
            display: inline-flex; gap: 2px; padding: 2px;
            background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px;
        }
        .q-btn.seg {
            min-height: 28px; padding: 0 12px; border-radius: 6px;
            font-size: 13px; font-weight: 500; text-transform: none; letter-spacing: 0;
            color: var(--muted);
        }
        .q-btn.seg-active { background: var(--seg-active); color: var(--text); box-shadow: 0 1px 2px rgba(16, 24, 40, .1); }

        /* Findings list */
        .row {
            display: grid; align-items: center; gap: 16px;
            grid-template-columns: 190px minmax(0, 1fr) 90px 270px;
            padding: 12px 20px; border-bottom: 1px solid var(--border);
        }
        .row:last-child { border-bottom: none; }
        .row:not(.row-head):hover { background: var(--surface-2); }
        .row-head {
            padding: 9px 20px; background: var(--surface-2);
            font-size: 12px; font-weight: 500; color: var(--muted);
        }
        .src { display: flex; flex-direction: column; min-width: 0; }
        .src-name { font-weight: 600; font-size: 13.5px; }
        .src-cat { font-size: 12px; color: var(--muted); }
        .row-title { font-size: 13.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .row-actions { display: flex; justify-content: flex-end; align-items: center; gap: 8px; }
        .empty { padding: 56px 20px; text-align: center; display: flex; flex-direction: column; gap: 2px; align-items: center; }
        .empty-title { font-weight: 600; font-size: 14px; }
        .empty-sub { color: var(--muted); font-size: 13px; }

        /* Activity log */
        .activity .q-item { padding: 14px 20px; min-height: 0; font-size: 14px; font-weight: 600; }
        .activity .q-expansion-item__content { border-top: 1px solid var(--border); }
        .log {
            height: 260px; padding: 12px 14px;
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            font-size: 12px; line-height: 1.65; color: var(--muted);
            background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px;
        }

        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 8px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--faint); }

        @media (max-width: 900px) {
            .stats, .form-grid { grid-template-columns: 1fr; }
            .row { grid-template-columns: 1fr; gap: 8px; }
            .row-head { display: none; }
            .row-actions { justify-content: flex-start; flex-wrap: wrap; }
            .brand-sep, .brand-sub { display: none; }
        }
    </style>
''')

dark = ui.dark_mode(True)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

state = {'scan_id': None, 'filter': 'All', 'busy': False}
log_queue = deque()  # thread-safe hand-off from scan threads to the UI log


def div(*classes):
    return ui.element('div').classes(' '.join(classes))


def risk_level(score):
    if score >= 60:
        return 'High', 'high'
    if score >= 30:
        return 'Moderate', 'mod'
    return 'Low', 'low'


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
            ui.label('Flamingo').classes('brand-name')
            div('brand-sep')
            ui.label('Exposure monitoring').classes('brand-sub')

        with div('header-right'):
            with div('status'):
                status_dot = div('status-dot')
                status_text = ui.label('Ready')
            theme_btn = ui.button(icon='light_mode', on_click=toggle_theme) \
                .props('flat round dense').classes('icon-btn')
            theme_btn.tooltip('Toggle light / dark theme')

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

with div('page'):

    with div():
        ui.label('Exposure report').classes('page-title')
        ui.label('Find where personal information is exposed, then track each removal request to completion.') \
            .classes('page-sub')

    # --- New scan -----------------------------------------------------------
    with div('surface'):
        with div('card-head'):
            ui.label('New scan').classes('card-title')
            ui.label('Enter a name, an email address, or both.').classes('card-note')
        with div('card-body'):
            with div('form-grid'):
                name_input = ui.input(label='Full name').props('outlined dense')
                loc_input = ui.input(label='Location', placeholder='City, State').props('outlined dense')
                email_input = ui.input(label='Email address').props('outlined dense')
                scan_btn = ui.button('Run scan').props('unelevated no-caps').classes('btn btn-primary')

    # --- Summary ------------------------------------------------------------
    with div('stats'):
        with div('surface', 'stat'):
            ui.label('Exposure score').classes('stat-label')
            with div('stat-row'):
                score_label = ui.label('0').classes('stat-value')
                ui.label('/ 100').classes('stat-unit')
            with div('meter'):
                risk_fill = div('meter-fill', 'fill-none').style('width:0%')
            risk_chip = ui.label('No scan yet').classes('chip chip-none').style('margin-top:8px')

        with div('surface', 'stat'):
            ui.label('Exposures found').classes('stat-label')
            total_hits_label = ui.label('0').classes('stat-value')
            ui.label('Across brokers, breach records and search results').classes('stat-hint')

        with div('surface', 'stat'):
            ui.label('Removed').classes('stat-label')
            progress_label = ui.label('0%').classes('stat-value')
            with div('meter'):
                progress_fill = div('meter-fill', 'fill-ok').style('width:0%')
            progress_hint = ui.label('0 of 0 resolved').classes('stat-hint')

    # --- Findings -----------------------------------------------------------
    with div('surface'):
        with div('card-head'):
            with ui.element('div').style('display:flex;align-items:baseline;gap:12px'):
                ui.label('Findings').classes('card-title')
                shown_label = ui.label('').classes('card-note')

            filter_buttons = {}
            with div('segmented'):
                for _label in ('All', 'Pending', 'Removed'):
                    filter_buttons[_label] = ui.button(
                        _label, on_click=lambda _, f=_label: set_filter(f)
                    ).props('flat no-caps dense').classes('seg')

        with div('row', 'row-head'):
            ui.label('Source')
            ui.label('Description')
            ui.label('Status')
            ui.label('')

        table_container = div()

    # --- Scan activity ------------------------------------------------------
    activity_panel = ui.expansion('Scan activity').classes('surface activity')
    with activity_panel:
        with div('card-body'):
            activity_log = ui.log(max_lines=300).classes('log w-full')


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
    while log_queue:
        activity_log.push(log_queue.popleft())


ui.timer(0.2, flush_log)


def set_filter(value):
    state['filter'] = value
    refresh_results_view()


def make_toggle(finding_id, current_status):
    def handler():
        new_status = 'Pending' if current_status == 'Removed' else 'Removed'
        tracker.update_finding_status(finding_id, new_status)
        tracker.recalculate_active_score(state['scan_id'])
        ui.notify(f'Marked as {new_status.lower()}', position='bottom-right', timeout=1500)
        refresh_results_view()
    return handler


def render_empty(title, message):
    with table_container:
        with div('empty'):
            ui.label(title).classes('empty-title')
            ui.label(message).classes('empty-sub')


def refresh_results_view():
    """Renders findings, updates the summary tiles, and applies the active filter."""
    table_container.clear()

    scan_id, active_score, _status, findings = tracker.get_latest_scan_findings()
    state['scan_id'] = scan_id

    total_items = len(findings)
    removed_items = sum(1 for item in findings if item['status'] == 'Removed')
    prog_pct = int((removed_items / total_items) * 100) if total_items > 0 else 0

    # Summary tiles
    level, key = risk_level(active_score) if scan_id else ('No scan yet', 'none')
    score_label.set_text(str(active_score))
    risk_fill.style(replace=f'width:{min(max(active_score, 0), 100)}%')
    risk_fill.classes(replace=f'meter-fill fill-{key}')
    risk_chip.set_text(level)
    risk_chip.classes(replace=f'chip chip-{key}')

    total_hits_label.set_text(str(total_items))
    progress_label.set_text(f'{prog_pct}%')
    progress_fill.style(replace=f'width:{prog_pct}%')
    progress_hint.set_text(f'{removed_items} of {total_items} resolved')

    # Filter control
    for label, btn in filter_buttons.items():
        btn.classes(replace='seg seg-active' if label == state['filter'] else 'seg')

    filtered = findings
    if state['filter'] != 'All':
        filtered = [f for f in findings if f['status'] == state['filter']]
    shown_label.set_text(f'Showing {len(filtered)} of {total_items}' if total_items else '')

    if total_items == 0:
        render_empty('No results yet', 'Run a scan to populate this report.')
        return
    if not filtered:
        render_empty('Nothing to show', f'No findings are currently marked {state["filter"].lower()}.')
        return

    for item in filtered:
        is_removed = item['status'] == 'Removed'
        with table_container:
            with div('row'):
                with div('src'):
                    ui.label(item['source']).classes('src-name')
                    ui.label(item['category']).classes('src-cat')

                ui.label(item['title']).classes('row-title').tooltip(item['title'])

                ui.label('Removed' if is_removed else 'Pending') \
                    .classes('chip chip-ok' if is_removed else 'chip chip-mod')

                with div('row-actions'):
                    if item['url'] and item['url'] != 'N/A':
                        view_link = ui.link(target=item['url'], new_tab=True).classes('btn btn-icon')
                        with view_link:
                            ui.icon('open_in_new', size='16px')
                        view_link.tooltip('Open listing')

                    if item['opt_out_url'] and item['opt_out_url'] != 'N/A':
                        ui.link('Opt out', item['opt_out_url'], new_tab=True).classes('btn')

                    ui.button(
                        'Reopen' if is_removed else 'Mark removed',
                        on_click=make_toggle(item['id'], item['status']),
                    ).props('flat no-caps dense').classes('btn')


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
            osint_engine.scan_email_breaches, email, log_callback=log) if email else []

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

# Render initial database view on page launch
refresh_results_view()

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='Flamingo | Exposure monitoring', port=2525)