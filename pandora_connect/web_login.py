#!/usr/bin/env python

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import \
    NoSuchElementException, \
    InvalidElementStateException,\
    NoSuchWindowException, \
    WebDriverException, \
    ElementNotInteractableException
import time
import re
import sys
import argparse


class CPLogin(webdriver.Firefox):
    def __init__(self, address, username='', password='', profile_dir=''):
        options = Options()
        options.headless = True
        if profile_dir:
            profile = webdriver.FirefoxProfile(profile_directory=profile_dir)
            webdriver.Firefox.__init__(self, firefox_profile=profile, options=options)
        else:
            webdriver.Firefox.__init__(self, options=options)
        self.status = 0
        self.address = address
        self.username = username
        self.password = password
        self.login_button = None
        self.logoff_button = None
        self.username_field = None
        self.password_field = None
        self.error_span = None
        self.error_text = ''
        self.re_access_span = None

    def open_page(self):
        print(self.address)
        self.get(self.address)
        self.implicitly_wait(5)

    def login(self, username='', password=''):
        self.open_page()
        if username:
            self.username = username
        if password:
            self.password = password
        if not self.username or not self.password:
            self.status = 2
            self.quit()
            return self.status

        for i in range(6):
            self.find_logoff_button()
            self.find_login_button()

            if self.login_button:
                self.find_error_span()
                if re.search('bad.*credential', self.error_text, re.IGNORECASE):
                    self.status = 2
                    self.quit()
                    return self.status
                self.connect()
            elif self.logoff_button:
                self.status = 1
                self.quit()
                return self.status
            else:
                self.status = 3
                unknown = True
                self.find_re_access_span()
                if self.re_access_span:
                    for span in self.re_access_span:
                        if re.search('regain.*access', span.text, re.IGNORECASE):
                            unknown = False
                            self.re_access_span.click()
                if unknown:
                    self.open_page()

        self.quit()
        return self.status

    def find_login_button(self):
        try:
            self.login_button = self.find_element_by_id('UserCheck_Login_Button_span')
        except NoSuchElementException:
            self.login_button = None

    def find_logoff_button(self):
        try:
            self.logoff_button = self.find_element_by_id('UserCheck_Logoff_Button_span')
        except NoSuchElementException:
            self.logoff_button = None

    def find_username_field(self):
        try:
            self.username_field = self.find_element_by_id('LoginUserPassword_auth_username')
            try:
                self.username_field.clear()
            except InvalidElementStateException:
                pass
        except NoSuchElementException:
            self.username_field = None

    def find_password_field(self):
        try:
            self.password_field = self.find_element_by_id('LoginUserPassword_auth_password')
            try:
                self.password_field.clear()
            except InvalidElementStateException:
                pass
        except NoSuchElementException:
            self.password_field = None

    def find_error_span(self):
        try:
            self.error_span = self.find_element_by_id('LoginUserPassword_error_message')
        except NoSuchElementException:
            self.error_span = None
        if self.error_span:
            self.error_text = self.error_span.text.strip()
        else:
            self.error_text = ''

    def find_re_access_span(self):
        try:
            self.re_access_span = self.find_element_by_class_name('portal_link')
        except NoSuchElementException:
            self.re_access_span = None

    def connect(self):
        self.find_username_field()
        self.find_password_field()
        try:
            self.username_field.send_keys(self.username)
            self.password_field.send_keys(self.password)
        except ElementNotInteractableException:
            self.open_page()
        else:
            time.sleep(1)
            self.login_button.click()

    def logoff(self):
        self.get(self.address)
        self.implicitly_wait(5)

        self.find_logoff_button()
        if self.logoff_button:
            self.logoff_button.click()
        time.sleep(1)
        self.quit()
        time.sleep(1)
        return 1


def main():
    parser = argparse.ArgumentParser(description='Connection to Check Point')
    parser.add_argument('-a', action='store', dest='address', type=str, help='Check Point address')
    parser.add_argument('-c', action='store_true', dest='connect', help='Connect to Check Point')
    parser.add_argument('-n', action='store', dest='name', type=str, help='Domain user name')
    parser.add_argument('-p', action='store', dest='password', type=str, help='Domain password')
    parser.add_argument('-d', action='store_true', dest='disconnect', help='Disconnect')
    parser.add_argument('-f', action='store', dest='profile', type=str, help='Firefox profile directory')
    args = parser.parse_args()

    profile_dir = ''
    if args.profile:
        profile_dir = args.profile
    if args.address and args.connect and args.name and args.password and not args.disconnect:
        login = CPLogin(address=args.address, username=args.name, password=args.password, profile_dir=profile_dir)
        try:
            status = login.login()
        except (NoSuchWindowException, WebDriverException):
            status = 3
        sys.exit(status)
    elif args.address and args.disconnect:
        logoff = CPLogin(address=args.address, profile_dir=profile_dir)
        logoff.logoff()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
