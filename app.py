import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Mazarintipset", layout="wide", page_icon="⚽")

# ── COLORS ───────────────────────────────────────────────────────────────────
BG      = "#002944"
YELLOW  = "#FFDD00"
WHITE   = "#FFFFFF"
GREY    = "#8899AA"
LGREY   = "#1A3A55"
BLACK   = "#000000"

st.markdown(f"""
<style>
  html, body, [class*="css"] {{ background-color:{BG}; color:{WHITE}; font-family:'Segoe UI',sans-serif; }}
  .stApp {{ background-color:{BG}; }}
  section[data-testid="stSidebar"] {{ display:none; }}
  div[data-testid="stMetricValue"] {{ color:{YELLOW}; font-size:2rem; font-weight:700; }}
  div[data-testid="stMetricLabel"] {{ color:{GREY}; font-size:.75rem; text-transform:uppercase; letter-spacing:.08em; }}
  div[data-testid="stMetricDelta"] {{ color:{GREY}; }}
  h1,h2,h3 {{ color:{YELLOW}; }}
  .block-container {{ padding-top:1.5rem; padding-bottom:1rem; }}
  [data-testid="stHorizontalBlock"] > div {{ gap:0.5rem; }}
  .podium-card {{
    border-radius:12px; padding:1.2rem 1rem; text-align:center;
    border:1px solid {LGREY};
  }}
</style>
""", unsafe_allow_html=True)

# ── DATA LOAD ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    bets = pd.read_csv("bets.csv")
    bets = bets[bets["team"] != "Email address"].dropna(subset=["bet"])
    bets = bets[pd.to_numeric(bets["bet"], errors="coerce").notna()]
    bets["bet"] = bets["bet"].astype(float).astype(int)

    standings = pd.read_csv("league_current_standings.csv")
    return bets, standings

bets, standings = load_data()

MAX_WEEK = standings["week"].max()
latest   = standings[standings["week"] == MAX_WEEK].copy()
latest   = latest.sort_values("Points", ascending=False).reset_index(drop=True)
latest["Position"] = latest.index + 1

# ── SCORING LOGIC ─────────────────────────────────────────────────────────────
def score_row(bet_pos, actual_pos):
    if actual_pos == 1 and bet_pos == 1:   return 7
    if actual_pos >= 2:
        diff = abs(bet_pos - actual_pos)
        if diff == 0: return 5
        if diff == 1: return 3
        if diff == 2: return 1
    return 0

def calc_player_scores_at_week(week_num):
    w_stand = standings[standings["week"] == week_num].copy()
    w_stand = w_stand.sort_values("Points", ascending=False).reset_index(drop=True)
    w_stand["Position"] = w_stand.index + 1
    pos_map = dict(zip(w_stand["Team"], w_stand["Position"]))

    rows = []
    for _, r in bets.iterrows():
        actual = pos_map.get(r["team"])
        if actual is None:
            continue
        pts = score_row(int(r["bet"]), actual)
        rows.append({"Name": r["Name"], "team": r["team"], "bet": r["bet"],
                     "actual_pos": actual, "points": pts, "week": week_num})
    return pd.DataFrame(rows)

# Build weekly scores
weekly_dfs = [calc_player_scores_at_week(w) for w in sorted(standings["week"].unique())]
all_weekly = pd.concat(weekly_dfs)

# Current total scores (latest week)
current_scores = all_weekly[all_weekly["week"] == MAX_WEEK].groupby("Name")["points"].sum().reset_index()
current_scores = current_scores.sort_values("points", ascending=False).reset_index(drop=True)
current_scores["Rank"] = current_scores.index + 1

# Previous week scores for arrows
prev_week = MAX_WEEK - 1
if prev_week in standings["week"].values:
    prev_scores = all_weekly[all_weekly["week"] == prev_week].groupby("Name")["points"].sum().reset_index()
    prev_scores.columns = ["Name", "prev_points"]
    current_scores = current_scores.merge(prev_scores, on="Name", how="left")
    current_scores["delta"] = current_scores["points"] - current_scores["prev_points"]
