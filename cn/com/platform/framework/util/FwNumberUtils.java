/*
 * Copyright(c) 2011
 */
package cn.com.platform.framework.util;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.DecimalFormat;
import java.util.Objects;


/**
 * 数値に関するユーティリティクラス。
 * 
 * @author t.d.m
 */
public final class FwNumberUtils {

  /**
   * NumberUtils 的构造。
   */
  private FwNumberUtils() {}

  /**
   * 文字列を int型に変換する。
   * <p>
   * 文字列が nullまたは長さ0の文字の場合は 0を返却する。<br>
   * </p>
   * 
   * <pre>
   *   NumberUtils.toInt(null) = 0
   *   NumberUtils.toInt(&quot;&quot;) = 0
   *   NumberUtils.toInt(&quot;1&quot;) = 1
   * </pre>
   * 
   * @param _value 変換対象の文字列
   * @return 変換後の int型
   */
  public static int toInt(String _value) {
    return toInt(_value, 0);
  }

  /**
   * 文字列を int型に変換する。
   * <p>
   * 文字列が nullまたは長さ0の文字の場合は デフォルト値を返却する。<br>
   * </p>
   * 
   * <pre>
   *   NumberUtils.toInt(null, 1) = 1
   *   NumberUtils.toInt(&quot;&quot;, 1) = 1
   *   NumberUtils.toInt(&quot;1&quot;, 0) = 1
   * </pre>
   * 
   * @param _value 変換対象の文字列
   * @param _defaultValue 文字列がnullまたは長さ0の場合に返却するデフォルト値
   * @return 変換後の int型
   */
  public static int toInt(String _value, int _defaultValue) {
    if (FwCheckUtils.isEmpty(_value)) {
      return _defaultValue;
    }
    return toBigDecimal(_value).intValue();
  }

  /**
   * 文字列を long型に変換する。
   * <p>
   * 文字列が nullまたは長さ0の文字の場合は 0を返却する。<br>
   * </p>
   * 
   * <pre>
   *   NumberUtils.toLong(null) = 0L
   *   NumberUtils.toLong(&quot;&quot;) = 0L
   *   NumberUtils.toLong(&quot;1&quot;) = 1L
   * </pre>
   * 
   * @param _value 変換対象の文字列
   * @return 変換後の long型
   */
  public static long toLong(String _value) {
    return toLong(_value, 0L);
  }

  /**
   * 文字列を int型に変換する。
   * <p>
   * 文字列が nullまたは長さ0の文字の場合は デフォルト値を返却する。<br>
   * </p>
   * 
   * <pre>
   *   NumberUtils.toLong(null, 1L) = 1
   *   NumberUtils.toLong(&quot;&quot;, 1L) = 1
   *   NumberUtils.toLong(&quot;1&quot;, 0L) = 1
   * </pre>
   * 
   * @param _value 変換対象の文字列
   * @param _defaultValue 文字列がnullまたは長さ0の場合に返却するデフォルト値
   * @return 変換後の int型
   */
  public static long toLong(String _value, long _defaultValue) {
    if (FwCheckUtils.isEmpty(_value)) {
      return _defaultValue;
    }
    return toBigDecimal(_value).longValue();
  }

  /**
   * 文字列を BigDecimalに変換する。
   * <p>
   * 文字列が nullまたは長さ0の文字の場合は 0を返却する。<br>
   * </p>
   * 
   * @param _value 変換対象の文字列
   * @return 変換後の BigDecimal
   */
  public static BigDecimal toBigDecimal(String _value) {
    return toBigDecimal(_value, 0);
  }

  /**
   * 文字列を BigDecimalに変換する。
   * <p>
   * 文字列が nullまたは長さ0の文字の場合は 0を返却する。<br>
   * </p>
   * 
   * @param _value 変換対象
   * @return 変換後の BigDecimal
   */
  public static BigDecimal toBigDecimal(Object _value) {
    return toBigDecimal(String.valueOf(_value), 0);
  }

  /**
   * 文字列を BigDecimalに変換する。
   * <p>
   * 文字列が nullまたは長さ0の文字の場合は デフォルト値を返却する。<br>
   * </p>
   * 
   * <pre>
   *   NumberUtils.toBigDecimal(null, 1D) = 1
   *   NumberUtils.toBigDecimal(&quot;&quot;, 1D) = 1
   *   NumberUtils.toBigDecimal(&quot;1&quot;, 0D) = 1
   * </pre>
   * 
   * @param _value 変換対象の文字列
   * @param _defaultValue 文字列がnullまたは長さ0の場合に返却するデフォルト値
   * @return 変換後の BigDecimal
   */
  public static BigDecimal toBigDecimal(String _value, double _defaultValue) {
    if (FwCheckUtils.isEmpty(_value)) {
      return new BigDecimal(_defaultValue);
    }
    return new BigDecimal(_value.replaceAll(",", ""));
  }

