import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from flask import Flask, request, jsonify, render_template
import pickle
import math
import os,io
import json
import cv2
import glob
import csv
import numpy.ma as ma
from flask import Flask, render_template
from flask import Flask,render_template, flash, redirect , url_for , session ,request, logging
from werkzeug import secure_filename
from google.cloud import vision
from google.cloud.vision import types
import pytesseract
from PIL import Image
from datetime import date,datetime
import pytz


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/UPLOAD_FOLDER/'

#google vision
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'google_api_account_tocken.json'
client = vision.ImageAnnotatorClient()

#Pyteseract path
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract'

global_template_json_data = ''
global_template_name = ''
template_selected_by_user = ''
global_added_radio_fields = ''

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/home1')
def home1():
    return render_template('home.html')

@app.route('/upload')
def upload():
    template_name = list()
    try:
        template_csv = pd.read_csv('Template_files_DO_NOT_DELETE/template.csv')
        template_name = list(template_csv['template_name'])
    except:
        print('Template.csv file not found')

    return render_template('upload.html',template_names = template_name)

@app.route('/extract_text',methods=['POST'])
def extract_text():

    # Get the form data
    text_data = [x for x in request.form.values()]
    print(text_data)  # format = [algorithm,template_name,form_name]

    # Save the uploaded image to UPLOAD_FOLDER folder
    if request.method == "POST":
        if request.files:
            f = request.files['input_image']
            print(type(f))
            print(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            image_name = os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)).split('/')[-1] # Use this as image name

    # Reading the image uploaded form UPLOAD_FOLDER folder
    img = cv2.imread('static/UPLOAD_FOLDER/'+ image_name)
    dim = (1500, 1400)   # Used in templateCreation.html
    resized_img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

