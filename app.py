import streamlit as st
import pandas as pd
import collections
import io
import time
import random
from collections import defaultdict

# 1. Page Configuration
st.set_page_config(page_title="2 Master Maint Game", layout="centered")

# 2. Custom CSS (Preserving all previous styles)
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .big-training-text { font-size: 30px; font-weight: 900; color: #00ffcc; text-align: center; }
    .engine-title-block {
        background-color: #1f77b4; color: white; padding: 10px; border-radius: 8px;
        text-align: center; font-weight: bold; margin-bottom: 10px; border: 1px solid #444; font-size: 16px;
    }
    .summary-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; margin-top: 20px; }
    .summary-card { background-color: #0e1117; border: 2px solid #444; padding: 15px; border-radius: 10px; text-align: center; }
    .summary-label { font-size: 12px; color: #888; font-weight: bold; text-transform: uppercase; }
    .summary-value { font-size: 24px; font-weight: 900; color: #ffff00; }
    .pred-box { padding: 20px; border-radius: 15px; text-align: center; border: 2px solid white; margin-bottom: 10px; font-weight: bold; }
    .stat-row { display: flex; justify-content: space-around; background: #0e1117; padding: 10px; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px; }
    .stat-value { font-size: 22px; font-weight: 900; color: white; }
    
    /* Result Indicator Styles */
    .res-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
    .res-win { background-color: #28a745; border: 1px solid #fff; }
    .res-loss { background-color: #dc3545; border: 1px solid #fff; }
    .res-text-win { color: #28a745; font-weight: bold; }
    .res-text-loss { color: #dc3545; font-weight: bold; }

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
    st.session_state.stats = {"wins": 0, "loss": 0, "streak_e1": 0, "last_res_e1": None, "streak_e2": 0, "last_res_e2": None, "max_win": 0, "max_loss": 0}

# --- 4. ENGINE LOGIC FUNCTIONS (Unchanged) ---
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
    logic = collections.defaultdict(list)
    for i in range(len(nums) - 6):
        pat = "".join(map(str, nums[i:i+6]))
        next_val = "BIG" if sizes[i+6].upper() == 'B' else "SMALL"
        logic[pat].append(next_val)
    engine1_db = {pat: out[0] for pat, out in logic.items() if len(set(out)) == 1}
    engine2_model = defaultdict(list)
    for i in range(len(nums)-2):
        key = (nums[i], nums[i+1])
        engine2_model[key].append(nums[i+2])
    return engine1_db, engine2_model, nums

# --- 5. TRAINING PHASE (Unchanged) ---
if st.session_state.logic_db is None:
    st.title("🎯 2 Master Maint Game")
    st.warning("Please upload your overall historical data CSV file for training.")
    u_file = st.file_uploader("Upload historical game data", type="csv")
    if u_file:
        st.success("Training data CSV file uploaded successfully.")
        if st.button("🚀 ACTIVATE MASTER ENGINES"):
            window = st.empty()
            percent_text = st.empty()
            bar = st.progress(0)
            for p in range(0, 101, 5):
                time.sleep(0.05)
                bar.progress(p)
                percent_text.markdown(f"<h3 style='text-align: center; color: white;'>Training Progress: {p}%</h3>", unsafe_allow_html=True)
                window.markdown(f'<div class="big-training-text">SYNCING DATA...</div>', unsafe_allow_html=True)
            db1, model2, raw_nums = train_engines(u_file)
            st.session_state.logic_db = db1
            st.session_state.sequence_model = model2
            st.rerun()
    st.stop()

# --- 6. PREDICTION DASHBOARD ---
st.title("🎯 2 MASTER MAINT GAME")

total_played = len([h for h in st.session_state.history if h['Actual'] != 'WAIT'])
win_rate = (st.session_state.stats['wins'] / total_played) if total_played > 0 else 0

st.markdown(f"""
    <div class="stat-row">
        <div class="stat-item"><div class="stat-value" style="color:#28a745;">{st.session_state.stats['max_win']}</div><div style="font-size:10px; color:#888;">MAX WIN</div></div>
        <div class="stat-item"><div class="stat-value" style="color:#dc3545;">{st.session_state.stats['max_loss']}</div><div style="font-size:10px; color:#888;">MAX LOSS</div></div>
        <div class="stat-item"><div class="stat-value" style="color:#00ffcc;">{win_rate:.2f}</div><div style="font-size:10px; color:#888;">WIN RATE</div></div>
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

col_e1, col_e2 = st.columns(2)
with col_e1:
    st.markdown('<div class="engine-title-block">Master Engine 1 (Pattern)</div>', unsafe_allow_html=True)
    if pred1:
        c = "#dc3545" if pred1 == "BIG" else "#28a745"
        st.markdown(f'<div class="pred-box" style="background-color:{c}; color:white;">{pred1}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pred-box" style="background-color:#111; color:#444;">WAIT...</div>', unsafe_allow_html=True)

with col_e2:
    st.markdown('<div class="engine-title-block">Master Engine 2 (Freq)</div>', unsafe_allow_html=True)
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
        
        # Streak Calculation Logic for Engine 1
        res1_status, res1_html = "WAIT", "-"
        if pred1:
            is_win1 = (actual == pred1)
            res1_status = "WIN" if is_win1 else "LOSS"
            if res1_status == st.session_state.stats["last_res_e1"]:
                st.session_state.stats["streak_e1"] += 1
            else:
                st.session_state.stats["streak_e1"] = 1
                st.session_state.stats["last_res_e1"] = res1_status
            
            # Global Stats update (Based on E1)
            if is_win1: st.session_state.stats["wins"] += 1
            else: st.session_state.stats["loss"] += 1
            
            indicator_html = f'<span class="res-indicator {"res-win" if is_win1 else "res-loss"}"></span>'
            res_text_class = "res-text-win" if is_win1 else "res-text-loss"
            res1_html = f'{indicator_html} <span class="{res_text_class}">{res1_status}</span>'
        
        # Streak Calculation Logic for Engine 2
        res2_status, res2_html = "WAIT", "-"
        if pred2_num is not None:
            pred2_size = "BIG" if pred2_num >= 5 else "SMALL"
            is_win2 = (actual == pred2_size)
            res2_status = "WIN" if is_win2 else "LOSS"
            if res2_status == st.session_state.stats["last_res_e2"]:
                st.session_state.stats["streak_e2"] += 1
            else:
                st.session_state.stats["streak_e2"] = 1
                st.session_state.stats["last_res_e2"] = res2_status
            
            indicator_html2 = f'<span class="res-indicator {"res-win" if is_win2 else "res-loss"}"></span>'
            res_text_class2 = "res-text-win" if is_win2 else "res-text-loss"
            res2_html = f'{indicator_html2} <span class="{res_text_class2}">{res2_status}</span>'

        # Update Global Max Streaks
        if st.session_state.stats["last_res_e1"] == "WIN":
            st.session_state.stats["max_win"] = max(st.session_state.stats["max_win"], st.session_state.stats["streak_e1"])
        elif st.session_state.stats["last_res_e1"] == "LOSS":
            st.session_state.stats["max_loss"] = max(st.session_state.stats["max_loss"], st.session_state.stats["streak_e1"])

        # History Entry with 9 Columns
        st.session_state.history.insert(0, {
            "Round": len(st.session_state.history) + 1,
            "Number": new_digit,
            "Actual": actual,
            "E1 Pred": pred1 if pred1 else "WAIT",
            "→ Result (E1)": res1_html,
            "Running Streak (E1)": st.session_state.stats["streak_e1"] if pred1 else "-",
            "E2 Pred": f"{pred2_num}" if pred2_num is not None else "WAIT",
            "→ Result (E2)": res2_html,
            "Running Streak (E2)": st.session_state.stats["streak_e2"] if pred2_num is not None else "-"
        })
        st.session_state.num_sequence.append(new_digit); st.rerun()

# --- 7. BATCH SUMMARY & MASTER HISTORY ---
if total_played >= 500:
    st.divider()
    st.markdown(f"""
        <div class="summary-container">
            <div class="summary-card"><div class="summary-label">MAX WIN</div><div class="summary-value">{st.session_state.stats['max_win']}</div></div>
            <div class="summary-card"><div class="summary-label">MAX LOSS</div><div class="summary-value">{st.session_state.stats['max_loss']}</div></div>
            <div class="summary-card"><div class="summary-label">WINS</div><div class="summary-value">{st.session_state.stats['wins']}</div></div>
            <div class="summary-card"><div class="summary-label">LOSS</div><div class="summary-value">{st.session_state.stats['loss']}</div></div>
            <div class="summary-card"><div class="summary-label">WIN RATE</div><div class="summary-value" style="color:#00ffcc;">{win_rate:.2f}</div></div>
        </div>
    """, unsafe_allow_html=True)

if st.session_state.history:
    st.markdown("### 📋 MASTER HISTORY")
    history_df = pd.DataFrame(st.session_state.history)
    
    # Render 9-column HTML Table 
    st.write(history_df.head(15).to_html(escape=False, index=False), unsafe_allow_html=True)
    
    csv = history_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 DOWNLOAD GAME RESULTS (CSV)", data=csv, file_name='game_results.csv', mime='text/csv')

st.markdown("---")
if st.button("🔄 FULL SYSTEM RESET"):
    st.session_state.clear(); st.rerun()
