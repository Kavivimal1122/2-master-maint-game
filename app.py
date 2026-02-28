import streamlit as st
import pandas as pd
import collections
import io
import time
import random
from collections import defaultdict

# 1. Page Configuration
st.set_page_config(page_title="2 Master Maint Game", layout="centered")

# 2. Custom CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .big-training-text { font-size: 30px; font-weight: 900; color: #00ffcc; text-align: center; }
    .engine-title-block {
        background-color: #1f77b4; color: white; padding: 10px; border-radius: 8px;
        text-align: center; font-weight: bold; margin-bottom: 10px; border: 1px solid #444; font-size: 16px;
    }
    .stat-row { display: flex; justify-content: space-around; background: #0e1117; padding: 8px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    .stat-item { text-align: center; }
    .stat-label { font-size: 10px; color: #888; font-weight: bold; text-transform: uppercase; }
    .stat-value { font-size: 20px; font-weight: 900; color: white; }
    .pred-box { padding: 20px; border-radius: 15px; text-align: center; border: 2px solid white; margin-bottom: 10px; font-weight: bold; }
    .res-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
    .res-win { background-color: #28a745; border: 1px solid #fff; }
    .res-loss { background-color: #dc3545; border: 1px solid #fff; }
    .res-text-win { color: #28a745; font-weight: bold; }
    .res-text-loss { color: #dc3545; font-weight: bold; }
    div.stButton > button { width: 100% !important; height: 50px !important; font-weight: 900 !important; background-color: #ffff00 !important; color: black !important; border: 1px solid black !important; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. Session State
if 'logic_db' not in st.session_state: st.session_state.logic_db = None
if 'engine2_patterns' not in st.session_state: st.session_state.engine2_patterns = {}
if 'num_sequence' not in st.session_state: st.session_state.num_sequence = []
if 'history' not in st.session_state: st.session_state.history = []
if 'stats_e1' not in st.session_state: 
    st.session_state.stats_e1 = {"wins": 0, "loss": 0, "streak": 0, "last_res": None, "max_win": 0, "max_loss": 0}
if 'stats_e2' not in st.session_state: 
    st.session_state.stats_e2 = {"wins": 0, "loss": 0, "streak": 0, "last_res": None, "max_win": 0, "max_loss": 0}

# --- 4. ENGINE TRAINING LOGIC ---
def train_engines(master_file):
    data = []
    raw_content = master_file.getvalue().decode("utf-8").splitlines()
    for line in raw_content:
        clean_line = line.strip().strip('"')
        parts = clean_line.split('\t')
        if len(parts) == 3: data.append(parts)
        elif len(parts) == 1 and len(parts[0]) >= 3:
            s = parts[0]; data.append([s[0], s[1], s[2]])
    
    df = pd.DataFrame(data, columns=['number', 'size', 'color'])
    nums = df['number'].astype(str).tolist()
    sizes = df['size'].astype(str).tolist()
    
    # MASTER ENGINE 2: 6-DIGIT PATTERN TRAINING
    e2_patterns = collections.defaultdict(list)
    for i in range(len(nums) - 6):
        pat = "".join(nums[i:i+6])
        next_res = "BIG" if sizes[i+6].upper() == 'B' else "SMALL"
        e2_patterns[pat].append(next_res)
    
    # Store the most frequent result for each pattern
    final_e2_logic = {p: max(set(out), key=out.count) for p, out in e2_patterns.items()}
    
    # ENGINE 1: ORIGINAL LOGIC (Preserved)
    logic = collections.defaultdict(list)
    for i in range(len(nums) - 6):
        pat = "".join(nums[i:i+6])
        next_val = "BIG" if sizes[i+6].upper() == 'B' else "SMALL"
        logic[pat].append(next_val)
    engine1_db = {pat: out[0] for pat, out in logic.items() if len(set(out)) == 1}
    
    return engine1_db, final_e2_logic

# --- 5. TRAINING UI ---
if st.session_state.logic_db is None:
    st.title("🎯 2 Master Maint Game")
    st.warning("Please upload your historical data CSV file for training.")
    u_file = st.file_uploader("Upload CSV", type="csv")
    if u_file:
        if st.button("🚀 ACTIVATE MASTER ENGINES"):
            window = st.empty(); bar = st.progress(0)
            for p in range(0, 101, 10):
                time.sleep(0.05); bar.progress(p)
                window.markdown(f'<div class="big-training-text">LEARNING PATTERNS: {p}%</div>', unsafe_allow_html=True)
            db1, db2 = train_engines(u_file)
            st.session_state.logic_db = db1
            st.session_state.engine2_patterns = db2
            st.rerun()
    st.stop()

# --- 6. PREDICTION DASHBOARDS ---
st.title("🎯 2 MASTER MAINT GAME")

# ENGINE 1
current_6_pat = "".join(map(str, st.session_state.num_sequence[-6:]))
pred1 = st.session_state.logic_db.get(current_6_pat, None)
wr1 = (st.session_state.stats_e1['wins'] / (st.session_state.stats_e1['wins'] + st.session_state.stats_e1['loss'])) if (st.session_state.stats_e1['wins'] + st.session_state.stats_e1['loss']) > 0 else 0.0

# ENGINE 2 (Pattern-Based Prediction)
pred2 = st.session_state.engine2_patterns.get(current_6_pat, None)
wr2 = (st.session_state.stats_e2['wins'] / (st.session_state.stats_e2['wins'] + st.session_state.stats_e2['loss'])) if (st.session_state.stats_e2['wins'] + st.session_state.stats_e2['loss']) > 0 else 0.0

col_e1, col_e2 = st.columns(2)
with col_e1:
    st.markdown('<div class="engine-title-block">Master Engine 1</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-row"><div class="stat-item"><div class="stat-label">MAX W</div><div class="stat-value">{st.session_state.stats_e1["max_win"]}</div></div><div class="stat-item"><div class="stat-label">RATE</div><div class="stat-value">{wr1:.2f}</div></div></div>', unsafe_allow_html=True)
    c1 = ("#dc3545" if pred1 == "BIG" else "#28a745") if pred1 else "#111"
    st.markdown(f'<div class="pred-box" style="background-color:{c1}; color:white;">{pred1 if pred1 else "WAIT"}</div>', unsafe_allow_html=True)

with col_e2:
    st.markdown('<div class="engine-title-block">Master Engine 2</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-row"><div class="stat-item"><div class="stat-label">MAX W</div><div class="stat-value">{st.session_state.stats_e2["max_win"]}</div></div><div class="stat-item"><div class="stat-label">RATE</div><div class="stat-value">{wr2:.2f}</div></div></div>', unsafe_allow_html=True)
    c2 = ("#dc3545" if pred2 == "BIG" else "#28a745") if pred2 else "#111"
    st.markdown(f'<div class="pred-box" style="background-color:{c2}; color:white;">{pred2 if pred2 else "WAIT"}</div>', unsafe_allow_html=True)

# --- 7. INPUT CONTROLS ---
if len(st.session_state.num_sequence) < 6:
    init = st.text_input("Sync last 6 numbers", max_chars=6)
    if st.button("INITIALIZE"):
        if len(init) == 6: st.session_state.num_sequence = [int(d) for d in init]; st.rerun()
else:
    new_digit = None
    row1, row2 = st.columns(5), st.columns(5)
    for i in range(5):
        if row1[i].button(str(i), key=f"n{i}"): new_digit = i
    for i in range(5, 10):
        if row2[i-5].button(str(i), key=f"n{i}"): new_digit = i

    if new_digit is not None:
        actual = "BIG" if new_digit >= 5 else "SMALL"
        
        # LOGIC E1
        res1_h, s1 = "-", "-"
        if pred1:
            is_w1 = (actual == pred1)
            stat1 = "WIN" if is_w1 else "LOSS"
            st.session_state.stats_e1["wins" if is_w1 else "loss"] += 1
            if stat1 == st.session_state.stats_e1["last_res"]: st.session_state.stats_e1["streak"] += 1
            else: st.session_state.stats_e1["streak"], st.session_state.stats_e1["last_res"] = 1, stat1
            st.session_state.stats_e1[f"max_{stat1.lower()}"] = max(st.session_state.stats_e1[f"max_{stat1.lower()}"], st.session_state.stats_e1["streak"])
            res1_h = f'<span class="res-indicator {"res-win" if is_w1 else "res-loss"}"></span> <span class="{"res-text-win" if is_w1 else "res-text-loss"}">{stat1}</span>'
            s1 = st.session_state.stats_e1["streak"]

        # LOGIC E2
        res2_h, s2 = "-", "-"
        if pred2:
            is_w2 = (actual == pred2)
            stat2 = "WIN" if is_w2 else "LOSS"
            st.session_state.stats_e2["wins" if is_w2 else "loss"] += 1
            if stat2 == st.session_state.stats_e2["last_res"]: st.session_state.stats_e2["streak"] += 1
            else: st.session_state.stats_e2["streak"], st.session_state.stats_e2["last_res"] = 1, stat2
            st.session_state.stats_e2[f"max_{stat2.lower()}"] = max(st.session_state.stats_e2[f"max_{stat2.lower()}"], st.session_state.stats_e2["streak"])
            res2_h = f'<span class="res-indicator {"res-win" if is_w2 else "res-loss"}"></span> <span class="{"res-text-win" if is_w2 else "res-text-loss"}">{stat2}</span>'
            s2 = st.session_state.stats_e2["streak"]

        st.session_state.history.insert(0, {
            "Round": len(st.session_state.history) + 1, "Number": new_digit, "Actual": actual,
            "E1 Pred": pred1 if pred1 else "WAIT", "→ Result (E1)": res1_h, "Streak (E1)": s1,
            "E2 Pred": pred2 if pred2 else "WAIT", "→ Result (E2)": res2_h, "Streak (E2)": s2
        })
        st.session_state.num_sequence.append(new_digit); st.rerun()

# --- 8. MASTER HISTORY & BATCH ---
if st.session_state.history:
    st.markdown("### 📋 MASTER HISTORY")
    h_df = pd.DataFrame(st.session_state.history)
    st.write(h_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.download_button("📥 DOWNLOAD CSV", h_df.to_csv(index=False), "results.csv", "text/csv")

st.markdown("---")
if st.button("🔄 RESET"): st.session_state.clear(); st.rerun()
