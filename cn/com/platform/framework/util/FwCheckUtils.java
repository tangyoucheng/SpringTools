/*
 * Copyright(c) 2011
 */
package cn.com.platform.framework.util;

import java.io.File;
import java.lang.Character.UnicodeBlock;
import java.math.BigDecimal;
import java.util.Date;
import cn.com.platform.framework.common.StandardConstantsIF;



/**
 * チェックユーティリティクラス。
 * <p>
 * 入力値などの値に対して評価を行うユーティリティクラス。
 * </p>
 * 
 * @author 唐友成
 * @date 2019-02-19
 */
public class FwCheckUtils {

  /**
   * CheckUtils 的构造。
   */
  private FwCheckUtils() {}


  /**
   * 指定された文字列がnullかどうかをチェックする。
   * <p>
   * 評価対象に指定された文字列がnullかどうかをチェックする。 長さ0の場合もnullと評価する。
   * </p>
   * 
   * @param _value 評価対象文字列
   * @return 評価結果 nullの場合は true、以外は false
   */
  public static boolean isEmpty(String _value) {
    if (_value == null || _value.length() == 0) {
      return true;
    }
    return false;
  }

}
