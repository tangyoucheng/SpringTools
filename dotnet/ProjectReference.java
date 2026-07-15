package dotnet;

/**
 * プロジェクト参照情報を表すクラス
 * XMLの<Reference>ノードに対応
 */
public class ProjectReference {

    /** 参照名（Include属性） */
    private String include;

    /** バージョン（Version情報） */
    private String version = "";

    /** 文化（Culture情報） */
    private String culture;

    /** 公開キー（PublicKeyToken情報） */
    private String publicKeyToken;

    /** プロセッサアーキテクチャ（processorArchitecture情報） */
    private String processorArchitecture;

    /** 特定バージョン（SpecificVersionノードの値） */
    private String specificVersion;

    /** パス（HintPathノードの値） */
    private String hintPath;

    /** プライベート（Privateノードの値） */
    private String isPrivate;

    // ------------------- Getter / Setter -------------------

    public String getInclude() {
        return include;
    }

    public void setInclude(String include) {
        this.include = include;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getCulture() {
        return culture;
    }

    public void setCulture(String culture) {
        this.culture = culture;
    }

    public String getPublicKeyToken() {
        return publicKeyToken;
    }

    public void setPublicKeyToken(String publicKeyToken) {
        this.publicKeyToken = publicKeyToken;
    }

    public String getProcessorArchitecture() {
        return processorArchitecture;
    }

    public void setProcessorArchitecture(String processorArchitecture) {
        this.processorArchitecture = processorArchitecture;
    }

    public String getSpecificVersion() {
        return specificVersion;
    }

    public void setSpecificVersion(String specificVersion) {
        this.specificVersion = specificVersion;
    }

    public String getHintPath() {
        return hintPath;
    }

    public void setHintPath(String hintPath) {
        this.hintPath = hintPath;
    }

    public String getIsPrivate() {
        return isPrivate;
    }

    public void setIsPrivate(String isPrivate) {
        this.isPrivate = isPrivate;
    }
}