# Croping the image as per template selected and saving to crop_folder_DO_NOT_DELETE
    image_path = r'crop_images_DO_NOT_DELETE/'

    # Check if foder 'crop images' exist or not
    # If not exit the create
    # if exist then delete all containt (make foder empty)
    folder = "crop_images_DO_NOT_DELETE"
    check_folder = os.path.isdir(folder)
    if not check_folder:
        os.makedirs(folder)
        print("created folder : ", folder)
    else:
        #     Delete all privious file in folder
        files = glob.glob(os.path.join('crop_images_DO_NOT_DELETE/*'))
        for file in files:
            os.remove(file)
        print("Removed all data from folder : ", folder)

    # Reading template from template.csv file Converting string to dict type
    df = pd.read_csv('Template_files_DO_NOT_DELETE/template.csv')

    global template_selected_by_user
    template_selected_by_user = text_data[1]     # Accept this field from user
    print("#######Incoming data")
    print(text_data)

    for index, row in df.iterrows():
        if(template_selected_by_user==row['template_name']):
            #print(row[0])
            location_dict = row[1]
            location_dict = location_dict.replace("'",'"')
            location_dict = json.loads(location_dict)

            radio_buttons = row[2]
            print(radio_buttons)
            radio_buttons = radio_buttons.replace("'",'"')
            radio_buttons = json.loads(radio_buttons)
            #print(location_dict)
            #print(type(location_dict))


    #  Save the croped part in folder
    for name,info in location_dict.items():
        print('Name:  '+name)
        print(info)
    #     cv2.imwrite(image_path+ name + ".jpg", img[y1:y2,x1:x2])
        x1 = info['Rectangle']['tx'] + info['Rectangle']['x']
        x2 = info['Rectangle']['tx'] + info['Rectangle']['x'] + info['Rectangle']['width']
        y1 = info['Rectangle']['ty'] + info['Rectangle']['y']
        y2 = info['Rectangle']['ty'] + info['Rectangle']['y'] + info['Rectangle']['height']
        print(x1,x2,y1,y2)
        roi = resized_img[y1:y2,x1:x2]
        # Saving the image with croped name
        cv2.imwrite( image_path+name+".jpg", roi)
        print('-------------------------------------------------------------------------------------------------------------------')

        if(text_data[0]=='googlevision'):
            # Google vision algorithm

            FOLDER_PATH = r'D:\Projects Ongoing\HakerEarth OCR\Flask (Final project)\crop_images_DO_NOT_DELETE'
            extracted_text = {}
            for file in glob.glob("crop_images_DO_NOT_DELETE/*"):
                print(file)
                # Get file name
                image_name = file.split("\\")[-1]
                image_name_without_extension = image_name.split('.')[0]
                print(image_name_without_extension)

                # Pass image to google vision Api to get text
                FILE_PATH = os.path.join(FOLDER_PATH, image_name)

                with io.open(FILE_PATH, 'rb') as image_file:
                    content = image_file.read()
                image = vision.types.Image(content=content)
                response = client.document_text_detection(image=image)
                # Get text
                docText = response.full_text_annotation.text
                text = docText.rstrip("\n").replace('\n',' ')
                # Get confidance
                pages = response.full_text_annotation.pages
            #     print(pages)
                confidance = 0
                count = 0
                for page in pages:
                    for block in page.blocks:
            #             print('block confidence:', block.confidence)
                        confidance = confidance + block.confidence
                        count += 1
                if count!=0:
                    confidance = confidance/count

                if(confidance > 98.00):
                    color = 'green'
                elif(confidance > 95.00):
                    color = 'orange'
                else:
                    color = 'red'

                extracted_text[image_name_without_extension] = {'text':text,'confidance':confidance,'color':color}
                print('############################')
            print(extracted_text)

        else:
            print("########## Pyteseract #########")
            #pyteseract Algorithm
            FOLDER_PATH = r'D:\Projects Ongoing\HakerEarth OCR\Flask (Final project)\crop_images_DO_NOT_DELETE'
            extracted_text = {}
            for file in glob.glob("crop_images_DO_NOT_DELETE/*"):
                print(file)

                # Get file name
                image_name = file.split("\\")[-1]
                image_name_without_extension = image_name.split('.')[0]
                print(image_name_without_extension)


                # loading image
                FILE_PATH = os.path.join(FOLDER_PATH, image_name)
                image = cv2.imread(FILE_PATH,0)

                # Pre-process image here



                #passing image to pyteseract
                data = pytesseract.image_to_data(image, output_type='data.frame') #dataframe
                data = data[data.conf != -1]   # removing blank
                # extracting text
                text = ''
                for  line in data['text']:
                    text = text + ' ' + str(line)
                print(text)

                #confidance
                confidance = data['conf'].mean()


                if(confidance > 90.00):
                    color = 'green'
                elif(confidance > 80.00):
                    color = 'orange'
                else:
                    color = 'red'
                extracted_text[image_name_without_extension] ={'text':text,'confidance':confidance,'color':color}
                print('-------------------------------------------')
            print(extracted_text)


    return render_template('extracted_text.html',extracted_text = extracted_text,extra_radio_buttons = radio_buttons)


@app.route('/upload_create_template')
def upload_create_template():
    return render_template('upload_create_template.html')


@app.route('/template', methods=['POST'])
def template():

    # Save the uploaded image to UPLOAD_FOLDER folder
    if request.method == "POST":
        if request.files:
            f = request.files['input_image']
            print(type(f))
            print(f.filename) # while passing if file name contains space,(,) then it converting to number form
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            file = os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)).split('/')[-1]
            print(file) # So passing this format

    # Get the form data and saving to global variables
    text_data = [x for x in request.form.values()]
    print('In Template: ')
    print(text_data)   # template name used in /save_template so make global
    template_name = text_data[0]
    global global_template_name
    global_template_name = template_name.replace(" ", "")
    # return render_template('temp.html',file_name=f.filename)
    return render_template('templateCreation.html',file_name=file)

