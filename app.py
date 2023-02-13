import json

from flask import Flask, redirect, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import shlex
import time
import os
import shutil
import base64
from PIL import Image


app = Flask(__name__)
CORS(app)

process = None


@app.route("/")
def hello_world():
    return "Hello World!"


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/cmd1")
def cmd1():
    # get json data
    # store in local directory
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            shlex.split(
                "python labelme2coco.py aipart/demo aipart/demo_coco/annotations.json"
            )
        )
        process.wait()
        return "success -- labelme2coco"

    return "Error!"

# @app.route('/checkstate')
# def checkstate():
#     global process
#     if process is None or process.poll() is not None:

@app.route("/cmd2")
def cmd2():
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            # shlex.split(
            #     "python maskrcnn_coco_oyster_training.py aipart/demo_train aipart/demo_coco/annotations.json aipart/demo aipart/demo_model/output"
            # )
            [
                "python",
                "maskrcnn_coco_oyster_training.py",
                "aipart/demo_train",  # input training dataset name
                "aipart/demo_coco/annotations.json",  # input annotated file
                "aipart/demo",  # input image dir
                "aipart/demo_model/output",  # output dir
            ]
        )
        process.wait()
        return "success --- training"

    return "Error!"


@app.route("/cmd3")
def cmd3():
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            shlex.split(
                "python maskrcnn_coco_oyster_testing.py '20220822_144720' 'datasets_test/20220822_144720.json'  aipart/datasets_test aipart/test_model/output"
            )
        )
        process.wait()
        return "success --- testing"

    return "Error!"


# airpart/jack/lambel1/mode1
#                     /mode2
#                     /mode3


@app.route("/labelme2coco", methods=["POST"])
def labelme2coco():
    my_json = request.get_json()

    # 2.  save folder seperated by userid or username
    labelme_folder = "aipart/demo/"
    annotations_json_url = "aipart/demo_coco/annotations.json"

    # 3. ensure the folder exists
    if not os.path.exists(labelme_folder):
        # if the demo_folder directory is not present
        # then create it.
        os.makedirs(labelme_folder)

    # 4. save json file to folder
    with open(labelme_folder + "/origin.json", "w", encoding="utf-8") as f:
        json.dump(my_json, f, ensure_ascii=False)

    # 5. run python labelme2coco code
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            shlex.split(
                "python labelme2coco.py {} {}".format(
                    labelme_folder, annotations_json_url
                )
            )
        )

        process.wait()

        # check if annotations.json create or not
        if os.path.exists(annotations_json_url):
            with open(annotations_json_url) as json_file:
                data = json.load(json_file)

            return jsonify(data)
        else:
            print("File not Exists")
            return jsonify({"Status": "Fail"})

        return redirect("success")

    return "Error!"

@app.route("/labelme2coco_old", methods=["POST"])
def labelme2coco_old():
    my_json = request.get_json()

    # 2.  save folder seperated by userid or username
    labelme_folder = "aipart/labelme2coco/user1/labels"
    annotations_json_url = "aipart/labelme2coco/user1/coco/annotations.json"

    # 3. ensure the folder exists
    if not os.path.exists(labelme_folder):
        # if the demo_folder directory is not present
        # then create it.
        os.makedirs(labelme_folder)

    # 4. save json file to folder
    with open(labelme_folder + "/origin.json", "w", encoding="utf-8") as f:
        json.dump(my_json, f, ensure_ascii=False)

    # 5. run python labelme2coco code
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            shlex.split(
                "python aipart/labelme2coco.py {} {}".format(
                    labelme_folder, annotations_json_url
                )
            )
        )

        process.wait()

        # check if annotations.json create or not
        if os.path.exists(annotations_json_url):
            with open(annotations_json_url) as json_file:
                data = json.load(json_file)

            return jsonify(data)
        else:
            print("File not Exists")
            return jsonify({"Status": "Fail"})

        return redirect("success")

    return "Error!"

@app.route("/save_json", methods=["POST"])
def save_json():
    data = request.get_json()

    # get data
    username = data["username"]
    album = data["album"]
    labeled_json = data["labeled_json"]

    album_folder = os.path.join("aipart",username,"album",album)
    img_name = labeled_json["imagePath"].split('.')[0]

    # check if the folder is exists
    if not os.path.exists(album_folder):
        # if the album directory does  not exist
        # then create it.
        os.makedirs(album_folder)
    
    img_json = os.path.join(album_folder,img_name+".json")
    img_path = os.path.join(album_folder,labeled_json["imagePath"])
    with open(img_json, "w", encoding="utf-8") as f:
        json.dump(labeled_json, f, ensure_ascii=False)
    
    # check if the picture is exists
    # TODO : save img
    with open(img_path, "wb") as fh:
        fh.write(base64.urlsafe_b64decode(labeled_json["imageData"]))

    return jsonify({"state": "success"})

