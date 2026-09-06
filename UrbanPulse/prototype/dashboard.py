import streamlit as st
import json, os, time, glob
import pandas as pd
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

BASE      = "UrbanPulse"
STATE_DIR = f"{BASE}/prototype/state"

def fp(name): return os.path.join(STATE_DIR, name)

def load(path, default=None):
    try:
        with open(path) as f: return json.load(f)
    except Exception:
        return default or {}

st.set_page_config(
    page_title="UrbanPulse — SIH Dashboard",
    page_icon="🚍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════

st.markdown("""
<style>
.stApp { background-color: #0d1117; }

[data-testid="metric-container"] {
    background: linear-gradient(135deg,#161b22,#21262d);
    border:1px solid #30363d; border-radius:10px; padding:14px;
}
[data-testid="metric-container"] label { color:#8b949e!important; font-size:.75rem!important; text-transform:uppercase; letter-spacing:.08em; }
[data-testid="stMetricValue"]          { color:#e6edf3!important; font-size:1.9rem!important; font-weight:700!important; }

.sec-title { font-size:1rem; font-weight:700; color:#58a6ff; text-transform:uppercase;
             letter-spacing:.1em; padding:6px 0 4px; border-bottom:1px solid #1f3050; margin-bottom:10px; }

.alert-card { background:linear-gradient(135deg,#2a0a0a,#3a1010); border:1px solid #f85149;
              border-left:4px solid #f85149; border-radius:8px; padding:12px 16px; margin:5px 0; }
.warn-card  { background:linear-gradient(135deg,#2a1f00,#3a2d00); border:1px solid #d29922;
              border-left:4px solid #d29922; border-radius:8px; padding:12px 16px; margin:5px 0; }
.ok-card    { background:linear-gradient(135deg,#062910,#0a3d18); border:1px solid #3fb950;
              border-left:4px solid #3fb950; border-radius:8px; padding:12px 16px; margin:5px 0; }
.info-card  { background:linear-gradient(135deg,#051d36,#0d2a4a); border:1px solid #388bfd;
              border-left:4px solid #388bfd; border-radius:8px; padding:12px 16px; margin:5px 0; }

.live-dot { width:10px;height:10px;border-radius:50%;background:#3fb950;
            display:inline-block; animation:blink 1s infinite; margin-right:6px; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

.priority-CRITICAL { color:#f85149!important; font-weight:700; }
.priority-HIGH     { color:#d29922!important; font-weight:700; }
.priority-MEDIUM   { color:#388bfd!important; }
.priority-LOW      { color:#3fb950!important; }

.badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:.72rem;
         font-weight:600; margin-right:4px; }
.b-red    { background:#f8514922;color:#f85149;border:1px solid #f85149; }
.b-orange { background:#d2992222;color:#d29922;border:1px solid #d29922; }
.b-blue   { background:#388bfd22;color:#388bfd;border:1px solid #388bfd; }
.b-green  { background:#3fb95022;color:#3fb950;border:1px solid #3fb950; }
.b-purple { background:#8b949e22;color:#c9d1d9;border:1px solid #8b949e; }

.stTabs [data-baseweb="tab-list"] { background:#161b22; border-radius:8px; }
.stTabs [data-baseweb="tab"]      { color:#8b949e; }
.stTabs [aria-selected="true"]    { color:#e6edf3!important; background:#21262d; border-radius:6px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# LOAD ALL STATE
# ═══════════════════════════════════════════════════════════

live     = load(fp("live_state.json"),     {"frame":0,"fps":0,"vehicles":0,"density":"—",
                                             "potholes":0,"waterlogging":0,"obstacles":0,
                                             "accidents":0,"htr":0,"sign_issues":0,
                                             "active_road_issues":0,"timestamp":""})
traffic  = load(fp("traffic_state.json"),  {"vehicles":0,"density":"—","cars":0,
                                             "motorcycles":0,"buses":0,"trucks":0,"timestamp":""})
pothole  = load(fp("pothole_state.json"),  {"potholes":0,"status":"NO DATA",
                                             "all_locations":[],"latitude":13.0827,"longitude":80.2707})
water    = load(fp("water_state.json"),    {"waterlog_count":0,"status":"NO DATA",
                                             "all_locations":[],"latitude":13.0827,"longitude":80.2707})
accident = load(fp("accident_state.json"), {"accidents":0,"htr":0,"status":"NO DATA",
                                             "recent_alerts":[],"latitude":13.0827,"longitude":80.2707})
roads_f  = load(fp("road_priority.json"),  {"roads":[],"total_roads":0,"generated":""})

ts_raw   = live.get("timestamp","")
ts_str   = ts_raw[:19].replace("T"," ") if ts_raw else "—"

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════

hc1, hc2 = st.columns([1,8])
with hc2:
    st.markdown("# 🚍 UrbanPulse")
    st.markdown(
        f"**AI Urban Road Intelligence** &nbsp;|&nbsp; Smart India Hackathon &nbsp;|&nbsp; "
        f'<span class="live-dot"></span>**LIVE** &nbsp;|&nbsp; '
        f"`{ts_str}`",
        unsafe_allow_html=True
    )

# ═══════════════════════════════════════════════════════════
# TOP STATUS BAR
# ═══════════════════════════════════════════════════════════

sb = st.columns(6)
with sb[0]: st.success("🟢 SYSTEM ONLINE")
with sb[1]: st.info(f"🎬 Frame: {live.get('frame',0)}")
with sb[2]: st.info(f"⚡ FPS: {live.get('fps',0)}")
with sb[3]:
    bus = pothole.get("bus_id","MTC-DEMO-001")
    st.warning(f"🚌 {bus}")
with sb[4]:
    total_issues = (pothole.get("potholes",0) + water.get("waterlog_count",0)
                    + accident.get("accidents",0) + accident.get("htr",0))
    if total_issues > 0: st.error(f"🚨 {total_issues} ISSUES")
    else:                st.success("✅ ALL CLEAR")
with sb[5]:
    d = traffic.get("density","—")
    if d=="HIGH":   st.error(f"🔴 TRAFFIC: {d}")
    elif d=="MEDIUM": st.warning(f"🟡 TRAFFIC: {d}")
    else:           st.success(f"🟢 TRAFFIC: {d}")

st.divider()

# ═══════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════

tab_live, tab_road, tab_traffic, tab_road_cond, tab_safety, tab_signs, tab_map = st.tabs([
    "🔴 Live Feed",
    "📋 Road Reports",
    "🚗 Traffic",
    "🛣️ Road Condition",
    "🚨 Safety",
    "🪧 Street Signs",
    "🗺️ Map"
])

# ═══════════════════════════════════════════════════════════
# TAB 1: LIVE FEED
# ═══════════════════════════════════════════════════════════

with tab_live:
    st.markdown('<div class="sec-title">🔴 Live Detection Feed</div>', unsafe_allow_html=True)

    lc = st.columns(4)
    with lc[0]:
        st.metric("Vehicles (live)", live.get("vehicles",0))
        st.metric("Density", live.get("density","—"))
    with lc[1]:
        st.metric("Potholes (total)", live.get("potholes",0))
        st.metric("Waterlogging", live.get("waterlogging",0))
    with lc[2]:
        st.metric("Obstacles", live.get("obstacles",0))
        st.metric("Sign Issues", live.get("sign_issues",0))
    with lc[3]:
        st.metric("Accidents", live.get("accidents",0))
        st.metric("Hit-and-Run", live.get("htr",0))

    st.divider()

    st.markdown('<div class="sec-title">Current Detection Summary</div>', unsafe_allow_html=True)

    issues_active = []
    if live.get("potholes",0)    > 0: issues_active.append(("🕳️ Pothole",     live["potholes"],    "b-red"))
    if live.get("waterlogging",0)> 0: issues_active.append(("🌊 Waterlogging", live["waterlogging"],"b-blue"))
    if live.get("accidents",0)   > 0: issues_active.append(("🚨 Accident",     live["accidents"],   "b-red"))
    if live.get("htr",0)         > 0: issues_active.append(("🏃 Hit & Run",    live["htr"],         "b-red"))
    if live.get("obstacles",0)   > 0: issues_active.append(("🚧 Obstacle",     live["obstacles"],   "b-orange"))
    if live.get("sign_issues",0) > 0: issues_active.append(("🪧 Sign Issue",   live["sign_issues"], "b-orange"))

    if issues_active:
        st.markdown(
            '<div class="alert-card">🚨 <b>ACTIVE DETECTIONS</b><br>' +
            " &nbsp; ".join([f'<span class="badge {bc}">{lbl} x{cnt}</span>'
                             for lbl,cnt,bc in issues_active]) +
            '</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-card">✅ No active issues detected on this route</div>',
                    unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-card">
    📹 <b>OpenCV window is running in Terminal 1</b><br>
    All detections are annotated live on the video feed.<br>
    This dashboard refreshes every 2 seconds from <code>live_state.json</code>.
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TAB 2: ROAD REPORTS (priority ranking)
# ═══════════════════════════════════════════════════════════

with tab_road:
    st.markdown('<div class="sec-title">📋 Road-Segment Reports (Priority Ranked)</div>',
                unsafe_allow_html=True)

    roads = roads_f.get("roads", [])
    if not roads:
        st.info("No road reports yet. Run `python UrbanPulse/run.py` to generate data.")
    else:
        # Summary metrics
        rc = st.columns(4)
        with rc[0]: st.metric("Total Roads Monitored", len(roads))
        critical = [r for r in roads if r.get("priority_level")=="CRITICAL"]
        high     = [r for r in roads if r.get("priority_level")=="HIGH"]
        with rc[1]: st.metric("🔴 Critical",   len(critical))
        with rc[2]: st.metric("🟠 High",       len(high))
        with rc[3]: st.metric("Generated",
                               roads_f.get("generated","")[:19].replace("T"," "))

        st.divider()

        # Priority table
        rows = []
        for r in roads:
            pl = r.get("priority_level","LOW")
            rows.append({
                "Road Segment":  r.get("segment_id",""),
                "Priority":      pl,
                "Score":         r.get("priority_score",0),
                "Potholes":      r.get("potholes",0),
                "Waterlogging":  r.get("waterlogging",0),
                "Accidents":     r.get("accidents",0),
                "Hit & Run":     r.get("htr",0),
                "Obstacles":     r.get("obstacles",0),
                "Sign Issues":   r.get("sign_issues",0),
                "Lat":           round(r.get("latitude",0),4),
                "Lon":           round(r.get("longitude",0),4),
                "Last Updated":  r.get("last_updated","")[:19].replace("T"," ")
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        # Critical + High cards
        urgent = [r for r in roads if r.get("priority_level") in ("CRITICAL","HIGH")]
        if urgent:
            st.markdown("### 🚨 Urgent Roads — Maintenance Required")
            for r in urgent[:5]:
                pl   = r.get("priority_level","")
                card = "alert-card" if pl=="CRITICAL" else "warn-card"
                issues_list = []
                if r.get("potholes",0):    issues_list.append(f"Pothole x{r['potholes']}")
                if r.get("waterlogging",0):issues_list.append(f"Waterlog x{r['waterlogging']}")
                if r.get("accidents",0):   issues_list.append(f"Accident x{r['accidents']}")
                if r.get("htr",0):         issues_list.append(f"HTR x{r['htr']}")
                if r.get("obstacles",0):   issues_list.append(f"Obstacle x{r['obstacles']}")

                st.markdown(
                    f'<div class="{card}">'
                    f'<b>{pl}</b> — Road: <b>{r.get("segment_id","")}</b> '
                    f'(Score: {r.get("priority_score",0)})<br>'
                    f'GPS: {r.get("latitude",0):.4f}, {r.get("longitude",0):.4f}<br>'
                    f'Issues: {" | ".join(issues_list)}<br>'
                    f'Last event: {r.get("last_updated","")[:19].replace("T"," ")}'
                    f'</div>', unsafe_allow_html=True
                )

        # Download report
        if rows:
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Download Road Priority Report (CSV)",
                data=csv, file_name="urbanpulse_road_report.csv",
                mime="text/csv"
            )

# ═══════════════════════════════════════════════════════════
# TAB 3: TRAFFIC
# ═══════════════════════════════════════════════════════════

with tab_traffic:
    st.markdown('<div class="sec-title">🚗 Traffic Intelligence</div>', unsafe_allow_html=True)
    tc = st.columns(6)
    with tc[0]: st.metric("Total Vehicles", traffic.get("vehicles",0))
    with tc[1]: st.metric("Density",        traffic.get("density","—"))
    with tc[2]: st.metric("🚗 Cars",         traffic.get("cars",0))
    with tc[3]: st.metric("🏍️ Motorcycles",  traffic.get("motorcycles",0))
    with tc[4]: st.metric("🚌 Buses",         traffic.get("buses",0))
    with tc[5]: st.metric("🚚 Trucks",         traffic.get("trucks",0))

    d = traffic.get("density","—")
    if d == "HIGH":
        st.markdown('<div class="alert-card">🔴 <b>HIGH TRAFFIC DENSITY</b> — Consider alternate route advisory</div>', unsafe_allow_html=True)
    elif d == "MEDIUM":
        st.markdown('<div class="warn-card">🟡 <b>MEDIUM TRAFFIC DENSITY</b> — Moderate congestion</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-card">🟢 <b>LOW TRAFFIC DENSITY</b> — Road is clear</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TAB 4: ROAD CONDITION
# ═══════════════════════════════════════════════════════════

with tab_road_cond:
    st.markdown('<div class="sec-title">🛣️ Road Condition</div>', unsafe_allow_html=True)

    rd1, rd2 = st.columns(2)

    with rd1:
        st.markdown("#### 🕳️ Pothole Detection")
        pc1, pc2, pc3 = st.columns(3)
        with pc1: st.metric("Confirmed Potholes", pothole.get("potholes",0))
        with pc2:
            conf = int(pothole.get("confidence",0)*100)
            st.metric("Confidence", f"{conf}%" if conf else "—")
        with pc3:
            pts = pothole.get("timestamp","")
            st.metric("Last Seen", pts[:10] if pts else "—")

        if pothole.get("potholes",0) > 0:
            st.markdown(
                f'<div class="alert-card">⚠️ <b>POTHOLES DETECTED</b><br>'
                f'Count: <b>{pothole["potholes"]}</b>  Confidence: <b>{conf}%</b><br>'
                f'GPS: {pothole.get("latitude","—")}, {pothole.get("longitude","—")}<br>'
                f'Bus: {pothole.get("bus_id","—")}'
                f'</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ok-card">✅ No potholes detected</div>', unsafe_allow_html=True)

    with rd2:
        st.markdown("#### 🌊 Waterlogging Detection")
        wc1, wc2, wc3 = st.columns(3)
        with wc1: st.metric("Waterlog Events", water.get("waterlog_count",0))
        with wc2:
            wconf = int(water.get("confidence",0)*100)
            st.metric("Confidence", f"{wconf}%" if wconf else "—")
        with wc3:
            wts = water.get("timestamp","")
            st.metric("Last Seen", wts[:10] if wts else "—")

        if water.get("waterlog_count",0) > 0:
            st.markdown(
                f'<div class="alert-card">🌊 <b>WATERLOGGING DETECTED</b><br>'
                f'Count: <b>{water["waterlog_count"]}</b>  Confidence: <b>{wconf}%</b><br>'
                f'GPS: {water.get("latitude","—")}, {water.get("longitude","—")}'
                f'</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ok-card">✅ No waterlogging detected</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TAB 5: SAFETY
# ═══════════════════════════════════════════════════════════

with tab_safety:
    st.markdown('<div class="sec-title">🚨 Safety Intelligence</div>', unsafe_allow_html=True)

    sf1, sf2, sf3 = st.columns(3)
    with sf1: st.metric("Accidents Detected",  accident.get("accidents",0))
    with sf2: st.metric("Hit-and-Run Events",  accident.get("htr",0))
    with sf3: st.metric("Obstacles on Road",   live.get("obstacles",0))

    st.divider()

    acc_n = accident.get("accidents",0)
    htr_n = accident.get("htr",0)

    if acc_n > 0 or htr_n > 0:
        msg = []
        if acc_n > 0: msg.append(f"<b>{acc_n} Accident(s)</b> detected")
        if htr_n > 0: msg.append(f"<b>{htr_n} Hit-and-Run</b> event(s) detected")
        st.markdown(
            f'<div class="alert-card">🚨 SAFETY ALERT<br>'
            f'{"<br>".join(msg)}<br>'
            f'GPS: {accident.get("latitude","—")}, {accident.get("longitude","—")}<br>'
            f'Bus: {accident.get("bus_id","—")}'
            f'</div>', unsafe_allow_html=True)

        recent = accident.get("recent_alerts",[])
        if recent:
            st.markdown("**Recent events:**")
            rev_rows = []
            for a in reversed(recent[-5:]):
                rev_rows.append({
                    "Event ID":  a.get("event_id",""),
                    "Type":      a.get("event_type",""),
                    "Frame":     a.get("frame",""),
                    "Vehicle(s)":str(a.get("vehicles_involved", a.get("vehicle_id",""))),
                    "IoU/Accel": a.get("overlap_iou", a.get("acceleration","—")),
                    "GPS":       f"{a.get('latitude','')}, {a.get('longitude','')}"
                })
            st.dataframe(pd.DataFrame(rev_rows), use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="ok-card">✅ No accidents or hit-and-run events detected</div>',
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("**Accident Detection Method:**")
    st.code("""
Multi-condition heuristic (no false positives from occlusion):
  1. IoU overlap between two tracked vehicles > 0.35 for 5+ consecutive frames
  2. At least one vehicle must have velocity > 8 px/frame (was actually moving)
  3. Velocity drop to < 3 px/frame after overlap (collision, not pass-through)
  4. Cooldown: 200 frames between events

Hit-and-Run:
  1. Person within 120px of a moving vehicle
  2. Person disappears from tracking within 25 frames
  3. Vehicle accelerates away by > 5 px/frame
    """, language="text")

# ═══════════════════════════════════════════════════════════
# TAB 6: STREET SIGNS
# ═══════════════════════════════════════════════════════════

with tab_signs:
    st.markdown('<div class="sec-title">🪧 Street Sign Detection + OCR Verification</div>',
                unsafe_allow_html=True)

    sign_events = []
    for ef in glob.glob(f"{BASE}/events/sign/SIGN-*.json"):
        try:
            with open(ef) as f: sign_events.append(json.load(f))
        except Exception: pass

    si_count = live.get("sign_issues",0)

    sic1, sic2 = st.columns(2)
    with sic1: st.metric("Sign Issues Detected", si_count)
    with sic2: st.metric("OCR Engine", "EasyOCR (English)")

    if si_count > 0:
        st.markdown(
            f'<div class="warn-card">⚠️ <b>{si_count} street sign text mismatches</b> found<br>'
            f'Sign text does not match GIS reference data for the road segment.</div>',
            unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-card">✅ All street signs verified or none detected yet</div>',
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("**How it works:**")
    st.markdown("""
    1. YOLOv8n detects traffic signs (traffic light, stop sign, parking meter) in each frame
    2. Sign region is cropped and passed to **EasyOCR**
    3. Detected text is compared against **GIS reference data** for the current GPS road segment
    4. If text doesn't match any expected sign → flagged as issue + saved to event file
    5. Issue is added to the road segment report and priority score
    """)

    st.markdown("**GIS Reference Data (simulated):**")
    gis_data = {
        "13.082_80.270": ["SPEED LIMIT 40", "NO PARKING"],
        "13.083_80.271": ["STOP", "ONE WAY"],
        "13.081_80.269": ["SCHOOL ZONE", "SPEED LIMIT 30"],
    }
    gis_rows = [{"Segment": k, "Expected Signs": ", ".join(v)} for k,v in gis_data.items()]
    st.dataframe(pd.DataFrame(gis_rows), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════
# TAB 7: MAP
# ═══════════════════════════════════════════════════════════

with tab_map:
    st.markdown('<div class="sec-title">🗺️ All Detected Events — Map View</div>',
                unsafe_allow_html=True)

    map_rows = []
    for loc in pothole.get("all_locations", []):
        if loc.get("lat") and loc.get("lon"):
            map_rows.append({"lat":loc["lat"],"lon":loc["lon"],"type":"Pothole"})
    for loc in water.get("all_locations", []):
        if loc.get("lat") and loc.get("lon"):
            map_rows.append({"lat":loc["lat"],"lon":loc["lon"],"type":"Waterlog"})
    for r in roads_f.get("roads",[]):
        if r.get("accidents",0) > 0 or r.get("htr",0) > 0:
            map_rows.append({"lat":r["latitude"],"lon":r["longitude"],"type":"Accident"})

    if not map_rows:
        map_rows.append({"lat":13.0827,"lon":80.2707,"type":"Bus Location"})

    df_map = pd.DataFrame(map_rows)
    st.map(df_map[["lat","lon"]], zoom=13)
    st.caption(
        f"Showing {len([r for r in map_rows if r['type']=='Pothole'])} pothole(s) · "
        f"{len([r for r in map_rows if r['type']=='Waterlog'])} waterlog(s) · "
        f"{len([r for r in map_rows if r['type']=='Accident'])} accident(s)"
    )

    # Road reports on map
    road_map = []
    for r in roads_f.get("roads",[]):
        if r.get("priority_score",0) > 0:
            road_map.append({
                "lat":   r["latitude"],
                "lon":   r["longitude"],
                "score": r["priority_score"],
                "level": r["priority_level"]
            })
    if road_map:
        st.markdown("**Road priority points:**")
        st.dataframe(pd.DataFrame(road_map), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════

st.divider()
st.caption(
    "UrbanPulse v3 — AI-Powered Urban Road Intelligence · "
    "Smart India Hackathon · Detection: Traffic, Obstacles, Potholes, "
    "Waterlogging, Accidents, Hit-and-Run, Street Signs"
)

# ═══════════════════════════════════════════════════════════
# AUTO REFRESH (live data)
# ═══════════════════════════════════════════════════════════

time.sleep(2)
st.rerun()
