#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import datetime
import sys

from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_date(date, format)

# app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  query_set = Venue.query.order_by(Venue.city, Venue.state).all()
  ref_city = None
  ref_state = None
  for venue in query_set:
    if venue.state == ref_state and venue.city == ref_city:
      data[-1]["venues"].append({
        "id": venue.id,
        "name": venue.name
      })
    else:
      data.append({
        "city": venue.city,
        "state": venue.state,
        "venues": [{
          "id": venue.id,
          "name": venue.name
        }]
      })
      ref_city = venue.city
      ref_state = venue.state
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response = {}
  response["count"] = 0
  response['data'] = []
  q = request.form.get('search_term')
  query_set = Venue.query.\
              filter(Venue.name.ilike(f'{q}%') | Venue.name.ilike(f'%{q}') | Venue.name.ilike(f'%{q}%')).all()

  for result in query_set:
    response['data'].append({
      "id": result.id,
      "name": result.name
    })
  response['count'] = len(query_set)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try:
    data = Venue.query.get(venue_id)
    shows = Venue.query.get(venue_id).shows
    past_shows = [show for show in shows if show.start_time < datetime.datetime.today()]
    upcoming_shows = [show for show in shows if show.start_time >= datetime.datetime.today()]
    past_shows = [
      {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      } 
    for show in past_shows]

    upcoming_shows = [
      {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      } 
    for show in upcoming_shows]
    
    data = {
      "id": data.id,
      "name": data.name,
      "genres": data.genres,
      "address": data.address,
      "city": data.city,
      "state": data.state,
      "phone": data.phone,
      "website": data.website,
      "facebook_link": data.facebook_link,
      "seeking_talent": data.seeking_talent,
      "seeking_description": data.seeking_description,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }    
  except:
    print(sys.exc_info())
    return render_template('errors/500.html'), 500
  if not data:
    return render_template('errors/404.html'), 404
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    fb_link = request.form['facebook_link']

    new_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=fb_link)
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + new_venue.name + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + new_venue.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  try:
    venue_to_delete = Venue.query.get(venue_id)
    db.session.delete(venue_to_delete)
    db.session.commit()
    flash('Venue was successfully Deleted!')
  except:
    db.session.rollback()
    flash('Something went wrong!')
    error = True
  finally:
    db.session.close()
  if(error):
    return jsonify({"message": "Failed"})
  return jsonify({"message": "Succeed"})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  query_set = Artist.query.all()
  data = [ {"id": artist.id, "name": artist.name} for artist in query_set]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response = {}
  response["count"] = 0
  response['data'] = []
  q = request.form.get('search_term')
  query_set = Artist.query.\
              filter(Artist.name.ilike(f'{q}%') | Artist.name.ilike(f'%{q}') | Artist.name.ilike(f'%{q}%')).all()

  for result in query_set:
    response['data'].append({
      "id": result.id,
      "name": result.name
    })
  response['count'] = len(query_set)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  try:
    data = Artist.query.get(artist_id)
    shows = Artist.query.get(artist_id).shows
    past_shows = [show for show in shows if show.start_time < datetime.datetime.today()]
    upcoming_shows = [show for show in shows if show.start_time >= datetime.datetime.today()]
    past_shows = [
      {
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      } 
    for show in past_shows]

    upcoming_shows = [
      {
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "venue_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      } 
    for show in upcoming_shows]
    
    data = {
      "id": data.id,
      "name": data.name,
      "genres": data.genres,
      "city": data.city,
      "state": data.state,
      "phone": data.phone,
      "website": data.website,
      "facebook_link": data.facebook_link,
      "seeking_venue": data.seeking_venue,
      "seeking_description": data.seeking_description,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    } 
  except:
    print(sys.exc_info())
    return render_template('errors/500.html'), 500
  if not data:
    return render_template('errors/404.html'), 404
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>
  try:
    artist = Artist.query.get(artist_id)
  except:
    return render_template('errors/500.html'), 500
  if not artist:
    return render_template('errors/404.html'), 404
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    edit_artist = Artist.query.get(artist_id)
  except:
    return render_template('errors/500.html'), 500
  if not edit_artist:
    return render_template('errors/404.html'), 404
  form = ArtistForm(obj=edit_artist)
  if form.validate_on_submit():
    edit_artist.name = form.name.data
    edit_artist.city = form.city.data
    edit_artist.state = form.state.data
    edit_artist.phone = form.phone.data
    edit_artist.genres = form.genres.data
    edit_artist.facebook_link = form.facebook_link.data
    db.session.commit()
    return redirect(url_for('show_artist', artist_id=edit_artist.id))
  return render_template('forms/edit_artist.html', form=form, artist=edit_artist)

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>
  try:
    venue = Venue.query.get(venue_id)
  except:
    return render_template('errors/500.html'), 500
  if not venue:
    return render_template('errors/404.html'), 404
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    edit_venue = Venue.query.get(venue_id)
  except:
    return render_template('errors/500.html'), 500
  if not edit_venue:
    return render_template('errors/404.html'), 404
  form = VenueForm(obj=edit_venue)
  if form.validate_on_submit():
    edit_venue.name = form.name.data
    edit_venue.city = form.city.data
    edit_venue.state = form.state.data
    edit_venue.address = form.address.data
    edit_venue.phone = form.phone.data
    edit_venue.genres = form.genres.data
    edit_venue.facebook_link = form.facebook_link.data
    db.session.commit()
    return redirect(url_for('show_venue', venue_id=edit_venue.id))
  return render_template('forms/edit_venue.html', form=form, venue=edit_venue)
  

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    fb_link = request.form['facebook_link']

    new_Artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=fb_link)
    db.session.add(new_Artist)
    db.session.commit()
    flash('Artist ' + new_Artist.name + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + new_Artist.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.all()
  data = [{
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "artist_id": show.artist_id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": show.start_time
  }for show in shows]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  try:
    venue_id = request.form['venue_id']
    artist_id = request.form['artist_id']
    start_time = request.form['start_time']
    new_show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
