// Package terminal ports adapters/terminal/*.py and terminals/*.py: the
// per-application "recolor this terminal/editor" integrations.
package terminal

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
)

// LoadJSONCFile mirrors jsonc.load_jsonc_file.
func LoadJSONCFile(path string) (map[string]any, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return ParseJSONC(string(raw))
}

// DumpJSONFile mirrors jsonc.dump_json_file.
//
// Note: unlike the Python version (which preserves original key insertion
// order via dict), Go's encoding/json sorts map keys alphabetically on
// marshal, so re-written files may reorder keys relative to what a user
// hand-edited. Values are preserved exactly; only key order can differ.
func DumpJSONFile(path string, data map[string]any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	out, err := json.MarshalIndent(data, "", "    ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}

// ParseJSONC mirrors jsonc.parse_jsonc.
func ParseJSONC(text string) (map[string]any, error) {
	stripped := stripComments(text)
	stripped = removeTrailingCommas(stripped)
	var data map[string]any
	if err := json.Unmarshal([]byte(stripped), &data); err != nil {
		return nil, err
	}
	return data, nil
}

// stripComments mirrors jsonc._strip_comments: a hand-rolled scanner that
// removes // and /* */ comments while respecting string literals.
func stripComments(text string) string {
	runes := []rune(text)
	length := len(runes)
	result := make([]rune, 0, length)

	inString := false
	inLineComment := false
	inBlockComment := false
	escaped := false

	i := 0
	for i < length {
		ch := runes[i]
		var nxt rune
		if i+1 < length {
			nxt = runes[i+1]
		}

		if inLineComment {
			if ch == '\n' {
				inLineComment = false
				result = append(result, ch)
			}
			i++
			continue
		}

		if inBlockComment {
			if ch == '*' && nxt == '/' {
				inBlockComment = false
				i += 2
				continue
			}
			if ch == '\n' {
				result = append(result, ch)
			}
			i++
			continue
		}

		if inString {
			result = append(result, ch)
			if escaped {
				escaped = false
			} else if ch == '\\' {
				escaped = true
			} else if ch == '"' {
				inString = false
			}
			i++
			continue
		}

		if ch == '/' && nxt == '/' {
			inLineComment = true
			i += 2
			continue
		}
		if ch == '/' && nxt == '*' {
			inBlockComment = true
			i += 2
			continue
		}
		if ch == '"' {
			inString = true
		}

		result = append(result, ch)
		i++
	}

	return string(result)
}

var trailingCommaRE = regexp.MustCompile(`,(\s*[}\]])`)

// removeTrailingCommas mirrors jsonc._remove_trailing_commas.
func removeTrailingCommas(text string) string {
	for {
		next := trailingCommaRE.ReplaceAllString(text, "$1")
		if next == text {
			return text
		}
		text = next
	}
}
