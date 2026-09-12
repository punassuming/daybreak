package terminal

import (
	"strings"
	"testing"
)

func TestUpsertTOMLKeyReplacesExistingKey(t *testing.T) {
	content := "onboarding = false\n\n[theme]\n# comment\nname = \"catppuccin\"\nauto_switch = false\n"
	got := upsertTOMLKey(content, "theme", "name", "nord")

	if !strings.Contains(got, `name = "nord"`) {
		t.Errorf("expected name = \"nord\", got:\n%s", got)
	}
	if strings.Contains(got, `name = "catppuccin"`) {
		t.Errorf("old value should be gone, got:\n%s", got)
	}
	if !strings.Contains(got, "# comment") {
		t.Error("expected surrounding comment to be preserved")
	}
	if !strings.Contains(got, "auto_switch = false") {
		t.Error("expected unrelated key in the same section to be preserved")
	}
}

func TestUpsertTOMLKeyInsertsMissingKeyIntoExistingSection(t *testing.T) {
	content := "[theme]\nauto_switch = false\n"
	got := upsertTOMLKey(content, "theme", "name", "nord")

	if !strings.Contains(got, `name = "nord"`) {
		t.Errorf("expected name to be inserted, got:\n%s", got)
	}
	if !strings.Contains(got, "auto_switch = false") {
		t.Error("expected existing key to be preserved")
	}
}

func TestUpsertTOMLKeyAppendsMissingSection(t *testing.T) {
	content := "schema_version = 2\n"
	got := upsertTOMLKey(content, "tui", "theme", "gruvbox-dark")

	if !strings.Contains(got, "[tui]") {
		t.Errorf("expected [tui] section to be appended, got:\n%s", got)
	}
	if !strings.Contains(got, `theme = "gruvbox-dark"`) {
		t.Errorf("expected theme key, got:\n%s", got)
	}
	if !strings.Contains(got, "schema_version = 2") {
		t.Error("expected original content to be preserved")
	}
}

func TestUpsertTOMLKeyDoesNotBleedIntoNextSection(t *testing.T) {
	content := "[flavor]\ndark = \"old-dark\"\n\n[manager]\nsort_by = \"alphabetical\"\n"
	got := upsertTOMLKey(content, "flavor", "light", "catppuccin-latte")

	if !strings.Contains(got, `light = "catppuccin-latte"`) {
		t.Errorf("expected light key inserted in [flavor], got:\n%s", got)
	}
	flavorEnd := strings.Index(got, "[manager]")
	lightIdx := strings.Index(got, "light =")
	if flavorEnd == -1 || lightIdx == -1 || lightIdx > flavorEnd {
		t.Errorf("expected light key to land inside [flavor], before [manager], got:\n%s", got)
	}
}
