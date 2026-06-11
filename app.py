# -*- coding: utf-8 -*-
"""
基本情報技術者試験 単語＆クイズアプリ（Vocab-Archive & Test-Run）

本アプリは「クラウドDB（Postgres）＋Googleログイン」前提で動作します。
記録はログインしたGoogleアカウント（メールアドレス）単位で保存されます。
必要な設定（Streamlit Secrets）:
  - DATABASE_URL … Neon等のPostgres接続文字列
  - [auth]       … Googleログイン設定（client_id / client_secret 等）
  - DEV_USER     … (任意・開発用) ログインなしで動作確認する場合のユーザー名
"""
import hashlib
import html
import json
import math
import os
import random
from datetime import datetime

import pandas as pd
import streamlit as st

# --- ページ設定 ---
st.set_page_config(page_title="基本情報 単語＆クイズ", layout="centered",
                   initial_sidebar_state="expanded")

# ==========================================
# 全体デザイン（CSS）: サイバーネオンテーマ（青紫ビビッド）
# ==========================================
st.markdown("""
<style>
/* ===== 全体の余白 ===== */
.block-container {
    padding: 2.4rem 3rem 5rem !important;
    max-width: 880px;
}
[data-testid="stVerticalBlock"] { gap: 1.05rem; }
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] > div:first-child {
    padding: 1.6rem 1.3rem 2rem;
}

/* ===== ベース文字色 ===== */
.stApp, .stApp p, .stApp label, .stApp li,
.stMarkdown, .stMarkdown p, .stMarkdown li {
    color: #cdd9f6;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #eaf2ff; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #7e8db5; }
[data-testid="stWidgetLabel"] p { color: #5fd4ff; font-weight: 600; letter-spacing: .04em; }
[data-testid="stMetricValue"] { color: #5fd4ff; }
[data-testid="stMetricLabel"] p { color: #9fb2dd; }

/* ===== サイバーグリッド ===== */
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none;
    background-image:
        linear-gradient(rgba(95, 130, 255, 0.06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(95, 130, 255, 0.06) 1px, transparent 1px);
    background-size: 38px 38px;
}

/* ===== ボタン（共通）===== */
.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(95, 130, 255, 0.50);
    background: rgba(12, 18, 48, 0.85);
    color: #9ec3ff;
    font-weight: 600;
    padding: 0.55rem 1.1rem;
    box-shadow: 0 0 12px rgba(95, 130, 255, 0.15), inset 0 0 16px rgba(95, 130, 255, 0.05);
    transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    border-color: #7da2ff;
    color: #e6f0ff;
    box-shadow: 0 0 22px rgba(123, 63, 242, 0.45);
}
.stButton > button:active { transform: translateY(0); }
.stButton > button:disabled {
    opacity: 0.45;
    transform: none;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(90deg, #2d7dff 0%, #7b3ff2 60%, #b43fff 100%);
    border: none;
    color: #ffffff;
    box-shadow: 0 0 18px rgba(123, 63, 242, 0.55);
}
.stButton > button[kind="primary"]:hover {
    color: #ffffff;
    box-shadow: 0 0 30px rgba(180, 63, 255, 0.65);
}

/* ===== ホーム画面の大型メニューカード ===== */
div[class*="st-key-home_"] button {
    padding: 1.4rem 1.6rem !important;
    font-size: 1.12rem !important;
    text-align: left !important;
    justify-content: flex-start !important;
    border-radius: 14px !important;
    background: rgba(10, 16, 44, 0.92) !important;
}
div[class*="st-key-home_list"] button {
    border: 1px solid rgba(45, 226, 255, 0.65) !important; color: #7ee8ff !important;
    box-shadow: 0 0 16px rgba(45, 226, 255, 0.20) !important;
}
div[class*="st-key-home_list"] button:hover { box-shadow: 0 0 26px rgba(45, 226, 255, 0.45) !important; }
div[class*="st-key-home_quiz"] button {
    border: 1px solid rgba(255, 138, 60, 0.70) !important; color: #ffb36b !important;
    box-shadow: 0 0 16px rgba(255, 138, 60, 0.18) !important;
}
div[class*="st-key-home_quiz"] button:hover { box-shadow: 0 0 26px rgba(255, 138, 60, 0.45) !important; }
div[class*="st-key-home_guide"] button {
    border: 1px solid rgba(62, 242, 177, 0.65) !important; color: #6ef5c2 !important;
    box-shadow: 0 0 16px rgba(62, 242, 177, 0.18) !important;
}
div[class*="st-key-home_guide"] button:hover { box-shadow: 0 0 26px rgba(62, 242, 177, 0.45) !important; }

/* ===== ナビゲーションバー（小型）===== */
div[class*="st-key-nav_"] button {
    padding: 0.3rem 0.6rem !important;
    font-size: 0.85rem !important;
    border-radius: 999px !important;
    white-space: nowrap !important;
}

/* ===== チェックボタン（小型・1行固定）===== */
div[class*="st-key-chk_"] button {
    padding: 0.2rem 0.3rem !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
    letter-spacing: normal !important;
    min-height: 0 !important;
}
div[class*="st-key-chk_"] button p { white-space: nowrap !important; }

/* ===== 回答ボタン（左寄せ・ゆったり）===== */
div[class*="st-key-ans_"] button {
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.85rem 1.2rem !important;
}

/* ===== 開始・検索ボタン（オレンジアクセント / デザイン案準拠）===== */
div[class*="st-key-start_"] button, div[class*="st-key-kw_search"] button {
    background: rgba(20, 12, 40, 0.9) !important;
    border: 1px solid rgba(255, 138, 60, 0.75) !important;
    color: #ffb36b !important;
    box-shadow: 0 0 14px rgba(255, 138, 60, 0.20) !important;
}
div[class*="st-key-start_"] button:hover, div[class*="st-key-kw_search"] button:hover {
    box-shadow: 0 0 26px rgba(255, 138, 60, 0.50) !important;
}

/* ===== 単語カード（keyを持つ枠付きコンテナのみ装飾）===== */
div[class*="st-key-card_"] {
    background: rgba(10, 16, 44, 0.92);
    border: 1px solid rgba(95, 130, 255, 0.30) !important;
    border-radius: 14px;
    box-shadow: 0 0 16px rgba(95, 130, 255, 0.10);
    padding: 16px 20px;
}

/* ===== サイドバー ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070b24 0%, #140f38 100%);
    border-right: 1px solid rgba(95, 130, 255, 0.25);
}

/* ===== 入力欄・セレクト ===== */
.stTextInput input, .stNumberInput input {
    background: rgba(12, 18, 48, 0.9); color: #d6e4ff;
    border: 1px solid rgba(95, 130, 255, 0.45);
    border-radius: 10px;
}
div[data-baseweb="select"] > div {
    background: rgba(12, 18, 48, 0.9); border-color: rgba(95, 130, 255, 0.45);
    color: #d6e4ff; border-radius: 10px;
}
div[data-baseweb="select"] span { color: #d6e4ff; }

/* ===== エキスパンダー ===== */
details[data-testid="stExpander"], [data-testid="stExpander"] details {
    background: rgba(10, 16, 44, 0.92);
    border: 1px solid rgba(95, 130, 255, 0.30);
    border-radius: 12px;
}

/* ===== ページ見出し（01 / HOME 風）===== */
.pg-eyebrow {
    font-family: "Consolas", "Courier New", monospace;
    color: #5fd4ff; font-size: 0.85rem; font-weight: 700;
    letter-spacing: .25em; margin-bottom: 2px;
}
.pg-title { font-size: 1.7rem; font-weight: 800; color: #eaf2ff; line-height: 1.3; }
.pg-sub { color: #8a9cc8; margin: 2px 0 10px; }

/* ===== チェック日付 ===== */
.chk-date {
    text-align: center; color: #7e8db5; font-size: 0.76rem;
    margin: 3px 0 2px; white-space: nowrap;
}

/* ===== クイズ問題カード ===== */
.q-panel {
    background: rgba(10, 16, 44, 0.95);
    border: 1px solid rgba(45, 226, 255, 0.55);
    border-radius: 12px; padding: 20px 22px;
    font-size: 1.08rem; font-weight: 700; color: #eaf2ff; line-height: 1.8;
    box-shadow: 0 0 20px rgba(45, 140, 255, 0.20);
}
.q-meta {
    font-family: "Consolas", "Courier New", monospace;
    color: #8a9cc8; letter-spacing: .15em; font-size: 0.9rem;
}

/* ===== 結果画面（YOUR SCORE）===== */
.score-card {
    background: rgba(10, 16, 44, 0.95);
    border: 1px solid rgba(95, 130, 255, 0.40);
    border-radius: 16px; padding: 30px 24px; text-align: center;
    box-shadow: 0 0 24px rgba(95, 130, 255, 0.18);
}
.score-label {
    font-family: "Consolas", "Courier New", monospace;
    color: #8a9cc8; letter-spacing: .35em; font-size: 0.95rem; margin-bottom: 8px;
}
.score-pct {
    font-size: 4rem; font-weight: 900; line-height: 1.1;
    color: #3ef2b1; text-shadow: 0 0 24px rgba(62, 242, 177, 0.45);
}
.score-sub { color: #cdd9f6; margin-top: 8px; font-size: 1.05rem; }
.stat-card {
    background: rgba(10, 16, 44, 0.95);
    border: 1px solid rgba(95, 130, 255, 0.30);
    border-radius: 12px; padding: 16px 12px; text-align: center;
    box-shadow: 0 0 14px rgba(95, 130, 255, 0.10);
}
.stat-label { color: #8a9cc8; font-size: 0.9rem; margin-bottom: 4px; }
.stat-value { font-size: 1.9rem; font-weight: 800; }
.stat-value.cyan { color: #5fd4ff; text-shadow: 0 0 14px rgba(95, 212, 255, 0.45); }
.stat-value.orange { color: #ff9d4d; text-shadow: 0 0 14px rgba(255, 157, 77, 0.45); }

/* ===== タイトル ===== */
.app-header { text-align: center; padding: 14px 0 6px; }
.app-header .app-sub {
    font-size: clamp(0.78rem, 2.2vw, 0.95rem);
    font-weight: 700; color: #6fa9d8; letter-spacing: .45em; margin-bottom: 4px;
}
.app-header .app-main {
    font-size: clamp(1.7rem, 5.5vw, 2.5rem);
    font-weight: 900; line-height: 1.25; white-space: nowrap;
    background: linear-gradient(90deg, #2de2ff 0%, #7b8cff 40%, #d36bff 75%, #ff5ce1 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 14px rgba(123, 140, 255, 0.50));
}
.app-header .app-deco { -webkit-text-fill-color: initial; filter: none; }
.app-header .app-en {
    font-family: "Consolas", "Courier New", monospace;
    color: #5fd4ff; font-size: clamp(0.7rem, 1.8vw, 0.85rem);
    letter-spacing: .3em; margin-top: 4px;
}

/* ===== 説明書ページ ===== */
.guide-hero {
    background: rgba(10, 16, 44, 0.95); border-radius: 16px; padding: 28px 24px;
    text-align: center; border: 1px solid rgba(123, 140, 255, 0.45);
    border-top: 4px solid #7b8cff;
    box-shadow: 0 0 26px rgba(123, 140, 255, 0.20);
    margin-bottom: 20px;
}
.guide-hero h2 { margin: 0 0 8px; color: #eaf2ff; }
.guide-hero p { margin: 0; color: #9fb2dd; line-height: 1.8; }
.guide-card {
    background: rgba(10, 16, 44, 0.95); border-radius: 14px; padding: 20px 24px;
    margin-bottom: 18px;
    border: 1px solid rgba(95, 130, 255, 0.25);
    border-left: 4px solid #7b8cff;
    box-shadow: 0 0 16px rgba(95, 130, 255, 0.10);
}
.guide-card.green { border-left-color: #3ef2b1; }
.guide-card.blue { border-left-color: #2d7dff; }
.guide-card.purple { border-left-color: #b43fff; }
.guide-card.pink { border-left-color: #ff5ce1; }
.guide-card h3 { margin: 0 0 10px; color: #eaf2ff; }
.guide-card p, .guide-card li { color: #b9c7ea; line-height: 1.9; margin: 5px 0; }
.guide-card ul { margin: 8px 0; padding-left: 20px; }
.guide-card b { color: #5fd4ff; }
.badge {
    display: inline-block; background: rgba(95, 130, 255, 0.14);
    color: #7da2ff; border: 1px solid rgba(95, 130, 255, 0.50);
    border-radius: 999px; padding: 2px 12px; font-size: .78rem;
    font-weight: 700; margin-right: 6px;
}
.badge.green { background: rgba(62, 242, 177, .12); color: #3ef2b1; border-color: rgba(62, 242, 177, .5); }
.badge.blue { background: rgba(45, 125, 255, .14); color: #7db3ff; border-color: rgba(45, 125, 255, .5); }
.badge.purple { background: rgba(180, 63, 255, .14); color: #d18bff; border-color: rgba(180, 63, 255, .5); }
.step { display: flex; gap: 14px; margin: 12px 0; align-items: flex-start; }
.step-num {
    background: linear-gradient(135deg, #2d7dff, #b43fff); color: #fff;
    min-width: 30px; height: 30px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; flex-shrink: 0;
    box-shadow: 0 0 12px rgba(123, 63, 242, 0.50);
}
.step-body { color: #b9c7ea; line-height: 1.8; padding-top: 3px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# タイトル
# ==========================================
st.markdown("""
<div class="app-header">
  <div class="app-sub">基本情報技術者試験</div>
  <div class="app-main"><span class="app-deco">⚡</span> 単語＆クイズ <span class="app-deco">⚡</span></div>
  <div class="app-en">VOCAB-ARCHIVE &amp; TEST-RUN</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# パス設定
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Basic_Theory_Glossary.xlsx")

CHOICE_LETTERS = ["A", "B", "C", "D"]
ORDINALS = {1: "1st", 2: "2nd", 3: "3rd"}

# ==========================================
# 1. データベース（クラウドDB専用）
#    Secrets の DATABASE_URL（Postgres/Neon等）に保存する。
#    記録はログインしたGoogleアカウント（メールアドレス）単位で分離される。
# ==========================================
def _secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def _detect_db_url():
    url = str(_secret("DATABASE_URL", "") or os.environ.get("DATABASE_URL", "")).strip()
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


DB_URL = _detect_db_url()

if not DB_URL:
    st.error("⚙️ データベースが設定されていません。\n\n"
             "Streamlit Cloud の Secrets に DATABASE_URL（Postgres接続文字列）を"
             "設定してください。詳細は「GitHub_StreamlitCloud_公開手順.txt」を"
             "参照してください。")
    st.stop()

from sqlalchemy import create_engine, text as sql_text


@st.cache_resource
def _get_engine():
    return create_engine(DB_URL, pool_pre_ping=True)


def init_db():
    with _get_engine().begin() as cx:
        cx.execute(sql_text("""
            CREATE TABLE IF NOT EXISTS quiz_records (
                user_id TEXT NOT NULL,
                qid TEXT,
                question TEXT,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                last_date TEXT,
                PRIMARY KEY (user_id, qid)
            )"""))
        cx.execute(sql_text("""
            CREATE TABLE IF NOT EXISTS check_records (
                user_id TEXT NOT NULL,
                wid TEXT,
                slot INTEGER,
                date TEXT,
                PRIMARY KEY (user_id, wid, slot)
            )"""))
        # 旧スキーマ（user_id なし）からの移行（ベストエフォート）
        try:
            for tbl, pk in (("quiz_records", "user_id, qid"),
                            ("check_records", "user_id, wid, slot")):
                cols = [r[0] for r in cx.execute(sql_text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = :t"), {"t": tbl}).fetchall()]
                if cols and "user_id" not in cols:
                    cx.execute(sql_text(
                        f"ALTER TABLE {tbl} ADD COLUMN user_id TEXT NOT NULL DEFAULT 'local'"))
                    cx.execute(sql_text(
                        f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {tbl}_pkey"))
                    cx.execute(sql_text(f"ALTER TABLE {tbl} ADD PRIMARY KEY ({pk})"))
        except Exception:
            pass


try:
    init_db()
except Exception as _db_err:
    st.error(f"⚙️ データベースに接続できませんでした。\n\n"
             f"DATABASE_URL の設定を確認してください。\n\n詳細: {_db_err}")
    st.stop()


def record_quiz_result(qid, question, is_correct):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c_add = 1 if is_correct else 0
    w_add = 0 if is_correct else 1
    with _get_engine().begin() as cx:
        cx.execute(sql_text("""
            INSERT INTO quiz_records (user_id, qid, question, correct_count, wrong_count, last_date)
            VALUES (:u, :qid, :q, :c, :w, :d)
            ON CONFLICT (user_id, qid) DO UPDATE SET
                correct_count = quiz_records.correct_count + EXCLUDED.correct_count,
                wrong_count   = quiz_records.wrong_count + EXCLUDED.wrong_count,
                last_date     = EXCLUDED.last_date
        """), {"u": USER_ID, "qid": qid, "q": question, "c": c_add, "w": w_add, "d": now})


def get_quiz_records():
    with _get_engine().connect() as cx:
        return pd.read_sql(sql_text("SELECT * FROM quiz_records WHERE user_id = :u"),
                           cx, params={"u": USER_ID})


def get_checks():
    with _get_engine().connect() as cx:
        rows = cx.execute(sql_text(
            "SELECT wid, slot, date FROM check_records WHERE user_id = :u"),
            {"u": USER_ID}).fetchall()
    return {(w, s): d for w, s, d in rows}


def set_check(wid, slot):
    today = datetime.now().strftime("%Y-%m-%d")
    with _get_engine().begin() as cx:
        cx.execute(sql_text("""
            INSERT INTO check_records (user_id, wid, slot, date) VALUES (:u, :w, :s, :d)
            ON CONFLICT (user_id, wid, slot) DO UPDATE SET date = EXCLUDED.date
        """), {"u": USER_ID, "w": wid, "s": slot, "d": today})


def clear_check(wid, slot):
    with _get_engine().begin() as cx:
        cx.execute(sql_text(
            "DELETE FROM check_records WHERE user_id=:u AND wid=:w AND slot=:s"),
            {"u": USER_ID, "w": wid, "s": slot})


# ==========================================
# 1b. バックアップ（エクスポート／インポート）※自分の記録のみ対象
# ==========================================
def export_backup_json():
    quiz = get_quiz_records().drop(columns=["user_id"], errors="ignore").to_dict(orient="records")
    checks = [{"wid": w, "slot": s, "date": d}
              for (w, s), d in get_checks().items()]
    return json.dumps({
        "app": "fe-vocab-quiz",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "quiz_records": quiz,
        "check_records": checks,
    }, ensure_ascii=False, indent=1)


def import_backup_json(text_data):
    data = json.loads(text_data)
    quiz = data.get("quiz_records", [])
    checks = data.get("check_records", [])
    with _get_engine().begin() as cx:
        for r in quiz:
            cx.execute(sql_text("""
                INSERT INTO quiz_records (user_id, qid, question, correct_count, wrong_count, last_date)
                VALUES (:u, :qid, :q, :c, :w, :d)
                ON CONFLICT (user_id, qid) DO UPDATE SET
                    question = EXCLUDED.question,
                    correct_count = EXCLUDED.correct_count,
                    wrong_count = EXCLUDED.wrong_count,
                    last_date = EXCLUDED.last_date
            """), {"u": USER_ID, "qid": r.get("qid"), "q": r.get("question"),
                   "c": int(r.get("correct_count", 0)),
                   "w": int(r.get("wrong_count", 0)),
                   "d": r.get("last_date")})
        for r in checks:
            cx.execute(sql_text("""
                INSERT INTO check_records (user_id, wid, slot, date) VALUES (:u, :w, :s, :d)
                ON CONFLICT (user_id, wid, slot) DO UPDATE SET date = EXCLUDED.date
            """), {"u": USER_ID, "w": r.get("wid"), "s": int(r.get("slot", 1)),
                   "d": r.get("date")})
    return len(quiz), len(checks)


# ==========================================
# 1c. Googleログイン（必須）
#     記録はGoogleアカウント（メールアドレス）単位で保存される
# ==========================================
def _auth_enabled():
    try:
        return "auth" in st.secrets
    except Exception:
        return False


AUTH_ENABLED = _auth_enabled()
DEV_USER = str(_secret("DEV_USER", "")).strip()  # 開発・動作確認用

if AUTH_ENABLED:
    if not st.user.is_logged_in:
        st.markdown("""
<div class="guide-hero">
  <h2>🔐 ログイン</h2>
  <p>学習記録をあなたのGoogleアカウントに紐づけて保存します。<br>
  記録は本人のアカウントでログインしたときだけ表示されます。</p>
</div>
""", unsafe_allow_html=True)
        if st.button("🔑 Googleアカウントでログイン", key="login_btn",
                     use_container_width=True, type="primary"):
            st.login()
        st.stop()
    USER_ID = str(st.user.email)
elif DEV_USER:
    USER_ID = DEV_USER  # ログインなしの動作確認モード
else:
    st.error("⚙️ Googleログインが設定されていません。\n\n"
             "Streamlit Cloud の Secrets に [auth]（Googleログイン設定）を"
             "追加してください。詳細は「GitHub_StreamlitCloud_公開手順.txt」を"
             "参照してください。")
    st.stop()

# ==========================================
# 2. Excelファイルの読み込み
# ==========================================
@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_PATH):
        st.error(f"❌ エクセルファイルが見つかりません。\n"
                 f"「Basic_Theory_Glossary.xlsx」を app.py と同じフォルダに置いてください。\n"
                 f"（現在探している場所: {EXCEL_PATH}）")
        st.stop()
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        st.error(f"❌ Excelファイルの読み込み中にエラーが発生しました:\n{e}")
        st.stop()

    df.columns = df.columns.astype(str).str.strip()

    required_cols = ["大分類名称", "中分類名称", "小分類名称", "細目名称", "用語", "説明",
                     "頻出レベル", "問題文", "選択肢A", "選択肢B", "選択肢C", "選択肢D", "正解"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Excelファイルに必要な列が見つかりません: {missing}\n"
                 f"（実際の列: {list(df.columns)}）")
        st.stop()

    df = df.rename(columns={
        "大分類名称": "大分類",
        "中分類名称": "中分類",
        "小分類名称": "小分類",
        "細目名称": "細目",
        "用語": "単語",
        "説明": "単語の意味",
        "頻出レベル": "難易度",
        "問題文": "問題",
    })

    for col in ["大分類", "中分類", "小分類", "細目", "難易度", "問題",
                "選択肢A", "選択肢B", "選択肢C", "選択肢D"]:
        df[col] = df[col].astype(str).str.strip()
    df["正解"] = df["正解"].astype(str).str.strip().str.upper()

    df = df[df["問題"].ne("") & df["正解"].isin(CHOICE_LETTERS)].copy()

    def make_qid(row):
        src = "|".join([row["問題"], row["選択肢A"], row["選択肢B"],
                        row["選択肢C"], row["選択肢D"]])
        return hashlib.md5(src.encode("utf-8")).hexdigest()

    df["qid"] = df.apply(make_qid, axis=1)
    df = df.drop_duplicates(subset="qid").reset_index(drop=True)

    df["単語"] = df["単語"].fillna("").astype(str).str.strip()
    df["単語の意味"] = df["単語の意味"].fillna("").astype(str).str.strip()
    df["wid"] = (df["単語"] + "|" + df["単語の意味"]).map(
        lambda s: hashlib.md5(s.encode("utf-8")).hexdigest())
    return df


df = load_data()

# ==========================================
# 3. ページ管理（ホーム画面方式＋ナビバー）
# ==========================================
if "page" not in st.session_state:
    st.session_state.page = "home"


def goto(p):
    st.session_state.page = p
    st.rerun()


page = st.session_state.page

PAGE_BG = {
    "home": "linear-gradient(135deg, #060a28 0%, #1b0f3f 55%, #0a1135 100%)",
    "list": "linear-gradient(135deg, #051226 0%, #0a2440 50%, #101040 100%)",
    "quiz": "linear-gradient(135deg, #070b2e 0%, #1d1048 55%, #0a1440 100%)",
    "guide": "linear-gradient(135deg, #120a30 0%, #2a0e3d 55%, #160a35 100%)",
}
st.markdown("<style>.stApp { background: " + PAGE_BG[page] +
            " fixed; }</style>", unsafe_allow_html=True)


def page_header(num, code, title, sub=""):
    h = (f"<div class='pg-eyebrow'>{num} / {code}</div>"
         f"<div class='pg-title'>{title}</div>")
    if sub:
        h += f"<p class='pg-sub'>{sub}</p>"
    st.markdown(h, unsafe_allow_html=True)


# ナビゲーションバー（どのページからでも各モードへ移動可能）
if page != "home":
    nav_items = [("home", "⌂ HOME"), ("list", "📋 単語一覧"),
                 ("quiz", "🎮 クイズ"), ("guide", "📖 説明書")]
    nav_cols = st.columns(4)
    for (p_key, p_label), nc in zip(nav_items, nav_cols):
        with nc:
            if st.button(p_label, key=f"nav_{p_key}", use_container_width=True,
                         disabled=(page == p_key)):
                goto(p_key)


# ==========================================
# 4. 絞り込み共通関数（大分類→中分類→小分類→細目→頻出レベル）
# ==========================================
def category_filters(container, base_df, key_prefix):
    """絞り込みUI。絞り込み後のdfと条件ラベルを返す"""
    result = base_df

    majors = ["すべて"] + sorted(result["大分類"].unique().tolist())
    sel_major = container.selectbox("大分類", majors, key=f"{key_prefix}_major")
    if sel_major != "すべて":
        result = result[result["大分類"] == sel_major]

    minors = ["すべて"] + sorted(result["中分類"].unique().tolist())
    sel_minor = container.selectbox("中分類", minors, key=f"{key_prefix}_minor")
    if sel_minor != "すべて":
        result = result[result["中分類"] == sel_minor]

    smalls = ["すべて"] + sorted(result["小分類"].unique().tolist())
    sel_small = container.selectbox("小分類", smalls, key=f"{key_prefix}_small")
    if sel_small != "すべて":
        result = result[result["小分類"] == sel_small]

    details = ["すべて"] + sorted(result["細目"].unique().tolist())
    sel_detail = container.selectbox("細目", details, key=f"{key_prefix}_detail")
    if sel_detail != "すべて":
        result = result[result["細目"] == sel_detail]

    diffs = ["すべて"] + sorted(result["難易度"].unique().tolist())
    sel_diff = container.selectbox("頻出レベル（A=頻出）", diffs, key=f"{key_prefix}_diff")
    if sel_diff != "すべて":
        result = result[result["難易度"] == sel_diff]

    labels = [x for x in [sel_major, sel_minor, sel_small, sel_detail] if x != "すべて"]
    if sel_diff != "すべて":
        labels.append(f"レベル{sel_diff}")
    label = " ➔ ".join(labels) if labels else "全範囲"
    return result, label


# ------------------------------------------
# ページ0：ホーム画面
# ------------------------------------------
if page == "home":
    st.sidebar.header("🏠 HOME")
    st.sidebar.write("メニューを選択してください。")

    page_header("01", "HOME", "ホーム画面", "メインダッシュボードからモードを選択")

    if st.button("📋　単語一覧 ─ 用語リストの閲覧・検索", key="home_list",
                 use_container_width=True):
        goto("list")
    if st.button("🎮　4択テストに挑戦 ─ クイズモードで学習", key="home_quiz",
                 use_container_width=True):
        goto("quiz")
    if st.button("📖　説明書 ─ 使い方ガイド", key="home_guide",
                 use_container_width=True):
        goto("guide")

# ------------------------------------------
# ページ1：単語一覧
# ------------------------------------------
elif page == "list":
    page_header("02", "WORD LIST", "単語一覧")

    st.sidebar.header("🔍 絞り込み条件")
    filtered_df, _ = category_filters(st.sidebar, df, "list")

    checks = get_checks()
    check_count_by_wid = {}
    for (w, _slot) in checks:
        check_count_by_wid[w] = check_count_by_wid.get(w, 0) + 1

    words_df = filtered_df.drop_duplicates(subset="wid")

    sel_chk = st.sidebar.selectbox("チェック数", ["すべて", "0個", "1個", "2個", "3個"],
                                   key="list_chk")
    if sel_chk != "すべて":
        n_chk = int(sel_chk[0])
        words_df = words_df[words_df["wid"].map(
            lambda w: check_count_by_wid.get(w, 0)) == n_chk]

    st.sidebar.write(f"**現在の対象数: {len(words_df)} 件**")
    hide_meaning = st.sidebar.toggle("🙈 暗記モード（意味を隠す）", key="hide_meaning")

    search_query = st.text_input("単語や意味からキーワードで検索")
    display_df = words_df
    if search_query:
        mask = (display_df["単語"].str.contains(search_query, na=False, regex=False)
                | display_df["単語の意味"].str.contains(search_query, na=False, regex=False))
        display_df = display_df[mask]

    total = len(display_df)
    col_a, col_b = st.columns(2)
    with col_a:
        page_size = st.selectbox("1ページの表示件数", [10, 20, 50, 100], index=1)
    n_pages = max(1, math.ceil(total / page_size))
    with col_b:
        pg = st.number_input(f"ページ (全{n_pages}ページ)", min_value=1,
                             max_value=n_pages, value=1, step=1)

    start = (pg - 1) * page_size
    page_df = display_df.iloc[start:start + page_size]
    st.write(f"対象 {total} 件中 {start + 1}〜{start + len(page_df)} 件を表示")
    st.caption("✔ 右上の 1st / 2nd / 3rd ボタンで「確認した日」を記録できます（✅を押すと取り消し）")

    for _, row in page_df.iterrows():
        wid = row["wid"]
        with st.container(border=True, key=f"card_{wid}"):
            left, right = st.columns([7, 5], vertical_alignment="center")
            with left:
                st.markdown(f"#### ✨ {row['単語'] if row['単語'] else '（用語なし）'}")
                st.caption(f"📌 {row['大分類']} ＞ {row['中分類']} ＞ {row['小分類']}"
                           f" ＞ {row['細目']} | 頻出レベル: {row['難易度']}")
            with right:
                check_cols = st.columns(3)
                for slot, cc in zip((1, 2, 3), check_cols):
                    date = checks.get((wid, slot))
                    with cc:
                        if date:
                            if st.button("✅", key=f"chk_{wid}_{slot}",
                                         use_container_width=True,
                                         help=f"{ORDINALS[slot]} に確認した日: {date}（押すと取り消し）"):
                                clear_check(wid, slot)
                                st.rerun()
                            st.markdown(f"<div class='chk-date'>{date[5:].replace('-', '/')}</div>",
                                        unsafe_allow_html=True)
                        else:
                            if st.button(ORDINALS[slot], key=f"chk_{wid}_{slot}",
                                         use_container_width=True,
                                         help=f"{ORDINALS[slot]} の確認チェックを付ける"):
                                set_check(wid, slot)
                                st.rerun()
                            st.markdown("<div class='chk-date'>未確認</div>",
                                        unsafe_allow_html=True)
            meaning = row['単語の意味'] if row['単語の意味'] else '（解説なし）'
            if hide_meaning:
                with st.expander("📖 意味を表示"):
                    st.markdown(f"📝 {meaning}")
            else:
                st.markdown(f"📝 {meaning}")

# ------------------------------------------
# ページ2：4択テスト
# ------------------------------------------
elif page == "quiz":
    defaults = {"test_active": False, "test_questions": None, "test_index": 0,
                "test_answered": False, "test_selected": None, "test_score": 0,
                "test_mode_name": "", "test_wrong_qids": [], "test_seed": 0.0}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    def start_test(questions, mode_name):
        st.session_state.test_questions = questions.reset_index(drop=True)
        st.session_state.test_index = 0
        st.session_state.test_active = True
        st.session_state.test_answered = False
        st.session_state.test_selected = None
        st.session_state.test_score = 0
        st.session_state.test_mode_name = mode_name
        st.session_state.test_wrong_qids = []
        st.session_state.test_seed = random.random()

    st.sidebar.header("🎯 クイズモード")
    st.sidebar.write("条件を絞り込んでクイズを開始できます。")

    if not st.session_state.test_active:
        page_header("03", "QUIZ SETUP", "出題条件設定",
                    "フィルター条件を選択してテストを開始")

        st.markdown("### 1️⃣ 条件を指定してテスト")
        test_target_df, mode_name = category_filters(st, df, "test")

        rec_df = get_quiz_records()
        correct_by_qid = (dict(zip(rec_df["qid"], rec_df["correct_count"]))
                          if not rec_df.empty else {})
        sel_target = st.selectbox(
            "出題対象",
            ["すべて", "未正解の問題のみ", "正解1回以下の問題のみ"],
            key="test_target")
        if sel_target == "未正解の問題のみ":
            test_target_df = test_target_df[test_target_df["qid"].map(
                lambda x: correct_by_qid.get(x, 0)) == 0]
            mode_name += "（未正解のみ）"
        elif sel_target == "正解1回以下の問題のみ":
            test_target_df = test_target_df[test_target_df["qid"].map(
                lambda x: correct_by_qid.get(x, 0)) <= 1]
            mode_name += "（正解1回以下）"

        num_options = ["5", "10", "20", "30", "すべて"]
        sel_num = st.selectbox("出題数", num_options, index=1, key="test_num")

        if st.button(f"📁 【{mode_name}】のテストを開始 (対象 {len(test_target_df)} 問)",
                     use_container_width=True, key="start_test_btn"):
            if len(test_target_df) > 0:
                if sel_num == "すべて":
                    qs = test_target_df.sample(frac=1)
                else:
                    qs = test_target_df.sample(n=min(int(sel_num), len(test_target_df)))
                start_test(qs, mode_name)
                st.rerun()
            else:
                st.warning("選択した条件に合致する問題がありません。")

        st.write("")
        st.markdown("### 2️⃣ ランダムテスト")
        if st.button("🎲 【全問題からランダム10問】テストを開始",
                     use_container_width=True, key="start_random_btn"):
            start_test(df.sample(n=min(10, len(df))), "全問からランダム10問")
            st.rerun()

        st.write("")
        st.markdown("### 3️⃣ 単語で抽出（テスト一覧）")
        col_kw1, col_kw2 = st.columns([4, 1], vertical_alignment="bottom")
        with col_kw1:
            kw = st.text_input("問題文・選択肢に含まれる単語を入力（例: ハッシュ）",
                               key="kw_extract")
        with col_kw2:
            st.button("🔍 検索", key="kw_search_btn", use_container_width=True)
        if kw:
            kw_mask = df["問題"].str.contains(kw, na=False, regex=False)
            for letter in CHOICE_LETTERS:
                kw_mask |= df[f"選択肢{letter}"].str.contains(kw, na=False, regex=False)
            kw_df = df[kw_mask]
            if len(kw_df) == 0:
                st.warning(f"「{kw}」を含む問題は見つかりませんでした。")
            else:
                st.markdown("""
<style>
.flip-container { margin-bottom: 18px; }
.flip-toggle { display: none !important; }
.flip-card { display: block; background-color: transparent; perspective: 1000px; cursor: pointer; }
.flip-card-inner { position: relative; width: 100%; transition: transform 0.6s ease; transform-style: preserve-3d; }
.flip-toggle:checked + .flip-card .flip-card-inner { transform: rotateY(180deg); }
.flip-card-front, .flip-card-back { width: 100%; backface-visibility: hidden; border-radius: 14px; padding: 22px 24px; box-sizing: border-box; }
.flip-card-front { position: relative; background-color: rgba(10,16,44,0.95); border: 1px solid rgba(45,226,255,0.40); border-left: 4px solid #2de2ff; box-shadow: 0 0 16px rgba(45,140,255,0.12); }
.flip-card-back { position: absolute; top: 0; left: 0; height: 100%; background-color: rgba(20,12,48,0.97); border: 1px solid rgba(180,63,255,0.45); border-left: 4px solid #b43fff; transform: rotateY(180deg); overflow-y: auto; box-shadow: 0 0 16px rgba(180,63,255,0.15); }
.q-tags { font-size: 0.85rem; color: #5d6f9e; margin-bottom: 10px; font-weight: 500; padding-right: 150px; }
.q-text { font-size: 1.05rem; font-weight: bold; color: #eaf2ff; margin-bottom: 12px; line-height: 1.7; }
.q-choice { font-size: 0.95rem; color: #b9c7ea; margin-bottom: 6px; line-height: 1.6; }
.q-ans { font-size: 1.1rem; color: #5fd4ff; font-weight: bold; margin-bottom: 14px;}
.q-desc { font-size: 0.95rem; color: #b9c7ea; line-height: 1.7; }
.q-stat { position: absolute; top: 16px; right: 18px; font-size: 0.78rem; color: #5fd4ff;
          border: 1px solid rgba(95, 212, 255, 0.45); border-radius: 999px;
          padding: 2px 12px; white-space: nowrap; }
.q-stat.na { color: #7e8db5; border-color: rgba(126, 141, 181, 0.45); }
.hint-txt { text-align: right; color: #44537a; font-size: 0.8rem; margin-top: 10px; font-style: italic;}
</style>
""", unsafe_allow_html=True)

                total_kw = len(kw_df)
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    kw_page_size = st.selectbox("1ページの表示件数", [5, 10, 20, 50],
                                                index=1, key="kw_size")
                kw_pages = max(1, math.ceil(total_kw / kw_page_size))
                with col_k2:
                    kw_page = st.number_input(f"ページ (全{kw_pages}ページ)", min_value=1,
                                              max_value=kw_pages, value=1, step=1,
                                              key="kw_page")
                kw_start = (kw_page - 1) * kw_page_size
                kw_page_df = kw_df.iloc[kw_start:kw_start + kw_page_size]
                st.write(f"「{kw}」を含む問題 {total_kw} 件中 "
                         f"{kw_start + 1}〜{kw_start + len(kw_page_df)} 件を表示"
                         "（カードをタップすると答えが見られます）")

                stats_by_qid = ({r.qid: (int(r.correct_count), int(r.wrong_count))
                                 for r in rec_df.itertuples()}
                                if not rec_df.empty else {})

                e = html.escape
                cards = []
                for i, (_, r) in enumerate(kw_page_df.iterrows()):
                    correct = e(str(r[f"選択肢{r['正解']}"]))
                    choice_lines = "".join(
                        f'<div class="q-choice">{e(str(r[f"選択肢{letter}"]))}</div>'
                        for letter in CHOICE_LETTERS)
                    desc = (f'<div class="q-desc">📖 【{e(r["単語"])}】 {e(r["単語の意味"])}</div>'
                            if r["単語"] and r["単語の意味"] else "")
                    cw = stats_by_qid.get(r["qid"])
                    if cw:
                        stat_html = f'<div class="q-stat">正解 {cw[0]} / 不正解 {cw[1]}</div>'
                    else:
                        stat_html = '<div class="q-stat na">未挑戦</div>'
                    cards.append(f'''
<div class="flip-container">
  <input type="checkbox" id="kwcard-{i}" class="flip-toggle">
  <label for="kwcard-{i}" class="flip-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        {stat_html}
        <div class="q-tags">📌 {e(r['大分類'])} ＞ {e(r['中分類'])} ＞ {e(r['小分類'])} ＞ {e(r['細目'])} | 頻出レベル: {e(r['難易度'])}</div>
        <div class="q-text">Q. {e(r['問題'])}</div>
        {choice_lines}
        <div class="hint-txt">👆 タップして答えを見る</div>
      </div>
      <div class="flip-card-back">
        <div class="q-tags">✅ 答え</div>
        <div class="q-ans">💡 正解: {correct}</div>
        {desc}
        <div class="hint-txt">🔄 もう一度タップして戻る</div>
      </div>
    </div>
  </label>
</div>''')
                st.markdown("\n".join(cards), unsafe_allow_html=True)

    else:
        idx = st.session_state.test_index
        questions = st.session_state.test_questions

        if idx >= len(questions):
            page_header("05", "RESULTS", "結果画面")
            total_qs = len(questions)
            score = st.session_state.test_score
            rate = round(score / total_qs * 100, 1) if total_qs > 0 else 0
            rate_disp = int(rate) if rate == int(rate) else rate

            st.write(f"**実施モード:** {st.session_state.test_mode_name}")

            st.markdown(f"""
<div class="score-card">
  <div class="score-label">YOUR SCORE</div>
  <div class="score-pct">{rate_disp}%</div>
  <div class="score-sub">{score} / {total_qs} 問正解</div>
</div>
""", unsafe_allow_html=True)

            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown(f"<div class='stat-card'><div class='stat-label'>正解</div>"
                            f"<div class='stat-value cyan'>{score}</div></div>",
                            unsafe_allow_html=True)
            with sc2:
                st.markdown(f"<div class='stat-card'><div class='stat-label'>不正解</div>"
                            f"<div class='stat-value orange'>{total_qs - score}</div></div>",
                            unsafe_allow_html=True)

            if rate == 100:
                st.balloons()
                st.success("素晴らしい！全問正解です！パーフェクト！ 🏆✨")
            elif rate >= 80:
                st.success("高得点です！この調子でマスターを目指しましょう！ 👍")
            elif rate >= 60:
                st.info("合格点クリアです！間違えた問題を復習しておきましょう。 💪")
            else:
                st.warning("もう少し頑張りましょう！単語一覧で復習するのがおすすめです。 📝")

            st.write("")
            if st.button("🔄 もう一度挑戦", use_container_width=True,
                         key="retry_same_btn"):
                start_test(questions.sample(frac=1), st.session_state.test_mode_name)
                st.rerun()

            wrong_qids = st.session_state.get("test_wrong_qids", [])
            if wrong_qids:
                if st.button(f"🔁 間違えた {len(wrong_qids)} 問だけ復習",
                             use_container_width=True, key="retry_wrong_btn"):
                    retry_df = df[df["qid"].isin(wrong_qids)]
                    start_test(retry_df.sample(frac=1),
                               st.session_state.test_mode_name + "・復習")
                    st.rerun()

            if st.button("⌂ ホームに戻る", use_container_width=True,
                         type="primary", key="back_home_btn"):
                st.session_state.test_active = False
                goto("home")

        else:
            q = questions.iloc[idx]

            page_header("04", "QUIZ SCREEN",
                        f"テスト挑戦中（{st.session_state.test_mode_name}）")
            st.markdown(f"<div class='q-meta'>問題 {idx + 1} / {len(questions)}</div>",
                        unsafe_allow_html=True)
            st.progress(idx / len(questions))

            st.caption(f"{q['大分類']} ＞ {q['中分類']} ＞ {q['小分類']} ＞ {q['細目']}"
                       f" | 頻出レベル: {q['難易度']}")
            st.markdown(f"<div class='q-panel'>Q. {html.escape(q['問題'])}</div>",
                        unsafe_allow_html=True)

            # 選択肢をシャッフルして記号を振り直す（同じ問題の表示中は順序固定）
            rng = random.Random(f"{st.session_state.test_seed}_{q['qid']}")
            shuffled = rng.sample(CHOICE_LETTERS, len(CHOICE_LETTERS))

            def choice_body(letter):
                text = str(q[f"選択肢{letter}"])
                return text[2:] if len(text) > 2 and text[0] in "ABCD" and text[1] in ".．" else text

            choices = [(orig, f"{new}.　{choice_body(orig)}")
                       for new, orig in zip(CHOICE_LETTERS, shuffled)]

            if not st.session_state.test_answered:
                for i, (letter, text) in enumerate(choices):
                    if st.button(text, key=f"ans_{idx}_{i}", use_container_width=True):
                        st.session_state.test_selected = letter
                        st.session_state.test_answered = True
                        is_correct = (letter == q["正解"])
                        if is_correct:
                            st.session_state.test_score += 1
                        else:
                            st.session_state.test_wrong_qids.append(q["qid"])
                        record_quiz_result(q["qid"], q["問題"], is_correct)
                        st.rerun()
            else:
                selected = st.session_state.test_selected
                correct = q["正解"]

                if selected == correct:
                    st.success("✨ **正解です！**")
                else:
                    st.error("❌ **不正解...**")

                for letter, text in choices:
                    if letter == correct:
                        st.info(f"🟩 {text} （★これが正解）")
                    elif letter == selected:
                        st.write(f"🟥 {text} （あなたの回答）")
                    else:
                        st.write(f"⬜ {text}")

                if q["単語"] and q["単語の意味"]:
                    st.warning(f"📖 **関連用語の解説:**\n\n**【{q['単語']}】**\n{q['単語の意味']}")

                st.write("---")
                history = get_quiz_records()
                if not history.empty and q["qid"] in history["qid"].values:
                    stats = history[history["qid"] == q["qid"]].iloc[0]
                    t = stats["correct_count"] + stats["wrong_count"]
                    rate = round(stats["correct_count"] / t * 100, 1) if t > 0 else 0
                    st.caption(f"📊 この問題の通算戦績: 正解 {stats['correct_count']}回 / "
                               f"不正解 {stats['wrong_count']}回 (正解率 {rate}%)")

                st.write("")
                if st.button("次へ ➡️", key="next_q_btn", type="primary",
                             use_container_width=True):
                    st.session_state.test_index += 1
                    st.session_state.test_answered = False
                    st.session_state.test_selected = None
                    st.rerun()

            st.write("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ 中断（メニューに戻る）", key="abort_test_btn",
                             use_container_width=True):
                    st.session_state.test_active = False
                    st.rerun()
            with col2:
                if st.button("🏁 テスト終了（結果発表へ）", key="finish_test_early_btn",
                             use_container_width=True):
                    actual_count = idx + 1 if st.session_state.test_answered else idx
                    if actual_count > 0:
                        st.session_state.test_questions = questions.iloc[:actual_count].reset_index(drop=True)
                        st.session_state.test_index = actual_count
                    else:
                        st.session_state.test_active = False
                    st.rerun()

# ------------------------------------------
# ページ3：説明書（使い方ガイド）
# ------------------------------------------
else:
    st.sidebar.header("📖 説明書")
    st.sidebar.write("このアプリの使い方ガイドです。")

    page_header("06", "GUIDE", "説明書")

    storage_now = f"✅ ログイン中: {USER_ID} ── 記録はこのアカウントに保存されています。"

    st.markdown(f"""
<div class="guide-hero">
  <h2>⚡ SYSTEM GUIDE ─ 単語＆クイズの世界へ ⚡</h2>
  <p>このアプリは、基本情報技術者試験の<b>2964問</b>を収録した<br>
  あなた専用の単語帳＆クイズマシンです。<br>
  スキマ時間にポチポチするだけで、合格にグングン近づきます💨</p>
</div>

<div class="guide-card green">
  <h3>📋 単語一覧 ─ WORD LIST</h3>
  <p><span class="badge green">単語帳</span>単語と意味のカードがずらり。まずはここで知識をインプット！</p>
  <ul>
    <li>🔖 カード右上の「1st・2nd・3rd」ボタンで<b>確認した日を記録</b>。
        3周まわせば記憶はバッチリ！（押し間違えたら✅をもう一度押せば取り消し）</li>
    <li>🔍 サイドバーで<b>分類（細目まで）・頻出レベル・チェック数</b>の絞り込みができます。
        「チェック0個」で絞れば、まだ見ていない単語だけに集中！</li>
    <li>🙈 <b>暗記モード</b>をONにすると意味が隠れます。
        頭の中で答えてからクリックして答え合わせ！</li>
  </ul>
</div>

<div class="guide-card blue">
  <h3>🎮 4択テストに挑戦 ─ QUIZ</h3>
  <p><span class="badge blue">クイズ</span>覚えた知識をテストでアウトプット！始め方は3つ。</p>
  <div class="step"><div class="step-num">1</div><div class="step-body">
    <b>条件を指定してテスト</b> … 分類（細目まで）・頻出レベル・出題数を選んでスタート。
    「出題対象」で<b>未正解の問題だけ</b>に絞れば、弱点克服モードに！</div></div>
  <div class="step"><div class="step-num">2</div><div class="step-body">
    <b>ランダムテスト</b> … 全問からランダムに10問。今日の腕試しにどうぞ🎲</div></div>
  <div class="step"><div class="step-num">3</div><div class="step-body">
    <b>単語で抽出（テスト一覧）</b> … 気になる単語を入力して🔍検索すると、
    その単語を含む問題がカードでずらり。カード右上にこれまでの戦績
    （正解/不正解、未挑戦）が表示されます。タップすると裏返って答えが見えます🃏</div></div>
  <p>💫 選択肢は毎回シャッフル！「答えの位置」では覚えられません（いいことです）。<br>
  🔁 結果画面では「もう一度挑戦」「間違えた問題だけ復習」でその場でリベンジできます。</p>
</div>

<div class="guide-card purple">
  <h3>📈 進捗ダッシュボード</h3>
  <p><span class="badge purple">記録</span>サイドバーの下にひっそり待機。開くと…</p>
  <ul>
    <li>✅ チェック済み単語数（全体のどこまで進んだ？）</li>
    <li>🎯 クイズ通算正解率＆挑戦済み問題数</li>
    <li>📊 分類ごとの進捗バー（苦手分野がまるわかり）</li>
  </ul>
</div>

<div class="guide-card pink">
  <h3>💾 学習記録はぜんぶ自動保存</h3>
  <p><b>チェックや正誤記録は、ログインした「あなたのGoogleアカウント
  （メールアドレス）」を名札にして、インターネット上の専用データベースに
  自動保存されます。</b>
  保存ボタンを押す必要はありません。アプリを閉じても、
  スマホでも別のパソコンでも、同じアカウントでログインすれば
  いつでも続きから学習できます。</p>
  <p>🔒 記録は本人だけのもの──ほかの利用者に見られたり
  混ざったりすることはありません。ログアウトしても記録は消えず、
  次にログインしたときにまた表示されます。</p>
  <p>🔁 心配なときは、サイドバーの「💾 バックアップ／復元」で
  自分の記録をファイルに書き出して保険として残せます。</p>
  <p>{storage_now}</p>
</div>

<div class="guide-card">
  <h3>🏆 おすすめ勉強法「3周チェック法」</h3>
  <div class="step"><div class="step-num">1</div><div class="step-body">
    <b>1周目</b>：単語一覧をざっと読んで「1st」をポチ。完璧じゃなくてOK！</div></div>
  <div class="step"><div class="step-num">2</div><div class="step-body">
    <b>2周目</b>：暗記モードで自分テスト。思い出せたら「2nd」をポチ。</div></div>
  <div class="step"><div class="step-num">3</div><div class="step-body">
    <b>3周目</b>：クイズで腕試し→間違えた問題だけ復習→「3rd」をポチ。</div></div>
  <p>チェック3個の単語が増えるほど、合格が近づきます。がんばって！💪✨</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# サイドバー：アカウント（Googleログイン時のみ表示）
# ==========================================
st.sidebar.caption(f"👤 ログイン中: {USER_ID}")
if AUTH_ENABLED:
    if st.sidebar.button("🚪 ログアウト", key="logout_btn", use_container_width=True):
        st.logout()

# ==========================================
# サイドバー下部：進捗ダッシュボード（共通）
# ==========================================
with st.sidebar.expander("📈 進捗ダッシュボード", expanded=False):
    all_words = df.drop_duplicates(subset="wid")
    checks_all = get_checks()
    checked_wids = {w for (w, _s) in checks_all}
    n_checked = sum(1 for w in all_words["wid"] if w in checked_wids)
    st.metric("チェック済み単語", f"{n_checked} / {len(all_words)}")

    rec_all = get_quiz_records()
    if not rec_all.empty:
        total_ans = int(rec_all["correct_count"].sum() + rec_all["wrong_count"].sum())
        total_cor = int(rec_all["correct_count"].sum())
        rate_all = round(total_cor / total_ans * 100, 1) if total_ans else 0
        st.metric("クイズ通算正解率", f"{rate_all}%",
                  delta=f"{total_cor} / {total_ans} 回")
        st.metric("挑戦済み問題数", f"{len(rec_all)} / {len(df)}")
    else:
        st.metric("クイズ通算正解率", "未実施")

    st.caption("分類別チェック進捗")
    for major, g in all_words.groupby("大分類", sort=False):
        c = sum(1 for w in g["wid"] if w in checked_wids)
        st.progress(c / len(g) if len(g) else 0.0, text=f"{major} {c}/{len(g)}")

# ==========================================
# サイドバー下部：バックアップ／復元（共通）
# ==========================================
with st.sidebar.expander("💾 バックアップ／復元", expanded=False):
    if "bk_msg" in st.session_state:
        st.success(st.session_state.pop("bk_msg"))
    st.caption(f"保存先: ☁ クラウドDB（{USER_ID} 専用）")
    st.download_button(
        "⬇ 記録をダウンロード",
        data=export_backup_json(),
        file_name=f"quiz_backup_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True,
        key="bk_download",
    )
    up = st.file_uploader("バックアップ(.json)から復元", type=["json"], key="bk_upload")
    if up is not None:
        if st.button("⬆ この内容で復元（同じ問題は上書き）", key="bk_restore_btn",
                     use_container_width=True):
            try:
                n1, n2 = import_backup_json(up.getvalue().decode("utf-8"))
                st.session_state["bk_msg"] = f"復元しました（クイズ記録 {n1} 件 / チェック {n2} 件）"
                st.rerun()
            except Exception as ex:
                st.error(f"復元に失敗しました: {ex}")
