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