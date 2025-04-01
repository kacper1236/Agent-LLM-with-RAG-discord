import os
from datetime import datetime

from werkzeug.utils import secure_filename

TEMP_FOLDER = os.getenv('TEMP_FOLDER', './_temp')
FILES_FOLDER = os.getenv('TEMP_FOLDER', './_files')


def saveFile(file, data: list[str]):
    # Save the uploaded file with a secure filename and return the file path
    print("Loading file ... " + os.path.join(TEMP_FOLDER) + "/__" + "__".join(data) + "__" + secure_filename(file.filename))
    ct = datetime.now()
    ts = ct.timestamp()
    filename = str(ts) + "__" + "__".join(data) + "__" + secure_filename(file.filename)
    file_path = os.path.join(TEMP_FOLDER, filename)
    file.save(file_path)

    return file_path