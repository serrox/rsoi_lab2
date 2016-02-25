import sys
import json, requests
import flask
import os
import webbrowser

authenticate_code = ""
access_token = ""
client_id = "1"
client_secret = "2"

def get_code():
    app = flask.Flask(__name__)

    def shutdown_flask():
        func = flask.request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return "Done"

    @app.route("/")
    def requst():
        global authenticate_code

        try:
            authenticate_code = flask.request.args["code"]
        except (ValueError, KeyError):
            flask.abort(400, "code not found!")

        shutdown_flask()

        return "Ok"

    app.run(port=8080)

def authenticate():
	global access_token
	params = "grant_type=access_token&code=" + authenticate_code + "&client_id=" + client_id + "&client_secret="+ client_secret
	headers = {
		"Content-type": "application/x-www-form-urlencoded"
	}
	r = requests.post("http://localhost:8086/oauth", data=params,headers=headers).json()
	access_token = r['access_token']
	return

def authenticate_user():
	global authenticate_code
	print('Opening login windows.')
	webbrowser.open_new("http://localhost:8086/login?redirect_uri=http://localhost:8080/&client_id="+client_id)
	get_code()
	return authenticate()

def get_info():
	url = "http://localhost:8086/me"
	headers = { 'Authorization' : 'Bearer ' + access_token}
	r = requests.get(url, headers=headers).json()
	print("About Me")
	print("Name: " + str(r['name']))
	print("E-mail: " + str(r['email']))
	print("About: " + str(r['description']))

	cv_id = r['cv']

	url = "http://localhost:8086/cv?id=" + str(cv_id)
	headers = { 'Authorization' : 'Bearer ' + access_token}
	r = requests.get(url, headers=headers).json()

	print(r)
	print("CV name: " + str(r['name']))
	print("Profession: " + str(r['profession']))
	if str(r['image']) != 'null' :
		print("CV image: " + str(r['image']))
	print("Projects:")
	for proj in r["projects_id"]:
		url = "http://localhost:8086/project?id=" + str(proj)
		headers = { 'Authorization' : 'Bearer ' + access_token}
		r = requests.get(url, headers=headers).json()
		print(" Project name:  " + r["name"])
		print(" Project type:  " + r["type"])
		print(" Project image: " + r["image"])
		print(" ")
	
	return

def find_CVs():
	print(" ")
	print("List all CVs")
	print("First 2")
	url = "http://localhost:8086/search?count=2"
	headers = { 'Authorization' : 'Bearer ' + access_token}
	r = requests.get(url, headers=headers).json()
	for CV in r:
		print("Name:       " + CV["name"])
		print("Profession: " + CV["Profession"])
		if CV["Image"] != "null":
			print("Image:      " + CV["Image"])
		print(" ")
	print("Second 2")
	url = "http://localhost:8086/search?count=2&start=2"
	headers = { 'Authorization' : 'Bearer ' + access_token}
	r = requests.get(url, headers=headers).json()
	for CV in r:
		print("Name:       " + CV["name"])
		print("Profession: " + CV["Profession"])
		if CV["Image"] != "null":
			print("Image:      " + CV["Image"])
		print(" ")
	return

authenticate_user()
get_info()
find_CVs()