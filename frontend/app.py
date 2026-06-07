from flask import Flask, request, render_template
from datetime import datetime

app = Flask(__name__)

# Données utilisateur
user = {
    'nom': 'Prince',
    'prenom': 'Prince',
    'initiales': 'P',
    'email': 'princetchimon@gmail.com',
    'filiere': 'RSI',
    'niveau': 'Licence 2',
    'statut': 'Mentoré·e',
    'sessions': 0,
    'membre_depuis': 'juin 2026',
    'biographie': '',
    'competences': ['SQL', 'Computer Vision', 'Git']
}

stats = {
    'sessions': 0,
    'competences': 3,
    'messages_non_lus': 0,
    'mes_offres': 0
}

meilleurs_matchs = [
    {'nom': 'Roméo Ahouansou', 'initiales': 'RA', 'filiere': 'RSI', 'niveau': 'Licence 3', 
     'score': 35, 'couleur': '#7c3aed', 'badge_classe': 'bv', 'badge_texte': 'Même filière'},
    {'nom': 'Fatoumata Diallo', 'initiales': 'FD', 'filiere': 'GLG', 'niveau': 'Master 1',
     'score': 29, 'couleur': '#2ecc71', 'badge_classe': 'bb', 'badge_texte': '2 compétences en commun'},
]

offres_recentes = [
    {'titre': 'Initiation au Machine Learning avec Python', 'auteur': 'Koffi Amédée Mensah', 'type': 'Offre', 'type_class': 'bo'},
    {'titre': 'Développement Web Full-Stack', 'auteur': 'Fatoumata Diallo', 'type': 'Offre', 'type_class': 'bo'},
]

# Données pour la page Explorer
profils = [
    {'nom': 'Koffi Amédée Mensah', 'initiales': 'KA', 'filiere': 'IA', 'role': 'Mentor', 
     'bio': 'Master 2 en IA, passionné par le traitement du langage naturel. J\'accompagne les juniors en ML/DL.', 
     'competences': ['Python', 'Machine Learning', 'Deep Learning', 'NLP'], 
     'note': 4.9, 'sessions': 18, 'couleur': '#e67e22'},
    {'nom': 'Fatoumata Diallo', 'initiales': 'FD', 'filiere': 'GLG', 'role': 'Mentor', 
     'bio': 'Développeuse full-stack en Master 1 GLG. Je propose du mentorat en développement web et mobile.', 
     'competences': ['Java', 'React', 'Node.js', 'SQL'], 
     'note': 4.7, 'sessions': 12, 'couleur': '#2ecc71'},
    {'nom': 'Roméo Ahouansou', 'initiales': 'RA', 'filiere': 'RSI', 'role': 'Mentor & Mentoré', 
     'bio': 'Spécialiste réseaux, je recherche un mentor en cybersécurité avancée et j\'offre du mentorat en administration réseau.', 
     'competences': ['Réseaux', 'Linux', 'Cybersécurité', 'Python'], 
     'note': 4.5, 'sessions': 6, 'couleur': '#7c3aed'},
    {'nom': 'Élise Noukpo', 'initiales': 'EN', 'filiere': 'IA', 'role': 'Mentoré', 
     'bio': 'Étudiante en L3 IA, je cherche un mentor pour m\'accompagner dans mon passage au ML et au Deep Learning.', 
     'competences': ['Python', 'Statistiques', 'Mathématiques', 'Algorithmique'], 
     'note': 5.0, 'sessions': 3, 'couleur': '#e74c3c'}
]

annonces = [
    {'type': 'offre', 'auteur': 'Karthi Ameline Mousain', 'initiales': 'KA', 'filiere': 'IA', 
     'titre': 'Initiation au Machine Learning avec Python', 
     'description': 'Je propose des sessions hebdomadaires pour apprendre les fondamentaux du ML : régression, classification, clustering. On utilise scikit-learn et pandas.', 
     'competences': ['Python', 'Machine Learning', 'Statistiques'], 
     'date': 'Publié le 10/01/2025', 'couleur': '#e67e22'},
    {'type': 'offre', 'auteur': 'Fabianna Diablo', 'initiales': 'FD', 'filiere': 'GLG', 
     'titre': 'Développement Web Full-Stack (React + Node.js)', 
     'description': 'Accompagnement complet pour créer des applications web modernes. De la maquette au déploiement, on couvre tout le processus.', 
     'competences': ['React', 'Node.js', 'SQL'], 
     'date': 'Publié le 12/01/2025', 'couleur': '#2ecc71'},
    {'type': 'demande', 'auteur': 'Elise Noukpo', 'initiales': 'EN', 'filiere': 'IA', 
     'titre': 'Recherche mentor pour transition vers le Deep Learning', 
     'description': "J'ai des bases en Python et en stats. Je cherche quelqu'un pour m'accompagner dans l'apprentissage des réseaux de neurones et TensorFlow.", 
     'competences': ['Deep Learning', 'Python', 'NLP'], 
     'date': 'Publié le 14/01/2025', 'couleur': '#e74c3c'},
    {'type': 'offre', 'auteur': 'Cédric Dossou', 'initiales': 'CD', 'filiere': 'Cybersécurité', 
     'titre': 'Introduction à la Cybersécurité et CTF', 
     'description': 'Pour les étudiants en RSI ou Cybersécurité souhaitant apprendre les bases de la sécurité offensive et participer à des CTF.', 
     'competences': ['Cybersécurité', 'Linux', 'Python'], 
     'date': 'Publié le 14/01/2025', 'couleur': '#3498db'}
]

# Données pour la page Matching
matching_data = [
    {'nom': 'Théophile Zannou', 'initiales': 'TZ', 'filiere': 'ISI', 'niveau': 'Master 1', 
     'role': 'mentor', 'competences': 0, 'filiere_score': 15, 'dispo_score': 0, 
     'total': 15, 'couleur': '#e67e22'},
    {'nom': 'Roméo Ahoannoun', 'initiales': 'RA', 'filiere': 'RSI', 'niveau': 'Licence 3', 
     'role': 'mentore', 'competences': 0, 'filiere_score': 5, 'dispo_score': 0, 
     'total': 5, 'couleur': '#7c3aed'}
]

# Données pour la page Profil
disponibilites = {
    'Lundi': [False, False, False, False, False],
    'Mardi': [True, True, False, False, False],
    'Mercredi': [False, False, True, True, False],
    'Jeudi': [False, True, False, False, True],
    'Vendredi': [True, False, False, True, False],
    'Samedi': [False, False, True, False, True]
}

@app.route('/')
def dashboard():
    return render_template('dashboard.html', active='dashboard', user=user, stats=stats,
                          meilleurs_matchs=meilleurs_matchs, offres_recentes=offres_recentes,
                          date=datetime.now().strftime('%A %d %B').lower())

@app.route('/matching')
def matching():
    return render_template('matching.html', active='matching', user=user, matching_data=matching_data)

@app.route('/explorer')
def explorer():
    return render_template('explorer.html', active='explorer', user=user,
                          profils=profils, annonces=annonces)

@app.route('/messagerie')
def messagerie():
    return render_template('messagerie.html', active='messagerie', user=user)

@app.route('/profil')
def profil():
    return render_template('profil.html', active='profil', user=user,
                          disponibilites=disponibilites)

if __name__ == '__main__':
    app.run(debug=True)