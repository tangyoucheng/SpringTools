
import pandas as pd
import oracledb
import math
from sqlalchemy import create_engine, text

# ==================== 2. Oracleデータ型・長さ・漢字コメントの取得 ====================
def get_oracle_meta(engine, table_name):
    query = text("""
        SELECT 
            tc.COLUMN_NAME, 
            tc.DATA_TYPE, 
            tc.DATA_LENGTH, 
            tc.DATA_PRECISION, 
            tc.DATA_SCALE, 
            cc.COMMENTS,
            CASE 
              WHEN tc.DATA_TYPE LIKE 'TIMESTAMP%' THEN tc.DATA_SCALE
              ELSE NULL 
            END AS TIMESTAMP_SCALE
        FROM USER_TAB_COLUMNS tc
        LEFT JOIN USER_COL_COMMENTS cc 
          ON tc.TABLE_NAME = cc.TABLE_NAME AND tc.COLUMN_NAME = cc.COLUMN_NAME
        WHERE tc.TABLE_NAME = :table_name
        ORDER BY tc.COLUMN_ID
    """)
    
    type_dict = {}
    comment_dict = {}
    
    with engine.connect() as conn:
        result = conn.execute(query, {"table_name": table_name})
        for row in result:
            col, dtype, dlen, dprec, dscale, comments, ts_scale = row
            
            # 漢字名（コメント）が空の場合は英文名をそのまま入れる
            comment_dict[col] = comments if (comments is not None and comments.strip() != "") else col
            
            if dtype in ("VARCHAR2", "CHAR", "NVARCHAR2", "NCHAR"):
                type_str = f"{dtype}({dlen})"
            elif dtype == "NUMBER":
                if dprec is not None and dscale is not None and dscale > 0:
                    type_str = f"NUMBER({dprec},{dscale})"
                elif dprec is not None:
                    type_str = f"NUMBER({dprec})"
                else:
                    type_str = "NUMBER"
            elif dtype == "DATE":
                type_str = "DATE"
            elif "TIMESTAMP" in dtype:
                if ts_scale is not None:
                    if "WITH TIME ZONE" in dtype:
                        type_str = f"TIMESTAMP({ts_scale}) WITH TIME ZONE"
                    elif "WITH LOCAL TIME ZONE" in dtype:
                        type_str = f"TIMESTAMP({ts_scale}) WITH LOCAL TIME ZONE"
                    else:
                        type_str = f"TIMESTAMP({ts_scale})"
                else:
                    type_str = dtype
            else:
                type_str = dtype
            type_dict[col] = type_str
            
    return type_dict, comment_dict
