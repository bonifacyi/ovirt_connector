from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

from web_login import CPLogin
import pandora_data as data


CONNECTION_STATUS = {
    0: data.QT_CONF['welcome_text'],
    1: 'Connection success',
    2: data.QT_CONF['wrong_credentials'],
    3: data.QT_CONF['unknown_problem'],
}


class ThreadConnect(QtCore.QThread):
    signal = QtCore.pyqtSignal(int)

    def __init__(self, target=False, username='', password='', parent=None):
        QtCore.QThread.__init__(self, parent=parent)
        self.target = target
        self.username = username
        self.password = password
        self.status = 0

    def run(self):
        if self.target:
            login = CPLogin(
                address=data.CP_ADDRESS,
                username=self.username,
                password=self.password,
                profile_dir=data.FIREFOX_PROFILE)
            self.status = login.login()
        else:
            logoff = CPLogin(address=data.CP_ADDRESS, profile_dir=data.FIREFOX_PROFILE)
            self.status = logoff.logoff()
        self.signal.emit(self.status)


class Thread(QtCore.QThread):
    signal = QtCore.pyqtSignal(int)

    def __init__(self, partial_function=None, parent=None):
        QtCore.QThread.__init__(self, parent=parent)
        self.partial_function = partial_function
        self.status = 0

    def run(self) -> None:
        if self.partial_function:
            answer = self.partial_function()
            if answer:
                self.status = answer
            self.signal.emit(self.status)


