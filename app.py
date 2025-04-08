from flask import Flask  #import flask module 

app = Flask(__name__)    #create an instance of the Flask class


import config
import models
import routes

if __name__ == '__main__':
    app.run(debug=True)  #run the application