var auth       = require('basic-auth')
var express    = require('express')
var logStream  = require('logrotate-stream')
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
    res.set('WWW-Authenticate', 'Basic realm="Password required for viewing ART monitor data"');
    return res.status(401).send();
  }
  return next();
})

// Serve static csv files
app.use('/data', serveIndex('./data', {'icons': true}))
app.use('/data', express.static('./data'))

// run server
var server = app.listen(3000, function () {
    var host = server.address().address;
    var port = server.address().port;

    console.log('Example app listening at http://%s:%s', host, port);

  }
)