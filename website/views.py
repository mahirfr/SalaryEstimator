from crypt import methods
from nis import cat
from unicodedata import category
from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from .utilities import REGIONS
from . import db
from .models import User, Day, Zone
from datetime import datetime
from sqlalchemy import desc


views = Blueprint('views', __name__)

# Calculates salary of temporary worker
@views.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # User's input for his hourly rate, hours worked and meal plans 
        rate = request.form.get('rate')
        
        hours1 = request.form.get('heures1')
        hours2 = request.form.get('heures2')
        hours3 = request.form.get('heures3')
        hours4 = request.form.get('heures4')

        hours = [hours1, hours2, hours3, hours4]

        # Overtime and regular pay
        supp_125 = 0
        supp_150 = 0
        regular = 0

        # Total hours and meal plans
        sum_hours = 0

        try:
            float(rate)
        except:
            flash('Les données d\'entrée sont incorrectes, réessayez', category='error')
            return render_template('index.html', user=current_user)

        # Calculations of overtime and regular pay
        # 60 = max amout of hours legally possible
        # if hours > 42, hourly rate = 150%
        # 35 to 42, hourly rate = 125%
        # 35 = regular work week hours
        for i in range(len(hours)):
            if hours[i] == "":
                hours[i] = 0
            elif float(hours[i]) < 0 or float(hours[i]) > 60:
                flash('Entrez un chiffre entre 0 et 60', category='error')
                return render_template('index.html', user=current_user)
            elif float(hours[i]) > 42 and float(hours[i]) <= 60:
                sum_hours += 35 * float(rate) + (42 - 35) * (float(rate) + (float(rate) * 0.25)) + (float(hours[i]) - 42) * (float(rate) + (float(rate) * 0.5))
                supp_150 += float(hours[i]) - 42
                supp_125 += 7
                regular += 35
                continue
            elif float(hours[i]) > 35 and float(hours[i]) <= 42:
                sum_hours += 35 * float(rate) + (float(hours[i]) - 35) * (float(rate) + (float(rate) * 0.25))
                supp_125 += float(hours[i]) - 35
                regular += 35
                continue
            elif float(hours[i]) > 0 and float(hours[i]) <= 35:
                sum_hours += float(hours[i]) * float(rate)
                regular += float(hours[i])
            else:
                flash('Les données d\'entrée sont incorrectes, réessayez', category='error')
                return render_template('index.html', user=current_user)
        
        # Payed vacation and end of work mission allowances 
        # ifm = 10% of total pay
        # icp = 10% of total pay ifm included
        ifm = (sum_hours * 10) / 100
        icp = ((sum_hours + ifm) * 10) / 100

            
        flash('Salaire estimé!', category="success")
        return render_template("salaire.html", salary=sum_hours+icp+ifm, supp_125=supp_125, supp_150=supp_150, regular=regular, icp=icp, ifm=ifm, user=current_user)

    return render_template("index.html", user=current_user)


