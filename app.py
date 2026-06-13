import os
import sys
import subprocess

# --- آلية التثبيت الذاتي المحدثة لتتوافق مع Python 3.14 ---
def install_requirements_dynamically():
    # أزلنا تحديد رقم الإصدار لـ pyinstaller و static-ffmpeg ليتثبت أحدث إصدار متوافق تلقائياً
    required_packages = ["Flask==3.0.2", "pyinstaller", "static-ffmpeg"]
    for package in required_packages:
        pkg_name = package.split("==")[0]
        try:
            __import__(pkg_name.replace("-", "_"))
        except ImportError:
            print(f"[Tool Alpha Core] {pkg_name} not found. Installing dynamically...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# تشغيل التثبيت التلقائي قبل استدعاء الـ Flask
install_requirements_dynamically()

# الآن نقوم باستدعاء المكتبات بأمان تام بعد التأكد من تثبيتها
import shutil
import asyncio
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory

# تفعيل الـ FFmpeg المدمج تلقائياً
import static_ffmpeg
static_ffmpeg.add_paths()
import PyInstaller.__main__

app = Flask(__name__)

UPLOAD_FOLDER = os.path.abspath("./uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def auto_delete_file(folder_path):
    def delay_delete():
        import time
        time.sleep(1800)  # حذف تلقائي بعد 30 دقيقة
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"[Security] Task folder {folder_path} has been self-destructed.")
            
    threading.Thread(target=delay_delete, daemon=True).start()

async def run_pyinstaller(args):
    def run():
        PyInstaller.__main__.run(args)
    await asyncio.to_thread(run)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-page/<task_id>/<filename>')
def download_page(task_id, filename):
    return render_template('download.html', task_id=task_id, filename=filename)

@app.route('/download-file/<task_id>/<filename>')
def download_file(task_id, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], task_id, "dist"), filename)

@app.route('/convert', methods=['POST'])
async def convert_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    target_format = request.form.get('format', '').lower().strip()
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    task_id = f"task_{os.urandom(4).hex()}"
    task_dir = os.path.join(app.config['UPLOAD_FOLDER'], task_id)
    input_dir = os.path.join(task_dir, "input")
    output_dir = os.path.join(task_dir, "dist")
    
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    input_path = os.path.join(input_dir, file.filename)
    file.save(input_path)
    
    base_name = os.path.splitext(file.filename)[0]
    output_filename = f"{base_name}.{target_format}"
    output_path = os.path.join(output_dir, output_filename)
    
    try:
        if target_format == "exe" and file.filename.endswith('.py'):
            work_path = os.path.join(task_dir, "build")
            args = [
                '--onefile', '--noconsole', '--clean',
                '--workpath', work_path, '--distpath', output_dir,
                input_path
            ]
            await run_pyinstaller(args)
        else:
            if input_path.lower().endswith(('.mp3', '.wav', '.ogg')) and target_format == 'mp4':
                cmd = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1", 
                    "-i", input_path, "-c:v", "libx264", "-tune", "stillimage", 
                    "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", output_path
                ]
            else:
                cmd = ["ffmpeg", "-y", "-i", input_path, output_path]
                
            process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            await process.communicate()

        if os.path.exists(output_path):
            auto_delete_file(task_dir)
            return jsonify({"success": True, "redirect": f"/download-page/{task_id}/{output_filename}"})
        else:
            raise Exception("Conversion engine failed to produce the output file.")
            
    except Exception as e:
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # تهيئة السيرفر للعمل السحابي
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
