
from flask import Flask, request, render_template_string
import hashlib
import mimetypes

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

PAGE = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DRINKO Scanner</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;background:#08080c;color:white;
 font-family:Arial,sans-serif;overflow-x:hidden
}
canvas{
 position:fixed;inset:0;width:100%;height:100%;
 z-index:-1;opacity:.65
}
header{
 text-align:center;padding:24px 10px;
 border-bottom:1px solid #481018;
 background:#10090de0
}
.logo{
 color:#ff263b;font-size:38px;font-weight:900;
 letter-spacing:7px;text-shadow:0 0 20px red
}
.subtitle{color:#b98c93;font-size:12px}
main{max-width:550px;margin:25px auto;padding:15px}
.panel{
 background:#120d13eF;border:1px solid #69202b;
 border-radius:18px;padding:22px;margin-bottom:20px;
 box-shadow:0 0 25px #ff002215
}
h2{color:#ff3549;text-align:center}
.cube-area{
 height:175px;display:flex;align-items:center;
 justify-content:center;perspective:500px
}
.cube{
 width:85px;height:85px;position:relative;
 transform-style:preserve-3d;
 animation:rotate 9s linear infinite
}
.face{
 position:absolute;width:85px;height:85px;
 border:2px solid #ff3549;
 background:#ff172010;
 box-shadow:inset 0 0 20px #ff263b55,0 0 15px #ff263b55
}
.front{transform:translateZ(42px)}
.back{transform:rotateY(180deg) translateZ(42px)}
.right{transform:rotateY(90deg) translateZ(42px)}
.left{transform:rotateY(-90deg) translateZ(42px)}
.top{transform:rotateX(90deg) translateZ(42px)}
.bottom{transform:rotateX(-90deg) translateZ(42px)}
@keyframes rotate{
 from{transform:rotateX(0) rotateY(0)}
 to{transform:rotateX(360deg) rotateY(360deg)}
}
.status{
 text-align:center;color:#ff5365;
 font-size:12px;letter-spacing:2px
}
.upload{
 border:1px dashed #ff3549;border-radius:14px;
 padding:25px 12px;text-align:center;
 background:#250b1230
}
input[type=file]{max-width:100%;color:#ddd;margin:15px 0}
button{
 background:#a90e25;color:white;border:1px solid #ff5263;
 border-radius:10px;padding:13px 25px;
 font-size:16px;font-weight:bold;cursor:pointer;
 box-shadow:0 0 15px #ff263b44
}
button:active{transform:scale(.96)}
.result{
 background:#1b1017;border-radius:12px;
 padding:15px;overflow-wrap:anywhere;
 line-height:1.8
}
.red{color:#ff6574}
footer{text-align:center;color:#76545b;font-size:11px;padding:20px}
</style>
</head>
<body>
<canvas id="matrix"></canvas>

<header>
 <div class="logo">DRINKO</div>
 <div class="subtitle">ADVANCED FILE SECURITY SCANNER</div>
</header>

<main>
 <section class="panel">
  <div class="cube-area">
   <div class="cube">
    <div class="face front"></div>
    <div class="face back"></div>
    <div class="face right"></div>
    <div class="face left"></div>
    <div class="face top"></div>
    <div class="face bottom"></div>
   </div>
  </div>
  <h2>مركز الحماية DRINKO</h2>
  <div class="status">● SYSTEM READY</div>
 </section>

 <section class="panel">
  <h2>فحص الملفات</h2>
  <form method="POST" enctype="multipart/form-data">
   <div class="upload">
    <div style="font-size:35px">⬆</div>
    <p>اختر ملفاً من هاتفك</p>
    <input type="file" name="file" required>
    <br>
    <button type="submit">بدء الفحص</button>
   </div>
  </form>
 </section>

 {% if result %}
 <section class="panel">
  <h2>نتيجة الفحص</h2>
  <div class="result">
   <div>الملف: <span class="red">{{result.name}}</span></div>
   <div>الحجم: {{result.size}} MB</div>
   <div>النوع المتوقع: {{result.kind}}</div>
   <div>SHA256:</div>
   <div class="red">{{result.sha}}</div>
   <div>الحالة: تم حساب البصمة بنجاح</div>
   <p>هذه المعلومات لا تثبت أن الملف آمن أو خبيث.</p>
  </div>
 </section>
 {% endif %}
</main>

<footer>DRINKO SECURITY LAB • LOCAL SCANNING</footer>

<script>
const canvas=document.getElementById("matrix");
const ctx=canvas.getContext("2d");
let drops=[];
function resize(){
 canvas.width=innerWidth;
 canvas.height=innerHeight;
 drops=Array(Math.ceil(canvas.width/17)).fill(1);
}
resize();
addEventListener("resize",resize);
function draw(){
 ctx.fillStyle="rgba(8,8,12,0.09)";
 ctx.fillRect(0,0,canvas.width,canvas.height);
 ctx.fillStyle="#ff263b";
 ctx.font="14px monospace";
 drops.forEach((y,i)=>{
  ctx.fillText(
   Math.random()>.5?"1":"0",i*17,y*17
  );
  if(y*17>canvas.height&&Math.random()>.975)drops[i]=0;
  drops[i]++;
 });
}
setInterval(draw,55);
</script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        uploaded = request.files.get("file")

        if uploaded and uploaded.filename:
            sha = hashlib.sha256()
            size = 0

            while True:
                chunk = uploaded.stream.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                sha.update(chunk)

            kind = mimetypes.guess_type(uploaded.filename)[0]
            result = {
                "name": uploaded.filename,
                "size": round(size / 1024 / 1024, 2),
                "kind": kind or "غير معروف",
                "sha": sha.hexdigest()
            }

    return render_template_string(PAGE, result=result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

