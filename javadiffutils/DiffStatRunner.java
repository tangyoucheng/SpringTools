package javadiffutils;

import com.github.difflib.DiffUtils;
import com.github.difflib.patch.AbstractDelta;
import com.github.difflib.patch.DeltaType;
import com.github.difflib.patch.Patch;

import cn.com.platform.framework.file.ExcelMakeFile;
import javadiffutils.JavaDiffCounter.LineStat;
import jp.sf.amateras.stepcounter.CountResult;
import jp.sf.amateras.stepcounter.StepCounter;
import jp.sf.amateras.stepcounter.StepCounterFactory;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.xssf.usermodel.XSSFSheet;

public class DiffStatRunner {

	public static String sheetNewName;
	public static List<String> extensions;


    public static void main(String[] args) throws Exception {
    	// 1. リストを生成して拡張子を追加
    	extensions = new ArrayList<>();
    	extensions.add(".sh");

    	extensions.add(".java");
    	extensions.add(".xml");
//    	extensions.add(".xml.dev");
//    	extensions.add(".xml.rel");
    	extensions.add(".properties");
    	extensions.add(".html");
    	extensions.add(".css");
    	extensions.add(".js");
    	extensions.add(".config");
//    	extensions.add(".config.dev");
//    	extensions.add(".config.rel");
    	extensions.add(".dev");
    	extensions.add(".rel");
    	extensions.add(".sql");
    	extensions.add(".yml");

    	extensions.add(".cs");
    	extensions.add(".Designer");
    	extensions.add(".Designer.cs");
    	extensions.add(".csproj");

		String outputDir = "output.DiffStat"; // 存放EXCEL报告的目录

		ModuleInfo[] modules = new ModuleInfo[] {
		new ModuleInfo("resources", "C:\\old\\resources",
				"C:\\new\\resources") };


		String projectPath = Paths.get("").toAbsolutePath().toString();
		ExcelMakeFile excelMakeFile = new ExcelMakeFile(
				new File(projectPath + "/src/main/resources/templates/template_DiffExcel.xlsx"));

        for (ModuleInfo module : modules) {
            System.out.println("\n========================================");
            System.out.println("模块: " + module.name);
            System.out.println("========================================");


			sheetNewName = module.name;
			excelMakeFile.cloneSheet(excelMakeFile.workbook.getSheetAt(0).getSheetName(), sheetNewName);

			XSSFSheet outputSheet = excelMakeFile.workbook.getSheet(sheetNewName);
			String sheetName = outputSheet.getSheetName();

            // 存储当前模块下所有文件的明细
            List<FileInfo> fileDetails = new ArrayList<>();

            Map<String, File> oldFileMap = getAllFilesRelative(new File(module.oldPath));
            Map<String, File> newFileMap = getAllFilesRelative(new File(module.newPath));

            Set<String> allPaths = new TreeSet<>(oldFileMap.keySet()); // TreeSet 保证输出路径有序
            allPaths.addAll(newFileMap.keySet());

            int moduleAdd = 0, moduleDel = 0, moduleChg = 0;

            long moduleStepBefore = 0, moduleNonBefore = 0, moduleCommentBefore = 0;
            long moduleStepAfter = 0, moduleNonAfter = 0, moduleCommentAfter = 0;

            for (String relPath : allPaths) {
                File oldFile = oldFileMap.get(relPath);
                File newFile = newFileMap.get(relPath);
                FileInfo info = new FileInfo(relPath);

				if (relPath.endsWith(".sln")
						|| relPath.endsWith(".csproj.user")) {
					continue;
				}

                try {
                    if (oldFile != null && newFile != null) {
                    	int firstDot = newFile.getName().indexOf(".");
                    	String multiExt = newFile.getName().substring(firstDot + 1);
                    	String[] parts = multiExt.split("\\.", 2);
                    	if ("Fisshplate".equals(parts[0])) {
                    		info.type = "csproj";
						} else if ("Designer".equals(parts[0])) {
							info.type = "cs";
						} else {
							info.type = parts[0];
						}
//                    	info.type = FileUtils.getExtension(newFile.getName());

                        // 【变更/未变】
                    	System.out.println(oldFile.toPath());
                        List<String> oldLines = Files.readAllLines(oldFile.toPath());
                        List<String> newLines = Files.readAllLines(newFile.toPath());
                        Patch<String> patch = DiffUtils.diff(oldLines, newLines);

                        // 修改前
//                        for (AbstractDelta<String> delta : patch.getDeltas()) {
//                            switch (delta.getType()) {
//                                case INSERT: info.add += delta.getTarget().getLines().size(); break;
//                                case DELETE: info.del += delta.getSource().getLines().size(); break;
//                                case CHANGE: info.chg += delta.getSource().getLines().size(); break;
//                            }
//                        }

                        // 修改后   核心：差异对比逻辑
                        for (AbstractDelta<String> delta : patch.getDeltas()) {
                            int sourceSize = delta.getSource().getLines().size();
                            int targetSize = delta.getTarget().getLines().size();

                            if (delta.getType() == DeltaType.INSERT) {
                            	info.add += targetSize;
                            } else if (delta.getType() == DeltaType.DELETE) {
                            	info.del += sourceSize;
                            } else if (delta.getType() == DeltaType.CHANGE) {
                                // 优化后的 CHANGE 逻辑：
                                // 如果 1 行变成 2 行 -> 1 行变更，1 行新增
                                int common = Math.min(sourceSize, targetSize);
                                info.chg += common;
                                if (targetSize > sourceSize) {
                                	info.add += (targetSize - sourceSize);
                                } else if (sourceSize > targetSize) {
                                	info.del += (sourceSize - targetSize);
                                }
                            }
                        }

//                        info.status = (info.add + info.del + info.chg > 0) ? "MODIFIED" : "SAME";
//                        info.status = (info.add + info.del + info.chg > 0) ? "変更" : "変更なし";
                        if (info.add + info.del + info.chg > 0) {
                        	info.status = "変更";
						} else {
							continue;
//                        	info.status = "変更なし";
						}


//    					StepCounter counter = StepCounterFactory.getCounter(oldFile.getAbsolutePath());
//    					CountResult countResult = counter.count(oldFile, StandardCharsets.UTF_8.displayName());
//    					info.stepBefore = countResult.getStep();
//    					info.nonBefore = countResult.getNon();
//    					info.commentBefore = countResult.getComment();

                        countBeforeLinesByExtension(info,oldFile, oldLines);

//    					counter = StepCounterFactory.getCounter(newFile.getAbsolutePath());
//    					countResult = counter.count(newFile, StandardCharsets.UTF_8.displayName());
//    					info.stepAfter = countResult.getStep();
//    					info.nonAfter = countResult.getNon();
//    					info.commentAfter = countResult.getComment();

                        countAfterLinesByExtension(info,newFile, newLines);


                    } else if (oldFile == null) {
                    	info.type = FileUtils.getExtension(newFile.getName());
                        // 【新增文件】
                        info.add = Files.readAllLines(newFile.toPath()).size();
//                        info.status = "NEW";
                        info.status = "新規";

//    					StepCounter counter = StepCounterFactory.getCounter(newFile.getAbsolutePath());
//    					CountResult countResult = counter.count(newFile, StandardCharsets.UTF_8.displayName());
//    					info.stepAfter = countResult.getStep();
//    					info.nonAfter = countResult.getNon();
//    					info.commentAfter = countResult.getComment();

                        countAfterLinesByExtension(info,newFile, Files.readAllLines(newFile.toPath()));

                    } else {
                    	info.type = FileUtils.getExtension(oldFile.getName());
                        // 【删除文件】
                        info.del = Files.readAllLines(oldFile.toPath()).size();
//                        info.status = "DELETED";
                        info.status = "削除";

//    					StepCounter counter = StepCounterFactory.getCounter(oldFile.getAbsolutePath());
//    					CountResult countResult = counter.count(oldFile, StandardCharsets.UTF_8.displayName());
//    					info.stepBefore = countResult.getStep();
//    					info.nonBefore = countResult.getNon();
//    					info.commentBefore = countResult.getComment();

                        countBeforeLinesByExtension(info,oldFile, Files.readAllLines(oldFile.toPath()));

                    }
                } catch (Exception e) {
                	info.status = "ERROR";
                	throw e;
                }

                // 累加模块总数
                moduleAdd += info.add;
                moduleDel += info.del;
                moduleChg += info.chg;

//                info.type ="java";
                moduleStepBefore += info.stepBefore;
                moduleNonBefore += info.nonBefore;
                moduleCommentBefore += info.commentBefore;
                moduleStepAfter += info.stepAfter;
                moduleNonAfter += info.nonAfter;
                moduleCommentAfter += info.commentAfter;

                fileDetails.add(info);
            }

            // --- 输出每个文件的明细 ---
            System.out.printf("%-10s | %-5s | %-5s | %-5s | %s\n", "状态", "新增", "删除", "修改", "文件路径");
            System.out.println("----------------------------------------------------------------------");
            for (FileInfo fileInfo : fileDetails) {
            	// ############
//                if (fileInfo.status.equals("SAME")) continue; // 可选：不打印未变化的文件
                System.out.printf("%-10s | %-5d | %-5d | %-5d | %s\n", fileInfo.status, fileInfo.add, fileInfo.del, fileInfo.chg, fileInfo.path);


				int sheetLastRowNum = outputSheet.getLastRowNum() + 2;
				excelMakeFile.setCellValue(sheetName, "B" + sheetLastRowNum, sheetLastRowNum - 3);
				excelMakeFile.setCellValue(sheetName, "C" + sheetLastRowNum, fileInfo.path);

				excelMakeFile.setCellValue(sheetName, "D" + sheetLastRowNum, fileInfo.type);
				excelMakeFile.setCellValue(sheetName, "E" + sheetLastRowNum, fileInfo.stepBefore);
				excelMakeFile.setCellValue(sheetName, "F" + sheetLastRowNum, fileInfo.nonBefore);
				excelMakeFile.setCellValue(sheetName, "G" + sheetLastRowNum, fileInfo.commentBefore);
				excelMakeFile.setCellValue(sheetName, "H" + sheetLastRowNum,
						fileInfo.stepBefore + fileInfo.nonBefore + fileInfo.commentBefore);

				excelMakeFile.setCellValue(sheetName, "I" + sheetLastRowNum, fileInfo.status);
				excelMakeFile.setCellValue(sheetName, "J" + sheetLastRowNum, fileInfo.add);
				excelMakeFile.setCellValue(sheetName, "K" + sheetLastRowNum, fileInfo.del);
				excelMakeFile.setCellValue(sheetName, "L" + sheetLastRowNum, fileInfo.chg);

				excelMakeFile.setCellValue(sheetName, "M" + sheetLastRowNum, fileInfo.type);
				excelMakeFile.setCellValue(sheetName, "N" + sheetLastRowNum, fileInfo.stepAfter);
				excelMakeFile.setCellValue(sheetName, "O" + sheetLastRowNum, fileInfo.nonAfter);
				excelMakeFile.setCellValue(sheetName, "P" + sheetLastRowNum, fileInfo.commentAfter);
				excelMakeFile.setCellValue(sheetName, "Q" + sheetLastRowNum,
						fileInfo.stepAfter + fileInfo.nonAfter + fileInfo.commentAfter);

				setBorderStyle(excelMakeFile, sheetName, sheetLastRowNum);

            }

			int sheetLastRowNum = outputSheet.getLastRowNum() + 2;
			excelMakeFile.setCellValue(sheetName, "B" + sheetLastRowNum, sheetLastRowNum - 3);
			excelMakeFile.setCellValue(sheetName, "C" + sheetLastRowNum, "合計");

//			excelMakeFile.setCellValue(sheetName, "D" + sheetLastRowNum, fileInfo.type);
			excelMakeFile.setCellValue(sheetName, "E" + sheetLastRowNum, moduleStepBefore);
			excelMakeFile.setCellValue(sheetName, "F" + sheetLastRowNum, moduleNonBefore);
			excelMakeFile.setCellValue(sheetName, "G" + sheetLastRowNum, moduleCommentBefore);
			excelMakeFile.setCellValue(sheetName, "H" + sheetLastRowNum,
					moduleStepBefore + moduleNonBefore + moduleCommentBefore);

//			excelMakeFile.setCellValue(sheetName, "I" + sheetLastRowNum, fileInfo.status);
			excelMakeFile.setCellValue(sheetName, "J" + sheetLastRowNum, moduleAdd);
			excelMakeFile.setCellValue(sheetName, "K" + sheetLastRowNum, moduleDel);
			excelMakeFile.setCellValue(sheetName, "L" + sheetLastRowNum, moduleChg);

//			excelMakeFile.setCellValue(sheetName, "M" + sheetLastRowNum, fileInfo.type);
			excelMakeFile.setCellValue(sheetName, "N" + sheetLastRowNum, moduleStepAfter);
			excelMakeFile.setCellValue(sheetName, "O" + sheetLastRowNum, moduleNonAfter);
			excelMakeFile.setCellValue(sheetName, "P" + sheetLastRowNum, moduleCommentAfter);
			excelMakeFile.setCellValue(sheetName, "Q" + sheetLastRowNum,
					moduleStepAfter + moduleNonAfter + moduleCommentAfter);

			setBorderStyle(excelMakeFile, sheetName, sheetLastRowNum);

            // --- 输出模块汇总 ---
            System.out.println("----------------------------------------------------------------------");
            System.out.println("模块汇总 -> 新增: " + moduleAdd + " | 删除: " + moduleDel + " | 变更: " + moduleChg);
        }


        DateTimeFormatter df = DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS");
        String fileName = "ステップカウント一覧・集計".concat("_").concat(df.format(LocalDateTime.now()));
        fileName = fileName.concat(".xlsx");

        Path path = Paths.get(projectPath, outputDir, fileName);
        // 关键：创建目录（递归创建）
        Files.createDirectories(path.getParent());
        // 再写文件
        Files.write(path, excelMakeFile.getBytes());
    }



