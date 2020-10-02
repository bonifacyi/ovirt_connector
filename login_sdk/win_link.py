import os
from win32com.shell import shell, shellcon
from win32com.client import Dispatch
import pythoncom


def link_destination(file_path):
    shortcut = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink,
        None,
        pythoncom.CLSCTX_INPROC_SERVER,
        shell.IID_IShellLink
    )
    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
    persist_file.Load(file_path)
    
    try:
        path = shortcut.GetPath(2)[0]
    except:
        path = ''
    return path


def link_set_icon(link_path, new_icon):
    shortcut = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink,
        None,
        pythoncom.CLSCTX_INPROC_SERVER,
        shell.IID_IShellLink
    )
    persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
    persist_file.Load(link_path)
    
    shortcut.SetIconLocation(new_icon, 0)
    persist_file.Save(link_path, 0)


def create_link(link_path, destination, icon=None):
    win_shell = Dispatch('WScript.Shell')
    shortcut = win_shell.CreateShortCut(link_path)
    shortcut.Targetpath = destination
    if not os.path.isdir(destination):
        shortcut.WorkingDirectory = os.path.dirname(destination)
    if icon:
        shortcut.IconLocation = icon
    shortcut.save()


def safely_create_link(link_name, target_path, icon=None):
    desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)

    desktop_files = os.listdir(desktop)
    for file in desktop_files:
        if file[-4:] == '.lnk':
            file_path = os.path.join(desktop, file)
            file_destination = link_destination(file_path)
            file_destination_norm = os.path.normcase(os.path.normpath(file_destination)).strip(' /\\')
            target_path_norm = os.path.normcase(os.path.normpath(target_path)).strip(' /\\')
            if file_destination_norm == target_path_norm:
                if icon:
                    link_set_icon(file_path, icon)
                return

    if link_name[-4:] != '.lnk':
        link_name += '.lnk'
    link_path = os.path.join(desktop, link_name)
    create_link(link_path, target_path, icon)
