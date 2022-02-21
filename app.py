from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
from moviepy.editor import *
import numpy as np
import time
#import PIL
import tensorflow as tf
from tensorflow import keras
#import urllib.request
from flask import Flask, request, jsonify, send_file, render_template
from flask_restful import Api

app = Flask(__name__)
api = Api(app)
app.secret_key = "secret key"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(APP_ROOT,'static')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 #(max upload 100Mb)

ALLOWED_VIDEO_EXTENSIONS = set(['mp4', 'avi', 'mkv', 'webm'])
ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
MODEL = keras.models.load_model(os.path.join(app.config['UPLOAD_FOLDER'],'model/nsfw_mobilenet2.32.steep 500.drop_0.2_0.4_80_224x224.h5'))
CLASS_NAMES = ['neutral', 'porn', 'sexy']

class video_filtring:

	"""docstring for video_filtring"""
	def __init__(self, video_name, extension = ".mp4"):
		super(video_filtring, self).__init__()
		self.video_name = video_name.split('.')[0]
		self.extension = extension
		self.clip = VideoFileClip(video_name)
		self.safe = list()
		self.unsafe = list()
		self.sexy = list()
		self.neutral = list()
		self.porn = list()
		self.img_size=224


	def frame_predict_ado(self):
		duration = int(self.clip.duration)

		for i in range(duration):
    
		    # screenshot video by time
		    frame = self.clip.get_frame(i)


		    # convert screenshpot to PIL format and resize
		    img =  tf.keras.preprocessing.image.array_to_img(frame)
		    newsize = (self.img_size, self.img_size)
		    img = img.resize(newsize)
		    img_array = keras.preprocessing.image.img_to_array(img)
		    img_array /= 255
		    img_array = tf.expand_dims(img_array, 0) # Create a batch

		    # predict
		    predictions = MODEL.predict(img_array)
		    y_pred = np.argmax(predictions, axis=1)
		    
		    if y_pred==0:
		        self.neutral.append(i)
		    if y_pred==1:
		        self.porn.append(i)
		    if y_pred==2:
		        self.sexy.append(i)


	def frame_predict_child(self):
		duration = int(self.clip.duration)

		for i in range(duration):
    
		    # screenshot video by time
		    frame = self.clip.get_frame(i)

		    # convert screenshpot to PIL format and resize
		    img =  tf.keras.preprocessing.image.array_to_img(frame)
		    newsize = (self.img_size, self.img_size)
		    img = img.resize(newsize)
		    img_array = keras.preprocessing.image.img_to_array(img)
		    img_array /= 255
		    img_array = tf.expand_dims(img_array, 0) # Create a batch

		    # predict
		    predictions = MODEL.predict(img_array)
		    y_pred = np.argmax(predictions, axis=1)
		    
		    if y_pred==0:
		        self.safe.append(i)
		    else:
		        self.unsafe.append(i)
    

	def reduce_list(self, times_list):
		start=times_list[0]
		temp=0
		cut_list=list()
		cut_list.clear()
		for times in times_list:
			if times==start:
				temp=times
			if times==temp+1:
				temp=times
			if times>temp+1:
				cut_list.append((start,temp+1))
				start=times
				temp=times
		cut_list.append((start,temp+1))
		return cut_list

	def filter_reduce_list(self, times_list):
		i=-1
		while True:
			if (i<(len(times_list)-2)):
				i+=1
			else:
				break

			X1,X2=times_list[i]
			Y1,Y2=times_list[i+1]

			if ((Y1-X2)<5):
				del times_list[i:i+1]
				times_list[i]=(X1,Y2)

		j=-1
		while True:
			if (j<(len(times_list)-1)):
				j+=1
			else:
				break

			X,Y=times_list[j]

			if ((Y-X)<3):
				del times_list[j]
				j-=1

		return times_list

	def write_safe_video(self):
		clipes=list()
		clipes.clear()
		reduce_times=self.reduce_list(self.safe)
		safe_times=self.filter_reduce_list(reduce_times)
		for times in safe_times:
			start,end=times
			clipes.append(self.clip.subclip(start,end))
		finale=concatenate_videoclips(clipes)
		name='safe_'+self.video_name.split('/')[-1]+self.extension
		finale.write_videofile(os.path.join(app.config['UPLOAD_FOLDER'],'upload',name))
		return os.path.join('static','upload',name)


	def write_unsafe_video(self):
		clipes=list()
		clipes.clear()
		unsafe_times=self.reduce_list(self.unsafe)
		for times in unsafe_times:
			start,end=times
			clipes.append(self.clip.subclip(start,end))
		finale=concatenate_videoclips(clipes)
		finale.write_videofile(os.path.join(app.config['UPLOAD_FOLDER'],"video/unsafe_video.mp4"))
		return os.path.join('static',"video/unsafe_video.mp4")


	def write_porn_video(self):
		clipes=list()
		clipes.clear()
		unsafe_times=self.reduce_list(self.porn)
		for times in unsafe_times:
			start,end=times
			clipes.append(self.clip.subclip(start,end))
		finale=concatenate_videoclips(clipes)
		finale.write_videofile(os.path.join(app.config['UPLOAD_FOLDER'],"video/porn_video.mp4"))
		return os.path.join('static',"video/neutral_video.mp4")

	def write_sexy_video(self):
		clipes=list()
		clipes.clear()
		unsafe_times=self.reduce_list(self.sexy)
		for times in unsafe_times:
			start,end=times
			clipes.append(self.clip.subclip(start,end))
		finale=concatenate_videoclips(clipes)
		finale.write_videofile(os.path.join(app.config['UPLOAD_FOLDER'],"video/sexy_video.mp4"))
		return os.path.join('static',"video/neutral_video.mp4")

	def write_neutral_video(self):
		clipes=list()
		clipes.clear()
		unsafe_times=self.reduce_list(self.neutral)
		for times in unsafe_times:
			start,end=times
			clipes.append(self.clip.subclip(start,end))
		finale=concatenate_videoclips(clipes)
		finale.write_videofile(os.path.join(app.config['UPLOAD_FOLDER'],"video/neutral_video.mp4"))
		return os.path.join('static',"video/neutral_video.mp4")
		