else:
    current_scores["prev_points"] = 0
    current_scores["delta"] = 0

# Weekly cumulative per player
weekly_totals = []
for w in sorted(standings["week"].unique()):
    grp = all_weekly[all_weekly["week"] == w].groupby("Name")["points"].sum().reset_index()
    grp["week"] = w
    weekly_totals.append(grp)
weekly_totals = pd.concat(weekly_totals)

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"<h1 style='text-align:center;letter-spacing:.1em;margin-bottom:.2rem;color:{YELLOW}'>⚽ MAZARINTIPSET</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:{YELLOW};margin-top:0'>Week {MAX_WEEK} · {len(bets['Name'].unique())} players · {len(bets['team'].unique())} teams</p>", unsafe_allow_html=True)
st.markdown("---")


# ── LEADERBOARD + LEAGUE STANDINGS ───────────────────────────────────────────
col_lb, col_ls = st.columns([1, 1])

with col_lb:
    st.markdown(f"<h3 style='color:{YELLOW}'>🏆 Player Leaderboard</h3>", unsafe_allow_html=True)

    medal = {1: "🥇", 2: "🥈", 3: "🥉"}
    podium_cols = st.columns(3)

    for i, row in current_scores.head(3).iterrows():
        rank = row["Rank"]
        delta = row["delta"]
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        arrow_col = "#00CC66" if delta > 0 else ("#FF4444" if delta < 0 else YELLOW)
        border_col = YELLOW if rank == 1 else YELLOW
        podium_cols[i].markdown(f"""
        <div class="podium-card" style="background:{LGREY};border-color:{border_col}">
          <div style="font-size:1.8rem">{medal[rank]}</div>
          <div style="font-weight:700;font-size:1.1rem;color:{YELLOW}">{row['Name']}</div>
          <div style="font-size:1.6rem;color:{YELLOW};font-weight:900">{int(row['points'])}</div>
          <div style="font-size:.8rem;color:{arrow_col}">{arrow} {abs(int(delta))} vs prev week</div>
        </div>""", unsafe_allow_html=True)

    # Rest of players
    st.markdown("<br>", unsafe_allow_html=True)
    for _, row in current_scores.iloc[3:].iterrows():
        delta = row["delta"]
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        arrow_col = "#00CC66" if delta > 0 else ("#FF4444" if delta < 0 else YELLOW)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
             padding:.5rem .8rem;margin:.3rem 0;border-radius:8px;background:{LGREY}">
          <span style="color:{YELLOW}">{int(row['Rank'])}</span>
          <span style="font-weight:600;color:{YELLOW}">{row['Name']}</span>
          <span style="color:{YELLOW};font-weight:700">{int(row['points'])} pts</span>
          <span style="color:{arrow_col};font-size:.85rem">{arrow} {abs(int(delta))}</span>
        </div>""", unsafe_allow_html=True)

with col_ls:
    st.markdown(f"<h3 style='color:{YELLOW}'>📋 League Standings — Week {MAX_WEEK}</h3>", unsafe_allow_html=True)
    RELEGATION = len(latest)
    for _, row in latest.iterrows():
        pos = int(row["Position"])
        if pos == 1:
            bar_col = YELLOW
            txt_col = BLACK
        elif pos <= 3:
            bar_col = "#1E90FF"
            txt_col = WHITE
        elif pos >= RELEGATION - 1:
            bar_col = "#FF4444"
            txt_col = WHITE
        elif pos >= RELEGATION - 3:
            bar_col = "#CC8800"
            txt_col = WHITE
        else:
            bar_col = LGREY
            txt_col = WHITE

        gd_str = f"+{int(row['Goal Difference'])}" if row["Goal Difference"] > 0 else str(int(row["Goal Difference"]))
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
             padding:.35rem .8rem;margin:.2rem 0;border-radius:6px;background:{bar_col};color:{txt_col}">
          <span style="width:24px;font-weight:700">{pos}</span>
          <span style="flex:1;font-weight:600">{row['Team']}</span>
          <span style="width:36px;text-align:right">{int(row['Points'])}p</span>
          <span style="width:50px;text-align:right;font-size:.8rem;opacity:.8">{gd_str} GD</span>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── WEEKLY POINTS HEATMAP ─────────────────────────────────────────────────────
st.markdown(f"<h3 style='color:{YELLOW}'>📅 Points per Player per Week</h3>", unsafe_allow_html=True)

# Pivot: rows = players, cols = weeks
hm_pivot = weekly_totals.pivot_table(index="Name", columns="week", values="points", aggfunc="first")
hm_pivot = hm_pivot.sort_index()

weeks = sorted(hm_pivot.columns.tolist())
names = hm_pivot.index.tolist()
z = hm_pivot.values.tolist()

fig_hm = go.Figure(go.Heatmap(
    z=z,
    x=[f"W{w}" for w in weeks],
    y=names,
    text=[[f"{int(v)}p" if pd.notna(v) else "" for v in row] for row in z],
    texttemplate="%{text}",
    colorscale=[[0.0, BG], [1.0, YELLOW]],
    showscale=True,
    colorbar=dict(
        title=dict(text="Pts", font=dict(color=WHITE)),
        tickfont=dict(color=WHITE),
        bgcolor=BG,
        outlinecolor=LGREY,
    ),
    hovertemplate="<b>%{y}</b><br>%{x}<br>%{z} pts<extra></extra>",
))

fig_hm.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=WHITE),
    xaxis=dict(color=YELLOW, tickfont=dict(color=YELLOW), side="top"),
    yaxis=dict(color=YELLOW, tickfont=dict(color=YELLOW)),
    margin=dict(l=10, r=10, t=40, b=10),
    height=220,
)
st.plotly_chart(fig_hm, use_container_width=True)

st.markdown("---")

# ── TEAM vs PLAYER POINTS HEATMAP (latest week) ───────────────────────────────
st.markdown(f"<h3 style='color:{YELLOW}'>🏟️ Points per Team per Player — Week {MAX_WEEK}</h3>", unsafe_allow_html=True)

latest_week_scores = all_weekly[all_weekly["week"] == MAX_WEEK].copy()
team_player_pivot = latest_week_scores.pivot_table(index="team", columns="Name", values="points", aggfunc="first")

# Sort rows by league position (latest standings)
team_order = latest["Team"].tolist()
team_player_pivot = team_player_pivot.reindex([t for t in team_order if t in team_player_pivot.index])
team_player_pivot.index = [f"{i+1}. {t}" for i, t in enumerate(team_player_pivot.index)]

tp_z = team_player_pivot.values.tolist()
tp_x = list(team_player_pivot.columns)
tp_y = list(team_player_pivot.index)

fig_tp = go.Figure(go.Heatmap(
    z=tp_z,
    x=tp_x,
    y=tp_y,
    text=[[f"{int(v)}p" if pd.notna(v) else "" for v in row] for row in tp_z],
    texttemplate="%{text}",
    colorscale=[[0.0, BG], [1.0, YELLOW]],
    showscale=True,
    colorbar=dict(
        title=dict(text="Pts", font=dict(color=WHITE)),
        tickfont=dict(color=WHITE),
        bgcolor=BG,
        outlinecolor=LGREY,
    ),
    hovertemplate="<b>%{y}</b><br>%{x}<br>%{z} pts<extra></extra>",
))

fig_tp.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=WHITE),
    xaxis=dict(color=YELLOW, tickfont=dict(color=YELLOW), side="top"),
    yaxis=dict(color=YELLOW, tickfont=dict(color=YELLOW), autorange="reversed"),
    margin=dict(l=10, r=10, t=40, b=10),
    height=520,
)
st.plotly_chart(fig_tp, use_container_width=True)
