from crypt import methods
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash 
from . import db
from .utilities import REGIONS
from flask_login import login_required, login_user, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('mdp')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Connexion reussie!', category='success')
                return render_template('profile.html', user=current_user)
            else:
                flash('Mot de passe incorrect', category='error')
        else:
            flash('Adresse mail n\'existe pas.', category='error')
    return render_template('connexion.html', user=current_user)

@auth.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    return redirect(url_for('auth.connexion'))

@auth.route('/inscription', methods=['GET', 'POST'])
def inscription():

    if request.method == 'POST':
        email = request.form.get('email')
        mdp = request.form.get('mdp')
        confirmation = request.form.get('confirmation')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Adresse mail existe déjà', category='error')
            return render_template('inscription.html', user=current_user)
        elif len(email) < 4: 
            flash('Adresse mail doit être plus longue', category="error")
            return render_template('inscription.html', user=current_user)
        elif mdp != confirmation:
            flash('Mot de passes ne sont pas identiques', category="error")
            return render_template('inscription.html', user=current_user)
        elif len(mdp) < 5:
            flash('Mot de passe doit contenir au moins 5 charactères', category="error")
            return render_template('inscription.html', user=current_user)
        else:
            user = User(email=email, password=generate_password_hash(mdp, method='sha256'))
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash('Compte crée!', category="success") 
            flash('Vous pouvez maintenant configurer votre profile', category='success')
        return render_template('profile.html', user=current_user, regions=REGIONS)

    return render_template('inscription.html', user=current_user)
