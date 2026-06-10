"""
IFRI MentorLink - Application Flask FINALE V3 (CORRIGÉE)
Corrections :
  - Import blueprints depuis routes/ ET racine (messagerie)
  - Route / → /dashboard
  - Route /dashboard avec login_required
  - Context processor global → user dispo dans TOUS les templates
"""

import os
from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_socketio import SocketIO
from functools import wraps
from db import init_db, mysql

# ============================================================================
# 1. INITIALISATION
# ============================================================================
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__),   '..', 'frontend', 'statics'),
    static_url_path='/statics'
)

app.secret_key = 'mentorlink_secret_2026'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*")
init_db(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'statics', 'photos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ============================================================================
# 2. BLUEPRINTS
# ============================================================================
from routes.auth     import auth_bp
from routes.profil   import profil_bp
from routes.annonces import annonces_bp
from messagerie      import messagerie_bp, register_socketio_events

app.register_blueprint(auth_bp)
app.register_blueprint(profil_bp)
app.register_blueprint(annonces_bp)
app.register_blueprint(messagerie_bp)

register_socketio_events(socketio)

# ============================================================================
# 3. HELPERS
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            flash("Connectez-vous d'abord.", 'danger')
            return redirect(url_for('auth.connexion'))
        return f(*args, **kwargs)
    return decorated_function


def build_user_context(utilisateur):
    if not utilisateur:
        return {'id': None, 'initiales': '?', 'nom': 'Utilisateur',
                'prenom': '', 'filiere': '', 'niveau': '', 'email': ''}
    initiales = (utilisateur['nom'][0] + utilisateur['prenom'][0]).upper()
    return {
        'id':        utilisateur['id_utilisateur'],
        'initiales': initiales,
        'nom':       f"{utilisateur['prenom']} {utilisateur['nom']}",
        'prenom':    utilisateur['prenom'],
        'filiere':   utilisateur['filiere'],
        'niveau':    utilisateur['niveau'],
        'email':     utilisateur['email'],
        'bio':       utilisateur.get('Bio', ''),
        'photo':     utilisateur.get('photo', ''),
    }


def get_current_user():
    """Retourne (utilisateur_dict, user_context) pour l'utilisateur connecté."""
    if 'id' not in session:
        return None, None
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (session['id'],))
    utilisateur = cur.fetchone()
    cur.close()
    return utilisateur, build_user_context(utilisateur)


# ============================================================================
# 4. CONTEXT PROCESSOR GLOBAL
# ============================================================================
# Injecte automatiquement `user` dans TOUS les templates (base.html inclus)
# Plus besoin de passer user= dans chaque render_template des blueprints.

@app.context_processor
def inject_user():
    _, user_context = get_current_user()
    return dict(user=user_context)


# ============================================================================
# 5. ROUTES GLOBALES
# ============================================================================

@app.route('/')
def home():
    if 'id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.connexion'))


@app.route('/test')
def test():
    return "✅ IFRI MentorLink is running. Dieu est grand"


