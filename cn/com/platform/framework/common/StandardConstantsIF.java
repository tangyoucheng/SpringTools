/*
 * Copyright(c) 2011
 */

package cn.com.platform.framework.common;

import java.nio.charset.Charset;

/**
 * 框架常量。
 * 
 * @author admin
 */
public class StandardConstantsIF {

  /** 共通：换行。 */
  public static final String LINE_SEPARATOR = System.getProperty("line.separator");

  /** 共通：画面锁 */
  // String KYOTU_GAMEN_LOCK = create().getPattern("kyotu_gamen_lock");
  /** 共通：平台系统管理员。 */
  public static final String ROLE_SYSTEM_MANAGER = "system_manager";
  /** 共通：租户管理员。 */
  public static final String ROLE_TENANT_MANAGER = "tenant_manager";

  /** 共通：密码有効日数。 */
  public static final Integer KYOTU_PASSWORD_EFFECTIVE_DATE_SU = 180;

  /** 区分（共通）：有。 */
  public static final String FLAG_STATUS_ENABLE = "1";
  /** 区分（共通）：無。 */
  public static final String FLAG_STATUS_DISABLE = "0";

  /** 每页件数size small。 */
  public static final int SMALL_PAGE_SIZE = 10;
  /** 每页件数size medium。 */
  public static final int MEDIUM_PAGE_SIZE = 20;
  /** 每页件数size great。 */
  public static final int LARGE_PAGE_SIZE = 30;

  /** 排序：升序。 */
  public static final String SORT_SEQ_ASC = "ASC";
  /** 排序：降序。 */
  public static final String SORT_SEQ_DESC = "DESC";


  /** 数字格式 模式：#,###。 */
  public static final String SUTI_FORMAT_PTN_NUM = "#,###";
  /** 数字格式 模式：#,###元。 */
  public static final String SUTI_FORMAT_PTN_NUM_YEN = "#,###元";
  /** 数字格式 模式：#,###.00。 */
  public static final String SUUI_FORMAT_PTN_NUM_POINT_DOUBLE_ZERO = "#,###.00";

  /** 共通：编码（Shift-JIS）。 */
  public static final Charset MS932 = Charset.forName("MS932");
  /** AP服务器临时文件夹。 */
  public static final String APP_SERVER_TEMP_SESSION_FOLDER = "session_temp";
  /** 导出文件临时目录。 */
  public static final String APP_SERVER_TEMP_DOWNLOAD_FOLDER =
      APP_SERVER_TEMP_SESSION_FOLDER + "/{0}/downloadTempFile/{1}";
  /** 模板目录。 */
  public static final String APP_SERVER_TEMPLATE_FOLDER = "WEB-INF/template/{0}";

  /** 日期格式 模式（时刻）：HHmm（时分）。 */
  public static final String DATE_FORMAT_TIME_HHMM = "HHmm";
  /** 日期格式 模式（时刻）：HH:mm（时:分）。 */
  public static final String DATE_FORMAT_TIME_HH_MM_JI_MINUTE = "HH:mm";

  /** 日期格式 模式：yyyy-MM-dd。 */
  public static final String DATE_FORMART_YMD = "yyyy-MM-dd";
  /** 日期格式 模式：TIMESTAMP。 */
  public static final String DATE_FORMAT_TIMESTAMP = "yyyy-MM-dd HH:mm:ss.SSS";
  public static final String DATE_FORMART_YMDHMS_DASH = "yyyy-MM-dd HH:mm:ss";
  /** 日期格式 模式：yyyyMMddHHmmss（年月日时分秒）。 */
  public static final String DATE_FORMAT_YYYYMMDDHHMMSS = "yyyyMMddHHmmss";
  /** 共通：缩略图长度。 */
  public static final String KYOTU_IMAGE_THUMBNAIL_YO_SIZE_CHOHEN = "100";
  /** 共通：缩略图宽度。 */
  public static final String KYOTU_IMAGE_THUMBNAIL_YO_SIZE_TANPEN = "75";

