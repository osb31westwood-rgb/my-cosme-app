import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import qrcode
from io import BytesIO

# --- 1. 基本設定 ---
st.set_page_config(page_title="CosmeInsight Pro", layout="wide")

COLUMN_CONFIG = {
    "スキンケア商品（フェイスケア・ボディケア）": {
        "item_col": "今回ご使用の商品名を入力してください。",
        "type_col": "スキンケア商品を選択した方は種類を選択してください。",
        "concern_col": "肌のお悩み（※複数選択可）",
        "scores": ["肌なじみ・透明感", "しっとり感", "さらっと感", "肌への負担感のなさ・優しさ", "香りの好み", "パッケージのときめき・使いやすさ", "リピート欲・おすすめ度"]
    },
    "ヘアケア商品": {
        "item_col": "今回ご使用の商品名を入力してください。.1",
        "type_col": "ヘアケア商品を選択した方は種類を選択してください。",
        "concern_col": "髪のお悩み（※複数選択可）",
        "scores": ["指通り・まとまり", "ツヤ感", "地肌への刺激・洗い心地", "ダメージ補修・翌朝の髪の状態", "香りの好み", "パッケージのときめき・使いやすさ", "リピート欲・おすすめ度"]
    }
}

# --- 2. データ読み込み ---
@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT5HpURwDWt6S0KkQbiS8ugZksNm8yTokNeKE4X-oBHmLMubOvOKIsuU4q6_onLta2cd0brCBQc-cHA/pub?gid=1578087772&single=true&output=csv"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return None

df = load_data()

# --- 3. メインUI ---
st.sidebar.title("💄 Cosme Management")
# ★重要：ここに「AIポップ生成」を追加しました
menu = st.sidebar.radio("機能を選択", ["QR生成", "レーダーチャート比較", "分布図分析", "AIポップ生成"])

# --- 4. 各メニューの処理 ---

# (1) QR生成
if menu == "QR生成":
    st.header("🔗 商品別QRコード作成")
    target_genre = st.selectbox("ジャンル", list(COLUMN_CONFIG.keys()))
    prod_name = st.text_input("商品名を手入力")
    
    if st.button("QRコード発行"):
        base_url = "https://docs.google.com/forms/d/e/XXXXX/viewform?usp=pp_url&entry.111=" + prod_name
        qr = qrcode.make(base_url)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf, caption=f"{prod_name} 専用QR")
        st.download_button("画像を保存", buf.getvalue(), "qr.png")

# (2) レーダーチャート
elif menu == "レーダーチャート比較":
    st.header("📊 スパイダーチャート分析")
    if df is not None:
        genre = st.selectbox("分析ジャンル", list(COLUMN_CONFIG.keys()))
        conf = COLUMN_CONFIG[genre]
        sub_df = df[df["今回ご使用の商品のジャンルを選択してください。"] == genre].copy()
        
        analysis_mode = st.radio("分析軸を選んでください", ["商品ごとに比較", "年代別に比較", "お悩み別に比較"])

        if analysis_mode == "商品ごとに比較":
            items = sub_df[conf["item_col"]].unique()
            selected_items = st.multiselect("商品を選択", items)
            if selected_items:
                fig = go.Figure()
                for item in selected_items:
                    item_data = sub_df[sub_df[conf["item_col"]] == item][conf["scores"]].mean()
                    fig.add_trace(go.Scatterpolar(r=item_data.values, theta=conf["scores"], fill='toself', name=item))
                st.plotly_chart(fig, use_container_width=True)

        elif analysis_mode == "年代別に比較":
            item_name = st.selectbox("分析したい商品を選択", sub_df[conf["item_col"]].unique())
            target_df = sub_df[sub_df[conf["item_col"]] == item_name]
            available_ages = sorted(target_df["年齢"].unique())
            selected_ages = st.multiselect("比較する年代を選択", available_ages, default=available_ages)
            
            fig = go.Figure()
            for age in selected_ages:
                age_data = target_df[target_df["年齢"] == age][conf["scores"]].mean()
                fig.add_trace(go.Scatterpolar(r=age_data.values, theta=conf["scores"], fill='toself', name=f"{age}"))
            st.plotly_chart(fig, use_container_width=True)

        elif analysis_mode == "お悩み別に比較":
            item_name = st.selectbox("分析したい商品を選択", sub_df[conf["item_col"]].unique())
            target_df = sub_df[sub_df[conf["item_col"]] == item_name]
            concern_col = conf["concern_col"]
            all_concerns = []
            for c in target_df[concern_col].dropna():
                all_concerns.extend([x.strip() for x in str(c).split(',')])
            unique_concerns = sorted(list(set(all_concerns)))
            selected_concerns = st.multiselect("比較するお悩みを選択", unique_concerns)
            
            if selected_concerns:
                fig = go.Figure()
                for concern in selected_concerns:
                    concern_df = target_df[target_df[concern_col].str.contains(concern, na=False)]
                    concern_data = concern_df[conf["scores"]].mean()
                    fig.add_trace(go.Scatterpolar(r=concern_data.values, theta=conf["scores"], fill='toself', name=f"悩み：{concern}"))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("データが読み込めていません。")

# (3) 分布図
elif menu == "分布図分析":
    st.header("📈 お悩み×満足度の分布")
    if df is not None:
        genre = st.selectbox("分析ジャンル", list(COLUMN_CONFIG.keys()))
        conf = COLUMN_CONFIG[genre]
        sub_df = df[df["今回ご使用の商品のジャンルを選択してください。"] == genre]
        x_axis = st.selectbox("横軸（項目）", conf["scores"], index=0)
        y_axis = st.selectbox("縦軸（項目）", conf["scores"], index=len(conf["scores"])-1)
        fig = px.scatter(sub_df, x=x_axis, y=y_axis, color="年齢", hover_name=conf["item_col"])
        st.plotly_chart(fig, use_container_width=True)

# (4) AIポップ生成
elif menu == "AIポップ生成":
    st.header("📝 AI商品ポップ提案")
    if df is not None:
        genre = st.selectbox("ジャンル", list(COLUMN_CONFIG.keys()), key="pop_genre")
        conf = COLUMN_CONFIG[genre]
        sub_df = df[df["今回ご使用の商品のジャンルを選択してください。"] == genre]
        item_name = st.selectbox("ポップを作りたい商品", sub_df[conf["item_col"]].unique())
        item_stats = sub_df[sub_df[conf["item_col"]] == item_name][conf["scores"]].mean()
        best_feature = item_stats.idxmax()
        
        st.subheader(f"🔍 {item_name} の分析結果")
        st.write(f"この商品の最大の強みは **「{best_feature}」** です！")
        tone = st.select_slider("雰囲気", options=["信頼感（プロ風）", "親しみやすい", "おしゃれ・エモい", "インパクト重視"])
        
        if st.button("キャッチコピー案を生成"):
            if tone == "信頼感（プロ風）":
                st.info(f"【案】データが証明する実力。{best_feature}に妥協したくないあなたへ。")
            elif tone == "親しみやすい":
                st.success(f"【案】スタッフも驚いた！{item_name}で毎日がもっと楽しくなる。")
            elif tone == "おしゃれ・エモい":
                st.warning(f"【案】光を味方に。{best_feature}が導く、新しい私。")
            else:
                st.error(f"【案】リピート確定！？この「{best_feature}」は事件です。")

# (5) 最終エラーハンドリング
else:
    st.warning("メニューを選択してください。")