# ============================================================================
# 6. DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['id']
    utilisateur, user_context = get_current_user()

    cur = mysql.connection.cursor()

    # Matchs (sessions réalisées)
    cur.execute("""
        SELECT COUNT(*) as n FROM Matching
        WHERE id_mentor = %s OR id_mentore = %s
    """, (user_id, user_id))
    nb_sessions = cur.fetchone()['n']

    # Compétences
    cur.execute("SELECT COUNT(*) as n FROM MAITRISE WHERE id_utilisateur = %s", (user_id,))
    nb_comp = cur.fetchone()['n']

    # Annonces publiées
    cur.execute("SELECT COUNT(*) as n FROM Annonces WHERE id_utilisateur = %s", (user_id,))
    nb_offres = cur.fetchone()['n']

    # Notifications non lues
    nb_notifs = 0
    try:
        cur.execute("SELECT COUNT(*) as n FROM Notifications WHERE id_utilisateur = %s AND lu = FALSE", (user_id,))
        nb_notifs = cur.fetchone()['n']
    except Exception:
        pass

    stats = {
        'sessions':         nb_sessions,
        'competences':      nb_comp,
        'messages_non_lus': nb_notifs,
        'mes_offres':       nb_offres,
    }

    # Offres récentes
    cur.execute("""
        SELECT a.id_annonce, a.type_annonce, a.description_perso, u.nom, u.prenom
        FROM Annonces a
        JOIN Utilisateurs u ON a.id_utilisateur = u.id_utilisateur
        WHERE a.statut = 'actif' AND a.id_utilisateur != %s
        ORDER BY a.date_creation DESC LIMIT 3
    """, (user_id,))
    raw_offres = cur.fetchall()
    offres_recentes = [{
        'titre':      (o['description_perso'] or o['type_annonce'])[:45],
        'auteur':     f"{o['prenom']} {o['nom']}",
        'type':       o['type_annonce'],
        'type_class': 'bo' if o['type_annonce'] == 'offre' else 'bd',
    } for o in raw_offres]

    cur.close()

    # Meilleurs matchs depuis l'algorithme
    from matching import trouver_mentors
    couleurs = ['#7c3aed', '#2ecc71', '#e67e22', '#3498db', '#e74c3c']
    bruts = trouver_mentors(user_id, mysql)
    meilleurs_matchs = []
    for i, m in enumerate(bruts[:5]):
        total = round(m['score_matieres'] * 4.5 + m['score_dispos'] * 4.0 + m['score_filiere'] * 1.5)
        meilleurs_matchs.append({
            'nom':          f"{m['prenom']} {m['nom']}",
            'initiales':    (m['nom'][0] + m['prenom'][0]).upper(),
            'filiere':      m['filiere'],
            'niveau':       m['niveau'],
            'score':        total,
            'couleur':      couleurs[i % len(couleurs)],
            'badge_classe': 'bv',
            'badge_texte':  'Mentor recommandé',
        })

    return render_template(
        'dashboard.html',
        stats=stats,
        meilleurs_matchs=meilleurs_matchs,
        offres_recentes=offres_recentes,
        active='dashboard'
    )


# ============================================================================
# 7. MATCHING
# ============================================================================

@app.route('/matching')
@login_required
def matching():
    from matching import trouver_mentors

    matching_filter = request.args.get('filter', 'all')
    min_score       = int(request.args.get('min', 0))
    user_id         = session['id']

    bruts = trouver_mentors(user_id, mysql)

    couleurs = ['#7c3aed', '#2ecc71', '#e67e22', '#3498db', '#e74c3c',
                '#1abc9c', '#9b59b6', '#f39c12', '#16a085', '#c0392b']
    matching_data = []

    for i, m in enumerate(bruts):
        competences_pts = round(m['score_matieres'] * 4.5)
        dispo_pts       = round(m['score_dispos']   * 4.0)
        filiere_pts     = round(m['score_filiere']  * 1.5)
        total           = competences_pts + dispo_pts + filiere_pts

        if total < min_score:
            continue
        if matching_filter == 'mentor' and m.get('role', 'mentor') != 'mentor':
            continue
        if matching_filter == 'mentore' and m.get('role', 'mentor') != 'mentore':
            continue

        matching_data.append({
            'id_mentor':     m['id_mentor'],
            'nom':           f"{m['prenom']} {m['nom']}",
            'initiales':     (m['nom'][0] + m['prenom'][0]).upper(),
            'filiere':       m['filiere'],
            'niveau':        m['niveau'],
            'role':          'mentor',
            'competences':   competences_pts,
            'dispo_score':   dispo_pts,
            'filiere_score': filiere_pts,
            'total':         total,
            'couleur':       couleurs[i % len(couleurs)],
        })

    return render_template(
        'matching.html',
        matching_data=matching_data,
        matching_filter=matching_filter,
        min_score=min_score,
        active='matching'
    )


# ============================================================================
# 8. EXPLORER
# ============================================================================