@app.route("/training_model", methods=["POST"])
def training_model():
    global process

    data = request.get_json()
    # get data
    username = data["username"]
    album = data["album"]
    model = data["model"]

    # prepare data
    album_folder = os.path.join("aipart",username, "album", album)
    annotations_json = os.path.join("aipart",username,"album",album+"_coco","annotations.json")
    save_model = os.path.join("aipart","Model",username,model)

    # label2coco
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            shlex.split(
                "python labelme2coco.py {} {}".format(album_folder,annotations_json)
            )
        )
        process.wait()
        

        # after annotations_json file built, we will get categories object.
        # we can save to the model folder
        with open(annotations_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            categories = data["categories"]
        
        # remove categories.json, make sure each time the model categories is latest
        # if last_checkpoint is exists, means the training step already done
        cate_json_path = os.path.join(save_model,"categories.json")
        last_checkpoint_path = os.path.join(save_model,"last_checkpoint")
        if os.path.exists(cate_json_path):
            os.remove(cate_json_path)
            with open(os.path.join(save_model,"categories.json"),"w",encoding="utf-8") as f:
                json.dump(categories,f)
        
        if os.path.exists(last_checkpoint_path):
            os.remove(last_checkpoint_path)

        # training album data 
        process = subprocess.Popen(
            [
                "python",
                "maskrcnn_coco_oyster_training.py",
                "aipart/demo_train",  # input training dataset name
                annotations_json,  # input annotated file
                album_folder,  # input image dir
                save_model,  # output dir
            ]
        )
        
        return jsonify({"state": "success"})
    
    return jsonify({"state": "error"})

def getJsonData(pic_data,test_folder,pic_name, username, model):
    # pic_data ===> to image
    # TODO change img_str to image.jpg file
    img_path = os.path.join(test_folder, pic_name)
    with open(img_path, "wb") as fh:
        fh.write(base64.urlsafe_b64decode(pic_data))

    # get image width and height
    img = Image.open(img_path)
    # get width and height
    width = img.width
    height = img.height

    # get category info by username and model
    cate_json_path = os.path.join("aipart","Model",username,model,"categories.json")
    with open(cate_json_path,"r",encoding="utf-8") as f:
        categories = json.load(f)
    
    return {
                "images": [
                    {
                        "height": height,
                        "width": width,
                        "id": 0,
                        "file_name": pic_name
                    }
                ],
                "categories": categories, 
                "annotations": [ ]
            }

    

@app.route("/testing_pic", methods=["POST"])
def testing_pic():
    global process

    # get data
    data = request.get_json()
    username = data["username"]
    model = data["model"]
    pic_name = data["pic_name"] # 123.jpg
    pic_data = data["pic_data"] # picture file 


    # prepare data
    pic_title = pic_name.split(".")[0]
    test_pic_json = os.path.join("aipart",username,"Predict",pic_title+".json")
    test_folder = os.path.join("aipart",username,"Predict")
    test_model = os.path.join("aipart","Model",username,model) 

    # check if the folder is exists
    if not os.path.exists(test_folder):
        # if the album directory does  not exist
        # then create it.
        os.makedirs(test_folder)
    
    for filename in os.listdir(test_folder):
        file_path = os.path.join(test_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    img_json = os.path.join(test_folder,pic_title+".json")

    pic_json = getJsonData(pic_data,test_folder,pic_name,username,model)

    with open(img_json, "w", encoding="utf-8") as f:
        json.dump(pic_json, f, ensure_ascii=False)

    # test image
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            [   
                "python",
                "maskrcnn_coco_oyster_testing.py",
                pic_name,  
                test_pic_json, 
                test_folder,  
                test_model
            ]
        )
        
        return jsonify({"state": "success"})

    return jsonify({"state": "error"})

@app.route("/testing_pic_old", methods=["POST"])
def testing_pic_old():
    global process

    # get data
    data = request.get_json()
    username = data["username"]
    model = data["model"]
    pic_data = data["pic_data"] # picture file 
    pic_json = data["pic_json"]

    # prepare data
    pic_name = pic_json["images"][0]["file_name"].split(".")[0]
    test_pic_json = os.path.join("aipart",username,"Predict",pic_name+".json")
    test_folder = os.path.join("aipart",username,"Predict")
    test_model = os.path.join("aipart","Model",username,model) 

    # check if the folder is exists
    if not os.path.exists(test_folder):
        # if the album directory does  not exist
        # then create it.
        os.makedirs(test_folder)

    img_json = os.path.join(test_folder,pic_name+".json")
    img_path = os.path.join(test_folder,pic_json["images"][0]["file_name"])
    with open(img_json, "w", encoding="utf-8") as f:
        json.dump(pic_json, f, ensure_ascii=False)

    # TODO change img_str to image.jpg file
    with open(img_path, "wb") as fh:
        fh.write(base64.urlsafe_b64decode(pic_data))

    # test image
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            [   
                "python",
                "maskrcnn_coco_oyster_testing.py",
                pic_name,  
                test_pic_json, 
                test_folder,  
                test_model
            ]
        )
        
        return jsonify({"state": "success"})

    return jsonify({"state": "error"})


@app.route("/save_json2", methods=["POST"])
def save_json2():
    my_json = request.get_json()

    folder_name = "datasets_" + time.strftime("%Y%m%d%H%M%S")
    labelme_folder = "aipart/{}".format(folder_name)
    annotations_json_url = "aipart/{}_coco/annotations.json".format(folder_name)

    if not os.path.exists(labelme_folder):
        # if the demo_folder directory is not present
        # then create it.
        os.makedirs(labelme_folder)

    with open(labelme_folder + "/my.json", "w", encoding="utf-8") as f:
        json.dump(my_json, f, ensure_ascii=False)

    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            shlex.split(
                "python aipart/labelme2coco.py {} {}".format(
                    labelme_folder, annotations_json_url
                )
            )
        )
        process.wait()

        if os.path.exists(annotations_json_url):
            with open(annotations_json_url) as json_file:
                data = json.load(json_file)
                print(json_file)
            return jsonify(data)
        else:
            print("File not Exists")
            return jsonify({"Status": "Fail"})

        return redirect("success")

    return "Error!"


@app.route("/success")
def success():
    return "Successful!"


if __name__ == "__main__":
    app.run()
