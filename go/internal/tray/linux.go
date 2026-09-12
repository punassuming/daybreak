//go:build linux

// Package tray (Linux side) ports linux_tray.py: a KDE StatusNotifierItem
// (SNI) + com.canonical.dbusmenu tray icon over D-Bus.
//
// The Python original supports two interchangeable backends (dbus-python +
// GLib, or dbus-fast + asyncio) purely because of Python packaging
// differences — one's a system package usually preinstalled on KDE, the
// other's a pure-Python pip fallback. Go has one good D-Bus library
// (godbus/dbus), so this port only needs one implementation.
//
// UNTESTED against a real Plasma session — this was ported without access
// to a Linux/KDE machine. It's modeled closely on the working Python
// implementation's D-Bus surface (same interface names, same property
// set, same menu item ids), but hasn't been verified against a real
// StatusNotifierWatcher/system tray host.
package tray

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	"github.com/godbus/dbus/v5"
	"github.com/godbus/dbus/v5/introspect"

	"daybreak/internal/orchestrator"
	"daybreak/internal/shellsetup"
)

const (
	sniIface          = "org.kde.StatusNotifierItem"
	sniWatcherService = "org.kde.StatusNotifierWatcher"
	sniWatcherPath    = "/StatusNotifierWatcher"
	sniWatcherIface   = "org.kde.StatusNotifierWatcher"
	dbusMenuIface     = "com.canonical.dbusmenu"
	propertiesIface   = "org.freedesktop.DBus.Properties"
	introspectIface   = "org.freedesktop.DBus.Introspectable"
)

// Controller mirrors linux_tray.py's LinuxTrayController.
type Controller struct {
	Orch         *orchestrator.Orchestrator
	CurrentMode  string
	CurrentTheme string
}

func NewController(orch *orchestrator.Orchestrator) *Controller {
	c := &Controller{Orch: orch}
	c.CurrentMode = orch.GetCurrentMode()
	c.CurrentTheme = orch.Config.GetModeThemeName(c.CurrentMode)
	return c
}

func titleCase(s string) string {
	if s == "" {
		return s
	}
	return strings.ToUpper(s[:1]) + s[1:]
}

func (c *Controller) TooltipText() string {
	return fmt.Sprintf("Daybreak (%s: %s)", titleCase(c.CurrentMode), c.CurrentTheme)
}

func (c *Controller) StatusText() string {
	return fmt.Sprintf("%s mode - %s", titleCase(c.CurrentMode), c.CurrentTheme)
}

func (c *Controller) ApplyMode(mode string) string {
	themeName, err := c.Orch.Apply(mode, "")
	if err != nil {
		log.Printf("Failed to apply %s mode: %v", mode, err)
		return c.CurrentTheme
	}
	c.CurrentMode = mode
	c.CurrentTheme = themeName
	log.Printf("Switched to %s mode using theme '%s'.", mode, themeName)
	return themeName
}

func (c *Controller) ToggleMode() (string, string) {
	mode, themeName, err := c.Orch.ApplyToggle("")
	if err != nil {
		log.Printf("Failed to toggle mode: %v", err)
		return c.CurrentMode, c.CurrentTheme
	}
	c.CurrentMode = mode
	c.CurrentTheme = themeName
	log.Printf("Switched to %s mode using theme '%s'.", mode, themeName)
	return mode, themeName
}

// notify mirrors LinuxTrayController._notify: a best-effort notify-send.
func (c *Controller) notify(summary, body string) {
	cmd := exec.Command("notify-send", "-a", "Daybreak", "-i", "preferences-desktop-display-color", summary, body)
	_ = cmd.Run()
}

func (c *Controller) notifyModeChange(source string) {
	c.notify(fmt.Sprintf("Daybreak: %s", titleCase(c.CurrentMode)), fmt.Sprintf("%s\nTheme: %s", source, c.CurrentTheme))
}

func (c *Controller) OpenConfig() {
	c.Orch.Config.Save()
	_ = exec.Command("xdg-open", c.Orch.Config.ConfigFile).Start()
}

