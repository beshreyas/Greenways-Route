$(document).ready(function(){

  var mc = {
    '0-50'     : 'green',
    '51-100'    : 'yellow',
    '101-150'   : 'orange',
    '151-200'   : 'red',
    '201-300'   : 'maroon',
    '300-99999'   : 'brown'
  };

function between(x, min, max) {
  return x >= min && x <= max;
}