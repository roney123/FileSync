#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Roney'

import hashlib
import os
import logging
import shutil

cache_dir = "."
ignore_name = ".FSignore"
backup_dir = ".backup"
config_name = ".FSconfig"
auth_name = ".auth"
default_ignore = [".FSconfig", ".backup", ".FSignore", ".auth", ".git", ".idea"]

def is_match(s, p):
    scur, pcur, sstar, pstar = 0, 0, None, None
    while scur < len(s):
        if pcur < len(p) and p[pcur] in [s[scur], '?']:
            scur, pcur = scur + 1, pcur + 1
        elif pcur < len(p) and p[pcur] == '*':
            pstar, pcur = pcur, pcur + 1
            sstar = scur
        elif pstar is not None:
            pcur = pstar + 1
            sstar += 1
            scur = sstar
        else:
            return False

    while pcur < len(p) and p[pcur] == '*':
        pcur += 1

    return pcur >= len(p)


class FileIgnore:
    def __init__(self, ignore_file):
        self.re_list = []
        if os.path.exists(ignore_file):
            with open(ignore_file, 'r') as f:
                for line in f.readlines():
                    line = line.replace("\n", "").replace(" ", "")
                    _p = os.path.join(os.path.dirname(ignore_file), line)
                    self.re_list.append(_p)

    def filter(self, txt):
        for _re in self.re_list:
            if is_match(txt, _re):
                return True
        return False


def get_file_md5(file_name):
    m = hashlib.md5()
    try:
        with open(file_name, 'rb') as fobj:
            while True:
                data = fobj.read(4096)
                if not data:
                    break
                m.update(data)
        return m.hexdigest()
    except BaseException as e:
        logging.warning(e)
    return -1


def get_dir_tree(path):
    path = os.path.abspath(path)
    ignore_file = os.path.join(path, ignore_name)
    dir_dict = dict()
    dir_dict[path] = dict()
    dir_list = [(path, dir_dict[path])]
    _re = FileIgnore(ignore_file)
    while len(dir_list) > 0:
        _p, _d = dir_list.pop()
        for file in os.listdir(_p):
            now_path = os.path.join(_p, file)
            if not _re.filter(now_path):
                if os.path.isdir(now_path):
                    _d[file] = dict()
                    dir_list.append((now_path, _d[file]))
                else:
                    _d[file] = get_file_md5(now_path)
    return dir_dict


def remove_file(root_path, relative_file):
    abs_file = os.path.join(root_path, relative_file)
    try:
        if os.path.exists(abs_file):
            if os.path.isdir(abs_file):
                shutil.rmtree(abs_file)
            else:
                if backup_dir:
                    backup_file = os.path.join(root_path, os.path.join(backup_dir, relative_file))
                    backup_file_dir = os.path.dirname(backup_file)
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    if not os.path.exists(backup_file_dir):
                        os.makedirs(backup_file_dir)
                    os.rename(abs_file, backup_file)
                else:
                    os.remove(abs_file)
    except BaseException as e:
        logging.warning("remove file/dir error: {}".format(e))
    return not os.path.exists(abs_file)


def test_dir(path):
    path = os.path.abspath(path)
    ignore_file = os.path.join(path,ignore_name)
    if not os.access(path, os.W_OK):
        return False, path
    else:
        dir_list = [path]
        _re = FileIgnore(ignore_file)
        while len(dir_list) > 0:
            _p = dir_list.pop()
            for file in os.listdir(_p):
                now_path = os.path.join(_p, file)
                if not _re.filter(now_path):
                    if not os.access(now_path, os.W_OK) or not os.access(now_path, os.R_OK):
                        return False, now_path
                    if os.path.isdir(now_path):
                        dir_list.append(now_path)
        return True,""


def creat_ignore(path):
    ignore_file = os.path.join(path, ignore_name)
    if not os.path.exists(ignore_file):
        with open(ignore_file, "w") as f:
            for line in default_ignore:
                f.write(line + '\n')


def print_dict(d):
    print(json.dumps(d, indent=4, sort_keys=True))

if __name__ == "__main__":
    import json
    print(remove_file(".", "backup/1"))
    # print(json.dumps(get_dir_tree("./"), indent=4, sort_keys=True))
    # # print(os.access(r"C:\Users\zhangqiSX3552\Desktop\1", os.R_OK))
    # print(creat_ignore("."))

