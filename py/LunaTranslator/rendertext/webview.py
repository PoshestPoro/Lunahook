from qtsymbols import *
from rendertext.somefunctions import dataget
import gobject, uuid, json, os, functools, windows, time
from urllib.parse import quote
from myutils.utils import threader
from myutils.config import globalconfig, static_data, _TR
from myutils.wrapper import tryprint, threader
from gui.usefulwidget import WebivewWidget
from gui.textbrowser import TextType

testsavejs = False


class TextBrowser(QWidget, dataget):
    dropfilecallback = pyqtSignal(str)
    contentsChanged = pyqtSignal(QSize)

    @tryprint
    def resizeEvent(self, event: QResizeEvent):
        self.webivewwidget.resize(event.size())

    def __init__(self, parent) -> None:
        super().__init__(parent)
        # webview2当会执行alert之类的弹窗js时，若qt窗口不可视，会卡住
        self.webivewwidget = WebivewWidget(self)
        self.webivewwidget.move(0, 0)
        self.setMouseTracking(True)
        self.webivewwidget.add_menu(
            0,
            _TR("查词"),
            threader(
                lambda w: gobject.baseobject.searchwordW.search_word.emit(
                    w.replace("\n", "").strip(), False
                )
            ),
        )
        self.webivewwidget.add_menu(
            1,
            _TR("翻译"),
            lambda w: gobject.baseobject.textgetmethod(w.replace("\n", "").strip()),
        )
        self.webivewwidget.add_menu(
            2,
            _TR("朗读"),
            lambda w: gobject.baseobject.read_text(w.replace("\n", "").strip()),
        )
        self.webivewwidget.add_menu_noselect(0, _TR("清空"), self.___cleartext)
        self.webivewwidget.set_transparent_background()
        self.webivewwidget.dropfilecallback.connect(self.dropfilecallback)
        self.webivewwidget.bind(
            "calllunaclickedword", gobject.baseobject.clickwordcallback
        )
        self.webivewwidget.bind("calllunaMouseMove", self.calllunaMouseMove)
        self.webivewwidget.bind("calllunaMousePress", self.calllunaMousePress)
        self.webivewwidget.bind("calllunaMouseRelease", self.calllunaMouseRelease)
        self.webivewwidget.bind("calllunaheightchange", self.calllunaheightchange)
        self.webivewwidget.bind("calllunaloadready", self.resetflags)
        self.saveiterclasspointer = {}
        self.isfirst = True
        self.flags = {}

    def ___cleartext(self):
        self.parent().clear()
        gobject.baseobject.currenttext = ""

    def resetflags(self):
        for k, v in self.flags.items():
            self.debugeval("{}({})".format(k, int(v)))
        self.setfontstyle()
        self.parent().refreshcontent()

    def switchcursor(self, cursor):
        cursor_map = {
            Qt.CursorShape.ArrowCursor: "default",
            Qt.CursorShape.UpArrowCursor: "n-resize",
            Qt.CursorShape.CrossCursor: "crosshair",
            Qt.CursorShape.WaitCursor: "wait",
            Qt.CursorShape.IBeamCursor: "text",
            Qt.CursorShape.SizeVerCursor: "ns-resize",
            Qt.CursorShape.SizeHorCursor: "ew-resize",
            Qt.CursorShape.SizeBDiagCursor: "nesw-resize",
            Qt.CursorShape.SizeFDiagCursor: "nwse-resize",
            Qt.CursorShape.SizeAllCursor: "move",
            Qt.CursorShape.BlankCursor: "none",
            Qt.CursorShape.SplitVCursor: "row-resize",
            Qt.CursorShape.SplitHCursor: "col-resize",
            Qt.CursorShape.PointingHandCursor: "pointer",
            Qt.CursorShape.ForbiddenCursor: "not-allowed",
            Qt.CursorShape.WhatsThisCursor: "help",
            Qt.CursorShape.BusyCursor: "progress",
            Qt.CursorShape.OpenHandCursor: "grab",
            Qt.CursorShape.ClosedHandCursor: "grabbing",
        }
        self.webivewwidget.eval(
            'switchcursor("{}")'.format(cursor_map.get(cursor, "default"))
        )

    @tryprint
    def showEvent(self, e):
        if not self.isfirst:
            return
        if not isinstance(self.webivewwidget, WebivewWidget):
            return
        self.isfirst = False
        self.loadex()
        gobject.baseobject.translation_ui.cursorSet.connect(self.switchcursor)

    def loadex(self, extra=None):
        if not extra:
            extra = self.loadextra()
            extra = extra if extra else ""
        with open(
            r"LunaTranslator\rendertext\webview.html", "r", encoding="utf8"
        ) as ff:
            html = ff.read().replace("__PLACEHOLDER_EXTRA_HTML_", extra)
        with open(
            r"LunaTranslator\rendertext\webview_parsed.html", "w", encoding="utf8"
        ) as ff:
            ff.write(html)
        self.webivewwidget.navigate(
            os.path.abspath(r"LunaTranslator\rendertext\webview_parsed.html")
        )

    def loadextra(self):
        if not globalconfig["useextrahtml"]:
            return
        for _ in [
            "userconfig/extrahtml.html",
            r"LunaTranslator\rendertext\exampleextrahtml.html",
        ]:
            if not os.path.exists(_):
                continue
            with open(_, "r", encoding="utf8") as ff:
                return ff.read()

    def debugeval(self, js):
        # print(js)
        self.webivewwidget.eval(js)

    # js api
    def setselectable(self, b):
        self.debugeval("setselectable({})".format(int(b)))
        self.flags["setselectable"] = b

    def showatcenter(self, show):
        self.debugeval("showatcenter({})".format(int(show)))
        self.flags["showatcenter"] = show

    def showhidetranslate(self, show):
        self.debugeval("showhidetranslate({})".format(int(show)))
        self.flags["showhidetranslate"] = show

    def showhideorigin(self, show):
        self.debugeval("showhideorigin({})".format(int(show)))
        self.flags["showhideorigin"] = show

    def showhideerror(self, show):
        self.debugeval("showhideerror({})".format(int(show)))
        self.flags["showhideerror"] = show

    def create_div_line_id(self, _id, texttype: TextType):
        self.debugeval('create_div_line_id("{}",{})'.format(_id, texttype))

    def clear_all(self):
        self.debugeval("clear_all()")

    def create_internal_text(self, style, styleargs, _id, text, args):
        text = quote(text)
        args = quote(json.dumps(args))
        styleargs = quote(json.dumps(styleargs))
        self.debugeval(
            'create_internal_text("{}","{}","{}","{}","{}");'.format(
                style, styleargs, _id, text, args
            )
        )

    def create_internal_rubytext(self, style, styleargs, _id, tag, args):
        tag = quote(json.dumps(tag))
        args = quote(json.dumps(args))
        styleargs = quote(json.dumps(styleargs))
        self.debugeval(
            'create_internal_rubytext("{}","{}","{}","{}","{}");'.format(
                style, styleargs, _id, tag, args
            )
        )

    def calllunaheightchange(self, h):
        self.contentsChanged.emit(
            QSize(
                self.width(),
                int(h * self.webivewwidget.get_zoom()),
            )
        )

    def parsemousebutton(self, i):
        btn_map = {
            0: Qt.MouseButton.LeftButton,
            1: Qt.MouseButton.MiddleButton,
            2: Qt.MouseButton.RightButton,
            3: Qt.MouseButton.BackButton,
            4: Qt.MouseButton.ForwardButton,
        }
        return btn_map.get(i, Qt.MouseButton.NoButton)

    def parsexyaspos(self, x, y):
        zoom = self.webivewwidget.get_zoom()
        x = zoom * x
        y = zoom * y
        return QPointF(x, y)

    def calllunaMousePress(self, btn, x, y):
        pos = self.parsexyaspos(x, y)
        btn = self.parsemousebutton(btn)
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            pos,
            btn,
            btn,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(self, event)

    def calllunaMouseRelease(self, btn, x, y):
        pos = self.parsexyaspos(x, y)
        btn = self.parsemousebutton(btn)
        event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            pos,
            btn,
            btn,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(self, event)

    def calllunaMouseMove(self, x, y):
        pos = self.parsexyaspos(x, y)
        event = QMouseEvent(
            QEvent.Type.MouseMove,
            pos,
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(self, event)

    # native api end
    def setfontstyle(self):
        def __loadfont(argc, extra):
            fm, fs, bold = argc
            return dict(
                fontFamily=fm,
                fontSize=fs,
                bold=bold,
                lineHeight=max(1, self.measureH(*argc) + extra),
            )

        args = dict(
            origin=__loadfont(
                self._getfontinfo(TextType.Origin), globalconfig["extra_space"]
            ),
            trans=__loadfont(
                self._getfontinfo(TextType.Translate), globalconfig["extra_space_trans"]
            ),
            hira=__loadfont(self._getfontinfo_kana(), 0),
        )
        args = quote(json.dumps(args))
        self.debugeval('setfontstyle("{}");'.format(args))

    def iter_append(self, iter_context_class, texttype: TextType, text, color):

        if iter_context_class not in self.saveiterclasspointer:
            _id = self.createtextlineid(texttype)
            self.saveiterclasspointer[iter_context_class] = _id

        _id = self.saveiterclasspointer[iter_context_class]
        self._webview_append(_id, text, [], [], color)

    def createtextlineid(self, texttype: TextType):

        _id = "luna_{}".format(uuid.uuid4())
        self.create_div_line_id(_id, texttype)
        return _id

    def append(self, texttype: TextType, text, tag, flags, color):
        _id = self.createtextlineid(texttype)
        self._webview_append(_id, text, tag, flags, color)

    def measureH(self, font_family, font_size, bold):
        font = QFont()
        font.setFamily(font_family)
        font.setPointSizeF(font_size)
        font.setBold(bold)
        fmetrics = QFontMetricsF(font)
        return fmetrics.height()

    def _getstylevalid(self):
        currenttype = globalconfig["rendertext_using_internal"]["webview"]
        if currenttype not in static_data["textrender"]["webview"]:
            currenttype = static_data["textrender"]["webview"][0]
            globalconfig["rendertext_using_internal"]["webview"] = static_data[
                "textrender"
            ]["webview"][0]
        return currenttype

    def _webview_append(self, _id, text: str, tag, flags, color):
        style = self._getstylevalid()
        styleargs = globalconfig["rendertext"]["webview"][style].get("args", {})
        if len(tag):
            isshowhira, isshow_fenci, isfenciclick = flags
            if isshow_fenci:
                for word in tag:
                    color1 = self._randomcolor(word)
                    word["color"] = color1
            args = dict(
                color=color,
                kanacolor=self._getkanacolor(),
                isshowhira=isshowhira,
                isshow_fenci=isshow_fenci,
                isfenciclick=isfenciclick,
            )
            self.create_internal_rubytext(style, styleargs, _id, tag, args)
        else:
            sig = "LUNASHOWHTML"
            userawhtml = sig in text
            if userawhtml:
                text = text.replace(sig, "")

            args = dict(color=color, userawhtml=userawhtml)

            self.create_internal_text(style, styleargs, _id, text, args)

    def clear(self):

        self.clear_all()
        self.saveiterclasspointer.clear()
