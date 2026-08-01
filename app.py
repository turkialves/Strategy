from __future__ import annotations

import shutil
import socket
import sys
import tempfile
import threading
import traceback
import uuid
import webbrowser
import zipfile
from pathlib import Path

from flask import (
    Flask,
    after_this_request,
    render_template,
    request,
    send_file,
)

from processor import process_folder
from report import create_report
from hqi_processor import process_hqi_folder
from hqi_report import create_hqi_report
from adaa_processor import process_adaa_weekly
from adaa_report import create_adaa_report

def get_resource_path(relative_path: str) -> Path:
    """
    يعيد المسار الصحيح للملفات سواء كان البرنامج يعمل:
    - من ملفات Python مباشرة.
    - أو من تطبيق تم إنشاؤه باستخدام PyInstaller.
    """
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path


TEMPLATE_FOLDER = get_resource_path("templates")
STATIC_FOLDER = get_resource_path("static")


app = Flask(
    __name__,
    template_folder=str(TEMPLATE_FOLDER),
    static_folder=str(STATIC_FOLDER),
)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024

ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}


def is_excel_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def find_available_port(
    host: str = "127.0.0.1",
    preferred_port: int = 5001,
) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, preferred_port))
            return preferred_port
        except OSError:
            sock.bind((host, 0))
            return int(sock.getsockname()[1])


def open_browser(url: str) -> None:
    webbrowser.open_new(url)


def save_uploaded_files(uploaded_files, source_folder: Path) -> None:
    for index, uploaded_file in enumerate(uploaded_files, start=1):
        relative_name = uploaded_file.filename.replace("\\", "/")

        parts = [
            part
            for part in relative_name.split("/")
            if part not in {"", ".", ".."}
        ]

        if not parts:
            extension = Path(uploaded_file.filename).suffix
            parts = [f"source_{index}{extension}"]

        target_path = source_folder.joinpath(*parts)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists():
            new_name = (
                f"{target_path.stem}_"
                f"{uuid.uuid4().hex[:6]}"
                f"{target_path.suffix}"
            )
            target_path = target_path.with_name(new_name)

        uploaded_file.save(target_path)


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@app.route("/clinic-audit", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/hqi", methods=["GET"])
def hqi_page():
    return render_template("hqi.html")
@app.route("/adaa", methods=["GET"])
def adaa_page():
    return render_template("adaa.html")
@app.route("/adaa-weekly", methods=["GET"])
def adaa_weekly_page():
    return render_template("adaa_weekly.html")
@app.route("/process", methods=["POST"])
def process_files():
    month = request.form.get("month")
    master_file = request.files.get("master")
    source_files = request.files.getlist("files")

    if not master_file or not master_file.filename:
        return render_template("index.html", error="اختر ملف الماستر."), 400

    if not is_excel_file(master_file.filename):
        return render_template(
            "index.html",
            error="ملف الماستر يجب أن يكون XLSX أو XLSM.",
        ), 400

    source_files = [
        file
        for file in source_files
        if file
        and file.filename
        and is_excel_file(file.filename)
        and not Path(file.filename).name.startswith("~$")
    ]

    if not source_files:
        return render_template(
            "index.html",
            error="اختر مجلد ملفات المؤشرات.",
        ), 400

    work_folder = Path(tempfile.mkdtemp(prefix="quality_importer_"))
    source_folder = work_folder / "sources"
    source_folder.mkdir(parents=True, exist_ok=True)

    try:
        master_name = Path(master_file.filename).name
        master_path = work_folder / master_name
        master_file.save(master_path)

        save_uploaded_files(source_files, source_folder)

        result = process_folder(
            str(source_folder),
            str(master_path),
            selected_month=month,
        )

        output_path = Path(result["output_path"])
        report_path = output_path.with_name(
            f"{output_path.stem} - Dashboard.html"
        )

        create_report(result, report_path)

        zip_path = work_folder / f"{output_path.stem}.zip"

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zip_file:
            zip_file.write(output_path, arcname=output_path.name)
            zip_file.write(report_path, arcname=report_path.name)

        @after_this_request
        def remove_temp_files(response):
            shutil.rmtree(work_folder, ignore_errors=True)
            return response

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_path.name,
            mimetype="application/zip",
        )

    except Exception as error:
        error_details = traceback.format_exc()
        shutil.rmtree(work_folder, ignore_errors=True)

        return render_template(
            "index.html",
            error=str(error),
            details=error_details,
        ), 500