func (c *Controller) RunSetup() {
	shellsetup.InstallShellHook()
}

// HandleCommand mirrors LinuxTrayController.handle_command; false means exit.
func (c *Controller) HandleCommand(id int) bool {
	switch id {
	case idToggle:
		c.ToggleMode()
		c.notifyModeChange("Source: Tray Toggle")
	case idLight:
		c.ApplyMode("light")
		c.notifyModeChange("Source: Tray -> Switch to Light")
	case idDark:
		c.ApplyMode("dark")
		c.notifyModeChange("Source: Tray -> Switch to Dark")
	case idOpenConfig:
		c.OpenConfig()
		c.notify("Daybreak: Open Config", "Source: Tray -> Open Config")
	case idRunSetup:
		c.RunSetup()
		c.notify("Daybreak: Setup", "Source: Tray -> Run Setup")
	case idExit:
		return false
	}
	return true
}

// renderSNIIconPixels mirrors linux_tray._render_sni_icon_pixels: converts
// renderModeIconPixels' BGRA output to the ARGB32 big-endian format the SNI
// IconPixmap property requires.
func renderSNIIconPixels(mode string, size int) []byte {
	bgra := RenderModeIconPixels(mode, size)
	result := make([]byte, len(bgra))
	for i := 0; i < len(bgra); i += 4 {
		result[i] = bgra[i+3]   // alpha
		result[i+1] = bgra[i+2] // red
		result[i+2] = bgra[i+1] // green
		result[i+3] = bgra[i]   // blue
	}
	return result
}

// pixmapEntry mirrors the SNI IconPixmap element type a(iiay).
type pixmapEntry struct {
	Width  int32
	Height int32
	Pixels []byte
}

// tooltipStruct mirrors the SNI ToolTip property type (sa(iiay)ss).
type tooltipStruct struct {
	IconName    string
	IconPixmap  []pixmapEntry
	Title       string
	Description string
}

// menuItem mirrors a com.canonical.dbusmenu layout item, type (ia{sv}av).
type menuItem struct {
	ID         int32
	Properties map[string]dbus.Variant
	Children   []dbus.Variant
}

// groupProperty mirrors a dbusmenu GetGroupProperties element, type (ia{sv}).
type groupProperty struct {
	ID         int32
	Properties map[string]dbus.Variant
}

type itemSpec struct {
	id          int32
	label       string
	enabled     bool
	itemType    string
	toggleType  string
	toggleState int32
}

type dbusMenuServer struct {
	controller   *Controller
	revision     uint32
	conn         *dbus.Conn
	path         dbus.ObjectPath
	updateIconFn func()
	quitFn       func()
}

func (m *dbusMenuServer) makeItem(spec itemSpec) dbus.Variant {
	props := map[string]dbus.Variant{}
	if spec.label != "" {
		props["label"] = dbus.MakeVariant(spec.label)
	}
	if !spec.enabled {
		props["enabled"] = dbus.MakeVariant(false)
	}
	if spec.itemType != "" {
		props["type"] = dbus.MakeVariant(spec.itemType)
	}
	if spec.toggleType != "" {
		props["toggle-type"] = dbus.MakeVariant(spec.toggleType)
		props["toggle-state"] = dbus.MakeVariant(spec.toggleState)
	}
	return dbus.MakeVariant(menuItem{ID: spec.id, Properties: props, Children: []dbus.Variant{}})
}

