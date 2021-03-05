#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
这是R File Sync的启动端
建议编译成exe,放在环境变量中使用
"""
__author__ = 'Roney'

from client import *
import sys

def print_help():
    info = """
****************** R File Sync ******************
This is a client and the work path can only be the current path!
Usage: rfs.py Action [Arguments]
Action:
    initialize: rfs.py init remote_server remote_path
                # Initialize the work path and the remote path. The remote path must not exist.
    test:       rfs.py test
                # Test the read and write permissions of both files.
    different:  rfs.py diff
                # Compare the differences between the both files.
    push:       rfs.py push [y]
                # Synchronize local files to the server.
    pull:       rfs.py pull [y]
                # Synchronize server files to the local.
Explain:
    [y] stands for optional, so I recommend not using it.

    """
    print(info)


def print_error(info,b_help=False):
    print("******************\n{}\n******************".format(info))
    if b_help:
        print_help()


def print_success():
    print("\n******************\nRun success!!!\n******************")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
    else:
        action = sys.argv[1]
        if action == "init":
            if len(sys.argv) == 4:
                remote_server,remote_path = sys.argv[2],sys.argv[3]
                if init(remote_server, remote_path):
                    print_success()
                else:
                    print_error("remote_server:{} remote_path:{} not init.".format(remote_server,remote_path))
            else:
                print_error("Input error.", True)
        elif action == "test":
            if test():
                print_success()
            else:
                print_error("Test error.")
        elif action == "diff":
            if diff() is not None:
                print_success()
            else:
                print_error("Diff error.")

        elif action == "push":
            diff_dict = diff()
            if diff_dict:
                if len(sys.argv) >= 3:
                    c = sys.argv[2].upper()
                else:
                    c = input("\nPush [Y/y/N/n] : ").upper()
                if c == "Y":
                    if push(diff_dict):
                        print_success()
                    else:
                        print_error("Push error.")
            else:
                print_error("Diff error.")
        elif action == "pull":
            diff_dict = diff()
            if diff_dict:
                if len(sys.argv) >= 3:
                    c = sys.argv[2].upper()
                else:
                    c = input("\nPush [Y/y/N/n] : ").upper()
                if c == "Y":
                    if pull(diff_dict):
                        print_success()
                    else:
                        print_error("Pull error.")
            else:
                print_error("Diff error.")
        else:
            print_error("Input error.", True)
