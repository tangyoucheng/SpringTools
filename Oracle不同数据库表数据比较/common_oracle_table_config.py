
# ==================== ★ 比較対象の複数テーブル設定 ★ ====================
# ここに対象のテーブル、業務主キーのリストをすべて定義します。
# 何表あっても、ここに追記するだけで自動で順番に処理されます。
#
# 【重要】業務主キーを指定（単一、または複合主キーのリスト）
# 例1（単一カラム）: BUSINESS_PKS = ["ORDER_NO"]
# 例2（複合カラム）: BUSINESS_PKS = ["USER_ID", "PRODUCT_ID"]
TABLES_CONFIG = [
    {
        "TABLE_NAME": "TCMMSGINFO",
        "BUSINESS_PKS": ["SQSEQ"]
    },
    {
        "TABLE_NAME": "TCMMTHOJO",
        "BUSINESS_PKS": ["CDCMP", "KBMST", "CDCODE"]
    }
]