    private static void countBeforeLinesByExtension(FileInfo info, File file, List<String> lines) {
        String ext = getMainType(file);

        // 简单的策略模式
        switch (ext) {
            case "java": case "cpp": case "c": case "cs": case "Designer": case "js": case "ts":
                countBeforeByRules(info,lines, "//", "/*", "*/");
                break;
            case "xml": case "html": case "csproj":
                countBeforeByRules(info,lines, null, "<!--", "-->");
                break;
            case "py": case "properties": case "sh": case "yml":
                countBeforeByRules(info,lines, "#", null, null);
                break;
            default:
                // 未知类型：全部计入代码行，仅统计空行
                countBeforeByRules(info,lines, null, null, null);
                break;
        }
    }

    private static void countBeforeByRules(FileInfo info, List<String> lines, String singleLine, String blockStart, String blockEnd) {
        boolean inBlock = false;
        for (String line : lines) {
            String t = line.trim();
            if (t.isEmpty()) {
            	info.nonBefore++;
                continue;
            }
            if (!inBlock && blockStart != null && t.startsWith(blockStart)) {
            	info.commentBefore++;
                if (blockEnd != null && !t.endsWith(blockEnd)) inBlock = true;
                continue;
            }
            if (inBlock) {
            	info.commentBefore++;
                if (blockEnd != null && t.endsWith(blockEnd)) inBlock = false;
                continue;
            }
            if (singleLine != null && t.startsWith(singleLine)) {
            	info.commentBefore++;
                continue;
            }
            info.stepBefore++;
        }
    }

