var $ = require('jquery'),
  c3 = require('c3'),
  analytics = require('ga-browser')(),
  config = require('./config.js'),
  footable = require('footable')

var chart

var receiveData = function(data) {
  drawChart(data.summary)
  drawTables(data)
}

var drawChart = function(data) {

  // parse data
  var columnData = []

  // headers to first val of array
  for (var i = 0; i < data[0].length; i++) {
    columnData.push([data[0][i]])
  }

  for (var i = 1; i < data.length; i++) {
    for (var j = 0; j < data[i].length; j++) {
      columnData[j].push(data[i][j])
    }
  }

  // data

  var data = {
    x: 'Timestamp',
    xFormat: '%Y-%m-%d %H:%M:%S',
    columns: columnData,
    type: 'bar'
  }

  if(!chart) {
    chart = c3.generate({
      bindto: '#chart',
      data: data,
      axis: {
        y: {
          label: {
            text: 'Count',
            position: 'outer-middle'
          }
        },
        x: {
          label: {
            text: 'Time',
            position: 'outer-center'
          },
          type: 'timeseries',
          tick: {
            format: '%m-%d %H:%M'
          }          
        }
      }
    })
  } else {
    chart.load(data)
  }

  $(window).trigger('resize')

}

var drawTables = function(data) {
  
  drawTable('#summary_table', data.summary)
  drawTable('#stop_table', data.stop)
  drawTable('#vehicle_table', data.vehicle)

}

var drawTable = function(id, data) {
  
  // remove previous dom
  $(id).empty()
  
  // calc columns
  var cols = []
  for (var i = 0; i < data[0].length; i++) {

    var curField = data[0][i],
      col = {
        name: curField,
        title: curField
      }

    if(i > 6) {
      col.breakpoints = 'xs sm md'
    } else if(i > 4) {
      col.breakpoints = 'xs sm'
    } else if(i > 2) {
      col.breakpoints = 'xs'
    }

    cols.push(col)

  }

  // calc rows
  var rows = []
  for (var i = 1; i < data.length; i++) {
    var curRow = {}
    for (var j = 0; j < data[0].length; j++) {
      curRow[data[0][j]] = data[i][j]
    }
    rows.push(curRow)
  }

  $(id).footable({
    paging: { enabled: true },
    filtering: { enabled: true },
    sorting: { enabled: true },
    columns: cols,
    rows: rows
  })
}

var selectionChange = function() {

  $.ajax({
    url: '/recent',
    data: { filter: $('#recent_select').val() },
    error: function(jqXHR, textStatus, errorThrown) {
      alert('Error retrieving data.')
    },
    success: receiveData
  })

}

$(function() {

  // GA tracking
  analytics('create', config.gaTrackingId, 'auto')
  analytics('send', 'pageview', {
    page: '/',
    title: 'Home'
  })

  $('#recent_select').on('change', selectionChange)

  selectionChange()

})