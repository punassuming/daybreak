import logging
import os
import platform
import subprocess

logger = logging.getLogger("daybreak")

ID_TOGGLE = 1001
ID_LIGHT = 1002
ID_DARK = 1003
ID_EXIT = 1004
ID_OPEN_CONFIG = 1005
ID_RUN_SETUP = 1006

_SNI_IFACE = "org.kde.StatusNotifierItem"
_SNI_WATCHER_SERVICE = "org.kde.StatusNotifierWatcher"
_SNI_WATCHER_PATH = "/StatusNotifierWatcher"
_SNI_WATCHER_IFACE = "org.kde.StatusNotifierWatcher"
_DBUSMENU_IFACE = "com.canonical.dbusmenu"
_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"


def _render_sni_icon_pixels(mode: str, size: int = 22) -> bytes:
    """Render icon pixels in ARGB32 big-endian format required by SNI IconPixmap."""
    from daybreak.windows_tray import _render_mode_icon_pixels

    bgra = _render_mode_icon_pixels(mode, size)
    result = bytearray(len(bgra))
    for i in range(0, len(bgra), 4):
        result[i] = bgra[i + 3]      # alpha
        result[i + 1] = bgra[i + 2]  # red
        result[i + 2] = bgra[i + 1]  # green
        result[i + 3] = bgra[i]      # blue
    return bytes(result)


def _encode_pixmap_for_dbus(pixels: bytes, size: int):
    """Wrap icon pixels in the SNI IconPixmap DBus type a(iiay) for dbus-python."""
    import dbus

    data = dbus.Array([dbus.Byte(b) for b in pixels], signature="y")
    struct = dbus.Struct([dbus.Int32(size), dbus.Int32(size), data], signature="iiay")
    return dbus.Array([struct], signature="(iiay)")


class LinuxTrayController:
    """Tray controller for Linux — mirrors TrayController from windows_tray but uses xdg-open."""

    def __init__(self, orchestrator=None):
        from daybreak.cli.runtime import build_orchestrator
        from daybreak.config import config

        self._config = config
        self.orchestrator = orchestrator or build_orchestrator()
        self.current_mode = self.orchestrator.get_current_mode()
        self.current_theme = config.get_mode_theme_name(self.current_mode)

    def tooltip_text(self) -> str:
        return f"Daybreak ({self.current_mode.title()}: {self.current_theme})"

    def status_text(self) -> str:
        return f"{self.current_mode.title()} mode - {self.current_theme}"

    def apply_mode(self, mode: str):
        theme_name = self.orchestrator.apply(mode)
        self.current_mode = mode
        self.current_theme = theme_name
        logger.info(f"Switched to {mode} mode using theme '{theme_name}'.")
        return theme_name

    def toggle_mode(self):
        mode, theme_name = self.orchestrator.apply_toggle()
        self.current_mode = mode
        self.current_theme = theme_name
        logger.info(f"Switched to {mode} mode using theme '{theme_name}'.")
        return mode, theme_name

    def open_config(self):
        self._config.save()
        subprocess.Popen(["xdg-open", str(self._config.config_file)])

    def run_setup(self):
        from daybreak.shell_setup import install_shell_hook

        install_shell_hook()

    def handle_command(self, command_id: int) -> bool:
        if command_id == ID_TOGGLE:
            self.toggle_mode()
            return True
        if command_id == ID_LIGHT:
            self.apply_mode("light")
            return True
        if command_id == ID_DARK:
            self.apply_mode("dark")
            return True
        if command_id == ID_OPEN_CONFIG:
            self.open_config()
            return True
        if command_id == ID_RUN_SETUP:
            self.run_setup()
            return True
        if command_id == ID_EXIT:
            return False
        return True


# ---------------------------------------------------------------------------
# Backend: dbus-python + GLib (C extension, usually pre-installed on KDE)
# ---------------------------------------------------------------------------