  /**
   * 文字列から BegDecimalを生成する。
   * <p>
   * 文字列が <code>null</code> または 長さ0の場合は <code>null</code>が返却される。
   * </p>
   * 
   * <pre>
   *   NumberUtils.createBegDecimal(null) = null
   *   NumberUtils.createBegDecimal(&quot;&quot;) = null
   *   NumberUtils.createBegDecimal(&quot;1&quot;) = 1
   * </pre>
   * 
   * @param _value 変換対象の文字列
   * @return 変換後の BigDecimal
   */
  public static BigDecimal createBigDecimal(String _value) {
    if (FwCheckUtils.isEmpty(_value)) {
      return null;
    }
    return new BigDecimal(_value.replaceAll(",", ""));
  }

  /**
   * 指定した数値書式に変換する。
   * 
   * @param _value 変換対象の文字列
   * @param _format 数値書式
   * @return 変換後の文字列
   */
  public static String format(String _value, String _format) {
    return format(toBigDecimal(_value), _format);
  }

  /**
   * 指定した数値書式に変換する。
   * 
   * @param _value 変換対象
   * @param _format 数値書式
   * @return 変換後の文字列
   */
  public static String format(Object _value, String _format) {
    return format(toBigDecimal(Objects.toString(_value)), _format);
  }

  /**
   * 指定した数値書式に変換する。
   * 
   * @param _value 変換対象の数値
   * @param _format 数値書式
   * @return 変換後の文字列
   */
  public static String format(BigDecimal _value, String _format) {
    if (_value == null) {
      return "";
    }
    DecimalFormat df = new DecimalFormat(_format);
    return df.format(_value.doubleValue());
  }

  /**
   * 乗算を行う。
   * <p>
   * ( _value * _divisor ) である乗算結果を返却する。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _multiplicand 乗算する値
   * @return 除算結果
   */
  public static BigDecimal multiply(int _value, int _multiplicand) {
    return multiply(_value, _multiplicand, RoundingMode.DOWN);
  }

  /**
   * 乗算を行う。
   * <p>
   * ( _value * _divisor ) である乗算結果を返却する。<br>
   * 指定されたスケール、丸めモードが乗算結果に適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _multiplicand 乗算する値
   * @param _roundingMode 丸めモード
   * @return 除算結果
   */
  public static BigDecimal multiply(int _value, int _multiplicand, RoundingMode _roundingMode) {
    return multiply(new BigDecimal(_value), new BigDecimal(_multiplicand), 0, _roundingMode);
  }

  /**
   * 乗算を行う。
   * <p>
   * ( _value * _divisor ) である除算結果を返却する。<br>
   * スケール 0、丸めモード {link@RoundingMode#DOWN} が乗算結果に適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _multiplicand 除算する値
   * @return 除算結果
   */
  public static BigDecimal multiply(String _value, String _multiplicand) {
    return multiply(toBigDecimal(_value), toBigDecimal(_multiplicand), 0, RoundingMode.DOWN);
  }

  /**
   * 乗算を行う。
   * <p>
   * ( _value * _divisor ) である除算結果を返却する。<br>
   * 指定されたスケール、丸めモードが乗算結果に適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _multiplicand 除算する値
   * @param _scale 返却する値のスケール
   * @param _roundingMode 丸めモード
   * @return 除算結果
   */
  public static BigDecimal multiply(String _value, String _multiplicand, int _scale,
      RoundingMode _roundingMode) {
    return multiply(toBigDecimal(_value), toBigDecimal(_multiplicand), _scale, _roundingMode);
  }

  /**
   * 乗算を行う。
   * <p>
   * ( _value / _divisor ) で、除算結果を返却する。<br>
   * 指定されたスケール、丸めモードが適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _multiplicand 除算する値
   * @param _scale 返却する値のスケール
   * @param _roundingMode 丸めモード
   * @return 除算結果
   */
  public static BigDecimal multiply(BigDecimal _value, BigDecimal _multiplicand, int _scale,
      RoundingMode _roundingMode) {

    BigDecimal result = _value.multiply(_multiplicand);
    return result.setScale(_scale, _roundingMode);
  }

  /**
   * 除算を行う。
   * <p>
   * ( _value / _divisor ) で、スケールが 0 である除算結果を返却する。<br>
   * 丸めモードは、{link@RoundingMode#DOWN}
   * </p>
   * 
   * @param _value 計算対象値
   * @param _divisor 除算する値
   * @return 除算結果
   */
  public static BigDecimal devide(int _value, int _divisor) {
    return devide(_value, _divisor, 0, RoundingMode.DOWN);
  }

