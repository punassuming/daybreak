package shellsetup

import (
	"strings"
	"testing"
)

func TestNormalizeIntegrationsSectionTextDedupesSections(t *testing.T) {
	content := `schema_version = 2

[theme]
active = "Nord"

[integrations]
neovim_dark_scheme = "nord"

[integrations]
windows_terminal_dark_scheme = "One Half Dark"

[integrations]
neovim_dark_scheme = "onedark"
`
	normalized := normalizeIntegrationsSectionText(content)

	if got := strings.Count(normalized, "[integrations]"); got != 1 {
		t.Errorf("[integrations] count = %d, want 1\n%s", got, normalized)
	}
	if !strings.Contains(normalized, `neovim_dark_scheme = "onedark"`) {
		t.Error("expected neovim_dark_scheme = \"onedark\" in output")
	}
	if !strings.Contains(normalized, `windows_terminal_dark_scheme = "One Half Dark"`) {
		t.Error("expected windows_terminal_dark_scheme = \"One Half Dark\" in output")
	}
	if got := strings.Count(normalized, `neovim_dark_scheme = "onedark"`); got != 1 {
		t.Errorf(`count of neovim_dark_scheme = "onedark" = %d, want 1`, got)
	}
}

func TestNormalizeIntegrationsSectionTextNoOpWhenNoIntegrations(t *testing.T) {
	content := "schema_version = 2\n\n[theme]\nactive = \"Nord\"\n"
	if got := normalizeIntegrationsSectionText(content); got != content {
		t.Errorf("expected no-op passthrough, got:\n%s", got)
	}
}
