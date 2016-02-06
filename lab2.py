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
		print("h0")
		try:
			client_id = flask.request.args["client_id"]
		except (ValueError, KeyError):
			flask.abort(400, "client_id not found!")
		try:
			redir = flask.request.args["redirect_uri"]
		except (ValueError, KeyError):
			redir = None

		if redir is None:
			return flask.render_template(
				"login.html",
				client_id=client_id
			)
		else:
			return flask.render_template(
				"login.html",
				redirect_uri=redir,
				client_id=client_id
			)


	@app.route("/login", methods=["POST"])
	def post_login():
		try:
			client_id = flask.request.form["client_id"]
		except (ValueError, KeyError):
			flask.abort(400, "client_id not found!")
		try:
			redir = flask.request.form["redirect_uri"]
		except (ValueError, KeyError):
			redir = None
		try:
			email = flask.request.form["email"]
		except (ValueError, KeyError):
			flask.abort(400, "email not found!")
		try:
			password = flask.request.form["pass"]
		except (ValueError, KeyError):
			flask.abort(400, "password no found!")
		user_id = login_hash(email,password)
		q = "SELECT COUNT(*)\
			FROM apps\
			WHERE client_id='{}'".format(client_id)
		r = db.exec_query(q).fetchone()
		if r[0] > 0:
			random.seed(version=2)
			code = random.randint(10000,99999)
			d = datetime.datetime.now() + datetime.timedelta(minutes=10)
			date = d.isoformat()
			q = "INSERT INTO codes VALUES ('{}', '{}', '{}', '{}')".format(client_id, user_id, code, date)
			db.exec_query(q)
			db.commit()
			if redir is None:
				return flask.render_template(
					"code.html",
					code=code
				)
			else:
				flask.redirect(redir + "/?code=" + str(code));
		else:
			flask.abort(400)

	@app.route("/oauth", methods=["POST"])
	def post_oauth():
		try:
			fn = flask.request.form["grant_type"]
		except (ValueError, KeyError):
			flask.abort(400, "grant_type not found!")
		if fn == "access_token":
			try:
				client_id = flask.request.form["client_id"]
			except (ValueError, KeyError):
				flask.abort(400, "client_id not found!")
			try:
				client_secret = flask.request.form["client_secret"]
			except (ValueError, KeyError):
				flask.abort(400, "client_secret not found!")
			try:
				code = flask.request.form["code"]
			except (ValueError, KeyError):
				flask.abort(400, "code not found!")
			q = "SELECT COUNT(*)\
				FROM apps\
				WHERE secret_id = '{}' AND client_id = '{}'".format(secret_id, client_id)
			r = db.exec_query(q).fetchone()
			if r[0]<=0:
				flask.abort(400, "wrong id")
			q = "SELECT expires, user_id\
				FROM codes\
				WHERE code = '{}'".format(code)
			r = db.exec_query(q).fetchone()
			if len(r) > 0:
				d = datetime.datetime.now()
				dt= datetime.datetime.strptime(r[0].split('.')[0],"%Y-%m-%dT%H:%M:%S")
				if dt < d:
					flask.abort(400)
			else:
				flask.abort(400)

			d = datetime.datetime.now().isoformat()
			token = md5((client_id+'token'+d).encode("utf-8")).hexdigest()
			rtoken = md5((client_id+'rtoken'+d).encode("utf-8")).hexdigest()

			date = datetime.datetime.now() + datetime.timedelta(days=365)

			q = "INSERT INTO app_tokens VALUES\
				('{}', '{}', '{}', '{}', '{}')".format(client_id, user_id, token, rtoken, date.isoformat())
			r = db.exec_query(q)
			db.commit()

			return json.dumps({
				"access_token": token,
				"token_type": "bearer",
				"expires_in": 86400,
				"refresh_token": rtoken
			}), 201
		elif fn == "refresh_token":
			try:
				refresh_token = flask.request.form["refresh_token"]
			except (ValueError, KeyError):
				flask.abort(400, "refresh_token not found!")
			q = "SELECT  client_id, user_id FROM app_tokens WHERE refresh_token='{}'".format(r_token)
			r = db.exec_query(q).fetchall()
			if len(r) == 0:
				flask.abort(403)

			client_id = r[0][0]
			user_id = r[0][1]

			d = datetime.datetime.now().isoformat()
			token = md5((client_id+'token'+d).encode("utf-8")).hexdigest()
			rtoken = md5((client_id+'rtoken'+d).encode("utf-8")).hexdigest()

			date = datetime.datetime.now() + datetime.timedelta(days=365)

			q = "INSERT INTO app_tokens VALUES\
				('{}', '{}', '{}', '{}', '{}')".format(client_id, user_id, token, rtoken, date.isoformat())
			r = db.exec_query(q)
			db.commit()

			return json.dumps({
				"access_token": token,
				"token_type": "bearer",
				"expires_in": 86400,
				"refresh_token": rtoken
			}), 201
		else:
			flask.abort(400)

	app.run(debug=True, port=8086)
	
run_server()