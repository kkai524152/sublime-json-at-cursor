# JsonAtCursor

一个给 Sublime Text 用的小插件，用来直接格式化“光标所在位置”的 JSON 对象或数组。

## 功能

- 有选区时，优先格式化你选中的 JSON。
- 没有选区时，从光标位置向外扫描，自动找到包围光标的合法 JSON 对象或数组。
- 只替换那一段 JSON，所以很适合日志、混合文本、接口响应片段这类场景。
- 如果 JSON 前后同一行还有普通文本，会自动在 JSON 前后断行，让日志阅读更清爽。

## Windows 安装

1. 在 Sublime Text 里打开 `Preferences -> Browse Packages...`
2. 新建一个目录：`JsonAtCursor`
3. 把下面 3 个文件复制进去：
   - `json_at_cursor.py`
   - `Default.sublime-commands`
   - `Default (Windows).sublime-keymap`
   - `JsonAtCursor.sublime-settings`
4. 重启 Sublime Text，或者执行 `Tools -> Developer -> Reload Plugin`

## 使用方式

1. 把光标放到某段 JSON 的任意位置
2. 打开命令面板
3. 执行 `JSON: Format JSON At Cursor`

也可以直接按快捷键：`Ctrl+Alt+L`

## 可调配置

在 `JsonAtCursor.sublime-settings` 里可以修改：

- `indent`：缩进空格数，默认 `2`
- `sort_keys`：是否按 key 排序，默认 `false`
- `ensure_ascii`：是否把中文转成 `\\uXXXX`，默认 `false`

## 说明

- 当前针对的是标准 JSON，不支持 JSON5、单引号对象字面量等非标准写法。
- 花括号匹配时会正确跳过字符串里的 `{`、`}`、`[`、`]`，避免常见误判。
