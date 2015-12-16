var $ = require('jquery'),
  analytics = require('ga-browser')(),
  c3 = require('c3'),
  config = require('./config.js'),
  d3 = require('d3'),
  footable = require('footable')

var chart

var receiveData = function(data) {
  drawChart(data.summary)
  drawTables(data)
}

var drawChart = function(data) {

  // Summary data column mapping:
  // 0: Timestamp
  // 1: Number of Vehicles
  // 2: Number of Vehicles with a Route ID Assigned
  // 3: Number of Vehicles with Location Data
  // 4: Number of Route Stop Pairs
  // 5: Route Stop Pairs with Predictions

  // parse data & hardcode percentage headers
  var columnData = [
    ['Timestamp'],
    ['Percent of Vehicles Not Assigned to Route'],
    ['Percent of Vehicles Assigned to Route'],
    ['Percent of Vehicles With Location Data'],
    ['Percent of Route-Stop Pairs with no Prediction'],
    ['Percent of Route-Stop Pairs with Prediction']
  ] 

  for (var i = 1; i < data.length; i++) {
    var numVehicles = data[i][1],
      pctVehNoRoute = (numVehicles - data[i][2]) / numVehicles,
      pctVehWithRoute = data[i][2] / numVehicles,
      pctVehWithLocation = data[i][3] / numVehicles,
      pctRSNoPrediction = (data[i][4] - data[i][5]) / data[i][4],
      pctRSWithPrediction = data[i][5] / data[i][4];

    columnData[0].push(data[i][0])
    columnData[1].push(pctVehNoRoute)
    columnData[2].push(pctVehWithRoute)
    columnData[3].push(pctVehWithLocation)
    columnData[4].push(pctRSNoPrediction)
    columnData[5].push(pctRSWithPrediction)
    
  }

  // c3 data cfg
  var data = {
    x: 'Timestamp',
    xFormat: '%Y-%m-%d %H:%M:%S',
    columns: columnData,
    type: 'bar',
    groups: [
      ['Percent of Vehicles Not Assigned to Route',
        'Percent of Vehicles Assigned to Route',
        'Percent of Vehicles With Location Data'],
      ['Percent of Route-Stop Pairs with no Prediction',
        'Percent of Route-Stop Pairs with Prediction']
    ]
  }

  if(!chart) {
    // create chart
    chart = c3.generate({
      bindto: '#chart',
      data: data,
      axis: {
        y: {
          label: {
            text: 'Count',
            position: 'outer-middle'
          },
          tick: {
            format: d3.format('%')
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
      },
      tooltip: {
        contents: function (d, defaultTitleFormat, defaultValueFormat, color) {
          // copied from http://stackoverflow.com/a/25750639/269834
          // avoids sorting by highest value

          var $$ = this, config = $$.config,
            titleFormat = config.tooltip_format_title || defaultTitleFormat,
            nameFormat = config.tooltip_format_name || function (name) { return name; },
            valueFormat = config.tooltip_format_value || defaultValueFormat,
            text, i, title, value, name, bgcolor;

          for (i = 0; i < d.length; i++) {
            if (! (d[i] && (d[i].value || d[i].value === 0))) { continue; }

            if (! text) {
                title = titleFormat ? titleFormat(d[i].x) : d[i].x;
                text = "<table class='" + $$.CLASS.tooltip + "'>" + (title || title === 0 ? "<tr><th colspan='2'>" + title + "</th></tr>" : "");
            }

            name = nameFormat(d[i].name);
            value = valueFormat(d[i].value, d[i].ratio, d[i].id, d[i].index);
            bgcolor = $$.levelColor ? $$.levelColor(d[i].value) : color(d[i].id);

            text += "<tr class='" + $$.CLASS.tooltipName + "-" + d[i].id + "'>";
            text += "<td class='name'><span style='background-color:" + bgcolor + "'></span>" + name + "</td>";
            text += "<td class='value'>" + value + "</td>";
            text += "</tr>";
          }
          return text + "</table>";
        }
      }
    })
  } else {
    // load data in existing chart
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