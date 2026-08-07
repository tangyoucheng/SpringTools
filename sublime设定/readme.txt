在 Sublime Text 中，按下万能快捷键：Ctrl + Shift + P（唤起全局命令面板）。
在输入框中输入：Customize Color Scheme（自定义配色方案），然后直接回车。
此时，Sublime 会聪明地为你打开一个全新的左右分裂窗口：
  左边是你当前正在使用的颜色主题代码（只读）。
  右边是专门用来让你修改当前主题颜色的空白花括号 { }。
{
    "globals":
    {
        // 1. 设置选中背景为 Notepad++ 同款翠绿色
        "selection": "#C0E29E",
        // 2. 确保选中区域里的文字颜色变成深黑色，防止看不清字
        "selection_foreground": "#000000"
    }
}


在 Notepad++ 中，除了 Alt + 左键，大家最常用的键盘纵向选择快捷键是 Alt + Shift + 键盘上下方向键。
在 Sublime Text 顶部菜单栏点击：Preferences -> Key Bindings（快捷键设置）。
此时会弹出一个左右分裂的窗口：
  左边是系统默认的只读配置。
  右边是你自己的自定义配置（User）。
  把下面这段代码复制到右边的中括号 [ ] 之间（如果右边本来就有内容，记得用逗号隔开）：
[
    { "keys": ["shift+alt+up"], "command": "select_lines", "args": {"forward": false} },
    { "keys": ["shift+alt+down"], "command": "select_lines", "args": {"forward": true} }
]

3步汉化操作指南
1打开命令面板
  Windows / Linux 用户：按下快捷键 Ctrl + Shift + P。
  Mac 用户：按下快捷键 Cmd + Shift + P。
2安装包管理器（如果已经安装过，请跳过此步）
  在弹出的输入框中输入 Install Package Control，看到同名选项后回车。
  等待几秒钟，系统提示安装成功后点击“OK”。
3安装中文语言包
  再次按下 Ctrl + Shift + P（或 Cmd + Shift + P）。
  输入 Install Package，选中 Package Control: Install Package 并回车。
  在新出现的输入框中输入 ChineseLocalizations，选中这个插件并回车。