def allowed_file(filename, extension):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in extension


def remove_upload_file():
	# iterating over each and every folder and file in the path
	
	seconds = time.time() - ( 3 * 60 * 60)
	for root_folder, folders, files in os.walk(os.path.join(app.config['UPLOAD_FOLDER'],"upload")):

		for file in files:

			# file path
			file_path = os.path.join(root_folder, file)

			# comparing the days
			if seconds >= get_file_age(file_path):

				# invoking the remove_file function
				remove_file(file_path)


def get_file_age(path):

	# getting ctime of the file/folder
	# time will be in seconds
	ctime = os.stat(path).st_ctime

	# returning the time
	return ctime


def remove_file(path):

	# removing the file
	if not os.remove(path):

		# success message
		print(f"{path} is removed successfully")

	else:

		# failure message
		print(f"Unable to delete the {path}")


@app.route("/")
def main():
	path = os.path.join(app.config['UPLOAD_FOLDER'],"upload")

	# Check whether the specified path exists or not
	isExist = os.path.exists(path)
	if not isExist:
  
  		os.makedirs(path)
	remove_upload_file()
	return render_template('index.html')

@app.route("/test")
def test():
    return render_template('test.html')

#// $('#download').html(href="{{ url_for('download', file=".concat(data['video'], ")}}"));
@app.route("/download/<path:file>", methods=['GET'])
def download(file):
	return send_file(file, as_attachment=True)

@app.route("/upload", methods=['POST'])
def upload():
	if request.method == 'POST':
		try:
			f = request.files['file']
		except RequestEntityTooLarge:
			return jsonify({'message' : 'Arret du processus',
			          'video' : 'error'})

		
		if f and allowed_file(f.filename, ALLOWED_VIDEO_EXTENSIONS):
			filename=secure_filename(f.filename)
			f.save(os.path.join(app.config['UPLOAD_FOLDER'], 'upload/'+filename))
			video = video_filtring('static/upload/'+filename)
			video.frame_predict_child()
			if len(video.safe) > 0 :
				safe = video.write_safe_video()
				os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'upload/'+filename))
				return jsonify({'message' : 'Processus terminer',
							'video' : safe
							})
			else:
				os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'upload/'+filename))
				return jsonify({'message' : 'Processus terminer',
							'video' : 'unsafe'
							})
		else:
			return jsonify({'message' : 'Arret du processus',
			          'video' : 'error'})



if __name__ == "__main__":
	app.run(debug=True)