// buildRoot mirrors _DbusMenuService._build_tree / _DbusMenuInterface._build_tree.
func (m *dbusMenuServer) buildRoot() menuItem {
	mode := m.controller.CurrentMode
	lightToggle, darkToggle := int32(0), int32(0)
	if mode == "light" {
		lightToggle = 1
	} else if mode == "dark" {
		darkToggle = 1
	}

	children := []dbus.Variant{
		m.makeItem(itemSpec{id: 9000, label: m.controller.StatusText()}),
		m.makeItem(itemSpec{id: 9001, enabled: true, itemType: "separator"}),
		m.makeItem(itemSpec{id: idToggle, label: "Toggle", enabled: true}),
		m.makeItem(itemSpec{id: idLight, label: "Switch to Light", enabled: true, toggleType: "radio", toggleState: lightToggle}),
		m.makeItem(itemSpec{id: idDark, label: "Switch to Dark", enabled: true, toggleType: "radio", toggleState: darkToggle}),
		m.makeItem(itemSpec{id: 9002, enabled: true, itemType: "separator"}),
		m.makeItem(itemSpec{id: idOpenConfig, label: "Open Config", enabled: true}),
		m.makeItem(itemSpec{id: idRunSetup, label: "Run Setup", enabled: true}),
		m.makeItem(itemSpec{id: 9003, enabled: true, itemType: "separator"}),
		m.makeItem(itemSpec{id: idExit, label: "Exit", enabled: true}),
	}

	return menuItem{
		ID:         0,
		Properties: map[string]dbus.Variant{"children-display": dbus.MakeVariant("submenu")},
		Children:   children,
	}
}

func (m *dbusMenuServer) GetLayout(parentID int32, recursionDepth int32, propertyNames []string) (uint32, menuItem, *dbus.Error) {
	return m.revision, m.buildRoot(), nil
}

func (m *dbusMenuServer) GetGroupProperties(ids []int32, propertyNames []string) ([]groupProperty, *dbus.Error) {
	return []groupProperty{}, nil
}

func (m *dbusMenuServer) GetProperty(id int32, name string) (dbus.Variant, *dbus.Error) {
	return dbus.MakeVariant(""), nil
}

func (m *dbusMenuServer) Event(id int32, eventID string, data dbus.Variant, timestamp uint32) *dbus.Error {
	if eventID != "clicked" {
		return nil
	}
	if !m.controller.HandleCommand(int(id)) {
		if m.quitFn != nil {
			m.quitFn()
		}
		return nil
	}
	m.revision++
	_ = m.conn.Emit(m.path, dbusMenuIface+".LayoutUpdated", m.revision, int32(0))
	if m.updateIconFn != nil {
		m.updateIconFn()
	}
	return nil
}

func (m *dbusMenuServer) AboutToShow(id int32) (bool, *dbus.Error) {
	return false, nil
}

func (m *dbusMenuServer) AboutToShowGroup(ids []int32) ([]bool, *dbus.Error) {
	return make([]bool, len(ids)), nil
}

type sniServer struct {
	conn       *dbus.Conn
	controller *Controller
	path       dbus.ObjectPath
	menuPath   dbus.ObjectPath
}

func (s *sniServer) getAllProps() map[string]dbus.Variant {
	mode := s.controller.CurrentMode
	pixmap := []pixmapEntry{{Width: 22, Height: 22, Pixels: renderSNIIconPixels(mode, 22)}}
	return map[string]dbus.Variant{
		"Category":            dbus.MakeVariant("ApplicationStatus"),
		"Id":                  dbus.MakeVariant("daybreak"),
		"Title":               dbus.MakeVariant("Daybreak"),
		"Status":              dbus.MakeVariant("Active"),
		"IconName":            dbus.MakeVariant(""),
		"IconPixmap":          dbus.MakeVariant(pixmap),
		"AttentionIconName":   dbus.MakeVariant(""),
		"AttentionIconPixmap": dbus.MakeVariant([]pixmapEntry{}),
		"OverlayIconName":     dbus.MakeVariant(""),
		"OverlayIconPixmap":   dbus.MakeVariant([]pixmapEntry{}),
		"Menu":                dbus.MakeVariant(s.menuPath),
		"ItemIsMenu":          dbus.MakeVariant(false),
		"ToolTip":             dbus.MakeVariant(tooltipStruct{"", []pixmapEntry{}, s.controller.TooltipText(), ""}),
		"IconThemePath":       dbus.MakeVariant(""),
		"WindowId":            dbus.MakeVariant(int32(0)),
	}
}

