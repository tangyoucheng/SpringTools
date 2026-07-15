package cn.com.platform.framework.file;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.util.Date;
import org.apache.commons.lang3.StringUtils;
import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.DataFormat;
import org.apache.poi.ss.usermodel.DateUtil;
import org.apache.poi.ss.usermodel.FillPatternType;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.FormulaEvaluator;
import org.apache.poi.ss.usermodel.HorizontalAlignment;
import org.apache.poi.ss.usermodel.Name;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.util.AreaReference;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.ss.util.CellReference;
import org.apache.poi.xssf.streaming.SXSSFSheet;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.beans.BeanUtils;
import cn.com.platform.framework.common.exception.SystemException;
import cn.com.platform.framework.util.FwDateUtils;
import cn.com.platform.framework.util.FwNumberUtils;

/**
 * 大きなEXCELファイルクラス。
 * </p>
 * 大きなEXCELファイルを生成し作成を行う。
 * 
 * @author 唐友成
 * @since 2017年11月22日
 */
public class ExcelMakeSFile extends ExcelFile {

  /** ワークブック。 */
  public SXSSFWorkbook workbook;

  /** 英字変換用。 */
  static final int CONVERT_CD_TO_ALPHABET = 26;

  /** 数字文字列変換用。 */
  static final int CONVERT_CD_TO_NUMBER_STRING = 64;

  /**
   * ExcelMakeFile を構築する。
   * <p>
   * Excelのインスタンスを生成する
   * </p>
   */
  public ExcelMakeSFile() {
    super();

    workbook = null;

    // ブックを新規生成する。
    workbook = new SXSSFWorkbook();
  }

  /**
   * ExcelMakeFile を構築する。
   * <p>
   * フォーマットファイルを読み込みExcelのインスタンスを生成する。
   * </p>
   *
   * @param byteFile ファイルバイト配列
   * @throws IOException 読み込みでエラーが発生した場合スロー
   */
  public ExcelMakeSFile(byte[] byteFile) throws IOException {
    super();

    // 初期化を行う
    workbook = null;

    // 既存ファイルを読み込む
    ByteArrayInputStream instream = new ByteArrayInputStream(byteFile);

    // ブックを生成する
    workbook = new SXSSFWorkbook(new XSSFWorkbook(instream), 1000);

    // 不要オブジェクトを破棄する
    instream.close();
    instream = null;
  }

  /**
   * ExcelMakeFile を構築する。
   * <p>
   * フォーマットファイルを読み込みExcelのインスタンスを生成する
   * </p>
   *
   * @param inputStream インプットストリーム
   * @throws IOException 読み込みでエラーが発生した場合スロー
   */
  public ExcelMakeSFile(InputStream inputStream) throws IOException {
    super();

    // 初期化を行う
    workbook = null;

    // InputStreamにする
    ByteArrayInputStream infile = (ByteArrayInputStream) inputStream;

    // ブックを生成する
    workbook = new SXSSFWorkbook(new XSSFWorkbook(infile), 1000);

    // 不要オブジェクトを破棄する
    infile.close();
    infile = null;
  }

  /**
   * Excelファイルのバイト配列を返却する。
   *
   * @return byte[] ファイルのバイト配列
   * @throws IOException 読み込みでエラーが発生した場合スロー
   */
  public byte[] getBytes() throws IOException {

    // 出力ファイルオブジェクトを生成する
    ByteArrayOutputStream outstream = new ByteArrayOutputStream();

    // Excelファイルを生成する
    workbook.write(outstream);

    byte[] fileByte = outstream.toByteArray();
    outstream.close();

    // 不要オブジェクトを破棄する
    outstream = null;

    // バイト配列を返却する
    return fileByte;
  }

  /**
   * Excelファイルを作成する。
   *
   * @param strOutputPath ファイル出力パス
   * @return boolean true:出力成功 false:出力失敗
   * @throws IOException 読み込みでエラーが発生した場合スロー
   */
  public boolean outputFile(String strOutputPath) throws IOException {

    // 出力ファイルオブジェクトを生成する
    FileOutputStream outfile = new FileOutputStream(strOutputPath);

    // Excelファイルを出力する
    workbook.write(outfile);

    // 出力結果を設定する
    boolean blnResult = true;

    // 不要オブジェクトを破棄する
    outfile.close();
    outfile = null;

    // 出力結果を返却する
    return blnResult;
  }

  /**
   * 行のインスタンスを生成する。
   *
   * @param sheet シート
   * @param lngRowNo 行番号
   * @return 行インスタンス
   */
  private Row createRow(Sheet sheet, int lngRowNo) {

    // 生成した行のインスタンスを返却する
    return sheet.createRow(lngRowNo);
  }

  /**
   * セルのインスタンスを生成する。
   *
   * @param row 行
   * @param lngColumnNo 行番号
   * @return セルインスタンス
   */
  private Cell createCell(Row row, int lngColumnNo) {

    // 生成したセルのインスタンスを返却する
    return row.createCell(lngColumnNo);
  }

  /**
   * シートを取得する。
   *
   * @param strSheetName シート名
   * @return Sheet
   */
  private Sheet getSheet(String strSheetName) {

    // 生成したシートを返却する
    return workbook.getSheet(strSheetName);

  }

  /**
   * 行を取得する。
   *
   * @param sheet シート
   * @param strA1 A1形式のセル位置
   * @return Row
   */
  private Row getRow(Sheet sheet, String strA1) {
    // ローカル変数宣言 //
    Row row = null;
    int intRow = 0;

    // / 1.A1形式の文字列から行インデックスを取得する
    intRow = getRowIndex(strA1);

    // / 2.行番号から行を読み込む
    row = sheet.getRow(intRow);

    // / 3.行が存在しない場合
    if (row == null) {
      // // 3.1.行のインスタンスを生成する
      row = createRow(sheet, intRow);
    }

    // / 5.取得した行を返す
    return row;

  }

  /**
   * セルを取得する。
   *
   * @param sheet シート
   * @param strA1 A1形式のセル位置
   * @return Cell
   */
  public Cell getCell(Sheet sheet, String strA1) {
    // ローカル変数宣言 //
    Row row = null;
    Cell cell = null;
    int intCol = 0;

    // / 1.行を取得する
    row = getRow(sheet, strA1);

    // / 2.A1形式の文字列からカラムインデックスを取得する
    intCol = getColIndex(strA1);

    // / 3.セルを取得する
    cell = row.getCell(intCol);

    // / 4.セルが存在しない場合
    if (cell == null) {
      // // 4.1.セルのインスタンスを生成する
      cell = createCell(row, intCol);
    }

    // / 6.取得したセルを返す
    return cell;
  }

