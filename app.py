
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "matrix-private-key"
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#10131c">
<title>Matrix Messenger</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0; background: #10131c; color: white;
  font-family: Arial, sans-serif; height: 100dvh;
  display: flex; justify-content: center;
}
.app {
  width: 100%; max-width: 600px; height: 100%;
  display: flex; flex-direction: column;
  background: #171b27;
}
header {
  padding: 18px; background: #202638;
  border-bottom: 1px solid #343b50;
}
.logo { font-size: 25px; font-weight: bold; color: #7c9cff; }
.subtitle { font-size: 12px; color: #aab3c8; margin-top: 5px; }
#messages {
  flex: 1; overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 10px;
}
.message {
  background: #282f42; padding: 11px 14px;
  border-radius: 14px; max-width: 85%; overflow-wrap: anywhere;
  align-self: flex-start;
}
.message b { color: #91aaff; font-size: 12px; }
.message p { margin: 7px 0 3px; white-space: pre-wrap; }
.message small { color: #aab3c8; font-size: 10px; }
.system { color: #aab3c8; text-align: center; font-size: 12px; }
form {
  display: flex; gap: 8px; padding: 12px;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  background: #202638;
}
input {
  min-width: 0; flex: 1; border: 1px solid #414b65;
  border-radius: 12px; padding: 13px;
  background: #111521; color: white; font-size: 16px;
}
button {
  border: 0; border-radius: 12px; padding: 0 18px;
  background: #6687ff; color: white; font-weight: bold;
}
#login {
  padding: 12px; display: flex; gap: 8px;
  background: #202638;
}
#login input { width: 100%; }
</style>
</head>
<body>
<div class="app">
  <header>
    <div class="logo">⬡ MATRIX</div>
    <div class="subtitle">MATRIX MOBILE • پیام‌رسان آزمایشی</div>
  </header>

  <div id="login">
    <input id="username" maxlength="24" placeholder="اسم خودت رو بنویس">
    <button id="join" type="button">ورود</button>
  </div>

  <main id="messages">
    <div class="system">به Matrix خوش اومدی.</div>
    <div class="system">برای شروع، اسمت رو وارد کن.</div>
  </main>

  <form id="form">
    <input id="text" maxlength="1000" autocomplete="off"
           placeholder="پیامت رو بنویس..." disabled>
    <button id="send" disabled>ارسال</button>
  </form>
</div>

<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<script>
const messages = document.getElementById("messages");
const username = document.getElementById("username");
const join = document.getElementById("join");
const textInput = document.getElementById("text");
const form = document.getElementById("form");
const send = document.getElementById("send");
let myName = "";
let socket = null;

function addSystem(text) {
  const div = document.createElement("div");
  div.className = "system";
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function addMessage(data) {
  const div = document.createElement("div");
  div.className = "message";
  const name = document.createElement("b");
  name.textContent = data.name || "کاربر";
  const body = document.createElement("p");
  body.textContent = data.text || "";
  const time = document.createElement("small");
  time.textContent = data.time || "";
  div.append(name, body, time);
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

join.addEventListener("click", () => {
  const name = username.value.trim();
  if (!name) {
    username.focus();
    return;
  }
  myName = name;
  socket = io();

  socket.on("connect", () => {
    socket.emit("join", {name: myName});
    username.disabled = true;
    join.disabled = true;
    textInput.disabled = false;
    send.disabled = false;
    addSystem("به سرور Matrix وصل شدی.");
    textInput.focus();
  });

  socket.on("chat_message", addMessage);
  socket.on("notice", data => addSystem(data.text));
  socket.on("connect_error", () => addSystem("اتصال برقرار نشد؛ سرور رو بررسی کن."));
});

form.addEventListener("submit", event => {
  event.preventDefault();
  const text = textInput.value.trim();
  if (!text || !socket || !socket.connected) return;
  socket.emit("chat_message", {text: text});
  textInput.value = "";
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

users = {}

@socketio.on("join")
def on_join(data):
    name = str(data.get("name", "کاربر")).strip()[:24] or "کاربر"
    users[request_id()] = name
    emit("notice", {"text": f"{name} وارد Matrix شد."}, broadcast=True)

def request_id():
    from flask import request
    return request.sid

@socketio.on("chat_message")
def on_message(data):
    from flask import request
    name = users.get(request.sid, "کاربر")
    message = str(data.get("text", "")).strip()[:1000]
    if not message:
        return
    emit("chat_message", {
        "name": name,
        "text": message,
        "time": datetime.now().strftime("%H:%M")
    }, broadcast=True)

@socketio.on("disconnect")
def on_disconnect():
    from flask import request
    name = users.pop(request.sid, None)
    if name:
        emit("notice", {"text": f"{name} از Matrix خارج شد."}, broadcast=True)

if __name__ == "__main__":
    print("Matrix is running at http://127.0.0.1:5001")
    socketio.run(app, host="0.0.0.0", port=5001, debug=False)