def _run_tray_dbus_python():
    import dbus
    import dbus.bus
    import dbus.service
    import dbus.mainloop.glib
    from gi.repository import GLib

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    class _DbusMenuService(dbus.service.Object):
        def __init__(self, bus, path, controller):
            dbus.service.Object.__init__(self, bus, path)
            self._controller = controller
            self._revision = 1
            self._mainloop = None
            self._sni_svc = None

        def _build_item(self, item_id, label=None, enabled=True, item_type=None,
                        toggle_type=None, toggle_state=0):
            props = {}
            if label is not None:
                props["label"] = dbus.String(label)
            if not enabled:
                props["enabled"] = dbus.Boolean(False)
            if item_type:
                props["type"] = dbus.String(item_type)
            if toggle_type:
                props["toggle-type"] = dbus.String(toggle_type)
                props["toggle-state"] = dbus.Int32(toggle_state)
            return dbus.Struct(
                [dbus.Int32(item_id),
                 dbus.Dictionary(props, signature="sv"),
                 dbus.Array([], signature="v")],
                signature="ia{sv}av",
                variant_level=1,
            )

        def _build_tree(self):
            mode = self._controller.current_mode
            children = dbus.Array(
                [
                    self._build_item(9000, self._controller.status_text(), enabled=False),
                    self._build_item(9001, item_type="separator"),
                    self._build_item(ID_TOGGLE, "Toggle"),
                    self._build_item(ID_LIGHT, "Switch to Light",
                                     toggle_type="radio",
                                     toggle_state=1 if mode == "light" else 0),
                    self._build_item(ID_DARK, "Switch to Dark",
                                     toggle_type="radio",
                                     toggle_state=1 if mode == "dark" else 0),
                    self._build_item(9002, item_type="separator"),
                    self._build_item(ID_OPEN_CONFIG, "Open Config"),
                    self._build_item(ID_RUN_SETUP, "Run Setup"),
                    self._build_item(9003, item_type="separator"),
                    self._build_item(ID_EXIT, "Exit"),
                ],
                signature="v",
            )
            root_props = dbus.Dictionary(
                {"children-display": dbus.String("submenu")}, signature="sv"
            )
            return dbus.Struct(
                [dbus.Int32(0), root_props, children], signature="ia{sv}av"
            )

        @dbus.service.method(_DBUSMENU_IFACE, in_signature="iias", out_signature="u(ia{sv}av)")
        def GetLayout(self, parentId, recursionDepth, propertyNames):
            return (dbus.UInt32(self._revision), self._build_tree())

        @dbus.service.method(_DBUSMENU_IFACE, in_signature="aias", out_signature="a(ia{sv})")
        def GetGroupProperties(self, ids, propertyNames):
            return dbus.Array([], signature="(ia{sv})")

        @dbus.service.method(_DBUSMENU_IFACE, in_signature="is", out_signature="v")
        def GetProperty(self, item_id, name):
            return dbus.String("", variant_level=1)

        @dbus.service.method(_DBUSMENU_IFACE, in_signature="isvu")
        def Event(self, item_id, event_id, data, timestamp):
            if event_id != "clicked":
                return
            should_continue = self._controller.handle_command(int(item_id))
            if not should_continue:
                if self._mainloop:
                    GLib.idle_add(self._mainloop.quit)
                return
            self._revision += 1
            self.LayoutUpdated(dbus.UInt32(self._revision), dbus.Int32(0))
            if self._sni_svc:
                self._sni_svc.update_icon()

        @dbus.service.method(_DBUSMENU_IFACE, in_signature="i", out_signature="b")
        def AboutToShow(self, item_id):
            return False

        @dbus.service.method(_DBUSMENU_IFACE, in_signature="ai", out_signature="ab")
        def AboutToShowGroup(self, ids):
            return dbus.Array([False] * len(ids), signature="b")

        @dbus.service.signal(_DBUSMENU_IFACE, signature="ui")
        def LayoutUpdated(self, revision, parentId):
            pass

        @dbus.service.signal(_DBUSMENU_IFACE, signature="a(ia{sv})a(ias)")
        def ItemsPropertiesUpdated(self, updatedProps, removedProps):
            pass

    class _StatusNotifierItemService(dbus.service.Object):
        def __init__(self, bus, path, controller, menu_path):
            dbus.service.Object.__init__(self, bus, path)
            self._controller = controller
            self._menu_path = menu_path
            self._pixmaps = {
                "light": _encode_pixmap_for_dbus(_render_sni_icon_pixels("light"), 22),
                "dark": _encode_pixmap_for_dbus(_render_sni_icon_pixels("dark"), 22),
            }

        def _get_all_props(self):
            mode = self._controller.current_mode
            return {
                "Category": dbus.String("ApplicationStatus"),
                "Id": dbus.String("daybreak"),
                "Title": dbus.String("Daybreak"),
                "Status": dbus.String("Active"),
                "IconName": dbus.String(""),
                "IconPixmap": self._pixmaps[mode],
                "AttentionIconName": dbus.String(""),
                "AttentionIconPixmap": dbus.Array([], signature="(iiay)"),
                "OverlayIconName": dbus.String(""),
                "OverlayIconPixmap": dbus.Array([], signature="(iiay)"),
                "Menu": dbus.ObjectPath(self._menu_path),
                "ItemIsMenu": dbus.Boolean(False),
                "ToolTip": dbus.Struct(
                    [dbus.String(""),
                     dbus.Array([], signature="(iiay)"),
                     dbus.String(self._controller.tooltip_text()),
                     dbus.String("")],
                    signature="sa(iiay)ss",
                ),
                "IconThemePath": dbus.String(""),
                "WindowId": dbus.Int32(0),
            }

        @dbus.service.method(_PROPERTIES_IFACE, in_signature="ss", out_signature="v")
        def Get(self, interface_name, property_name):
            val = self._get_all_props().get(property_name)
            if val is None:
                raise dbus.exceptions.DBusException(
                    f"Property {property_name!r} not found on {interface_name!r}",
                    name="org.freedesktop.DBus.Error.InvalidArgs",
                )
            return val

        @dbus.service.method(_PROPERTIES_IFACE, in_signature="s", out_signature="a{sv}")
        def GetAll(self, interface_name):
            return dbus.Dictionary(self._get_all_props(), signature="sv")

        @dbus.service.method(_SNI_IFACE, in_signature="ii")
        def Activate(self, x, y):
            self._controller.toggle_mode()
            self.update_icon()

        @dbus.service.method(_SNI_IFACE, in_signature="ii")
        def SecondaryActivate(self, x, y):
            self._controller.toggle_mode()
            self.update_icon()

        @dbus.service.method(_SNI_IFACE, in_signature="ii")
        def ContextMenu(self, x, y):
            pass

        @dbus.service.method(_SNI_IFACE, in_signature="is")
        def Scroll(self, delta, orientation):
            pass

        def update_icon(self):
            self.NewIcon()
            self.NewToolTip()

        @dbus.service.signal(_SNI_IFACE)
        def NewIcon(self):
            pass

        @dbus.service.signal(_SNI_IFACE)
        def NewToolTip(self):
            pass

        @dbus.service.signal(_SNI_IFACE, signature="s")
        def NewStatus(self, status):
            pass

    bus = dbus.SessionBus()
    service_name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
    bus.request_name(service_name, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)

    controller = LinuxTrayController()
    menu_path = "/MenuBar"
    sni_path = "/StatusNotifierItem"

    menu_svc = _DbusMenuService(bus, menu_path, controller)
    sni_svc = _StatusNotifierItemService(bus, sni_path, controller, menu_path)
    menu_svc._sni_svc = sni_svc

    try:
        watcher_obj = bus.get_object(_SNI_WATCHER_SERVICE, _SNI_WATCHER_PATH)
        watcher_iface = dbus.Interface(watcher_obj, _SNI_WATCHER_IFACE)
        watcher_iface.RegisterStatusNotifierItem(service_name)
    except dbus.DBusException as exc:
        logger.warning(f"Could not register with StatusNotifierWatcher: {exc}")

    mainloop = GLib.MainLoop()
    menu_svc._mainloop = mainloop

    def _on_name_owner_changed(name, old_owner, new_owner):
        if new_owner:
            try:
                obj = bus.get_object(_SNI_WATCHER_SERVICE, _SNI_WATCHER_PATH)
                dbus.Interface(obj, _SNI_WATCHER_IFACE).RegisterStatusNotifierItem(service_name)
            except dbus.DBusException:
                pass

    bus.add_signal_receiver(
        _on_name_owner_changed,
        signal_name="NameOwnerChanged",
        dbus_interface="org.freedesktop.DBus",
        arg0=_SNI_WATCHER_SERVICE,
    )

    try:
        mainloop.run()
    finally:
        try:
            bus.release_name(service_name)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Backend: dbus-fast (pure Python, pip install dbus-fast)
# ---------------------------------------------------------------------------

async def _run_tray_dbus_fast():
    import asyncio
    from dbus_fast.aio import MessageBus
    from dbus_fast.service import ServiceInterface, method, signal, dbus_property
    from dbus_fast.constants import BusType, PropertyAccess
    from dbus_fast import Variant

    stop_event = asyncio.Event()

    class _DbusMenuInterface(ServiceInterface):
        def __init__(self, controller):
            super().__init__(_DBUSMENU_IFACE)
            self._controller = controller
            self._revision = 1
            self._sni_iface = None

        def _make_item(self, item_id, label=None, enabled=True, item_type=None,
                       toggle_type=None, toggle_state=0):
            props = {}
            if label is not None:
                props["label"] = Variant("s", label)
            if not enabled:
                props["enabled"] = Variant("b", False)
            if item_type:
                props["type"] = Variant("s", item_type)
            if toggle_type:
                props["toggle-type"] = Variant("s", toggle_type)
                props["toggle-state"] = Variant("i", toggle_state)
            return Variant("(ia{sv}av)", [item_id, props, []])

        def _build_tree(self):
            mode = self._controller.current_mode
            children = [
                self._make_item(9000, self._controller.status_text(), enabled=False),
                self._make_item(9001, item_type="separator"),
                self._make_item(ID_TOGGLE, "Toggle"),
                self._make_item(ID_LIGHT, "Switch to Light",
                                toggle_type="radio",
                                toggle_state=1 if mode == "light" else 0),
                self._make_item(ID_DARK, "Switch to Dark",
                                toggle_type="radio",
                                toggle_state=1 if mode == "dark" else 0),
                self._make_item(9002, item_type="separator"),
                self._make_item(ID_OPEN_CONFIG, "Open Config"),
                self._make_item(ID_RUN_SETUP, "Run Setup"),
                self._make_item(9003, item_type="separator"),
                self._make_item(ID_EXIT, "Exit"),
            ]
            root_props = {"children-display": Variant("s", "submenu")}
            return [0, root_props, children]

        @method()
        def GetLayout(self, parentId: "i", recursionDepth: "i", propertyNames: "as") -> "u(ia{sv}av)":
            return [self._revision, self._build_tree()]

        @method()
        def GetGroupProperties(self, ids: "ai", propertyNames: "as") -> "a(ia{sv})":
            return []

        @method()
        def GetProperty(self, item_id: "i", name: "s") -> "v":
            return Variant("s", "")

        @method()
        def Event(self, item_id: "i", event_id: "s", data: "v", timestamp: "u") -> None:
            if event_id != "clicked":
                return
            should_continue = self._controller.handle_command(int(item_id))
            if not should_continue:
                stop_event.set()
                return
            self._revision += 1
            self.LayoutUpdated(self._revision, 0)
            if self._sni_iface:
                self._sni_iface.NewIcon()
                self._sni_iface.NewToolTip()

        @method()
        def AboutToShow(self, item_id: "i") -> "b":
            return False

        @method()
        def AboutToShowGroup(self, ids: "ai") -> "ab":
            return [False] * len(ids)

        @signal()
        def LayoutUpdated(self, revision: "u", parentId: "i") -> None:
            pass

        @signal()
        def ItemsPropertiesUpdated(self, updatedProps: "a(ia{sv})", removedProps: "a(ias)") -> None:
            pass

    class _SniInterface(ServiceInterface):
        def __init__(self, controller, menu_path):
            super().__init__(_SNI_IFACE)
            self._controller = controller
            self._menu_path = menu_path

        def _pixmap(self):
            pixels = _render_sni_icon_pixels(self._controller.current_mode, 22)
            return [[22, 22, pixels]]

        @dbus_property(access=PropertyAccess.READ)
        def Category(self) -> "s":
            return "ApplicationStatus"

        @dbus_property(access=PropertyAccess.READ)
        def Id(self) -> "s":
            return "daybreak"

        @dbus_property(access=PropertyAccess.READ)
        def Title(self) -> "s":
            return "Daybreak"

        @dbus_property(access=PropertyAccess.READ)
        def Status(self) -> "s":
            return "Active"

        @dbus_property(access=PropertyAccess.READ)
        def IconName(self) -> "s":
            return ""

        @dbus_property(access=PropertyAccess.READ)
        def IconPixmap(self) -> "a(iiay)":
            return self._pixmap()

        @dbus_property(access=PropertyAccess.READ)
        def AttentionIconName(self) -> "s":
            return ""

        @dbus_property(access=PropertyAccess.READ)
        def AttentionIconPixmap(self) -> "a(iiay)":
            return []

        @dbus_property(access=PropertyAccess.READ)
        def OverlayIconName(self) -> "s":
            return ""

        @dbus_property(access=PropertyAccess.READ)
        def OverlayIconPixmap(self) -> "a(iiay)":
            return []

        @dbus_property(access=PropertyAccess.READ)
        def Menu(self) -> "o":
            return self._menu_path

        @dbus_property(access=PropertyAccess.READ)
        def ItemIsMenu(self) -> "b":
            return False

        @dbus_property(access=PropertyAccess.READ)
        def ToolTip(self) -> "(sa(iiay)ss)":
            return ["", [], self._controller.tooltip_text(), ""]

        @dbus_property(access=PropertyAccess.READ)
        def IconThemePath(self) -> "s":
            return ""

        @dbus_property(access=PropertyAccess.READ)
        def WindowId(self) -> "i":
            return 0

        @method()
        def Activate(self, x: "i", y: "i") -> None:
            self._controller.toggle_mode()
            self.NewIcon()
            self.NewToolTip()

        @method()
        def SecondaryActivate(self, x: "i", y: "i") -> None:
            self._controller.toggle_mode()
            self.NewIcon()
            self.NewToolTip()

        @method()
        def ContextMenu(self, x: "i", y: "i") -> None:
            pass

        @method()
        def Scroll(self, delta: "i", orientation: "s") -> None:
            pass

        @signal()
        def NewIcon(self) -> None:
            pass

        @signal()
        def NewToolTip(self) -> None:
            pass

        @signal()
        def NewStatus(self, status: "s") -> None:
            pass

    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    service_name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
    await bus.request_name(service_name)

    controller = LinuxTrayController()
    menu_iface = _DbusMenuInterface(controller)
    sni_iface = _SniInterface(controller, "/MenuBar")
    menu_iface._sni_iface = sni_iface

    bus.export("/MenuBar", menu_iface)
    bus.export("/StatusNotifierItem", sni_iface)

    try:
        intr = await bus.introspect(_SNI_WATCHER_SERVICE, _SNI_WATCHER_PATH)
        watcher_proxy = bus.get_proxy_object(_SNI_WATCHER_SERVICE, _SNI_WATCHER_PATH, intr)
        watcher = watcher_proxy.get_interface(_SNI_WATCHER_IFACE)
        await watcher.call_register_status_notifier_item(service_name)
    except Exception as exc:
        logger.warning(f"Could not register with StatusNotifierWatcher: {exc}")

    await stop_event.wait()
    bus.disconnect()


# ---------------------------------------------------------------------------
# Entry point — tries dbus-python first, then dbus-fast
# ---------------------------------------------------------------------------

def run_linux_tray():
    if platform.system() != "Linux":
        raise RuntimeError("Linux tray mode is only available on Linux.")

    # Preferred: dbus-python + GLib (C extension, ships with KDE)
    try:
        import dbus as _dbus  # noqa: F401
        _run_tray_dbus_python()
        return
    except ImportError:
        pass

    # Fallback: dbus-fast (pure Python, no system packages needed)
    try:
        import dbus_fast as _dbus_fast  # noqa: F401
        import asyncio
        asyncio.run(_run_tray_dbus_fast())
        return
    except ImportError:
        pass

    raise SystemExit(
        "A DBus library is required for the Linux tray. Install one of:\n"
        "\n"
        "  System package (preferred on KDE/Arch):\n"
        "    sudo pacman -S python-dbus          # Arch / Manjaro\n"
        "    sudo apt install python3-dbus        # Ubuntu / Debian\n"
        "    sudo dnf install python3-dbus        # Fedora\n"
        "\n"
        "  Pure Python (works everywhere pip does):\n"
        "    pip install dbus-fast"
    )