  /**
   * 除算を行う。
   * <p>
   * ( _value / _divisor ) で、スケールが 0 である除算結果を返却する。<br>
   * 指定された丸めモードが適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _divisor 除算する値
   * @param _roundingMode 丸めモード
   * @return 除算結果
   */
  public static BigDecimal devide(int _value, int _divisor, RoundingMode _roundingMode) {
    return devide(_value, _divisor, 0, _roundingMode);
  }

  /**
   * 除算を行う。
   * <p>
   * ( _value / _divisor ) で、除算結果を返却する。<br>
   * 指定されたスケール、丸めモードが適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _divisor 除算する値
   * @param _scale 返却する値のスケール
   * @param _roundingMode 丸めモード
   * @return 除算結果
   */
  public static BigDecimal devide(int _value, int _divisor, int _scale,
      RoundingMode _roundingMode) {
    return devide(new BigDecimal(_value), new BigDecimal(_divisor), _scale, _roundingMode);
  }

  /**
   * 除算を行う。
   * <p>
   * ( _value / _divisor ) で、スケールが 0 である除算結果を返却する。<br>
   * 丸めモードは、{link@RoundingMode#DOWN}
   * </p>
   * 
   * @param _value 計算対象値
   * @param _divisor 除算する値
   * @return 除算結果
   */
  public static BigDecimal devide(String _value, String _divisor) {
    return devide(toBigDecimal(_value), toBigDecimal(_divisor), 0, RoundingMode.DOWN);
  }

  /**
   * 除算を行う。
   * <p>
   * ( _value / _divisor ) で、除算結果を返却する。<br>
   * 指定されたスケール、丸めモードが適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _divisor 除算する値
   * @param _scale 返却する値のスケール
   * @param _roundingMode 丸めモード
   * @return 除算結果
   */
  public static BigDecimal devide(String _value, String _divisor, int _scale,
      RoundingMode _roundingMode) {
    return devide(toBigDecimal(_value), toBigDecimal(_divisor), _scale, _roundingMode);
  }

  /**
   * 除算を行う。
   * <p>
   * ( _value / _divisor ) で、除算結果を返却する。<br>
   * 指定されたスケール、丸めモードが適用される。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _divisor 除算する値
   * @param _scale 返却する値のスケール
   * @param _roundingMode 丸めモード
   * @return 除算結果
   */
  public static BigDecimal devide(BigDecimal _value, BigDecimal _divisor, int _scale,
      RoundingMode _roundingMode) {
    return _value.divide(_divisor, _scale, _roundingMode);
  }

  /**
   * 除算を行ない、商と剰余を返却する。
   * <p>
   * ( _value / _divisor ) の整数（商）と、( _value % _divisor ) である剰余を返却する。
   * </p>
   * 
   * @param _value 計算対象値
   * @param _divisor 除算する値
   * @return 除算結果
   */
  public static BigDecimal[] divideAndRemainder(BigDecimal _value, BigDecimal _divisor) {
    return _value.divideAndRemainder(_divisor);
  }

  /**
   * 絶対値を返却する。
   * 
   * @param _value 取得対象値
   * @return 絶対値
   */
  public static BigDecimal abs(int _value) {
    return abs(new BigDecimal(_value));
  }

  /**
   * 絶対値を返却する。
   * 
   * @param _value 取得対象値
   * @return 絶対値
   */
  public static BigDecimal abs(String _value) {
    return abs(toBigDecimal(_value));
  }

  /**
   * 絶対値を返却する。
   * 
   * @param _value 取得対象値
   * @return 絶対値
   */
  public static BigDecimal abs(BigDecimal _value) {
    return _value.abs();
  }

  /**
   * -1 を乗算した値を返却する。
   * 
   * @param _value 取得対象値
   * @return -1 を乗算した値
   */
  public static BigDecimal negate(int _value) {
    return negate(new BigDecimal(_value));
  }

  /**
   * -1 を乗算した値を返却する。
   * 
   * @param _value 取得対象値
   * @return -1 を乗算した値
   */
  public static BigDecimal negate(String _value) {
    return negate(toBigDecimal(_value));
  }

  /**
   * -1 を乗算した値を返却する。
   * 
   * @param _value 取得対象値
   * @return -1 を乗算した値
   */
  public static BigDecimal negate(BigDecimal _value) {
    return _value.negate();
  }

  /**
   * 指定されたスケール、丸めモードを適用した値を返却する。
   * 
   * @param _value 取得対象値
   * @param _scale スケール
   * @param _roundingMode 丸めモード
   * @return 丸めた値
   */
  public static BigDecimal round(BigDecimal _value, int _scale, RoundingMode _roundingMode) {
    return _value.setScale(_scale, _roundingMode);
  }

}