  /**
   * セルに値を設定する(String型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param strValue 設定する値
   * @param strExcelDataDiv EXCELデータ区分
   * @throws SystemException 异常的场合
   */
  public void setCellValue(String strSheetName, String strA1, String strValue,
      String strExcelDataDiv) throws SystemException {
    // ローカル変数宣言 //
    Date dteDate = null;
    String inputStrValue = StringUtils.defaultString(strValue);

    try {

      if (inputStrValue == null || inputStrValue.equals("")) {
        return;
      }

      /// 1.EXCELデータ区分により、処理分岐
      //// 1.2.文字列または値が空の場合
      if (strExcelDataDiv.equals(DATA_SET_TYPE_STRING) || inputStrValue == null
          || inputStrValue.equals("")) {
        ///// 1.2.1.文字列として出力
        setCellValue(strSheetName, strA1, inputStrValue);
      } else if (strExcelDataDiv.equals(DATA_SET_TYPE_NUMBER)) { //// 1.3.数値の場合
        ///// 1.3.1.数値に変換
        BigDecimal bdecValue = FwNumberUtils.toBigDecimal(inputStrValue);
        ///// 1.3.2.数値変換されたかどうかで処理分岐
        if (bdecValue != null) {
          ////// 1.3.2.1.数値変換が正常に行われた場合、数値を出力
          setCellValue(strSheetName, strA1, bdecValue);
        } else {
          ////// 1.3.2.2.数値変換に失敗した場合、文字列として出力
          setCellValue(strSheetName, strA1, inputStrValue);
        }
        bdecValue = null;
      } else if (strExcelDataDiv.equals(DATA_SET_DATE)) { //// 1.4.日付の場合
        ///// 1.4.1.日付に変換
        dteDate = FwDateUtils.parse(inputStrValue, strExcelDataDiv);
        ///// 1.4.2.日付変換されたかどうかで処理分岐
        if (dteDate != null) {
          ////// 1.4.2.1.日付変換が正常に行われた場合、日付数値を出力
          setCellValue(strSheetName, strA1, DateUtil.getExcelDate(dteDate));
        } else {
          ////// 1.4.2.2.日付変換に失敗した場合、文字列として出力
          setCellValue(strSheetName, strA1, inputStrValue);
        }
      }

      /// 2.例外が発生した場合
    } catch (Exception e1) {
      //// 2.1.その他の例外が発生した場合
      // 例外ログを出力する
      // LogCom.getInstance().logExceptionInfo(strMethodName, e.getMessage(), null);
      // 例外をスローする
      throw new SystemException(e1.getMessage(), e1);
    }

  }

  /**
   * セルに値を設定する(String型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param strValue 設定する値
   */
  public void setCellValue(String strSheetName, String strA1, String strValue) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル
    CellStyle style = null;

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルのエンコーディングを指定する
    // cell.setEncoding(Cell.ENCODING_UTF_16);

    // / 4.セル内改行を設定する
    if (strValue != null && strValue.indexOf(CELL_INNER_NEW_LINE_CHAR) > -1) {
      style = cell.getCellStyle();
      style.setWrapText(true);
      cell.setCellStyle(style);
    }

    // / 5.セルに値を設定する
    cell.setCellValue(strValue);

