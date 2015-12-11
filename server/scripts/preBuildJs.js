var fs = require('fs-extra'),
  rimraf = require('rimraf'),
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

var filenameToCopy = (process.argv[2] === '-p' ? 'web.js' : 'web.js');
rimraf('./server/js/config.js', function() {
  fs.copy('config/' + filenameToCopy, './server/js/config.js', opCallback('js config copied'));
});