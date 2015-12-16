var async      = require('async')
var auth       = require('basic-auth')
var csv        = require('csv')
var express    = require('express')
var fs         = require('fs')
var logStream  = require('logrotate-stream')
var moment     = require('moment')
var morgan     = require('morgan')
var serveIndex = require('serve-index')

var config = require('../config/server.js')

var app = express()

// log requests
app.use(morgan('combined', { stream: logStream({ file: './server/log.log', size: '1M', keep: 3 })}))

// basic http auth
app.use(function(req, res, next) {
  var user = auth(req);
  if (!user || !config.users[user.name] || config.users[user.name] !== user.pass) {
    res.set('WWW-Authenticate', 'Basic realm="Password required for viewing monitor data"');
    return res.status(401).send();
  }
  return next();
})

// Serve static csv files
app.use('/data', serveIndex('./data', {'icons': true}))
app.use('/data', express.static('./data'))

// homepage static files
app.use(express.static('./server/static'))

// webservice to get data
app.get('/recent', function(req, res) {

  // parse querystring params
  var minuteFilter = req.query.filter || 30,
    now = moment()

  // prep response
  var data = {}

  var makeParseFileFn = function(name) {
    return function(cb) {
      var input = fs.createReadStream('./data/' + name + '_last_2_hours.csv')
      var parser = csv.parse()

      // it's a real PITA to find a csv module that will give you the header
      // so I'm hardcoding them
      if(name === 'summary') {
        var out = [['Timestamp', 'Number of Vehicles', 'Number of Vehicles with a Route ID Assigned', 'Number of Vehicles with Location Data', 'Number of Route-Stop Pairs', 'Number of Route-Stop Pairs with Predictions']]
      } else if(name === 'stop') {
        var out = [['Timestamp', 'Stop ID', 'Stop Name', 'Number of Routes', 'Number of Predictions', 'Number of Routes with Predictions', 'Routes with Predictions', 'Display Text']]
      } else if(name === 'vehicle') {
        var out = [['Timestamp', 'Vehicle ID', 'Route ID', 'Pattern ID', 'Work Piece ID', 'Providing Updates', 'Location Timestamp', 'Location Latitude', 'Location Longitude']]
      }

      parser.on('readable', function () {
        while(line = parser.read()) {
          var md = moment(line[0], 'YYYY-MM-DD HH:mm:ss')
          if(md.isValid() && md.add(minuteFilter, 'minutes').isAfter(now)) {
            out.push(line)
          }
        }
      })
      
      parser.on('end', function (count) {
        data[name] = out
        cb()
      })

      input.pipe(parser)

    }
  }

  // read through csv files
  async.parallel([
    makeParseFileFn('summary'),
    makeParseFileFn('stop'),
    makeParseFileFn('vehicle')
  ],
  function(err, results) {
    if(err) {
      res.status(500).send(err)
    }
    res.send(data)
  })

})

// run server
var server = app.listen(3000, function () {
    var host = server.address().address;
    var port = server.address().port;

    console.log('Example app listening at http://%s:%s', host, port);

  }
)