    // / 6.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
  }

  /**
   * セルに値を設定する(Date型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param dateValue 設定する値
   */
  public void setCellValue(String strSheetName, String strA1, Date dateValue) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルのエンコーディングを指定する
    // cell.setEncoding(Cell.ENCODING_UTF_16);

    // / 4.EXCEL日付を数値として取得する
    double excelDate = DateUtil.getExcelDate(dateValue);

    // / 5.セルに値を設定する
    cell.setCellValue(excelDate);

    // / 6.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
  }

  /**
   * セルに値を設定する(Date型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param dateValue 設定する値
   * @param strDateFormat 日付フォーマット
   */
  public void setCellValue(String strSheetName, String strA1, Date dateValue,
      String strDateFormat) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルのエンコーディングを指定する
    // cell.setEncoding(Cell.ENCODING_UTF_16);

    // / 4.セルの日付書式を設定する
    // // 4.1.対象セルの書式を取得する
    CellStyle cellStyle = null; // セル書式
    DataFormat format = null; // 日付書式
    cellStyle = cell.getCellStyle();
    format = workbook.createDataFormat();

    // // 4.2.任意の日付書式を設定する
    cellStyle.setDataFormat(format.getFormat(strDateFormat));
    cell.setCellStyle(cellStyle);

    // / 5.セルに値を設定する
    cell.setCellValue(dateValue);

    // / 6.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
    cellStyle = null;
    format = null;
  }

  /**
   * セルに値を設定する(long型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param lngValue 設定する値
   */
  public void setCellValue(String strSheetName, String strA1, long lngValue) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルのエンコーディングを指定する
    // cell.setEncoding(Cell.ENCODING_UTF_16);

    // / 4.セルに値を設定する
    cell.setCellValue(lngValue);

    // / 5.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
  }

  /**
   * セルに値を設定する(BigDecimal型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param dblValue 設定する値
   */
  public void setCellValue(String strSheetName, String strA1, double dblValue) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルのエンコーディングを指定する
    // cell.setEncoding(Cell.ENCODING_UTF_16);

    // / 4.セルに値を設定する
    cell.setCellValue(dblValue);

    // / 5.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
  }

  /**
   * セルに値を設定する(BigDecimal型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param bdecValue 設定する値
   */
  public void setCellValue(String strSheetName, String strA1, BigDecimal bdecValue) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルのエンコーディングを指定する
    // cell.setEncoding(Cell.ENCODING_UTF_16);

    // / 4.セルに値を設定する
    if (bdecValue != null) {
      if (bdecValue.compareTo(BigDecimal.ZERO) == 0) {
        cell.setCellValue("");
      } else {
        cell.setCellValue(bdecValue.doubleValue());
      }
    } else {
      cell.setCellValue("");
    }

    // / 5.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
  }

  /**
   * セルに数式を設定する。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @param strFormula 設定する数式
   */
  public void setCellFormula(String strSheetName, String strA1, String strFormula) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルのエンコーディングを指定する
    // cell.setEncoding(Cell.ENCODING_UTF_16);

    // / 4.セルに値を設定する
    cell.setCellFormula(null);
    cell.setCellFormula(strFormula);

    // / 5.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
  }

  /**
   * シート名を取得する。
   *
   * @return String シート名
   */
  public long getNumberOfSheets() {

    // / 1.シート名を設定する
    return workbook.getNumberOfSheets();
  }

  /**
   * シート名を取得する。
   *
   * @param lngSheetNo シート番号
   * @return String シート名
   */
  public String getSheetName(int lngSheetNo) {

    // / 1.シート名を設定する
    return workbook.getSheetName(lngSheetNo);
  }

  /**
   * シート名を設定する。
   *
   * @param lngSheetNo シート番号
   * @param strSheetName シート名
   */
  public void setSheetName(int lngSheetNo, String strSheetName) {

    // / 1.シート名を設定する
    // workbook.setSheetName((int) lngSheetNo, strSheetName, XSSFWorkbook.ENCODING_UTF_16);
    workbook.setSheetName(lngSheetNo, strSheetName);
  }

  /**
   * 指定したシート名が存在するかどうか。
   *
   * @param strSheetName シート名
   * @return 存在するかどうか
   */
  public boolean existSheet(String strSheetName) {
    return getSheet(strSheetName) != null;
  }

  /**
   * 最初のシートの最初のセルにフォーカスする。
   */
  public void setInitFocus() {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Row row = null;

    // / 1.シートを取得する
    sheet = workbook.getSheetAt(0);

    // / 2.行を取得する
    row = sheet.getRow(0);
    if (row == null) {
      row = createRow(sheet, 0);
    }

    // / 3.セルを取得する
    Cell cell = row.getCell((short) 0);
    if (cell == null) {
      cell = createCell(row, 0);
    }

    // / 4.セルをアクティブにする
    cell.setAsActiveCell();

    // / 5.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
    row = null;
  }

  /**
   * シートを選択状態にする。
   *
   * @param strSheetName シート名
   */
  public void selectedSheet(String strSheetName) {
    if (workbook.getSheet(strSheetName) != null) {
      workbook.getSheet(strSheetName).setSelected(true);
    }
  }

  /**
   * デフォルトシートを選択状態にする。
   */
  public void selectedDeaultSheet() {
    workbook.getSheetAt(0).setSelected(true);
  }

  /**
   * シートをコピーする(同ブック内のみ) 末尾にシートの複製を生成する。
   *
   * @param strSheetNameFrom コピー元シート名
   * @param strSheetNameTo コピー先シート名
   */
  public void cloneSheet(String strSheetNameFrom, String strSheetNameTo) {
    // / 1.コピー対象のシートが存在する場合
    if (workbook.getSheet(strSheetNameFrom) != null) {

      // // 1.1.シートをコピーする
      // workbook.cloneSheet(workbook.getSheetIndex(strSheetNameFrom));
      workbook.createSheet(strSheetNameTo);

      // // 1.2.シート名を設定する
      // workbook.setSheetName(workbook.getNumberOfSheets() - 1, strSheetNameTo,
      // XSSFWorkbook.ENCODING_UTF_16);
      workbook.setSheetName(workbook.getNumberOfSheets() - 1, strSheetNameTo);

      // 行タイトルを複写する
      clonePrintRowTitle(strSheetNameFrom, strSheetNameTo);
    }
  }

  /**
   * 行の繰返しの複写。
   *
   * @param strSheetNameFrom 複写元行位置
   * @param strSheetNameTo 複写先行位置
   */
  private void clonePrintRowTitle(String strSheetNameFrom, String strSheetNameTo) {
    // ローカル変数宣言 //
    Name hssfName = null;

    // 印刷タイトルの複写
    // タイトル設定情報を取得する
    hssfName = workbook.getName("Print_Titles");
    // 設定情報が取得できない場合は、処理を抜ける
    if (hssfName == null) {
      return;
    }
    String title = hssfName.getRefersToFormula();

    // 設定情報が取得できない場合は、処理を抜ける
    if (StringUtils.isEmpty(title)) {
      return;
    }

    // 設定情報を取得する
    // RangeAddress address = new RangeAddress(hssfName.getReference());
    AreaReference areaReference = new AreaReference(hssfName.getRefersToFormula(), null);
    CellReference cref = (CellReference) areaReference.getAllReferencedCells()[0];
    // 設定情報のシート名が複写元シート名でない場合は、処理を抜ける
    if (!cref.getSheetName().equals(strSheetNameFrom)) {
      return;
    }
    // 開始セル、終了セル情報を取得する
    CellReference fromCell = (CellReference) areaReference.getFirstCell();
    CellReference toCell = (CellReference) areaReference.getLastCell();

    // 行タイトルか否かの判定する（開始セルのの列、終了セルの列が255以上であること）
    if (fromCell.getCol() != 0 || toCell.getCol() < 255) {
      return;
    }

    // 行タイトルの設定を行う
    SXSSFSheet targetSheet = workbook.getSheet(strSheetNameTo);
    CellRangeAddress columnRangeRef =
        new CellRangeAddress(fromCell.getRow(), toCell.getRow(), -1, -1);
    targetSheet.setRepeatingColumns(columnRangeRef);
  }

  /**
   * 書式をコピーする。
   *
   * @param strSheetName シート名
   * @param strRangeFrom コピー元
   * @param strRangeTo コピー先
   */
  public void copyCellStyle(String strSheetName, String strRangeFrom, String strRangeTo) {
    // ローカル変数宣言 //
    Sheet sheet = null; // 対象シート
    Cell cell = null; // コピー元セルインスタンス

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }

    // // 2.1.コピー元のセルを取得する
    cell = getCell(sheet, strRangeFrom);

    // // 2.2.コピー先の行を生成する
    Cell targetCell = getCell(sheet, strRangeTo);

    // /// 2.4.3.コピー元のセルがNULLではない場合
    if (cell != null) {

      // //// 2.4.3.2.セルの書式をコピーする
      targetCell.setCellStyle(cell.getCellStyle());

      // //// 2.4.3.3.行の高さをコピーする
      getRow(sheet, strRangeTo).setHeight(getRow(sheet, strRangeFrom).getHeight());
    }

    // / 4.不要オブジェクトを破棄する
    sheet = null;
    cell = null;
    targetCell = null;
  }

  /**
   * Excelの行を書式コピーする コピー先インデックスフラグ：絶対インデックス指定。
   *
   * @param strSheetName 対象シート名
   * @param lngStartRow コピー開始行インデックス
   * @param lngEndRow コピー終了行インデックス
   * @param lngTargetRow コピー先開始行インデックス
   */
  public void copyRowStyle(String strSheetName, int lngStartRow, int lngEndRow, int lngTargetRow) {
    copyRow(strSheetName, lngStartRow, lngEndRow, lngTargetRow, COPY_VALUE_UNCOPY,
        COPY_TARGET_ABUSOLUTE);
  }

  /**
   * Excelの行をコピーする。
   *
   * @param strSheetName 対象シート名
   * @param lngStartRow コピー開始行インデックス
   * @param lngEndRow コピー終了行インデックス
   * @param lngTargetRow コピー先開始行インデックス
   * @param strValueFlg セル値コピーフラグ
   * @param strTargetRowFlg コピー先インデックスフラグ(絶対インデックス指定、相対インデックス指定)
   * @throws SystemException 异常的场合
   */
  public void copyRow(String strSheetName, int lngStartRow, int lngEndRow, int lngTargetRow,
      String strValueFlg, String strTargetRowFlg) {
    // ローカル変数宣言 //
    Row row = null; // コピー元行インスタンス
    Row targetRow = null; // コピー先行インスタンス
    Cell cell = null; // コピー元セルインスタンス
    Cell targetCell = null; // コピー先セルインスタンス
    long lngCellLength = 0; // 有効セル数

    // / 1.コピーする行数分繰り返す
    for (int i = lngStartRow; i <= lngEndRow; i++) {

      // // 1.1.コピー元の行を取得する
      row = workbook.getSheet(strSheetName).getRow(i);
      if (row == null) {
        row = workbook.getSheet(strSheetName).createRow(i);
      }

      // // 1.2.コピー先の行を生成する
      // /// 1.2.1.相対インデックスの場合
      if (strTargetRowFlg.equals(COPY_TARGET_RELATIVE)) {
        targetRow = workbook.getSheet(strSheetName).createRow(lngTargetRow + i);
        // /// 1.2.2.絶対インデックスの場合
      } else {
        targetRow = workbook.getSheet(strSheetName).createRow((lngTargetRow + i - lngStartRow));
      }

      // // 1.3.行の中で有効なセル数を取得する
      lngCellLength = row.getLastCellNum();

      // // 1.4.有効なセル数分繰り返す
      for (int j = 0; j < lngCellLength; j++) {

        // /// 1.4.1.コピー元のセルを取得する
        cell = row.getCell(j);

        // /// 1.4.2.コピー先のセルを生成する
        targetCell = targetRow.createCell(j);

        // /// 1.4.3.コピー元のセルがNULLではない場合
        if (cell != null) {

          // //// 1.4.3.1.値セットフラグが「セット」の場合セルの値をコピーする
          if (strValueFlg.equals(COPY_VALUE_COPY)) {
            switch (cell.getCellType()) {

              case BLANK:
                break;
              case BOOLEAN:
                targetCell.setCellValue(cell.getBooleanCellValue());
                break;
              case ERROR:
                targetCell.setCellValue(cell.getErrorCellValue());
                break;
              case FORMULA:
                targetCell.setCellFormula(cell.getCellFormula());
                break;
              case NUMERIC:
                targetCell.setCellValue(cell.getNumericCellValue());
                break;
              case STRING:
                targetCell.setCellValue(cell.getStringCellValue());
                break;
              default:
                break;

            }
          }
          // //// 1.4.3.2.セルの書式をコピーする
          targetCell.setCellStyle(cell.getCellStyle());
        }
      }

      // // 1.5.行の高さをコピーする
      targetRow.setHeight(row.getHeight());
    }
  }

  /**
   * Excelの行をコピーする。
   *
   * @param strSheetName 対象シート名
   * @param lngStartCol コピー開始行インデックス
   * @param lngEndCol コピー終了行インデックス
   * @param lngTargetCol コピー先開始行インデックス
   * @param strValueFlg セル値コピーフラグ
   * @param strTargetRowFlg コピー先インデックスフラグ(絶対インデックス指定、相対インデックス指定)
   * @throws SystemException 异常的场合
   */
  public void copyCol(String strSheetName, int lngStartCol, int lngEndCol, int lngTargetCol,
      String strValueFlg, String strTargetRowFlg) {
    // ローカル変数宣言 //
    Row row = null; // コピー元行インスタンス
    Row targetRow = null; // コピー先行インスタンス
    Cell cell = null; // コピー元セルインスタンス
    Cell targetCell = null; // コピー先セルインスタンス
    long lngCellLength = 0; // 有効セル数

    // / 1.コピーする行数分繰り返す
    for (int i = lngStartCol; i <= lngEndCol; i++) {

      // // 1.1.コピー元の行を取得する
      row = workbook.getSheet(strSheetName).getRow(i);

      // // 1.2.コピー先の行を生成する
      // /// 1.2.1.相対インデックスの場合
      if (strTargetRowFlg.equals(COPY_TARGET_RELATIVE)) {
        targetRow = workbook.getSheet(strSheetName).createRow(lngTargetCol + i);
        // /// 1.2.2.絶対インデックスの場合
      } else {
        targetRow = workbook.getSheet(strSheetName).createRow(lngTargetCol);
      }

      // // 1.3.行の中で有効なセル数を取得する
      lngCellLength = row.getLastCellNum();

      // // 1.4.有効なセル数分繰り返す
      for (int j = 0; j < lngCellLength; j++) {

        // /// 1.4.1.コピー元のセルを取得する
        cell = row.getCell(j);

        // /// 1.4.2.コピー先のセルを生成する
        targetCell = targetRow.createCell(j);

        // /// 1.4.3.コピー元のセルがNULLではない場合
        if (cell != null) {

          // //// 1.4.3.1.値セットフラグが「セット」の場合セルの値をコピーする
          if (strValueFlg.equals(COPY_VALUE_COPY)) {
            switch (cell.getCellType()) {

              case BLANK:
                break;
              case BOOLEAN:
                targetCell.setCellValue(cell.getBooleanCellValue());
                break;
              case ERROR:
                targetCell.setCellValue(cell.getErrorCellValue());
                break;
              case FORMULA:
                targetCell.setCellFormula(cell.getCellFormula());
                break;
              case NUMERIC:
                targetCell.setCellValue(cell.getNumericCellValue());
                break;
              case STRING:
                targetCell.setCellValue(cell.getStringCellValue());
                break;
              default:
                break;

            }
          }
          // //// 1.4.3.2.セルの書式をコピーする
          targetCell.setCellStyle(cell.getCellStyle());
        }
      }

      // // 1.5.行の高さをコピーする
      targetRow.setHeight(row.getHeight());
    }
  }

  /**
   * Excelの範囲をコピーする。
   *
   * @param strSheetName 対象シート名
   * @param lngCopyBaseStartRow コピー元開始行インデックス
   * @param lngCopyBaseStartCol コピー元開始列インデックス
   * @param lngCopyBaseEndRow コピー元終了行インデックス
   * @param lngCopyBaseEndCol コピー元終了列インデックス
   * @param lngCopyTargetRow コピー先開始行インデックス
   * @param lngCopyTargetCol コピー先開始列インデックス
   * @param strValueFlg セル値コピーフラグ
   */
  public void copyRange(String strSheetName, int lngCopyBaseStartRow, int lngCopyBaseStartCol,
      int lngCopyBaseEndRow, int lngCopyBaseEndCol, int lngCopyTargetRow, int lngCopyTargetCol,
      String strValueFlg) {
    // ローカル変数宣言 //
    Row row = null; // コピー元行インスタンス
    Row targetRow = null; // コピー先行インスタンス
    Cell cell = null; // コピー元セルインスタンス
    Cell targetCell = null; // コピー先セルインスタンス
    int lngEndCol = 0; // 終了列
    int lngTargetRow = 0; // 複写先行
    int lngTargetCol = 0; // 複写先列

    /// 1.コピーする行数分繰り返す
    for (int i = lngCopyBaseStartRow; i <= lngCopyBaseEndRow; i++) {
      //// 1.1.コピー元の行を取得する
      row = workbook.getSheet(strSheetName).getRow(i);

      //// 1.2.コピー先の行を生成する
      lngTargetRow = lngCopyTargetRow + i - lngCopyBaseStartRow;
      targetRow = workbook.getSheet(strSheetName).getRow(lngTargetRow);
      if (targetRow == null) {
        targetRow = workbook.getSheet(strSheetName).createRow(lngTargetRow);
      }

      //// 1.3.コピー行の中で有効なセル数を取得する
      lngEndCol = row.getLastCellNum();
      ///// 1.3.1.複写の終了列より複写終了セルが少ない場合は、有効セル数に複写終了セルを指定する
      if (lngEndCol > lngCopyBaseEndCol) {
        lngEndCol = lngCopyBaseEndCol;
      }
      ///// 1.3.2.複写の終了列より複写開始セルが少ない場合は、複写を行わない
      if (lngEndCol < lngCopyBaseStartCol) {
        continue;
      }

      //// 1.4.有効なセル数分繰り返す
      for (int j = lngCopyBaseStartCol; j <= lngEndCol; j++) {

        ///// 1.4.1.コピー元のセルを取得する
        cell = row.getCell(j);

        ///// 1.4.2.コピー先のセルを生成する
        lngTargetCol = lngCopyTargetCol + j - lngCopyBaseStartCol;
        targetCell = targetRow.createCell(lngTargetCol);

        ///// 1.4.3.コピー元のセルがNULLではない場合
        if (cell != null) {

          ////// 1.4.3.1.値セットフラグが「セット」の場合セルの値をコピーする
          if (strValueFlg.equals(COPY_VALUE_COPY)) {
            switch (cell.getCellType()) {

              case BLANK:
                break;
              case BOOLEAN:
                targetCell.setCellValue(cell.getBooleanCellValue());
                break;
              case ERROR:
                targetCell.setCellValue(cell.getErrorCellValue());
                break;
              case FORMULA:
                targetCell.setCellFormula(cell.getCellFormula());
                break;
              case NUMERIC:
                targetCell.setCellValue(cell.getNumericCellValue());
                break;
              case STRING:
                targetCell.setCellValue(cell.getStringCellValue());
                break;
              default:
                break;

            }
          }
          ////// 1.4.3.2.セルの書式をコピーする
          targetCell.setCellStyle(cell.getCellStyle());
        }
      }

      //// 1.5.行の高さをコピーする
      targetRow.setHeight(row.getHeight());
    }
  }

  /**
   * Excelの範囲をコピーする。
   *
   * @param strSheetName 対象シート名
   * @param lngCopyBaseStartRow コピー元開始行インデックス
   * @param lngCopyBaseStartCol コピー元開始列インデックス
   * @param lngCopyBaseEndRow コピー元終了行インデックス
   * @param lngCopyBaseEndCol コピー元終了列インデックス
   * @param strTargetSheetName コピー先シート名
   * @param lngCopyTargetRow コピー先開始行インデックス
   * @param lngCopyTargetCol コピー先開始列インデックス
   * @param strValueFlg セル値コピーフラグ
   */
  public void copyRange(String strSheetName, int lngCopyBaseStartRow, int lngCopyBaseStartCol,
      int lngCopyBaseEndRow, int lngCopyBaseEndCol, String strTargetSheetName, int lngCopyTargetRow,
      int lngCopyTargetCol, String strValueFlg) {
    // ローカル変数宣言 //
    Row row = null; // コピー元行インスタンス
    Row targetRow = null; // コピー先行インスタンス
    Cell cell = null; // コピー元セルインスタンス
    Cell targetCell = null; // コピー先セルインスタンス
    long lngEndCol = 0; // 終了列
    int lngTargetRow = 0; // 複写先行
    int lngTargetCol = 0; // 複写先列

    /// 1.コピーする行数分繰り返す
    for (int i = lngCopyBaseStartRow; i <= lngCopyBaseEndRow; i++) {
      //// 1.1.コピー元の行を取得する
      row = workbook.getSheet(strSheetName).getRow(i);

      //// 1.2.コピー先の行を生成する
      lngTargetRow = lngCopyTargetRow + i - lngCopyBaseStartRow;
      targetRow = workbook.getSheet(strTargetSheetName).getRow(lngTargetRow);
      if (targetRow == null) {
        targetRow = workbook.getSheet(strTargetSheetName).createRow(lngTargetRow);
      }

      //// 1.3.コピー行の中で有効なセル数を取得する
      lngEndCol = row.getLastCellNum();
      ///// 1.3.1.複写の終了列より複写終了セルが少ない場合は、有効セル数に複写終了セルを指定する
      if (lngEndCol > lngCopyBaseEndCol) {
        lngEndCol = lngCopyBaseEndCol;
      }
      ///// 1.3.2.複写の終了列より複写開始セルが少ない場合は、複写を行わない
      if (lngEndCol < lngCopyBaseStartCol) {
        continue;
      }

      //// 1.4.有効なセル数分繰り返す
      for (int j = lngCopyBaseStartCol; j <= lngEndCol; j++) {

        ///// 1.4.1.コピー元のセルを取得する
        cell = row.getCell(j);

        ///// 1.4.2.コピー先のセルを生成する
        lngTargetCol = lngCopyTargetCol + j - lngCopyBaseStartCol;
        targetCell = targetRow.createCell(lngTargetCol);

        ///// 1.4.3.コピー元のセルがNULLではない場合
        if (cell != null) {

          ////// 1.4.3.1.値セットフラグが「セット」の場合セルの値をコピーする
          if (strValueFlg.equals(COPY_VALUE_COPY)) {
            switch (cell.getCellType()) {

              case BLANK:
                break;
              case BOOLEAN:
                targetCell.setCellValue(cell.getBooleanCellValue());
                break;
              case ERROR:
                targetCell.setCellValue(cell.getErrorCellValue());
                break;
              case FORMULA:
                targetCell.setCellFormula(cell.getCellFormula());
                break;
              case NUMERIC:
                targetCell.setCellValue(cell.getNumericCellValue());
                break;
              case STRING:
                targetCell.setCellValue(cell.getStringCellValue());
                break;
              default:
                break;

            }
          }
          ////// 1.4.3.2.セルの書式をコピーする
          targetCell.setCellStyle(cell.getCellStyle());
        }
      }

      //// 1.5.行の高さをコピーする
      targetRow.setHeight(row.getHeight());
    }
  }

  /**
   * Excelの範囲を挿入する。
   *
   * @param strSheetName 対象シート名
   * @param lngCopyBaseStartRow コピー元開始行インデックス
   * @param lngCopyBaseStartCol コピー元開始列インデックス
   * @param lngCopyBaseEndRow コピー元終了行インデックス
   * @param lngCopyBaseEndCol コピー元終了列インデックス
   * @param strTargetSheetName コピー先シート名
   * @param lngCopyTargetRow コピー先開始行インデックス
   * @param lngCopyTargetCol コピー先開始列インデックス
   * @param strValueFlg セル値コピーフラグ
   */
  public void insertRange(String strSheetName, int lngCopyBaseStartRow, int lngCopyBaseStartCol,
      int lngCopyBaseEndRow, int lngCopyBaseEndCol, String strTargetSheetName, int lngCopyTargetRow,
      int lngCopyTargetCol, String strValueFlg) {
    // ローカル変数宣言 //
    Row row = null; // コピー元行インスタンス
    Row targetRow = null; // コピー先行インスタンス
    Cell cell = null; // コピー元セルインスタンス
    Cell targetCell = null; // コピー先セルインスタンス
    long lngEndCol = 0; // 終了列
    int lngTargetRow = 0; // 複写先行
    int lngTargetCol = 0; // 複写先列

    /// 1.コピーする行数分繰り返す
    for (int i = lngCopyBaseStartRow; i <= lngCopyBaseEndRow; i++) {
      //// 1.1.コピー元の行を取得する
      row = workbook.getSheet(strSheetName).getRow(i);

      //// 1.2.コピー先の行を生成する
      lngTargetRow = lngCopyTargetRow + i - lngCopyBaseStartRow;
      targetRow = workbook.getSheet(strTargetSheetName).getRow(lngTargetRow);
      if (targetRow == null) {
        targetRow = workbook.getSheet(strTargetSheetName).createRow(lngTargetRow);
      } else {
        int lastRowNo = workbook.getSheet(strTargetSheetName).getLastRowNum();
        workbook.getSheet(strTargetSheetName).shiftRows(lngTargetRow, lastRowNo, 1, true, false);
        targetRow = workbook.getSheet(strTargetSheetName).createRow(lngTargetRow);
      }

      //// 1.3.コピー行の中で有効なセル数を取得する
      lngEndCol = row.getLastCellNum();
      ///// 1.3.1.複写の終了列より複写終了セルが少ない場合は、有効セル数に複写終了セルを指定する
      if (lngEndCol > lngCopyBaseEndCol) {
        lngEndCol = lngCopyBaseEndCol;
      }
      ///// 1.3.2.複写の終了列より複写開始セルが少ない場合は、複写を行わない
      if (lngEndCol < lngCopyBaseStartCol) {
        continue;
      }

      //// 1.4.有効なセル数分繰り返す
      for (int j = lngCopyBaseStartCol; j <= lngEndCol; j++) {

        ///// 1.4.1.コピー元のセルを取得する
        cell = row.getCell(j);

        ///// 1.4.2.コピー先のセルを生成する
        lngTargetCol = lngCopyTargetCol + j - lngCopyBaseStartCol;
        targetCell = targetRow.createCell(lngTargetCol);

        ///// 1.4.3.コピー元のセルがNULLではない場合
        if (cell != null) {

          ////// 1.4.3.1.値セットフラグが「セット」の場合セルの値をコピーする
          if (strValueFlg.equals(COPY_VALUE_COPY)) {
            switch (cell.getCellType()) {

              case BLANK:
                break;
              case BOOLEAN:
                targetCell.setCellValue(cell.getBooleanCellValue());
                break;
              case ERROR:
                targetCell.setCellValue(cell.getErrorCellValue());
                break;
              case FORMULA:
                targetCell.setCellFormula(cell.getCellFormula());
                break;
              case NUMERIC:
                targetCell.setCellValue(cell.getNumericCellValue());
                break;
              case STRING:
                targetCell.setCellValue(cell.getStringCellValue());
                break;
              default:
                break;

            }
          }
          ////// 1.4.3.2.セルの書式をコピーする
          targetCell.setCellStyle(cell.getCellStyle());
        }
      }

      //// 1.5.行の高さをコピーする
      targetRow.setHeight(row.getHeight());
    }
  }

  /**
   * シートを削除する。
   *
   * @param strSheetName シート名
   */
  public void deleteSheet(String strSheetName) {
    // ローカル変数宣言 //
    Sheet sheet = null;

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できない場合、nullを返却する
    if (sheet == null) {
      return;
    }

    // / 2.シートを削除する
    workbook.removeSheetAt(workbook.getSheetIndex(strSheetName));
  }

  /**
   * セルのスタイルを生成する。
   *
   * @return CellStyle スタイル情報
   */
  public CellStyle getCreateStyle() {

    // スタイルを返却する
    return workbook.createCellStyle();
  }

  /**
   * セルのスタイルを取得する。
   *
   * @param strSheetName シート名
   * @param strRange セル位置
   * @return CellStyle 指定されたセルのスタイル情報
   */
  public CellStyle getCellStyle(String strSheetName, String strRange) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル
    CellStyle retStyle = null; // セルのスタイル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できない場合、nullを返却する
    if (sheet == null) {
      return retStyle;
    }

    // / 2.セルからセルのスタイルを取得する
    cell = getCell(sheet, strRange);
    retStyle = cell.getCellStyle();

    // / 4.取得したセルのスタイルを返却する
    return retStyle;
  }

  /**
   * セルのスタイルを設定する。
   *
   * @param strSheetName シート名
   * @param strRange セル位置
   * @param style スタイル情報
   */
  public void setCellStyle(String strSheetName, String strRange, CellStyle style) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できない場合、処理を終了する
    if (sheet == null) {
      return;
    }

    // / 2.セルにスタイルを設定する
    cell = getCell(sheet, strRange);
    cell.setCellStyle(style);
  }

  /**
   * フォントを生成する。
   *
   * @return Font フォント情報
   */
  public Font getCreateFont() {
    return workbook.createFont();
  }

  /**
   * デフォルトフォント取得。
   *
   * @param index フォントインデックス
   * @return Font フォント情報
   */
  public Font getFont(int index) {
    return workbook.getFontAt(index);
  }

  /**
   * ヘッダ（左）を設定する。
   *
   * @param strSheetName シート名
   * @param strHeader 設定する文字列
   */
  public void setHeaderLeft(String strSheetName, String strHeader) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      sheet.getHeader().setLeft(strHeader);
    }
  }

  /**
   * ヘッダ（中央）を設定する。
   *
   * @param strSheetName シート名
   * @param strHeader 設定する文字列
   */
  public void setHeaderCenter(String strSheetName, String strHeader) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      sheet.getHeader().setCenter(strHeader);
    }
  }

  /**
   * ヘッダ（右）を設定する。
   *
   * @param strSheetName シート名
   * @param strHeader 設定する文字列
   */
  public void setHeaderRight(String strSheetName, String strHeader) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      sheet.getHeader().setRight(strHeader);
    }
  }

  /**
   * フッタ（左）を設定する。
   *
   * @param strSheetName シート名
   * @param strFooter 設定する文字列
   */
  public void setFooterLeft(String strSheetName, String strFooter) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      sheet.getFooter().setLeft(strFooter);
    }
  }

  /**
   * フッタ（中央）を設定する。
   *
   * @param strSheetName シート名
   * @param strFooter 設定する文字列
   */
  public void setFooterCenter(String strSheetName, String strFooter) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      sheet.getFooter().setCenter(strFooter);
    }
  }

  /**
   * フッタ（右）を設定する。
   *
   * @param strSheetName シート名
   * @param strFooter 設定する文字列
   */
  public void setFooterRight(String strSheetName, String strFooter) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      sheet.getFooter().setRight(strFooter);
    }
  }

  /**
   * 開始セル位置から最終セルまで行をクリアする。
   *
   * @param strSheetName 対象シート名
   * @param strStartCellPosition 開始セル位置
   */
  public void clearRow(String strSheetName, String strStartCellPosition) {
    // ローカル変数宣言 //
    Sheet sheet = null;
    Row row = null; // コピー元行インスタンス
    Cell cell = null; // コピー元セルインスタンス

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // / / 1.1.シートが取得できない場合は、処理を終了する
    if (sheet == null) {
      return;
    }

    // / 2.行を取得する
    row = getRow(sheet, strStartCellPosition);

    // / 3.最終セルインデックスを取得する
    int lngLastCellIndex = row.getLastCellNum();

    // / 4.クリアする
    for (int i = getColIndex(strStartCellPosition); i <= lngLastCellIndex; i++) {
      cell = row.getCell(i);
      if (cell != null) {
        cell.setBlank();;
      }
    }
  }

  /**
   * 開始行位置から最終行まで列をクリアする。
   *
   * @param strSheetName 対象シート名
   * @param strStartCellPosition 開始セル位置
   */
  public void clearCol(String strSheetName, String strStartCellPosition) {
    // ローカル変数宣言 //
    Sheet sheet = null;
    Row row = null; // コピー元行インスタンス
    Cell cell = null; // コピー元セルインスタンス

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できない場合は、処理を終了する
    if (sheet == null) {
      return;
    }

    // / 2.行を取得する
    row = getRow(sheet, strStartCellPosition);

    // / 3.最終セルインデックスを取得する
    int lngLastRowIndex = sheet.getLastRowNum();

    // / 4.列インデックスを取得する
    int lngColIndex = getColIndex(strStartCellPosition);

    // / 5.クリアする
    for (int i = getRowIndex(strStartCellPosition); i <= lngLastRowIndex; i++) {

      // / 5.1.行を取得する
      row = sheet.getRow(i);
      if (row == null) {
        continue;
      }

      // / 5.2.セルを取得する
      cell = row.getCell(lngColIndex);
      if (cell != null) {
        // / 5.3.クリアする
        cell.setBlank();;
      }
    }
  }

  /**
   * セルを結合する(レンジ指定)。
   *
   * @param strSheetName 対象シート名
   * @param strStartA1 開始位置
   * @param strEndA1 終了位置
   */
  public void mergedCell(String strSheetName, String strStartA1, String strEndA1) {

    // / 1.セル結合を呼び出す
    mergedCell(strSheetName, getRowIndex(strStartA1), getRowIndex(strEndA1),
        getColIndex(strStartA1), getColIndex(strEndA1));
  }

  /**
   * セルを結合する(行、列指定)。
   *
   * @param strSheetName 対象シート名
   * @param lngStartRow 開始行位置
   * @param lngEndRow 終了行位置
   * @param lngStartCol 開始列位置
   * @param lngEndCol 終了列位置
   */
  public void mergedCell(String strSheetName, int lngStartRow, int lngEndRow, int lngStartCol,
      int lngEndCol) {

    // シートを取得する
    Sheet sheet = getSheet(strSheetName);
    // シートが取得できない場合は、処理を終了する
    if (sheet == null) {
      return;
    }

    // セルを結合する
    sheet.addMergedRegion(new CellRangeAddress(lngStartRow, lngEndRow, lngStartCol, lngEndCol));
  }

  /**
   * 行を移動する。
   *
   * @param strSheetName 対象シート名
   * @param lngStartRow 開始行
   * @param lngEndRow 終了行
   * @param lngMoveRowNum 移動行数
   */
  public void moveRows(String strSheetName, int lngStartRow, int lngEndRow, int lngMoveRowNum) {
    // ローカル変数宣言 //
    Sheet sheet = null;

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できない場合は、処理を終了する
    if (sheet == null) {
      return;
    }

    // / 2.行を結合する
    sheet.shiftRows(lngStartRow, lngEndRow, lngMoveRowNum, true, true);
  }

  /**
   * 印刷タイトルを設定する。
   *
   * @param strSheetName シート名
   * @param lngStartCol 列開始位置
   * @param lngEndCol 列終了位置
   * @param lngStartRow 行開始位置
   * @param lngEndRow 列開始位置
   */
  public void setPrintTitle(String strSheetName, int lngStartCol, int lngEndCol, int lngStartRow,
      int lngEndRow) {
    SXSSFSheet targetSheet = workbook.getSheet(strSheetName);
    CellRangeAddress columnRangeRef =
        new CellRangeAddress(lngStartRow, lngEndRow, lngStartCol, lngEndCol);
    targetSheet.setRepeatingColumns(columnRangeRef);
  }

  /**
   * 印刷タイトル（行タイトル）を設定する。
   * </p>
   * 制限事項:<br>
   * 列タイトルはクリアされます。
   * </p>
   *
   * @param strSheetName シート名
   * @param lngStartRow 行開始位置
   * @param lngEndRow 行終了位置
   */
  public void setPrintTitleRows(String strSheetName, int lngStartRow, int lngEndRow) {
    SXSSFSheet targetSheet = workbook.getSheet(strSheetName);
    CellRangeAddress columnRangeRef = new CellRangeAddress(lngStartRow, lngEndRow, -1, -1);
    targetSheet.setRepeatingColumns(columnRangeRef);
  }

  /**
   * 印刷タイトル（列タイトル）を設定する。
   * </p>
   * 制限事項:<br>
   * 行タイトルはクリアされます。
   * </p>
   *
   * @param strSheetName シート名
   * @param lngStartCol 行開始位置
   * @param lngEndCol 行終了位置
   */
  public void setPrintTitleCols(String strSheetName, int lngStartCol, int lngEndCol) {
    SXSSFSheet targetSheet = workbook.getSheet(strSheetName);
    CellRangeAddress columnRangeRef = new CellRangeAddress(-1, -1, lngStartCol, lngEndCol);
    targetSheet.setRepeatingColumns(columnRangeRef);
  }

  /**
   * 印刷範囲の指定。
   *
   * @param strSheetName 対象シート名
   * @param lngStartRow 開始行位置
   * @param lngEndRow 終了行位置
   * @param lngStartCol 開始列位置
   * @param lngEndCol 終了列位置
   */
  public void setPrintArea(String strSheetName, int lngStartRow, int lngEndRow, int lngStartCol,
      int lngEndCol) {
    // ローカル変数宣言 //
    int intSheetIndex = 0; // シートインデックス

    // / 1.シートインデックスを取得する
    intSheetIndex = workbook.getSheetIndex(strSheetName);

    // / 2.印刷範囲を指定する
    workbook.setPrintArea(intSheetIndex, lngStartCol, lngEndCol, lngStartRow, lngEndRow);
  }

  /**
   * 改ページを設定する。
   *
   * @param strSheetName 値を設定するシート名
   * @param lngSetRow 行
   * @param lngSetCol 列
   */
  public void setPageBreak(String strSheetName, int lngSetRow, int lngSetCol) {
    setPageRowBreak(strSheetName, lngSetRow);
    setPageColumnBreak(strSheetName, lngSetCol);
  }

  /**
   * 改ページを設定する（行）。
   *
   * @param strSheetName 値を設定するシート名
   * @param lngSetRow 行
   */
  public void setPageRowBreak(String strSheetName, int lngSetRow) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    /// 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }
    sheet.setRowBreak(lngSetRow);
  }

  /**
   * 改ページを設定する（列）。
   *
   * @param strSheetName 値を設定するシート名
   * @param lngSetCol 列
   */
  public void setPageColumnBreak(String strSheetName, int lngSetCol) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    /// 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return;
    }
    sheet.setColumnBreak(lngSetCol);
  }

  /**
   * セルの罫線（上）を設定する。
   *
   * @param strSheetName シート名
   * @param range A1形式のセル位置
   * @param borderStyle ボーダースタイル
   */
  public void setBorderTop(String strSheetName, String range, BorderStyle borderStyle) {
    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setBorderTop(borderStyle);
    setCellStyleProperty(strSheetName, getRowIndex(range), getColIndex(range), cellStyle);
  }

  /**
   * セルの罫線（下）を設定する。
   *
   * @param strSheetName シート名
   * @param range A1形式のセル位置
   * @param borderStyle ボーダースタイル
   */
  public void setBorderBottom(String strSheetName, String range, BorderStyle borderStyle) {
    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setBorderBottom(borderStyle);
    setCellStyleProperty(strSheetName, getRowIndex(range), getColIndex(range), cellStyle);
  }

  /**
   * セルの罫線（左）を設定する。
   *
   * @param strSheetName シート名
   * @param range A1形式のセル位置
   * @param borderStyle ボーダースタイル
   */
  public void setBorderLeft(String strSheetName, String range, BorderStyle borderStyle) {
    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setBorderLeft(borderStyle);
    setCellStyleProperty(strSheetName, getRowIndex(range), getColIndex(range), cellStyle);
  }

  /**
   * セルの罫線（右）を設定する。
   *
   * @param strSheetName シート名
   * @param range A1形式のセル位置
   * @param borderStyle ボーダースタイル
   */
  public void setBorderRight(String strSheetName, String range, BorderStyle borderStyle) {
    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setBorderRight(borderStyle);
    setCellStyleProperty(strSheetName, getRowIndex(range), getColIndex(range), cellStyle);
  }

  /**
   * セルの網掛け色（背景色）を設定する。
   * </p>
   * 制限事項: <br>
   * 一部、書式設定が解除されます。
   * <ul>
   * <li>縮小して全体を表示する</li>
   * </ul>
   * </p>
   *
   * @param strSheetName シート名
   * @param range A1形式のセル位置
   * @param color カラーインデックス
   */
  public void setFillForegroundColor(String strSheetName, String range, short color) {
    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setFillForegroundColor(color);
    setCellStyleProperty(strSheetName, getRowIndex(range), getColIndex(range), cellStyle);
  }

  /**
   * セルの網掛けパターンを設定する。
   * </p>
   * 制限事項: <br>
   * 一部、書式設定が解除されます。
   * <ul>
   * <li>縮小して全体を表示する</li>
   * </ul>
   * </p>
   *
   * @param strSheetName シート名
   * @param range A1形式のセル位置
   * @param style 網掛けスタイル
   */
  public void setFillPattern(String strSheetName, String range, FillPatternType style) {
    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setFillPattern(style);
    setCellStyleProperty(strSheetName, getRowIndex(range), getColIndex(range), cellStyle);
  }

  /**
   * セル内の水平方向の位置を設定する。
   *
   * @param strSheetName シート名
   * @param range A1形式のセル位置
   * @param alignmentStyle 水平方向の位置スタイル
   */
  public void setAlignment(String strSheetName, String range, HorizontalAlignment alignmentStyle) {
    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setAlignment(alignmentStyle);
    setCellStyleProperty(strSheetName, getRowIndex(range), getColIndex(range), cellStyle);
  }

  /**
   * セルスタイルを設定する。
   * </p>
   * 制限事項: <br>
   * 一部、書式設定が解除されます。
   * <ul>
   * <li>縮小して全体を表示する</li>
   * </ul>
   * </p>
   *
   * @param strSheetName シート名
   * @param row 行インデックス
   * @param col 列インデックス
   * @param cellStyle 設定するスタイル
   */
  private void setCellStyleProperty(String strSheetName, int row, int col, CellStyle cellStyle) {
    Sheet currentSheet = workbook.getSheet(strSheetName);
    Row currentRow = currentSheet.getRow(row);
    Cell currentCell = currentRow.getCell(col);
    currentCell.setCellStyle(cellStyle);
  }

  /**
   * フォントの色を設定する。
   * </p>
   * 制限事項: <br>
   * 一部、書式設定が解除されます。
   * <ul>
   * <li>縮小して全体を表示する</li>
   * </ul>
   * </p>
   *
   * @param strSheetName シート名
   * @param range セル
   * @param fontColor 色
   */
  public void setFontColor(String strSheetName, String range, short fontColor) {
    setFontColor(strSheetName, getRowIndex(range), getColIndex(range), fontColor);
  }

  /**
   * フォントの色を設定する。
   *
   * @param strSheetName シート名
   * @param row 行インデックス
   * @param col 列インデックス
   * @param fontColor 色
   */
  private void setFontColor(String strSheetName, int row, int col, short fontColor) {
    Sheet currentSheet = workbook.getSheet(strSheetName);
    Row currentRow = currentSheet.getRow(row);
    Cell currentCell = currentRow.getCell(col);

    Font origFont = getFont(currentCell.getCellStyle().getFontIndexAsInt());
    Font font = workbook.createFont();

    BeanUtils.copyProperties(origFont, font);
    font.setColor(fontColor);

    CellStyle cellStyle = workbook.createCellStyle();
    cellStyle.setFont(font);
    currentCell.setCellStyle(cellStyle);

  }

  // Excelからセル値取得メッソドを追加
  /**
   * セルに値を取得する(String型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @return セルの値
   */
  public String getStringCellValue(String strSheetName, String strA1) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return "";
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルに値を取得する
    String result = cell.getStringCellValue();

    // / 4.不要オブジェクトを破棄する
    sheet = null;
    cell = null;

    /// 5.結果を返却する
    return result;
  }

  /**
   * セルに値を取得する(Date型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @return セルの値
   */
  public Date getDateCellValue(String strSheetName, String strA1) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return null;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルに値を取得する
    Date result = cell.getDateCellValue();

    // / 4.不要オブジェクトを破棄する
    sheet = null;
    cell = null;

    /// 5.結果を返却する
    return result;
  }

  /**
   * セルに値を取得する(BigDecimal型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @return セルの値
   */
  public BigDecimal getBigDecimalCellValue(String strSheetName, String strA1) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return null;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルに値を取得する
    BigDecimal result = FwNumberUtils.toBigDecimal(cell.getStringCellValue());

    // / 4.不要オブジェクトを破棄する
    sheet = null;
    cell = null;

    /// 5.結果を返却する
    return result;
  }



  /**
   * セルに値を取得する(Double型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @return セルの値
   */
  public Double getFormulaNumericCellValue(String strSheetName, String strA1) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return null;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルに値を取得する
    FormulaEvaluator evaluator = workbook.getCreationHelper().createFormulaEvaluator();
    Double result = evaluator.evaluate(cell).getNumberValue();// 例 读取计算结果 =SUM(M6:M15)

    // / 4.不要オブジェクトを破棄する
    sheet = null;
    cell = null;

    /// 5.結果を返却する
    return result;
  }



  /**
   * セルに値を取得する(Double型)。
   *
   * @param strSheetName 値を設定するシート名
   * @param strA1 A1形式のセル位置
   * @return セルの値
   */
  public Double getDoubleCellValue(String strSheetName, String strA1) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート
    Cell cell = null; // セル

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    if (sheet == null) {
      return null;
    }

    // / 2.セルを取得する
    cell = getCell(sheet, strA1);

    // / 3.セルに値を取得する
    Double result = cell.getNumericCellValue();

    // / 4.不要オブジェクトを破棄する
    sheet = null;
    cell = null;

    /// 5.結果を返却する
    return result;
  }

  /**
   * 行の高さを取得する。
   *
   * @param strSheetName シート名
   * @param rowIndex 行数
   */
  public short getRowHeight(String strSheetName, int rowIndex) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      return sheet.getRow(rowIndex).getHeight();
    }

    return (short) 0;
  }

  /**
   * 行の高さを設定する。
   *
   * @param strSheetName シート名
   * @param rowIndex 行数
   * @param height 設定する高さ
   */
  public void setRowHeight(String strSheetName, int rowIndex, short height) {
    // ローカル変数宣言 //
    Sheet sheet = null; // シート

    // / 1.シートを取得する
    sheet = getSheet(strSheetName);
    // // 1.1.シートが取得できた場合
    if (sheet != null) {
      sheet.getRow(rowIndex).setHeight(height);
    }
  }
}
