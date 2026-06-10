from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from functools import wraps
from db import mysql

messagerie_bp = Blueprint('messagerie', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'id' not in session:
            flash("Connectez-vous d'abord.", 'danger')
            return redirect(url_for('auth.connexion'))
        return f(*args, **kwargs)
    return decorated


def register_socketio_events(socketio):
    from flask_socketio import emit, join_room

    @socketio.on('rejoindre_discussion')
    def handle_join(data):
        room = str(data.get('discussion_id'))
        join_room(room)

    @socketio.on('envoyer_message')
    def handle_message(data):
        discussion_id = data.get('discussion_id')
        contenu       = data.get('contenu', '').strip()
        user_id       = session.get('id')

        if not contenu or not discussion_id or not user_id:
            return

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO Messages (id_discussion, id_utilisateur, contenu) VALUES (%s, %s, %s)",
            (discussion_id, user_id, contenu)
        )
        mysql.connection.commit()
        id_msg = cur.lastrowid

        cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
        u = cur.fetchone()
        cur.close()

        emit('nouveau_message', {
            'id_message':    id_msg,
            'contenu':       contenu,
            'id_utilisateur': user_id,
            'nom':           u['nom'] if u else '',
            'prenom':        u['prenom'] if u else '',
        }, room=str(discussion_id))


def _build_user_context(utilisateur):
    if not utilisateur:
        return {'initiales': '?', 'nom': '', 'filiere': '', 'niveau': ''}
    initiales = (utilisateur['nom'][0] + utilisateur['prenom'][0]).upper()
    return {
        'id':        utilisateur['id_utilisateur'],
        'initiales': initiales,
        'nom':       f"{utilisateur['prenom']} {utilisateur['nom']}",
        'prenom':    utilisateur['prenom'],
        'filiere':   utilisateur['filiere'],
        'niveau':    utilisateur['niveau'],
        'email':     utilisateur['email'],
    }


# ── Page principale messagerie ────────────────────────────────────────────────
@messagerie_bp.route('/messagerie')
@login_required
def messagerie():
    user_id = session['id']
    cur = mysql.connection.cursor()

    # Toutes les discussions de l'utilisateur avec le dernier message
    cur.execute("""
        SELECT d.id_discussion, d.date_creation,
               GROUP_CONCAT(DISTINCT CONCAT(u.prenom, ' ', u.nom)
                   ORDER BY u.nom SEPARATOR ', ') AS participants,
               (SELECT contenu FROM Messages
                WHERE id_discussion = d.id_discussion
                ORDER BY date_envoi DESC LIMIT 1) AS dernier_message,
               (SELECT date_envoi FROM Messages
                WHERE id_discussion = d.id_discussion
                ORDER BY date_envoi DESC LIMIT 1) AS date_dernier
        FROM Discussions d
        JOIN PARTICIPATION p  ON d.id_discussion = p.id_discussion
        JOIN PARTICIPATION p2 ON d.id_discussion = p2.id_discussion
        JOIN Utilisateurs u   ON p2.id_utilisateur = u.id_utilisateur
        WHERE p.id_utilisateur = %s
          AND u.id_utilisateur != %s
        GROUP BY d.id_discussion
        ORDER BY date_dernier DESC
    """, (user_id, user_id))
    discussions = cur.fetchall()

    # Discussion active (paramètre GET ou première)
    discussion_id = request.args.get('discussion', None)
    if discussion_id:
        discussion_id = int(discussion_id)
    elif discussions:
        discussion_id = discussions[0]['id_discussion']

    messages = []
    if discussion_id:
        cur.execute("""
            SELECT m.*, u.nom, u.prenom, u.photo
            FROM Messages m
            JOIN Utilisateurs u ON m.id_utilisateur = u.id_utilisateur
            WHERE m.id_discussion = %s
            ORDER BY m.date_envoi ASC
        """, (discussion_id,))
        messages = cur.fetchall()

    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
    utilisateur = cur.fetchone()
    cur.close()

    return render_template(
        'messagerie.html',
        user=_build_user_context(utilisateur),
        discussions=discussions,
        messages=messages,
        discussion_active=discussion_id,
        active='messagerie'
    )


# ── Créer ou rejoindre une discussion avec un utilisateur ────────────────────
@messagerie_bp.route('/messagerie/contacter/<int:id_destinataire>', methods=['GET', 'POST'])
@login_required
def contacter(id_destinataire):
    """
    Appelé depuis la page annonces ou explorer quand on clique "Contacter".
    Crée une discussion privée entre l'utilisateur connecté et le destinataire
    si elle n'existe pas déjà, puis redirige vers la messagerie.
    """
    user_id = session['id']

    if id_destinataire == user_id:
        flash("Vous ne pouvez pas vous envoyer un message.", 'danger')
        return redirect(url_for('messagerie.messagerie'))

    cur = mysql.connection.cursor()

    # Chercher si une discussion privée existe déjà entre les deux
    cur.execute("""
        SELECT p1.id_discussion
        FROM PARTICIPATION p1
        JOIN PARTICIPATION p2 ON p1.id_discussion = p2.id_discussion
        WHERE p1.id_utilisateur = %s AND p2.id_utilisateur = %s
        GROUP BY p1.id_discussion
        HAVING COUNT(DISTINCT p1.id_utilisateur) >= 1
        LIMIT 1
    """, (user_id, id_destinataire))
    existante = cur.fetchone()

    if existante:
        discussion_id = existante['id_discussion']
    else:
        # Créer une nouvelle discussion
        cur.execute("INSERT INTO Discussions () VALUES ()")
        mysql.connection.commit()
        discussion_id = cur.lastrowid

        cur.execute(
            "INSERT INTO PARTICIPATION (id_discussion, id_utilisateur) VALUES (%s, %s)",
            (discussion_id, user_id)
        )
        cur.execute(
            "INSERT INTO PARTICIPATION (id_discussion, id_utilisateur) VALUES (%s, %s)",
            (discussion_id, id_destinataire)
        )

        # Message d'accroche si fourni (depuis formulaire annonce)
        message_init = request.form.get('message_accomp', '').strip()
        if message_init:
            cur.execute(
                "INSERT INTO Messages (id_discussion, id_utilisateur, contenu) VALUES (%s, %s, %s)",
                (discussion_id, user_id, message_init)
            )

        mysql.connection.commit()

    cur.close()
    flash("Conversation ouverte !", 'success')
    return redirect(url_for('messagerie.messagerie', discussion=discussion_id))


# ── Envoyer un message (fallback sans SocketIO) ───────────────────────────────
@messagerie_bp.route('/messagerie/envoyer', methods=['POST'])
@login_required
def envoyer():
    user_id       = session['id']
    discussion_id = request.form.get('discussion_id')
    contenu       = request.form.get('contenu', '').strip()

    if not contenu or not discussion_id:
        return redirect(url_for('messagerie.messagerie'))

    cur = mysql.connection.cursor()
    # Vérifier que l'utilisateur participe à la discussion
    cur.execute(
        "SELECT * FROM PARTICIPATION WHERE id_discussion = %s AND id_utilisateur = %s",
        (discussion_id, user_id)
    )
    if not cur.fetchone():
        cur.close()
        flash("Accès refusé.", 'danger')
        return redirect(url_for('messagerie.messagerie'))

    cur.execute(
        "INSERT INTO Messages (id_discussion, id_utilisateur, contenu) VALUES (%s, %s, %s)",
        (discussion_id, user_id, contenu)
    )
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('messagerie.messagerie', discussion=discussion_id))