@views.route('/detail', methods=['GET', 'POST'])
@login_required
def detail():
    user = current_user
    # Get user's input
    if request.method == 'POST':
        date = request.form.get('date')
        hours = request.form.get('hours')
        zone = request.form.get('zone')
        # turn the date string into date datetime stripping the time
        date_entered = datetime.strptime(date, '%Y-%m-%d').date()

        current_week = date_entered.strftime('%W')

        try:
            hours = int(hours)
            zone = int(zone)
        except:
            flash('Données entrées sont invalides !', category='error')
            return render_template('detail.html', user=user)

        meal = 0

        if hours > 4 and hours <= 12:
            meal = 1
        # 12h of work per day for 5 days is the max legal limit
        elif hours > 12:
            flash('Les heures depasent la limite legale de travail', category='error')
            return render_template('detail.html', user=user)

        # This region doesn't have a zone 7
        if user.region == 'Lorraine' and zone > 50:
            zone = 50

        # Check if user exceeded legal work limit for one week which is 60h
        exceeded = db.engine.execute("SELECT strftime('%W', date) as week, sum(hours) as hours FROM day WHERE week = ? AND user_id = ?;", current_week, user.id)
        for item in exceeded:
            if item.hours != None and item.hours + hours > 60:
                flash('Vous avez depassé la limite legale d\'heures travaillées pour cette semaine', category='error')
                return render_template('detail.html', user=user)

        # Check if user already entered the same date 
        exists = db.session.query(db.session.query(Day).filter_by(date=date_entered, user_id=user.id).exists()).scalar()
        if exists:
            flash('Vous avez déjà une entrée pour cette date', category='error')
            return render_template('detail.html', user=user)
        
        zones = Zone.query.filter_by(km=zone, user_id=user.id).first()
        # Check if user filled out his profile 
        if zones is None:
            flash('Veuillez d\'abord remplir votre profile ou appliquer vos données !', category='error')
            return render_template("profile.html", user=user, regions=REGIONS)
        # Adds the input to db (Day table)
        day = Day(date=date_entered, hours=hours, meal_qty=meal, user_id=user.id, zone_id=zones.id)
        db.session.add(day)
        db.session.commit()

        # Initialized vars, dicts, and lists
        weeks_pay = 0
        regular_hours = 0
        hrs_125 = 0
        hrs_150 = 0
        weekly_meals = 0
        sum_zones = 0
        monthly_hours = {}
        monthly_total_hrs = 0
        monthly_reg = 0
        monthly_125 = 0
        monthly_150 = 0
        week = {}
        months = {"month": 0, "weeks": [], "ifm": 0, "icp": 0, "monthly_hours": [], "monthly_pay": 0}
        processed = []
        monthly_pay = 0
        two_weeks_hours = 0

        # Query to get user's info grouped by month and by week
        results = db.engine.execute("SELECT strftime('%W', date) as week, strftime('%m', date) as month, sum(hours) as hours, date, sum(price) as commute, sum(meal_qty) as weekly_meals, day.id as id FROM zone JOIN day ON day.zone_id = zone.id WHERE day.user_id = ? GROUP BY month, week;", user.id)
        month = None

        # This counter is used to check if lask week == current week
        # This occurs when a week begins in the previous month and ends in the current one
        # It's needed to calculate the overtime pay if any
        last_week_checker = 0

        # Loops through the above query
        for result in results:

            # Get first month
            if month == None:
                months["month"] = int(result.month)
            
            # Checks if month changed
            if month != int(result.month) and month != None:
                ifm = monthly_pay * 0.1
                icp = (monthly_pay + ifm) * 0.1
                monthly_pay += ifm + icp
                monthly_hours["monthly_total_hrs"] = monthly_total_hrs
                monthly_hours["monthly_reg"] = monthly_reg
                monthly_hours["monthly_125"] = monthly_125
                monthly_hours["monthly_150"] = monthly_150
                months["monthly_hours"].append(monthly_hours)
                months["month"] = month
                months["ifm"] = ifm
                months["icp"] = icp
                months["monthly_pay"] = monthly_pay
                processed.append(months)

                # Checks if week is in both months and calculates overtime
                if months["weeks"][last_week_checker - 1]["week"] == int(result.week):
                    past_week_125 = months["weeks"][last_week_checker - 1]["hrs_125"]
                    past_week_150 = months["weeks"][last_week_checker - 1]["hrs_150"]
                    past_week = months["weeks"][last_week_checker - 1]["total_hours"]
                    two_weeks_hours = past_week + result.hours
                    if past_week > 42:
                        hrs_125 = 0
                        hrs_150 = result.hours - past_week_150
                    elif past_week > 35 and past_week <= 42 and two_weeks_hours > 42:
                        hrs_125 = 42 - 35 - past_week_125
                        hrs_150 = result.hours - hrs_125
                    elif past_week >= 0 and past_week <= 35 and two_weeks_hours > 35:
                        if two_weeks_hours > 42:
                            regular_hours = 35
                            hrs_125 = 42 - regular_hours
                            hrs_150 = two_weeks_hours - 42
                        else:
                            hrs_125 = two_weeks_hours - 35
                            hrs_150 = 0
                
                # Initializes the month and related values to 0
                months = {"month": 0, "weeks": [], "ifm": 0, "icp": 0, "monthly_hours": [], "monthly_pay": 0}
                monthly_pay = 0
                monthly_hours = {}
                monthly_total_hrs = 0
                monthly_reg = 0
                monthly_125 = 0
                monthly_150 = 0
                ifm = 0
                icp = 0
                last_week_checker = 0

            # Where the pay and overtime are calculated calculated 
            if result.hours > 42:
                regular_hours = 35
                hrs_125 = 42 - regular_hours
                hrs_150 = result.hours - 42
                weeks_pay = regular_hours * user.hourly_rate + hrs_125 * (user.hourly_rate + (user.hourly_rate * 0.25)) + hrs_150 * (user.hourly_rate + (user.hourly_rate * 0.50))
                sum_zones = result.commute
                weekly_meals = result.weekly_meals * user.meal
                monthly_pay += weeks_pay + sum_zones + weekly_meals
            elif result.hours > 35 and result.hours <= 42:
                regular_hours = 35
                hrs_125 = result.hours - regular_hours
                weeks_pay = regular_hours * user.hourly_rate + hrs_125 * (user.hourly_rate + (user.hourly_rate * 0.25))
                sum_zones = result.commute
                weekly_meals = result.weekly_meals * user.meal
                monthly_pay += weeks_pay + sum_zones + weekly_meals
            elif result.hours >= 0 and result.hours <= 35:
                # This checks for overtime when the same week is in two months
                if two_weeks_hours > 35:
                    regular_hours = result.hours - hrs_125 - hrs_150
                    weeks_pay = regular_hours * user.hourly_rate + hrs_125 * (user.hourly_rate + (user.hourly_rate * 0.25)) + hrs_150 * (user.hourly_rate + (user.hourly_rate * 0.50))
                    sum_zones = result.commute                
                    weekly_meals = result.weekly_meals * user.meal
                    monthly_pay += weeks_pay + sum_zones + weekly_meals
                else:
                    weeks_pay = result.hours * user.hourly_rate
                    regular_hours = result.hours
                    sum_zones = result.commute                
                    weekly_meals = result.weekly_meals * user.meal
                    monthly_pay += weeks_pay + sum_zones + weekly_meals

            # Add the monthly hours
            monthly_reg += regular_hours
            monthly_125 += hrs_125
            monthly_150 += hrs_150
            monthly_total_hrs += regular_hours + hrs_125 + hrs_150

            # Append results to week
            week["week"] = int(result.week)
            week["weeks_pay"] = weeks_pay
            week["hrs_125"] = hrs_125
            week["hrs_150"] = hrs_150
            if two_weeks_hours > 35:
                week["total_hours"] = result.hours 
            else:
                week["total_hours"] = regular_hours + hrs_125 + hrs_150
            week["commute"] = result.commute
            week["meals"] = weekly_meals
            months["weeks"].append(week)
            week = {}
            weeks_pay = 0
            regular_hours = 0
            hrs_125 = 0
            hrs_150 = 0
            weekly_meals = 0
            sum_zones = 0
            two_weeks_hours = 0

            month = int(result.month)
            last_week_checker += 1

        # Because the for loop ends before the last month is added 
        # We add it outside of it 
        ifm = monthly_pay * 0.1
        icp = (monthly_pay + ifm) * 0.1
        monthly_pay += ifm + icp
        monthly_hours["monthly_total_hrs"] = monthly_total_hrs
        monthly_hours["monthly_reg"] = monthly_reg
        monthly_hours["monthly_125"] = monthly_125
        monthly_hours["monthly_150"] = monthly_150
        months["monthly_hours"].append(monthly_hours)
        months["month"] = month
        months["ifm"] = ifm
        months["icp"] = icp
        months["monthly_pay"] = monthly_pay
        processed.append(months)
            
        return render_template("detail.html", user=user, processed=processed)

    elif request.method == 'GET':
        return render_template("detail.html", user=user)

