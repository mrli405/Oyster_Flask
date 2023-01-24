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
           shlex.split("python aipart/labelme2coco.py aipart/datasets_20220822 aipart/datasets_20220822_coco/c3 --labels aipart/labels.txt"))
        return redirect('success')
    return 'Waiting!'

@app.route('/success')
def success():
    return 'Successful!'

if __name__ == '__main__':
    app.run()
