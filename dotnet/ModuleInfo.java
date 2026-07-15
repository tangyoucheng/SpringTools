package dotnet;

public class ModuleInfo {
    String name;
    String oldSrc;
    String newSrc;
    String type;

    ModuleInfo(String name, String oldSrc, String newSrc, String type) {
        this.name = name;
        this.oldSrc = oldSrc;
        this.newSrc = newSrc;
        this.type = type;
    }
}
