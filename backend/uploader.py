import os
import uuid

from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png"
}


def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def save_profile_picture(file, upload_folder):

    if not allowed_file(file.filename):
        raise ValueError("Extension non autorisée.")

    extension = file.filename.rsplit(".", 1)[1].lower()

    filename = secure_filename(
        f"{uuid.uuid4().hex}.{extension}"
    )

    filepath = os.path.join(upload_folder, filename)

    file.save(filepath)

    return filename