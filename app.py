import sqlite3
from flask import Flask, flash, redirect, render_template, request, jsonify, session
import random
import requests
import json
import locale

app = Flask(__name__)
app.secret_key = "Sessions"


@app.route("/")
def main():
     if 'username' not in session:
          return redirect("/login")
     elif session['username'] == "":
          return redirect("/login")
     else:
          users = query_db(f"SELECT * FROM users")
          for i in users:
               if session['username'] != i[2]:
                    pass
               else:
                    username = i[2]
                    break
     cash = query_db(f"SELECT cash FROM users WHERE username == '{session['username']}'")[0][0]
     coins = query_db(f"SELECT name, quantity FROM coins WHERE user_id IN (SELECT id FROM users WHERE username == '{session['username']}')")
     return render_template(
          "index.html",
          username=session['username'],
          coins=coins,
          cash=cash
          )

@app.route("/login", methods=['POST', 'GET'])
def login():
     if request.method == "POST":
          username = request.form.get('username')
          password = request.form.get('password')

          users = query_db(f"SELECT * FROM users WHERE username == '{username}' AND password == '{password}'")

          if len(users) < 1:
               return redirect('/login')
          else:
               session['username'] = username
               return redirect("/")
     else:
          return render_template("login.html")

@app.route("/register", methods=['POST', 'GET'])
def register():
     if request.method == "POST":
          username = request.form.get('username')
          password = request.form.get('password')
          confirm = request.form.get('confirm')


          if password == confirm:
               pass
          else:
               return redirect("/")
          users = query_db(f"SELECT * FROM users WHERE username == '{username}'")
          if not users:
               pass
          else:
               return redirect('/register')

          available_id = query_db(f"SELECT id FROM users ORDER BY id DESC LIMIT 1")[0][0]

          query_db(f"INSERT INTO users (id, cash, username, password) VALUES ({int(available_id + 1)}, 10000, '{username}', '{password}')")
          session['username'] = username
          return redirect("/")
     else:
          return render_template("register.html")


@app.route("/logout", methods=['POST', 'GET'])
def logout():
     session['username'] = ""
     return redirect('/login')

@app.route("/sell", methods=['POST'])
def sell():
     name = request.form.get('name')
     quantity = request.form.get('quantity')
     quantity = int(quantity)

     if not name or not quantity:
          return "Empty Fields"

     cash = query_db(f"SELECT cash FROM users WHERE username == '{session['username']}'")[0][0]

     #try:
     # queries api for live prices
     responce = requests.get(f"https://api.coincap.io/v2/assets/{name}")
     object = responce.json()
     # indexes into json object to get desired values
     price = object['data']['priceUsd']
     price = round(float(price), 3)
     
     price = round(price * int(quantity))
     if price < 1:
          price = 3

     user_id = query_db(f"SELECT id FROM users WHERE username == '{session['username']}'")[0][0]

     check = 0
     try:
          check = query_db(f"SELECT * FROM coins WHERE user_id == {user_id} AND name == '{name}'")[0][2]
     except:
          pass

     if quantity > check:
          return "Not enough Couns"

     query_db(f"UPDATE users SET cash = {cash + price} WHERE username == '{session['username']}'")
     if check == quantity:
          query_db(f"DELETE FROM coins WHERE user_id == {user_id} AND name == '{name}'")
     else:
          query_db(f"UPDATE coins SET quantity = {int(check) - int(quantity)} WHERE user_id == {user_id} AND name == '{name}'")
     return redirect("/")
     #except:
          #return "No internet"

@app.route("/buy", methods=['POST'])
def buy():
     name = request.form.get('name')
     quantity = request.form.get('quantity')

     if not name or not quantity:
          return "Empty Fields"

     cash = query_db(f"SELECT cash FROM users WHERE username == '{session['username']}'")[0][0]

     try:
          # queries api for live prices
          responce = requests.get(f"https://api.coincap.io/v2/assets/{name}")
          object = responce.json()
          # indexes into json object to get desired values
          price = object['data']['priceUsd']
          price = round(float(price), 3)
          
          price = round(price * int(quantity))
          if price < 1:
               price = 1

          if cash < price:
               return "Not enough Cash"
          user_id = query_db(f"SELECT id FROM users WHERE username == '{session['username']}'")[0][0]
          check = 0
          try:
               check = query_db(f"SELECT * FROM coins WHERE user_id == {user_id} AND name == '{name}'")[0][2]
          except:
               pass
          query_db(f"UPDATE users SET cash = {cash - price} WHERE username == '{session['username']}'")
          if check == 0:
               query_db(f"INSERT INTO coins VALUES ({user_id},'{name}', {int(quantity)})")
          else:
               query_db(f"UPDATE coins SET quantity = {int(check) + int(quantity)} WHERE user_id == {user_id} AND name == '{name}'")
          return redirect("/")

               # prints results of the comma function
     except:
          return "No internet Connection"

def query_db(text):
     conn = sqlite3.connect("data.db")
     cursor = conn.cursor()
     cursor.execute(f"{text}")
     value = cursor.fetchall()
     conn.commit()
     return value