class LoginWindow(QtWidgets.QWidget):
    def __init__(self, target=1, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        icon = QtGui.QIcon(data.ICON)
        width = data.QT_CONF['width']
        height = data.QT_CONF['height']
        desktop = QtWidgets.QApplication.desktop()
        x = (desktop.width() - width) // 2
        y = (desktop.height() - height) // 2
        self.setGeometry(x, y, width, height)
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowStaysOnTopHint)
        self.text_font = QtGui.QFont(data.QT_CONF['font_family'], data.QT_CONF['font_size'])
        self.button_size = QtCore.QSize(90, 40)

        self.status_login = 0
        self.status_sync = 0

        # display login form or waiting box
        self.main_stack = QtWidgets.QStackedLayout()
        self.setLayout(self.main_stack)

        # login form
        self.form_widget = QtWidgets.QWidget()
        self.form_id = self.main_stack.addWidget(self.form_widget)
        self.form = QtWidgets.QFormLayout()
        self.form.setContentsMargins(20, 20, 20, 20)
        self.form.setVerticalSpacing(15)
        self.form_widget.setLayout(self.form)

        # waiting box
        self.waiting_widget = QtWidgets.QWidget()
        self.waiting_box = QtWidgets.QHBoxLayout()
        self.waiting_box.setContentsMargins(20, 20, 20, 30)
        self.waiting_dialog = QtWidgets.QProgressDialog()
        self.waiting_box.addWidget(self.waiting_dialog)

        self.waiting_text = QtWidgets.QLabel()
        self.waiting_text.setMinimumHeight(40)
        self.waiting_text.setFont(self.text_font)
        self.waiting_text.setAlignment(QtCore.Qt.AlignCenter)

        self.waiting_cancel = QtWidgets.QPushButton(data.QT_CONF['cancel'])
        self.waiting_cancel.setMinimumHeight(35)
        self.waiting_cancel.setFont(self.text_font)

        self.waiting_dialog.setMinimumDuration(0)
        self.waiting_dialog.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        self.waiting_dialog.setLabel(self.waiting_text)
        self.waiting_dialog.setCancelButton(self.waiting_cancel)
        self.waiting_dialog.canceled.connect(self.kill_connect)
        self.waiting_dialog.setRange(0, 0)

        self.waiting_id = self.main_stack.addWidget(self.waiting_widget)
        self.waiting_widget.setLayout(self.waiting_box)

        # 0 row in form (main message text):
        self.message_box = QtWidgets.QHBoxLayout()
        self.message_text = QtWidgets.QLabel()
        self.message_text.setFont(self.text_font)
        self.message_text.setAlignment(QtCore.Qt.AlignCenter)
        self.message_box.setContentsMargins(0, 0, 0, 10)
        self.message_box.addWidget(self.message_text)
        self.form.addRow(self.message_box)

        # 1 row in form (login text + entry):
        self.login_text = QtWidgets.QLabel(data.QT_CONF['login_text'])
        self.login_text.setFont(self.text_font)
        self.login_text.setAlignment(QtCore.Qt.AlignRight)
        self.login_entry = QtWidgets.QLineEdit()
        self.login_entry.setFont(self.text_font)
        self.form.addRow(self.login_text, self.login_entry)

        # 2 row in form (password text + entry):
        self.password_text = QtWidgets.QLabel(data.QT_CONF['password_text'])
        self.password_text.setFont(self.text_font)
        self.password_entry = QtWidgets.QLineEdit()
        self.password_entry.setFont(self.text_font)
        self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)
        self.form.addRow(self.password_text, self.password_entry)

        # 3 row in form (buttons):
        self.button_box = QtWidgets.QHBoxLayout()

        self.button_ok = QtWidgets.QPushButton(data.QT_CONF['ok'])
        self.button_ok.setFixedSize(self.button_size)
        self.button_ok.setFont(self.text_font)
        self.button_ok.clicked.connect(self.on_ok_clicked)

        self.button_cancel = QtWidgets.QPushButton(data.QT_CONF['cancel'])
        self.button_cancel.setFixedSize(self.button_size)
        self.button_cancel.setFont(self.text_font)
        self.button_cancel.clicked.connect(self.on_cancel_clicked)

        self.button_box.addWidget(self.button_ok, alignment=QtCore.Qt.AlignLeft)
        self.button_box.addWidget(self.button_cancel, alignment=QtCore.Qt.AlignRight)
        self.button_box.setContentsMargins(40, 20, 40, 0)
        self.form.addRow(self.button_box)

        # treading initialise
        self.username = ''
        self.password = ''
        self.thread_sync = Thread()
        if target:
            self.thread_login = ThreadConnect(target=True)
            self.thread_login.signal.connect(self.end_web_login)
            self.thread_sync.signal.connect(self.end_sync)
            self.display_login()
        else:
            self.thread_login = ThreadConnect(target=False)
            self.thread_login.signal.connect(self.stop_login)
            self.thread_sync.signal.connect(self.stop_sync)
            self.logoff()

    def display_login(self):
        self.setWindowTitle(data.QT_CONF['title'])
        self.message_text.setText(CONNECTION_STATUS[self.status_login])
        self.waiting_text.setText(data.QT_CONF['wait_text'])
        self.main_stack.setCurrentIndex(self.form_id)

    def display_waiting(self):
        self.waiting_dialog.forceShow()
        self.main_stack.setCurrentIndex(self.waiting_id)

    def on_ok_clicked(self):
        self.username = self.login_entry.text()
        self.password = self.password_entry.text()
        if self.username:
            if self.password:
                self.display_waiting()

                self.thread_login.username = self.username
                self.thread_login.password = self.password
                own_sync = partial(data.own_sync, self.username, self.password)
                self.thread_sync.partial_function = own_sync

                if not self.thread_login.isRunning():
                    self.thread_login.start()

                if not self.thread_sync.isRunning():
                    self.thread_sync.start()
            else:
                self.message_text.setText(data.QT_CONF['no_password'])
        else:
            self.message_text.setText(data.QT_CONF['no_name'])

    def on_cancel_clicked(self):
        self.close()
        data.shutdown()

    @QtCore.pyqtSlot(int)
    def end_web_login(self, signal):
        if signal:
            self.status_login = signal
        if self.status_sync:
            self.run_browser()

    @QtCore.pyqtSlot(int)
    def end_sync(self, signal):
        if signal:
            self.status_sync = signal
        if self.status_login:
            self.run_browser()

    def run_browser(self):
        if self.status_login == 1:
            data.start_files_create(self.username, self.password)
            data.before_shutdown()
            self.close()
        elif self.status_login in (2, 3):
            self.display_login()
        else:
            self.display_login()
            self.message_text.setText('Error. Status: {}'.format(self.status_login))
        self.status_login = 0
        self.status_sync = 0

    def kill_connect(self):
        if self.thread_login.isRunning():
            self.thread_login.yieldCurrentThread()
        if self.thread_sync.isRunning():
            self.thread_sync.yieldCurrentThread()
        self.on_cancel_clicked()

    def logoff(self):
        self.setWindowTitle(data.QT_CONF['title_logoff'])
        self.waiting_text.setText(data.QT_CONF['wait_logoff_text'])
        self.waiting_cancel.setDisabled(True)
        self.display_waiting()

        self.thread_sync.partial_function = partial(data.stop)

        if not self.thread_login.isRunning():
            self.thread_login.start()

        if not self.thread_sync.isRunning():
            self.thread_sync.start()

    @QtCore.pyqtSlot(int)
    def stop_login(self, signal):
        if signal:
            self.status_login = signal
        if self.status_sync:
            self.on_cancel_clicked()

    @QtCore.pyqtSlot(int)
    def stop_sync(self, signal):
        if signal:
            self.status_sync = signal
        if self.status_login:
            self.on_cancel_clicked()

    def event(self, e):
        if e.type() == QtCore.QEvent.KeyPress:
            if e.key() in (QtCore.Qt.Key_Enter, 16777220, 16777221):
                self.on_ok_clicked()
        return QtWidgets.QWidget.event(self, e)


def main():
    import sys
    args = sys.argv
    if len(args) != 2:
        print('Need arg "on" or "off"')
        sys.exit(1)
    app = QtWidgets.QApplication([args[0]])

    if args[1] == 'on':
        window = LoginWindow(target=1)
    elif args[1] == 'off':
        window = LoginWindow(target=0)
    else:
        print('Need argument "on" or "off"')
        sys.exit(1)

    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
