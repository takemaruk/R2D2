# -*- coding: utf-8 -*-
import socket
import time
import cv2
import string
import xml.etree.ElementTree as ET
from mutagen.mp3 import MP3 as mp3
import pygame
import RPi.GPIO as GPIO
import glob
import random
import os

class Sound:
	def __init__(self):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		self.dir = 'sounds'
	
	def is_play(self):
		return pygame.mixer.music.get_busy()

	def play(self,filename,wait_play_end = True):
		filepath = os.path.join(self.dir,filename)
		pygame.mixer.music.load(filepath) #音源を読み込み
		pygame.mixer.music.play(1)
		if wait_play_end:
			while self.is_play():
				continue

class Ear:
	host = 'localhost'
	port = 10500

	def __init__(self):
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((self.host, self.port))

	def listen(self):
		data = ""
		while (string.find(data, "\n.") == -1):
			data = data + self.client.recv(1024)
		print(data)
		self.word = ""
		for line in data.split('\n'):
			index = line.find('WORD="')
		
			if index != -1:
				line = line[index + 6:line.find('"', index + 6)]
				if line != "[s]":
					self.word = self.word + line
		
		self.score = 0
		for line in data.split('\n'):
			index = line.find('CM="')
	
			if index != -1:
				line = line[index+4:line.find('"', index + 6)]
				if line != "[s]":
					self.score = float(line)

	def get_word(self):
		return self.word
	
	def get_score(self):
		return self.score
	
	def __del__(self):
		self.client.close()

class Light:
	led_pin = 26
	def __init__(self):
		GPIO.setmode(GPIO.BCM)                       
		GPIO.setup(self.led_pin,GPIO.OUT)
		self.light_flag = False
	
	def on(self):
		GPIO.output(self.led_pin,GPIO.HIGH)
		self.light_flag = True

	def off(self):
		GPIO.output(self.led_pin,GPIO.LOW)
		self.light_flag = False
	
	def is_Light(self):
		return self.light_flag
	
	def __del__(self):
		self.off()

class Mouse:
	word_dictionary = {
		"ohayou"	:{"filename"	:"R2_good_morning.mp3"		,"threshold":0.75},
		"konnichiha":{"filename"	:"R2_hello.mp3"				,"threshold":0.75},
		"konbanwa"	:{"filename"	:"R2_good_night.mp3"		,"threshold":0.75},
		"STARWARS"	:{"filename"	:"STAR_WARS_main_theme.mp3"	,"threshold":0.75},
		"ABLab"		:{"filename"	:"R2_ABLab.mp3"				,"threshold":0.75},
		"pien"		:{"filename"	:"Shocked R2D2.mp3"			,"threshold":0.75},
	}

	
	def __init__(self):
		self.sound = Sound()
		self.rondom_sounds_list = glob.glob(os.path.join(self.sound.dir,"*.mp3"))
		self.rondom_sounds_list = [os.path.basename(p) for p in glob.glob(os.path.join(self.sound.dir,"*.mp3")) if os.path.isfile(p)]
	
	def talk(self,word,score):
		wait_play_end = True
		filename  = self.word_dictionary[word]["filename"]
		threshold = self.word_dictionary[word]["threshold"]

		if(score > threshold):
			if word == "STARWRS":
				wait_play_end = False
			self.sound.play(filename,wait_play_end=wait_play_end)

	def random_talk(self):
		filename = random.choice(self.rondom_sounds_list)
		self.sound.play(filename)

class Eye:
	files = {
		"shutter"	:"Camera-Phone03-1.mp3",
		"R2_photo"	:"R2_photo.mp3"
		}

	def __init__(self):
		self.sound   = Sound()
		self.capture = cv2.VideoCapture(0)

	def shoot(self):
		#R2 speek
		self.sound.play(self.files["shutter"])
		#シャッター音
		self.sound.play(self.files["R2_photo"])

		#shoot photo
		ret, frame = self.capture.read()
		#write image
		now = time.ctime()
		cv2.imwrite(now+'.jpg', frame)
		#表示
		cv2.imshow('camera capture', frame)
		#待つ（ms）
		cv2.waitKey(3000)
		#開放、ウィンドウを閉じる
		cv2.destroyAllWindows()
		
	def __del__(self):
		self.capture.release()

class R2D2:
	word_dictionary = {
		"wake_up"	:{"word":"R2"	,"threshold":0.50},
		"end"		:{"word":"bye"	,"threshold":0.95,"filename":"R2_bye.mp3"},
		"shoot"		:{"word":"photo","threshold":0.75}
	}

	def __init__(self):
		self.wake_up_flag = False
		self.end_flag	  = False

		self.eye   = Eye()
		self.mouse = Mouse()
		self.ear   = Ear()
		self.light = Light()

	def check_word(self,word,score,key):
		return word == self.word_dictionary[key]["word"] and score > self.word_dictionary[key]["threshold"]

	def run(self):
		self.ear.listen()
		word  = self.ear.get_word()
		score = self.ear.get_score()
			
		if self.check_word(word,score,"wake_up"):
			self.wake_up_flag = True
			self.light.on()
			self.mouse.random_talk()

		print("word:{},score:{},wake up:{}".format(word,score,self.wake_up_flag))

		if self.wake_up_flag:
			# R2 Talk
			print(self.mouse.word_dictionary.keys())
			if word in self.mouse.word_dictionary:
				print("talk word:{}".format(word))
				self.mouse.talk(word,score)
				self.wake_up_flag = False
				self.light.off()

			# R2 Shoot
			elif self.check_word(word,score,"shoot"):
				self.eye.shoot()
				self.wake_up_flag = False
				self.light.off()

			# sytem end
			elif self.check_word(word,score,"end"):
				self.mouse.sound.play(self.word_dictionary["end"]["filename"])
				self.end_flag = True

	def get_end_flag(self):
		return self.end_flag

	def __del__(self):
		del self.eye
		del self.ear
		del self.mouse
		del self.light


if __name__ == '__main__':
	print('----------START!----------\n')

	R2 = R2D2()
	try:
		while True:
			R2.run()
			if R2.get_end_flag():
				del R2
				break

	except KeyboardInterrupt:
		del R2