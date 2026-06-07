from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import mysql

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Matières")
        matieres = cur.fetchall()
        cur.close()
        return render_template('inscription.html', matieres=matieres)

    nom       = request.form.get('nom', '').strip()
    prenom    = request.form.get('prenom', '').strip()
    telephone = request.form.get('telephone', '').strip()
    email     = request.form.get('email', '').strip().lower()
    mdp       = request.form.get('mot_de_passe', '')
    mdp_conf  = request.form.get('mot_de_passe_confirm', '')
    filiere   = request.form.get('filiere', '').strip()
    niveau    = request.form.get('niveau', '').strip()

    if not all([nom, prenom, telephone, email, mdp, filiere, niveau]):
        flash('Tous les champs sont obligatoires.', 'danger')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Matières")
        matieres = cur.fetchall()
        cur.close()
        return render_template('inscription.html', matieres=matieres)

    if mdp != mdp_conf:
        flash('Les mots de passe ne correspondent pas.', 'danger')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Matières")
        matieres = cur.fetchall()
        cur.close()
        return render_template('inscription.html', matieres=matieres)

    if len(mdp) < 6:
        flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Matières")
        matieres = cur.fetchall()
        cur.close()
        return render_template('inscription.html', matieres=matieres)

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id_utilisateur FROM Utilisateurs WHERE email = %s OR telephone = %s",
        (email, telephone)
    )
    if cur.fetchone():
        cur.close()
        flash('Email ou téléphone déjà utilisé.', 'danger')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Matières")
        matieres = cur.fetchall()
        cur.close()
        return render_template('inscription.html', matieres=matieres)

    cur.execute(
        "INSERT INTO Utilisateurs (nom, prenom, telephone, email, mot_de_passe, filiere, niveau) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (nom, prenom, telephone, email, generate_password_hash(mdp), filiere, niveau)
    )
    mysql.connection.commit()
    id_utilisateur = cur.lastrowid

    for id_matiere in request.form.getlist('points_forts'):
        cur.execute(
            "INSERT INTO MAITRISE (id_utilisateur, id_matiere) VALUES (%s, %s)",
            (id_utilisateur, id_matiere)
        )

    for id_matiere in request.form.getlist('points_faibles'):
        cur.execute(
            "INSERT INTO BESOIN (id_utilisateur, id_matiere) VALUES (%s, %s)",
            (id_utilisateur, id_matiere)
        )

    mysql.connection.commit()
    cur.close()

    flash('Inscription réussie ! Connectez-vous.', 'success')
    return redirect(url_for('auth.connexion'))


@auth_bp.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'GET':
        return render_template('connexion.html')

    identifiant = request.form.get('identifiant', '').strip().lower()
    mdp         = request.form.get('mot_de_passe', '')

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM Utilisateurs WHERE email = %s OR telephone = %s",
        (identifiant, identifiant)
    )
    utilisateur = cur.fetchone()
    cur.close()

    if not utilisateur or not check_password_hash(utilisateur['mot_de_passe'], mdp):
        flash('Identifiant ou mot de passe incorrect.', 'danger')
        return render_template('connexion.html')

    session.clear()
    session['id']     = utilisateur['id_utilisateur']
    session['nom']    = utilisateur['nom']
    session['prenom'] = utilisateur['prenom']

    flash(f"Bienvenue {utilisateur['prenom']} !", 'success')
    return redirect(url_for('annonces.liste'))


@auth_bp.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect(url_for('auth.connexion'))