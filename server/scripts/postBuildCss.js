var rimraf = require('rimraf'),
  fs = require('fs');

fs.readdirSync('./server/static').forEach(function(file) {
  if(file.indexOf('.css') == -1) return;
  if(file == "main.css") return;
  rimraf('./server/static/' + file, function(){});
});