@views.route('/consultez', methods=['GET', 'POST'])
@login_required
def consultez():

    user = current_user

    # ORM join of two tables which displayes the date, distance price,
    # distance in kilometers, and the id of the day table 
    # which is used for deleting in the below post request
    rows = Zone.query.join(Day, Zone.id==Day.zone_id)\
        .add_columns(Day.date, Day.hours, Zone.price, Zone.km, Day.id)\
        .filter(Day.user_id == user.id)\

    if request.method == 'POST':
        suppr = request.form.get('suppr')

        # Delete input for the given day
        delete = Day.query.filter_by(id=int(suppr)).first()
        db.session.delete(delete)
        db.session.commit()

        return render_template("consultez.html", user=user, rows=rows)

    return render_template("consultez.html", user=user, rows=rows)

@views.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():

    if request.method == 'POST':
        # Get user's input 
        user = current_user
        rate = request.form.get("rate")
        region = request.form.get("region")
        meal = request.form.get("meal")
        zone10 = request.form.get("10")
        zone20 = request.form.get("20")
        zone30 = request.form.get("30")
        zone40 = request.form.get("40")
        zone50 = request.form.get("50")
        zone60 = request.form.get("60")        
        zone70 = request.form.get("70")

        zones = [zone10, zone20, zone30, zone40, zone50, zone60, zone70]
        # Check if zone input is valid 
        for zone in zones:
            if zone == "" or zone == 0:
                flash('Données entrées sont invalides', category='error')
                return render_template("profile.html", user=user, regions=REGIONS)
            else:
                zone = float(zone)

        # If the values are none put them to default
        if rate == "" or rate == None:
            rate == 11.07
        if meal == "" or meal == None:
            meal = 1

        # Update the user's info
        id = user.id
        update_user = User.query.filter_by(id=id).first()
        update_user.region = region
        update_user.hourly_rate = float(rate)
        update_user.meal = float(meal)

        # Update zone info
        zone1 = Zone(km=10, price=zone10, user_id=id)
        db.session.add(zone1)
        zone2 = Zone(km=20, price=zone20, user_id=id)
        db.session.add(zone2)
        zone3 = Zone(km=30, price=zone30, user_id=id)
        db.session.add(zone3)
        zone4 = Zone(km=40, price=zone40, user_id=id)
        db.session.add(zone4)
        zone5 = Zone(km=50, price=zone50, user_id=id)
        db.session.add(zone5)
        zone6 = Zone(km=60, price=zone60, user_id=id)
        db.session.add(zone6)
        zone7 = Zone(km=70, price=zone70, user_id=id)
        db.session.add(zone7)
        db.session.commit()
 
        return render_template("profile.html", user=user, regions=REGIONS)

    else:
        return render_template("profile.html", user=current_user, regions=REGIONS)
   