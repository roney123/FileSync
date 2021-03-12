#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
这是R File Sync的服务端
建议后台启动，output储存好
请注意有时候权限不足所带来的问题
"""
__author__ = 'Roney'

from abc import ABC

import tornado.web
import tornado.ioloop
import os
import json
import logging
import utils
import argparse
import uuid
import aiofiles

logging = logging.getLogger()
logging.setLevel("INFO")


def is_auth(root, auth):
    try:
        with open(os.path.join(root, utils.auth_name),"r") as f:
            return auth == f.read().replace("\n", "")
    except BaseException as e:
        logging.warning(e)
    return False


def creat_auth(root, auth):
    with open(os.path.join(root,utils.auth_name), "w") as f:
        f.write(auth)


class AuthHandler(tornado.web.RequestHandler):

    def is_auth(self,root):
        auth = self.get_argument("auth", None)
        if not is_auth(root, auth):
            logging.warning("auth:{} or root:{} is error".format(root, auth))
            self.write(json.dumps(dict(status=1, message="auth:{} or root:{} is error".format(root, auth))))
            return False
        return True


class UploadHandler(AuthHandler, ABC):

    async def post(self):
        root = self.get_argument("root", None)
        relative_file = self.get_argument("file", None)
        if not self.is_auth(root):
            return

        logging.info("UploadHandler root:{} file: {} ".format(root, relative_file))
        abs_file = os.path.join(root, relative_file)
        if os.path.exists(abs_file) and not os.access(abs_file,os.W_OK):
            self.write(json.dumps(dict(status=1, message="no write permission:{}".format(abs_file))))
        else:
            if abs_file:
                logging.info("download file start:{}".format(abs_file))
                cache_file = os.path.join(root, utils.cache_dir, os.path.basename(relative_file)+"_"+str(uuid.uuid4()))
                async with aiofiles.open(cache_file, 'wb') as f:
                    await f.write(self.request.body)
                logging.info("download file end:{}".format(abs_file))
                if utils.remove_file(root, relative_file):
                    if utils.move_file(cache_file, abs_file):
                        self.write(json.dumps(dict(status=0)))
                    else:
                        logging.warning("move file error {} -> {}".format(cache_file,abs_file))
                        self.write(json.dumps(dict(status=1, message="cache to file move error")))
                else:
                    logging.warning("remove file error {}".format(abs_file))
                    self.write(json.dumps(dict(status=1, message="file not remove")))
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            else:
                self.write(json.dumps(dict(status=1, message="file is none")))


class DownloadHandler(AuthHandler, ABC):

    async def get(self):
        root = self.get_argument("root", None)
        relative_file = self.get_argument("file", None)
        if not self.is_auth(root):
            return

        logging.info("DownloadHandler root:{} file: {} ".format(root, relative_file))
        abs_file = os.path.join(root, relative_file)
        if not os.path.exists(abs_file) or not os.access(abs_file, os.R_OK):
            self.write("ERROR")
        else:
            logging.info("read file start:{}".format(abs_file))
            with open(abs_file, 'rb') as f:
                data = f.read()
                logging.info("read file end:{} size:{}".format(abs_file, len(data)))
                self.write(data)


class RemoveHandler(AuthHandler, ABC):

    def get(self):
        root = self.get_argument("root", None)
        relative_file = self.get_argument("file", None)
        if not self.is_auth(root):
            return
        logging.info("RemoveHandler root:{} file: {} ".format(root, relative_file))
        if root and relative_file:
            if os.path.exists(os.path.join(root, relative_file)):
                if utils.remove_file(root, relative_file):
                    self.write(json.dumps(dict(status=0)))
                else:
                    self.write(json.dumps(dict(status=1, message="file not remove")))
            else:

                self.write(json.dumps(dict(status=1, message="file not exists")))
        else:
            self.write(json.dumps(dict(status=1, message="param is none")))


class GetHandler(AuthHandler, ABC):

    def get(self):
        root = self.get_argument("root", None)
        if not self.is_auth(root):
            return
        logging.info("GetHandler root: {}".format(root))
        if not root:
            self.write(json.dumps(dict(status=1, message='path is None')))
        else:
            self.write(json.dumps(dict(status=0, data=utils.get_dir_tree(root))))


class TestHandler(AuthHandler, ABC):

    def get(self):
        root = self.get_argument("root", None)
        if not self.is_auth(root):
            return
        logging.info("TestHandler path: {}".format(root))
        if not root or not os.path.exists(root):
            self.write(json.dumps(dict(status=1, message='path is None or not exists')))
        else:
            b, m = utils.test_dir(root)
            if b:
                self.write(json.dumps(dict(status=0)))
            else:
                self.write(json.dumps(dict(status=1, message=m)))


class InitHandler(tornado.web.RequestHandler, ABC):

    def get(self):
        root = self.get_argument("root", None)
        auth = self.get_argument("auth", None)
        if not auth:
            logging.warning("Init auth is None")
            self.write(json.dumps(dict(status=1, message="Init auth is None")))
        logging.info("InitHandler root: {}".format(root))
        if not root or not os.path.exists(root) or len(os.listdir(root)) > 0:
            self.write(json.dumps(dict(status=1, message='root is None or not exists or root not empty')))
        else:
            try:
                utils.creat_ignore(root)
                creat_auth(root, auth)
            except BaseException as e:
                logging.warning(e)
            if os.path.exists(root) and is_auth(root, auth):
                self.write(json.dumps(dict(status=0)))
            else:
                self.write(json.dumps(dict(status=1, message='path not create or no permission')))


class MkDirHandler(AuthHandler, ABC):

    def get(self):
        root = self.get_argument("root", None)
        relative_path = self.get_argument("path", None)
        if not self.is_auth(root):
            return
        path = os.path.join(root, relative_path)
        logging.info("MkDirHandler relative path: {}".format(relative_path))
        if not path or os.path.exists(path):
            self.write(json.dumps(dict(status=1, message='path is None or exists')))
        else:
            try:
                os.makedirs(path)
            except BaseException as e:
                logging.warning(e)
            if os.path.exists(path):
                self.write(json.dumps(dict(status=0)))
            else:
                self.write(json.dumps(dict(status=1, message='path not create')))


class MainHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        self.write("It's \"R File Sync\".\nIt's not a joke...")


application = tornado.web.Application([
    (r"/upload", UploadHandler),
    (r"/mkdir", MkDirHandler),
    (r"/download", DownloadHandler),
    (r"/remove",  RemoveHandler),
    (r"/get", GetHandler),
    (r"/test", TestHandler),
    (r"/init", InitHandler),
    (r"/init", MainHandler)
])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Parameters for file sync server')
    parser.add_argument('port', type=int, help='server port')
    parser.add_argument('--use_backup', type=bool, default=True, help='use backup dir')
    args = parser.parse_args()
    logging.info("server port: {},backup_dir: {}".format(args.port, args.use_backup))
    if not args.use_backup:
        utils.backup_dir = None
    application.listen(args.port)
    tornado.ioloop.IOLoop.instance().start()
