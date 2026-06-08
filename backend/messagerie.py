from flask import Flask, jsonify, session
import mysql.connector
app = Flask(__name__)
app.secret_key = 'mentorlink_2026'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Kaylhia2007',
    'database': 'ifri_mentorLink',
}
def get_db():
    return mysql.connector.connect(**DB_CONFIG)
@app.route('/discussions')
def get_discussions():
    user_id = session.get('user_id', 1)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.id_discussion, d.date_creation,
               u.nom, u.prenom, u.photo,
               (SELECT contenu FROM Messages m2
                WHERE m2.id_discussion = d.id_discussion
                ORDER BY m2.date_envoi DESC LIMIT 1) AS dernier_message,
               (SELECT COUNT(*) FROM Messages m3
                WHERE m3.id_discussion = d.id_discussion
                AND m3.lu = FALSE
                AND m3.id_utilisateur != %s) AS non_lus
        FROM Discussions d
        JOIN PARTICIPATION p ON d.id_discussion = p.id_discussion
        JOIN PARTICIPATION p2 ON d.id_discussion = p2.id_discussion 
             AND p2.id_utilisateur != %s
        JOIN Utilisateurs u ON u.id_utilisateur = p2.id_utilisateur
        WHERE p.id_utilisateur = %s
        ORDER BY d.date_creation DESC
    """, (user_id, user_id, user_id))
    discussions = cursor.fetchall()
    for d in discussions:
        d['date_creation'] = d['date_creation'].strftime('%d/%m %H:%M')
    cursor.close()
    db.close()
    return jsonify(discussions)

@app.route('/discussion/<int:id_discussion>')
def get_messages(id_discussion):
    user_id = session.get('user_id', 1)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE Messages SET lu = TRUE
        WHERE id_discussion = %s AND id_utilisateur != %s
    """, (id_discussion, user_id))
    db.commit()
    cursor.execute("""
        SELECT m.id_message, m.contenu, m.date_envoi,
               u.nom, u.prenom, u.id_utilisateur
        FROM Messages m
        JOIN Utilisateurs u ON m.id_utilisateur = u.id_utilisateur
        WHERE m.id_discussion = %s
        ORDER BY m.date_envoi ASC
    """, (id_discussion,))
    messages = cursor.fetchall()
    for msg in messages:
        msg['date_envoi'] = msg['date_envoi'].strftime('%H:%M')
    cursor.close()
    db.close()
    return jsonify(messages)
if __name__ == '__main__':
    app.run(debug=True, port=5001)  