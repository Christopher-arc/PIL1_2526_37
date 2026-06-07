import MySQLdb
from MySQLdb.cursors import DictCursor
from config import Config

def get_connection():
    return MySQLdb.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=DictCursor
    )

# ========== 1. UTILISATEURS ==========
def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Utilisateurs WHERE email = %s", (email,))
    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def create_user(nom, prenom, email, telephone, mot_de_passe, filiere, niveau, bio=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Utilisateurs (nom, prenom, email, telephone, mot_de_passe, filiere, niveau, bio)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (nom, prenom, email, telephone, mot_de_passe, filiere, niveau, bio))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id

# ========== 2. ANNONCES ==========
def get_annonces(filtre_matiere=None, filtre_format=None):
    conn = get_connection()
    cur = conn.cursor()
    sql = """
        SELECT a.*, u.nom, u.prenom, u.filiere, u.niveau
        FROM Annonces a
        JOIN Utilisateurs u ON a.id_utilisateur = u.id_utilisateur
        WHERE a.statut = 'actif'
    """
    params = []
    
    if filtre_format:
        sql += " AND a.format_session = %s"
        params.append(filtre_format)
    
    cur.execute(sql, params)
    data = cur.fetchall()
    conn.close()
    return data

def get_annonce_by_id(annonce_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, u.nom, u.prenom, u.filiere, u.niveau
        FROM Annonces a
        JOIN Utilisateurs u ON a.id_utilisateur = u.id_utilisateur
        WHERE a.id_annonce = %s
    """, (annonce_id,))
    annonce = cur.fetchone()
    conn.close()
    return annonce

def create_annonce(id_utilisateur, type_annonce, format_session, description_perso):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Annonces (id_utilisateur, type_annonce, format_session, description_perso)
        VALUES (%s, %s, %s, %s)
    """, (id_utilisateur, type_annonce, format_session, description_perso))
    annonce_id = cur.lastrowid
    conn.commit()
    conn.close()
    return annonce_id

# ========== 3. MESSAGES ==========
def get_messages_by_discussion(discussion_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.*, u.nom, u.prenom
        FROM Messages m
        JOIN Utilisateurs u ON m.id_utilisateur = u.id_utilisateur
        WHERE m.id_discussion = %s
        ORDER BY m.date_envoi ASC
    """, (discussion_id,))
    messages = cur.fetchall()
    conn.close()
    return messages

def get_discussions_by_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.*, 
               GROUP_CONCAT(DISTINCT u.id_utilisateur) as participants
        FROM Discussions d
        JOIN PARTICIPATION p ON d.id_discussion = p.id_discussion
        JOIN Utilisateurs u ON p.id_utilisateur = u.id_utilisateur
        WHERE d.id_discussion IN (
            SELECT id_discussion FROM PARTICIPATION WHERE id_utilisateur = %s
        )
        GROUP BY d.id_discussion
    """, (user_id,))
    data = cur.fetchall()
    conn.close()
    return data

def send_message(id_discussion, id_utilisateur, contenu):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Messages (id_discussion, id_utilisateur, contenu)
        VALUES (%s, %s, %s)
    """, (id_discussion, id_utilisateur, contenu))
    message_id = cur.lastrowid
    conn.commit()
    conn.close()
    return message_id

# ========== Gestion des NOTIFICATIONS des messages ==========
def create_notification(user_id, type_notification, contenu):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Notifications (id_utilisateur, type_notif, contenu)
        VALUES (%s, %s, %s)
    """, (user_id, type_notification, contenu))
    notif_id = cur.lastrowid
    conn.commit()
    conn.close()
    return notif_id

def get_notifications_non_lues(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM Notifications
        WHERE id_utilisateur = %s AND lu = FALSE
        ORDER BY date_creation DESC
    """, (user_id,))
    data = cur.fetchall()
    conn.close()
    return data

def mark_notification_as_lue(notification_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Notifications SET lu = TRUE WHERE id_notification = %s", (notification_id,))
    conn.commit()
    conn.close()
    return True

# ========== Phase 5. MATCHING ==========
def get_matches_for_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.*, 
               u1.nom as mentor_nom, u1.prenom as mentor_prenom,
               u2.nom as mentore_nom, u2.prenom as mentore_prenom
        FROM Matching m
        JOIN Utilisateurs u1 ON m.id_mentor = u1.id_utilisateur
        JOIN Utilisateurs u2 ON m.id_mentore = u2.id_utilisateur
        WHERE m.id_mentor = %s OR m.id_mentore = %s
    """, (user_id, user_id))
    data = cur.fetchall()
    conn.close()
    return data

def create_match(id_mentor, id_mentore, score_compatibilite):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Matching (id_mentor, id_mentore, score_compatibilite)
        VALUES (%s, %s, %s)
    """, (id_mentor, id_mentore, score_compatibilite))
    match_id = cur.lastrowid
    conn.commit()
    conn.close()
    return match_id

# ========== Phase 6 :  RÉPONSES AUX ANNONCES ==========
def get_reponses_for_annonce(annonce_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, u.nom, u.prenom, u.filiere
        FROM Reponses r
        JOIN Utilisateurs u ON r.id_utilisateur = u.id_utilisateur
        WHERE r.id_annonce = %s
    """, (annonce_id,))
    data = cur.fetchall()
    conn.close()
    return data

def create_reponse(id_utilisateur, id_annonce, message_accomp=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Reponses (id_utilisateur, id_annonce, message_accomp)
        VALUES (%s, %s, %s)
    """, (id_utilisateur, id_annonce, message_accomp))
    reponse_id = cur.lastrowid
    conn.commit()
    conn.close()
    return reponse_id
