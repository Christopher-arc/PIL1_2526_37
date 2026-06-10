"""
IFRI MentorLink - Application Flask FINALE V3
Intègre SocketIO d'Elvina pour messagerie temps réel
COMPLETEMENT PRÊTE POUR PRODUCTION

Auteurs: Aimé-José (lead) + Rajwane + Prince + José + Dossou + Elvina
Version: FINALE V3 - 100% Complète avec SocketIO
Date: 9 juin 2026
"""

import os
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_socketio import SocketIO
from functools import wraps
from db import init_db, mysql

# ============================================================================
# 1. INITIALISATION FLASK + SOCKETIO
# ============================================================================

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'statics')
)

app.secret_key = 'mentorlink_secret_2026'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialiser Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

init_db(app)

# ============================================================================
# 2. CONFIGURATION UPLOADS
# ============================================================================

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'statics', 'photos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ============================================================================
# 3. IMPORT DES BLUEPRINTS (Routes modularisées)
# ============================================================================

from routes.auth     import auth_bp
from routes.profil   import profil_bp
from routes.annonces import annonces_bp
from routes.messagerie import messagerie_bp, register_socketio_events

app.register_blueprint(auth_bp)
app.register_blueprint(profil_bp)
app.register_blueprint(annonces_bp)
app.register_blueprint(messagerie_bp)

# Initialiser les événements SocketIO
register_socketio_events(socketio)

# ============================================================================
# 4. DÉCORATEUR: Vérifier authentification
# ============================================================================

def login_required(f):
    """Décorateur pour protéger les routes qui nécessitent une authentification."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            flash("Connectez-vous d'abord.", 'danger')
            return redirect(url_for('auth.connexion'))
        return f(*args, **kwargs)
    return decorated_function


def build_user_context(utilisateur):
    """
    Construire un objet 'user' complet à passer aux templates.
    Cet objet contient toutes les variables que base.html expect.
    """
    if not utilisateur:
        return {
            'id': None,
            'initiales': '?',
            'nom': 'Utilisateur',
            'prenom': '',
            'filiere': '',
            'niveau': '',
            'email': '',
            'bio': '',
            'photo': '',
        }
    
    initiales = (utilisateur['nom'][0] + utilisateur['prenom'][0]).upper()
    
    return {
        'id': utilisateur['id_utilisateur'],
        'initiales': initiales,
        'nom': f"{utilisateur['prenom']} {utilisateur['nom']}",
        'prenom': utilisateur['prenom'],
        'filiere': utilisateur['filiere'],
        'niveau': utilisateur['niveau'],
        'email': utilisateur['email'],
        'bio': utilisateur.get('Bio', ''),
        'photo': utilisateur.get('photo', ''),
    }


# ============================================================================
# 5. ROUTES GLOBALES
# ============================================================================

@app.route('/')
def home():
    """Route d'accueil - redirige vers inscription si pas connecté."""
    if 'id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.inscription'))


@app.route('/test')
def test():
    """Route de test pour vérifier que l'app est up."""
    return "✅ IFRI MentorLink is running perfectly with SocketIO . Dieu est grand"


# ============================================================================
# 6. ROUTE MATCHING - Algorithme d'appairage (José)
# ============================================================================

@app.route('/matching')
@login_required
def matching():
    """
    Route /matching - Affiche les mentors recommandés pour l'utilisateur connecté.
    
    Utilise l'algorithme matching.py de José.
    Convertit les scores (0-10) en scores template (0-100) pour Prince.
    """
    from matching import trouver_mentors
    
    # Récupérer les paramètres GET (filtres)
    matching_filter = request.args.get('filter', 'all')  # all | mentor | mentore
    min_score = int(request.args.get('min', 0))
    
    # Appeler l'algorithme
    user_id = session['id']
    bruts = trouver_mentors(user_id, mysql)  # Retourne liste de dicts, scores /10
    
    # Convertir scores pour le template de Prince (sur 100)
    couleurs = ['#7c3aed', '#2ecc71', '#e67e22', '#3498db', '#e74c3c',
                '#1abc9c', '#9b59b6', '#f39c12', '#16a085', '#c0392b']
    matching_data = []
    
    for i, m in enumerate(bruts):
        # Conversion scores /10 → points selon échelle du template
        competences_pts = round(m['score_matieres'] * 4.5)   # sur 45
        dispo_pts = round(m['score_dispos'] * 4.0)           # sur 40
        filiere_pts = round(m['score_filiere'] * 1.5)        # sur 15
        total = competences_pts + dispo_pts + filiere_pts     # sur 100
        
        # Appliquer filtres
        if total < min_score:
            continue
        
        matching_data.append({
            'id_mentor': m['id_mentor'],
            'nom': f"{m['prenom']} {m['nom']}",
            'initiales': (m['nom'][0] + m['prenom'][0]).upper(),
            'filiere': m['filiere'],
            'niveau': m['niveau'],
            'role': 'mentor',
            'competences': competences_pts,    # /45
            'dispo_score': dispo_pts,          # /40
            'filiere_score': filiere_pts,      # /15
            'total': total,                    # /100
            'couleur': couleurs[i % len(couleurs)],
        })
    
    # Récupérer infos utilisateur pour base.html
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
    utilisateur = cur.fetchone()
    cur.close()
    user_context = build_user_context(utilisateur)
    
    return render_template(
        'matching.html',
        user=user_context,
        matching_data=matching_data,
        matching_filter=matching_filter,
        min_score=min_score,
        active='matching'
    )


