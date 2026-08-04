
# ==================== ★ 比較対象の複数テーブル設定 ★ ====================
# ここに対象のテーブル、業務主キーのリストをすべて定義します。
# 何表あっても、ここに追記するだけで自動で順番に処理されます。
#
# 【重要】業務主キーを指定（単一、または複合主キーのリスト）
# 例1（単一カラム）: BUSINESS_PKS = ["ORDER_NO"]
# 例2（複合カラム）: BUSINESS_PKS = ["USER_ID", "PRODUCT_ID"]
#
# EXTRA_WHERE に比較したい特定の条件を SQL 形式で記述します。
# 条件がない場合は、"EXTRA_WHERE": None または空文字 "" にしてください。
TABLES_CONFIG = [
    {
        "TABLE_NAME": "TCMMSGINFO",
        "BUSINESS_PKS": ["SQSEQ"],
        "EXTRA_WHERE": "CDSOSINMOTOCMP = '00' AND DTUPD >= TO_DATE('2022-01-01', 'YYYY-MM-DD')",
    },
    {
        "TABLE_NAME": "TCMMTHOJO",
        "BUSINESS_PKS": ["CDCMP", "KBMST", "CDCODE"],
        "EXTRA_WHERE": "" ,
    },
    {
        "TABLE_NAME": "TCMMTHANYO",
        "BUSINESS_PKS": ["CDCMP", "KBMST", "CDCODE"],
        "EXTRA_WHERE": "CDCMP = '00'" ,
    },
]
