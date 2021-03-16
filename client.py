#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Roney'

import os
import json
from urllib.parse import quote
import requests
import uuid
import utils
import tqdm

remote_only = "remote only"
modify = "modify"
local_only = "local only"


def simple_http_get(url):
    try:
        response = requests.get(url, timeout=6)
        if response.status_code == 200:
            res = json.loads(response.text)
            if res["status"] == 0:
                return True
            else:
                print("remote:{}".format(res["message"]))
    except BaseException as e:
        print(e)
    return False


def remote_test(ip, remote_root, auth):
    _url = "{}/test?root={}&auth={}".format(ip, quote(remote_root), auth)
    return simple_http_get(_url)


def remote_tree(ip, remote_root, auth):
    _url = "{}/get?root={}&auth={}".format(ip, quote(remote_root), auth)
    try:
        response = requests.get(_url, timeout=30)
        if response.status_code == 200:
            res = json.loads(response.text)
            if res["status"] == 0:
                return res["data"]
            else:
                print(res["message"])
    except BaseException as e:
        print(e)
    return None


def remote_mkdir(ip,remote_root, path,auth):
    _url = "{}/mkdir?root={}&path={}&auth={}".format(ip,quote(remote_root), quote(path),auth)
    return simple_http_get(_url)


def remote_remove(ip,remote_root,file,auth):
    _url = "{}/remove?root={}&file={}&auth={}".format(ip, quote(remote_root),quote(file),auth)
    return simple_http_get(_url)


def remote_upload(ip,remote_root,local_root,file,auth):
    _url = "{}/upload?root={}&file={}&auth={}".format(ip,quote(remote_root),quote(file),auth)
    try:
        with open(os.path.join(local_root, file), 'rb') as f:
            data = f.read()
        response = requests.post(_url, data=data)
        if response.status_code == 200:
            res = json.loads(response.text)
            if res["status"] == 0:
                return True
            else:
                print(res["message"])
    except BaseException as e:
        print("remote_upload:{}".format(e))
    return False


def remote_init(ip, remote_root,auth):
    url = "{}/init?root={}&auth={}".format(ip, quote(remote_root), auth)
    return simple_http_get(url)


def remote_download(ip,remote_root,local_root,file,auth):
    _url = "{}/download?root={}&file={}&auth={}".format(ip,quote(remote_root),quote(file),auth)
    cache_file = os.path.join(local_root, utils.cache_dir, os.path.basename(file) + "_" + str(uuid.uuid4()))

    try:
        response = requests.get(_url, timeout=30)
        if response.status_code == 200:
            if response.content != "ERROR":
                with open(cache_file, "wb") as f:
                    f.write(response.content)
                abs_file = os.path.join(local_root, file)
                if not utils.remove_file(local_root, file):
                    print("download remove local error:{}".format(abs_file))
                else:

                    if utils.move_file(cache_file, abs_file):
                        return True
                    else:
                        print("download file cache -> local error:{}".format(cache_file))

            else:
                print("download error,maybe server not root:{} file:{}".format(remote_root,file))
        else:
            print("response.status_code: {}".format(response.status_code))
    except BaseException as e:
        import traceback
        traceback.print_exc()
        print(e)
    if os.path.exists(cache_file):
        os.remove(cache_file)
    return False


def read_config():
    config_file = os.path.join(".", utils.config_name)
    with open(config_file, 'r') as f:
        ip, remote_path,auth = f.read().replace("\n","").split("\t")
    return ip, remote_path, auth


def tree_join_path(root, file):
    if not root or root == ".":
        return file
    return "{}/{}".format(root, file)


def diff():
    diff_dict = {
        remote_only: dict(),
        modify: dict(),
        local_only: dict(),
    }
    if not test():
        print("Error: test is error!")
        return None
    ip, remote_path, auth = read_config()
    local_path = "."
    remote_tree_dict = remote_tree(ip, remote_path, auth)
    if remote_tree_dict is None:
        print("Error: server maybe timeout.")
    local_tree_dict = utils.get_dir_tree(local_path)
    relative_path = "."
    _d = [(relative_path, list(remote_tree_dict.values())[0], list(local_tree_dict.values())[0])]
    while len(_d) > 0:
        _relative_path, _r, _l = _d.pop(0)
        for k in _r:
            _now_relative_path = tree_join_path(_relative_path, k)
            if k in _l:
                if isinstance(_r[k], dict):
                    if isinstance(_l[k], dict):
                        # 远程是文件夹 本地是文件夹
                        _d.append((_now_relative_path,_r[k],_l[k]))
                    else:
                        # 远程是文件夹 本地是文件
                        diff_dict[remote_only][_now_relative_path] = _r[k]
                        diff_dict[local_only][_now_relative_path] = _l[k]
                else:
                    if isinstance(_l[k], dict):
                        # 远程是文件 本地是文件夹
                        diff_dict[remote_only][_now_relative_path] = _r[k]
                        diff_dict[local_only][_now_relative_path] = _l[k]
                    else:
                        # 远程是文件 本地是文件
                        if _r[k] != _l[k]:
                            diff_dict[modify][_now_relative_path] = "{}_{}".format(_r[k],_l[k])
                _l.pop(k)
            else:
                diff_dict[remote_only][_now_relative_path] = _r[k]
        for k in _l:
            _now_relative_path = tree_join_path(_relative_path, k)
            diff_dict[local_only][_now_relative_path] = _l[k]
    print("Diff:\nRemote root: '{}'".format(remote_path))
    utils.print_dict(diff_dict)
    return get_tree_leaf(diff_dict)


