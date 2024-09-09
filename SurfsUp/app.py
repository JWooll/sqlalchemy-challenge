# Import the dependencies.
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime as dt

#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def landing():
    return (
        f"Welcome to Jacob's Weather App!<br/>"
        f"Precipitation in inches over one year: /api/v1.0/precipitation<br/>"
        f"List of stations and information: /api/v1.0/stations<br/>"
        f"Temperatures at most commonly reported station over one year: /api/v1.0/tobs<br/>"
        f"<br/>Dates must be entered in YYYY-MM-DD format<br/>"
        f"Min, average, and max temperature after start date: /api/v1.0/&lt;start&gt;<br/>"
        f"Min, average, and max temperature after start date and before end date: /api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    maxDate = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    MDdt = dt.datetime.strptime(maxDate[0], '%Y-%m-%d').date() # Sets value to dt type
    yearAgo = MDdt - dt.timedelta(days=365) # Modifies value using dt subtracting 1 year
    yearAgo = str(yearAgo) # Converts new value back to string
    prcpLastYear = session.query(Measurement.date,Measurement.prcp).filter(Measurement.date > yearAgo).all()

    prcpDIC = {date: prcp for date, prcp in prcpLastYear}
    return jsonify(prcpDIC)

@app.route("/api/v1.0/stations")
def stations():
    stations = session.query(Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()
    stationsDIC = {
        station: { 
            "latitude": latitude, 
            "longitude": longitude, 
            "elevation": elevation,
            "name": name
        }
        for station, name, latitude, longitude, elevation in stations
    }
    return jsonify(stationsDIC)

@app.route("/api/v1.0/tobs")
def tobs():
    maxDate = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    MDdt = dt.datetime.strptime(maxDate[0], '%Y-%m-%d').date() # Sets value to dt type
    yearAgo = MDdt - dt.timedelta(days=365) # Modifies value using dt subtracting 1 year
    yearAgo = str(yearAgo) # Converts new value back to string
    
    stationCounts = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).\
    order_by((func.count(Measurement.station)).desc()).all()
    activeStation = stationCounts[0][0] # The [0][0] here seperates the station name as a string from its nesting
    
    tobsYear = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == activeStation).\
            filter(Measurement.date > yearAgo).all()
    tobsDIC = {date: tobs for date, tobs in tobsYear}
    return jsonify(tobsDIC)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    values = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    
    if end:
        temps = session.query(*values).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    else:
        temps = session.query(*values).filter(Measurement.date >= start).all()
    
    # Put the results into a dictionary
    datesDIC = {
        "TMIN": temps[0][0],
        "TAVG": temps[0][1],
        "TMAX": temps[0][2]
    }
    
    return jsonify(datesDIC)

    

session.close()

if __name__ == '__main__':
    app.run(debug=True)