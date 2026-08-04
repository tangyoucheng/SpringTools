
# ==================== 1. Oracle 19c 接続設定 ====================
# SQLAlchemy 形式の接続文字列 (URL) を作成します
# 形式: oracle+oracledb://ユーザー名:パスワード@ホスト名:ポート番号/サービス名
# 移行前（旧）データベース接続情報
#URL_OLD = "oracle+oracledb://old_user:old_password@old_host:1521/old_service_name"
# 移行後（新）データベース接続情報
#URL_NEW = "oracle+oracledb://new_user:new_password@new_host:1521/new_service_name"

# SQLAlchemy の Engine オブジェクトを作成（これで UserWarning が完全に消えます）
engine_old = create_engine(URL_OLD)
engine_new = create_engine(URL_NEW)