def get_tree_leaf(tree_dict):
    new_tree = dict()
    for k, v in tree_dict.items():
        new_tree[k] = []  # (bool,file) : True is dir, False is file
        for name, _d in v.items():
            dir_list = [(name, _d)]
            while len(dir_list) > 0:
                now_path, _d = dir_list.pop()
                if isinstance(_d, dict):
                    new_tree[k].append((True, now_path))
                    for next_name, next_dict in _d.items():
                        next_path = tree_join_path(now_path, next_name)
                        dir_list.append((next_path, next_dict))
                else:
                    new_tree[k].append((False, now_path))
    utils.print_dict(new_tree)
    return new_tree


def push(diff_dict):
    re_bool = True
    try:
        print("Push start")
        ip, remote_path, auth = read_config()
        local_path = "."
        for _, d in tqdm.tqdm(diff_dict[remote_only], desc="Delete", ncols=0):
            if not remote_remove(ip, remote_path, d, auth):
                print("{}: file remove fault".format(d))
                re_bool = False
        for _, m in tqdm.tqdm(diff_dict[modify], desc="Modify", ncols=0):
            if not remote_upload(ip, remote_path, local_path, m, auth):
                print("{}: file modify fault".format(m))
                re_bool = False
        for is_dir, a in tqdm.tqdm(diff_dict[local_only], desc="Add", ncols=0):
            if is_dir:
                if not remote_mkdir(ip, remote_path, a, auth):
                    print("{}: dir creat fault".format(a))
                    re_bool = False
            else:
                if not remote_upload(ip, remote_path, local_path, a, auth):
                    print("{}: file add fault".format(a))
                    re_bool = False
        print("Push end")
        return re_bool
    except BaseException as e:
        print("error: {}".format(e))
        return False


def pull(diff_dict):
    re_bool = True
    try:
        print("Pull start")
        ip, remote_path, auth = read_config()
        local_path = "."
        for _, d in tqdm.tqdm(diff_dict[local_only], desc="Delete", ncols=0):
            if not utils.remove_file(local_path,d):
                print("{}: file remove fault".format(d))
                re_bool = False
        for _, m in tqdm.tqdm(diff_dict[modify], desc="Modify", ncols=0):
            if not remote_download(ip, remote_path, local_path, m, auth):
                print("{}: file modify fault".format(m))
                re_bool = False
        for is_dir, a in tqdm.tqdm(diff_dict[remote_only], desc="Add", ncols=0):
            if is_dir:
                local_file = os.path.join(local_path,a)
                if not os.path.exists(local_file):
                    os.makedirs(local_file)
                    if not os.path.exists(local_file):
                        print("{}: dir creat fault".format(a))
                        re_bool = False
            else:
                if not remote_download(ip, remote_path, local_path, a, auth):
                    print("{}: file add fault".format(a))
                    re_bool = False
        print("Pull end")
        return re_bool
    except BaseException as e:
        print("error: {}".format(e))
        return False


def test():
    try:
        ip, remote_path, auth = read_config()
        local_path = "."
        b, m = utils.test_dir(local_path)
        if not b:
            print("local error:{}".format(m))
            return False
        return remote_test(ip, remote_path, auth)
    except BaseException as e:
        print("error: {}".format(e))
        return False


def init(ip,remote_path):
    try:
        config_file = os.path.join(".", utils.config_name)
        if os.path.exists(config_file):
            print("{}: config exists".format(config_file))
            return False
        else:
            auth = str(uuid.uuid4())
            if not remote_init(ip,remote_path,auth):
                print("{}: remote error".format(config_file))
                return False
            with open(config_file, 'w') as f:
                f.write("{}\t{}\t{}".format(ip, remote_path, auth))
            utils.creat_ignore(".")
        return test()
    except BaseException as e:
        print("error: {}".format(e))
        return False

if __name__ == "__main__":
    pass
    #init("http://127.0.0.1:8889",r"C:\Users\zhangqiSX3552\Desktop\testFS")
    # print(json.dumps(diff(), indent=4, sort_keys=True))
    # _diff_dict = diff()
    # push(_diff_dict)