@app.route("/process-hqi", methods=["POST"])
def process_hqi_files():
    month = request.form.get("month")
    master_file = request.files.get("master")
    source_files = request.files.getlist("files")

    if not month:
        return render_template("hqi.html", error="اختر الشهر."), 400

    if not master_file or not master_file.filename:
        return render_template("hqi.html", error="اختر ملف الماستر."), 400

    if not is_excel_file(master_file.filename):
        return render_template(
            "hqi.html",
            error="ملف الماستر يجب أن يكون XLSX أو XLSM.",
        ), 400

    source_files = [
        file
        for file in source_files
        if file
        and file.filename
        and is_excel_file(file.filename)
        and not Path(file.filename).name.startswith("~$")
    ]

    if not source_files:
        return render_template(
            "hqi.html",
            error="اختر مجلد ملفات HQI.",
        ), 400

    work_folder = Path(tempfile.mkdtemp(prefix="hqi_importer_"))
    source_folder = work_folder / "sources"
    source_folder.mkdir(parents=True, exist_ok=True)

    try:
        master_name = Path(master_file.filename).name
        master_path = work_folder / master_name
        master_file.save(master_path)

        save_uploaded_files(source_files, source_folder)

        result = process_hqi_folder(
            folder=str(source_folder),
            master_file=str(master_path),
            selected_month=month,
        )

        output_path = Path(result["output_path"])

        report_path = output_path.with_name(
            f"{output_path.stem} - HQI Report.html"
        )

        create_hqi_report(
            result,
            report_path,
        )

        zip_path = work_folder / f"{output_path.stem}.zip"

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zip_file:
            zip_file.write(output_path, arcname=output_path.name)
            zip_file.write(report_path, arcname=report_path.name)

        @after_this_request
        def remove_hqi_temp_files(response):
            shutil.rmtree(work_folder, ignore_errors=True)
            return response

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_path.name,
            mimetype="application/zip",
        )

    except Exception as error:
        error_details = traceback.format_exc()
        shutil.rmtree(work_folder, ignore_errors=True)

        return render_template(
            "hqi.html",
            error=str(error),
            details=error_details,
        ), 500


@app.route("/process-adaa-weekly", methods=["POST"])
def process_adaa_weekly_files():
    master_file = request.files.get("master_file")
    source_files = request.files.getlist("source_files")

    if not master_file or not master_file.filename:
        return render_template(
            "adaa_weekly.html",
            error="اختر ملف الماستر.",
        ), 400

    if not is_excel_file(master_file.filename):
        return render_template(
            "adaa_weekly.html",
            error="ملف الماستر يجب أن يكون XLSX أو XLSM.",
        ), 400

    source_files = [
        file
        for file in source_files
        if file
        and file.filename
        and is_excel_file(file.filename)
        and not Path(file.filename).name.startswith("~$")
    ]

    if not source_files:
        return render_template(
            "adaa_weekly.html",
            error="اختر ملفات مؤشرات ADAA الأسبوعية.",
        ), 400

    work_folder = Path(tempfile.mkdtemp(prefix="adaa_"))
    source_folder = work_folder / "sources"
    source_folder.mkdir(parents=True, exist_ok=True)

    try:
        master_name = Path(master_file.filename).name
        master_path = work_folder / master_name
        master_file.save(master_path)

        save_uploaded_files(source_files, source_folder)

        output_path = work_folder / f"Processed_{master_name}"

        result = process_adaa_weekly(
            master_file=master_path,
            hospital_files=[
                file_path
                for file_path in source_folder.rglob("*")
                if file_path.is_file()
            ],
            output_file=output_path,
        )

        report_path = output_path.with_name(
            f"{output_path.stem} - ADAA Report.html"
        )
        create_adaa_report(result, report_path)

        zip_path = work_folder / f"{output_path.stem}.zip"

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zip_file:
            zip_file.write(output_path, arcname=output_path.name)
            zip_file.write(report_path, arcname=report_path.name)

        @after_this_request
        def remove_adaa_temp_files(response):
            shutil.rmtree(work_folder, ignore_errors=True)
            return response

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_path.name,
            mimetype="application/zip",
        )

    except Exception as error:
        error_details = traceback.format_exc()
        shutil.rmtree(work_folder, ignore_errors=True)

        return render_template(
            "adaa_weekly.html",
            error=str(error),
            details=error_details,
        ), 500


if __name__ == "__main__":
    server_host = "127.0.0.1"
    server_port = find_available_port(
        host=server_host,
        preferred_port=5001,
    )

    server_url = f"http://{server_host}:{server_port}"

    threading.Timer(
        1.5,
        open_browser,
        args=(server_url,),
    ).start()

    app.run(
        host=server_host,
        port=server_port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )
