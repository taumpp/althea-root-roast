"""Launcher-only connection phase: loading artwork and the shared status popup."""
import app
import constInfo
import introbackground
import launcherhandoff
import localeInfo
import net
import serverInfo
import ui
import wndMgr


class ConnectionWindow(ui.ScriptWindow):
    def __init__(self, stream, message=None):
        ui.ScriptWindow.__init__(self)
        self.stream = stream
        self.message = message
        self.background = None
        self.screenSize = None
        self.closed = True
        self.terminal = False
        self.exiting = False

    def Open(self):
        self.closed = False
        net.SetPhaseWindow(net.PHASE_WINDOW_LOGIN, self)
        net.SetAccountConnectorHandler(self)
        self.SetWindowName("LauncherConnectionWindow")
        self.background = ui.ExpandedImageBox()
        self.background.SetParent(self)
        self.background.AddFlag("not_pick")
        self._RefreshBackground()
        self.background.Show()
        self.Show()
        app.ShowCursor()
        self.stream.isAutoLogin = 0
        self.stream.isAutoSelect = 0
        if not self.message:
            self.message = self.stream.connectionFailureMessage
        if self.message:
            self._Fail(self.message)
            return
        if self.stream.launcherConnectionAttempted:
            self._Fail(localeInfo.LOGIN_CONNECTION_CLOSED)
            return
        record = launcherhandoff.consume()
        if record is None:
            self._Fail(localeInfo.LOGIN_LAUNCHER_REQUIRED)
            return
        serverName, channelID, login, password = record
        for serverID, server in serverInfo.REGION_DICT[0].items():
            if server["name"] == serverName and channelID in server["channel"]:
                break
        else:
            self._Fail(localeInfo.LOGIN_LAUNCHER_REQUIRED)
            return
        channel = server["channel"][channelID]
        auth = serverInfo.REGION_AUTH_SERVER_DICT[0].get(serverID)
        mark = serverInfo.MARKADDR_DICT.get(serverID * 10)
        if auth is None or mark is None:
            self._Fail(localeInfo.LOGIN_CONNECT_FAILURE)
            return
        self.stream.SetConnectInfo(channel["ip"], channel["tcp_port"], auth["ip"], auth["port"])
        net.SetServerInfo(("|cFFFF8C00%s |cFFFFFFFF- |cFFFFD700%s" % (serverName, channel["name"])).strip())
        net.SetMarkServer(mark["ip"], mark["tcp_port"])
        app.SetGuildMarkPath(mark["mark"])
        app.SetGuildSymbolPath(mark["symbol_path"])
        constInfo.ch = channelID
        constInfo.LastAccount = login.lower()
        if constInfo.SEQUENCE_PACKET_ENABLE:
            net.SetPacketSequenceMode()
        self.stream.SetCharacterSlot(0)
        self.stream.isAutoLogin = 1
        self.stream.SetLoginInfo(login, password)
        self._Status(localeInfo.LOGIN_CONNETING)
        self.stream.launcherConnectionAttempted = True
        if self.stream.Connect() is False:
            self.OnConnectFailure()

    def _RefreshBackground(self):
        size = (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        if size != self.screenSize:
            self.screenSize = size
            self.SetSize(*size)
            introbackground.apply_background(self.background, *size)

    def _DismissStatus(self):
        # PopupDialog.Close invokes its callback even during phase teardown or
        # message replacement. Disarm it before a programmatic close.
        self.stream.popupWindow.CloseEvent = 0
        self.stream.popupWindow.Close()

    def _Status(self, message, button=None):
        self._DismissStatus()
        self.stream.popupWindow.Open(message, self.Exit, button or localeInfo.UI_CANCEL)

    def _Fail(self, message):
        if self.closed or self.terminal:
            return
        self.terminal = True
        self.message = message
        self.stream.connectionFailureMessage = message
        self._Status(message, localeInfo.UI_OK)

    def OnConnectFailure(self):
        self._Fail(localeInfo.LOGIN_CONNECT_FAILURE)

    def OnHandShake(self):
        if not self.closed and not self.terminal:
            self._Status(localeInfo.LOGIN_CONNECT_SUCCESS)

    def OnLoginStart(self):
        if not self.closed and not self.terminal:
            self._Status(localeInfo.LOGIN_PROCESSING)

    def OnLoginFailure(self, error):
        if self.closed or self.exiting:
            return
        messages = {
            'ALREADY': localeInfo.LOGIN_FAILURE_ALREAY,
            'NOID': localeInfo.LOGIN_FAILURE_NOT_EXIST_ID,
            'WRONGPWD': localeInfo.LOGIN_FAILURE_WRONG_PASSWORD,
            'FULL': localeInfo.LOGIN_FAILURE_TOO_MANY_USER,
            'SHUTDOWN': localeInfo.LOGIN_FAILURE_SHUTDOWN,
            'REPAIR': localeInfo.LOGIN_FAILURE_REPAIR_ID,
            'BLOCK': localeInfo.LOGIN_FAILURE_BLOCK_ID,
            'BESAMEKEY': localeInfo.LOGIN_FAILURE_BE_SAME_KEY,
            'NOTAVAIL': localeInfo.LOGIN_FAILURE_NOT_AVAIL,
            'NOBILL': localeInfo.LOGIN_FAILURE_NOBILL,
            'BLKLOGIN': localeInfo.LOGIN_FAILURE_BLOCK_LOGIN,
            'WEBBLK': localeInfo.LOGIN_FAILURE_WEB_BLOCK,
            'BADSCLID': localeInfo.LOGIN_FAILURE_WRONG_SOCIALID,
            'AGELIMIT': localeInfo.LOGIN_FAILURE_SHUTDOWN_TIME,
            'HWID_BAN': localeInfo.LOGIN_FAILURE_BLOCK_ID,
            'VIP_ONLY': localeInfo.LOGIN_FAILURE_VIP_ONLY,
            'DEVICE_LIMIT': localeInfo.LOGIN_FAILURE_DEVICE_LIMIT,
            'DEVICE_L': localeInfo.LOGIN_FAILURE_DEVICE_LIMIT,
            'DEVLIM': localeInfo.LOGIN_FAILURE_DEVICE_LIMIT,
            'DEVICE_ID': localeInfo.LOGIN_FAILURE_DEVICE_ID,
            'DEVICE_I': localeInfo.LOGIN_FAILURE_DEVICE_ID,
            'DEVID': localeInfo.LOGIN_FAILURE_DEVICE_ID,
            'DEVAPPR': localeInfo.LOGIN_FAILURE_DEVICE_APPROVAL,
            'DEVWAIT': localeInfo.LOGIN_FAILURE_DEVICE_COOLDOWN,
            'DEVERR': localeInfo.LOGIN_FAILURE_DEVICE_UNAVAILABLE,
        }
        # A reason received from the server is more precise than a transport
        # close (which cannot distinguish a restart, kick or network outage).
        if self.message == localeInfo.LOGIN_CONNECTION_CLOSED:
            self.terminal = False
        self._Fail(messages.get(error, localeInfo.LOGIN_FAILURE_UNKNOWN))

    def OnUpdate(self):
        if self.closed:
            return
        self._RefreshBackground()

    def Exit(self):
        if self.exiting:
            return
        self.exiting = True
        self.terminal = True
        net.Disconnect()
        app.Exit()

    def OnExit(self):
        self.Exit()

    def OnPressEscapeKey(self):
        self.Exit()
        return True

    def OnPressExitKey(self):
        self.Exit()
        return True

    def Close(self):
        if self.closed:
            return
        self.closed = True
        self._DismissStatus()
        net.ClearPhaseWindow(net.PHASE_WINDOW_LOGIN, self)
        net.SetAccountConnectorHandler(0)
        self.KillFocus()
        self.Hide()
        self.background.Hide()
        self.background = None
        app.HideCursor()
