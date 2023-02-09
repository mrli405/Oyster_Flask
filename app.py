from flask import Flask, redirect
import subprocess
import shlex


app = Flask(__name__)

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
        return redirect('success')
    return 'Error!'

1. python
2.

@app.route('/success')
def success():
    return 'Successful!'

@app.route('/success3')
def success3():
    print('Successfuldddddd!')
    return 'ddddd'

if __name__ == '__main__':
    app.run()
