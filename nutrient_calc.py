import pandas as pd
import re
import unicodedata


# =================================================
# 📌 食材データ読み込み
# =================================================
def load_foods(csv_path):
    df = pd.read_csv(csv_path)
    return df


# =================================================
# 📌 食材検索
# =================================================
def search_foods(query: str, foods_df, limit: int = 10):
    if not query:
        return foods_df.head(limit)

    # 部分一致（大文字小文字区別なし）
    mask = foods_df["name"].str.contains(query, case=False, na=False)
    results = foods_df[mask]

    if results.empty:
        # 何もヒットしない場合 → 全体から上位 N 件返す
        return foods_df.head(limit)

    return results.head(limit)


# =================================================
# 📌 自由入力 さつまいも130 などを解析
# =================================================
def parse_free_text(text: str, foods_df, max_candidate: int = 10):
    results = []

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return results

    # 食材名 + 数値 + g（g省略可）
    pattern = re.compile(r"^(?P<name>.+?)(?P<amount>\d+(?:\.\d+)?)\s*(?:g|グラム)?$")

    for line in lines:
        norm = unicodedata.normalize("NFKC", line)
        m = pattern.search(norm)
        if not m:
            continue

        raw_name = m.group("name").strip()
        grams = float(m.group("amount"))

        # 食材名マッチング
        candidates = search_foods(raw_name, foods_df, limit=max_candidate)
        if candidates is None or candidates.empty:
            continue

        matched = candidates.iloc[0]["name"]

        results.append({
            "name": matched,
            "grams": grams
        })

    return results


# =================================================
# 📌 栄養計算
# =================================================
def compute_nutrients(items, foods_df):
    total = {
        "kcal": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "fiber": 0,
        "vitA": 0,
        "vitB1": 0,
        "vitB2": 0,
        "vitC": 0,
    }

    details = []

    for item in items:
        name = item["name"]
        grams = item["grams"]

        row = foods_df[foods_df["name"] == name].iloc[0]
        ratio = grams / 100.0

        d = {
            "name": name,
            "grams": grams,
            "kcal": row["kcal"] * ratio,
            "protein": row["protein"] * ratio,
            "fat": row["fat"] * ratio,
            "carbs": row["carbs"] * ratio,
            "fiber": row["fiber"] * ratio,
            "vitA": row["vitA"] * ratio,
            "vitB1": row["vitB1"] * ratio,
            "vitB2": row["vitB2"] * ratio,
            "vitC": row["vitC"] * ratio,
        }

        details.append(d)

        # 合計値
        total["kcal"] += d["kcal"]
        total["protein"] += d["protein"]
        total["fat"] += d["fat"]
        total["carbs"] += d["carbs"]
        total["fiber"] += d["fiber"]
        total["vitA"] += d["vitA"]
        total["vitB1"] += d["vitB1"]
        total["vitB2"] += d["vitB2"]
        total["vitC"] += d["vitC"]

    return total, details
