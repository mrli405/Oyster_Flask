import json

from flask import Flask, redirect, request, jsonify
from flask_cors import CORS
import subprocess
import shlex
import time

import os


app = Flask(__name__)
CORS(app)

process = None

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/cmd1')
def cmd1():
    # get json data
    # store in local directory
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
           # shlex.split("python aipart/labelme2coco.py aipart/datasets_20220822 aipart/datasets_20220822_coco/result"))
           # shlex.split("python aipart/labelme2coco.py aipart/datasets_20220822 aipart/datasets_20220822_coco/annotations.json"))
            shlex.split("python aipart/labelme2coco.py aipart/datasets_20230209 aipart/datasets_20230209_coco/annotations.json"))
        process.wait()
        return redirect('success')

    return 'Error!'

@app.route('/getjson',methods=["POST"])
def getjson():
    my_json = request.get_json()
    my_age = my_json["age"]
    return jsonify({"name":"abc","age":my_age})

# 原封不动的返回json，表示，可以接受一个json文件，并且返回一个json文件
@app.route('/getjson_and_back',methods=["POST"])
def getjson_and_back():

    my_json = request.form["name"]
    print(type(my_json))
    return my_json

# 接受post+formdata 数据, 使用request.form["XXX"]接受数据
@app.route('/get_data_form_and_back',methods=["POST"])
def get_data_form_and_back():
    my_json = request.form["name"]
    return my_json

#
@app.route('/return_one_json',methods=["POST"])
def return_one_json():
    name = request.form['name']
    city = request.form['city']

    return "{} live in {}".format(name, city)

@app.route('/save_json',methods=["POST"])
def save_json():
    # 1. 得到json文件
    my_json = request.get_json()

    # 2.  保存到时间戳名字文件夹
    folder_name = "datasets_"+time.strftime('%Y%m%d%H%M%S')
    labelme_folder = "aipart/{}".format(folder_name)
    annotations_json_url = "aipart/{}_coco/annotations.json".format(folder_name)

    # 3. 创建文件夹，先判断是否存在该目录
    if not os.path.exists(labelme_folder):
        # if the demo_folder directory is not present
        # then create it.
        os.makedirs(labelme_folder)

    # 4. 保存json到该目录
    with open(labelme_folder+"/my.json", 'w', encoding='utf-8') as f:
        json.dump(my_json, f, ensure_ascii=False)

    # 5. 执行python labelme2coco 代码
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            shlex.split(
                "python aipart/labelme2coco.py {} {}".format(labelme_folder,annotations_json_url)))
        process.wait()

        # 判断annotations.json是否生成，没有生成返回失败
        if (os.path.exists(annotations_json_url)):
            with open(annotations_json_url) as json_file:
                data = json.load(json_file)
                print(json_file)
            return jsonify(data)
        else:
            print("File not Exists")
            return jsonify({"Status": "Fail"})

        return redirect('success')

    return 'Error!'

@app.route('/readjsonfile')
def readjsonfile():
    with open('my.json') as json_file:
        data = json.load(json_file)
        print(json_file)
    resp = jsonify(data)
    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp

@app.route('/success')
def success():
    return 'Successful!'


# testing using another method to run python code
@app.route('/cmd2')
def cmd2():
    from myfun import myffff
    return myffff()


if __name__ == '__main__':
    app.run()
