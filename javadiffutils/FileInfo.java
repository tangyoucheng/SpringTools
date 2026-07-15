package javadiffutils;

/**
 * 辅助类：记录单个文件信息
 */
public class FileInfo {
	String type;
	String path;
	String status;
	int add = 0, del = 0, chg = 0;
	long stepBefore = 0;
	long nonBefore = 0;
	long commentBefore = 0;
	long stepAfter = 0;
	long nonAfter = 0;
	long commentAfter = 0;

	FileInfo(String path) {
		this.path = path;
	}

}
