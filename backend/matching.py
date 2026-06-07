# ============================================================
#  matching.py — Algorithme de matching du projet IFRI_MentorLink
# Très très bien détaillée pour que moi mm je comprennes et vous après
#  À placer à la racine du projet Flask cf Rajwane
# ============================================================
#
#  ELEMENTS DU COURS DE PYTHON UTILISÉS (avec explications) :
#  - def     : définir une fonction (bloc de code réutilisable)
#  - set()   : ensemble sans doublons, permet l'intersection avec &
#  - list    : liste ordonnée d'éléments
#  - dict    : dictionnaire clé→valeur (ex: {'nom': 'Koffi'})
#  - for     : boucle pour parcourir une liste
#  - if/else : condition
#  - .sort() : trier une liste
#  - return  : ce que la fonction renvoie
# ============================================================
 
#  FONCTION 1 : Score de compatibilité des matières (sur 10)
#
#  PRINCIPE :
#  On regarde combien de matières que U veut apprendre
#  sont maîtrisées par le mentor M.
#
#  EXEMPLE :
#  U a besoin de : [Python, Maths, Algo]  → 3 matières
#  M maîtrise    : [Python, BDD, Algo]    → 2 en commun
#  Score = (2/3) × 10 = 6.67 / 10
#
#  CONCEPT PYTHON — set et intersection (&) :
#  set([1,2,3]) & set([2,3,4]) → {2, 3}  (éléments en commun)
 
def calculer_score_matieres(besoins_user, matieres_mentor):
    """
    besoins_user   : liste d'id_matiere que le user veut apprendre
    matieres_mentor: liste d'id_matiere que le mentor maîtrise
    Retourne un score entre 0 et 10
    """
    # Si l'utilisateur n'a défini aucun besoin → score 0
    if not besoins_user:
        return 0.0
 
    # On convertit les listes en sets pour trouver l'intersection
    set_besoins = set(besoins_user)
    set_mentor  = set(matieres_mentor)
 
    # L'intersection = matières en commun entre besoins et compétences du mentor
    matieres_communes = set_besoins & set_mentor
 
    # Score = (nb commun / nb total de besoins) × 10
    score = (len(matieres_communes) / len(set_besoins)) * 10
 
    return round(score, 2)   # on arrondit à 2 décimales

 
#  FONCTION 2 : Score de compatibilité des disponibilités (sur 10)
#
#  PRINCIPE :
#  On cherche combien de créneaux horaires sont en commun.
#
#  EXEMPLE :
#  U disponible  : [Lundi 8h, Mercredi 14h, Vendredi 10h]
#  M disponible  : [Lundi 8h, Jeudi 13h]
#  En commun     : [Lundi 8h]  → 1 créneau
#  Dénominateur  : max(3, 2) = 3
#  Score = (1/3) × 10 = 3.33 / 10
 
def calculer_score_dispos(dispos_user, dispos_mentor):
    """
    dispos_user  : liste d'id_dispo de l'utilisateur
    dispos_mentor: liste d'id_dispo du mentor
    Retourne un score entre 0 et 10
    """
    # Si l'un ou l'autre n'a pas renseigné ses disponibilités → score 0
    if not dispos_user or not dispos_mentor:
        return 0.0
 
    set_user   = set(dispos_user)
    set_mentor = set(dispos_mentor)
 
    dispos_communes = set_user & set_mentor
 
    # On divise par le max des deux pour ne pas avantager
    # quelqu'un qui renseigne beaucoup de créneaux
    denominateur = max(len(set_user), len(set_mentor))
    score = (len(dispos_communes) / denominateur) * 10
 
    return round(score, 2)
  

#  FONCTION 3 : Score de proximité filière/niveau (sur 10)
#
#  PRINCIPE :
#  Même filière = meilleur score (le mentor comprend mieux le cursus)
#  Mentor à niveau supérieur = bonus
#
#  EXEMPLE :
#  User  : IA L1 / Mentor : IA L2
#  Même filière → 8pts + niveau supérieur → +2pts = 10/10
#
#  EXEMPLE 2 :
#  User : IA L1 / Mentor : GL L3
#  Filière différente → 4pts + niveau supérieur → +2pts = 6/10
#
#  CONCEPT PYTHON — dictionnaire :
#  niveaux = {'L1': 1, 'L2': 2, ...}
#  niveaux['L2'] → 2   (on accède à la valeur avec la clé)
 
def calculer_score_filiere(filiere_user, niveau_user, filiere_mentor, niveau_mentor):
    """
    Retourne un score entre 0 et 10
    """
    score = 0
 
    # Même filière → 8 points de base
    if filiere_user == filiere_mentor:
        score = 8
    else:
        # Filières différentes mais compatibles (ex: IA ↔ IM)
        score = 4
 
    # Dictionnaire pour convertir le niveau en nombre
    # L1=1, L2=2, L3=3, M1=4, M2=5
    niveaux = {'L1': 1, 'L2': 2, 'L3': 3, 'M1': 4, 'M2': 5}
 
    # .get(clé, valeur_par_défaut) : si la clé n'existe pas → 1
    niveau_user_num   = niveaux.get(niveau_user, 1)
    niveau_mentor_num = niveaux.get(niveau_mentor, 1)
 
    # Bonus si le mentor est plus avancé dans ses études
    if niveau_mentor_num > niveau_user_num:
        score += 2
 
    # On s'assure que le score ne dépasse pas 10
    return min(score, 10)
 