  /** jodconverter officeHome。 */
  public static final String JODCONVERTER_OFFICEHOME = "jodconverter.officeHome";
  /** jodconverter portNumbers。 */
  public static final String JODCONVERTER_PORTNUMBERS = "jodconverter.portNumbers";
  /** jodconverter workingDir。 */
  public static final String JODCONVERTER_WORKINGDIR = "jodconverter.workingDir";


  /** 会话ID 会员登陆可。 */
  public static final String MEMBER_LOGIN_PERMIT = "memberLoginPermit";
  /** 会话ID 后台管理员登陆可。 */
  public static final String ADMIN_LOGIN_PERMIT = "adminLoginPermit";

  /** 普通用户URI。 */
  public static final String URI_BASE_HOME = "home";
  /** 普通用户URI。 */
  public static final String URI_BASE_MEMBER = "member";
  /** 后台管理员URI。 */
  public static final String URI_BASE_ADMIN = "admin";
  /** API用的URI。 */
  public static final String URI_BASE_API = "api";

  /** activiti流程变量 start。 */
  /** 任务状态。 */
  public static final String ACT_TASK_STATUS = "taskStatus";
  /** 业务状态。 */
  public static final String ACT_BUSINESS_STATUS = "businessStatus";
  /** 审批信息。 */
  public static final String ACT_PROCESS_HISTORY = "processHistoryList";
  /** 工作流-办理状态。 */
  public static final String PROCESSING_STATUS = "processingStatus";
  /** 工作流-业务阶段。 */
  public static final String BUSINESS_STAGE = "businessStage";
  /** 申请人。 */
  public static final String ACT_APPLICANT = "applicant";
  /** 申请人。 */
  public static final String ACT_APPLICANT_NAME = "applicantName";
  /** 审核者。 */
  public static final String ACT_APPROVECANT = "approvecant";
  /** 当前审核角色。 */
  public static final String ACT_RU_ROLE = "ruRole";
  /** 历史审核角色。 */
  public static final String ACT_HI_ROLE = "hiRole";
  /** 申请日期。 */
  public static final String ACT_APPLY_DATE = "applyDate";
  /** 服务指南Id。 */
  public static final String ACT_PAGE_ID = "pageId";
  /** 服务指南版本Id。 */
  public static final String ACT_PAGE_VERSION_ID = "pageVersionId";
  /** 服务指南名称。 */
  public static final String ACT_SERVICE_NAME = "serviceName";
  /** 服务页面菜单Id。 */
  public static final String ACT_MENU_ID = "menuId";
  /** 版本号。 */
  public static final String ACT_VERSION = "version";
  /** 备注。 */
  public static final String ACT_REMARK = "remark";
  /** 删除标识。 */
  public static final String ACT_DELETE_FLAG = "deleteFlag";
  /** 部门编码。 */
  public static final String ACT_DEPARTMENT_ID = "departmentId";
  /** 身份证号。 */
  public static final String ACT_CARD_NO = "cardNo";
  /** 性别。 */
  public static final String ACT_SEX = "sex";
  /** 出生年月。 */
  public static final String ACT_BIRTHDAY = "birthday";
  /** 现住址。 */
  public static final String ACT_PRESENT_ADDRESS = "presentAddress";
  /** 去向。 */
  public static final String ACT_NEXT_DEPARTMENT = "nextDepartMent";
  /** 是否领取。 */
  public static final String ACT_GET_FLAG = "getFlag";
  /** 是否办结。 */
  public static final String ACT_IS_OVER = "isOver";
  /** 联系电话。 */
  public static final String ACT_PHONE = "phone";
  /** 联系电话。 */
  public static final String ACT_NODE_ID = "nodeId";
  /** 联系电话。 */
  public static final String ACT_DATE_KEY = "dateKey";
  /** 党建宣传发布Id。 */
  public static final String ACT_PROPAGANDA_ID = "propagandaId";
  /** 党建宣传发布Id。 */
  public static final String ACT_PROPAGANDA_VERSION_ID = "propagandaVersionId";
  /** 党建宣传发布名称。 */
  public static final String ACT_PROPAGANDA_TITEL = "propagandaTitel";
  /** 党建宣传发布类型。 */
  public static final String ACT_PROPAGANDA_TYPE_ID = "propagandaTypeId";
  /** activiti流程变量 end。 */
}
