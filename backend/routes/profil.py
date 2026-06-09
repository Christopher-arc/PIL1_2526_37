from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import mysql
import os

profil_bp = Blueprint('profil', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'statics', 'photos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'id' not in session:
            flash("Connectez-vous d'abord.", 'danger')
            return redirect(url_for('auth.connexion'))
        return f(*args, **kwargs)
    return decorated


@profil_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    cur = mysql.connection.cursor()

    if request.method == 'GET':
        cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (session['id'],))
        utilisateur = cur.fetchone()

        cur.execute("SELECT * FROM `Matieres`")
        matieres = cur.fetchall()

        cur.execute("SELECT id_matiere FROM MAITRISE WHERE id_utilisateur = %s", (session['id'],))
        points_forts = [r['id_matiere'] for r in cur.fetchall()]

        cur.execute("SELECT id_matiere FROM BESOIN WHERE id_utilisateur = %s", (session['id'],))
        points_faibles = [r['id_matiere'] for r in cur.fetchall()]

        cur.execute("SELECT * FROM `Disponibilites`")
        dispos = cur.fetchall()

        cur.execute("SELECT id_dispo FROM USER_DISPONIBILITE WHERE id_utilisateur = %s", (session['id'],))
        mes_dispos = [r['id_dispo'] for r in cur.fetchall()]

        cur.close()
        return render_template('profil.html',
                               utilisateur=utilisateur,
                               matieres=matieres,
                               points_forts=points_forts,
                               points_faibles=points_faibles,
                               dispos=dispos,
                               mes_dispos=mes_dispos)

    # ── POST — mise à jour infos de base ─────────────────────
    nom       = request.form.get('nom', '').strip()
    prenom    = request.form.get('prenom', '').strip()
    telephone = request.form.get('telephone', '').strip()
    filiere   = request.form.get('filiere', '').strip()
    niveau    = request.form.get('niveau', '').strip()
    bio       = request.form.get('bio', '').strip()

    if not all([nom, prenom, telephone, filiere, niveau]):
        flash('Tous les champs obligatoires doivent être remplis.', 'danger')
        return redirect(url_for('profil.profil'))

    # Photo de profil
    photo_nom = None
    photo = request.files.get('photo')
    if photo and photo.filename and allowed_file(photo.filename):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        photo_nom = secure_filename(f"{session['id']}_{photo.filename}")
        photo.save(os.path.join(UPLOAD_FOLDER, photo_nom))

    if photo_nom:
        cur.execute(
            "UPDATE Utilisateurs SET nom=%s, prenom=%s, telephone=%s, filiere=%s, niveau=%s, Bio=%s, photo=%s WHERE id_utilisateur=%s",
            (nom, prenom, telephone, filiere, niveau, Bio, photo_nom, session['id'])
        )
    else:
        cur.execute(
            "UPDATE Utilisateurs SET nom=%s, prenom=%s, telephone=%s, filiere=%s, niveau=%s, Bio=%s WHERE id_utilisateur=%s",
            (nom, prenom, telephone, filiere, niveau, bio, session['id'])
        )

    # Points forts
    cur.execute("DELETE FROM MAITRISE WHERE id_utilisateur = %s", (session['id'],))
    for id_matiere in request.form.getlist('points_forts'):
        cur.execute("INSERT INTO MAITRISE (id_utilisateur, id_matiere) VALUES (%s, %s)", (session['id'], id_matiere))

    # Points faibles
    cur.execute("DELETE FROM BESOIN WHERE id_utilisateur = %s", (session['id'],))
    for id_matiere in request.form.getlist('points_faibles'):
        cur.execute("INSERT INTO BESOIN (id_utilisateur, id_matiere) VALUES (%s, %s)", (session['id'], id_matiere))

    # Disponibilités
    cur.execute("DELETE FROM USER_DISPONIBILITE WHERE id_utilisateur = %s", (session['id'],))
    for id_dispo in request.form.getlist('disponibilites'):
        cur.execute("INSERT INTO USER_DISPONIBILITE (id_utilisateur, id_dispo) VALUES (%s, %s)", (session['id'], id_dispo))

    mysql.connection.commit()
    cur.close()

    session['nom']    = nom
    session['prenom'] = prenom

    flash('Profil mis à jour.', 'success')
    return redirect(url_for('profil.profil'))


