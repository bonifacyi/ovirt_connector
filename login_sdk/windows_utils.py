import os
import win32crypt
import win32security
import win32api
import hashlib
import base64


def get_name():
    fullname = win32api.GetUserNameEx(3)
    username = win32api.GetUserNameEx(4)
    return fullname, username


def encrypt_data(word):
    entropy = get_entropy()
    
    word_bytes = win32crypt.CryptProtectData(word.encode(), None, entropy, None, None, 0)
    encrypt_word = base64.b64encode(word_bytes).decode()
    
    return encrypt_word


def decrypt_data(encrypt_word):        
    entropy = get_entropy()
    
    word_bytes = base64.b64decode(encrypt_word.encode())
    word = win32crypt.CryptUnprotectData(word_bytes, entropy, None, None, 0)[1].decode()
    
    return word


def get_entropy():
    try:
        sid = win32security.ConvertSidToStringSid(win32security.LookupAccountName(None, os.getlogin())[0])
        entropy = hashlib.md5(sid.encode()).digest()
    except:
        entropy = ''
    return entropy
