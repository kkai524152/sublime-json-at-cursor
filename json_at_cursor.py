import json
import re

import sublime
import sublime_plugin


BRACKET_PAIRS = {
    "{": "}",
    "[": "]",
}


class FormatJsonAtCursorCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        buffer_text = self.view.substr(sublime.Region(0, self.view.size()))
        selections = list(self.view.sel())
        replacements = {}
        missing_targets = 0

        for selection in selections:
            target_region = self._resolve_target_region(buffer_text, selection)
            if target_region is None:
                missing_targets += 1
                continue

            formatted_json = self._format_region(buffer_text, target_region)
            replacements[(target_region.begin(), target_region.end())] = formatted_json

        if not replacements:
            message = "JsonAtCursor: no valid JSON object or array found at the cursor."
            sublime.status_message(message)
            sublime.error_message(message)
            return

        applied = []
        for start, end in sorted(replacements.keys(), reverse=True):
            region = sublime.Region(start, end)
            self.view.replace(edit, region, replacements[(start, end)])
            applied.append(region)

        if missing_targets:
            sublime.status_message(
                "JsonAtCursor: formatted {0} region(s); skipped {1} cursor(s) without valid JSON.".format(
                    len(applied), missing_targets
                )
            )
        else:
            sublime.status_message(
                "JsonAtCursor: formatted {0} JSON region(s).".format(len(applied))
            )

    def _resolve_target_region(self, buffer_text, selection):
        selected_region = self._trimmed_selection_region(buffer_text, selection)
        if selected_region is not None and self._is_valid_json(buffer_text[selected_region.begin():selected_region.end()]):
            return selected_region

        cursor = selection.begin()
        region = self._find_enclosing_json_region(buffer_text, cursor)
        if region is None and cursor > 0:
            region = self._find_enclosing_json_region(buffer_text, cursor - 1)
        return region

    def _trimmed_selection_region(self, buffer_text, selection):
        if selection.empty():
            return None

        start = selection.begin()
        end = selection.end()
        selected_text = buffer_text[start:end]
        stripped = selected_text.strip()
        if not stripped:
            return None

        leading = len(selected_text) - len(selected_text.lstrip())
        trailing = len(selected_text) - len(selected_text.rstrip())
        return sublime.Region(start + leading, end - trailing)

    def _find_enclosing_json_region(self, buffer_text, cursor):
        if not buffer_text:
            return None

        search_start = min(max(cursor, 0), len(buffer_text) - 1)
        best_region = None

        for start in range(search_start, -1, -1):
            if buffer_text[start] not in BRACKET_PAIRS:
                continue

            end = self._find_matching_end(buffer_text, start)
            if end is None or not (start <= cursor < end):
                continue

            candidate = buffer_text[start:end]
            if not self._is_valid_json(candidate):
                continue

            region = sublime.Region(start, end)
            if best_region is None or region.size() > best_region.size():
                best_region = region

        return best_region

    def _find_matching_end(self, buffer_text, start):
        stack = [buffer_text[start]]
        in_string = False
        escaped = False

        for index in range(start + 1, len(buffer_text)):
            char = buffer_text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char in BRACKET_PAIRS:
                stack.append(char)
                continue

            if char in BRACKET_PAIRS.values():
                if not stack:
                    return None

                expected = BRACKET_PAIRS[stack[-1]]
                if char != expected:
                    return None

                stack.pop()
                if not stack:
                    return index + 1

        return None

    def _is_valid_json(self, candidate):
        try:
            json.loads(candidate)
            return True
        except Exception:
            return False

    def _format_region(self, buffer_text, region):
        settings = sublime.load_settings("JsonAtCursor.sublime-settings")
        indent = int(settings.get("indent", 2))
        sort_keys = bool(settings.get("sort_keys", False))
        ensure_ascii = bool(settings.get("ensure_ascii", False))

        candidate = buffer_text[region.begin():region.end()]
        parsed = json.loads(candidate)
        pretty = json.dumps(
            parsed,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
        )

        line_start = buffer_text.rfind("\n", 0, region.begin()) + 1
        line_end = buffer_text.find("\n", region.end())
        if line_end == -1:
            line_end = len(buffer_text)

        line_prefix = buffer_text[line_start:region.begin()]
        line_suffix = buffer_text[region.end():line_end]
        line_indent = re.match(r"[ \t]*", buffer_text[line_start:line_end]).group(0)

        before_has_text = bool(line_prefix.strip())
        after_has_text = bool(line_suffix.strip())

        if before_has_text or after_has_text:
            block = self._indent_block(pretty, line_indent, include_first_line=True)
            leading = "\n" if before_has_text else ""
            trailing = "\n" + line_indent if after_has_text else ""
            return leading + block + trailing

        column = region.begin() - line_start
        if column <= 0:
            return self._indent_block(pretty, line_indent, include_first_line=True)

        return self._indent_block(pretty, " " * column)

    def _indent_block(self, text, prefix, include_first_line=False):
        if not prefix:
            return text

        lines = text.splitlines()
        if include_first_line:
            return prefix + lines[0] + "".join("\n" + prefix + line for line in lines[1:])

        return lines[0] + "".join("\n" + prefix + line for line in lines[1:])
