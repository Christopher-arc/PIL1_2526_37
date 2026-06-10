# ============================================================
#  matching.py — Algorithme de matching IFRI_MentorLink
#  CORRECTION : DictCursor retourne des dicts → utiliser ligne['colonne']
#               au lieu de ligne[0]
# ============================================================

def calculer_score_matieres(besoins_user, matieres_mentor):
    if not besoins_user:
        return 0.0
    set_besoins = set(besoins_user)
    set_mentor  = set(matieres_mentor)
    matieres_communes = set_besoins & set_mentor
    score = (len(matieres_communes) / len(set_besoins)) * 10
    return round(score, 2)


def calculer_score_dispos(dispos_user, dispos_mentor):
    if not dispos_user or not dispos_mentor:
        return 0.0
    set_user   = set(dispos_user)
    set_mentor = set(dispos_mentor)
    dispos_communes = set_user & set_mentor
    denominateur = max(len(set_user), len(set_mentor))
    score = (len(dispos_communes) / denominateur) * 10
    return round(score, 2)


def calculer_score_filiere(filiere_user, niveau_user, filiere_mentor, niveau_mentor):
    score = 8 if filiere_user == filiere_mentor else 4
    niveaux = {'L1': 1, 'L2': 2, 'L3': 3, 'M1': 4, 'M2': 5,
               'Licence 1': 1, 'Licence 2': 2, 'Licence 3': 3,
               'Master 1': 4, 'Master 2': 5}
    niveau_user_num   = niveaux.get(niveau_user, 1)
    niveau_mentor_num = niveaux.get(niveau_mentor, 1)
    if niveau_mentor_num > niveau_user_num:
        score += 2
    return min(score, 10)


def calculer_score_global(s_matieres, s_dispos, s_filiere):
    return round((s_matieres * 4.5 + s_dispos * 4.0 + s_filiere * 1.5) / 10, 2)


def trouver_mentors(user_id, db):
    """
    Retourne une liste de dicts triée par score_global décroissant.
    CORRECTION KeyError:0 → on utilise ligne['id_matiere'] car DictCursor
    """
    cursor = db.connection.cursor()

    # ── Besoins de l'utilisateur ──────────────────────────────
    cursor.execute(
        "SELECT id_matiere FROM BESOIN WHERE id_utilisateur = %s", (user_id,)
    )
    # CORRECTION : ligne['id_matiere'] au lieu de ligne[0]
    besoins_user = [ligne['id_matiere'] for ligne in cursor.fetchall()]

    if not besoins_user:
        cursor.close()
        return []

    # ── Disponibilités de l'utilisateur ──────────────────────
    cursor.execute(
        "SELECT id_dispo FROM USER_DISPONIBILITE WHERE id_utilisateur = %s", (user_id,)
    )
    dispos_user = [ligne['id_dispo'] for ligne in cursor.fetchall()]

    # ── Filière et niveau de l'utilisateur ───────────────────
    cursor.execute(
        "SELECT filiere, niveau FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,)
    )
    ligne = cursor.fetchone()
    filiere_user = ligne['filiere'] if ligne else ''
    niveau_user  = ligne['niveau']  if ligne else ''

    # ── Mentors potentiels ────────────────────────────────────
    placeholders = ','.join(['%s'] * len(besoins_user))
    cursor.execute(f"""
        SELECT DISTINCT u.id_utilisateur, u.nom, u.prenom,
                        u.photo, u.filiere, u.niveau
        FROM Utilisateurs u
        JOIN MAITRISE m ON u.id_utilisateur = m.id_utilisateur
        WHERE m.id_matiere IN ({placeholders})
        AND u.id_utilisateur != %s
    """, (*besoins_user, user_id))
    mentors_potentiels = cursor.fetchall()

    # ── Calcul des scores ─────────────────────────────────────
    resultats = []
    for mentor in mentors_potentiels:
        id_mentor       = mentor['id_utilisateur']
        nom             = mentor['nom']
        prenom          = mentor['prenom']
        photo           = mentor['photo']
        filiere_mentor  = mentor['filiere']
        niveau_mentor   = mentor['niveau']

        cursor.execute(
            "SELECT id_matiere FROM MAITRISE WHERE id_utilisateur = %s", (id_mentor,)
        )
        matieres_mentor = [l['id_matiere'] for l in cursor.fetchall()]

        cursor.execute(
            "SELECT id_dispo FROM USER_DISPONIBILITE WHERE id_utilisateur = %s", (id_mentor,)
        )
        dispos_mentor = [l['id_dispo'] for l in cursor.fetchall()]

        s_matieres = calculer_score_matieres(besoins_user, matieres_mentor)
        s_dispos   = calculer_score_dispos(dispos_user, dispos_mentor)
        s_filiere  = calculer_score_filiere(filiere_user, niveau_user,
                                            filiere_mentor, niveau_mentor)
        s_global   = calculer_score_global(s_matieres, s_dispos, s_filiere)

        if s_global > 0:
            resultats.append({
                'id_mentor':       id_mentor,
                'nom':             nom,
                'prenom':          prenom,
                'photo':           photo,
                'filiere':         filiere_mentor,
                'niveau':          niveau_mentor,
                'score_matieres':  s_matieres,
                'score_dispos':    s_dispos,
                'score_filiere':   s_filiere,
                'score_global':    s_global,
            })

    resultats.sort(key=lambda x: x['score_global'], reverse=True)
    cursor.close()
    return resultats
