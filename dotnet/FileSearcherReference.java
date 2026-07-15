package dotnet;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.apache.poi.openxml4j.exceptions.InvalidFormatException;
import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.xssf.usermodel.XSSFSheet;

import cn.com.platform.framework.file.ExcelMakeFile;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.Namespace;
import org.dom4j.io.SAXReader;
import org.dom4j.XPath;
import org.dom4j.Node;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;

public class FileSearcherReference {

	public static String sheetNewName;

	public static void main(String[] args) throws Exception {

		String outputDir = "output.csproj"; // 存放EXCEL报告的目录

//    	String sourcePath = "C:\\\\src";
//    	String sourcePath = "C:\src\\Projects";
//    	String sourcePath = "C:\\src\\SI";
//    	String sourcePath = "C:\\src\\VM";
		String sourcePath = "C:\\src\\VZ";

		ModuleInfo[] modules = new ModuleInfo[] { new ModuleInfo("FW", "C:\\src\\Projects", "", "FW"),
				new ModuleInfo("SI", "C:\\src\\SI", "", "業務アプリ"),
				new ModuleInfo("VM", "C:\\src\\VM", "", "業務アプリ"),
				new ModuleInfo("VZ", "C:\\src\\VZ", "", "業務アプリ") };
//		ModuleInfo[] modules = new ModuleInfo[] { new ModuleInfo("FW", "C:\\src\\Projects", "", "FW")};
//		ModuleInfo[] modules = new ModuleInfo[] { new ModuleInfo("FW", "C:\\src\\SI", "", "業務アプリ")};
//		ModuleInfo[] modules = new ModuleInfo[] { new ModuleInfo("FW", "C:\\src\\VM", "", "業務アプリ")};
//		ModuleInfo[] modules = new ModuleInfo[] { new ModuleInfo("FW", "C:\\src\\VZ", "", "業務アプリ")};

		// 遍历每个模块执行统计
		for (ModuleInfo module : modules) {
			System.out.println("===== " + module.name + " =====");

			String projectPath = Paths.get("").toAbsolutePath().toString();
			ExcelMakeFile excelMakeFile = new ExcelMakeFile(
					new File(projectPath + "/src/main/resources/templates/template_csproj_reference.xlsx"));

	        // 统计结构：DLL名 Version
	        // ✅ 用 Set 自动去重
	        Set<DllInfo> dllSet = new HashSet<DllInfo>();


			sheetNewName = module.name;
			excelMakeFile.cloneSheet(excelMakeFile.workbook.getSheetAt(1).getSheetName(), sheetNewName);

			// 対象のディレクトリパス
			Path startPath = Paths.get(module.oldSrc);

			try (Stream<Path> stream = Files.walk(startPath)) {
				// 条件に合うファイルをリスト化
				List<Path> csprojFiles = stream.filter(Files::isRegularFile) // ディレクトリを除外
						.filter(path -> path.toString().endsWith(".csproj")) // 拡張子チェック
						.collect(Collectors.toList());

				XSSFSheet outputSheet = excelMakeFile.workbook.getSheet(sheetNewName);
				String sheetName = outputSheet.getSheetName();

				for (Path csprojPath : csprojFiles) {
//					int sheetLastRowNum = outputSheet.getLastRowNum() + 2;
//					excelMakeFile.setCellValue(sheetName, "B" + sheetLastRowNum, sheetLastRowNum - 3);
//					excelMakeFile.setCellValue(sheetName, "C" + sheetLastRowNum, module.type);
//					excelMakeFile.setCellValue(sheetName, "D" + sheetLastRowNum, sheetNewName);
//					excelMakeFile.setCellValue(sheetName, "E" + sheetLastRowNum,
//							csprojPath.toString().replace("C:\\Kyocera_src\\", ""));

			        // ============= START =============
//			        File xmlFile = new File("path/to/your/Project.csproj"); // 修改为你的文件路径
					File xmlFile = csprojPath.toFile();
			        SAXReader reader = new SAXReader();
			        Document doc = reader.read(xmlFile);

			        // MSBuild XML 的命名空间
			        Namespace msbuildNs = new Namespace("", "http://schemas.microsoft.com/developer/msbuild/2003");
			        XPath xPath = doc.createXPath("//msbuild:Reference");
			        xPath.setNamespaceURIs(java.util.Collections.singletonMap("msbuild", msbuildNs.getURI()));

			        List<Node> referenceNodes = xPath.selectNodes(doc);
			        List<ProjectReference> references = new ArrayList<>();

					for (Node node : referenceNodes) {
						if (node instanceof Element) {
							Element ref = (Element) node;
							ProjectReference pr = new ProjectReference();

							// Include 属性
							String include = ref.attributeValue("Include");
							pr.setInclude(include);

							// 解析 Include 内的 Version, Culture, PublicKeyToken, processorArchitecture
							if (include != null) {
								for (String part : include.split(",")) {
									String[] kv = part.trim().split("=", 2);
									if (kv.length == 2) {
										String key = kv[0].trim().toLowerCase();
										String value = kv[1].trim();
										switch (key) {
										case "version":
											pr.setVersion(value);
											break;
										case "culture":
											pr.setCulture(value);
											break;
										case "publickeytoken":
											pr.setPublicKeyToken(value);
											break;
										case "processorarchitecture":
											pr.setProcessorArchitecture(value);
											break;
										}
									} else {
										pr.setInclude(part);
									}
								}
							}

							// SpecificVersion
							Element specificVersion = ref.element("SpecificVersion");
							pr.setSpecificVersion(specificVersion != null ? specificVersion.getTextTrim() : null);

							// HintPath
							Element hintPath = ref.element("HintPath");
							pr.setHintPath(hintPath != null ? hintPath.getTextTrim() : null);

							// Private
							Element isPrivate = ref.element("Private");
							pr.setIsPrivate(isPrivate != null ? isPrivate.getTextTrim() : null);

							references.add(pr);
						}

						// 输出测试：完整解析 8 个字段
						for (ProjectReference pr : references) {
							System.out.println("参照名（Include）: " + pr.getInclude());
							System.out.println("バージョン（Version）: " + pr.getVersion());
							System.out.println("文化（Culture）: " + pr.getCulture());
							System.out.println("公開キー（PublicKeyToken）: " + pr.getPublicKeyToken());
							System.out.println("プロセッサアーキテクチャ: " + pr.getProcessorArchitecture());
							System.out.println("特定バージョン: " + pr.getSpecificVersion());
							System.out.println("パス（HintPath）: " + pr.getHintPath());
							System.out.println("プライベート: " + pr.getIsPrivate());
							System.out.println("------------------------------------------------");

							int sheetLastRowNum = outputSheet.getLastRowNum() + 2;
							excelMakeFile.setCellValue(sheetName, "B" + sheetLastRowNum, sheetLastRowNum - 3);
							excelMakeFile.setCellValue(sheetName, "C" + sheetLastRowNum, module.type);
							excelMakeFile.setCellValue(sheetName, "D" + sheetLastRowNum, sheetNewName);
							excelMakeFile.setCellValue(sheetName, "E" + sheetLastRowNum,
									csprojPath.toString().replace("C:\\Kyocera_src\\", ""));

							excelMakeFile.setCellValue(sheetName, "F" + sheetLastRowNum, pr.getInclude());
							excelMakeFile.setCellValue(sheetName, "G" + sheetLastRowNum, pr.getVersion());
							excelMakeFile.setCellValue(sheetName, "H" + sheetLastRowNum, pr.getCulture());
							excelMakeFile.setCellValue(sheetName, "I" + sheetLastRowNum, pr.getPublicKeyToken());
							excelMakeFile.setCellValue(sheetName, "J" + sheetLastRowNum, pr.getProcessorArchitecture());
							excelMakeFile.setCellValue(sheetName, "K" + sheetLastRowNum, pr.getSpecificVersion());
							excelMakeFile.setCellValue(sheetName, "L" + sheetLastRowNum, pr.getHintPath());
							excelMakeFile.setCellValue(sheetName, "M" + sheetLastRowNum, pr.getIsPrivate());

							setBorderStyle(excelMakeFile, sheetName, sheetLastRowNum);

					        // 统计结构：DLL名 Version
							dllSet.add(new DllInfo(pr.getInclude().trim().replaceAll("\\s+", ""), pr.getVersion().trim().replaceAll("\\s+", "")));
						}

					}
					// ============= END =============

				}

				// 結果の表示
//				csprojFiles.forEach(System.out::println);
//				System.out.println("見つかったファイル数: " + csprojFiles.size());

			} catch (IOException e) {
				e.printStackTrace();
			}

	        List<DllInfo> dllList = new ArrayList<>(dllSet);
	        // 🔽 按 DLL 名降序排序
	        dllList.sort((a, b) -> b.dllName.compareToIgnoreCase(a.dllName));


			XSSFSheet outputSheet0 = excelMakeFile.workbook.getSheetAt(0);
			String sheetName0 = outputSheet0.getSheetName();
	        // 输出
	        for (DllInfo info : dllList) {
				int sheetLastRowNum = outputSheet0.getLastRowNum() + 2;
				excelMakeFile.setCellValue(sheetName0, "C" + sheetLastRowNum, sheetLastRowNum - 3);
				excelMakeFile.setCellValue(sheetName0, "D" + sheetLastRowNum, info.dllName);
				excelMakeFile.setCellValue(sheetName0, "E" + sheetLastRowNum, info.version);

				setBorderStyle0(excelMakeFile, sheetName0, sheetLastRowNum);

	            System.out.println("DLL名: " + info.dllName + " | Version: " + info.version);
	        }


	        DateTimeFormatter df = DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS");
	        String fileName = module.name +"プロジェクト参照一覧・集計".concat("_").concat(df.format(LocalDateTime.now()));
	        fileName = fileName.concat(".xlsx");

	        Path path = Paths.get(projectPath, outputDir, fileName);
	        // 关键：创建目录（递归创建）
	        Files.createDirectories(path.getParent());
	        // 再写文件
	        Files.write(path, excelMakeFile.getBytes());
		}


	}

	private static void setBorderStyle0(ExcelMakeFile excelMakeFile, String sheetName, int sheetLastRowNum) {

		// 设置列范围 B~I
		String[] cols = { "B", "C", "D", "E", "F" };
		for (String colLetter : cols) {
			excelMakeFile.setBorder(sheetName, colLetter + sheetLastRowNum, BorderStyle.THIN);
		}
	}

	private static void setBorderStyle(ExcelMakeFile excelMakeFile, String sheetName, int sheetLastRowNum) {

		// 设置列范围 B~I
		String[] cols = { "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M" };
		for (String colLetter : cols) {
			excelMakeFile.setBorder(sheetName, colLetter + sheetLastRowNum, BorderStyle.THIN);
		}
	}
}
