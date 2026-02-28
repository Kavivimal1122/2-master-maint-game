import streamlit as st
import pandas as pd
import collections
import io
import time
import random
from collections import defaultdict

# 1. Page Configuration
st.set_page_config(page_title="2 Master Maint Game", layout="centered")

# 2. Custom CSS for Unified Interface
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .big-training-text { font-size: 30px; font-weight: 900; color: #00ffcc; text-align: center; }
    .pred-box { padding: 20px; border-radius: 15px; text-align: center; border: 2px solid white; margin-bottom: 10px; font-weight: bold; }
    .engine-label { font-size: 14px; font-weight: bold; color: #ffff00; text-transform: uppercase; margin-bottom: 5px; }
    .stat-row { display: flex; justify-content: space-around; background: #0e1117; padding: 10px; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px; }
    .stat-value { font-size: 22px; font-weight: 900; color: white; }
    div.stButton > button { width: 100% !important; height: 50px !important; font-weight: 900 !important; background-color: #ffff00 !important; color: black !important; border: 1px solid black !important; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if 'logic_db' not in st.session_state: st.session_state.logic_db = None
if 'sequence_model' not in st.session_state: st.session_state.sequence_model = None
if 'num_sequence' not in st.session_state: st.session_state.num_sequence = []
if 'history' not in st.session_state: st.session_state.history = []
if 'stats' not in st.session_state: 
    st.session_state.stats = {"wins": 0, "loss": 0, "streak": 0, "last_res": None, "max_win": 0, "max_loss": 0}

# --- 4. ENGINE LOGIC FUNCTIONS ---
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
    nums = df['number'].astype(int).tolist()
    sizes = df['size'].astype(str).tolist()
    
    # Engine 1: Deterministic (6-Step)
    logic = collections.defaultdict(list)
    for i in range(len(nums) - 6):
        pat = "".join(map(str, nums[i:i+6]))
        next_val = "BIG" if sizes[i+6].upper() == 'B' else "SMALL"
        logic[pat].append(next_val)
    engine1_db = {pat: out[0] for pat, out in logic.items() if len(set(out)) == 1}

    # Engine 2: Sequence Probability (2-Step)
    engine2_model = defaultdict(list)
    for i in range(len(nums)-2):
        key = (nums[i], nums[i+1])
        engine2_model[key].append(nums[i+2])
    
    return engine1_db, engine2_model, nums

# --- 5. TRAINING PHASE ---
if st.session_state.logic_db is None:
    st.title("🤖 2 Master Maint Training")
    st.info("Upload 'OVER all.CSV' or 'Qus.CSV' to sync both Master Engines.")
    u_file = st.file_uploader("Upload CSV Data", type="csv")
    
    if u_file:
        if st.button("🚀 ACTIVATE MASTER ENGINES"):
            window = st.empty(); bar = st.progress(0)
            for p in range(0, 101, 10):
                time.sleep(0.05); bar.progress(p)
                window.markdown(f'<div class="big-training-text">SYNCING MASTER DATA: {p}%</div>', unsafe_allow_html=True)
            db1, model2, raw_nums = train_engines(u_file)
            st.session_state.logic_db = db1
            st.session_state.sequence_model = model2
            st.session_state.raw_numbers = raw_nums
            st.rerun()
    st.stop()

# --- 6. PREDICTION DASHBOARD ---
st.title("🎯 2 MASTER MAINT GAME")

# Unified Statistics
total = st.session_state.stats['wins'] + st.session_state.stats['loss']
win_rate = (st.session_state.stats['wins'] / total * 100) if total > 0 else 0
st.markdown(f"""
    <div class="stat-row">
        <div class="stat-item"><div class="stat-value" style="color:#28a745;">{st.session_state.stats['max_win']}</div><div style="font-size:10px; color:#888;">MAX WIN</div></div>
        <div class="stat-item"><div class="stat-value" style="color:#dc3545;">{st.session_state.stats['max_loss']}</div><div style="font-size:10px; color:#888;">MAX LOSS</div></div>
        <div class="stat-item"><div class="stat-value" style="color:#00ffcc;">{win_rate:.1f}%</div><div style="font-size:10px; color:#888;">WIN RATE</div></div>
    </div>
""", unsafe_allow_html=True)

# Calculation for Predictions
current_6_pat = "".join(map(str, st.session_state.num_sequence[-6:]))
current_2_key = tuple(st.session_state.num_sequence[-2:]) if len(st.session_state.num_sequence) >= 2 else None

pred1 = st.session_state.logic_db.get(current_6_pat, None)
pred2_num = None
if current_2_key in st.session_state.sequence_model:
    vals = st.session_state.sequence_model[current_2_key]
    pred2_num = max(set(vals), key=vals.count)

# Display Area
col_e1, col_e2 = st.columns(2)
with col_e1:
    st.markdown('<p class="engine-label">Master Engine 1 (Pattern)</p>', unsafe_allow_html=True)
    if pred1:
        c = "#dc3545" if pred1 == "BIG" else "#28a745"
        st.markdown(f'<div class="pred-box" style="background-color:{c}; color:white;">{pred1}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pred-box" style="background-color:#111; color:#444;">WAIT...</div>', unsafe_allow_html=True)

with col_e2:
    st.markdown('<p class="engine-label">Master Engine 2 (Freq)</p>', unsafe_allow_html=True)
    if pred2_num is not None:
        size2 = "BIG" if pred2_num >= 5 else "SMALL"
        c2 = "#dc3545" if size2 == "BIG" else "#28a745"
        st.markdown(f'<div class="pred-box" style="background-color:{c2}; color:white;">{pred2_num} ({size2})</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pred-box" style="background-color:#111; color:#444;">WAIT...</div>', unsafe_allow_html=True)

# Input Controls
if len(st.session_state.num_sequence) < 6:
    init = st.text_input("Sync last 6 numbers", max_chars=6)
    if st.button("INITIALIZE"):
        if len(init) == 6:
            st.session_state.num_sequence = [int(d) for d in init]; st.rerun()
else:
    new_digit = None
    row1, row2 = st.columns(5), st.columns(5)
    for i in range(5):
        if row1[i].button(str(i), key=f"n{i}"): new_digit = i
    for i in range(5, 10):
        if row2[i-5].button(str(i), key=f"n{i}"): new_digit = i

    if new_digit is not None:
        actual = "BIG" if new_digit >= 5 else "SMALL"
        active_pred = pred1 if pred1 else ("BIG" if (pred2_num is not None and pred2_num >= 5) else "SMALL")
        is_win = (actual == active_pred)
        res_type = "win" if is_win else "loss"
        st.session_state.stats["wins" if is_win else "loss"] += 1
        if res_type == st.session_state.stats["last_res"]: st.session_state.stats["streak"] += 1
        else: st.session_state.stats["streak"], st.session_state.stats["last_res"] = 1, res_type
        st.session_state.stats[f"max_{res_type}"] = max(st.session_state.stats[f"max_{res_type}"], st.session_state.stats["streak"])

        st.session_state.history.insert(0, {
            "Round": len(st.session_state.history) + 1,
            "Number": new_digit,
            "Actual": actual,
            "E1 Pred": pred1 if pred1 else "WAIT",
            "E2 Pred": f"{pred2_num}" if pred2_num is not None else "WAIT",
            "Result": "✅ WIN" if is_win else "❌ LOSS"
        })
        st.session_state.num_sequence.append(new_digit); st.rerun()

if st.session_state.history:
    st.markdown("### 📋 MASTER HISTORY")
    st.table(pd.DataFrame(st.session_state.history).head(15))

if st.button("🔄 FULL SYSTEM RESET"):
    st.session_state.clear(); st.rerun()
