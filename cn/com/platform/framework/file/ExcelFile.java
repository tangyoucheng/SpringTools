package cn.com.platform.framework.file;

import java.text.SimpleDateFormat;

/**
 * エクセルファイル操作。
 * 
 * @author 唐友成
 * @since 2017年11月22日
 */
public abstract class ExcelFile {

  /* データ取得タイプ（ReadExcelComで使用） */
  public static final String DATA_GET_TYPE_STRING = "0"; // 文字
  public static final String DATA_GET_TYPE_LABEL = "1"; // ラベル
  public static final String DATA_GET_TYPE_NUMBER = "2"; // 数値
  public static final String DATA_GET_TYPE_BOOLEAN = "3"; // BOOL
  public static final String DATA_GET_TYPE_DATE = "4"; // 日付
  public static final String DATA_GET_TYPE_DECIMAL = "5"; // 数値(小数点有り)

  /* データ取得タイプ（MakeExcelComで使用するで使用） */
  public static final String DATA_SET_TYPE_STRING = "1"; // 文字
  public static final String DATA_SET_TYPE_NUMBER = "2"; // 数値
  public static final String DATA_SET_DATE = "3"; // 日付

  /* Excelのセル参照方式変換用（A1形式→R1C1形式、R1C1形式→A1形式を行う際に使用） */
  public static final int CONVERT_CD_TO_ALPHABET = 26; // 英字変換用
  public static final int CONVERT_CD_TO_NUMBER_STRING = 64; // 数字文字列変換用

  /* コピー方式（コピーの際、コピー先の行指定が相対か絶対か） */
  public static final String COPY_TARGET_ABUSOLUTE = "1"; // 絶対位置
  public static final String COPY_TARGET_RELATIVE = "0"; // 相対位置

  /* コピー方式（コピーの際、セルの値をコピーするか否か） */
  public static final String COPY_VALUE_COPY = "1"; // コピーする
  public static final String COPY_VALUE_UNCOPY = "0"; // コピーしない

  /* その他 */
  public static final String CELL_INNER_NEW_LINE_CHAR = "\n"; // セル内改行

  /* 書式情報 */
  private String strDefaultDateFormat = new SimpleDateFormat().toLocalizedPattern(); // 標準日付書式

  /**
   * ExcelFile を構築する。
   */
  public ExcelFile() {
    super();
  }

  /**
   * A1形式から行インデックスを取得する。
   * 
   * @param strA1 A1形式
   * @return 行インデックス
   */
  public int getRowIndex(String strA1) {

    // /1.nullの場合、-1
    if (strA1 == null) {
      return -1;
    }

    // /2.行文字列の取得
    String strRowString = strA1.replaceAll("[a-zA-Z]", "");

    // //2.1.取得できなかった場合、-1
    if (strRowString.length() == 0) {
      return -1;
    }

    // /3.行インデックスを返す
    return Integer.parseInt(strRowString) - 1;
  }

  /**
   * A1形式から列インデックスを取得する。
   * 
   * @param strA1 A1形式
   * @return 列インデックス
   */
  public int getColIndex(String strA1) {

    // / 1.nullの場合、-1
    if (strA1 == null) {
      return -1;
    }

    // / 2.英字部分を取得する
    String strColString = strA1.replaceAll("[0-9]", "");

    // / 3.取得した英字が1桁または2桁でない場合、-1
    if (strColString.length() <= 0 || strColString.length() > 2) {
      return -1;
    }

    char char1Data = 0; // 英字一桁目
    char char2Data = 0; // 英字二桁目
    // / 4.英字の文字コードを取得する
    // // 4.1.一桁目の英字の文字コードを取得する
    char1Data = strColString.charAt(0);
    char1Data -= CONVERT_CD_TO_NUMBER_STRING;

    // // 4.2.二桁目がある場合、二桁目の英字の文字コードを取得する
    if (strColString.length() >= 2) {
      char2Data = strColString.charAt(1);
      char2Data -= CONVERT_CD_TO_NUMBER_STRING;
    }

    // / 5.列インデックスを返す
    if (char2Data <= 0) {
      // // 5.1.一桁の場合
      return char1Data - 1;
    } else {
      // // 5.2.二桁の場合
      return char1Data * CONVERT_CD_TO_ALPHABET + char2Data - 1;
    }

  }

  /**
   * 行インデックス、列インデックスからRangeを取得する。
   * 
   * @param intRow 行インデックス
   * @param intCol 列インデックス
   * @return インデックス
   */
  public String getRange(int intRow, int intCol) {
    String strResult = "";

    // / 1.インデックスからA1形式の位置文字列を作成する
    if (intRow < 0 || intCol < 0) {
      return "";
    }

    // // 1.1.列文字列の作成
    int intBuf = intCol / CONVERT_CD_TO_ALPHABET;
    if (intBuf > 0) {
      strResult += String.valueOf((char) (CONVERT_CD_TO_NUMBER_STRING + intBuf));
    }

    intBuf = intCol % CONVERT_CD_TO_ALPHABET + 1;
    strResult += String.valueOf((char) (CONVERT_CD_TO_NUMBER_STRING + intBuf));

    // // 1.2.行文字列の作成
    strResult += String.valueOf(intRow + 1);

    // /2.作成した値を返す
    return strResult;

  }

  /**
   * 指定セル位置から指定した数移動した場所のセル位置を返す。
   * 
   * @param strRange セル位置
   * @param intRowMove 移動行数
   * @param intColMove 移動列数
   * @return インデックス
   */
  public String getRange(String strRange, int intRowMove, int intColMove) {

    // /1.インデックスを取得する
    int intRow = getRowIndex(strRange);
    int intCol = getColIndex(strRange);

    // /2.移動後のセル位置を取得する
    String strResult = getRange(intRow + intRowMove, intCol + intColMove);

    // /3.取得した値を返す
    return strResult;

  }

  /**
   * 標準日付書式を返します。
   * 
   * @return String 標準日付書式
   */
  public String getDefaultDateFormat() {
    return strDefaultDateFormat;
  }

  /**
   * 標準日付書式を設定します。
   * 
   * @param strDefaultDateFormat 標準日付書式
   */
  public void setDefaultDateFormat(String strDefaultDateFormat) {
    this.strDefaultDateFormat = strDefaultDateFormat;
  }

}
