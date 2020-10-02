from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

import sdk_rdp_generate as rdp


CONNECTION_STATUS = {
    0: rdp.QT_CONF['welcome_text'],
    1: 'Connection success',
    2: rdp.QT_CONF['wrong_credentials'],
    3: rdp.QT_CONF['unknown_problem'],
}


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
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        width = rdp.QT_CONF['width']
        height = rdp.QT_CONF['height']

        desktop = QtWidgets.QApplication.desktop()
        x = (desktop.availableGeometry().width() - width) // 2
        y = (desktop.availableGeometry().height() - height) // 2
        self.setGeometry(x, y, width, height)

        icon = QtGui.QIcon(rdp.ICON)
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        self.text_font = QtGui.QFont(rdp.QT_CONF['font_family'], rdp.QT_CONF['font_size'])
        self.button_size = QtCore.QSize(90, 40)
        self.setWindowTitle(rdp.QT_CONF['title'])

        self.status_login = 0
        
        # init rdp connection class
        self.rdp_connect = rdp.RdpConnect()
        self.fullname, self.username, self.password = self.rdp_connect.load_data()

        # display login form or waiting box or info box
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

        self.waiting_cancel = QtWidgets.QPushButton(rdp.QT_CONF['cancel'])
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

        # info box
        self.info_widget = QtWidgets.QWidget()
        self.info_box = QtWidgets.QVBoxLayout()
        self.info_box.setContentsMargins(20, 20, 20, 30)

        self.info_text = QtWidgets.QLabel()
        self.info_text.setMinimumHeight(40)
        self.info_text.setFont(self.text_font)
        self.info_text.setAlignment(QtCore.Qt.AlignCenter)
        self.info_box.addWidget(self.info_text)

        self.info_close = QtWidgets.QPushButton(rdp.QT_CONF['cancel'])
        self.info_close.setFixedSize(self.button_size)
        self.info_close.setFont(self.text_font)
        self.info_close.clicked.connect(self.on_cancel_clicked)
        self.info_box.addWidget(self.info_close, alignment=QtCore.Qt.AlignCenter)
        self.info_box.setContentsMargins(40, 20, 40, 0)

        self.info_id = self.main_stack.addWidget(self.info_widget)
        self.info_widget.setLayout(self.info_box)
        
        # 0 row in form (main message text):
        self.message_box = QtWidgets.QHBoxLayout()
        self.message_text = QtWidgets.QLabel()
        self.message_text.setFont(self.text_font)
        self.message_text.setAlignment(QtCore.Qt.AlignCenter)
        self.message_box.setContentsMargins(0, 0, 0, 10)
        self.message_box.addWidget(self.message_text)
        self.form.addRow(self.message_box)

        # 1 row in form (login text + entry):
        self.login_text = QtWidgets.QLabel(rdp.QT_CONF['login_text'])
        self.login_text.setFont(self.text_font)
        self.login_text.setAlignment(QtCore.Qt.AlignRight)
        self.login_entry = QtWidgets.QLineEdit()
        self.login_entry.setFont(self.text_font)
        if self.fullname:
            self.login_entry.setText(self.fullname)
        else:
            self.login_entry.setText(self.username)
        self.login_entry.setReadOnly(True)
        self.form.addRow(self.login_text, self.login_entry)

        # 2 row in form (password text + entry):
        self.password_text = QtWidgets.QLabel(rdp.QT_CONF['password_text'])
        self.password_text.setFont(self.text_font)
        self.password_entry = QtWidgets.QLineEdit()
        self.password_entry.setFont(self.text_font)
        self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)
        self.form.addRow(self.password_text, self.password_entry)

        # 3 row in form (buttons):
        self.button_box = QtWidgets.QHBoxLayout()

        self.button_ok = QtWidgets.QPushButton(rdp.QT_CONF['ok'])
        self.button_ok.setFixedSize(self.button_size)
        self.button_ok.setFont(self.text_font)
        self.button_ok.clicked.connect(self.on_ok_clicked)

        self.button_cancel = QtWidgets.QPushButton(rdp.QT_CONF['cancel'])
        self.button_cancel.setFixedSize(self.button_size)
        self.button_cancel.setFont(self.text_font)
        self.button_cancel.clicked.connect(self.on_cancel_clicked)

        self.button_box.addWidget(self.button_ok, alignment=QtCore.Qt.AlignLeft)
        self.button_box.addWidget(self.button_cancel, alignment=QtCore.Qt.AlignRight)
        self.button_box.setContentsMargins(40, 20, 40, 0)
        self.form.addRow(self.button_box)
        
        # treading initialise
        self.thread_login = Thread()
        self.thread_login.signal.connect(self.end_login)

        # show window depending on the availability of user data
        if self.username:
            if self.password:
                self.rdp_login()
            else:
                self.display_login()
        else:
            self.status_login = 3
            self.display_info()

    def display_login(self):
        self.message_text.setText(CONNECTION_STATUS[self.status_login])
        self.main_stack.setCurrentIndex(self.form_id)

    def display_waiting(self):
        self.waiting_text.setText(rdp.QT_CONF['wait_text'])
        self.waiting_dialog.forceShow()
        self.main_stack.setCurrentIndex(self.waiting_id)

    def display_info(self):
        self.info_text.setText(CONNECTION_STATUS[self.status_login])
        self.main_stack.setCurrentIndex(self.info_id)

    def rdp_login(self):
        self.display_waiting()
        login = partial(self.rdp_connect.connect)
        self.thread_login.partial_function = login

        if not self.thread_login.isRunning():
            self.thread_login.start()

    def on_ok_clicked(self):
        self.password = self.password_entry.text()
        if self.password:
            self.rdp_connect.save_data(self.password)
            self.rdp_login()
        else:
            self.message_text.setText(rdp.QT_CONF['no_password'])

    def on_cancel_clicked(self):
        self.close()

    @QtCore.pyqtSlot(int)
    def end_login(self, signal):
        if signal:
            self.status_login = signal
        self.run_console()

    def run_console(self):
        if self.status_login == 1:      # success
            self.close()
            self.rdp_connect.run_rdp_console()
        elif self.status_login == 2:    # bad user credentials
            self.display_login()
        elif self.status_login == 3:    # server or LAN problem
            self.display_info()
        else:
            self.display_info()
            self.info_text.setText('Error. Status: {}'.format(self.status_login))
        self.status_login = 0

    def kill_connect(self):
        if self.thread_login.isRunning():
            self.thread_login.yieldCurrentThread()
        self.on_cancel_clicked()

    def event(self, e):
        if e.type() == QtCore.QEvent.KeyPress:
            if e.key() in (QtCore.Qt.Key_Enter, 16777220, 16777221):
                if self.main_stack.currentIndex() == self.form_id:
                    self.on_ok_clicked()
                #elif self.main_stack.currentIndex() == self.waiting_id:
                #    self.kill_connect()
                elif self.main_stack.currentIndex() == self.info_id:
                    self.on_cancel_clicked()
        return QtWidgets.QWidget.event(self, e)


def main():
    import sys
    args = sys.argv

    app = QtWidgets.QApplication([args[0]])
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
