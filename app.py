# app.py

from nicegui import ui
import osint_engine
import tracker

# Initialize local SQLite DB
tracker.init_db()

# --- Custom Styling & Fonts ---
ui.add_head_html('''
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;600&display=swap">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: #090d16;
            color: #e2e8f0;
        }
        .cyber-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(51, 65, 85, 0.6);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .cyber-card:hover {
            border-color: rgba(14, 165, 233, 0.4);
            box-shadow: 0 0 20px rgba(14, 165, 233, 0.1);
        }
        .terminal-box {
            font-family: 'JetBrains Mono', monospace;
            background: #030712;
            border: 1px solid #1e293b;
        }
        .glow-red { box-shadow: 0 0 25px rgba(239, 68, 68, 0.25); }
        .glow-green { box-shadow: 0 0 25px rgba(16, 185, 129, 0.25); }
        .glow-cyan { box-shadow: 0 0 25px rgba(6, 182, 212, 0.25); }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #090d16; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #0ea5e9; }
    </style>
''')

ui.dark_mode(True)

# State variables
scan_id = None
current_filter = "All"

# --- TOP NAVIGATION BAR ---
with ui.header().classes('bg-slate-950/80 border-b border-slate-800 backdrop-blur-md px-8 py-4 flex justify-between items-center'):
    with ui.row().classes('items-center gap-3'):
        ui.icon('radar', size='md', color='cyan-4')
        with ui.column().classes('gap-0'):
            ui.label('FLAMINGO // OSINT').classes('text-lg font-black tracking-widest text-cyan-400')
            ui.label('EXPOSURE RECON & REMEDATION ENGINE').classes('text-[10px] text-slate-500 font-mono tracking-wider')
    
    with ui.row().classes('items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-full border border-slate-800'):
        ui.element('div').classes('w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse')
        ui.label('SYSTEM ACTIVE').classes('text-xs font-mono text-emerald-400 font-bold tracking-wider')