@app.route('/explorer')
@login_required
def explorer():
    user_id = session['id']

    cur = mysql.connection.cursor()

    def td_str(td):
        if td is None: return ''
        if hasattr(td, 'total_seconds'):
            t = int(td.total_seconds())
            return f"{t//3600:02d}:{(t%3600)//60:02d}:00"
        return str(td)

    cur.execute("SELECT * FROM `Matieres`")
    matieres = cur.fetchall()

    cur.execute("SELECT * FROM `Disponibilites`")
    dispos = [{'id_dispo': d['id_dispo'], 'jour': d['jour'],
               'heure_debut': td_str(d['heure_debut']), 'heure_fin': td_str(d['heure_fin'])}
              for d in cur.fetchall()]

    cur.execute("SELECT id_matiere FROM BESOIN WHERE id_utilisateur = %s",   (user_id,))
    mes_lacunes = [r['id_matiere'] for r in cur.fetchall()]

    cur.execute("SELECT id_matiere FROM MAITRISE WHERE id_utilisateur = %s", (user_id,))
    mes_competences = [r['id_matiere'] for r in cur.fetchall()]

    # Annonces (toutes actives, pas les siennes)
    cur.execute("""
        SELECT a.*, u.nom, u.prenom, u.filiere, u.niveau, u.photo,
               a.id_utilisateur,
               GROUP_CONCAT(DISTINCT m.nom_matiere ORDER BY m.nom_matiere SEPARATOR ', ') AS matieres_annonce
        FROM Annonces a
        JOIN Utilisateurs u ON a.id_utilisateur = u.id_utilisateur
        LEFT JOIN ANNONCE_MATIERE am ON a.id_annonce = am.id_annonce
        LEFT JOIN `Matieres` m ON am.id_matiere = m.id_matiere
        WHERE a.statut = 'actif' AND a.id_utilisateur != %s
        GROUP BY a.id_annonce
        ORDER BY a.date_creation DESC LIMIT 30
    """, (user_id,))
    annonces_pertinentes = cur.fetchall()

    # Profils des autres utilisateurs
    cur.execute("""
        SELECT u.id_utilisateur, u.nom, u.prenom, u.filiere, u.niveau, u.Bio,
               GROUP_CONCAT(DISTINCT m.nom_matiere SEPARATOR ', ') AS competences_str
        FROM Utilisateurs u
        LEFT JOIN MAITRISE ma ON u.id_utilisateur = ma.id_utilisateur
        LEFT JOIN `Matieres` m ON ma.id_matiere = m.id_matiere
        WHERE u.id_utilisateur != %s
        GROUP BY u.id_utilisateur
        LIMIT 40
    """, (user_id,))
    raw_profils = cur.fetchall()
    cur.close()

    couleurs = ['#7c3aed','#2ecc71','#e67e22','#3498db','#e74c3c',
                '#1abc9c','#9b59b6','#f39c12','#16a085','#c0392b']
    profils = []
    for i, p in enumerate(raw_profils):
        comps = p['competences_str'].split(', ') if p['competences_str'] else []
        profils.append({
            'id':          p['id_utilisateur'],
            'nom':         f"{p['prenom']} {p['nom']}",
            'initiales':   (p['nom'][0] + p['prenom'][0]).upper(),
            'filiere':     p['filiere'] or '',
            'niveau':      p['niveau']  or '',
            'bio':         p['Bio']     or '',
            'competences': comps,
            'couleur':     couleurs[i % len(couleurs)],
            'note':        4.5,
            'sessions':    0,
        })

    return render_template(
        'explorer.html',
        annonces=annonces_pertinentes,
        profils=profils,
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
def page_not_found(e):
    return "Page non trouvée – <a href='/dashboard'>Retour</a>", 404

@app.errorhandler(500)
def internal_error(e):
    return "Erreur serveur", 500


# ============================================================================
# 10. DÉMARRAGE
# ============================================================================

if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080, host='0.0.0.0', allow_unsafe_werkzeug=True)