@app.route('/passdata',methods = ['POST'])
def passdata():

    # Get json string wrriten in jquey function on click save and save to global variables
    template_json_data = request.form['canvas_data']
     # Added radio buttons list
    print('####### In passdata ########')
    print(template_json_data) # this template data used in /save_template so make global
    global global_template_json_data
    global_template_json_data = template_json_data
    print(global_template_json_data)
    return render_template('success_create_template.html')

@app.route('/passradiobuttons',methods = ['POST'])
def passradiobuttons():

    # Get json string wrriten in jquey function on click save and save to global variables
    added_radio_fields = request.form['added_radio_fields']
    global global_added_radio_fields
    global_added_radio_fields = added_radio_fields
    print('####### In pass radio buttons ########')
    print(added_radio_fields)
    return render_template('success_create_template.html')

@app.route('/save_template')
def save_template():

    print('####### In save_template ########')
    # Getting global data
    print(global_template_name)
    print(global_template_json_data)
    print(type(global_template_json_data))
    index = global_template_json_data.index('mapping_id_name')
    json_modified = global_template_json_data[:index-3] + ',' + global_template_json_data[index-1:]
    # convert to json format
    json_modified = json.loads(json_modified)

    # Creating new dict from extracted infomation having format {name: {info},.....}
    location_dict = {}
    for id,name in json_modified["mapping_id_name"][0].items():
        for k in json_modified["model"][1:]:
            if(k['Rectangle']['id']==id):
                location_dict[name] = k
                print('***********')
    print('Final Json String')
    print(location_dict)

    # Saving extracted information in template.csv file
    # create folder if not exist
    folder = "Template_files_DO_NOT_DELETE"
    check_folder = os.path.isdir(folder)
    if not check_folder:
        os.makedirs(folder)
        print("created folder : ", folder)


    filename = 'Template_files_DO_NOT_DELETE/template.csv'
    heading = ['template_name','data','radio_fields']
    row = list([global_template_name,location_dict,global_added_radio_fields])

    if os.path.exists(filename):
        append_write = 'a' # append if already exists
    else:
        append_write = 'w' # make a new file if not


    with open(filename, append_write) as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        if append_write=='w':
            csvwriter.writerow(heading)

        # writing the data rows
        csvwriter.writerow(row)

    return render_template('success_create_template.html')

@app.route('/save_data', methods=['POST'])
def save_data():
    print("######## In save data #############")
    data = request.form
    print(dict(data))
    for key,value in dict(data).items():
        print(key)
        print(value)
    with open('data.csv', 'w') as f:
        for key in dict(data).keys():
            f.write("%s, %s\n" % (key, dict(data)[key]))

    # Create Folder
    folder = "Data_files_DO_NOT_DELETE"
    check_folder = os.path.isdir(folder)
    if not check_folder:
        os.makedirs(folder)
        print("created folder : ", folder)

    filename = 'Data_files_DO_NOT_DELETE/'+ template_selected_by_user +'.csv'
    print(filename)
    heading = list(data.keys())
    # add data and time  in heading
    heading.insert(0,'Date')
    heading.insert(1,'Time')

    if os.path.exists(filename):
        append_write = 'a' # append if already exists
    else:
        append_write = 'w' # make a new file if not


    with open(filename, append_write) as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        if append_write=='w':
            csvwriter.writerow(heading)

        # writing the data rows
        row = list(data.values())
        # Add date and time
        IST = pytz.timezone('Asia/Kolkata')
        today = date.today()
        today = today.strftime("%d %b %Y")
        now = datetime.now(IST)
        current_time = now.strftime("%H:%M:%S")
        row.insert(0,today)
        row.insert(1,current_time)

        csvwriter.writerow(row)

    return render_template('save_conformation.html',file_name = template_selected_by_user)


if __name__ == "__main__":
    app.secret_key='secret123'
    app.run(debug=True)
