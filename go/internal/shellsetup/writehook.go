package shellsetup

import (
	"log"
	"os"
	"path/filepath"
	"strings"
)

// writeHook mirrors shell_setup._write_hook: appends hook text to rcPath
// (creating it if missing), skipping if a Daybreak hook is already present.
func writeHook(rcPath, hook, shellName string) {
	if _, err := os.Stat(rcPath); err != nil {
		log.Printf("Config file %s not found. Creating it...", rcPath)
		if err := os.MkdirAll(filepath.Dir(rcPath), 0o755); err != nil {
			log.Printf("Failed to create config file: %v", err)
			return
		}
		f, err := os.OpenFile(rcPath, os.O_CREATE|os.O_WRONLY, 0o644)
		if err != nil {
			log.Printf("Failed to create config file: %v", err)
			return
		}
		f.Close()
	}

	content, err := os.ReadFile(rcPath)
	if err != nil {
		log.Printf("Failed to write to config file: %v", err)
		return
	}

	if strings.Contains(string(content), "daybreak/theme") {
		log.Printf("Daybreak hook already found in %s. Skipping.", rcPath)
		return
	}

	f, err := os.OpenFile(rcPath, os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		log.Printf("Failed to write to config file: %v", err)
		return
	}
	defer f.Close()
	if _, err := f.WriteString(hook); err != nil {
		log.Printf("Failed to write to config file: %v", err)
		return
	}

	log.Printf("Successfully added Daybreak hook to %s config:", shellName)
	log.Printf("  -> %s", rcPath)
	log.Printf("Restart your shell or source the file to apply changes.")
}
