var fs = require('fs');

var tryToMakeDir = function(dir) {
  try {
    fs.mkdirSync(dir);
  } catch(e) {
    if ( e.code != 'EEXIST' ) throw e;
  }
}

tryToMakeDir('./server/static');