# --- MAIN DASHBOARD CONTAINER ---
with ui.column().classes('max-w-7xl mx-auto p-6 w-full gap-6'):

    # 1. SEARCH & TARGET INPUT PANEL
    with ui.card().classes('cyber-card w-full p-6 rounded-2xl'):
        with ui.row().classes('items-center justify-between mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('person_search', size='sm', color='cyan-4')
                ui.label('TARGET PROFILER').classes('text-sm font-bold tracking-wider text-slate-300 font-mono')
            ui.label('Step 1: Input Identity Vectors').classes('text-xs text-slate-500')

        with ui.row().classes('w-full gap-4 items-center'):
            name_input = ui.input(placeholder='Target Full Name').props('outlined dense dark icon=person color=cyan').classes('flex-1')
            loc_input = ui.input(placeholder='City, State (e.g. Seattle, WA)').props('outlined dense dark icon=place color=cyan').classes('flex-1')
            email_input = ui.input(placeholder='Target Email Address').props('outlined dense dark icon=email color=cyan').classes('flex-1')
            
            scan_btn = ui.button('RUN RECON SCAN', icon='radar').props('unelevated color=red-7').classes('font-bold px-6 py-2 rounded-xl text-xs tracking-wider glow-red transition-all hover:scale-105')

    # 2. METRICS & RISK STATUS GRID
    with ui.row().classes('w-full gap-4'):
        # Active Risk Score Gauge
        with ui.card().classes('cyber-card flex-1 p-5 rounded-2xl flex flex-col justify-between items-center text-center relative overflow-hidden'):
            ui.label('ACTIVE EXPOSURE SCORE').classes('text-[11px] font-mono font-bold text-slate-400 tracking-wider')
            score_label = ui.label('0').classes('text-6xl font-black text-red-500 my-1 font-mono tracking-tight')
            status_badge = ui.badge('RAW ENGINE', color='slate-800', text_color='slate-400').props('rounded font-mono text-[10px]')

        # Total Detected Exposure Points
        with ui.card().classes('cyber-card flex-1 p-5 rounded-2xl flex flex-col justify-between'):
            with ui.row().classes('items-center justify-between'):
                ui.label('TOTAL EXPOSURES').classes('text-[11px] font-mono font-bold text-slate-400 tracking-wider')
                ui.icon('warning', size='xs', color='amber-4')
            total_hits_label = ui.label('0').classes('text-4xl font-bold text-white my-1 font-mono')
            ui.label('Tracked across 30+ sources').classes('text-xs text-slate-500')

        # Remediation Progress Gauge
        with ui.card().classes('cyber-card flex-1 p-5 rounded-2xl flex flex-col justify-between'):
            with ui.row().classes('items-center justify-between'):
                ui.label('REMEDIATION').classes('text-[11px] font-mono font-bold text-slate-400 tracking-wider')
                ui.icon('check_circle', size='xs', color='emerald-4')
            progress_label = ui.label('0%').classes('text-4xl font-bold text-emerald-400 my-1 font-mono')
            progress_bar = ui.linear_progress(value=0.0, color='emerald-5').props('instant-feedback rounded').classes('h-1.5')

    # 3. LIVE TERMINAL FEED & EXPOSURE MAP
    with ui.row().classes('w-full gap-6 items-start'):
        
        # Left: Findings & Opt-Out Action Center
        with ui.card().classes('cyber-card flex-[3] p-6 rounded-2xl gap-4'):
            with ui.row().classes('w-full items-center justify-between border-b border-slate-800 pb-4'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('list_alt', size='sm', color='cyan-4')
                    ui.label('EXPOSURE FINDINGS & REMOVALS').classes('text-sm font-bold tracking-wider text-slate-300 font-mono')
                
                # Filter Toggle Buttons
                with ui.row().classes('gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800'):
                    def set_filter(f):
                        global current_filter
                        current_filter = f
                        refresh_results_view()
                        
                    ui.button('All', on_click=lambda: set_filter('All')).props('flat dense size=sm color=cyan').classes('text-xs')
                    ui.button('Pending', on_click=lambda: set_filter('Pending')).props('flat dense size=sm color=amber').classes('text-xs')
                    ui.button('Removed', on_click=lambda: set_filter('Removed')).props('flat dense size=sm color=emerald').classes('text-xs')

            # Container where result cards render
            table_container = ui.column().classes('w-full gap-3')

        # Right: Cyberpunk Terminal Logs
        with ui.card().classes('terminal-box flex-[2] p-4 rounded-2xl border border-slate-800 shadow-2xl'):
            # Terminal Header Dots
            with ui.row().classes('items-center justify-between w-full mb-3 border-b border-slate-800/80 pb-2'):
                with ui.row().classes('gap-1.5 items-center'):
                    ui.element('div').classes('w-2.5 h-2.5 rounded-full bg-red-500/80')
                    ui.element('div').classes('w-2.5 h-2.5 rounded-full bg-amber-500/80')
                    ui.element('div').classes('w-2.5 h-2.5 rounded-full bg-emerald-500/80')
                ui.label('live_recon.log').classes('text-[11px] font-mono text-slate-500')
            
            terminal_log = ui.log(max_lines=20).classes('w-full h-96 text-emerald-400 font-mono text-[11px] leading-relaxed')


# --- CONTROLLER LOGIC ---

def refresh_results_view():
    """Renders data findings, updates active score gauges, and applies filters."""
    global scan_id
    table_container.clear()
    
    scan_id, active_score, status_str, findings = tracker.get_latest_scan_findings()
    
    # Calculate progress stats
    total_items = len(findings)
    removed_items = sum(1 for item in findings if item['status'] == 'Removed')
    prog_pct = int((removed_items / total_items) * 100) if total_items > 0 else 0
    
    # Update Dashboard Gauge Metrics
    score_label.set_text(str(active_score))
    total_hits_label.set_text(str(total_items))
    progress_label.set_text(f"{prog_pct}%")
    progress_bar.set_value(prog_pct / 100.0)
    
    # Color-code Exposure Badge
    status_badge.set_text(status_str)
    if active_score >= 60:
        status_badge.props('color=red-10 text-color=red-2')
        score_label.classes(replace='text-red-500')
    elif active_score >= 30:
        status_badge.props('color=amber-10 text-color=amber-2')
        score_label.classes(replace='text-amber-500')
    else:
        status_badge.props('color=emerald-10 text-color=emerald-2')
        score_label.classes(replace='text-emerald-400')

    # Apply Active Filters
    filtered_findings = findings
    if current_filter != "All":
        filtered_findings = [f for f in findings if f['status'] == current_filter]

    if not filtered_findings:
        with table_container:
            with ui.column().classes('w-full items-center justify-center p-12 text-center border border-dashed border-slate-800 rounded-xl'):
                ui.icon('radar', size='lg', color='slate-7').classes('mb-2 animate-spin-slow')
                ui.label('No exposure data found for this filter.').classes('text-sm font-mono text-slate-500')
        return

    # Render Individual Exposure Cards
    for item in filtered_findings:
        is_removed = item['status'] == 'Removed'
        
        with table_container:
            card_border = 'border-slate-800/80 bg-slate-900/40' if not is_removed else 'border-emerald-900/30 bg-emerald-950/10'
            
            with ui.row().classes(f'w-full p-4 rounded-xl border {card_border} items-center justify-between transition-all hover:bg-slate-800/50 gap-4'):
                
                # Category Badge & Title Details
                with ui.column().classes('gap-1 flex-1'):
                    with ui.row().classes('items-center gap-2'):
                        cat_color = 'purple-9' if item['category'] == 'Data Broker' else 'red-9' if 'Breach' in item['category'] else 'amber-9'
                        ui.badge(item['category'].upper(), color=cat_color).props('dense rounded font-mono text-[9px]')
                        ui.label(item['source'].upper()).classes('text-xs font-mono font-bold text-cyan-400')
                    
                    ui.label(item['title']).classes('text-xs font-medium text-slate-200 line-clamp-1')

                # Action Button Links (Profile Link & Direct Opt-Out Link)
                with ui.row().classes('items-center gap-2'):
                    if item['url'] and item['url'] != 'N/A':
                        ui.button(icon='open_in_new', on_click=lambda u=item['url']: ui.navigate.to(u, new_tab=True)).props('flat round dense color=sky').tooltip('Open Profile Link')
                        
                    if item['opt_out_url'] and item['opt_out_url'] != 'N/A':
                        ui.button('OPT-OUT', icon='shield', on_click=lambda u=item['opt_out_url']: ui.navigate.to(u, new_tab=True)).props('unelevated dense color=emerald-8 text-color=white').classes('text-[10px] font-bold px-3 py-1 rounded-lg')

                    # Interactive Status Toggle Button Switch
                    status_btn = ui.button(
                        'REMOVED' if is_removed else 'PENDING',
                        icon='check_circle' if is_removed else 'pending'
                    ).props(
                        f'unelevated dense color={"emerald-9" if is_removed else "amber-9"}'
                    ).classes('text-[10px] font-mono font-bold px-3 py-1 rounded-lg ml-2')

                    def toggle_status(f_id=item['id'], current_st=item['status']):
                        new_st = 'Pending' if current_st == 'Removed' else 'Removed'
                        tracker.update_finding_status(f_id, new_st)
                        tracker.recalculate_active_score(scan_id)
                        ui.notify(f"Updated status to {new_st}", type='positive' if new_st == 'Removed' else 'warning')
                        refresh_results_view()

                    status_btn.on_click(toggle_status)

def start_scan_workflow():
    """Triggers the full OSINT scanning sequence."""
    name = name_input.value.strip()
    loc = loc_input.value.strip()
    email = email_input.value.strip()
    
    if not name and not email:
        ui.notify('Identity vector missing! Provide Name or Email.', type='negative', position='top')
        return

    terminal_log.clear()
    terminal_log.push("⚡ INITIALIZING RECONNAISSANCE ENGINE...")
    terminal_log.push(f"  > Target Name  : {name if name else 'N/A'}")
    terminal_log.push(f"  > Target Loc   : {loc if loc else 'N/A'}")
    terminal_log.push(f"  > Target Email : {email if email else 'N/A'}\n")
    
    def log(msg):
        terminal_log.push(msg)

    # 1. Scan Data Brokers
    broker_hits = osint_engine.scan_data_brokers(name, loc, log_callback=log) if name else []
    
    # 2. Google Dork Pastebin / File Scans
    dork_hits = osint_engine.scan_google_dorks(name, email, log_callback=log)
    
    # 3. Breach Data Engine
    breach_hits = osint_engine.scan_email_breaches(email, log_callback=log) if email else []
    
    # 4. Gravatar Profiling
    grav_hit = osint_engine.check_gravatar_profile(email, log_callback=log) if email else False
    
    all_findings = broker_hits + dork_hits + breach_hits
    if grav_hit:
        all_findings.append({
            "category": "Gravatar Profile",
            "source": "Gravatar",
            "title": "Public Gravatar Profile Linked to Email",
            "url": "https://gravatar.com",
            "opt_out_url": "N/A"
        })

    # Base Score Calculation
    raw_score = min((len(broker_hits) * 5) + (len(breach_hits) * 8) + (len(dork_hits) * 5) + (10 if grav_hit else 0), 100)
    raw_status = "🔴 FULLY COOKED" if raw_score >= 60 else "🟠 MEDIUM WELL" if raw_score >= 30 else "🟢 RAW"

    # Persist findings to database
    tracker.save_scan_results({"name": name, "location": loc, "email": email}, raw_score, raw_status, all_findings)
    
    terminal_log.push("\n✅ SCAN COMPLETE. Results mapped to database.")
    refresh_results_view()

scan_btn.on_click(start_scan_workflow)

# Render initial database view on page launch
refresh_results_view()

ui.run(title='Flamingo OSINT Engine', port=8080, dark=True)