import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png"
}

def allowed_file(filename):
    """Vérifier si extension fichier est autorisée"""
    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )

def save_profile_picture(file, upload_folder):
    """Sauvegarder une photo de profil avec UUID unique
    
    Args:
        file: FileStorage object de Flask
        upload_folder: Chemin du dossier upload
        
    Returns:
        str: Nom du fichier sauvegardé
        
    Raises:
        ValueError: Si extension non autorisée
    """
    # NOUVEAU: Vérifier que le dossier existe
    os.makedirs(upload_folder, exist_ok=True)
    
    if not allowed_file(file.filename):
        raise ValueError("Extension non autorisée. Utilisez jpg, jpeg ou png.")

    extension = file.filename.rsplit(".", 1)[1].lower()
    
    # UUID unique pour éviter les collisions
    filename = secure_filename(
        f"{uuid.uuid4().hex}.{extension}"
    )

    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return filename