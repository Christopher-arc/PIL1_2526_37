import os
from flask import Flask, redirect, url_for
from db import init_db

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'statics')
)

app.secret_key = 'mentorlink_secret'

init_db(app)

from routes.auth     import auth_bp
from routes.profil   import profil_bp
from routes.annonces import annonces_bp

app.register_blueprint(auth_bp)
app.register_blueprint(profil_bp)
app.register_blueprint(annonces_bp)

@app.route('/')
def home():
    return redirect(url_for('auth.inscription'))
@app.route('/test')
def test():
    return "ca marche"
if __name__ == '__main__':
    app.run(debug=True, port=8080)