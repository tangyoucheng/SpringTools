package javadiffutils;

public class FileUtils {
    /**
     * ファイル名から拡張子を小文字で取得します。
     * @param fileName ファイル名（またはパス）
     * @return 拡張子（存在しない場合は空文字）
     */
    public static String getExtension(String fileName) {
        if (fileName == null) {
            return "";
        }

        String ext = "";
        int i = fileName.lastIndexOf('.');
        if (i > 0) {
            ext = fileName.substring(i + 1).toLowerCase();
        }
        return ext;
    }
}

