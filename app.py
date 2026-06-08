import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import sqlite3
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="基本情報 単語帳", layout="centered", initial_sidebar_state="expanded")
st.title("📚 基本情報技術者試験 単語帳")

# ==========================================
# データベースの準備
# ==========================================
def init_db():
    conn = sqlite3.connect("words.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS seen_records (
            word TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            date1 TEXT, date2 TEXT, date3 TEXT, date4 TEXT, date5 TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def mark_as_seen(word):
    conn = sqlite3.connect("words.db")
    c = conn.cursor()
    c.execute("SELECT count FROM seen_records WHERE word=?", (word,))
    row = c.fetchone()
    now = datetime.now().strftime("%Y-%m-%d")
    
    if row is None:
        c.execute("INSERT INTO seen_records (word, count, date1) VALUES (?, 1, ?)", (word, now))
    else:
        count = row[0]
        if count < 5:
            count += 1
            date_col = f"date{count}"
            c.execute(f"UPDATE seen_records SET count=?, {date_col}=? WHERE word=?", (count, now, word))
    conn.commit()
    conn.close()

def get_seen_data():
    conn = sqlite3.connect("words.db")
    df = pd.read_sql("SELECT * FROM seen_records", conn)
    conn.close()
    return df

# ==========================================
# 音声読み上げ用の関数
# ==========================================
def tts_button(word, meaning):
    text_to_speak = f"{word}。。 {meaning}"
    js_text = json.dumps(text_to_speak, ensure_ascii=False)
    
    js_code = f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
        <span style="font-size:14px; font-weight:bold; color:#333;">⚙️ スピード:</span>
        <input type="range" id="rateSlider" min="0.8" max="2.0" step="0.1" value="1.0" oninput="updateRate(this.value)">
        <span id="rateValue" style="font-size:14px; font-weight:bold; width:30px; color:#333;">1.0</span>
    </div>
    <button onclick="speak()" style="font-size:16px; padding:10px 20px; border-radius:8px; border:none; background-color:#4CAF50; color:white; cursor:pointer; width:100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        🔊 音声で読み上げ
    </button>
    <script>
    const rateSlider = document.getElementById('rateSlider');
    const rateValue = document.getElementById('rateValue');
    const savedRate = localStorage.getItem('speechRate') || "1.0";
    rateSlider.value = savedRate;
    rateValue.innerText = savedRate;
    
    function updateRate(val) {{
        rateValue.innerText = val;
        localStorage.setItem('speechRate', val);
    }}

    window.speechSynthesis.getVoices();

    function speak() {{
        const synth = window.speechSynthesis;
        const unlock = new SpeechSynthesisUtterance('');
        unlock.volume = 0;
        synth.speak(unlock);
        synth.cancel();

        setTimeout(() => {{
            const text = {js_text};
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'ja-JP'; 
            utterance.rate = parseFloat(rateSlider.value); 
            
            const voices = synth.getVoices();
            const jpVoices = voices.filter(v => v.lang.includes('ja'));
            if (jpVoices.length > 0) {{
                const premiumVoice = jpVoices.find(v => 
                    v.name.includes('Google') || v.name.includes('Premium') || 
                    v.name.includes('Siri') || v.name.includes('Kyoko') || v.name.includes('Nanami')
                );
                utterance.voice = premiumVoice ? premiumVoice : jpVoices[0];
            }}
            
            synth.speak(utterance);
        }}, 300);
    }}
    </script>
    """
    components.html(js_code, height=90)


def tts_all_button(df):
    data = df[["単語", "単語の意味"]].to_dict(orient="records")
    js_data = json.dumps(data, ensure_ascii=False)
    
    js_code = f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
        <span style="font-size:14px; font-weight:bold; color:#333;">⚙️ 読み上げスピード:</span>
        <input type="range" id="rateSliderAll" min="0.8" max="2.0" step="0.1" value="1.0" oninput="updateRateAll(this.value)">
        <span id="rateValueAll" style="font-size:14px; font-weight:bold; width:30px; color:#333;">1.0</span>
    </div>
    <div style="display: flex; gap: 5px;">
        <button onclick="speakAll()" style="font-size:14px; padding:8px 5px; border-radius:8px; border:none; background-color:#2196F3; color:white; cursor:pointer; flex:1; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            🔊 一括再生
        </button>
        <button onclick="pauseSpeaking()" style="font-size:14px; padding:8px 5px; border-radius:8px; border:none; background-color:#FF9800; color:white; cursor:pointer; flex:1; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            ⏸️ 一時停止
        </button>
        <button onclick="resumeSpeaking()" style="font-size:14px; padding:8px 5px; border-radius:8px; border:none; background-color:#4CAF50; color:white; cursor:pointer; flex:1; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            ▶️ 再開
        </button>
        <button onclick="stopSpeaking()" style="font-size:14px; padding:8px 5px; border-radius:8px; border:none; background-color:#f44336; color:white; cursor:pointer; flex:1; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            ⏹️ 停止
        </button>
    </div>
    <script>
    const rateSlider = document.getElementById('rateSliderAll');
    const rateValue = document.getElementById('rateValueAll');
    const savedRate = localStorage.getItem('speechRate') || "1.0";
    rateSlider.value = savedRate;
    rateValue.innerText = savedRate;
    
    function updateRateAll(val) {{
        rateValue.innerText = val;
        localStorage.setItem('speechRate', val);
    }}

    window.speechSynthesis.getVoices();

    const wordsList = {js_data};
    let currentIndex = 0;
    let isSpeakingAll = false;

    function speakNext() {{
        if (currentIndex >= wordsList.length || !isSpeakingAll) {{
            isSpeakingAll = false;
            return;
        }}
        
        const synth = window.speechSynthesis;
        const item = wordsList[currentIndex];
        const text = item["単語"] + "。。 " + item["単語の意味"];
        const utterance = new SpeechSynthesisUtterance(text);
        
        utterance.lang = 'ja-JP';
        utterance.rate = parseFloat(rateSlider.value);
        
        const voices = synth.getVoices();
        const jpVoices = voices.filter(v => v.lang.includes('ja'));
        if (jpVoices.length > 0) {{
            let selectedVoice = jpVoices.find(v => 
                v.name.includes('Google') || v.name.includes('Premium') || 
                v.name.includes('Siri') || v.name.includes('Kyoko') || v.name.includes('Nanami')
            );
            if (!selectedVoice) selectedVoice = jpVoices[0];
            utterance.voice = selectedVoice;
        }}
        
        utterance.onend = () => {{
            currentIndex++;
            if (isSpeakingAll) {{
                setTimeout(speakNext, 50); 
            }}
        }};
        
        synth.speak(utterance);
    }}

    function speakAll() {{
        const synth = window.speechSynthesis;
        const unlock = new SpeechSynthesisUtterance('');
        unlock.volume = 0;
        synth.speak(unlock);
        synth.cancel(); 
        currentIndex = 0;
        isSpeakingAll = true;
        setTimeout(speakNext, 300);
    }}
    
    function pauseSpeaking() {{
        window.speechSynthesis.pause();
    }}
    function resumeSpeaking() {{
        window.speechSynthesis.resume();
    }}
    function stopSpeaking() {{
        isSpeakingAll = false;
        window.speechSynthesis.cancel();
    }}
    </script>
    """
    components.html(js_code, height=90)


# ==========================================
# アプリ本体
# ==========================================
@st.cache_data
def load_data():
    return pd.read_excel("Basic_Theory_Glossary.xlsx") 

try:
    df = load_data()
except FileNotFoundError:
    st.error("エクセルファイルが見つかりません。")
    st.stop()

# --- サイドバーの設定 ---
st.sidebar.header("🔍 絞り込み条件")
major_categories = ["すべて"] + list(df["大分類"].unique())
selected_major = st.sidebar.selectbox("大分類を選択", major_categories)

if selected_major != "すべて":
    filtered_df = df[df["大分類"] == selected_major]
else:
    filtered_df = df

minor_categories = ["すべて"] + list(filtered_df["小分類"].unique())
selected_minor = st.sidebar.selectbox("小分類を選択", minor_categories)

if selected_minor != "すべて":
    filtered_df = filtered_df[filtered_df["小分類"] == selected_minor]

st.sidebar.write(f"**現在の対象単語数: {len(filtered_df)}件**")


# --- メイン画面 ---
st.write("") 
mode = st.radio(
    "画面を切り替える", 
    ["📋 単語カード（一覧）", "🎯 ランダムテスト"], 
    horizontal=True, 
    label_visibility="collapsed"
)

# ------------------------------------------
# 画面1：単語カード一覧
# ------------------------------------------
if mode == "📋 単語カード（一覧）":
    search_query = st.text_input("単語名で検索（キーワード入力）")
    display_df = filtered_df
    
    if search_query:
        display_df = display_df[display_df["単語"].str.contains(search_query, na=False)]
    
    if len(display_df) > 0:
        st.write("---")
        tts_all_button(display_df)
        st.write("---")
        
    seen_df = get_seen_data()
    if not seen_df.empty:
        display_df = display_df.merge(seen_df, how="left", left_on="単語", right_on="word")
        display_df['count'] = display_df['count'].fillna(0).astype(int)
        for i in range(1, 6):
            display_df[f'date{i}'] = display_df[f'date{i}'].fillna("")
    else:
        display_df['count'] = 0
        for i in range(1, 6):
            display_df[f'date{i}'] = ""

    # ★CSSにタグ用の設定（.word-tags）を追加
    st.markdown("""
    <style>
    .word-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 6px solid #4CAF50;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .word-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .word-title-container {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        margin-bottom: 8px;
        gap: 8px;
    }
    .word-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
    }
    .word-tags {
        font-size: 0.85rem;
        color: #95a5a6; /* 薄い灰色 */
        font-weight: normal;
    }
    .word-meaning {
        font-size: 1.05rem;
        color: #34495e;
        margin-bottom: 15px;
        line-height: 1.6;
    }
    .word-meta {
        font-size: 0.9rem;
        color: #7f8c8d;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px dashed #ecf0f1;
        padding-top: 10px;
    }
    .star-rating {
        color: #f39c12;
        font-size: 1.1rem;
        letter-spacing: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1単語ずつカード状にして表示
    for _, row in display_df.iterrows():
        word = row['単語']
        meaning = row['単語の意味']
        major = row['大分類']
        minor = row['小分類']
        count = int(row['count'])
        
        stars = "★" * count + "☆" * (5 - count)
        dates = [str(row[f'date{i}']) for i in range(1, 6) if str(row[f'date{i}']).strip() != ""]
        date_str = f"🕒 最終確認: {dates[-1]}" if dates else "🕒 未学習"
        
        # ★タイトルの横に「#大分類 #小分類」を埋め込むHTMLに変更
        card_html = f"""
        <div class="word-card">
            <div class="word-title-container">
                <span class="word-title">✨ {word}</span>
                <span class="word-tags">#{major} #{minor}</span>
            </div>
            <div class="word-meaning">{meaning}</div>
            <div class="word-meta">
                <span><span class="star-rating">{stars}</span> ({count}/5)</span>
                <span>{date_str}</span>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)


# ------------------------------------------
# 画面2：ランダムテストと「見た」チェック機能
# ------------------------------------------
elif mode == "🎯 ランダムテスト":
    st.subheader("フラッシュカードテスト")
    st.write("ランダムに出題されます。学習が終わったら「見た」にチェックを入れましょう。")
    
    if "current_word" not in st.session_state:
        st.session_state.current_word = None
    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False

    if st.button("🎲 新しい単語をランダムに出題"):
        if len(filtered_df) > 0:
            st.session_state.current_word = filtered_df.sample(1).iloc[0]
            st.session_state.show_answer = False 
        else:
            st.warning("対象となる単語がありません。")

    if st.session_state.current_word is not None:
        current = st.session_state.current_word['単語']
        st.markdown("---")
        st.markdown("### ❓ 単語")
        st.info(f"**{current}**")
        
        if not st.session_state.show_answer:
            if st.button("👀 答えを見る"):
                st.session_state.show_answer = True
                st.rerun() 
                
        if st.session_state.show_answer:
            st.markdown("### 💡 意味")
            st.success(st.session_state.current_word['単語の意味'])
            
            tts_button(current, st.session_state.current_word['単語の意味'])
            
            st.write("---")
            conn = sqlite3.connect("words.db")
            c = conn.cursor()
            c.execute("SELECT count, date1, date2, date3, date4, date5 FROM seen_records WHERE word=?", (current,))
            row = c.fetchone()
            conn.close()
            
            count = row[0] if row else 0
            
            stars = "★" * count + "☆" * (5 - count)
            st.write(f"**☑️ 現在の習熟度: <span style='color:#f39c12; font-size:1.2rem;'>{stars}</span> ({count}/5回)**", unsafe_allow_html=True)
            
            if row and count > 0:
                dates = [d for d in row[1:] if d]
                st.caption("チェック履歴: " + " / ".join(dates))
                
            if count < 5:
                if st.button("✅ この単語を「見た」に記録する"):
                    mark_as_seen(current)
                    st.rerun() 
            else:
                st.success("🎉 この単語は既に5回チェック済みです（マスターしました！）")