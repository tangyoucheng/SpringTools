/*
 * Copyright(c) 2011
 */
package cn.com.platform.framework.util;

import java.lang.management.ManagementFactory;
import java.text.ParseException;
import java.text.ParsePosition;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import org.apache.commons.lang3.StringUtils;
import cn.com.platform.framework.common.StandardConstantsIF;
import cn.com.platform.framework.common.exception.SystemException;


/**
 * 日付に関するユーティリティクラス。
 * 
 * @author t.d.m
 */
public final class FwDateUtils {

  /**
   * DateUtils 的构造。
   */
  private FwDateUtils() {}

  /**
   * APサーバーから系统日付的取得。
   * 
   * @return 現在の系统日付
   */
  public static Date getSysDate() {

    LocalDateTime localDateTime = LocalDateTime.now();
    ZoneId zone = ZoneId.systemDefault();
    Instant instant = localDateTime.atZone(zone).toInstant();

    return Date.from(instant);
  }

  /**
   * APサーバーから系统日付的取得。
   * 
   * @return 現在の系统日付
   */
  public static Date getDateFromLocalDateTime(LocalDateTime  localDateTime) {

    ZoneId zone = ZoneId.systemDefault();
    Instant instant = localDateTime.atZone(zone).toInstant();

    return Date.from(instant);
  }
  
  /**
   * APサーバーから系统日付的取得。
   * 
   * @return 現在の系统日付
   */
  public static LocalDateTime getLocalDateTimeFromDate(Date date) {
    
    Instant instant = date.toInstant();
    ZoneId zone = ZoneId.systemDefault();
    
    return LocalDateTime.ofInstant(instant, zone);
  }

  /**
   * メモリの系统運用日的取得。
   * 
   * @return メモリで保存された系统運用日
   * @throws SystemException 失敗した場合スロー
   */
  public static LocalDateTime getSysDateTime() {
    return LocalDateTime.now();
  }

  /**
   * 获取服务器启动时间
   * 
   * @return
   */
  public static Date getServerStartDate() {
    long time = ManagementFactory.getRuntimeMXBean().getStartTime();
    return new Date(time);
  }

  /**
   * 计算两个时间差
   * 
   * @param endDate 结束时间
   * @param nowDate 开始时间
   * @return 时间差
   */
  public static String getDatePoor(Date endDate, Date nowDate) {
    long nd = 1000 * 24 * 60 * 60;
    long nh = 1000 * 60 * 60;
    long nm = 1000 * 60;
    // long ns = 1000;
    // 获得两个时间的毫秒时间差异
    long diff = endDate.getTime() - nowDate.getTime();
    // 计算差多少天
    long day = diff / nd;
    // 计算差多少小时
    long hour = diff % nd / nh;
    // 计算差多少分钟
    long min = diff % nd % nh / nm;
    // 计算差多少秒//输出结果
    // long sec = diff % nd % nh % nm / ns;
    return day + "天" + hour + "小时" + min + "分钟";
  }

  /**
   * 指定された形式の日付時刻文字列を日付型に変換する。
   * 
   * @param text 日付時刻文字列
   * @param format 日付時刻文字列の形式
   * @return 変換後の日付
   * @throws SystemException 日付時刻文字列の変換に失敗した場合スロー
   */
  public static Date parse(String text, String format) throws SystemException {

    if (StringUtils.isEmpty(text) || StringUtils.isEmpty(format)) {
      throw new IllegalArgumentException();
    }

    SimpleDateFormat dateFormat = new SimpleDateFormat(format);
    dateFormat.setLenient(false);
    ParsePosition pos = new ParsePosition(0);

    Date date = dateFormat.parse(text, pos);

    if (pos.getErrorIndex() >= 0) {
      throw new SystemException(
          new ParseException("日期文字(" + text + ")不能转换成日期类型。" + "形式=" + format, pos.getErrorIndex()));
    }

    return date;
  }

  /**
   * 指定された形式の日付時刻文字列を日付型に変換する。
   * 
   * @param date 日付時刻文字列
   * @return 変換後の日付
   * @throws SystemException 日付時刻文字列の変換に失敗した場合スロー
   */
  public static String parseFmtYMDHMS(Date date) {

    if (date == null) {
      return null;
    }

    SimpleDateFormat format = new SimpleDateFormat(StandardConstantsIF.DATE_FORMART_YMDHMS_DASH);
    return format.format(date);

  }

  /**
   * 指定された形式の日付時刻文字列を日付型に変換する。
   * 
   * @param date 日付時刻文字列
   * @return 変換後の日付
   * @throws SystemException 日付時刻文字列の変換に失敗した場合スロー
   */
  public static String parseFmtYMDHMS(LocalDateTime date) {

    if (date == null) {
      return null;
    }
    return date.format(DateTimeFormatter.ofPattern(StandardConstantsIF.DATE_FORMAT_TIMESTAMP));

  }

  /**
   * 指定年月日。
   * 
   * @param date 年月日
   * @return 年月日
   * @throws SystemException 年月日
   */
  public static String parseFmtYMD(Date date) {

    if (date == null) {
      return null;
    }

    SimpleDateFormat format = new SimpleDateFormat(StandardConstantsIF.DATE_FORMART_YMD);
    return format.format(date);

  }

  /**
   * 指定年月日。
   * 
   * @param date 年月日
   * @return 年月日
   * @throws SystemException 年月日
   */
  public static String parseFmtYMD(LocalDateTime date) {

    if (date == null) {
      return null;
    }
    return date.format(DateTimeFormatter.ISO_LOCAL_DATE);

  }


}
