// Package shellsetup ports shell_setup.py: installing shell hooks/launchers
// (daybreak setup) and refreshing Daybreak-owned generated artifacts.
package shellsetup

import "strings"

// normalizeIntegrationsSectionText mirrors
// shell_setup._normalize_integrations_section_text: collapses any duplicate
// [integrations] blocks in a config.toml into one, de-duplicating keys
// (last write wins, insertion order otherwise preserved) and reinserting the
// block where the first occurrence was found.
func normalizeIntegrationsSectionText(content string) string {
	lines := strings.Split(content, "\n")
	var outputLines []string
	integrations := map[string]string{}
	var integrationsOrder []string
	insertAt := -1
	inIntegrations := false

	setIntegration := func(key, rhs string) {
		if key == "" {
			return
		}
		if _, exists := integrations[key]; exists {
			for i, k := range integrationsOrder {
				if k == key {
					integrationsOrder = append(integrationsOrder[:i], integrationsOrder[i+1:]...)
					break
				}
			}
		}
		integrations[key] = rhs
		integrationsOrder = append(integrationsOrder, key)
	}

	for _, line := range lines {
		stripped := strings.TrimSpace(line)
		if strings.HasPrefix(stripped, "[") && strings.HasSuffix(stripped, "]") {
			sectionName := strings.TrimSpace(stripped[1 : len(stripped)-1])
			if sectionName == "integrations" {
				inIntegrations = true
				if insertAt == -1 {
					insertAt = len(outputLines)
				}
				continue
			}
			inIntegrations = false
			outputLines = append(outputLines, line)
			continue
		}

		if inIntegrations {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				key := strings.TrimSpace(parts[0])
				rhs := strings.TrimSpace(parts[1])
				if key != "" && rhs != "" {
					setIntegration(key, rhs)
				}
			}
			continue
		}

		outputLines = append(outputLines, line)
	}

	if len(integrations) == 0 {
		if strings.HasSuffix(content, "\n") {
			return content
		}
		return content + "\n"
	}

	if insertAt == -1 {
		insertAt = len(outputLines)
	}

	var block []string
	if insertAt > 0 && strings.TrimSpace(outputLines[insertAt-1]) != "" {
		block = append(block, "")
	}
	block = append(block, "[integrations]")
	for _, key := range integrationsOrder {
		block = append(block, key+" = "+integrations[key])
	}
	if insertAt < len(outputLines) && strings.TrimSpace(outputLines[insertAt]) != "" {
		block = append(block, "")
	}

	normalizedLines := append(append(append([]string{}, outputLines[:insertAt]...), block...), outputLines[insertAt:]...)
	return strings.TrimRight(strings.Join(normalizedLines, "\n"), "\n\r \t") + "\n"
}
