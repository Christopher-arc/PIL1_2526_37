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
if __name__ == '__main__':
    app.run(debug=True, port=5001)  