    private static void countAfterLinesByExtension(FileInfo info, File file, List<String> lines) {
//        String ext = FileUtils.getExtension(fileName);
        String ext = getMainType(file);

        // 简单的策略模式
        switch (ext) {
            case "java": case "cpp": case "c": case "cs": case "Designer": case "js": case "ts":
            	countAfterByRules(info,lines, "//", "/*", "*/");
                break;
            case "xml": case "html": case "csproj":
            	countAfterByRules(info,lines, null, "<!--", "-->");
                break;
            case "py": case "properties": case "sh": case "yml":
            	countAfterByRules(info,lines, "#", null, null);
                break;
            default:
                // 未知类型：全部计入代码行，仅统计空行
            	countAfterByRules(info,lines, null, null, null);
                break;
        }
    }

    private static void countAfterByRules(FileInfo info, List<String> lines, String singleLine, String blockStart, String blockEnd) {
        boolean inBlock = false;
        for (String line : lines) {
            String t = line.trim();
            if (t.isEmpty()) {
            	info.nonAfter++;
                continue;
            }
            if (!inBlock && blockStart != null && t.startsWith(blockStart)) {
            	info.commentAfter++;
                if (blockEnd != null && !t.endsWith(blockEnd)) inBlock = true;
                continue;
            }
            if (inBlock) {
            	info.commentAfter++;
                if (blockEnd != null && t.endsWith(blockEnd)) inBlock = false;
                continue;
            }
            if (singleLine != null && t.startsWith(singleLine)) {
            	info.commentAfter++;
                continue;
            }
            info.stepAfter++;
        }
    }

