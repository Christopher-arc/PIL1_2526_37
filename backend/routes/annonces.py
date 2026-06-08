from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import mysql

annonces_bp = Blueprint('annonces', __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'id' not in session:
            flash("Connectez-vous d'abord.", 'danger')
            return redirect(url_for('auth.connexion'))
        return f(*args, **kwargs)
    return decorated


@annonces_bp.route('/annonces', methods=['GET'])
@login_required
def liste():
    matiere        = request.args.get('matiere', '')
    format_session = request.args.get('format_session', '')
    id_dispo       = request.args.get('dispo', '')
    type_annonce   = request.args.get('type_annonce', '')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM `Matieres`")
    matieres = cur.fetchall()

    cur.execute("SELECT * FROM `Disponibilites`")
    dispos = cur.fetchall()

    cur.execute("SELECT id_matiere FROM BESOIN WHERE id_utilisateur = %s", (session['id'],))
    mes_lacunes = [r['id_matiere'] for r in cur.fetchall()]

    cur.execute("SELECT id_matiere FROM MAITRISE WHERE id_utilisateur = %s", (session['id'],))
    mes_competences = [r['id_matiere'] for r in cur.fetchall()]

    cur.execute("SELECT id_annonce FROM `Reponses` WHERE id_utilisateur = %s", (session['id'],))
    deja_repondu = [r['id_annonce'] for r in cur.fetchall()]

    annonces_pertinentes = []

    if mes_lacunes or mes_competences:
        query = """
            SELECT a.*,
                   u.nom, u.prenom, u.filiere, u.niveau, u.photo,
                   GROUP_CONCAT(DISTINCT m.nom_matiere ORDER BY m.nom_matiere SEPARATOR ', ') AS matieres_annonce,
                   GROUP_CONCAT(DISTINCT CONCAT(d.jour, ' ', d.heure_debut, '-', d.heure_fin) SEPARATOR ' | ') AS dispos_annonce
            FROM Annonces a
            JOIN Utilisateurs u ON a.id_utilisateur = u.id_utilisateur
            LEFT JOIN ANNONCE_MATIERE am ON a.id_annonce = am.id_annonce
            LEFT JOIN `Matières` m ON am.id_matiere = m.id_matiere
            LEFT JOIN ANNONCE_DISPONIBILITE ad ON a.id_annonce = ad.id_annonce
            LEFT JOIN `Disponibilites` d ON ad.id_dispo = d.id_dispo
            WHERE a.statut = 'actif'
            AND a.id_utilisateur != %s
            AND (
                (a.type_annonce = 'offre'   AND am.id_matiere IN ({lacunes}))
                OR
                (a.type_annonce = 'demande' AND am.id_matiere IN ({competences}))
            )
        """.format(
            lacunes    =','.join(['%s'] * len(mes_lacunes))     if mes_lacunes     else '0',
            competences=','.join(['%s'] * len(mes_competences)) if mes_competences else '0'
        )

        params = [session['id']] + mes_lacunes + mes_competences

        if matiere:
            query += " AND am.id_matiere = %s"
            params.append(matiere)

        if format_session:
            query += " AND a.format_session = %s"
            params.append(format_session)

        if id_dispo:
            query += " AND ad.id_dispo = %s"
            params.append(id_dispo)

        if type_annonce:
            query += " AND a.type_annonce = %s"
            params.append(type_annonce)

        query += " GROUP BY a.id_annonce ORDER BY a.date_creation DESC"

        cur.execute(query, params)
        annonces_pertinentes = cur.fetchall()

    cur.close()

    return render_template('annonces.html',
                           annonces=annonces_pertinentes,
                           matieres=matieres,
                           dispos=dispos,
                           matiere=matiere,
                           format_session=format_session,
                           id_dispo=id_dispo,
                           type_annonce=type_annonce,
                           mes_lacunes=mes_lacunes,
                           mes_competences=mes_competences,
                           deja_repondu=deja_repondu)


@annonces_bp.route('/annonces/new', methods=['POST'])
@login_required
def new():
    type_annonce   = request.form.get('type_annonce', '')
    format_session = request.form.get('format_session', '')
    description    = request.form.get('description_perso', '').strip()
    id_matieres    = request.form.getlist('matieres')
    id_dispos      = request.form.getlist('disponibilites')

    if not all([type_annonce, format_session]):
        flash('Type et format sont obligatoires.', 'danger')
        return redirect(url_for('annonces.liste'))

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO Annonces (id_utilisateur, type_annonce, format_session, description_perso) VALUES (%s, %s, %s, %s)",
        (session['id'], type_annonce, format_session, description)
    )
    mysql.connection.commit()
    id_annonce = cur.lastrowid

    for id_matiere in id_matieres:
        cur.execute("INSERT INTO ANNONCE_MATIERE (id_annonce, id_matiere) VALUES (%s, %s)", (id_annonce, id_matiere))

    for id_dispo in id_dispos:
        cur.execute("INSERT INTO ANNONCE_DISPONIBILITE (id_annonce, id_dispo) VALUES (%s, %s)", (id_annonce, id_dispo))

    mysql.connection.commit()
    cur.close()

    flash('Annonce créée avec succès.', 'success')
    return redirect(url_for('annonces.liste'))


