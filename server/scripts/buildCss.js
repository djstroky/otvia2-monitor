var concat = require('concat'),
  fs = require('fs-extra'),
  pjson = require('../../package.json'),
  files = [],
  dest = pjson.cssBuild.outFile,
  opCallback = function(success_message) {
  	return function(error) {
      if(error) {
    		console.error(error);
    		process.exit(2);
    		return;
  	  }
      console.log(success_message);
  	}
  };

fs.readdirSync('./server/styles').forEach(function(file) {
  if(file.indexOf('.css') == -1) return;
  files.push('./server/styles/' + file);
});

fs.readdirSync('./server/static').forEach(function(file) {
  if(file.indexOf('.css') == -1) return;
  if(file == "main.css") return;
  files.push('./server/static/' + file);
});

concat(files, dest, opCallback('files concatenated'));

// copy fonts
fs.copy('./server/styles/fonts',
  './server/static/fonts',
  opCallback('fonts moved'))

/*fs.copy('assets', 
    'static/public/assets', 
    opCallback('assets moved'));*/