# ── Modifier email ────────────────────────────────────────────
@profil_bp.route('/profil/modifier-email', methods=['POST'])
@login_required
def modifier_email():
    nouvel_email = request.form.get('email', '').strip().lower()
    mdp          = request.form.get('mot_de_passe', '')

    if not nouvel_email or not mdp:
        flash('Email et mot de passe requis.', 'danger')
        return redirect(url_for('profil.profil'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT mot_de_passe FROM Utilisateurs WHERE id_utilisateur = %s", (session['id'],))
    utilisateur = cur.fetchone()

    if not check_password_hash(utilisateur['mot_de_passe'], mdp):
        cur.close()
        flash('Mot de passe incorrect.', 'danger')
        return redirect(url_for('profil.profil'))

    cur.execute("SELECT id_utilisateur FROM Utilisateurs WHERE email = %s AND id_utilisateur != %s",
                (nouvel_email, session['id']))
    if cur.fetchone():
        cur.close()
        flash('Cet email est déjà utilisé.', 'danger')
        return redirect(url_for('profil.profil'))

    cur.execute("UPDATE Utilisateurs SET email=%s WHERE id_utilisateur=%s", (nouvel_email, session['id']))
    mysql.connection.commit()
    cur.close()

    flash('Email mis à jour.', 'success')
    return redirect(url_for('profil.profil'))


# ── Modifier mot de passe ─────────────────────────────────────
@profil_bp.route('/profil/modifier-mdp', methods=['POST'])
@login_required
def modifier_mdp():
    ancien_mdp  = request.form.get('ancien_mdp', '')
    nouveau_mdp = request.form.get('nouveau_mdp', '')
    confirm_mdp = request.form.get('confirm_mdp', '')

    if not all([ancien_mdp, nouveau_mdp, confirm_mdp]):
        flash('Tous les champs sont requis.', 'danger')
        return redirect(url_for('profil.profil'))

    if nouveau_mdp != confirm_mdp:
        flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
        return redirect(url_for('profil.profil'))

    if len(nouveau_mdp) < 6:
        flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
        return redirect(url_for('profil.profil'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT mot_de_passe FROM Utilisateurs WHERE id_utilisateur = %s", (session['id'],))
    utilisateur = cur.fetchone()

    if not check_password_hash(utilisateur['mot_de_passe'], ancien_mdp):
        cur.close()
        flash('Ancien mot de passe incorrect.', 'danger')
        return redirect(url_for('profil.profil'))

    cur.execute("UPDATE Utilisateurs SET mot_de_passe=%s WHERE id_utilisateur=%s",
                (generate_password_hash(nouveau_mdp), session['id']))
    mysql.connection.commit()
    cur.close()

    flash('Mot de passe mis à jour.', 'success')
    return redirect(url_for('profil.profil'))


# ── Mes annonces ──────────────────────────────────────────────
@profil_bp.route('/mes-annonces', methods=['GET'])
@login_required
def mes_annonces():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.*,
               GROUP_CONCAT(DISTINCT m.nom_matiere SEPARATOR ', ') AS matieres_annonce,
               GROUP_CONCAT(DISTINCT CONCAT(d.jour, ' ', d.heure_debut, '-', d.heure_fin) SEPARATOR ' | ') AS dispos_annonce
        FROM Annonces a
        LEFT JOIN ANNONCE_MATIERE am ON a.id_annonce = am.id_annonce
        LEFT JOIN `Matieres` m ON am.id_matiere = m.id_matiere
        LEFT JOIN ANNONCE_DISPONIBILITE ad ON a.id_annonce = ad.id_annonce
        LEFT JOIN `Disponibilites` d ON ad.id_dispo = d.id_dispo
        WHERE a.id_utilisateur = %s
        GROUP BY a.id_annonce
        ORDER BY a.date_creation DESC
    """, (session['id'],))
    annonces = cur.fetchall()

    cur.execute("SELECT * FROM `Matieres`")
    matieres = cur.fetchall()

    cur.execute("SELECT * FROM `Disponibilites`")
    dispos = cur.fetchall()

    cur.close()
    return render_template('mes_annonces.html', annonces=annonces, matieres=matieres, dispos=dispos)


# ── Supprimer annonce ─────────────────────────────────────────
@profil_bp.route('/annonces/supprimer/<int:id_annonce>', methods=['POST'])
@login_required
def supprimer_annonce(id_annonce):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_utilisateur FROM Annonces WHERE id_annonce = %s", (id_annonce,))
    annonce = cur.fetchone()

    if not annonce or annonce['id_utilisateur'] != session['id']:
        cur.close()
        flash('Action non autorisée.', 'danger')
        return redirect(url_for('profil.mes_annonces'))

    cur.execute("DELETE FROM ANNONCE_MATIERE WHERE id_annonce = %s", (id_annonce,))
    cur.execute("DELETE FROM ANNONCE_DISPONIBILITE WHERE id_annonce = %s", (id_annonce,))
    cur.execute("DELETE FROM Annonces WHERE id_annonce = %s", (id_annonce,))
    mysql.connection.commit()
    cur.close()

    flash('Annonce supprimée.', 'success')
    return redirect(url_for('profil.mes_annonces'))


# ── Modifier annonce ──────────────────────────────────────────
@profil_bp.route('/annonces/modifier/<int:id_annonce>', methods=['POST'])
@login_required
def modifier_annonce(id_annonce):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_utilisateur FROM Annonces WHERE id_annonce = %s", (id_annonce,))
    annonce = cur.fetchone()

    if not annonce or annonce['id_utilisateur'] != session['id']:
        cur.close()
        flash('Action non autorisée.', 'danger')
        return redirect(url_for('profil.mes_annonces'))

    type_annonce   = request.form.get('type_annonce', '')
    format_session = request.form.get('format_session', '')
    description    = request.form.get('description_perso', '').strip()
    statut         = request.form.get('statut', 'actif')
    id_matieres    = request.form.getlist('matieres')
    id_dispos      = request.form.getlist('disponibilites')

    cur.execute("""
        UPDATE Annonces SET type_annonce=%s, format_session=%s, description_perso=%s, statut=%s
        WHERE id_annonce=%s
    """, (type_annonce, format_session, description, statut, id_annonce))

    cur.execute("DELETE FROM ANNONCE_MATIERE WHERE id_annonce = %s", (id_annonce,))
    for id_matiere in id_matieres:
        cur.execute("INSERT INTO ANNONCE_MATIERE (id_annonce, id_matiere) VALUES (%s, %s)", (id_annonce, id_matiere))

    cur.execute("DELETE FROM ANNONCE_DISPONIBILITE WHERE id_annonce = %s", (id_annonce,))
    for id_dispo in id_dispos:
        cur.execute("INSERT INTO ANNONCE_DISPONIBILITE (id_annonce, id_dispo) VALUES (%s, %s)", (id_annonce, id_dispo))

    mysql.connection.commit()
    cur.close()

    flash('Annonce modifiée.', 'success')
    return redirect(url_for('profil.mes_annonces'))