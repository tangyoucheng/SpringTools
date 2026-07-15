package javadiffutils;

public class ModuleInfo {
    String name;
    String oldPath;
    String newPath;

    ModuleInfo(String name, String oldPath, String newPath) {
        this.name = name;
        this.oldPath = oldPath;
        this.newPath = newPath;
    }
}
