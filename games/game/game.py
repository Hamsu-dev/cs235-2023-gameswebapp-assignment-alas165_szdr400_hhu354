from flask import abort, render_template, Blueprint, redirect, url_for, request, session

from flask_wtf import FlaskForm
from wtforms import TextAreaField, HiddenField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange

import games.adapters.repository as repo
from games.game import services

import math

from games.authentication.authentication import login_required


game_blueprint = Blueprint(
    'game_bp', __name__
)


@game_blueprint.route('/game/<int:game_id>', methods=['GET', 'POST'])
def game_view(game_id):
    game_data = services.get_game_data(repo.repo_instance, game_id)

    if game_data is None:
        abort(404)

    form = ReviewForm()

    if request.method == 'POST':
        # User needs to be logged in to post a review
        if 'username' not in session:
            return redirect(url_for('auth_bp.login'))
        
        if form.validate_on_submit():
            rating = int(form.rating.data)
            comment = form.comment.data
            services.add_review(repo.repo_instance, game_id, rating, comment)
        # Form validation failed - this should handle itself automatically and show the invalid error messages
        # else:
        #     print('failed', form.errors)

    platform_support = []
    if game_data.windows: platform_support.append('Windows')
    if game_data.mac: platform_support.append('Mac')
    if game_data.linux: platform_support.append('Linux')
    platform_support = ', '.join(platform_support)

    print(game_data.categories)
    if 'Full controller support' in game_data.categories:
        controller_support = 'Full Support'
    elif 'Partial Controller Support' in game_data.categories:
        controller_support = 'Partial Support'
    else:
        controller_support = 'No Support'

    if 'Steam Cloud' in game_data.categories:
        cloud_support = 'Supported'
    else:
        cloud_support = 'Not Supported'

    return render_template(
        'game.html',
        title=f"My Title",
        heading="My Heading",
        game = game_data,
        game_id = game_id,
        form=form,
        controller_support = controller_support,
        platform_support = platform_support,
        cloud_support = cloud_support
    )


@game_blueprint.context_processor
def generate_star_rating():
    def star_rating(rating):
        # There's no half star unicode character :(
        # return 'star ' * math.floor(rating) + 'star-half ' * (math.floor(rating) != math.ceil(rating)) + 'star-empty ' * (5 - math.ceil(rating))
        return '★' * int(rating + 0.5) + '☆' * (5 - int(rating + 0.5))
    return dict(star_rating=star_rating)


class ReviewForm(FlaskForm):
    rating = IntegerField('Rating', [
        DataRequired(message='Rating required'),
        NumberRange(min=1, max=5, message='Rating must be between 1 and 5')
    ])
    comment = TextAreaField('Comment about the game', [
        DataRequired(),
        Length(min=4, message='The review is too short! Please try to be more descriptive'),
    ])
    submit = SubmitField('Submit review')


@game_blueprint.route('/game/add_to_wishlist', methods=['GET'])
@login_required
def add_to_wishlist():
    # Something should actually happen to let the user know that the item has been added to their wishlist
    game_id = int(request.args['game_id'])
    user = repo.repo_instance.get_user(session['username'])
    game = repo.repo_instance.get_game(game_id)
    user.wishlist.add_game(game)
    repo.repo_instance.add_user(user)
    return redirect(url_for('game_bp.game_view', game_id=game_id))