func (s *sniServer) Get(interfaceName, propertyName string) (dbus.Variant, *dbus.Error) {
	v, ok := s.getAllProps()[propertyName]
	if !ok {
		return dbus.Variant{}, dbus.NewError("org.freedesktop.DBus.Error.InvalidArgs",
			[]interface{}{fmt.Sprintf("Property %q not found on %q", propertyName, interfaceName)})
	}
	return v, nil
}

func (s *sniServer) GetAll(interfaceName string) (map[string]dbus.Variant, *dbus.Error) {
	return s.getAllProps(), nil
}

func (s *sniServer) Set(interfaceName, propertyName string, value dbus.Variant) *dbus.Error {
	return dbus.NewError("org.freedesktop.DBus.Error.PropertyReadOnly", nil)
}

func (s *sniServer) Activate(x, y int32) *dbus.Error {
	s.controller.ToggleMode()
	s.updateIcon()
	return nil
}

func (s *sniServer) SecondaryActivate(x, y int32) *dbus.Error {
	s.controller.ToggleMode()
	s.updateIcon()
	return nil
}

func (s *sniServer) ContextMenu(x, y int32) *dbus.Error { return nil }

func (s *sniServer) Scroll(delta int32, orientation string) *dbus.Error { return nil }

func (s *sniServer) updateIcon() {
	_ = s.conn.Emit(s.path, sniIface+".NewIcon")
	_ = s.conn.Emit(s.path, sniIface+".NewToolTip")
}

const menuIntrospectXML = `
<node>
  <interface name="com.canonical.dbusmenu">
    <method name="GetLayout">
      <arg name="parentId" direction="in" type="i"/>
      <arg name="recursionDepth" direction="in" type="i"/>
      <arg name="propertyNames" direction="in" type="as"/>
      <arg name="revision" direction="out" type="u"/>
      <arg name="layout" direction="out" type="(ia{sv}av)"/>
    </method>
    <method name="GetGroupProperties">
      <arg name="ids" direction="in" type="ai"/>
      <arg name="propertyNames" direction="in" type="as"/>
      <arg name="properties" direction="out" type="a(ia{sv})"/>
    </method>
    <method name="GetProperty">
      <arg name="id" direction="in" type="i"/>
      <arg name="name" direction="in" type="s"/>
      <arg name="value" direction="out" type="v"/>
    </method>
    <method name="Event">
      <arg name="id" direction="in" type="i"/>
      <arg name="eventId" direction="in" type="s"/>
      <arg name="data" direction="in" type="v"/>
      <arg name="timestamp" direction="in" type="u"/>
    </method>
    <method name="AboutToShow">
      <arg name="id" direction="in" type="i"/>
      <arg name="needUpdate" direction="out" type="b"/>
    </method>
    <method name="AboutToShowGroup">
      <arg name="ids" direction="in" type="ai"/>
      <arg name="updatesNeeded" direction="out" type="ab"/>
    </method>
    <signal name="LayoutUpdated">
      <arg name="revision" type="u"/>
      <arg name="parentId" type="i"/>
    </signal>
    <signal name="ItemsPropertiesUpdated">
      <arg name="updatedProps" type="a(ia{sv})"/>
      <arg name="removedProps" type="a(ias)"/>
    </signal>
  </interface>
</node>`

