## R File Sync
> 这是一个极其简单的本地代码与开发机同步程序。如果你的开发机没有跳板机之类的，那么你可以选择更好的方式。
### Explain
- RFS 由http服务端和客户端组成，所以天生支持7层负载。
- 这是一个代码同步工具，所以不要用来同步**大型文件**!!
- 请务必认真核实同步正确性，如果误删，不要**进行其他操作**，尽快去`.backup`寻找。
- RFSserver.py 是服务端，在服务器启动即可，一台机器启动一个实例就可以，保持后台运行，省力省心。
- RFS.py 是客户端，直接运行可显示使用帮助，强烈建议把RFS.py打包成可执行文件，在环境变量中指明，使用更简单。
- 需要保证local path 和 remote path 的所有文件多有读写权限。
- `init`需要remote path，而且 remote path必须为空文件夹。
- 只支持单文件与单文件同步，不支持多对一，当然可以自己探索，但不推荐使用。
- `init`会在服务端创建3个文件，客户端创建3个文件
    -`.auth`:鉴权文件，不可删除，remote path存在。
    - `.FSconfig`:远程服务配置，不可删除，删除=没有`init`，local path存在。
    - `.backup`:最近删除的文件备份，备份文件会覆盖，删除文件夹也会自动创建。
    - `.FSignore`: 类似于`.gitignore`，可自行填写。

### requests
- json
- argparse
- aiofiles
- tornado
- requests
- tqdm
- urllib
- hashlib
- shutil
- pyinstaller
### Usage
- server: `python3 RFSserver.py port`
- client: 
    - `pyinstaller --onefile RFS.py` 生成的可执行程序在./dist/RFS/中
    - 把程序添加到环境变量
    - `RFS`
### Contact
- Name: Roney
- Email: 648662976@qq.com