# generate_foods_csv.py
import os
import re
import pandas as pd

# ★ Excelファイル名（拡張子まで完全一致させる）
SRC_FILE = "20201225-mxt_kagsei-mext_01110_012.xlsx"
OUT_FILE = "foods.csv"


def parse_val(v):
    """
    成分表の値を float に変換する。
    'Tr' や '(40.5)' みたいな表記にも対応。
    """
    if pd.isna(v):
        return 0.0
    s = str(v).strip()
    if s in ("-", ""):
        return 0.0

    # Tr（微量）はとりあえず 0 とみなす
    s = s.replace("Tr", "0").replace("tr", "0")

    # カッコでくくられている値はカッコを外す
    s = s.replace("(", "").replace(")", "")

    # 数字・小数点・マイナス以外を全部削除
    s2 = re.sub(r"[^0-9.\-]", "", s)
    if s2 == "" or s2 == ".":
        return 0.0

    try:
        return float(s2)
    except ValueError:
        return 0.0


def main():
    # デバッグ用に状況を表示
    print("cwd:", os.getcwd())
    print("files in cwd:", os.listdir("."))
    print("SRC_FILE:", SRC_FILE)

    if not os.path.exists(SRC_FILE):
        print("❌ Excelファイルが見つかりません。ファイル名をもう一度確認してね。")
        return

    # このExcelの「表全体」シートは、
    # 12 行目（0始まりで 11）が成分識別子の行なので header=11 を指定
    df = pd.read_excel(SRC_FILE, sheet_name="表全体", header=11)

    # 成分識別子の列が食品名になっているので、それを name として使う
    name_col = "成分識別子"

    # 各栄養素の列名（このファイルで実際に入っていたやつ）
    col_map_src = {
        "energy_kcal": "ENERC_KCAL",  # エネルギー kcal
        "protein_g": "PROT-",         # たんぱく質
        "fat_g": "FAT-",              # 脂質
        "carbs_g": "CHOAVL",          # 利用可能炭水化物
        "fiber_g": "FIB-",            # 食物繊維
        "vitA_ug": "VITA_RAE",        # ビタミンA
        "vitC_mg": "VITC",            # ビタミンC
    }

    data = {
        "name": df[name_col],
        "kana": df[name_col],  # とりあえず同じ
        "per": 100,            # 可食部100gあたり
    }

    for new_col, src_col in col_map_src.items():
        if src_col in df.columns:
            data[new_col] = df[src_col].map(parse_val)
        else:
            print(f"⚠ 列が見つからないので 0 埋め: {src_col}")
            data[new_col] = 0.0

    # この版の表には VITB1 / VITB2 が無いので、とりあえず 0
    data["vitB1_mg"] = 0.0
    data["vitB2_mg"] = 0.0

    out_df = pd.DataFrame(
        data,
        columns=[
            "name",
            "kana",
            "per",
            "energy_kcal",
            "protein_g",
            "fat_g",
            "carbs_g",
            "fiber_g",
            "vitA_ug",
            "vitB1_mg",
            "vitB2_mg",
            "vitC_mg",
        ],
    )

    out_df.to_csv(OUT_FILE, index=False, encoding="utf-8")
    print(f"✅ {OUT_FILE} を出力しました（{len(out_df)} 行）")


if __name__ == "__main__":
    main()
