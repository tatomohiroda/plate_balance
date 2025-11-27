# app.py (デザイン付き軽量版)

import sys
from pathlib import Path
from datetime import date
import re
import streamlit as st
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


# ---------------------------
#  💅 カスタムデザイン
# ---------------------------
def set_custom_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;600;800&display=swap');

        html, body, [data-testid="stAppViewContainer"] {
            background: #fff7f1;
            font-family: 'M PLUS Rounded 1c', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        [data-testid="stAppViewContainer"] > .main {
            max-width: 780px;
            margin: 0 auto;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            font-weight: 800 !important;
            letter-spacing: 0.03em;
        }

        h1 {
            font-size: 2.3rem !important;
        }

        .block-container {
            padding-top: 1.5rem;
        }

        /* expander（「候補から食材をえらぶ」など） */
        [data-testid="stExpander"] {
            border-radius: 1rem;
            border: 1px solid #f0d9cf;
            background: #fffdfb;
        }

        [data-testid="stExpander"] > div {
            padding: 0.4rem 0.8rem 0.8rem 0.8rem;
        }

        /* 入力欄・セレクトボックス */
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stNumberInput input {
            border-radius: 0.9rem !important;
            border: 1px solid #f2cfc5 !important;
            background-color: #fffaf7 !important;
        }

        /* メインボタン */
        .stButton > button[kind="primary"] {
            border-radius: 999px;
            background: linear-gradient(135deg, #ff9aa2, #ffb7b2);
            color: white;
            border: none;
            padding: 0.5rem 1.6rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            box-shadow: 0 8px 14px rgba(255, 150, 150, 0.35);
        }

        .stButton > button[kind="primary"]:hover {
            filter: brightness(1.03);
            transform: translateY(-1px);
            box-shadow: 0 10px 18px rgba(255, 150, 150, 0.45);
        }

        /* 他のボタンも少し丸く */
        .stButton > button:not([kind="primary"]) {
            border-radius: 999px;
        }

        /* metric（合計カロリーなど） */
        [data-testid="stMetric"] {
            padding: 0.8rem 1rem;
            border-radius: 1.2rem;
            background: #fffdfb;
            box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        }

        [data-testid="stMetricValue"] {
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------
#  foods.csv を読み込む
# ---------------------------
@st.cache_data
def load_foods():
    csv_path = BASE_DIR / "foods.csv"
    return pd.read_csv(csv_path)


# ---------------------------
#  食材検索
# ---------------------------
def search_foods(query: str, df: pd.DataFrame, limit: int = 20):
    """食品名で部分一致検索"""
    if not query:
        return df.head(limit)

    q = query.strip()
    if q == "":
        return df.head(limit)

    hit = df[
        df["name"].str.contains(q, case=False, na=False)
        | df["kana"].str.contains(q, case=False, na=False)
    ]
    return hit.head(limit)


# ---------------------------
#  自由入力（例：さつまいも 130g）
# ---------------------------
def parse_free_text(text: str, df: pd.DataFrame):
    """
    テキストをパースして [{'name': 食品名, 'grams': g}, ...] にする
    """
    lines = text.split("\n")
    results = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 例：「さつまいも 130g」
        m = re.search(r"(.+?)\s*([0-9]+)\s*g", line)
        if not m:
            continue

        name_part = m.group(1).strip()
        grams = float(m.group(2))

        # 名前の部分一致で食品を取得
        candidates = df[df["name"].str.contains(name_part, na=False)]
        if candidates.empty:
            continue

        row = candidates.iloc[0]
        results.append({"name": row["name"], "grams": grams})

    return results


# ---------------------------
#  栄養計算
# ---------------------------
def compute_nutrients(items, df: pd.DataFrame):
    """
    items: [{'name': 食材名, 'grams': g}, ...]
    df: foods.csv の DataFrame
    """
    total = {
        "kcal": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbs": 0.0,
        "fiber": 0.0,
        "vitA": 0.0,
        "vitB1": 0.0,
        "vitB2": 0.0,
        "vitC": 0.0,
    }

    details = []

    for item in items:
        name = item["name"]
        grams = item["grams"]

        row = df[df["name"] == name].iloc[0]

        # foods.csv の per(=100g) に対して、入力された g で比率を出す
        ratio = grams / row["per"]

        kcal = row["energy_kcal"] * ratio
        protein = row["protein_g"] * ratio
        fat = row["fat_g"] * ratio
        carbs = row["carbs_g"] * ratio
        fiber = row["fiber_g"] * ratio
        vitA = row["vitA_ug"] * ratio
        vitB1 = row["vitB1_mg"] * ratio
        vitB2 = row["vitB2_mg"] * ratio
        vitC = row["vitC_mg"] * ratio

        # 1品分の計算結果
        details.append(
            {
                "name": name,
                "grams": grams,
                "kcal": kcal,
                "protein": protein,
                "fat": fat,
                "carbs": carbs,
                "fiber": fiber,
                "vitA": vitA,
                "vitB1": vitB1,
                "vitB2": vitB2,
                "vitC": vitC,
            }
        )

        # 合計に追加
        total["kcal"] += kcal
        total["protein"] += protein
        total["fat"] += fat
        total["carbs"] += carbs
        total["fiber"] += fiber
        total["vitA"] += vitA
        total["vitB1"] += vitB1
        total["vitB2"] += vitB2
        total["vitC"] += vitC

    return total, details


# ---------------------------
#  セッション状態の管理
# ---------------------------
def init_session_state():
    if "selected_items" not in st.session_state:
        st.session_state["selected_items"] = []


def add_selected_item(name: str, grams: float):
    st.session_state["selected_items"].append({"name": name, "grams": grams})


def clear_selected_items():
    st.session_state["selected_items"] = []


# ---------------------------
#  Streamlit アプリ本体（UI）
# ---------------------------
def main():
    st.set_page_config(
        page_title="Plate Balance（基礎版）",
        page_icon="🍽",
        layout="centered",
    )

    # 💅 デザイン反映
    set_custom_style()

    init_session_state()
    foods_df = load_foods()

    # タイトル周りをちょっと可愛く
    st.markdown("### Plate Balance（基礎版） 🍽")
    st.markdown(
        "<div style='color:#8c6b63; font-size:0.95rem; margin-bottom:0.8rem;'>"
        "自炊ごはんの栄養バランスを、ふんわり見える化するミニアプリ"
        "</div>",
        unsafe_allow_html=True,
    )

    # 日付 & 食事区分
    col1, col2 = st.columns(2)
    with col1:
        dt = st.date_input("日付をえらぶ", value=date.today())
    with col2:
        meal_type = st.selectbox(
            "どのごはん？",
            ["朝ごはん", "昼ごはん", "夜ごはん", "間食"],
        )

    st.markdown("---")

    # =========================
    # 🍙 食材追加エリア
    # =========================
    st.subheader("🍙 食材を追加する")

    # ---- 検索して追加 ----
    with st.expander("候補から食材をえらぶ", expanded=True):
        query = st.text_input("食材名で検索（例：さつまいも）", key="search_query")
        candidates = search_foods(query, foods_df, limit=30)

        food_name = st.selectbox(
            "候補",
            ["（えらばない）"] + list(candidates["name"].values),
            key="selected_name",
        )
        grams = st.number_input(
            "量（g）",
            min_value=0.0,
            max_value=3000.0,
            value=100.0,
            step=10.0,
            key="selected_grams",
        )

        if st.button("この食材を追加", type="primary"):
            if food_name != "（えらばない）" and grams > 0:
                add_selected_item(food_name, grams)
                st.success(f"{food_name} を {grams} g 追加しました")
            else:
                st.warning("食材と量を確認してね")

    # ---- 自由入力から追加 ----
    with st.expander("自由入力（例：さつまいも 130g）"):
        free_text = st.text_area(
            "1行に1品ずつ書いてね（今は g 表記だけ対応中）",
            height=120,
            key="free_text",
        )
        if st.button("自由入力から追加"):
            items = parse_free_text(free_text, foods_df)
            if not items:
                st.warning(
                    "読み取れた食材がありませんでした（g表記になっているか確認してね）"
                )
            else:
                for item in items:
                    add_selected_item(item["name"], item["grams"])
                st.success(f"{len(items)} 件の食材を追加しました")

    st.markdown("---")

    # =========================
    # 🧾 今日の食材リスト
    # =========================
    st.subheader("🧾 今日の食材リスト")

    if not st.session_state["selected_items"]:
        st.info("まだ食材が追加されていません。上から追加してみてね。")
    else:
        for i, item in enumerate(st.session_state["selected_items"], start=1):
            st.write(f"{i}. {item['name']} ・・・ {item['grams']} g")

        if st.button("リストをクリアする"):
            clear_selected_items()
            st.success("リストを空にしました")

    st.markdown("---")

    # =========================
    # 📊 栄養計算
    # =========================
    st.subheader("📊 栄養バランスを見る")

    if st.button("栄養を計算する", type="primary"):
        if not st.session_state["selected_items"]:
            st.warning("先に食材を追加してね")
        else:
            total, details = compute_nutrients(
                st.session_state["selected_items"], foods_df
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric("合計カロリー", f"{round(total['kcal'])} kcal")
                st.write(
                    f"タンパク質: {round(total['protein'], 1)} g\n\n"
                    f"脂質: {round(total['fat'], 1)} g\n\n"
                    f"炭水化物: {round(total['carbs'], 1)} g"
                )
            with col2:
                st.write(
                    f"食物繊維: {round(total['fiber'], 1)} g\n\n"
                    f"VitA: {round(total['vitA'], 0)} µg\n\n"
                    f"B1: {round(total['vitB1'], 2)} mg\n\n"
                    f"B2: {round(total['vitB2'], 2)} mg\n\n"
                    f"VitC: {round(total['vitC'], 0)} mg"
                )

            # 食材ごとの詳細
            st.markdown("#### 食材ごとの内訳")
            for d in details:
                st.write(
                    f"- {d['name']} {d['grams']} g → "
                    f"{round(d['kcal'])} kcal / "
                    f"P {round(d['protein'],1)} / "
                    f"F {round(d['fat'],1)} / "
                    f"C {round(d['carbs'],1)}"
                )


# ---------------------------
#  アプリ起動
# ---------------------------
if __name__ == "__main__":
    main()
