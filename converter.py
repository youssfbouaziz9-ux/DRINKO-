
from flask import Flask, request, render_template_string, send_file
from PIL import Image, ImageOps
from pathlib import Path
import subprocess
import tempfile
import shutil
import zipfile
import uuid
import os

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

OUT = Path.home() / "DRINKO" / "converted"
OUT.mkdir(parents=True, exist_ok=True)

HTML = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DRINKO CONVERTER</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;background:#08080c;color:white;
 font-family:Arial,sans-serif;min-height:100vh
}
canvas{position:fixed;inset:0;width:100%;height:100%;
 z-index:-1;opacity:.5}
header{text-align:center;padding:25px;
 background:#10090de8;border-bottom:1px solid #76202b}
.logo{font-size:38px;font-weight:900;color:#ff263b;
 letter-spacing:7px;text-shadow:0 0 20px red}
main{max-width:520px;margin:25px auto;padding:15px}
.panel{background:#150e14;border:1px solid #69202b;
 border-radius:18px;padding:22px;margin-bottom:18px;
 box-shadow:0 0 20px #ff002222}
h2{text-align:center;color:#ff4053}
.cube-area{height:110px;display:grid;place-items:center;
 perspective:400px}
.cube{width:55px;height:55px;position:relative;
 transform-style:preserve-3d;animation:spin 7s linear infinite}
.face{position:absolute;width:55px;height:55px;
 border:2px solid #ff3048;background:#ff172020;
 box-shadow:0 0 15px #ff263b55}
.f1{transform:translateZ(27px)}
.f2{transform:rotateY(180deg) translateZ(27px)}
.f3{transform:rotateY(90deg) translateZ(27px)}
.f4{transform:rotateY(-90deg) translateZ(27px)}
.f5{transform:rotateX(90deg) translateZ(27px)}
.f6{transform:rotateX(-90deg) translateZ(27px)}
@keyframes spin{to{transform:rotateX(360deg) rotateY(360deg)}}
button{width:100%;padding:14px;background:#a80e27;
 color:white;border:1px solid #ff5366;border-radius:10px;
 font-size:16px;font-weight:bold;margin-top:12px}
input{width:100%;margin:15px 0;color:white}
.note{color:#bba1a7;font-size:12px;line-height:1.8}
.result{background:#241018;padding:15px;border-radius:12px;
 color:#ff8791;overflow-wrap:anywhere}
footer{text-align:center;color:#80535c;font-size:11px;padding:20px}
</style>
</head>
<body>
<canvas id="matrix"></canvas>
<header>
 <div class="logo">DRINKO</div>
 <div style="color:#c18a91;font-size:12px">
 ADVANCED FILE CONVERTER
 </div>
</header>
<main>
 <section class="panel">
  <div class="cube-area">
   <div class="cube">
    <div class="face f1"></div><div class="face f2"></div>
    <div class="face f3"></div><div class="face f4"></div>
    <div class="face f5"></div><div class="face f6"></div>
   </div>
  </div>
  <h2>IMAGE → PDF</h2>
  <form action="/images-to-pdf" method="POST"
        enctype="multipart/form-data">
   <p>اختر صورة واحدة أو عدة صور:</p>
   <input type="file" name="images" accept="image/*"
          multiple required>
   <button>تحويل الصور إلى PDF</button>
  </form>
  <p class="note">يمكن دمج عدة صور في ملف PDF واحد.</p>
 </section>

 <section class="panel">
  <h2>PDF → IMAGE</h2>
  <form action="/pdf-to-images" method="POST"
        enctype="multipart/form-data">
   <p>اختر ملف PDF:</p>
   <input type="file" name="pdf" accept=".pdf,application/pdf"
          required>
   <button>تحويل PDF إلى صور PNG</button>
  </form>
  <p class="note">تُحوّل أول 50 صفحة إلى صور وتُجمع في ZIP.</p>
 </section>

 {% if message %}
 <section class="panel">
  <h2>النتيجة</h2>
  <div class="result">{{message}}</div>
  {% if download %}
  <a href="{{download}}" style="text-decoration:none">
   <button>تحميل الملف الناتج</button>
  </a>
  {% endif %}
 </section>
 {% endif %}
</main>
<footer>DRINKO • LOCAL CONVERSION • 2026</footer>
<script>
const c=document.getElementById("matrix");
const x=c.getContext("2d");
let drops=[];
function resize(){
 c.width=innerWidth;c.height=innerHeight;
 drops=Array(Math.ceil(c.width/17)).fill(1);
}
resize();addEventListener("resize",resize);
function draw(){
 x.fillStyle="rgba(8,8,12,.12)";
 x.fillRect(0,0,c.width,c.height);
 x.fillStyle="#ff263b";x.font="14px monospace";
 drops.forEach((y,i)=>{
  x.fillText(Math.random()>.5?"1":"0",i*17,y*17);
  if(y*17>c.height&&Math.random()>.975)drops[i]=0;
  drops[i]++;
 });
}
setInterval(draw,60);
</script>
</body>
</html>
"""


def page(message=None, download=None):
    from flask import render_template_string
    return render_template_string(
        HTML, message=message, download=download
    )


@app.route("/")
def home():
    return page()


@app.route("/images-to-pdf", methods=["POST"])
def images_to_pdf():
    files = request.files.getlist("images")
    files = [f for f in files if f.filename]

    if not files:
        return page("لم تختر أي صورة.")

    if len(files) > 30:
        return page("الحد الأقصى 30 صورة.")

    images = []

    try:
        for uploaded in files:
            img = Image.open(uploaded.stream)
            img = ImageOps.exif_transpose(img)
            img.load()

            if img.mode in ("RGBA", "LA"):
                rgba = img.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                img = background
            else:
                img = img.convert("RGB")

            images.append(img)

        output = OUT / f"DRINKO_{uuid.uuid4().hex[:10]}.pdf"

        images[0].save(
            output,
            "PDF",
            save_all=True,
            append_images=images[1:],
            resolution=120
        )

        for img in images:
            img.close()

        return send_file(
            output,
            as_attachment=True,
            download_name="DRINKO_CONVERTED.pdf"
        )

    except Exception as e:
        for img in images:
            img.close()
        return page("تعذر تحويل الصور: " + str(e))


@app.route("/pdf-to-images", methods=["POST"])
def pdf_to_images():
    uploaded = request.files.get("pdf")

    if not uploaded or not uploaded.filename:
        return page("لم تختر ملف PDF.")

    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        source = temp / "input.pdf"

        uploaded.save(source)

        if source.read_bytes()[:5] != b"%PDF-":
            return page("الملف ليس PDF صالحاً.")

        prefix = temp / "page"

        try:
            subprocess.run(
                [
                    "pdftoppm", "-f", "1", "-l", "50",
                    "-r", "120", "-png",
                    str(source), str(prefix)
                ],
                check=True,
                capture_output=True,
                timeout=180
            )

            pages = sorted(temp.glob("page-*.png"))

            if not pages:
                return page("لم يتم العثور على صفحات قابلة للتحويل.")

            output = OUT / f"DRINKO_{uuid.uuid4().hex[:10]}.zip"

            with zipfile.ZipFile(
                output, "w", zipfile.ZIP_DEFLATED
            ) as archive:
                for image in pages:
                    archive.write(image, image.name)

            return send_file(
                output,
                as_attachment=True,
                download_name="DRINKO_IMAGES.zip"
            )

        except subprocess.TimeoutExpired:
            return page("انتهى وقت التحويل. جرّب ملف PDF أصغر.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            return page("فشل التحويل. تأكد من تثبيت Poppler وصحة PDF.")
        except Exception as e:
            return page("حدث خطأ: " + str(e))


@app.errorhandler(413)
def too_large(error):
    return page("حجم الملف أكبر من الحد المسموح: 100 MB."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

