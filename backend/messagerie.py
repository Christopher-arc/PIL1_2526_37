from flask import Blueprint, render_template, request, session, redirect, url_for, flash
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

@messagerie_bp.route('/messagerie')
@login_required
def messagerie():
    """Page messagerie - Liste les discussions de l'utilisateur"""
    user_id = session['id']
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT d.*, 
               GROUP_CONCAT(DISTINCT u.nom SEPARATOR ', ') as participants
        FROM Discussions d
        JOIN PARTICIPATION p ON d.id_discussion = p.id_discussion
        JOIN Utilisateurs u ON p.id_utilisateur = u.id_utilisateur
        WHERE d.id_discussion IN (
            SELECT id_discussion FROM PARTICIPATION WHERE id_utilisateur = %s
        )
        GROUP BY d.id_discussion
        ORDER BY d.date_creation DESC
    """, (user_id,))
    discussions = cur.fetchall()
    
    messages = []
    discussion_id = None
    
    if discussions:
        discussion_id = discussions[0]['id_discussion']
        cur.execute("""
            SELECT m.*, u.nom, u.prenom, u.photo
            FROM Messages m
            JOIN Utilisateurs u ON m.id_utilisateur = u.id_utilisateur
            WHERE m.id_discussion = %s
            ORDER BY m.date_envoi ASC
        """, (discussion_id,))
        messages = cur.fetchall()
    
    cur.close()
    
    # Variables pour base.html
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
    utilisateur = cur.fetchone()
    cur.close()
    
    initiales = (utilisateur['nom'][0] + utilisateur['prenom'][0]).upper() if utilisateur else '?'
    
    return render_template(
        'messagerie.html',
        user={
            'initiales': initiales,
            'nom': f"{utilisateur['prenom']} {utilisateur['nom']}" if utilisateur else '',
            'filiere': utilisateur['filiere'] if utilisateur else '',
            'niveau': utilisateur['niveau'] if utilisateur else '',
        },
        discussions=discussions,
        messages=messages,
        active='messagerie'
    )

@messagerie_bp.route('/discussion/<int:discussion_id>')
@login_required
def discussion(discussion_id):
    """Charger une discussion spécifique"""
    user_id = session['id']
    cur = mysql.connection.cursor()
    
    # Vérifier que l'utilisateur participe à cette discussion
    cur.execute("""
        SELECT * FROM PARTICIPATION 
        WHERE id_discussion = %s AND id_utilisateur = %s
    """, (discussion_id, user_id))
    
    if not cur.fetchone():
        cur.close()
        flash("Accès refusé.", 'danger')
        return redirect(url_for('messagerie.messagerie'))
    
    # Charger les messages
    cur.execute("""
        SELECT m.*, u.nom, u.prenom
        FROM Messages m
        JOIN Utilisateurs u ON m.id_utilisateur = u.id_utilisateur
        WHERE m.id_discussion = %s
        ORDER BY m.date_envoi ASC
    """, (discussion_id,))
    messages = cur.fetchall()
    cur.close()
    
    return render_template(
        'messagerie.html',
        messages=messages,
        active='messagerie'
    )
@messagerie_bp.route('/nouveau_message', methods=['POST'])
@login_required
def nouveau_message():
    """Envoyer un message dans une discussion (fallback sans SocketIO)"""
    user_id = session['id']
    discussion_id = request.form.get('discussion_id')
    contenu = request.form.get('contenu', '').strip()

    if not discussion_id or not contenu:
        flash("Message vide ou discussion invalide.", 'danger')
        return redirect(url_for('messagerie.messagerie'))

    cur = mysql.connection.cursor()
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
    return redirect(url_for('messagerie.discussion', discussion_id=discussion_id))


def register_socketio_events(socketio):
    """
    Enregistre les événements Socket.IO pour la messagerie temps réel.
    Appelée depuis App_final.py après création du socketio.
    """

    @socketio.on('rejoindre_discussion')
    def on_rejoindre(data):
        from flask_socketio import join_room
        discussion_id = data.get('discussion_id')
        if discussion_id:
            join_room(str(discussion_id))

    @socketio.on('envoyer_message')
    def on_message(data):
        from flask_socketio import emit
        from datetime import datetime

        user_id = session.get('id')
        discussion_id = data.get('discussion_id')
        contenu = data.get('contenu', '').strip()

        if not user_id or not discussion_id or not contenu:
            return

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM PARTICIPATION WHERE id_discussion = %s AND id_utilisateur = %s",
            (discussion_id, user_id)
        )
        if not cur.fetchone():
            cur.close()
            return

        cur.execute(
            "INSERT INTO Messages (id_discussion, id_utilisateur, contenu) VALUES (%s, %s, %s)",
            (discussion_id, user_id, contenu)
        )
        mysql.connection.commit()
        id_message = cur.lastrowid

        cur.execute(
            "SELECT nom, prenom FROM Utilisateurs WHERE id_utilisateur = %s",
            (user_id,)
        )
        u = cur.fetchone()
        cur.close()

        emit('nouveau_message', {
            'id_message': id_message,
            'id_utilisateur': user_id,
            'nom': u['nom'] if u else '',
            'prenom': u['prenom'] if u else '',
            'contenu': contenu,
            'date_envoi': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }, room=str(discussion_id))