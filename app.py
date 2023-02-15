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
from labelme2coco import labelme2coco
from maskrcnn_coco_oyster_training import train_model
from maskrcnn_coco_oyster_testing import test_model
import threading
from lib.threads import ThreadManager

import glob

app = Flask(__name__)
CORS(app)
threadMan = ThreadManager()
process = None


@app.route("/")
def hello_world():
    return "Hello World!"

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/save_json", methods=["POST"])
def save_json():
    data = request.get_json()

    # get data
    username = data["username"]
    album = data["album"]
    labeled_json = data["labeled_json"]

    album_folder = os.path.join("aipart",username,"album",album)
    img_title = labeled_json["imagePath"].split('.')[0]

    # check if the folder is exists
    if not os.path.exists(album_folder):
        # if the album directory does  not exist
        # then create it.
        os.makedirs(album_folder)
    
    img_json = os.path.join(album_folder,img_title+".json")
    img_path = os.path.join(album_folder,labeled_json["imagePath"])
    with open(img_json, "w", encoding="utf-8") as f:
        json.dump(labeled_json, f, ensure_ascii=False)
    
    # check if the picture is exists
    # TODO : save img
    with open(img_path, "wb") as fh:
        fh.write(base64.urlsafe_b64decode(labeled_json["imageData"]))

    return jsonify({"state": "success"})

