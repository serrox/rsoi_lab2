import flask, os
import sqlite3
import json
from hashlib import md5
import datetime
import random

class db:
    @staticmethod
    def get():
        db = getattr(flask.g, '_database', None)
        if db is None:
            db = flask.g._database = sqlite3.connect("data.db")
        return db

    @staticmethod
    def close():
        db = getattr(flask.g, '_database', None)
        if db is not None:
            db.close()

    @staticmethod
    def exec_query(q):
        cursor = db.get().cursor()
        cursor.execute(q)
        return cursor

    @staticmethod
    def commit():
        db.get().commit()

    @staticmethod
    def next_id(column, table):
        q = "SELECT {0} FROM {1} ORDER BY {0} DESC".format(column, table)
        r = db.exec_query(q).fetchone()
        return int(r[0])+1

def run_server():
	app = flask.Flask(__name__)
	
	def login_hash(email, passwd):
		return md5((email+"salt"+passwd).encode("utf-8")).hexdigest()

	@app.route("/")
	def main_page():
		return "Sample Text"
	
	@app.route("/status")
	def status():
		return "Statu: OK"
	
	@app.route("/register", methods=["GET"])
	def reg_page_get():
		return flask.render_template("registration.html")
	
	@app.route("/register", methods=["POST"])
	def reg_page_post():
		p = flask.request.form
		q = "SELECT count(*)\
			FROM users\
			WHERE email='{}'".format(p['email'])
		r = db.exec_query(q).fetchone()
		if r[0]==0:
			user_id = md5((p['email']+'salt').encode("utf-8")).hexdigest()
			user_hash = login_hash(p['email'],p['pass'])
			q = "INSERT INTO users VALUES\
				('{}', '{}', '{}', '{}', '')".format(
				user_id, user_hash, p['email'], p['name']
			)
			db.exec_query(q)
			db.commit()
			return "Registration complete"
		else:
			return flask.render_template("Registration.html", error="There is user with such name or email already")

	@app.route("/login", methods=["GET"])
	def get_login():
		client_id = flask.request.args["client_id"]
		redir = flask.request.args["redirect_uri"]
		if client_id is None:
			flask.abort(400, "client_id no found!")
		if redir is None:
			flask.abort(400, "redirect url no found!")

		return flask.render_template(
			"login.html",
			redirect_uri=redir,
			client_id=client_id
		)

	@app.route("/login", methods=["POST"])
	def post_login():
		client_id = flask.request.form["client_id"]
		redir = flask.request.form["redirect_uri"]
		email = flask.request.form["email"]
		password = flask.request.form["pass"]
		if client_id is None:
			flask.abort(400, "client_id no found!")
		if redir is None:
			flask.abort(400, "redirect url no found!")
		user_id = login_hash(email,password)
		q = "SELECT COUNT(*)\
			FROM apps\
			WHERE client_id='{}'".format(client_id)
		r = db.exec_query(q).fetchone()
		if r[0] > 0:
			random.seed(version=2)
			code = random.randint(10000,99999)

			return flask.render_template(
				"code.html",
				code=code
			)
		else:
			flask.abort(400)

	app.run(debug=True, port=8086)
	
run_server()