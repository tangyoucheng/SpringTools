package dotnet;

import java.util.Objects;

class DllInfo {
    String dllName;
    String version;

    public DllInfo(String dllName, String version) {
        this.dllName = normalize(dllName);
        this.version = normalize(version);
    }

    private String normalize(String str) {
        if (str == null) return "";
        return str.trim()
                  .replaceAll("\\u00A0", "") // NBSP
                  .replaceAll("\\s+", "")
                  .toLowerCase();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof DllInfo)) return false;
        DllInfo that = (DllInfo) o;
        return Objects.equals(dllName, that.dllName) &&
               Objects.equals(version, that.version);
    }

    @Override
    public int hashCode() {
        return Objects.hash(dllName, version);
    }
}
