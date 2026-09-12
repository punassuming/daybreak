package terminal

import "strings"

// upsertTOMLKey sets `key = "value"` inside `[section]` in a TOML document,
// preserving everything else in the file byte-for-byte — including
// comments and unrelated sections — unlike a full parse+marshal round trip
// (which is why config files like herdr's or Codex's, that are meant to be
// hand-edited and heavily commented, are patched this way rather than
// loaded through a TOML library). If the section exists, an existing
// `key = ...` line inside it is replaced in place; otherwise the key is
// inserted right after the section header. If the section doesn't exist at
// all, it's appended at the end of the file.
func upsertTOMLKey(content, section, key, value string) string {
	lines := strings.Split(content, "\n")
	sectionHeader := "[" + section + "]"

	sectionStart := -1
	for i, line := range lines {
		if strings.TrimSpace(line) == sectionHeader {
			sectionStart = i
			break
		}
	}

	newKeyLine := key + ` = "` + value + `"`

	if sectionStart == -1 {
		out := strings.Join(lines, "\n")
		out = strings.TrimRight(out, "\n\r \t")
		if out != "" {
			out += "\n\n"
		}
		out += sectionHeader + "\n" + newKeyLine + "\n"
		return out
	}

	sectionEnd := len(lines)
	for i := sectionStart + 1; i < len(lines); i++ {
		trimmed := strings.TrimSpace(lines[i])
		if strings.HasPrefix(trimmed, "[") && strings.HasSuffix(trimmed, "]") {
			sectionEnd = i
			break
		}
	}

	for i := sectionStart + 1; i < sectionEnd; i++ {
		trimmed := strings.TrimSpace(lines[i])
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}
		parts := strings.SplitN(trimmed, "=", 2)
		if len(parts) == 2 && strings.TrimSpace(parts[0]) == key {
			lines[i] = newKeyLine
			return strings.Join(lines, "\n")
		}
	}

	out := make([]string, 0, len(lines)+1)
	out = append(out, lines[:sectionStart+1]...)
	out = append(out, newKeyLine)
	out = append(out, lines[sectionStart+1:]...)
	return strings.Join(out, "\n")
}