"""
Description:
    This function will analyze the json file in album, pick up the model basic category information
    and save the category to model folder in json file.
Parameters:
  @ string - annotations_json - annotations_json file path "aipart/jack/album/album_a_coco/annotations.json"
  @ string - save_model - model folder path "aipart/Model/jack/model1"
"""
def save_categories(annotations_json, save_model):
    # after annotations_json file built, we will get categories object.
    # we can save to the model folder
    with open(annotations_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        categories = data["categories"]
    
    # remove categories.json, make sure each time the model categories is latest
    # if last_checkpoint is exists, means the training step already done
    cate_json_path = os.path.join(save_model,"categories.json")
    
    if os.path.exists(cate_json_path):
        os.remove(cate_json_path)
        
    with open(os.path.join(save_model,"categories.json"),"w",encoding="utf-8") as f:
        json.dump(categories,f)

"""
Description:
    This will train model with a unique register name
Parameters:
  @ string - annotations_json - annotations_json file path "aipart/jack/album/album_a_coco/annotations.json"
  @ string - album_folder - album folder path "aipart/jack/album/album_a"
  @ string - save_model - model folder path "aipart/Model/jack/model1"
  @ string - registered_name - {username}_{album} "jack_albuumn_a"
"""
def train_model_final(annotations_json, album_folder, save_model,registered_name):
    if not os.path.exists(save_model):
        os.makedirs(save_model)
        print("| Creating dataset dir:", save_model)

    registered_name = f"{registered_name}_{int(time.time())}"
    print(registered_name,"start to training")
    train_model(registered_name, annotations_json, album_folder, save_model)

@app.route("/training_model", methods=["POST"])
def training_model():
    global process

    data = request.get_json()
    # get data
    username = data["username"]
    album = data["album"]
    model = data["model"]
    id = f"training::{username}::{model}"  

    # prepare data
    album_folder = os.path.join("aipart",username, "album", album)
    annotations_json = os.path.join("aipart",username,"album",album+"_coco","annotations.json")
    save_model = os.path.join("aipart","Model",username,model)

    labelme_json = glob.glob(os.path.join(album_folder, "*.json"))
    
    # Check if thread is already running
    if threadMan.is_running(id):
        return {"status": False, "info": "Training already in progress"}
    
    # if the album is not exists, can not training
    if not os.path.exists(album_folder):
        return {"status": False, "info": "Album data not exists"}

    labelme2coco(labelme_json,annotations_json)

    save_categories(annotations_json, save_model)

    ## use last_checkpoint_path file if exists to determine if the training process is finished or not
    ## but we choose threadMan in the end
    # last_checkpoint_path = os.path.join(save_model,"last_checkpoint")
    # if os.path.exists(last_checkpoint_path):
    #     os.remove(last_checkpoint_path)   

    threadMan.createThread(id, train_model_final, (annotations_json, album_folder, save_model,f"{username}_{album}")) 

    # Return a response immediately
    return jsonify({"message": "Training Waiting"})


@app.route("/training_model_result",methods=["POST"])
def training_model_check():
    data = request.get_json()
    # get data
    username = data["username"]
    album = data["album"]
    model = data["model"]
    id = f"training::{username}::{model}" 

    # Check if thread is already running
    if threadMan.is_running(id):
        return {"status": False, "info": "Training still running"}
    
    # Check if the Model has the output 
    save_model = os.path.join("aipart","Model",username,model)
    if not os.path.exists(save_model):
        return {"status": False, "info": "Training model already deleted."}

    return {"status": True, "info": "Training is finished"}

"""
Description:
    return json file of testing image.
Parameters:
  @ string - test_folder - Predict file path "aipart/jack/Predict"
  @ string - pic_name - picname "202212214.jpg"
  @ string - username - "jack"
  @ string - model - "model1"
"""
def getJsonData(test_folder,pic_name, username, model):
    # pic_data ===> to image
    # TODO change img_str to image.jpg file

    img_path = os.path.join(test_folder, pic_name)
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

@app.route("/testing_pic_result",methods=["POST"])
def testing_pic_result():
    data = request.get_json()

    username = data["username"]
    model = data["model"]
    pic_name = data["pic_name"] # 123.jpg
    pic_title = pic_name.split(".")[0]

    id = f"testing::{username}::{model}::{pic_title}"

    # if the Predict folder did not have this picture, return false
    if not os.path.exists(os.path.join("aipart",username,"Predict",pic_name)):
        return {
             "status":False,"info": "Did not exists this predict"
        }
    
    if threadMan.is_running(id):
        return {
            "status":False,"info": "Testing still running"
        }
    else:
        # perhaps tesing is finished or not exists
        # check result
        img_result_path = os.path.join("aipart",username,"Predict",username+"_*.jpg")

        if glob.glob(img_result_path):
            with open(glob.glob(img_result_path)[0], "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                
            return { 
                        "status":True,
                        "info":"Has result",
                        "result":
                            {"img": encoded_string,
                             "text":[2,3,4]
                            }
                 }
        else:
            return {"status":False,"info": "No result"}

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
    test_model_path = os.path.join("aipart","Model",username,model) 

    # check if the test picture folder is exists
    if not os.path.exists(test_folder):
        # if the album directory does not exist
        # then create it.
        os.makedirs(test_folder)

    # Error status detect
    # 1. training or testing currently
    train_id = f"training::{username}::{model}" 
    test_id = f"testing::{username}::{model}::{pic_title}"
    if threadMan.is_running(test_id):
        return {
            "status":False,"info": "Testing still running"
        }
    
    if threadMan.is_running(train_id):
        return {
            "status":False,"info": "Training Model Step still running"
        }

    # 2. if the model does not exist, can not test
    if not os.path.exists(test_model_path):
        return {
            "status":False,"info": "Model does not exists, can not test image"
        }

    # before testing picture, should remove all the file in the folder
    files = glob.glob(os.path.join(test_folder,"*"))
    for f in files:
        os.remove(f)
    
    img_path = os.path.join(test_folder, pic_name)
    with open(img_path, "wb") as fh:
        fh.write(base64.urlsafe_b64decode(pic_data))
    
    # prepare json file 
    img_json = os.path.join(test_folder,pic_title+".json")
    pic_json = getJsonData(test_folder,pic_name,username,model)
    with open(img_json, "w", encoding="utf-8") as f:
        json.dump(pic_json, f, ensure_ascii=False)

    # start to test image
    registered_name = f"{username}_{model}_{int(time.time())}"
    threadMan.createThread(test_id, test_model, (registered_name, test_pic_json,test_folder,test_model_path)) 

    # Return a response immediately
    return jsonify({"message": "Testing Waiting"})

if __name__ == "__main__":
    app.run()
