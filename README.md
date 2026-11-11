# DobotHub
DobotHub standardization of python library for usage of Dobot Magician and additional components.

## ✨ Features

## 🏗️ Project structure

## 📦 Getting started
### 🚀 Prerequisites

### 🔌 Hardware setup

## 📖 Usage



## 📡 Communication with the Dobot

### Communication protocol
The base of the communication with the Dobot is the Communication Protocol (https://www.alcom.no/wp-content/uploads/2019/11/Dobot-Communication-Protocol-V1.1.5-1.pdf). It contains a list of all commands the Dobot understands. 

### parser.py
The parser.py file translates between raw bytes to python values. It contains a dictionary with all the relevant translations. 

### message.py
The message.py file builds a structure, that the Dobot can understand the command. It contains functions to send an receive messages from and to the Dobot.

### client.py
In the client.py file the basic Dobot functions are defined.

### dobot.py
In these files the functions we use in the final script are defined. A function can contain several different basic functions from client.py

## 💡 How to add a new function
A new function based on the existing basic functions, defined in the client.py file, can be added easily by defining it in the respective file of the component.

## 🐛 Testing


## 📜 License 
DobotHub based on [dobot-python](https://github.com/AlexGustafsson/dobot-python)
from Alex Gustafsson (MIT-License). DobotHub itself is also licensed under the MIT License; see [LICENSE](LICENSE).