@annonces_bp.route('/annonces/repondre', methods=['POST'])
@login_required
def repondre():
    id_annonce     = request.form.get('id_annonce')
    message_accomp = request.form.get('message_accomp', '').strip()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_utilisateur FROM Annonces WHERE id_annonce = %s", (id_annonce,))
    annonce = cur.fetchone()

    if not annonce:
        cur.close()
        flash('Annonce introuvable.', 'danger')
        return redirect(url_for('annonces.liste'))

    if annonce['id_utilisateur'] == session['id']:
        cur.close()
        flash('Vous ne pouvez pas répondre à votre propre annonce.', 'danger')
        return redirect(url_for('annonces.liste'))

    cur.execute(
        "SELECT id_reponse FROM `Reponses` WHERE id_utilisateur = %s AND id_annonce = %s",
        (session['id'], id_annonce)
    )
    if cur.fetchone():
        cur.close()
        flash('Vous avez déjà répondu à cette annonce.', 'danger')
        return redirect(url_for('annonces.liste'))

    cur.execute(
        "INSERT INTO `Reponses` (id_utilisateur, id_annonce, message_accomp) VALUES (%s, %s, %s)",
        (session['id'], id_annonce, message_accomp)
    )
    mysql.connection.commit()
    cur.close()

    flash('Réponse envoyée.', 'success')
    return redirect(url_for('annonces.liste'))

@annonces_bp.route('/utilisateur/<int:id_utilisateur>')
@login_required
def voir_profil(id_utilisateur):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (id_utilisateur,))
    utilisateur = cur.fetchone()

    if not utilisateur:
        cur.close()
        flash('Utilisateur introuvable.', 'danger')
        return redirect(url_for('annonces.liste'))

    cur.execute("""
        SELECT m.nom_matiere FROM MAITRISE ma
        JOIN `Matieres` m ON ma.id_matiere = m.id_matiere
        WHERE ma.id_utilisateur = %s
    """, (id_utilisateur,))
    points_forts = cur.fetchall()

    cur.execute("""
        SELECT m.nom_matiere FROM BESOIN b
        JOIN `Matieres` m ON b.id_matiere = m.id_matiere
        WHERE b.id_utilisateur = %s
    """, (id_utilisateur,))
    points_faibles = cur.fetchall()

    cur.execute("""
        SELECT d.jour, d.heure_debut, d.heure_fin FROM USER_DISPONIBILITE ud
        JOIN `Disponibilites` d ON ud.id_dispo = d.id_dispo
        WHERE ud.id_utilisateur = %s
    """, (id_utilisateur,))
    dispos = cur.fetchall()

    cur.close()
    return render_template('voir_profil.html',
                           utilisateur=utilisateur,
                           points_forts=points_forts,
                           points_faibles=points_faibles,
                           dispos=dispos)