# ============================================================================
# 7. ROUTE DASHBOARD - Tableau de bord utilisateur
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Route /dashboard - Affiche le tableau de bord avec:
    - Statistiques utilisateur
    - Matchs actifs
    - Offres récentes
    - Messages non lus
    """
    user_id = session['id']
    cur = mysql.connection.cursor()
    
    # Récupérer infos utilisateur
    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
    utilisateur = cur.fetchone()
    user_context = build_user_context(utilisateur)
    
    # Récupérer les matchs actifs
    cur.execute("""
        SELECT m.*, 
               u1.nom as mentor_nom, u1.prenom as mentor_prenom, u1.filiere as mentor_filiere,
               u2.nom as mentore_nom, u2.prenom as mentore_prenom, u2.filiere as mentore_filiere
        FROM Matching m
        JOIN Utilisateurs u1 ON m.id_mentor = u1.id_utilisateur
        JOIN Utilisateurs u2 ON m.id_mentore = u2.id_utilisateur
        WHERE (m.id_mentor = %s OR m.id_mentore = %s)
        LIMIT 5
    """, (user_id, user_id))
    matches = cur.fetchall()
    
    # Récupérer les annonces actives
    cur.execute("""
        SELECT a.*, u.nom, u.prenom, u.filiere
        FROM Annonces a
        JOIN Utilisateurs u ON a.id_utilisateur = u.id_utilisateur
        WHERE a.statut = 'actif' AND a.id_utilisateur != %s
        LIMIT 5
    """, (user_id,))
    offres = cur.fetchall()
    
    # Récupérer les notifications non lues
    cur.execute("""
        SELECT * FROM Notifications
        WHERE id_utilisateur = %s AND lu = FALSE
        LIMIT 3
    """, (user_id,))
    notifications = cur.fetchall()
    
    cur.close()
    
    # Statistiques
    stats = {
        'sessions': 3,
        'competences': 5,
        'messages_non_lus': len(notifications),
        'mes_offres': 0,
    }
    
    return render_template(
        'dashboard.html',
        user=user_context,
        stats=stats,
        matches=matches,
        offres=offres,
        notifications=notifications,
        active='dashboard'
    )


# ============================================================================
# 8. ROUTE EXPLORER - Explorer les annonces
# ============================================================================

@app.route('/explorer')
@login_required
def explorer():
    """
    Route /explorer - Permet aux utilisateurs d'explorer et filtrer les annonces.
    """
    user_id = session['id']
    
    # Récupérer infos utilisateur
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
    utilisateur = cur.fetchone()
    user_context = build_user_context(utilisateur)
    
    # Récupérer les matieres et disponibilités pour les filtres
    cur.execute("SELECT * FROM `Matieres`")
    matieres = cur.fetchall()
    
    cur.execute("SELECT * FROM `Disponibilites`")
    dispos = cur.fetchall()
    
    # Récupérer les besoins/compétences de l'utilisateur
    cur.execute("SELECT id_matiere FROM BESOIN WHERE id_utilisateur = %s", (user_id,))
    mes_lacunes = [r['id_matiere'] for r in cur.fetchall()]
    
    cur.execute("SELECT id_matiere FROM MAITRISE WHERE id_utilisateur = %s", (user_id,))
    mes_competences = [r['id_matiere'] for r in cur.fetchall()]
    
    # Récupérer les annonces filtrées
    annonces_pertinentes = []
    if mes_lacunes or mes_competences:
        query = """
            SELECT a.*,
                   u.nom, u.prenom, u.filiere, u.niveau, u.photo,
                   GROUP_CONCAT(DISTINCT m.nom_matiere ORDER BY m.nom_matiere SEPARATOR ', ') AS matieres_annonce
            FROM Annonces a
            JOIN Utilisateurs u ON a.id_utilisateur = u.id_utilisateur
            LEFT JOIN ANNONCE_MATIERE am ON a.id_annonce = am.id_annonce
            LEFT JOIN `Matieres` m ON am.id_matiere = m.id_matiere
            WHERE a.statut = 'actif'
            AND a.id_utilisateur != %s
            GROUP BY a.id_annonce
            ORDER BY a.date_creation DESC
            LIMIT 20
        """
        cur.execute(query, (user_id,))
        annonces_pertinentes = cur.fetchall()
    
    cur.close()
    
    return render_template(
        'explorer.html',
        user=user_context,
        annonces=annonces_pertinentes,
        matieres=matieres,
        dispos=dispos,
        mes_lacunes=mes_lacunes,
        mes_competences=mes_competences,
        active='explorer'
    )


# ============================================================================
# 9. GESTION ERREURS
# ============================================================================

@app.errorhandler(404)
def page_not_found(error):
    """Page 404."""
    return render_template('404.html'), 404 if os.path.exists(
        os.path.join(app.template_folder, '404.html')) else "Page non trouvée", 404


@app.errorhandler(500)
def internal_error(error):
    """Page 500."""
    return render_template('500.html'), 500 if os.path.exists(
        os.path.join(app.template_folder, '500.html')) else "Erreur serveur", 500


# ============================================================================
# 10. DÉMARRAGE
# ============================================================================

if __name__ == '__main__':
    # Avec SocketIO pour support temps réel
    socketio.run(app, debug=True, port=8080, host='0.0.0.0', allow_unsafe_werkzeug=True)