const sniIntrospectXML = `
<node>
  <interface name="org.kde.StatusNotifierItem">
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconPixmap" type="a(iiay)" access="read"/>
    <property name="AttentionIconName" type="s" access="read"/>
    <property name="AttentionIconPixmap" type="a(iiay)" access="read"/>
    <property name="OverlayIconName" type="s" access="read"/>
    <property name="OverlayIconPixmap" type="a(iiay)" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
    <property name="IconThemePath" type="s" access="read"/>
    <property name="WindowId" type="i" access="read"/>
    <method name="Activate">
      <arg name="x" direction="in" type="i"/>
      <arg name="y" direction="in" type="i"/>
    </method>
    <method name="SecondaryActivate">
      <arg name="x" direction="in" type="i"/>
      <arg name="y" direction="in" type="i"/>
    </method>
    <method name="ContextMenu">
      <arg name="x" direction="in" type="i"/>
      <arg name="y" direction="in" type="i"/>
    </method>
    <method name="Scroll">
      <arg name="delta" direction="in" type="i"/>
      <arg name="orientation" direction="in" type="s"/>
    </method>
    <signal name="NewIcon"/>
    <signal name="NewToolTip"/>
    <signal name="NewStatus">
      <arg name="status" type="s"/>
    </signal>
  </interface>
</node>`

// Run mirrors linux_tray.run_linux_tray (minus the dual dbus-python/
// dbus-fast backend selection — see the package doc comment).
func Run(orch *orchestrator.Orchestrator) error {
	conn, err := dbus.ConnectSessionBus()
	if err != nil {
		return fmt.Errorf("failed to connect to session bus: %w", err)
	}
	defer conn.Close()

	serviceName := fmt.Sprintf("org.kde.StatusNotifierItem-%d-1", os.Getpid())
	reply, err := conn.RequestName(serviceName, dbus.NameFlagDoNotQueue)
	if err != nil {
		return fmt.Errorf("failed to request bus name %s: %w", serviceName, err)
	}
	if reply != dbus.RequestNameReplyPrimaryOwner {
		return fmt.Errorf("could not become primary owner of %s", serviceName)
	}

	controller := NewController(orch)
	menuPath := dbus.ObjectPath("/MenuBar")
	sniPath := dbus.ObjectPath("/StatusNotifierItem")

	quit := make(chan struct{})
	sni := &sniServer{conn: conn, controller: controller, path: sniPath, menuPath: menuPath}
	menu := &dbusMenuServer{
		controller:   controller,
		revision:     1,
		conn:         conn,
		path:         menuPath,
		updateIconFn: sni.updateIcon,
		quitFn:       func() { close(quit) },
	}

	if err := conn.Export(menu, menuPath, dbusMenuIface); err != nil {
		return fmt.Errorf("failed to export dbusmenu: %w", err)
	}
	if err := conn.Export(introspect.Introspectable(menuIntrospectXML), menuPath, introspectIface); err != nil {
		return fmt.Errorf("failed to export dbusmenu introspection: %w", err)
	}

	if err := conn.Export(sni, sniPath, sniIface); err != nil {
		return fmt.Errorf("failed to export StatusNotifierItem: %w", err)
	}
	if err := conn.Export(sni, sniPath, propertiesIface); err != nil {
		return fmt.Errorf("failed to export DBus.Properties: %w", err)
	}
	if err := conn.Export(introspect.Introspectable(sniIntrospectXML), sniPath, introspectIface); err != nil {
		return fmt.Errorf("failed to export SNI introspection: %w", err)
	}

	registerWithWatcher := func() {
		call := conn.Object(sniWatcherService, sniWatcherPath).Call(sniWatcherIface+".RegisterStatusNotifierItem", 0, serviceName)
		if call.Err != nil {
			log.Printf("Could not register with StatusNotifierWatcher: %v", call.Err)
		}
	}
	registerWithWatcher()

	if err := conn.AddMatchSignal(
		dbus.WithMatchInterface("org.freedesktop.DBus"),
		dbus.WithMatchMember("NameOwnerChanged"),
		dbus.WithMatchArg(0, sniWatcherService),
	); err == nil {
		signalCh := make(chan *dbus.Signal, 10)
		conn.Signal(signalCh)
		go func() {
			for sig := range signalCh {
				if len(sig.Body) >= 3 {
					if newOwner, ok := sig.Body[2].(string); ok && newOwner != "" {
						registerWithWatcher()
					}
				}
			}
		}()
	}

	log.Printf("Daybreak tray is running.")
	<-quit
	_, _ = conn.ReleaseName(serviceName)
	return nil
}