    // 辅助方法：获取相对路径映射
    private static Map<String, File> getAllFilesRelative(File baseDir) {
        Map<String, File> map = new HashMap<>();
        if (!baseDir.exists()) return map;
        List<File> files = new ArrayList<>();
        collectAllTextFiles(baseDir, files); // 修改为收集所有文本文件
        int baseLen = baseDir.getAbsolutePath().length();
        for (File f : files) map.put(f.getAbsolutePath().substring(baseLen), f);
        return map;
    }

    private static void collectAllTextFiles(File dir, List<File> list) {
        File[] files = dir.listFiles();
        if (files == null) return;
        for (File f : files) {
            if (f.isDirectory()) collectAllTextFiles(f, list);
            else {

                String ext = "";
                int i = f.getName().toLowerCase().lastIndexOf('.');
                if (i > 0) ext = f.getName().toLowerCase().substring(i).toLowerCase();

                // 过滤掉二进制文件
                if (extensions.contains(ext)) {
                    list.add(f);
                }
            }
        }
    }

	private static void setBorderStyle(ExcelMakeFile excelMakeFile, String sheetName, int sheetLastRowNum) {

		// 设置列范围 B~I
		String[] cols = { "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q" };
		for (String colLetter : cols) {
			excelMakeFile.setBorder(sheetName, colLetter + sheetLastRowNum, BorderStyle.THIN);
		}
	}

	public static String getMainType(File newFile) {
	    String name = newFile.getName();

	    int firstDot = name.indexOf(".");
	    if (firstDot == -1 || firstDot == name.length() - 1) {
	        return ""; // 没有扩展名
	    }

	    String multiExt = name.substring(firstDot + 1);

	    String[] parts = multiExt.split("\\.", 2);

	    return parts.length > 0 ? parts[0] : "";
	}
}

