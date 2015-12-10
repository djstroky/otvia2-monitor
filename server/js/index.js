var $ = require('jquery'),
  c3 = require('c3'),
  analytics = require('ga-browser')(),
  config = require('./config.js')

$(function() {

  // GA tracking
  analytics('create', config.gaTrackingId, 'auto')
  analytics('send', 'pageview', {
    page: '/',
    title: 'Home'
  })

  console.log('hello');
})