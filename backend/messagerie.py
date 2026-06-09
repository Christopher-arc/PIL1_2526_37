from flask import Flask, jsonify, session
from flask_socketio import SocketIO, emit, join_room
import mysql.connector
app = Flask(__name__)
app.secret_key = 'mentorlink_2026'
socketio = SocketIO(app, cors_allowed_origins="*")
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


@app.route('/notifications')
def get_notifications():
    user_id = session.get('user_id', 1)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_notification, type_notif, contenu, date_creation
        FROM Notifications
        WHERE id_utilisateur = %s AND lu = FALSE
        ORDER BY date_creation DESC
    """, (user_id,))
    notifs = cursor.fetchall()
    for n in notifs:
        n['date_creation'] = n['date_creation'].strftime('%d/%m %H:%M')
    cursor.close()
    db.close()
    return jsonify({'count': len(notifs), 'notifications': notifs})


@socketio.on('rejoindre_discussion')
def on_join(data):
    room = str(data['id_discussion'])
    join_room(room)


@socketio.on('send_message')
def handle_message(data):
    user_id = session.get('user_id', 1)
    id_discussion = data['id_discussion']
    contenu = data['contenu']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        INSERT INTO Messages (id_discussion, id_utilisateur, contenu, lu)
        VALUES (%s, %s, %s, FALSE)
    """, (id_discussion, user_id, contenu))
    db.commit()
    id_message = cursor.lastrowid
    cursor.execute("SELECT nom, prenom FROM Utilisateurs WHERE id_utilisateur = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    emit('receive_message', {
        'id_message': id_message,
        'contenu': contenu,
        'nom': user['nom'],
        'prenom': user['prenom'],
        'id_utilisateur': user_id,
        'date_envoi': __import__('datetime').datetime.now().strftime('%H:%M')
    }, room=str(id_discussion))
     

@app.route('/notifications/count')
def get_notification_count():
    user_id = session.get('user_id', 1)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM Notifications
        WHERE id_utilisateur = %s AND lu = FALSE
    """, (user_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return jsonify({'count': count})


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)